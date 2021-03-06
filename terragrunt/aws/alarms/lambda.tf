module "cloudwatch_alarms_slack" {
  source = "github.com/cds-snc/terraform-modules?ref=v3.0.9//notify_slack"

  function_name     = "cloudwatch-alarms-slack"
  project_name      = var.product_name
  slack_webhook_url = var.slack_webhook_url
  sns_topic_arns = [
    aws_sns_topic.cloudwatch_warning.arn,
    aws_sns_topic.cloudwatch_warning_us_east.arn
  ]

  billing_tag_value = var.billing_code
}
