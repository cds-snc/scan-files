#
# Athena database and query to view
# WAF ACL access logs
#
resource "aws_athena_database" "logs" {
  name   = "scan_files_logs"
  bucket = module.athena_bucket.s3_bucket_id

  encryption_configuration {
    encryption_option = "SSE_S3"
  }
}

resource "aws_athena_workgroup" "primary" {
  name = "primary"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${module.athena_bucket.s3_bucket_id}"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }

  tags = {
    CostCentre = var.billing_code
    Terraform  = "true"
  }
}

resource "aws_athena_named_query" "create_table_waf_logs" {
  name      = "Create WAF table"
  workgroup = aws_athena_workgroup.primary.name
  database  = aws_athena_database.logs.name
  query = templatefile("${path.module}/sql/athena_create_waf_table.sql",
    {
      bucket_location = "s3://${var.cbs_satellite_bucket_name}/waf_acl_logs/AWSLogs/${var.account_id}/"
      database_name   = aws_athena_database.logs.name
      table_name      = "waf_logs"
    }
  )
}

#
# Hold the Athena data
#
module "athena_bucket" {
  source            = "github.com/cds-snc/terraform-modules?ref=v3.0.13//S3"
  bucket_name       = "${var.product_name}-${var.env}-athena-bucket"
  billing_tag_value = var.billing_code

  lifecycle_rule = [
    {
      id      = "expire-objects-after-7-days"
      enabled = true
      expiration = {
        days                         = 7
        expired_object_delete_marker = false
      }
    },
  ]
}
