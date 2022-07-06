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
