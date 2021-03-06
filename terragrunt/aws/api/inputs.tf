variable "api_auth_token" {
  type      = string
  sensitive = true
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
