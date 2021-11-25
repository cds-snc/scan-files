variable "concurrent_scan_limit" {
  type        = number
  description = "The maximum number of ongoing scans"
}

variable "retry_interval_seconds" {
  type        = number
  description = "The number of seconds to wait before polling for results"
}

variable "api_function_arn" {
  type = string
}

variable "api_function_name" {
  type = string
}

variable "locktable_name" {
  type        = string
  description = "Scan queue lock semaphore Dynamodb table name"
}

variable "completed_scans_table_name" {
  type = string
}

variable "scan_queue_statemachine_name" {
  type = string
}

