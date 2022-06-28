resource "aws_cloudfront_distribution" "scan_files_api" {
  enabled     = true
  price_class = "PriceClass_100"
  web_acl_id  = aws_wafv2_web_acl.api_waf.id

  origin {
    domain_name = split("/", aws_lambda_function_url.scan_files_url.function_url)[2]
    origin_id   = aws_lambda_function_url.scan_files_url.function_name

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  default_cache_behavior {
    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods  = ["GET", "HEAD"]
    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }

    target_origin_id       = aws_lambda_function_url.scan_files_url.function_name
    viewer_protocol_policy = "redirect-to-https"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn            = aws_acm_certificate_validation.scan_files_certificate_validation.certificate_arn
    cloudfront_default_certificate = false
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  logging_config {
    include_cookies = false
    bucket          = module.log_bucket.s3_bucket_domain_name
    prefix          = "cloudfront"
  }

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
