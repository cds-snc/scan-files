variable "route53_health_check_api_id" {
  description = "ID of the API's Route53 health check"
  type        = string
}

variable "slack_webhook_url" {
  description = "Slack webhook URL that will be used to send notifications"
  type        = string
  sensitive   = true
}
