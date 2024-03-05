locals {
  api_role_arn             = "arn:aws:iam::${var.account_id}:role/${var.product_name}-api"
  cbs_satellite_bucket_arn = "arn:aws:s3:::${var.cbs_satellite_bucket_name}"
  scan_files_api_functions = ["api", "api-provisioned"]
}
