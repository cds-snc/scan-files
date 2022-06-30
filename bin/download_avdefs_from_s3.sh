#!/bin/bash

mkdir -p /workspace/api/clamav_defs

aws s3api get-object --region ca-central-1 --bucket scan-files-production-clamav-defs --key clamav_defs/bytecode.cvd /workspace/api/clamav_defs/bytecode.cvd > /dev/null 2>&1
aws s3api get-object --region ca-central-1 --bucket scan-files-production-clamav-defs --key clamav_defs/daily.cld /workspace/api/clamav_defs/daily.cld > /dev/null 2>&1
aws s3api get-object --region ca-central-1 --bucket scan-files-production-clamav-defs --key clamav_defs/daily.cvd /workspace/api/clamav_defs/daily.cvd > /dev/null 2>&1
aws s3api get-object --region ca-central-1 --bucket scan-files-production-clamav-defs --key clamav_defs/main.cvd /workspace/api/clamav_defs/main.cvd > /dev/null 2>&1

cp -r /workspace/api/clamav_defs/* /clamav