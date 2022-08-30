resource "aws_cloudwatch_dashboard" "ops" {
  dashboard_name = "Ops"
  dashboard_body = data.template_file.ops_dashboard.rendered
}

data "template_file" "ops_dashboard" {
  template = file("${path.module}/dashboards/ops.json")
  vars = {
    account_id                     = var.account_id
    api_cloudfront_distribution_id = var.api_cloudfront_distribution_id
    health_check_id                = var.route53_health_check_api_id
  }
}
