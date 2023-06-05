variable "scan_files_api_function_role_name" {
  description = "Name of the Scan Files API function role"
  type        = string
}

variable "scan_files_api_function_role_arn" {
  description = "ARN of the Scan Files API function role"
  type        = string
}

variable "scan_files_api_key_secret_arn" {
  description = "ARN of the Scan Files API key secret"
  type        = string
}

variable "scan_files_api_function_url" {
  description = "URL of the Scan Files API function"
  type        = string
  sensitive   = true
}

variable "sqs_event_accounts" {
  description = "Accounts that have an SQS queue to receive S3 events from"
  type        = set(string)
}
