resource "aws_cloudwatch_metric_alarm" "route53_health_check_api" {
  provider = aws.us-east-1

  alarm_name          = "ScanFilesAPIHealthCheck"
  alarm_description   = "Check that Scan Files API is healthy"
  comparison_operator = "LessThanThreshold"

  metric_name        = "HealthCheckStatus"
  namespace          = "AWS/Route53"
  period             = "60"
  evaluation_periods = "2"
  statistic          = "Average"
  threshold          = "1"
  treat_missing_data = "breaching"

  alarm_actions = [aws_sns_topic.cloudwatch_warning_us_east.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_warning_us_east.arn]

  dimensions = {
    HealthCheckId = var.route53_health_check_api_id
  }
}

resource "aws_cloudwatch_log_metric_filter" "scan_files_api_error" {
  name           = "ErrorLoggedAPI"
  pattern        = "ERROR"
  log_group_name = var.scan_files_api_log_group_name

  metric_transformation {
    name      = "ErrorLoggedAPI"
    namespace = "ScanFiles"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "scan_files_api_error" {
  alarm_name          = "ErrorLoggedAPI"
  alarm_description   = "Errors logged by the Scan Files API lambda function"
  comparison_operator = "GreaterThanThreshold"

  metric_name        = aws_cloudwatch_log_metric_filter.scan_files_api_error.metric_transformation[0].name
  namespace          = aws_cloudwatch_log_metric_filter.scan_files_api_error.metric_transformation[0].namespace
  period             = "60"
  evaluation_periods = "1"
  statistic          = "Sum"
  threshold          = var.scan_files_api_error_threshold
  treat_missing_data = "notBreaching"

  alarm_actions = [aws_sns_topic.cloudwatch_warning.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_warning.arn]
}

resource "aws_cloudwatch_log_metric_filter" "s3_scan_object_error" {
  name           = "ErrorLoggedS3ScanObject"
  pattern        = "ERROR"
  log_group_name = var.s3_scan_object_log_group_name

  metric_transformation {
    name      = "ErrorLoggedS3ScanObject"
    namespace = "ScanFiles"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "s3_scan_object_error" {
  alarm_name          = "ErrorLoggedS3ScanObject"
  alarm_description   = "Errors logged by the S3 scan object lambda function"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = aws_cloudwatch_log_metric_filter.s3_scan_object_error.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.s3_scan_object_error.metric_transformation[0].namespace

  period             = "60"
  evaluation_periods = "1"
  statistic          = "Sum"
  threshold          = var.s3_scan_object_error_threshold
  treat_missing_data = "notBreaching"

  alarm_actions = [aws_sns_topic.cloudwatch_warning.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_warning.arn]
}
