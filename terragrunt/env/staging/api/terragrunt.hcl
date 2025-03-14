terraform {
  source = "../../../aws//api"
}

dependencies {
  paths = ["../hosted_zone"]
}

dependency "hosted_zone" {
  config_path = "../hosted_zone"

  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs = {
    hosted_zone_id = ""
  }
}

inputs = {
  enable_waf     = true
  rds_username   = "databaseuser"
  hosted_zone_id = dependency.hosted_zone.outputs.hosted_zone_id
  oidc_exists    = true
}

include {
  path = find_in_parent_folders("root.hcl")
}