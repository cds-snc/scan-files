terraform {
  source = "git::https://github.com/cds-snc/scan-files//terragrunt/aws/integration_test?ref=${get_env("INFRASTRUCTURE_VERSION")}"
}

include {
  path = find_in_parent_folders("root.hcl")
}
