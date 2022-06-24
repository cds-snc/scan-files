terraform {
  source = "../../../aws//s3_scan_object"
}

include {
  path = find_in_parent_folders()
}
