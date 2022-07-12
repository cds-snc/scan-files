terraform {
  source = "git::https://github.com/cds-snc/scan-files//terragrunt/aws/alarms?ref=${get_env("INFRASTRUCTURE_VERSION")}"
}

dependencies {
  paths = ["../api"]
}

dependency "api" {
  config_path = "../api"

  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    route53_health_check_api_id = ""
  }
}

inputs = {
  route53_health_check_api_id = dependency.api.outputs.route53_health_check_api_id
}

include {
  path = find_in_parent_folders()
}
