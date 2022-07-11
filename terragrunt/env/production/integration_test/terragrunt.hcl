terraform {
  source = "../../../aws//integration_test"
}

include {
  path = find_in_parent_folders()
}
