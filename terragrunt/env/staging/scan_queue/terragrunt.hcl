terraform {
  source = "../../../aws//scan_queue"
}

dependencies {
  paths = ["../api"]
}

dependency "api" {
  config_path = "../api"

  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    api_function_arn  = "arn:aws:lambda:ca-central-1:127893201980:function:scan-files-api"
    api_function_name = "scan-files-api"
  }
}

inputs = {
  concurrent_scan_limit  = 5
  api_function_arn       = dependency.api.outputs.api_function_arn
  api_function_name      = dependency.api.outputs.api_function_name
}

include {
  path = find_in_parent_folders("root.hcl")
}