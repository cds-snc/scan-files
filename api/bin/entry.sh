#!/bin/sh
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    echo "Running aws-lambda-rie"
    exec find . -name "*.py" | entr -r /usr/bin/aws-lambda-rie /usr/local/bin/python -m awslambdaric "$1"
else
    echo "Retrieving environment parameters"
    ENV_PATH="/tmp/scanfiles"
    mkdir "$ENV_PATH"
    export DOTENV_PATH="$ENV_PATH"
    aws ssm get-parameters --region ca-central-1 --with-decryption --names ENVIRONMENT_VARIABLES --query 'Parameters[*].Value' --output text > "$ENV_PATH/.env"
    exec /usr/local/bin/python -m awslambdaric "$1"
fi