module "vpc" {
  source            = "github.com/cds-snc/terraform-modules?ref=v0.0.46//vpc"
  name              = var.product_name
  billing_tag_value = var.billing_code
  high_availability = true
  enable_flow_log   = false
  block_ssh         = true
  block_rdp         = true

  allow_https_request_out          = true
  allow_https_request_out_response = true
  allow_https_request_in           = true
  allow_https_request_in_response  = true
}


resource "aws_security_group" "api" {
  # checkov:skip=CKV2_AWS_5: False-positive, SG is attached in lambda.tf

  name        = "${var.product_name}_api_sg"
  description = "SG for the API lambda"

  vpc_id = module.vpc.vpc_id

  tags = {
    Name       = "${var.product_name}_api_sg"
    CostCentre = var.billing_code
    Terraform  = true
  }

  egress {
    description = "Allow API outbound connections to the internet"
    from_port   = 443
    to_port     = 443
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_flow_log" "cloud_based_sensor" {
  log_destination      = "arn:aws:s3:::${var.cbs_satellite_bucket_name}/vpc_flow_logs/"
  log_destination_type = "s3"
  traffic_type         = "ALL"
  vpc_id               = module.vpc.vpc_id
  log_format           = "$${vpc-id} $${version} $${account-id} $${interface-id} $${srcaddr} $${dstaddr} $${srcport} $${dstport} $${protocol} $${packets} $${bytes} $${start} $${end} $${action} $${log-status} $${subnet-id} $${instance-id}"

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
