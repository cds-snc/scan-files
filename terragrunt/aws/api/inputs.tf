variable "api_auth_token" {
  description = "The API auth token that must be added as a header to all requests to the API."
  type        = string
  sensitive   = true
}

variable "api_secret_environment_variables" {
  description = "The secret environment variables loaded by the API on cold start."
  type        = string
  sensitive   = true
}

variable "enable_waf" {
  description = "Turn the the WAF on the API on or off.  This is only meant to be used during testing."
  type        = bool
  default     = true
}

variable "rds_password" {
  type      = string
  sensitive = true
}

variable "rds_username" {
  type = string
}

variable "locktable_name" {
  type = string
}

variable "completed_scans_table_name" {
  type = string
}

variable "scan_queue_statemachine_name" {
  type = string
}

variable "hosted_zone_id" {
  type = string
}

variable "oidc_exists" {
  type = bool
}
