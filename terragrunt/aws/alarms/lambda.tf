module "cloudwatch_alarms_slack" {
  source = "github.com/cds-snc/terraform-modules?ref=v3.0.9//notify_slack"

  function_name     = "cloudwatch-alarms-slack"
  project_name      = var.product_name
  slack_webhook_url = var.slack_webhook_url
  sns_topic_arns = [
    aws_sns_topic.warning.arn,
    aws_sns_topic.warning_us_east.arn
  ]

  billing_tag_value = var.billing_code
}

#
# SNS: topic & subscription
#
resource "aws_sns_topic" "cloudwatch_warning" {
  # checkov:skip=CKV_AWS_26: encryption-at-rest not required for alarm topic
  name = "cloudwatch-alarms-warning"
}

resource "aws_sns_topic_subscription" "alert_warning" {
  topic_arn = aws_sns_topic.cloudwatch_warning.arn
  protocol  = "lambda"
  endpoint  = module.cloudwatch_alarms_slack.lambda_arn
}

resource "aws_sns_topic" "cloudwatch_warning_us_east" {
  # checkov:skip=CKV_AWS_26: encryption-at-rest not required for alarm topic
  provider = aws.us-east-1
  name     = "cloudwatch-alarms-warning"
}

resource "aws_sns_topic_subscription" "alert_warning_us_east" {
  provider  = aws.us-east-1
  topic_arn = aws_sns_topic.cloudwatch_warning_us_east.arn
  protocol  = "lambda"
  endpoint  = module.cloudwatch_alarms_slack.lambda_arn
}
