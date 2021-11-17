resource "aws_apigatewayv2_api" "api_wskt" {
  name        = "api-gatewayv2-websocket"
  description = "Proxy to handle websocket requests to our API"

  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_apigatewayv2_integration" "api_wskt_integ" {
  api_id               = aws_apigatewayv2_api.api_wskt.id
  integration_type     = "AWS_PROXY"
  connection_type      = "INTERNET"
  integration_method   = "POST"
  integration_uri      = module.api.invoke_arn
  passthrough_behavior = "WHEN_NO_MATCH"
}

resource "aws_apigatewayv2_route" "api_wskt_route_connect" {
  api_id    = aws_apigatewayv2_api.api_wskt.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.api_wskt_integ.id}"
}

resource "aws_apigatewayv2_route" "api_wskt_route_disconnect" {
  api_id    = aws_apigatewayv2_api.api_wskt.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.api_wskt_integ.id}"
}

resource "aws_apigatewayv2_route" "api_wskt_route_default" {
  api_id    = aws_apigatewayv2_api.api_wskt.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api_wskt_integ.id}"
}

resource "aws_apigatewayv2_stage" "api_wskt_stage" {
  api_id      = aws_apigatewayv2_api.api_wskt.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 10
    throttling_rate_limit  = 1
  }
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_wskt_access.arn
    format          = "$context.identity.sourceIp [$context.requestTime] \"$context.httpMethod $context.path $context.protocol\" $context.status $context.responseLength $context.requestId"
  }

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}
