#!/bin/bash
#
# Generate and upload files to an S3 bucket that is setup with the s3_scan_object
# module.  Then, check that each file has been scanned and has an av-checksum tag.
#
set -euo pipefail

BUCKET_NAME="$1"
DATA="some text or cat a file" # Adjust to change file size (larger files = higher load)
FILES=10                       # Adjust to increase load on the API
FOLDER="$(date '+%Y-%m-%d@%H:%M')"

echo "⚡ Starting async scan test with $FILES files"
SECONDS=0

# Create the test files
mkdir -p ./test
for N in $(seq $FILES); do
    echo "{\"$N $FOLDER\": $DATA}" > ./test/file."$N".json   
done

# Upload them to the bucket
echo "Uploading test files to s3://$BUCKET_NAME/$FOLDER"
aws s3 sync ./test s3://"$BUCKET_NAME"/"$FOLDER"

# Get the scan status for each file
for N in $(seq $FILES); do
    COUNTER=0
    echo -n "Checking scan status for file.$N.json "
    while true; do
        CHECKSUM="$(aws s3api get-object-tagging --bucket "$BUCKET_NAME" --key "$FOLDER/file.$N.json" --output text | grep 'av-checksum' || true)"
        if [ "$CHECKSUM" != "" ]; then
            echo -e "\n✅ Async scan completed for file.$N.json: $CHECKSUM"
            break
        fi
        COUNTER=$((COUNTER+1))
        if [ $COUNTER -gt 160 ]; then
            echo -e "\n💩 Async scan timed out for file.$N.json..."
            exit 1
        fi
        echo -n "."
        sleep 3
    done
done

DURATION=$SECONDS
echo "🎉 All done in $((DURATION / 60))m $((DURATION % 60))s."
rm -rf ./test
