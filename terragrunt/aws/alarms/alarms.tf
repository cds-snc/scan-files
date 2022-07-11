resource "aws_cloudwatch_metric_alarm" "route53_health_check_api" {
  provider = aws.us-east-1

  alarm_name          = "ScanFilesAPIHealthCheck"
  alarm_description   = "Check that Scan Files API is healthy"
  comparison_operator = "LessThanThreshold"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  evaluation_periods  = "2"
  statistic           = "Average"
  threshold           = "1"
  treat_missing_data  = "breaching"

  alarm_actions = [aws_sns_topic.cloudwatch_warning_us_east.arn]

  dimensions = {
    HealthCheckId = var.route53_health_check_api_id
  }
}
