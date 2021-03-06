output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}

output "log_bucket_id" {
  value = module.log_bucket.s3_bucket_id
}

output "function_arn" {
  value = module.api.function_arn
}

output "function_log_group_name" {
  value = "/aws/lambda/${module.api.function_name}"
}

output "function_name" {
  value = module.api.function_name
}

output "function_role_arn" {
  value = "arn:aws:iam::${var.account_id}:role/${module.api.function_name}"
}

output "invoke_arn" {
  value = module.api.invoke_arn
}

output "route53_health_check_api_id" {
  value = aws_route53_health_check.scan_files_A.id
}

output "scan_files_api_key_secret_arn" {
  value = aws_secretsmanager_secret.api_auth_token.arn
}
