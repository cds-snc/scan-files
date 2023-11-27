#!/bin/sh
# shellcheck disable=SC2120

ENV_PATH="/tmp/scanfiles"
TMP_ENV_FILE="$ENV_PATH/.env"

var_expand() {
  if [ -z "${1-}" ] || [ $# -ne 1 ]; then
    printf 'var_expand: expected one argument\n' >&2;
    return 1;
  fi
  eval printf '%s' "\"\${$1?}\"" 2> /dev/null # Variable double substitution to be able to check for variable
}

load_non_existing_envs() {
  _isComment='^[[:space:]]*#'
  _isBlank='^[[:space:]]*$'
  while IFS= read -r line || [ -n "$line" ]; do
    if echo "$line" | grep -Eq "$_isComment"; then # Ignore comment line
      continue
    fi
    if echo "$line" | grep -Eq "$_isBlank"; then # Ignore blank line
      continue
    fi
    key=$(echo "$line" | cut -d '=' -f 1)
    value=$(echo "$line" | cut -d '=' -f 2-)

    if [ -z "$(var_expand "$key")" ]; then # Check if environment variable doesn't exist
      export "${key}=${value}"
    fi
    
  done < $TMP_ENV_FILE
}

# Local testing
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
  echo "INFO Running aws-lambda-rie"
  exec /usr/bin/aws-lambda-rie /usr/local/bin/python -m awslambdaric "$1"

# Running in AWS Lambda
else
    if [ ! -f "$ENV_PATH/.env" ]; then # Only setup envs once per lambda lifecycle
      echo "INFO Retrieving environment parameters"
      if [ ! -d "$ENV_PATH" ]; then
        mkdir "$ENV_PATH"
      fi

      # Retrieve secrets and write them to the .env file
      ENV_VARS="$(aws ssm get-parameters --region ca-central-1 --with-decryption --names ENVIRONMENT_VARIABLES --query 'Parameters[*].Value' --output text)"
      if [ -z "$ENV_VARS" ]; then
        echo "ERROR Failed to retrieve secrets during init"
        exit 1
      else
        echo "$ENV_VARS" > "$TMP_ENV_FILE"
      fi
    fi

    # Check if the tmp .env file has content
    if [ ! -s "$TMP_ENV_FILE" ]; then
      echo "ERROR .env file does not have content"
      rm "$TMP_ENV_FILE"
      exit 1
    fi    
    load_non_existing_envs

    echo "INFO Starting lambda handler"
    exec /usr/local/bin/python -m awslambdaric "$1"
fi