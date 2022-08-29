resource "aws_cloudwatch_query_definition" "api_errors" {
  name = "Errors: API"

  log_group_names = [
    var.scan_files_api_log_group_name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message, @logStream
    | filter @message like /ERROR/
    | sort @timestamp desc
    | limit 20
  QUERY
}

resource "aws_cloudwatch_query_definition" "s3_scan_object_errors" {
  name = "Errors: S3 scan object"

  log_group_names = [
    var.s3_scan_object_log_group_name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message, @logStream
    | filter @message like /ERROR/
    | sort @timestamp desc
    | limit 20
  QUERY
}

resource "aws_cloudwatch_query_definition" "track_requests" {
  name = "Trace: single request"

  log_group_names = [
    var.scan_files_api_log_group_name,
    var.s3_scan_object_log_group_name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message, @logStream
    | filter @message like /REQUEST_ID/
    | sort @timestamp desc
    | limit 20
  QUERY
}