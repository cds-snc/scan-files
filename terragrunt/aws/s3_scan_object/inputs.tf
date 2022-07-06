variable "scan_files_api_function_role_arn" {
  description = "ARN of the Scan Files API function role"
  type        = string
}

variable "scan_files_api_key_kms_arn" {
  description = "ARN of the KMS key used to encrypt the Scan Files API key secret"
  type        = string
}

variable "scan_files_api_key_secret_arn" {
  description = "ARN of the Scan Files API key secret"
  type        = string
}
