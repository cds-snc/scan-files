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
    function_name                 = ""
    function_role_arn             = ""
    scan_files_api_key_secret_arn = ""
  }
}

inputs = {
  scan_files_api_function_role_arn  = dependency.api.outputs.function_role_arn
  scan_files_api_function_role_name = dependency.api.outputs.function_name
  scan_files_api_key_secret_arn     = dependency.api.outputs.scan_files_api_key_secret_arn
}

include {
  path = find_in_parent_folders()
}
