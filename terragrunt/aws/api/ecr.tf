resource "aws_ecr_repository" "api" {
  name                 = "${var.product_name}/api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  lifecycle {
    ignore_changes = [
      # Ignore changes to tags since tags are being updated by Github workflow
      # to track virus definition hashes.
      tags,
    ]
    prevent_destroy = true
  }

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_ecr_lifecycle_policy" "scan_files_exire_untagged" {
  repository = aws_ecr_repository.api.name
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
