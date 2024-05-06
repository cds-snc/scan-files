module "rds" {
  source                  = "github.com/cds-snc/terraform-modules//rds?ref=v9.4.2"
  backup_retention_period = 7
  billing_tag_value       = var.billing_code
  database_name           = "scan_files"
  instances               = 1
  name                    = "scan-files"
  preferred_backup_window = "07:00-09:00"
  subnet_ids              = module.vpc.private_subnet_ids
  username                = var.rds_username
  password                = var.rds_password
  vpc_id                  = module.vpc.vpc_id
  engine_version          = "14.9"

  upgrade_immediately         = true
  allow_major_version_upgrade = true
}
