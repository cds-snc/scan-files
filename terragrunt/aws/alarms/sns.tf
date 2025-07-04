#
# SNS: topic & subscription
#
resource "aws_sns_topic" "cloudwatch_warning" {
  name              = "cloudwatch-alarms-warning"
  kms_master_key_id = aws_kms_key.sns_cloudwatch.id
}

resource "aws_sns_topic_subscription" "alert_warning" {
  topic_arn = aws_sns_topic.cloudwatch_warning.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}

resource "aws_sns_topic" "cloudwatch_warning_us_east" {
  provider          = aws.us-east-1
  name              = "cloudwatch-alarms-warning"
  kms_master_key_id = aws_kms_key.sns_cloudwatch_us_east.id
}

resource "aws_sns_topic_subscription" "alert_warning_us_east" {
  provider  = aws.us-east-1
  topic_arn = aws_sns_topic.cloudwatch_warning_us_east.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}

#
# KMS: SNS topic encryption keys
# A CMK is required so we can apply a policy that allows CloudWatch to use it
#
resource "aws_kms_key" "sns_cloudwatch" {
  # checkov:skip=CKV_AWS_7: key rotation not required for CloudWatch SNS topic's messages
  description = "KMS key for CloudWatch SNS topic"
  policy      = data.aws_iam_policy_document.sns_cloudwatch.json
}

resource "aws_kms_key" "sns_cloudwatch_us_east" {
  # checkov:skip=CKV_AWS_7: key rotation not required for CloudWatch SNS topic's messages
  provider = aws.us-east-1

  description = "KMS key for CloudWatch SNS topic in US east"
  policy      = data.aws_iam_policy_document.sns_cloudwatch.json
}

data "aws_iam_policy_document" "sns_cloudwatch" {
  # checkov:skip=CKV_AWS_109: `resources = ["*"]` identifies the KMS key to which the key policy is attached
  # checkov:skip=CKV_AWS_111: `resources = ["*"]` identifies the KMS key to which the key policy is attached
  statement {
    effect    = "Allow"
    resources = ["*"]
    actions   = ["kms:*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"]
    }
  }

  statement {
    effect    = "Allow"
    resources = ["*"]
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*",
    ]

    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
  }
}