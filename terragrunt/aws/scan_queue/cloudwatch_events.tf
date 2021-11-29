#
# Event rule: defines events to capture and Step function to trigger
#
resource "aws_cloudwatch_event_rule" "sfn_events" {
  name        = "state-machine-${var.env}-lock-cleanup"
  description = "Capture State Machine events from the Scan queue step function"
  event_pattern = jsonencode({
    "source" : ["aws.states"],
    "detail" : {
      "stateMachineArn" : ["${aws_sfn_state_machine.scan_queue.arn}"]
      "status" : ["FAILED", "TIMED_OUT", "ABORTED"]
    }
  })
}

resource "aws_cloudwatch_event_target" "sfn_events" {
  rule     = aws_cloudwatch_event_rule.sfn_events.name
  arn      = aws_sfn_state_machine.scan_queue_lock_cleanup.arn
  role_arn = aws_iam_role.scan_queue.arn
}
