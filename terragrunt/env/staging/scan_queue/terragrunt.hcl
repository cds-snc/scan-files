terraform {
  source = "../../../aws//scan_queue"
}

dependencies {
  paths = ["../api"]
}

dependency "api" {
  config_path = "../api"

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    function_arn  = ""
    function_name = ""
  }
}

inputs = {
  concurrent_scan_limit  = 5
  retry_interval_seconds = 120
  api_function_arn       = dependency.api.outputs.function_arn
  api_function_name      = dependency.api.outputs.function_name
}

include {
  path = find_in_parent_folders()
}