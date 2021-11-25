module "api" {
  source                   = "github.com/cds-snc/terraform-modules?ref=v0.0.45//lambda"
  name                     = "api"
  billing_tag_value        = var.billing_code
  allow_api_gateway_invoke = true
  api_gateway_source_arn   = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
  ecr_arn                  = aws_ecr_repository.api.arn
  enable_lambda_insights   = true
  image_uri                = "${aws_ecr_repository.api.repository_url}:latest"
  vpc = {
    security_group_ids = [module.rds.proxy_security_group_id, aws_security_group.api.id]
    subnet_ids         = module.vpc.private_subnet_ids
  }

  environment_variables = {
    API_AUTH_TOKEN               = var.api_auth_token
    SQLALCHEMY_DATABASE_URI      = module.rds.proxy_connection_string_value
    MLWR_HOST                    = var.mlwr_host
    MLWR_USER                    = var.mlwr_user
    MLWR_KEY                     = var.mlwr_key
    FILE_QUEUE_BUCKET            = module.file-queue.s3_bucket_id
    SCAN_QUEUE_STATEMACHINE_NAME = var.scan_queue_statemachine_name
    COMPLETED_SCANS_TABLE_NAME   = var.completed_scans_table_name
  }

  policies = [
    data.aws_iam_policy_document.api_policies.json,
  ]
}
