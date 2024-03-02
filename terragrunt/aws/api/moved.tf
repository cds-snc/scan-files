moved {
  from = module.api
  to   = module.scan_files["api"]
}

moved {
  from = module.api_provisioned
  to   = module.scan_files["api-provisioned"]
}

moved {
  from = aws_lambda_function_url.scan_files_url
  to   = aws_lambda_function_url.scan_files["api"]
}

moved {
  from = aws_lambda_function_url.scan_files_provisioned_url
  to   = aws_lambda_function_url.scan_files["api-provisioned"]
}
