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
# Route53 DNS logging
#
resource "aws_cloudwatch_log_group" "route53_vpc_dns" {
  name              = "/aws/route53/${module.vpc.vpc_id}"
  retention_in_days = 14
}

data "aws_iam_policy_document" "route53_resolver_logging_policy" {
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    principals {
      identifiers = ["route53.amazonaws.com"]
      type        = "Service"
    }

    resources = [
      "${aws_cloudwatch_log_group.route53_vpc_dns.arn}/*"
    ]
  }
}

resource "aws_cloudwatch_log_resource_policy" "route53_vpc_dns" {
  policy_document = data.aws_iam_policy_document.route53_resolver_logging_policy.json
  policy_name     = "route53_resolver_logging_policy"
}

resource "aws_route53_resolver_query_log_config" "route53_vpc_dns" {
  name            = "route53_vpc_dns"
  destination_arn = aws_cloudwatch_log_group.route53_vpc_dns.arn
}

resource "aws_route53_resolver_query_log_config_association" "route53_vpc_dns" {
  resolver_query_log_config_id = aws_route53_resolver_query_log_config.route53_vpc_dns.id
  resource_id                  = module.vpc.vpc_id
}

#
# Resolve DNS firewall to only allow DNS queries to the `allowed` domains
# and block all other queries
#
resource "aws_route53_resolver_firewall_domain_list" "allowed" {
  name = "AllowedDomains"
  domains = [
    "*.cyber.gc.ca",
    "*.${var.region}.rds.amazonaws.com",
    "*.s3.${var.region}.amazonaws.com",
    "current.cvd.clamav.net",
    "database.clamav.net",
    "lambda.${var.region}.amazonaws.com",
    "secretsmanager.${var.region}.amazonaws.com",
    "sns.${var.region}.amazonaws.com",
    "ssm.${var.region}.amazonaws.com",
    "sts.amazonaws.com"
  ]

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_route53_resolver_firewall_domain_list" "blocked" {
  name    = "BlockedDomains"
  domains = ["*"]

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_route53_resolver_firewall_rule_group" "api_rules" {
  name = "ApiRules"

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_route53_resolver_firewall_rule" "allowed" {
  name                    = "AllowedDomains"
  action                  = "ALLOW"
  firewall_domain_list_id = aws_route53_resolver_firewall_domain_list.allowed.id
  firewall_rule_group_id  = aws_route53_resolver_firewall_rule_group.api_rules.id
  priority                = 100
}

resource "aws_route53_resolver_firewall_rule" "blocked" {
  name                    = "BlockedDomains"
  action                  = "BLOCK"
  block_response          = "NODATA"
  firewall_domain_list_id = aws_route53_resolver_firewall_domain_list.blocked.id
  firewall_rule_group_id  = aws_route53_resolver_firewall_rule_group.api_rules.id
  priority                = 200
}

resource "aws_route53_resolver_firewall_rule_group_association" "api_rules" {
  name                   = "ApiRules"
  firewall_rule_group_id = aws_route53_resolver_firewall_rule_group.api_rules.id
  priority               = 101
  vpc_id                 = module.vpc.vpc_id
}
