"use strict";

const axios = require("axios");
const { mockClient } = require("aws-sdk-client-mock");
const { S3Client, PutObjectTaggingCommand } = require("@aws-sdk/client-s3");
const { SecretsManagerClient, GetSecretValueCommand } = require("@aws-sdk/client-secrets-manager");

const mockS3Client = mockClient(S3Client);
const mockSecretManagerClient = mockClient(SecretsManagerClient);
mockSecretManagerClient.on(GetSecretValueCommand).resolves({
  SecretString: "someSuperSecretValue",
});

const { handler, helpers } = require("./app.js");
const {
  getRecordEventSource,
  getS3ObjectFromRecord,
  initConfig,
  parseS3Url,
  startS3ObjectScan,
  tagS3Object,
} = helpers;

jest.mock("axios");
global.console = {
  ...console,
  error: jest.fn(),
  info: jest.fn(),
};

const TEST_TIME = new Date(1978, 3, 30).getTime();
beforeAll(() => {
  jest.useFakeTimers().setSystemTime(TEST_TIME);
});

beforeEach(() => {
  jest.resetAllMocks();
  mockS3Client.reset();
  mockSecretManagerClient.reset();
});

describe("handler", () => {
  test("records success", async () => {
    const event = {
      Records: [
        {
          eventSource: "aws:s3",
          s3: {
            bucket: { name: "foo" },
            object: { key: "bar" },
          },
        },
        {
          EventSource: "aws:sns",
          Sns: {
            MessageAttributes: {
              "av-filepath": { Value: "s3://bam/baz" },
              "av-status": { Value: "SPIFY" },
            },
          },
        },
      ],
    };
    const expectedResponse = {
      status: 200,
      body: "Event records processesed: 2, Errors: 0",
    };

    axios.post.mockResolvedValue({ status: 200 });
    mockS3Client.on(PutObjectTaggingCommand).resolves({ VersionId: "yeet" });

    const response = await handler(event);
    expect(response).toEqual(expectedResponse);
    expect(mockS3Client).toHaveReceivedNthCommandWith(1, PutObjectTaggingCommand, {
      Bucket: "foo",
      Key: "bar",
      Tagging: {
        TagSet: [
          { Key: "av-scanner", Value: "clamav" },
          { Key: "av-status", Value: "in_progress" },
          { Key: "av-timestamp", Value: TEST_TIME },
        ],
      },
    });
    expect(mockS3Client).toHaveReceivedNthCommandWith(2, PutObjectTaggingCommand, {
      Bucket: "bam",
      Key: "baz",
      Tagging: {
        TagSet: [
          { Key: "av-scanner", Value: "clamav" },
          { Key: "av-status", Value: "SPIFY" },
          { Key: "av-timestamp", Value: TEST_TIME },
        ],
      },
    });
  });

  test("records failed, failed to start", async () => {
    const event = {
      Records: [
        {
          eventSource: "aws:s3",
          s3: {
            bucket: { name: "foo" },
            object: { key: "bar" },
          },
        },
      ],
    };
    const expectedResponse = {
      status: 422,
      body: "Event records processesed: 1, Errors: 1",
    };

    axios.post.mockResolvedValue({ status: 500 });
    mockS3Client.on(PutObjectTaggingCommand).resolves({ VersionId: "yeet" });

    const response = await handler(event);
    expect(response).toEqual(expectedResponse);
    expect(mockS3Client).toHaveReceivedNthCommandWith(1, PutObjectTaggingCommand, {
      Bucket: "foo",
      Key: "bar",
      Tagging: {
        TagSet: [
          { Key: "av-scanner", Value: "clamav" },
          { Key: "av-status", Value: "failed_to_start" },
          { Key: "av-timestamp", Value: TEST_TIME },
        ],
      },
    });
  });

  test("records failed, undefined reponse", async () => {
    const event = {
      Records: [
        {
          eventSource: "aws:s3",
          s3: {
            bucket: { name: "foo" },
            object: { key: "bar" },
          },
        },
      ],
    };
    const expectedResponse = {
      status: 422,
      body: "Event records processesed: 1, Errors: 1",
    };

    axios.post.mockResolvedValue(undefined);
    mockS3Client.on(PutObjectTaggingCommand).resolves({ VersionId: "yeet" });

    const response = await handler(event);
    expect(response).toEqual(expectedResponse);
    expect(mockS3Client).toHaveReceivedNthCommandWith(1, PutObjectTaggingCommand, {
      Bucket: "foo",
      Key: "bar",
      Tagging: {
        TagSet: [
          { Key: "av-scanner", Value: "clamav" },
          { Key: "av-status", Value: "failed_to_start" },
          { Key: "av-timestamp", Value: TEST_TIME },
        ],
      },
    });
  });

  test("records failed, invalid event source", async () => {
    const event = {
      Records: [
        {
          eventSource: "muffins",
        },
      ],
    };
    const expectedResponse = {
      status: 422,
      body: "Event records processesed: 1, Errors: 1",
    };

    axios.post.mockResolvedValue({ status: 200 });
    mockS3Client.on(PutObjectTaggingCommand).resolves({ VersionId: "yeet" });

    const response = await handler(event);
    expect(response).toEqual(expectedResponse);
  });
});

