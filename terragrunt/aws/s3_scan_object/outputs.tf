output "function_log_group_name" {
  value = "/var/lambda/${module.s3_scan_object.function_name}"
}
