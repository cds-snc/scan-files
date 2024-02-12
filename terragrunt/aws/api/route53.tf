resource "aws_route53_record" "scan_files_A" {
  zone_id = var.hosted_zone_id
  name    = var.domain
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.scan_files_api.domain_name
    zone_id                = aws_cloudfront_distribution.scan_files_api.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_health_check" "scan_files_A" {
  fqdn              = aws_route53_record.scan_files_A.fqdn
  port              = 443
  type              = "HTTPS"
  resource_path     = "/healthcheck"
  failure_threshold = "5"
  request_interval  = "30"
  regions           = ["us-east-1", "us-west-1", "us-west-2"]

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

#
# Route53 DNS logging and query firewall
#
module "resolver_dns" {
  source           = "github.com/cds-snc/terraform-modules//resolver_dns?ref=v9.0.6"
  vpc_id           = module.vpc.vpc_id
  firewall_enabled = true

  allowed_domains = [
    "*.amazonaws.com.",
    "*.cyber.gc.ca.",
    "current.cvd.clamav.net.",
    "database.clamav.net.",
    "database.clamav.net.cdn.cloudflare.net."
  ]

  billing_tag_value = var.billing_code
}
