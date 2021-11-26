#!/bin/bash

echo hitting api healthcheck endpoint
curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{
    "resource": "/",
    "path": "/healthcheck",
    "requestContext": {},
    "httpMethod": "GET",
    "headers": {},
    "multiValueHeaders": { },
    "queryStringParameters": null,
    "multiValueQueryStringParameters": null,
    "pathParameters": null,
    "stageVariables": null,
    "body": null,
    "isBase64Encoded": false
}' |jq
