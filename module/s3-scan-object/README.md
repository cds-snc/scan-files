# S3 scan object
Lambda function that triggers a ClamAV scan of newly created S3 objects and updates the object with the scan results.  The scan process and verdict is communicated via S3 object tags.

# Events
The function can be invoked by S3, SNS and custom events.

## S3 object create
Subscribe to `s3:ObjectCreated:*` events so that the function is invoked when a new S3 object is uploaded to a bucket.  This will cause the S3 object to be scanned using the ClamAV endpoint.

## SNS message published to a topic
Once the scan is complete, a message is published to an SNS topic the function is subscribed to.  This will cause the function to update the S3 object with the scan verdict.

## Custom recan
This custom event is used to trigger a ClamAV scan of an existing S3 object and follows the same process as the scan used for new S3 objects.  The event payload has the following structure:
```javascript
{
    "Records": [{
        "eventSource": "custom:rescan",
        "s3ObjectUrl": "s3://your-bucket-name/the-file.png"
    }]
}
```

# Infrastructure
The infrastructure required can be built using the [S3_scan_object](https://github.com/cds-snc/terraform-modules/tree/main/S3_scan_object) Terraform module.

## Development
```sh
yarn install       # Install dependencies
yarn test          # Run unit tests (Jest)
yarn lint          # Lint the code (eslint)
yarn format:write  # Format the code (prettier)
```