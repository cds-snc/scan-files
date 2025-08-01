locals {
  name_prefix     = "${var.product_name}-${var.env}"
  file_queue_name = "${local.name_prefix}-file-queue"
  clamav-defs     = "${local.name_prefix}-clamav-defs"
}

module "log_bucket" {
  source             = "github.com/cds-snc/terraform-modules//S3_log_bucket?ref=v10.6.2"
  bucket_name        = "${var.product_name}-${var.env}-logs"
  critical_tag_value = false
  versioning_status  = "Suspended"
  billing_tag_value  = var.billing_code
}

module "file-queue" {
  source      = "github.com/cds-snc/terraform-modules//S3?ref=v10.6.2"
  bucket_name = local.file_queue_name
  lifecycle_rule = [{
    id      = "expire"
    enabled = true
    expiration = {
      days = 7
    }
  }]
  billing_tag_value = var.billing_code
  logging = {
    "target_bucket" = module.log_bucket.s3_bucket_id
    "target_prefix" = local.file_queue_name
  }
}

module "clamav-defs" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v10.6.2"
  bucket_name       = local.clamav-defs
  billing_tag_value = var.billing_code
  logging = {
    "target_bucket" = module.log_bucket.s3_bucket_id
    "target_prefix" = local.clamav-defs
  }
}
