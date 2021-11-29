resource "aws_route53_zone" "scan_files" {
  name = var.hosted_zone_name

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
