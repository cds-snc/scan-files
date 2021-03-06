#!/bin/bash
# Note, this file isn't executed, it's sourced. So, skip strict bash commands in here
# as they'll terminate the shell.

echo "Sourcing migrate.sh"
function test_migrate_resp {
  if [[ $(cat "$1") =~ $(cat .github/workflows/scripts/expected_response.json) ]]; then
    echo "Migration Success"
    return 0
  fi
  echo "Migration Error"
  return 1
}

function migrate {
  aws lambda get-function \
    --function-name scan-files-api \
    --region ca-central-1 \
    --query 'Configuration.[State, LastUpdateStatus]' > status

  # Loop until ["Active","Successful"] vs {"LastUpdateStatus": "InProgress"}
  COUNTER=1
  while [[ $(jq < status '. | if type=="array" then true else false end') == "false" ]]
  do
    if [ $COUNTER -eq 12 ]; then
      echo "Migration error: Lambda ready state timeout after 120 seconds"
      break
    fi
    sleep 10
    aws lambda get-function \
      --function-name scan-files-api \
      --region ca-central-1 \
      --query 'Configuration.[State, LastUpdateStatus]' > status
    COUNTER=$((COUNTER+1))
  done

  aws lambda invoke \
    --function-name scan-files-api \
    --cli-binary-format raw-in-base64-out \
    --payload '{ "task": "migrate" }' \
    --region ca-central-1 \
    response
  test_migrate_resp response
}