describe("getRecordEventSource", () => {
  test("valid event sources", () => {
    expect(getRecordEventSource({ eventSource: "aws:s3" })).toBe("aws:s3");
    expect(getRecordEventSource({ EventSource: "aws:sns" })).toBe("aws:sns");
  });

  test("invalid event sources", () => {
    expect(getRecordEventSource({ eventSource: "aws:s3:ca-central-1" })).toBe(null);
    expect(getRecordEventSource({ EventSource: "aws:s3" })).toBe(null);
    expect(getRecordEventSource({ eventSource: "aws:sns" })).toBe(null);
    expect(getRecordEventSource({ eventSource: "pohtaytoes" })).toBe(null);
    expect(getRecordEventSource({})).toBe(null);
  });
});

describe("getS3ObjectFromRecord", () => {
  test("s3 event", () => {
    const record = {
      s3: {
        bucket: {
          name: "foo",
        },
        object: {
          key: encodeURIComponent("some-folder-path/this is the file name"),
        },
      },
    };
    const expected = {
      Bucket: "foo",
      Key: "some-folder-path/this is the file name",
    };
    expect(getS3ObjectFromRecord("aws:s3", record)).toEqual(expected);
  });

  test("sns event", () => {
    const record = {
      Sns: {
        MessageAttributes: {
          "av-filepath": {
            Value: "s3://bar/bam",
          },
        },
      },
    };
    const expected = {
      Bucket: "bar",
      Key: "bam",
    };
    expect(getS3ObjectFromRecord("aws:sns", record)).toEqual(expected);
  });

  test("sns event, invalid av-filepath", () => {
    const record = {
      Sns: {
        MessageAttributes: {
          "av-filepath": {
            Value: "file:///some.gif",
          },
        },
      },
    };
    expect(getS3ObjectFromRecord("aws:sns", record)).toBe(null);
  });

  test("invalid event", () => {
    expect(getS3ObjectFromRecord("muffins", {})).toBe(null);
  });
});

describe("initConfig", () => {
  test("retrieves the config value", async () => {
    mockSecretManagerClient.on(GetSecretValueCommand).resolvesOnce({
      SecretString: "anotherEquallySecretValue",
    });

    const config = await initConfig();
    expect(config).toEqual({ apiKey: "anotherEquallySecretValue" });
  });

  test("throws an error on failure", async () => {
    mockSecretManagerClient.on(GetSecretValueCommand).rejectsOnce(new Error("nope"));
    await expect(initConfig()).rejects.toThrow("nope");
  });
});

describe("parseS3Url", () => {
  test("successful parse", async () => {
    expect(parseS3Url("s3://foo/bar")).toEqual({ Bucket: "foo", Key: "bar" });
    expect(parseS3Url("s3://the-spice-must-flow/bar/bam/baz/bing.png")).toEqual({
      Bucket: "the-spice-must-flow",
      Key: "bar/bam/baz/bing.png",
    });
  });

  test("unsuccessful parse", async () => {
    expect(parseS3Url(undefined)).toBe(null);
    expect(parseS3Url(null)).toBe(null);
    expect(parseS3Url("")).toBe(null);
    expect(parseS3Url("s3://foo")).toBe(null);
  });
});

describe("startS3ObjectScan", () => {
  test("starts a scan", async () => {
    axios.post.mockResolvedValueOnce({ status: 200 });
    const response = await startS3ObjectScan(
      "http://somedomain.com",
      "someSuperSecretValue",
      {
        Bucket: "foo",
        Key: "bar",
      },
      "123456789012",
      "someSnsTopicArn"
    );
    expect(response).toEqual({ status: 200 });
    expect(axios.post.mock.calls[0]).toEqual([
      "http://somedomain.com",
      {
        aws_account: "123456789012",
        s3_key: "s3://foo/bar",
        sns_arn: "someSnsTopicArn",
      },
      {
        headers: {
          Accept: "application/json",
          Authorization: "someSuperSecretValue",
        },
      },
    ]);
  });

  test("fails to start a scan", async () => {
    axios.post.mockRejectedValueOnce({ response: { status: 500 } });
    const response = await startS3ObjectScan(
      "http://somedomain.com",
      "someSuperSecretValue",
      {
        Bucket: "foo",
        Key: "bar",
      },
      "123456789012",
      "someSnsTopicArn"
    );
    expect(response).toEqual({ status: 500 });
  });
});

describe("tagS3Object", () => {
  test("successfully tags", async () => {
    mockS3Client.on(PutObjectTaggingCommand).resolvesOnce({ VersionId: "yeet" });
    const input = {
      Bucket: "foo",
      Key: "bar",
      Tagging: {
        TagSet: [{ Key: "some-tag", Value: "some-value" }],
      },
    };
    const response = await tagS3Object(mockS3Client, { Bucket: "foo", Key: "bar" }, [
      { Key: "some-tag", Value: "some-value" },
    ]);
    expect(response).toBe(true);
    expect(mockS3Client).toHaveReceivedCommandWith(PutObjectTaggingCommand, input);
  });

  test("fails to tag", async () => {
    mockS3Client.on(PutObjectTaggingCommand).resolvesOnce({});
    const response = await tagS3Object(mockS3Client, {}, []);
    expect(response).toBe(false);
  });
});
