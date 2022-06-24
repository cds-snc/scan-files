#
# S3 object scan lambda Docker image
#
resource "aws_ecr_repository" "s3_scan_object" {
  name                 = "s3-scan-object"
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
  # While this statement does allow for the Lambda service to pull the image in any AWS account
  # using a matching region and function name, there is no cost for ECR image pulls when
  # the image is not leaving the AWS network.
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
      values   = ["arn:aws:lambda:${var.region}:*:function:s3-scan-object"]
      variable = "aws:SourceArn"
    }
  }

  # Allow any user principal part of our AWS org to pull the image
  statement {
    sid    = "AllowUserPull"
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

resource "aws_ecr_lifecycle_policy" "s3_scan_object_exire_untagged" {
  repository = aws_ecr_repository.s3_scan_object.name
  policy = jsonencode({
    "rules" : [
      {
        "rulePriority" : 1,
        "description" : "Expire untagged images older than 14 days",
        "selection" : {
          "tagStatus" : "untagged",
          "countType" : "sinceImagePushed",
          "countUnit" : "days",
          "countNumber" : 14
        },
        "action" : {
          "type" : "expire"
        }
      }
    ]
  })
}
