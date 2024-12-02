module "scan_files" {
  for_each = toset(local.scan_files_api_functions)

  source                 = "github.com/cds-snc/terraform-modules//lambda?ref=v10.1.0"
  name                   = "${var.product_name}-${each.key}"
  billing_tag_value      = var.billing_code
  ecr_arn                = aws_ecr_repository.api.arn
  enable_lambda_insights = true
  image_uri              = "${aws_ecr_repository.api.repository_url}:latest"
  memory                 = 3008
  timeout                = 300
  ephemeral_storage      = 768
  publish                = each.key == "api-provisioned"

  vpc = {
    security_group_ids = [module.rds.proxy_security_group_id, aws_security_group.api.id]
    subnet_ids         = module.vpc.private_subnet_ids
  }

  environment_variables = {
    API_AUTH_TOKEN_SECRET_ARN    = aws_secretsmanager_secret.api_auth_token.id
    AV_DEFINITION_S3_BUCKET      = "${var.product_name}-${var.env}-clamav-defs"
    AV_SCAN_USE_CACHE            = "False"
    AWS_MAX_ATTEMPTS             = "5"
    AWS_RETRY_MODE               = "standard"
    COMPLETED_SCANS_TABLE_NAME   = "completed-scans"
    FILE_CHECKSUM_TABLE_NAME     = "file-checksums"
    FILE_QUEUE_BUCKET            = module.file-queue.s3_bucket_id
    LOG_LEVEL                    = "INFO"
    OPENAPI_URL                  = "/openapi.json"
    POWERTOOLS_SERVICE_NAME      = "${var.product_name}-api"
    SCAN_QUEUE_STATEMACHINE_NAME = "assemblyline-file-scan-queue"
    SQLALCHEMY_DATABASE_URI      = module.rds.proxy_connection_string_value
  }

  policies = [
    data.aws_iam_policy_document.api_policies.json,
    data.aws_iam_policy_document.api_get_secrets.json,
    sensitive(data.aws_iam_policy_document.api_assume_cross_account.json)
  ]
}

# Rescan stale files every 24 hours

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.scan_files["api"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.assemblyline_rescan_every_24_hours.arn
}

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
  arn       = module.scan_files["api"].function_arn
  input     = jsonencode({ task = "assemblyline_resubmit_stale" })
}

# Update ClamAV virus database every 2 hours

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda_for_update_clamav" {
  statement_id  = "AllowExecutionFromCloudWatchForVirusDefs"
  action        = "lambda:InvokeFunction"
  function_name = module.scan_files["api"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.clamav_update_avdefs.arn
}

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
  arn       = module.scan_files["api"].function_arn
  input     = jsonencode({ task = "clamav_update_virus_defs" })
}

resource "aws_lambda_function_url" "scan_files" {
  # checkov:skip=CKV_AWS_258: Lambda function url auth is handled at the API level
  for_each = toset(local.scan_files_api_functions)

  function_name      = module.scan_files[each.key].function_name
  authorization_type = "NONE"
  qualifier          = each.key == "api-provisioned" ? aws_lambda_alias.api_provisioned_latest.name : null
}

#
# Setup provisioned concurency for the api-provisioned lambda
# This function will be used for synchronous requests
#
resource "aws_lambda_alias" "api_provisioned_latest" {
  name             = "latest"
  description      = "The most recently deployed version of the API"
  function_name    = module.scan_files["api-provisioned"].function_arn
  function_version = module.scan_files["api-provisioned"].function_version
}

resource "aws_lambda_provisioned_concurrency_config" "api_provisioned" {
  function_name                     = module.scan_files["api-provisioned"].function_name
  provisioned_concurrent_executions = 1
  qualifier                         = aws_lambda_alias.api_provisioned_latest.name
}
