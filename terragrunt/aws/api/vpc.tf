module "vpc" {
  source            = "github.com/cds-snc/terraform-modules?ref=v3.0.19//vpc"
  name              = var.product_name
  billing_tag_value = var.billing_code
  high_availability = true
  enable_flow_log   = true
  block_ssh         = true
  block_rdp         = true

  single_nat_gateway = var.env != "production"

  allow_https_request_out          = true
  allow_https_request_out_response = true
  allow_https_request_in           = true
  allow_https_request_in_response  = true
}

#
# VPC private endpoints
#
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = module.vpc.vpc_id
  vpc_endpoint_type   = "Interface"
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  private_dns_enabled = true
  security_group_ids = [
    aws_security_group.vpc_endpoint.id,
  ]
  subnet_ids = module.vpc.private_subnet_ids
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = module.vpc.vpc_id
  vpc_endpoint_type   = "Interface"
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  private_dns_enabled = true
  security_group_ids = [
    aws_security_group.vpc_endpoint.id,
  ]
  subnet_ids = module.vpc.private_subnet_ids
}

resource "aws_vpc_endpoint" "logs" {
  vpc_id              = module.vpc.vpc_id
  vpc_endpoint_type   = "Interface"
  service_name        = "com.amazonaws.${var.region}.logs"
  private_dns_enabled = true
  security_group_ids = [
    aws_security_group.vpc_endpoint.id,
  ]
  subnet_ids = module.vpc.private_subnet_ids
}

resource "aws_vpc_endpoint" "sns" {
  vpc_id              = module.vpc.vpc_id
  vpc_endpoint_type   = "Interface"
  service_name        = "com.amazonaws.${var.region}.sns"
  private_dns_enabled = true
  security_group_ids = [
    aws_security_group.vpc_endpoint.id,
  ]
  subnet_ids = module.vpc.private_subnet_ids
}

resource "aws_vpc_endpoint" "sts" {
  vpc_id              = module.vpc.vpc_id
  vpc_endpoint_type   = "Interface"
  service_name        = "com.amazonaws.${var.region}.sts"
  private_dns_enabled = true
  security_group_ids = [
    aws_security_group.vpc_endpoint.id,
  ]
  subnet_ids = module.vpc.private_subnet_ids
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = module.vpc.vpc_id
  vpc_endpoint_type = "Gateway"
  service_name      = "com.amazonaws.${var.region}.s3"
  route_table_ids   = [module.vpc.main_route_table_id]
}

#
# Security groups
#
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

resource "aws_security_group" "vpc_endpoint" {
  name        = "vpc_endpoints"
  description = "PrivateLink VPC endpoints"
  vpc_id      = module.vpc.vpc_id

  tags = {
    Name       = "${var.product_name}_api_sg"
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_security_group_rule" "ecr_private_endpoint_ingress" {
  description              = "Ingress from the API security group"
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.vpc_endpoint.id
  source_security_group_id = aws_security_group.api.id
}

resource "aws_security_group_rule" "s3_private_endpoint_ingress" {
  description       = "Ingress from the private S3 endpoint"
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  security_group_id = aws_security_group.vpc_endpoint.id
  prefix_list_ids = [
    aws_vpc_endpoint.s3.prefix_list_id
  ]
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
