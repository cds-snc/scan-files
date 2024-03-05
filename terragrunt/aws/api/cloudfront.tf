resource "aws_cloudfront_distribution" "scan_files" {
  for_each = toset(local.scan_files_api_functions)

  enabled     = true
  aliases     = [each.key == "api-provisioned" ? "sync.${var.domain}" : var.domain]
  price_class = "PriceClass_100"
  web_acl_id  = aws_wafv2_web_acl.api_waf.arn

  origin {
    domain_name = split("/", aws_lambda_function_url.scan_files[each.key].function_url)[2]
    origin_id   = aws_lambda_function_url.scan_files[each.key].function_name

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_read_timeout    = 60
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  default_cache_behavior {
    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = ["Authorization"]
      cookies {
        forward = "none"
      }
    }

    target_origin_id           = aws_lambda_function_url.scan_files[each.key].function_name
    viewer_protocol_policy     = "redirect-to-https"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers_policy_api.id
  }

  # Prevent caching of healthcheck calls
  ordered_cache_behavior {
    path_pattern    = "/healthcheck"
    allowed_methods = ["GET", "HEAD"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }

    target_origin_id           = aws_lambda_function_url.scan_files[each.key].function_name
    viewer_protocol_policy     = "redirect-to-https"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers_policy_api.id

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
    compress    = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.scan_files_certificate_validation.certificate_arn
    minimum_protocol_version = "TLSv1.2_2021"
    ssl_support_method       = "sni-only"
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

resource "aws_cloudfront_response_headers_policy" "security_headers_policy_api" {
  name = "scan-files-security-headers-api"

  security_headers_config {
    frame_options {
      frame_option = "DENY"
      override     = true
    }
    content_type_options {
      override = true
    }
    content_security_policy {
      content_security_policy = "report-uri https://csp-report-to.security.cdssandbox.xyz/report; default-src 'none'; script-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self'; frame-ancestors 'self'; form-action 'self';"
      override                = false
    }
    referrer_policy {
      override        = true
      referrer_policy = "same-origin"
    }
    strict_transport_security {
      override                   = true
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
    }
    xss_protection {
      override   = true
      mode_block = true
      protection = true
    }
  }
}
