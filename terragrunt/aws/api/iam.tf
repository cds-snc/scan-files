data "aws_iam_policy_document" "api_policies" {

  statement {

    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      "arn:aws:logs:${var.region}:${var.account_id}:log-group:*"
    ]
  }

  statement {

    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:ListBucketVersions",
      "s3:GetBucketLocation",
      "s3:Get*",
      "s3:Put*"
    ]
    resources = [
      module.file-queue.s3_bucket_arn,
      "${module.file-queue.s3_bucket_arn}/*",
      module.clamav-defs.s3_bucket_arn,
      "${module.clamav-defs.s3_bucket_arn}/*",
    ]
  }

  statement {

    effect = "Allow"

    actions = [
      "states:ListStateMachines",
      "states:ListActivities",
      "states:CreateActivity",
      "states:DescribeExecution",
      "states:StopExecution"
    ]

    resources = [
      "arn:aws:states:${var.region}:${var.account_id}:*"
    ]
  }

  statement {

    effect = "Allow"

    actions = [
      "states:StartExecution",

    ]

    resources = [
      "arn:aws:states:${var.region}:${var.account_id}:stateMachine:${var.scan_queue_statemachine_name}"
    ]
  }

  statement {

    effect = "Allow"

    actions = [
      "events:PutTargets",
      "events:PutRule",
      "events:DescribeRule"
    ]

    resources = [
      "arn:aws:events:${var.region}:${var.account_id}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule"
    ]
  }

  statement {

    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:DeleteItem",
      "dynamodb:PutItem",
    ]

    resources = [
      "arn:aws:dynamodb:${var.region}:${var.account_id}:table/${var.locktable_name}",
      "arn:aws:dynamodb:${var.region}:${var.account_id}:table/${var.completed_scans_table_name}"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameters",
    ]
    resources = [
      "arn:aws:ssm:${var.region}:${var.account_id}:parameter/ENVIRONMENT_VARIABLES"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      module.api.function_arn
    ]
  }
}

data "aws_iam_policy_document" "api_get_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      aws_secretsmanager_secret_version.api_auth_token.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
    ]
    resources = [
      aws_kms_key.scan-files.arn
    ]
  }
}

#
# Allow API to assume cross-account S3/SNS scan role
#
data "aws_iam_policy_document" "api_assume_cross_account" {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]
    resources = [
      "arn:aws:iam::*:role/ScanFilesGetObjects"
    ]
    condition {
      test     = "StringEquals"
      values   = [var.aws_org_id]
      variable = "aws:PrincipalOrgID"
    }
  }
}

resource "aws_iam_role" "waf_log_role" {
  name               = "${var.product_name}-logs"
  assume_role_policy = data.aws_iam_policy_document.firehose_assume_role.json

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_iam_policy" "write_waf_logs" {
  name        = "${var.product_name}_WriteLogs"
  description = "Allow writing WAF logs to S3 + CloudWatch"
  policy      = data.aws_iam_policy_document.write_waf_logs.json

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_iam_role_policy_attachment" "write_waf_logs" {
  role       = aws_iam_role.waf_log_role.name
  policy_arn = aws_iam_policy.write_waf_logs.arn
}

data "aws_iam_policy_document" "firehose_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["firehose.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "write_waf_logs" {
  statement {
    effect = "Allow"

    actions = [
      "s3:ListBucket",
    ]

    resources = [
      local.cbs_satellite_bucket_arn
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject*",
      "s3:PutObject*",
    ]

    resources = [
      "${local.cbs_satellite_bucket_arn}/waf_acl_logs/*"
    ]
  }
}
