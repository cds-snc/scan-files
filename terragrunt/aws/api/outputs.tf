output "api_cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.scan_files["api"].id
}

output "api_sync_cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.scan_files["api-provisioned"].id
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}

output "log_bucket_id" {
  value = module.log_bucket.s3_bucket_id
}

output "api_function_arn" {
  value = module.scan_files["api"].function_arn
}

output "api_sync_function_arn" {
  value = module.scan_files["api-provisioned"].function_arn
}

output "api_function_log_group_name" {
  value = "/aws/lambda/${module.scan_files["api"].function_name}"
}

output "api_sync_function_log_group_name" {
  value = "/aws/lambda/${module.scan_files["api-provisioned"].function_name}"
}

output "api_function_name" {
  value = module.scan_files["api"].function_name
}

output "api_sync_function_name" {
  value = module.scan_files["api-provisioned"].function_name
}

output "api_function_role_arn" {
  value = "arn:aws:iam::${var.account_id}:role/${module.scan_files["api"].function_name}"
}

output "api_function_url" {
  value     = aws_lambda_function_url.scan_files["api"].function_url
  sensitive = true
}

output "api_sync_function_url" {
  value     = aws_lambda_function_url.scan_files["api-provisioned"].function_url
  sensitive = true
}

output "api_invoke_arn" {
  value = module.scan_files["api"].invoke_arn
}

output "api_sync_invoke_arn" {
  value = module.scan_files["api-provisioned"].invoke_arn
}

output "route53_health_check_api_id" {
  value = aws_route53_health_check.scan_files_A.id
}

output "scan_files_api_key_secret_arn" {
  value = aws_secretsmanager_secret.api_auth_token.arn
}
