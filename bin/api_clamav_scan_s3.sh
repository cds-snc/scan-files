#!/bin/bash

echo hitting api healthcheck endpoint
curl "http://api:8080/2015-03-31/functions/function/invocations" -d '{
    "resource": "/",
    "path": "/clamav/s3",
    "requestContext": {},
    "httpMethod": "POST",
    "headers": {"Authorization": "123"},
    "multiValueHeaders": { },
    "queryStringParameters": null,
    "multiValueQueryStringParameters": null,
    "pathParameters": null,
    "stageVariables": null,
    "body": "{\"aws_account\": \"123456789012\",\"sns_arn\": \"arn:aws:sns:ca-central-1:123456789012:s3-object-scan-complete\",\"s3_key\": \"s3://s3-scan-object-upload-bucket-mntest/Architecture.JPG\"}",
    "isBase64Encoded": false
}' |jq
