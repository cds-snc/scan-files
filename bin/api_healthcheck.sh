#!/bin/bash

echo hitting api healthcheck endpoint
curl "http://api:8080/2015-03-31/functions/function/invocations" -d '{
    "resource": "/",
    "path": "/healthcheck",
    "requestContext": {},
    "httpMethod": "GET",
    "headers": {"x-scanning-request-id": "bar"},
    "multiValueHeaders": { },
    "queryStringParameters": null,
    "multiValueQueryStringParameters": null,
    "pathParameters": null,
    "stageVariables": null,
    "body": null,
    "isBase64Encoded": false
}' |jq
