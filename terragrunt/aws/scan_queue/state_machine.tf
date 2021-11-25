resource "aws_sfn_state_machine" "scan_queue" {
  name     = "assemblyline-file-scan-queue"
  role_arn = aws_iam_role.scan_queue.arn

  definition = data.template_file.scan_queue.rendered

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
data "template_file" "scan_queue" {
  template = file("state-machines/scan-queue.json")
  vars = {
    worker_lambda         = var.api_function_name
    table_semaphore       = aws_dynamodb_table.scan-locktable.name
    lock_name             = "ScanSemaphore"
    concurrent_scan_limit = var.concurrent_scan_limit
  }
}

resource "aws_sfn_state_machine" "scan_queue_lock_cleanup" {
  name     = "assemblyline-file-scan-queue-lock-cleanup"
  role_arn = aws_iam_role.scan_queue.arn

  definition = data.template_file.scan_queue_lock_cleanup.rendered

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
data "template_file" "scan_queue_lock_cleanup" {
  template = file("state-machines/scan-queue-lock-cleanup.json")
  vars = {
    table_semaphore = aws_dynamodb_table.scan-locktable.name
    lock_name       = "ScanSemaphore"
  }
}
