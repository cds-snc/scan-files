resource "aws_dynamodb_table" "scan-locktable" {
  attribute {
    name = "LockName"
    type = "S"
  }

  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockName"
  name         = var.locktable_name

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = "false"
  }

  read_capacity  = "0"
  stream_enabled = "false"
  write_capacity = "0"

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_dynamodb_table" "completed-scans" {
  attribute {
    name = "EXECUTION_ID"
    type = "S"
  }

  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "EXECUTION_ID"
  name         = "completed-scans"

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = "false"
  }

  read_capacity  = "0"
  stream_enabled = "false"
  write_capacity = "0"

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
