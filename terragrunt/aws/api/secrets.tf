resource "aws_secretsmanager_secret" "api_auth_token" {
  name       = "/scan-files/api_auth_token"
  kms_key_id = aws_kms_key.scan-files.arn

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_secretsmanager_secret_version" "api_auth_token" {
  secret_id     = aws_secretsmanager_secret.api_auth_token.id
  secret_string = var.api_auth_token
}
