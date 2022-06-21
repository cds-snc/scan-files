variable "account_id" {
  description = "(Required) The account ID to perform actions on."
  type        = string
}

variable "aws_org_id" {
  description = "(Required) The AWS org account ID.  Used to limit which roles the API can assume."
  type        = string
  sensitive   = true
}

variable "domain" {
  description = "(Required) Domain name to deploy to"
  type        = string
}

variable "env" {
  description = "The current running environment"
  type        = string
}

variable "product_name" {
  description = "(Required) The name of the product you are deploying."
  type        = string
}

variable "region" {
  description = "The current AWS region"
  type        = string
}

variable "billing_code" {
  description = "The billing code to tag our resources with"
  type        = string
}