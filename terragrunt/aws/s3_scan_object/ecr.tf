#
# S3 object scan lambda Docker image
#
resource "aws_ecr_repository" "s3_scan_object" {
  name                 = "${var.product_name}/module/s3-scan-object"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    CostCentre = var.billing_code
    Terraform  = "true"
  }
}

#
# Allow the lambda service in the same organization
# to pull the Docker image
#
resource "aws_ecr_repository_policy" "s3_scan_object" {
  repository = aws_ecr_repository.s3_scan_object.name
  policy     = sensitive(data.aws_iam_policy_document.s3_scan_object.json)
}

data "aws_iam_policy_document" "s3_scan_object" {
  # Allow Lambda service calls to pull the image for matching function ARNs.  Although
  # this gives the Lambda service access to pull the image for any function with a 
  # matching ARN, the `AllowAccountPull` statement prevents the creation of the 
  # function unless the account is part of our Organization.  As a result, this
  # effectively limits the Lambda service to only functions in our Organization.
  statement {
    sid    = "AllowServicePull"
    effect = "Allow"

    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer"
    ]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    condition {
      test     = "ArnLike"
      values   = ["arn:aws:lambda:${var.region}:*:function:s3-scan-object-*"]
      variable = "aws:SourceArn"
    }
  }

  # Allow any principal that is part of our AWS org to pull the image
  statement {
    sid    = "AllowAccountPull"
    effect = "Allow"

    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer"
    ]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    condition {
      test     = "StringEquals"
      values   = [var.aws_org_id]
      variable = "aws:PrincipalOrgID"
    }
  }
}
