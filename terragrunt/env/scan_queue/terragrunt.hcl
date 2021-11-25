terraform {
  source = "../../aws//scan_queue"
}

dependencies {
  paths = ["../api"]
}

dependency "api" {
  config_path = "../api"

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  concurrent_scan_limit = 10
  api_function_arn      = dependency.api.outputs.function_arn
  api_function_name     = dependency.api.outputs.function_name
}

include {
  path = find_in_parent_folders()
}