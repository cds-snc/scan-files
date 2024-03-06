terraform {
  source = "git::https://github.com/cds-snc/scan-files//terragrunt/aws/alarms?ref=${get_env("INFRASTRUCTURE_VERSION")}"
}

dependencies {
  paths = ["../hosted_zone", "../api", "../s3_scan_object"]
}

dependency "hosted_zone" {
  config_path = "../hosted_zone"

  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    hosted_zone_id = ""
  }
}

dependency "api" {
  config_path = "../api"

  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    api_cloudfront_distribution_id      = "api-cloudfront-distribution-id"
    api_sync_cloudfront_distribution_id = "api-provisioned-cloudfront-distribution-id"
    api_function_log_group_name         = "/aws/lambda/scan-files-api"
    api_sync_function_log_group_name    = "/aws/lambda/scan-files-api-provisioned"
    route53_health_check_api_id         = ""
  }
}

dependency "s3_scan_object" {
  config_path = "../s3_scan_object"

  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    function_log_group_name = "/aws/lambda/s3-scan-object"
  }
}

inputs = {
  route53_hosted_zone_id = dependency.hosted_zone.outputs.hosted_zone_id

  s3_scan_object_log_group_name       = dependency.s3_scan_object.outputs.function_log_group_name
  scan_files_api_log_group_name       = dependency.api.outputs.api_function_log_group_name
  scan_files_api_sync_log_group_name  = dependency.api.outputs.api_sync_function_log_group_name
  route53_health_check_api_id         = dependency.api.outputs.route53_health_check_api_id
  api_cloudfront_distribution_id      = dependency.api.outputs.api_cloudfront_distribution_id
  api_sync_cloudfront_distribution_id = dependency.api.outputs.api_sync_cloudfront_distribution_id

  s3_scan_object_error_threshold                = "1"
  scan_files_api_error_threshold                = "1"
  scan_files_api_warning_threshold              = "5"
  scan_files_api_scan_verdict_unknown_threshold = "1"
}

include {
  path = find_in_parent_folders()
}
