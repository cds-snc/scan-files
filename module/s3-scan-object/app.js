"use strict";

/**
 * Lambda function that can be invoked by S3 events or SNS messages.
 * This function triggers a scan of newly created S3 objects or updates
 * the scan status of existing S3 objects based on an SNS message payload.
 */

const axios = require("axios");
const pino = require("pino");
const util = require("util");
const { lambdaRequestTracker, pinoLambdaDestination } = require("pino-lambda");
const { S3Client, PutObjectTaggingCommand } = require("@aws-sdk/client-s3");
const { SecretsManagerClient, GetSecretValueCommand } = require("@aws-sdk/client-secrets-manager");
const { STSClient, AssumeRoleCommand } = require("@aws-sdk/client-sts");

const AWS_ROLE_TO_ASSUME = process.env.AWS_ROLE_TO_ASSUME ? process.env.AWS_ROLE_TO_ASSUME : "ScanFilesGetObjects";
const REGION = process.env.REGION;
const ENDPOINT_URL = process.env.AWS_SAM_LOCAL ? "http://host.docker.internal:3001" : undefined;
const LOGGING_LEVEL = process.env.LOGGING_LEVEL ? process.env.LOGGING_LEVEL : "info";
const SCAN_FILES_URL = process.env.SCAN_FILES_URL;
const SCAN_FILES_API_KEY_SECRET_ARN = process.env.SCAN_FILES_API_KEY_SECRET_ARN;
const SCAN_IN_PROGRESS = "in_progress";
const SCAN_FAILED_TO_START = "failed_to_start";
const SNS_SCAN_COMPLETE_TOPIC_ARN = process.env.SNS_SCAN_COMPLETE_TOPIC_ARN;
const EVENT_RESCAN = "custom:rescan";
const EVENT_S3 = "aws:s3";
const EVENT_SNS = "aws:sns";
const EVENT_SQS = "aws:sqs";

const stsClient = new STSClient({ region: REGION, endpoint: ENDPOINT_URL });
const secretsManagerClient = new SecretsManagerClient({ region: REGION, endpoint: ENDPOINT_URL });

// Setup logging and add a custom requestId attribute to all log messages
const logger = pino({ level: LOGGING_LEVEL }, pinoLambdaDestination());
const withRequest = lambdaRequestTracker({
  requestMixin: (event) => {
    return {
      correlation_id: event.RequestId ? event.RequestId : undefined,
    };
  },
});

/**
 * Performs function initialization outside of the Lambda handler so that
 * it only occurs once per cold start of the function rather than on
 * every invocation.
 * @returns {Promise<{apiKey: string}>} API key to use for the scan
 */
const initConfig = async () => {
  return (async () => {
    try {
      const command = new GetSecretValueCommand({
        SecretId: SCAN_FILES_API_KEY_SECRET_ARN,
      });
      const response = await secretsManagerClient.send(command);
      return { apiKey: response.SecretString };
    } catch (error) {
      logger.error(`Unable to get '${SCAN_FILES_API_KEY_SECRET_ARN}' secret: ${error}`);
      throw error;
    }
  })();
};

// Config object used by the handler.  On cold start it is initialized by the
// first handler call.
let config = null;

/**
 * Lambda handler function.  This function is invoked when a new S3 object is
 * created in response to `s3:ObjectCreated:*` events or when an SNS message
 * is received with an update scan status.
 * @param {Object} event Lambda invocation event
 */
exports.handler = async (event, context) => {
  withRequest(event, context);

  // Initialize the function configuration.  This only occurs once per cold start.
  if (config == null) {
    logger.info(`Initializing config`);
    config = await initConfig();
  }

  const errorCount = await processEventRecords(event, config.apiKey);

  return {
    status: errorCount > 0 ? 422 : 200,
    body: `Event records processesed: ${event.Records.length}, Errors: ${errorCount}`,
  };
};

