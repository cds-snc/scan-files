variable "api_cloudfront_distribution_id" {
  description = "ID of the API CloudFront distribution"
  type        = string
}

variable "route53_health_check_api_id" {
  description = "ID of the API's Route53 health check"
  type        = string
}

variable "s3_scan_object_log_group_name" {
  description = "CloudWatch log group name for the S3 scan object lambda function"
  type        = string
}

variable "s3_scan_object_error_threshold" {
  description = "CloudWatch alarm threshold for the S3 scan object lambda function ERROR logs"
  type        = string
}

variable "scan_files_api_log_group_name" {
  description = "CloudWatch log group name for the Scan Files API lambda function"
  type        = string
}

variable "scan_files_api_error_threshold" {
  description = "CloudWatch alarm threshold for the Scan Files API lambda function ERROR logs"
  type        = string
}

variable "scan_files_api_warning_threshold" {
  description = "CloudWatch alarm threshold for the Scan Files API lambda function WARNING logs"
  type        = string
}

variable "scan_files_api_scan_verdict_suspicious_threshold" {
  description = "CloudWatch alarm threshold for the Scan Files API scan verdicts that are suspicious"
  type        = string
}

variable "slack_webhook_url" {
  description = "Slack webhook URL that will be used to send notifications"
  type        = string
  sensitive   = true
}
