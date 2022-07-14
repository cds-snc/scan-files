output "function_log_group_name" {
  value = "/aws/lambda/${module.s3_scan_object.function_name}"
}
