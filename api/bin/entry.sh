#!/bin/sh
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    echo "Running aws-lambda-rie"
    exec find . -name "*.py" | entr -r /usr/bin/aws-lambda-rie /usr/local/bin/python -m awslambdaric "$1"
else
    echo "Retrieving environment parameters"
    aws ssm get-parameters --region ca-central-1 --with-decryption --names ENVIRONMENT_VARIABLES --query 'Parameters[*].Value' --output text > ".env"
    exec /usr/local/bin/python -m awslambdaric "$1"
fi