/**
 * Processes the event records.  This function is responsible for starting S3 event
 * record scans and updating the scan results based on SNS topic records.
 * @param {Object} event Lambda invocation event
 * @param {string} apiKey API key used to invoke the Scan Files API
 * @returns int Number of errors encountered processing the event records
 */
const processEventRecords = async (event, apiKey) => {
  const s3Clients = {};
  let errorCount = 0;

  if (!event.Records || event.Records.length === 0) {
    logger.warn(`No records to process for event: ${util.inspect(event)}`);
    return errorCount;
  }

  // Process all event records
  for (const record of event.Records) {
    logger.info(`Processing event record: ${util.inspect(record, false, 10)}`);

    // If this is an SQS event, extract the nested records from the body
    let eventSource = getRecordEventSource(record);
    if (eventSource === EVENT_SQS) {
      const eventBody = JSON.parse(record.body);
      eventBody["RequestId"] = record.messageId;
      eventBody["AccountId"] = record.eventSourceARN.split(":")[4];
      errorCount += await processEventRecords(eventBody, apiKey);
      continue;
    }

    let roleArn = null;
    let scanChecksum = null;
    let scanStatus = null;
    let isObjectTagged = false;
    let s3Object = getS3ObjectFromRecord(eventSource, record);
    let awsAccountId = getEventAttribute(eventSource, event, record, {
      root: "AccountId",
      sns: "aws-account",
    });
    let requestId = getEventAttribute(eventSource, event, record, {
      root: "RequestId",
      sns: "request-id",
    });

    // Make sure SNS events have a top-level RequestId attribute for logging
    event.RequestId = requestId || event.RequestId;

    // Do not scan S3 folder objects
    if (isS3Folder(s3Object)) {
      continue;
    }

    // Start a scan of the new S3 object
    if (awsAccountId != null && eventSource !== null && s3Object !== null) {
      if (eventSource === EVENT_RESCAN || eventSource === EVENT_S3) {
        const response = await startS3ObjectScan(
          `${SCAN_FILES_URL}/clamav/s3`,
          apiKey,
          s3Object,
          awsAccountId,
          SNS_SCAN_COMPLETE_TOPIC_ARN,
          requestId,
        );
        scanStatus = response !== undefined && response.status === 200 ? SCAN_IN_PROGRESS : SCAN_FAILED_TO_START;

        // Get the scan status for an existing S3 object
      } else if (eventSource === EVENT_SNS) {
        scanChecksum = record.Sns.MessageAttributes["av-checksum"].Value;
        scanStatus = record.Sns.MessageAttributes["av-status"].Value;
        logger.info(`S3 scan status '${scanStatus}' received for: ${util.inspect(s3Object)}`);
      }
    } else {
      logger.error(`Unsupported event record: ${util.inspect(record)}`);
    }

    // Tag the S3 object if we've got a scan status
    if (scanStatus !== null) {
      let tags = [
        { Key: "av-scanner", Value: "clamav" },
        { Key: "av-status", Value: scanStatus },
        { Key: "av-timestamp", Value: new Date().getTime() },
      ];

      if (scanChecksum && scanChecksum !== "None") {
        tags.push({ Key: "av-checksum", Value: scanChecksum });
      }

      if (requestId) {
        tags.push({ Key: "request-id", Value: requestId });
      }

      roleArn = `arn:aws:iam::${awsAccountId}:role/${AWS_ROLE_TO_ASSUME}`;
      s3Clients[awsAccountId] = await getS3Client(s3Clients[awsAccountId], stsClient, roleArn);
      isObjectTagged = await tagS3Object(s3Clients[awsAccountId], s3Object, tags);
    }

    // Track if there were any errors processing this record
    if (scanStatus === SCAN_FAILED_TO_START || isObjectTagged === false) {
      logger.warn(
        `Could not process event record: ${util.inspect(
          record,
        )} scanStatus: ${scanStatus} isObjectTagged: ${isObjectTagged}`,
      );
      errorCount++;
    }
  }

  return errorCount;
};

