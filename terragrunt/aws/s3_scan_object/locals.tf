locals {
  onboarded_accounts = jsondecode(file("${path.module}/onboarded_accounts.json"))
}
