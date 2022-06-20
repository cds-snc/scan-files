resource "aws_ssm_parameter" "api_auth_token" {
  #checkov:skip=CKV2_AWS_34:Encryption: Not required
  name  = "/scan-files/api_auth_token"
  type  = "SecureString"
  value = var.api_auth_token

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
