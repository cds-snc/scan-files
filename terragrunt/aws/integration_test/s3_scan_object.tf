module "integration_test" {
  source = "github.com/cds-snc/terraform-modules?ref=v3.0.10//S3_scan_object"

  product_name                = "integration-test"
  s3_upload_bucket_name       = module.integration_test_bucket.s3_bucket_id
  scan_files_role_arn         = "arn:aws:iam::${var.account_id}:role/scan-files-api"
  s3_scan_object_function_arn = "arn:aws:lambda:ca-central-1:${var.account_id}:function:s3-scan-object"
  s3_scan_object_role_arn     = "arn:aws:iam::${var.account_id}:role/s3-scan-object"

  billing_tag_value = var.billing_code
}

module "integration_test_bucket" {
  source            = "github.com/cds-snc/terraform-modules?ref=v3.0.9//S3"
  bucket_name       = "${var.product_name}-${var.env}-integration-test"
  billing_tag_value = var.billing_code

  lifecycle_rule = [
    {
      id      = "expire-objects-after-1-day"
      enabled = true
      expiration = {
        days                         = 1
        expired_object_delete_marker = false
      }
    },
  ]

  versioning = {
    enabled = true
  }
}
