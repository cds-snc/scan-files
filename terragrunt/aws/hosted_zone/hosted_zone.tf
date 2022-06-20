resource "aws_route53_zone" "scan_files" {
  name = var.domain

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
