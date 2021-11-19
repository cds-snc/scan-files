variable "api_auth_token" {
  type      = string
  sensitive = true
}

variable "mlwr_host" {
  type      = string
  sensitive = true
}

variable "mlwr_user" {
  type      = string
  sensitive = true
}

variable "mlwr_key" {
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
