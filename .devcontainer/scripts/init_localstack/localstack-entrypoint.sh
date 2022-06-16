#!/usr/bin/env bash

printf "Configuring localstack components..."
sleep 5;

function laws {
  aws --endpoint-url=http://localstack:4566 --region=ca-central-1 "$@"
}

set -x

printf "Setting Connection Info..."
laws configure set aws_access_key_id foo
laws configure set aws_secret_access_key bar
laws configure set region ca-central-1
laws configure set output json

printf "Creating bucket..."
laws s3api create-bucket \
    --bucket clamav-defs \
    --region ca-central-1 \
    --create-bucket-configuration LocationConstraint=ca-central-1

set +x