/**
 * Given a valid event source, returns the the request attribute
 * @param {string} eventSource Source of the event
 * @param {Object} event The event payload
 * @param {Object} record The event record payload
 * @param {{root: string, sns: string}} attribute The event attribute names
 * @returns string request ID
 */
const getEventAttribute = (eventSource, event, record, attribute) => {
  let value = null;

  if (eventSource === EVENT_S3 || eventSource === EVENT_RESCAN) {
    value = event[attribute.root] ? event[attribute.root] : null;
  } else if (eventSource === EVENT_SNS) {
    value = record.Sns.MessageAttributes[attribute.sns] ? record.Sns.MessageAttributes[attribute.sns].Value : null;
  }

  return value;
};

/**
 * Determines the event record's source.
 * @param {Object} record Lambda invocation event record
 * @returns {String} Event record source service, or `null` if not valid
 */
const getRecordEventSource = (record) => {
  let eventSource = record.eventSource || record.EventSource;
  const validSources = [EVENT_S3, EVENT_SNS, EVENT_SQS, EVENT_RESCAN];
  return validSources.includes(eventSource) ? eventSource : null;
};

/**
 * Assumes a role given by its ARN and returns the Creditentials object that can
 * be used by other SDK clients.
 * @param {STSClient} stsClient AWS SDK STS client used to assume the role
 * @param {string} roleArn ARN of the role to assume
 * @returns Credentials object for the role
 */
const getRoleCredentials = async (stsClient, roleArn) => {
  let credentials = null;

  try {
    logger.info(`Assuming role ${roleArn}`);
    const command = new AssumeRoleCommand({ RoleArn: roleArn, RoleSessionName: "s3-scan-object" });
    const response = await stsClient.send(command);
    // Submitted, without comment or judgement
    credentials = {
      accessKeyId: response.Credentials.AccessKeyId,
      secretAccessKey: response.Credentials.SecretAccessKey,
      sessionToken: response.Credentials.SessionToken,
    };
  } catch (error) {
    logger.error(`Failed to assume role ${roleArn}: ${error}`);
  }

  return credentials;
};

/**
 * Returns an S3 client if the passed in S3 client has not been initialized.  The S3 client
 * will be initialized using the temporary credentials provided by assuming the given role.
 * @param {S3Client} s3Client Initialized S3 client or null
 * @param {STSClient} stsClient STS client used to assume the role
 * @param {string} roleArn ARN of the role to assume to get tempoary credentials
 * @returns S3 client
 */
const getS3Client = async (s3Client, stsClient, roleArn) => {
  if (!s3Client) {
    logger.info(`Initializing new S3 client for ${roleArn}`);
    const credentials = await getRoleCredentials(stsClient, roleArn);
    return new S3Client({
      region: REGION,
      endpoint: ENDPOINT_URL,
      credentials: credentials,
    });
  } else {
    logger.info(`Returning cached S3 client for ${roleArn}`);
    return s3Client;
  }
};

/**
 * Retrieves the S3 object's Bucket and key from the Lambda invocation event.
 * @param {string} eventSource The source of the event record
 * @param {Object} record Lambda invocation event record
 * @returns {{Bucket: string, Key: string}} S3 object bucket and key
 */
const getS3ObjectFromRecord = (eventSource, record) => {
  let s3Object = null;

  if (eventSource === EVENT_RESCAN) {
    s3Object = parseS3Url(record.s3ObjectUrl);
  } else if (eventSource === EVENT_S3) {
    s3Object = {
      Bucket: record.s3.bucket.name,
      Key: decodeURIComponent(record.s3.object.key.replace(/\+/g, " ")),
    };
  } else if (eventSource === EVENT_SNS) {
    const s3ObjectUrl = record.Sns.MessageAttributes["av-filepath"].Value;
    if (s3ObjectUrl && s3ObjectUrl.startsWith("s3://")) {
      s3Object = parseS3Url(s3ObjectUrl);
    }
  }

  return s3Object;
};

