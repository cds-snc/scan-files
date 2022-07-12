module "integration_test" {
  source = "github.com/cds-snc/terraform-modules?ref=v3.0.9//S3_scan_object"

  product_name          = "integration-test"
  s3_upload_bucket_name = module.integration_test_bucket.s3_bucket_id

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
