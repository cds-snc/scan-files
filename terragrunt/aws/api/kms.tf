
data "aws_iam_policy_document" "kms_policies" {
  # checkov:skip=CKV_AWS_109: `resources=["*"]` references the key the policy is attached to
  # checkov:skip=CKV_AWS_111: `resources=["*"]` references the key the policy is attached to
  statement {

    effect = "Allow"

    actions = [
      "kms:*"
    ]

    resources = [
      "*"
    ]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"]
    }
  }
  statement {

    effect = "Allow"

    actions = [
      "kms:Encrypt*",
      "kms:Decrypt*",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*"
    ]

    resources = [
      "*"
    ]

    principals {
      type        = "Service"
      identifiers = ["logs.${var.region}.amazonaws.com"]
    }

    principals {
      type        = "Service"
      identifiers = ["secretsmanager.${var.region}.amazonaws.com"]
    }
  }

  statement {

    effect = "Allow"

    actions = [
      "kms:Decrypt*",
      "kms:GenerateDataKey*",
    ]

    resources = [
      "*"
    ]

    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
  }

  statement {

    sid = "APIRead"

    effect = "Allow"

    actions = [
      "kms:Decrypt"
    ]

    resources = [
      "*"
    ]

    principals {
      type        = "AWS"
      identifiers = [local.api_role_arn]
    }

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:role/s3-scan-object"]
    }
  }
}

resource "aws_kms_key" "scan-files" {
  description         = "KMS Key"
  enable_key_rotation = true

  policy = data.aws_iam_policy_document.kms_policies.json

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
