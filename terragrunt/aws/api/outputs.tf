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

output "function_name" {
  value = module.api.function_name
}

output "invoke_arn" {
  value = module.api.invoke_arn
}
