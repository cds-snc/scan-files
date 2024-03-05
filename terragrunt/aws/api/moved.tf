moved {
  from = module.api
  to   = module.scan_files["api"]
}

moved {
  from = aws_lambda_function_url.scan_files_url
  to   = aws_lambda_function_url.scan_files["api"]
}

moved {
  from = aws_cloudfront_distribution.scan_files_api
  to   = aws_cloudfront_distribution.scan_files["api"]
}
