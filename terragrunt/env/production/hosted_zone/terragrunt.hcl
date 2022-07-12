terraform {
  source = "git::https://github.com/cds-snc/scan-files//terragrunt/aws/hosted_zone?ref=${get_env("INFRASTRUCTURE_VERSION")}"
}

include {
  path = find_in_parent_folders()
}