/**
 * Checks if an S3 object represents a folder, which have keys ending with a forward slash `/`.
 * @param {{Bucket: string, Key: string}} s3Object S3 bucket and key
 * @returns Boolean True if the S3 object key is a folder
 */
const isS3Folder = (s3Object) => {
  return !!s3Object && typeof s3Object.Key === "string" && s3Object.Key.endsWith("/");
};

/**
 * Given an S3 object URL, parses the URL and returns the S3 object's bucket and key.
 * @param {string} url S3 object URL in format `s3://bucket/key`
 * @returns {{Bucket: string, Key: string}} S3 object bucket and key or null
 */
const parseS3Url = (url) => {
  let s3Object = null;

  const parsedUrl = url ? url.match(/s3:\/\/([^/]+)\/(.+)/) : null;
  if (parsedUrl !== null && parsedUrl.length === 3) {
    s3Object = {
      Bucket: parsedUrl[1],
      Key: parsedUrl[2],
    };
  }

  return s3Object;
};

/**
 * Starts a scan of the S3 object using the provided URL endpoint and API key.
 * @param {string} apiEndpoint API endpoint to use for the scan
 * @param {string} apiKey API authorization key to use for the scan
 * @param {{Bucket: string, Key: string}} s3Object S3 object to tag
 * @param {string} awsAccountId AWS account ID to use for the scan
 * @param {string} snsArn ARN of the SNS topic to publish scan results to
 * @param {string} requestId Request ID of the scan
 * @returns {Response} Axios response from the scan request
 */
const startS3ObjectScan = async (apiEndpoint, apiKey, s3Object, awsAccountId, snsArn, requestId) => {
  try {
    logger.info(`S3 scan starting for: ${util.inspect(s3Object)}`);
    const response = await axios.post(
      apiEndpoint,
      {
        aws_account: awsAccountId,
        s3_key: `s3://${s3Object.Bucket}/${s3Object.Key}`,
        sns_arn: snsArn,
      },
      {
        headers: {
          Accept: "application/json",
          Authorization: apiKey,
          "X-Scanning-Request-Id": requestId,
        },
      },
    );
    logger.info(`S3 scan response ${response.status}: ${util.inspect(response.data)}`);
    return response;
  } catch (error) {
    logger.error(`Could not start scan for ${util.inspect(s3Object)}: ${util.inspect(error)}`);
    return error.response;
  }
};

/**
 * Tags the S3 object with the provided tags.
 * @param {S3Client} s3Client AWS SDK S3 client used to tag the object
 * @param {{Bucket: string, Key: string}} s3Object S3 object to tag
 * @param {Array<{Key: string, Value: string}>} tags Array of Key/Value pairs to tag the S3 object with
 */
const tagS3Object = async (s3Client, s3Object, tags) => {
  const tagging = {
    Tagging: {
      TagSet: tags,
    },
  };
  let isSuccess = false;

  try {
    logger.info(`Tag S3 object starting: ${util.inspect(s3Object)} tags: ${util.inspect(tags)}`);
    const command = new PutObjectTaggingCommand({ ...s3Object, ...tagging });
    const response = await s3Client.send(command);
    isSuccess = response.$metadata && response.$metadata.httpStatusCode === 200;
    logger.info(`Tag S3 object response: ${util.inspect(response)}`);
  } catch (error) {
    logger.error(`Failed to tag S3 object: ${error}`);
  }

  return isSuccess;
};

// Helpers for testing
exports.helpers = {
  getEventAttribute,
  getRecordEventSource,
  getRoleCredentials,
  getS3Client,
  getS3ObjectFromRecord,
  initConfig,
  isS3Folder,
  parseS3Url,
  processEventRecords,
  startS3ObjectScan,
  tagS3Object,
};
