resource "aws_secretsmanager_secret" "api_auth_token" {
  name = "/scan-files/api_auth_token"
  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_secretsmanager_secret_version" "api_auth_token" {
  secret_id     = aws_secretsmanager_secret.api_auth_token.id
  secret_string = var.api_auth_token
}
