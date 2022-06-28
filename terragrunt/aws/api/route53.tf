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
