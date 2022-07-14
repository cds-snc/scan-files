#!/bin/bash

base64_encoded_file_upload=$(cat file_upload_payload)
echo hitting api clamav endpoint
curl "http://api:8080/2015-03-31/functions/function/invocations" -d '{
    "resource": "/",
    "path": "/clamav",
    "requestContext": {},
    "httpMethod": "POST",
    "headers": {"authorization": "123", "content-length": "7713", "content-type": "multipart/form-data; boundary=--------------------------733922910553358931761280", "accept-encoding": "gzip, deflate, br"},
    "multiValueHeaders": { },
    "queryStringParameters": {"ignore_cache": "true"},
    "multiValueQueryStringParameters": null,
    "pathParameters": null,
    "stageVariables": null,
    "body": "'"$base64_encoded_file_upload"'",
    "isBase64Encoded": "True"
}' |jq