terraform {
  source = "git::https://github.com/cds-snc/scan-files//terragrunt/aws/s3_scan_object?ref=${get_env("INFRASTRUCTURE_VERSION")}"
}

dependencies {
  paths = ["../api"]
}

dependency "api" {
  config_path = "../api"

  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    api_function_name             = "scan-files-api"
    api_function_role_arn         = "arn:aws:iam::806545929748:role/scan-files-api"
    api_function_url              = "http://localhost"
    scan_files_api_key_secret_arn = ""
  }
}

inputs = {
  scan_files_api_function_role_arn  = dependency.api.outputs.api_function_role_arn
  scan_files_api_function_role_name = dependency.api.outputs.api_function_name
  scan_files_api_function_url       = dependency.api.outputs.api_function_url
  scan_files_api_key_secret_arn     = dependency.api.outputs.scan_files_api_key_secret_arn

  sqs_event_accounts = [
    "296255494825", 
    "806545929748"
  ]
}

include {
  path = find_in_parent_folders("root.hcl")
}
