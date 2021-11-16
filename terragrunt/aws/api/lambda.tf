module "api" {
  source                   = "github.com/cds-snc/terraform-modules?ref=v0.0.44//lambda"
  name                     = "api"
  billing_tag_value        = var.billing_code
  allow_api_gateway_invoke = true
  api_gateway_source_arn   = aws_api_gateway_rest_api.api.arn
  ecr_arn                  = aws_ecr_repository.api.arn
  enable_lambda_insights   = true
  image_uri                = "${aws_ecr_repository.api.repository_url}:latest"
  vpc = {
    security_group_ids = [module.rds.proxy_security_group_id, aws_security_group.api.id]
    subnet_ids         = module.vpc.private_subnet_ids
  }

  policies = [
    data.aws_iam_policy_document.api_policies.json,
    data.aws_iam_policy_document.firehose_assume_role.json,
    data.aws_iam_policy_document.write_waf_logs.json
  ]
}
