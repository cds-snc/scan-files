module "s3_scan_object" {
  source = "github.com/cds-snc/terraform-modules//lambda?ref=v9.6.8"

  name      = "s3-scan-object"
  image_uri = "${aws_ecr_repository.s3_scan_object.repository_url}:latest"
  ecr_arn   = aws_ecr_repository.s3_scan_object.arn
  memory    = 512
  timeout   = 300

  environment_variables = {
    AWS_MAX_ATTEMPTS              = "5"
    AWS_RETRY_MODE                = "standard"
    LOGGING_LEVEL                 = "info"
    SCAN_FILES_URL                = var.scan_files_api_function_url
    SCAN_FILES_API_KEY_SECRET_ARN = var.scan_files_api_key_secret_arn
    SNS_SCAN_COMPLETE_TOPIC_ARN   = aws_sns_topic.scan_complete.arn
  }

  policies = [
    data.aws_iam_policy_document.s3_scan_object.json,
    sensitive(data.aws_iam_policy_document.assume_cross_account.json),
    sensitive(data.aws_iam_policy_document.sqs_s3_events.json),
  ]

  billing_tag_value = var.billing_code
}

#
# Lambda IAM policies
#
data "aws_iam_policy_document" "s3_scan_object" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      var.scan_files_api_key_secret_arn
    ]
  }
}

data "aws_iam_policy_document" "assume_cross_account" {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]
    resources = [
      "arn:aws:iam::*:role/ScanFilesGetObjects"
    ]
    condition {
      test     = "ForAnyValue:StringEquals"
      values   = [var.aws_org_id, var.aws_org_id_old]
      variable = "aws:PrincipalOrgID"
    }
  }
}

data "aws_iam_policy_document" "sqs_s3_events" {
  statement {
    sid    = "SqsKmsKeyDecrypt"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*",
      "kms:DescribeKey"
    ]
    resources = [
      "*"
    ]
    condition {
      test     = "ForAnyValue:StringLike"
      values   = ["alias/s3_scan_object_queue"]
      variable = "kms:ResourceAliases"
    }
    condition {
      test     = "ForAnyValue:StringEquals"
      values   = [var.aws_org_id, var.aws_org_id_old]
      variable = "aws:PrincipalOrgID"
    }
  }

  # checkov:skip=CKV_AWS_111:cross-account delete is restricted to within our org
  statement {
    sid    = "SqsQueueGetEvent"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
    ]
    resources = [
      "arn:aws:sqs:${var.region}:*:s3-scan-object"
    ]
    condition {
      test     = "ForAnyValue:StringEquals"
      values   = [var.aws_org_id, var.aws_org_id_old]
      variable = "aws:PrincipalOrgID"
    }
  }
}

resource "aws_lambda_permission" "s3_scan_object_org_account_execute" {
  statement_id     = "AllowExecutionFromOrgAccounts"
  action           = "lambda:InvokeFunction"
  function_name    = module.s3_scan_object.function_name
  principal        = "*"
  principal_org_id = var.aws_org_id
}

resource "aws_lambda_event_source_mapping" "sqs_s3_events" {
  for_each         = var.sqs_event_accounts
  event_source_arn = "arn:aws:sqs:${var.region}:${each.key}:s3-scan-object"
  function_name    = module.s3_scan_object.function_arn
}
