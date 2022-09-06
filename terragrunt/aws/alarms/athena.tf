#
# Hold the Athena data
#
module "athena_bucket" {
  source            = "github.com/cds-snc/terraform-modules?ref=v3.0.13//S3"
  bucket_name       = "${var.product_name}-${var.env}-athena-bucket"
  billing_tag_value = var.billing_code

  lifecycle_rule = [
    {
      id      = "expire-objects-after-7-days"
      enabled = true
      expiration = {
        days                         = 7
        expired_object_delete_marker = false
      }
    },
  ]
}
