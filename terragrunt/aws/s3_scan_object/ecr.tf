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
    (var.billing_tag_key) = var.billing_tag_value
    Terraform             = "true"
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
  statement {
    sid    = "AllowLambdaPull"
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
