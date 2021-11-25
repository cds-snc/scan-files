data "aws_iam_policy_document" "service_principal" {
  statement {
    effect = "Allow"

    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    principals {
      type        = "Service"
      identifiers = ["states.${var.region}.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scan_queue" {
  name               = "${var.product_name}-scan_queue"
  assume_role_policy = data.aws_iam_policy_document.service_principal.json

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

data "aws_iam_policy_document" "scan_runner_policies" {
  statement {

    effect = "Allow"

    actions = [
      "lambda:InvokeFunction"
    ]

    resources = [
      var.api_function_arn
    ]
  }

  statement {

    effect = "Allow"

    actions = [
      "states:ListStateMachines",
      "states:ListActivities",
      "states:CreateStateMachine",
      "states:CreateActivity",
      "states:DescribeExecution",
      "states:StartExecution",
      "states:StopExecution"
    ]

    resources = [
      "arn:aws:states:${var.region}:${var.account_id}:*"
    ]
  }

  statement {

    effect = "Allow"

    actions = [
      "dynamodb:GetRecords",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem"
    ]

    resources = [
      aws_dynamodb_table.scan-locktable.arn
    ]
  }

  statement {

    effect = "Allow"

    actions = [
      "states:ListStateMachines",
      "states:ListActivities",
      "states:CreateStateMachine",
      "states:CreateActivity",
      "states:DescribeExecution",
      "states:StartExecution",
      "states:StopExecution"
    ]

    resources = [
      "arn:aws:states:${var.region}:${var.account_id}:*"
    ]
  }

  statement {

    effect = "Allow"

    actions = [
      "events:PutTargets",
      "events:PutRule",
      "events:DescribeRule"
    ]

    resources = [
      "arn:aws:events:${var.region}:${var.account_id}:*"
    ]
  }
}

resource "aws_iam_policy" "scan_queue" {
  name   = "${var.product_name}-scan_queue"
  path   = "/"
  policy = data.aws_iam_policy_document.scan_runner_policies.json

  tags = {
    CostCentre = var.billing_code
    Terraform  = true
  }
}

resource "aws_iam_role_policy_attachment" "scan_runner" {
  role       = aws_iam_role.scan_queue.name
  policy_arn = aws_iam_policy.scan_queue.arn
}
