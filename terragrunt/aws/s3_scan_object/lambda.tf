module "s3_scan_object" {
  source = "github.com/cds-snc/terraform-modules?ref=v3.0.6//lambda"

  name      = "s3-scan-object"
  image_uri = "${aws_ecr_repository.s3_scan_object.repository_url}:latest"
  ecr_arn   = aws_ecr_repository.s3_scan_object.arn
  memory    = 512
  timeout   = 60

  reserved_concurrent_executions = 3

  environment_variables = {
    SCAN_FILES_URL                = "https://${var.domain}"
    SCAN_FILES_API_KEY_SECRET_ARN = var.scan_files_api_key_secret_arn
    SNS_SCAN_COMPLETE_TOPIC_ARN   = aws_sns_topic.scan_complete.arn
  }

  policies = [
    data.aws_iam_policy_document.s3_scan_object.json,
    sensitive(data.aws_iam_policy_document.assume_cross_account.json)
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
      test     = "StringEquals"
      values   = [var.aws_org_id]
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
