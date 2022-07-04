resource "aws_route53_record" "scan_files_A" {
  zone_id = var.hosted_zone_id
  name    = var.domain
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.scan_files_api.domain_name
    zone_id                = aws_cloudfront_distribution.scan_files_api.hosted_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_health_check" "scan_files_A" {
  fqdn              = aws_route53_record.scan_files_A.fqdn
  port              = 443
  type              = "HTTPS"
  resource_path     = "/healthcheck"
  failure_threshold = "5"
  request_interval  = "60"

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
