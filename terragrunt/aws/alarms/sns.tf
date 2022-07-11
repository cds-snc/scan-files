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
