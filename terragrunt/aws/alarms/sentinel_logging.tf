locals {
  scan_verdict_suspicious_arn = "arn:aws:logs:${var.region}:${var.account_id}:log-group:${var.scan_files_api_log_group_name}"
}

module "sentinel_forwarder" {
  source            = "github.com/cds-snc/terraform-modules?ref=v4.0.2//sentinel_forwarder"
  function_name     = "sentinel-cloud-watch-forwarder"
  billing_tag_value = var.billing_code

  customer_id = var.sentinel_customer_id
  shared_key  = var.sentinel_shared_key

  cloudwatch_log_arns = [locals.scan_verdict_suspicious_arn]
}


resource "aws_cloudwatch_log_subscription_filter" "scan_verdict_suspicious" {
  name            = local.scan_verdict_suspicious
  log_group_name  = var.scan_files_api_log_group_name
  filter_pattern  = "?suspicious ?malicious ?unknown ?unable_to_scan"
  destination_arn = module.sentinel_forwarder.lambda_arn
  distribution    = "Random"
}
