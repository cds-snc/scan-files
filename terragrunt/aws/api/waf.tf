resource "aws_wafv2_web_acl" "api_waf" {
  provider = aws.us-east-1

  name        = "api_waf"
  description = "WAF for API protection"
  scope       = "CLOUDFRONT"

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }

  default_action {
    allow {}
  }

  rule {
    name     = "IpAllowList"
    priority = 1

    action {
      allow {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.ip_allowlist.arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "IpAllowList"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "NorthAmericaOnly"
    priority = 2

    action {
      dynamic "block" {
        for_each = var.enable_waf == true ? [""] : []
        content {
        }
      }

      dynamic "count" {
        for_each = var.enable_waf == false ? [""] : []
        content {
        }
      }
    }

    statement {
      not_statement {
        statement {
          geo_match_statement {
            country_codes = ["CA", "US"]
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "NorthAmericaOnly"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "APIInvalidPath"
    priority = 5

    action {
      dynamic "block" {
        for_each = var.enable_waf == true ? [""] : []
        content {
        }
      }

      dynamic "count" {
        for_each = var.enable_waf == false ? [""] : []
        content {
        }
      }
    }

    statement {
      not_statement {
        statement {
          regex_pattern_set_reference_statement {
            arn = aws_wafv2_regex_pattern_set.valid_uri_paths.arn
            field_to_match {
              uri_path {}
            }
            text_transformation {
              priority = 1
              type     = "COMPRESS_WHITE_SPACE"
            }
            text_transformation {
              priority = 2
              type     = "LOWERCASE"
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "APIInvalidPaths"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 10

    override_action {
      dynamic "none" {
        for_each = var.enable_waf == true ? [""] : []
        content {
        }
      }

      dynamic "count" {
        for_each = var.enable_waf == false ? [""] : []
        content {
        }
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesAmazonIpReputationList"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "APIRateLimit"
    priority = 20

    action {
      dynamic "block" {
        for_each = var.enable_waf == true ? [""] : []
        content {
        }
      }

      dynamic "count" {
        for_each = var.enable_waf == false ? [""] : []
        content {
        }
      }
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "APIRateLimit"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 30

    override_action {
      dynamic "none" {
        for_each = var.enable_waf == true ? [""] : []
        content {
        }
      }

      dynamic "count" {
        for_each = var.enable_waf == false ? [""] : []
        content {
        }
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        scope_down_statement {
          not_statement {
            statement {
              and_statement {
                statement {
                  regex_pattern_set_reference_statement {
                    arn = aws_wafv2_regex_pattern_set.body_exclusions.arn
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      type     = "LOWERCASE"
                      priority = 1
                    }
                  }
                }
                statement {
                  byte_match_statement {
                    search_string         = "post"
                    positional_constraint = "EXACTLY"
                    field_to_match {
                      method {}
                    }
                    text_transformation {
                      type     = "LOWERCASE"
                      priority = 1
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 40

    override_action {
      dynamic "none" {
        for_each = var.enable_waf == true ? [""] : []
        content {
        }
      }

      dynamic "count" {
        for_each = var.enable_waf == false ? [""] : []
        content {
        }
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"

        scope_down_statement {
          not_statement {
            statement {
              and_statement {
                statement {
                  regex_pattern_set_reference_statement {
                    arn = aws_wafv2_regex_pattern_set.body_exclusions.arn
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      type     = "LOWERCASE"
                      priority = 1
                    }
                  }
                }
                statement {
                  byte_match_statement {
                    search_string         = "post"
                    positional_constraint = "EXACTLY"
                    field_to_match {
                      method {}
                    }
                    text_transformation {
                      type     = "LOWERCASE"
                      priority = 1
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSet"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesLinuxRuleSet"
    priority = 50

    override_action {
      dynamic "none" {
        for_each = var.enable_waf == true ? [""] : []
        content {
        }
      }

      dynamic "count" {
        for_each = var.enable_waf == false ? [""] : []
        content {
        }
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesLinuxRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesLinuxRuleSet"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 60

    override_action {
      dynamic "none" {
        for_each = var.enable_waf == true ? [""] : []
        content {
        }
      }

      dynamic "count" {
        for_each = var.enable_waf == false ? [""] : []
        content {
        }
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSet"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "api"
    sampled_requests_enabled   = false
  }
}

resource "aws_wafv2_regex_pattern_set" "body_exclusions" {
  provider    = aws.us-east-1
  name        = "RequestBodyExclusions"
  description = "Regex to match request urls with bodies that will trigger rulesets"
  scope       = "CLOUDFRONT"

  regular_expression {
    regex_string = "^/(clamav|assemblyline)(/s3)?$"
  }

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_wafv2_regex_pattern_set" "valid_uri_paths" {
  provider    = aws.us-east-1
  name        = "ValidURIPaths"
  description = "Regex to match the APIs valid URI paths"
  scope       = "CLOUDFRONT"

  # ops
  regular_expression {
    regex_string = "^/(healthcheck|version|docs|openapi.json)$"
  }

  # assemblyline
  regular_expression {
    regex_string = "^/assemblyline(/[\\w]{8}-[\\w]{4}-[\\w]{4}-[\\w]{4}-[\\w]{12})?$"
  }

  # clamav
  regular_expression {
    regex_string = "^/clamav(/([\\w]{8}-[\\w]{4}-[\\w]{4}-[\\w]{4}-[\\w]{12}|s3))?$"
  }

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_cloudwatch_log_group" "api_waf" {
  name              = "/aws/kinesisfirehose/api_waf"
  retention_in_days = 14

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_kinesis_firehose_delivery_stream" "api_waf" {
  provider = aws.us-east-1

  name        = "aws-waf-logs-${var.product_name}"
  destination = "extended_s3"

  server_side_encryption {
    enabled = true
  }

  extended_s3_configuration {
    role_arn           = aws_iam_role.waf_log_role.arn
    prefix             = "waf_acl_logs/AWSLogs/${var.account_id}/"
    bucket_arn         = local.cbs_satellite_bucket_arn
    compression_format = "GZIP"

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.api_waf.name
      log_stream_name = "WAFLogS3Delivery"
    }
  }

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_wafv2_web_acl_logging_configuration" "api_waf" {
  provider                = aws.us-east-1
  log_destination_configs = [aws_kinesis_firehose_delivery_stream.api_waf.arn]
  resource_arn            = aws_wafv2_web_acl.api_waf.arn
}

# Azure US East CIDR blocks that are being identified as being in Germany
# These should be allowed.
resource "aws_wafv2_ip_set" "ip_allowlist" {
  provider = aws.us-east-1

  name               = "ip_allowlist"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"
  addresses = [
    "172.172.0.0/15",
    "172.174.0.0/16",
    "172.175.0.0/16",
    "172.176.0.0/15"
  ]
}
