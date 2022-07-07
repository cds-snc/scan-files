resource "aws_iam_policy" "api_sns_publish" {
  name   = "${var.product_name}-sns-publish"
  path   = "/"
  policy = data.aws_iam_policy_document.api_sns_publish.json

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

data "aws_iam_policy_document" "api_sns_publish" {
  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*",
    ]
    resources = [
      aws_kms_key.sns_lambda.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "sns:Publish",
    ]
    resources = [
      aws_sns_topic.scan_complete.arn
    ]
  }
}

resource "aws_iam_role_policy_attachment" "api_sns_publish" {
  role       = var.scan_files_api_function_role_name
  policy_arn = aws_iam_policy.api_sns_publish.arn
}
