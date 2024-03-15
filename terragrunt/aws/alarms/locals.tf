locals {
  api_functions = [
    {
      name           = "api",
      log_group_name = var.scan_files_api_log_group_name,
    },
    {
      name           = "api-provisioned",
      log_group_name = var.scan_files_api_sync_log_group_name,
    },
  ]
  error_logged_api            = "ErrorLogged"
  error_logged_s3_scan_object = "ErrorLoggedS3ScanObject"
  error_namespace             = "ScanFiles"
  scan_verdict_suspicious     = "ScanVerdictSuspicious"
  scan_verdict_unknown        = "ScanVerdictUnknown"
  warning_logged_api          = "WarningLogged"

  # Metric filter patterns
  api_errors = [
    "ERROR",
    "Error",
    "error",
    "failed",
  ]
  api_errors_skip = [
    "database server doesn't have the latest patch",
  ]
  api_warnings = [
    "Warning",
    "warning",
  ]
  api_warnings_skip = [
    "database server doesn't have the latest patch",
  ]
  api_error_metric_pattern   = "[(w1=\"*${join("*\" || w1=\"*", local.api_errors)}*\") && w1!=\"*${join("*\" && w1!=\"*", local.api_errors_skip)}*\"]"
  api_warning_metric_pattern = "[(w1=\"*${join("*\" || w1=\"*", local.api_warnings)}*\") && w1!=\"*${join("*\" && w1!=\"*", local.api_warnings_skip)}*\"]"
}