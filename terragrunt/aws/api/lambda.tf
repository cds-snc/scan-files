module "api" {
  source                 = "github.com/cds-snc/terraform-modules?ref=v0.0.45//lambda"
  name                   = "${var.product_name}-api"
  billing_tag_value      = var.billing_code
  ecr_arn                = aws_ecr_repository.api.arn
  enable_lambda_insights = true
  image_uri              = "${aws_ecr_repository.api.repository_url}:latest"
  memory                 = 1536
  timeout                = 300

  vpc = {
    security_group_ids = [module.rds.proxy_security_group_id, aws_security_group.api.id]
    subnet_ids         = module.vpc.private_subnet_ids
  }

  environment_variables = {
    SQLALCHEMY_DATABASE_URI = module.rds.proxy_connection_string_value
    FILE_QUEUE_BUCKET       = module.file-queue.s3_bucket_id
    API_AUTH_TOKEN_SSM_NAME = aws_ssm_parameter.api_auth_token.name
  }

  policies = [
    data.aws_iam_policy_document.api_policies.json,
    sensitive(data.aws_iam_policy_document.api_assume_cross_account.json)
  ]
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.api.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.assemblyline_rescan_every_24_hours.arn
}

# Rescan stale files every 24 hours
resource "aws_cloudwatch_event_rule" "assemblyline_rescan_every_24_hours" {
  name                = "retry-stale-scans-${var.env}"
  description         = "Fires every 24 hours"
  schedule_expression = "cron(0 0 * * ? *)"

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_cloudwatch_event_target" "trigger_api_lambda_to_rescan" {
  rule      = aws_cloudwatch_event_rule.assemblyline_rescan_every_24_hours.name
  target_id = "${var.product_name}-${var.env}-assemblyline-stale-scan-resubmitter"
  arn       = module.api.function_arn
  input     = jsonencode({ task = "assemblyline_resubmit_stale" })
}

# Update ClamAV virus database every 2 hours
resource "aws_cloudwatch_event_rule" "clamav_update_avdefs" {
  name                = "clamav-update-avdefs-${var.env}"
  description         = "Updates ClamAV virus database every 2 hours"
  schedule_expression = "rate(2 hours)"

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_cloudwatch_event_target" "trigger_api_lambda_to_download_clamav_defs" {
  rule      = aws_cloudwatch_event_rule.clamav_update_avdefs.name
  target_id = "${var.product_name}-${var.env}-clamav-update-avdefs"
  arn       = module.api.function_arn
  input     = jsonencode({ task = "clamav_update_virus_defs" })
}

resource "aws_lambda_function_url" "scan_files_url" {
  # checkov:skip=CKV_AWS_258: Lambda function url auth is handled at the API level
  function_name      = module.api.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    max_age           = 86400
  }
}
