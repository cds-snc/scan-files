variable "concurrent_scan_limit" {
  description = "The maximum number of ongoing scans"
  type        = number
}

variable "retry_interval_seconds" {
  description = "The number of seconds to wait before polling for results"
  type        = number
}

variable "api_function_arn" {
  default = "ARN of the API function"
  type    = string
}

variable "api_function_name" {
  default = "Name of the API function"
  type    = string
}

variable "locktable_name" {
  description = "Scan queue lock semaphore Dynamodb table name"
  type        = string
}

variable "completed_scans_table_name" {
  description = "Complete scan Dynamodb table name"
  type        = string
}

variable "scan_queue_statemachine_name" {
  description = "Name of the scan queue state machine"
  type        = string
}

