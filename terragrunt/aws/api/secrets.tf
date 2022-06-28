resource "aws_secretsmanager_secret" "api_auth_token" {
  name       = "/scan-files/api_auth_token"
  kms_key_id = aws_kms_key.scan_files.arn

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_secretsmanager_secret_version" "api_auth_token" {
  secret_id     = aws_secretsmanager_secret.api_auth_token.id
  secret_string = var.api_auth_token
}

#
# Allow cross-account access to the API auth token for AWS accounts
# that are part of our Organization.
#
resource "aws_secretsmanager_secret_policy" "api_auth_token" {
  secret_arn = aws_secretsmanager_secret.api_auth_token.arn
  policy     = sensitive(data.aws_iam_policy_document.api_auth_token.json)
}

data "aws_iam_policy_document" "api_auth_token" {
  statement {
    sid       = "AccountOwnerFullAdmin"
    effect    = "Allow"
    resources = ["*"]
    actions   = ["secretsmanager:*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"]
    }
  }

  statement {
    sid       = "CrossAccountS3ScanObject"
    effect    = "Allow"
    resources = ["*"]
    actions   = ["secretsmanager:GetSecretValue"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    condition {
      test     = "ArnLike"
      values   = ["arn:aws:iam::*:role/s3-scan-object-*"]
      variable = "aws:PrincipalArn"
    }

    condition {
      test     = "StringEquals"
      values   = [var.aws_org_id]
      variable = "aws:PrincipalOrgID"
    }
  }
}
