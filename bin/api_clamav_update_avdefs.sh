#!/bin/bash 

echo hitting api clamav virus def update endpoint
curl "http://api:8080/2015-03-31/functions/function/invocations" -d '{
  "task": "clamav_update_virus_defs"
}' |jq
