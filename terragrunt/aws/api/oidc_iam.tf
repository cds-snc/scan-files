locals {
  oidc_role = "OIDCGithubWorkflowRole"
}

# Role used by Terraform to manage all satellite accounts
module "gh_oidc_roles" {
  source = "github.com/cds-snc/terraform-modules?ref=v2.0.5//gh_oidc_role"
  roles = [
    {
      name      = local.oidc_role
      repo_name = "scan-files"
      claim     = "*"
    }
  ]

  billing_tag_value = var.billing_code

}

data "aws_iam_policy" "admin" {
  name = "AdministratorAccess"
}

resource "aws_iam_role_policy_attachment" "admin" {
  role       = local.cbs_admin_role
  policy_arn = data.aws_iam_policy.admin.arn
  depends_on = [module.gh_oidc_roles]
}
