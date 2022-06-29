"use strict";

/**
 * Lambda function that can be invoked by S3 events or SNS messages.
 * This function triggers a scan of newly created S3 objects or updates
 * the scan status of existing S3 objects based on an SNS message payload.
 */

const axios = require("axios");
const util = require("util");
const { S3Client, PutObjectTaggingCommand } = require("@aws-sdk/client-s3");
const { SecretsManagerClient, GetSecretValueCommand } = require("@aws-sdk/client-secrets-manager");

const AWS_ACCOUNT_ID = process.env.AWS_ACCOUNT_ID;
const REGION = process.env.REGION;
const ENDPOINT_URL = process.env.AWS_SAM_LOCAL ? "http://host.docker.internal:3001" : undefined;
const SCAN_FILES_URL = process.env.SCAN_FILES_URL;
const SCAN_FILES_API_KEY_SECRET_ARN = process.env.SCAN_FILES_API_KEY_SECRET_ARN;
const SCAN_IN_PROGRESS = "in_progress";
const SCAN_FAILED_TO_START = "failed_to_start";
const SNS_SCAN_COMPLETE_TOPIC_ARN = process.env.SNS_SCAN_COMPLETE_TOPIC_ARN;
const EVENT_S3 = "aws:s3";
const EVENT_SNS = "aws:sns";

const s3Client = new S3Client({ region: REGION, endpoint: ENDPOINT_URL });
const secretsManagerClient = new SecretsManagerClient({ region: REGION, endpoint: ENDPOINT_URL });

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
      console.error(`Unable to get '${SCAN_FILES_API_KEY_SECRET_ARN}' secret: ${error}`);
      throw error;
    }
  })();
};

// Start config load on cold starts. This can switch to a top level `await` if we switch to ES modules:
// https://aws.amazon.com/blogs/compute/using-node-js-es-modules-and-top-level-await-in-aws-lambda/
const configPromise = initConfig();

/**
 * Lambda handler function.  This function is invoked when a new S3 object is
 * created in response to `s3:ObjectCreated:*` events or when an SNS message
 * is received with an update scan status.
 * @param {Object} event Lambda invocation event
 */
exports.handler = async (event) => {
  const config = await configPromise;
  let errorCount = 0;

  // Process all event records
  for (const record of event.Records) {
    let scanStatus = null;
    let isObjectTagged = false;
    let eventSource = getRecordEventSource(record);
    let s3Object = getS3ObjectFromRecord(eventSource, record);

    // Start a scan of the new S3 object
    if (eventSource !== null && s3Object !== null) {
      if (eventSource === EVENT_S3) {
        const response = await startS3ObjectScan(
          `${SCAN_FILES_URL}/clamav/s3`,
          config.apiKey,
          s3Object,
          AWS_ACCOUNT_ID,
          SNS_SCAN_COMPLETE_TOPIC_ARN
        );
        scanStatus =
          response !== undefined && response.status === 200
            ? SCAN_IN_PROGRESS
            : SCAN_FAILED_TO_START;

        // Get the scan status for an existing S3 object
      } else if (eventSource === EVENT_SNS) {
        scanStatus = record.Sns.MessageAttributes["av-status"].Value;
      }
    } else {
      console.error(`Unsupported event record: ${util.inspect(record)}`);
    }

    // Tag the S3 object if we've got a scan status
    if (scanStatus !== null) {
      isObjectTagged = await tagS3Object(s3Client, s3Object, [
        { Key: "av-scanner", Value: "clamav" },
        { Key: "av-status", Value: scanStatus },
        { Key: "av-timestamp", Value: new Date().getTime() },
      ]);
    }

    // Track if there were any errors processing this record
    if (scanStatus === SCAN_FAILED_TO_START || isObjectTagged === false) {
      errorCount++;
    }
  }

  return {
    status: errorCount > 0 ? 422 : 200,
    body: `Event records processesed: ${event.Records.length}, Errors: ${errorCount}`,
  };
};

/**
 * Determines the event record's source service.  This is either S3 or SNS.
 * @param {Object} record Lambda invocation event record
 * @returns {String} Event record source service, or `null` if not valid
 */
const getRecordEventSource = (record) => {
  let eventSource = null;

  if (record.eventSource === EVENT_S3) {
    eventSource = EVENT_S3;
  } else if (record.EventSource === EVENT_SNS) {
    eventSource = EVENT_SNS;
  }

  return eventSource;
};

/**
 * Retrieves the S3 object's Bucket and key from the Lambda invocation event.
 * @param {String} eventSource The source of the event record
 * @param {Object} record Lambda invocation event record
 * @returns {{Bucket: string, Key: string}} S3 object bucket and key
 */
const getS3ObjectFromRecord = (eventSource, record) => {
  let s3Object = null;

  if (eventSource === EVENT_S3) {
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
 * Given an S3 object URL, parses the URL and returns the S3 object's bucket and key.
 * @param {String} url S3 object URL in format `s3://bucket/key`
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
 * @param {String} apiEndpoint API endpoint to use for the scan
 * @param {String} apiKey API authorization key to use for the scan
 * @param {{Bucket: string, Key: string}} s3Object S3 object to tag
 * @param {String} awsAccountId AWS account ID to use for the scan
 * @param {String} snsArn ARN of the SNS topic to publish scan results to
 * @returns {Response} Axios response from the scan request
 */
const startS3ObjectScan = async (apiEndpoint, apiKey, s3Object, awsAccountId, snsArn) => {
  try {
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
        },
      }
    );
    console.info(`Scan response ${response.status}: ${util.inspect(response.data)}`);
    return response;
  } catch (error) {
    console.error(
      `Could not start scan for ${util.inspect(s3Object)}: ${util.inspect(error.response)}`
    );
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
    const command = new PutObjectTaggingCommand({ ...s3Object, ...tagging });
    const response = await s3Client.send(command);
    isSuccess = response.VersionId !== undefined;
  } catch (error) {
    console.error(`Failed to tag S3 object: ${error}`);
  }

  return isSuccess;
};

// Helpers for testing
exports.helpers = {
  getRecordEventSource,
  getS3ObjectFromRecord,
  initConfig,
  parseS3Url,
  startS3ObjectScan,
  tagS3Object,
};
