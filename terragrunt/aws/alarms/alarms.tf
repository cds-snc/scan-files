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

resource "aws_cloudwatch_log_metric_filter" "scan_files_error" {
  for_each = { for function in local.api_functions : function.name => function }

  name           = local.error_logged_api
  pattern        = local.api_error_metric_pattern
  log_group_name = each.value.log_group_name

  metric_transformation {
    name      = local.error_logged_api
    namespace = local.error_namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "scan_files_warning" {
  for_each = { for function in local.api_functions : function.name => function }

  name           = local.warning_logged_api
  pattern        = local.api_warning_metric_pattern
  log_group_name = each.value.log_group_name

  metric_transformation {
    name      = local.warning_logged_api
    namespace = local.error_namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "scan_files_error" {
  for_each = { for function in local.api_functions : function.name => function }

  alarm_name          = "${local.error_logged_api}-${each.value.name}"
  alarm_description   = "Errors logged by the Scan Files ${each.value.name} lambda function"
  comparison_operator = "GreaterThanOrEqualToThreshold"

  metric_name        = aws_cloudwatch_log_metric_filter.scan_files_error[each.value.name].metric_transformation[0].name
  namespace          = aws_cloudwatch_log_metric_filter.scan_files_error[each.value.name].metric_transformation[0].namespace
  period             = "60"
  evaluation_periods = "1"
  statistic          = "Sum"
  threshold          = var.scan_files_api_error_threshold
  treat_missing_data = "notBreaching"

  alarm_actions = [aws_sns_topic.cloudwatch_warning.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_warning.arn]
}

resource "aws_cloudwatch_metric_alarm" "scan_files_warning" {
  for_each = { for function in local.api_functions : function.name => function }

  alarm_name          = "${local.warning_logged_api}-${each.value.name}"
  alarm_description   = "Warnings logged by the Scan Files ${each.value.name} lambda function"
  comparison_operator = "GreaterThanOrEqualToThreshold"

  metric_name        = aws_cloudwatch_log_metric_filter.scan_files_warning[each.value.name].metric_transformation[0].name
  namespace          = aws_cloudwatch_log_metric_filter.scan_files_warning[each.value.name].metric_transformation[0].namespace
  period             = "60"
  evaluation_periods = "1"
  statistic          = "Sum"
  threshold          = var.scan_files_api_warning_threshold
  treat_missing_data = "notBreaching"

  alarm_actions = [aws_sns_topic.cloudwatch_warning.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_warning.arn]
}

resource "aws_cloudwatch_log_metric_filter" "scan_verdict_unknown" {
  for_each = { for function in local.api_functions : function.name => function }

  name           = local.scan_verdict_unknown
  pattern        = "?unknown ?unable_to_scan"
  log_group_name = each.value.log_group_name

  metric_transformation {
    name      = local.scan_verdict_unknown
    namespace = local.error_namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "scan_verdict_unknown" {
  for_each = { for function in local.api_functions : function.name => function }

  alarm_name          = "${local.scan_verdict_unknown}-${each.value.name}"
  alarm_description   = "Scans from the ${each.value.name} that returned an unknown or unable to scan verdict"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  metric_name         = aws_cloudwatch_log_metric_filter.scan_verdict_unknown[each.value.name].metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.scan_verdict_unknown[each.value.name].metric_transformation[0].namespace

  period             = "60"
  evaluation_periods = "1"
  statistic          = "Sum"
  threshold          = var.scan_files_api_scan_verdict_unknown_threshold
  treat_missing_data = "notBreaching"

  alarm_actions = [aws_sns_topic.cloudwatch_warning.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_warning.arn]
}

resource "aws_cloudwatch_log_metric_filter" "s3_scan_object_error" {
  name           = local.error_logged_s3_scan_object
  pattern        = "?ERROR ?Error ?error ?failed"
  log_group_name = var.s3_scan_object_log_group_name

  metric_transformation {
    name      = local.error_logged_s3_scan_object
    namespace = local.error_namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "s3_scan_object_error" {
  alarm_name          = local.error_logged_s3_scan_object
  alarm_description   = "Errors logged by the S3 scan object lambda function"
  comparison_operator = "GreaterThanOrEqualToThreshold"
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
