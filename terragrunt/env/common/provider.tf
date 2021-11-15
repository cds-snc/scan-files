provider "aws" {
  region              = var.region
  allowed_account_ids = [var.account_id]

  default_tags {
    tags = {
      CostCentre = var.billing_code
      Terraform  = "True"
    }
  }
}
