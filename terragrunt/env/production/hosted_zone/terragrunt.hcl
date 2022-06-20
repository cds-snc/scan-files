terraform {
  source = "../../../aws//hosted_zone"
}

inputs = {
  hosted_zone_name = "scan-files.alpha.canada.ca"
}

include {
  path = find_in_parent_folders()
}
