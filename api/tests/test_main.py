import json
import main
from unittest.mock import MagicMock, patch
from clamav_scanner.common import CLAMAV_LAMBDA_SCAN_TASK_NAME


@patch("main.Mangum")
def test_handler_api_gateway_event(mock_mangum, context_fixture, capsys):
    mock_asgi_handler = MagicMock()
    mock_asgi_handler.return_value = True
    mock_mangum.return_value = mock_asgi_handler
    assert (
        main.handler(
            {
                "headers": {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                "requestContext": {
                    "http": {
                        "method": "POST",
                        "path": "/foo",
                        "protocol": "HTTP/1.1",
                    }
                },
            },
            context_fixture,
        )
        is True
    )
    mock_asgi_handler.assert_called_once_with(
        {
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            "requestContext": {
                "http": {
                    "method": "POST",
                    "path": "/foo",
                    "protocol": "HTTP/1.1",
                }
            },
        },
        context_fixture,
    )

    log = capsys.readouterr().out.strip()
    metrics_output = json.loads(log)

    assert "ScanFiles" in log
    assert (
        "ColdStart"
        in metrics_output["_aws"]["CloudWatchMetrics"][0]["Metrics"][0]["Name"]
    )
    assert metrics_output["function_name"] == "scan-files-api"


@patch("main.log")
def test_handler_unmatched_event(mock_logger, context_fixture):
    assert main.handler({}, context_fixture) is False
    mock_logger.warning.assert_called_once_with("Handler received unrecognised event")


@patch("main.migrate_head")
def test_handler_migrate_event(mock_migrate_head, context_fixture):
    assert main.handler({"task": "migrate"}, context_fixture) == "Success"
    mock_migrate_head.assert_called_once()


def test_handler_heartbeat_event():
    assert main.handler({"task": "heartbeat"}, {}) == "Success"


@patch("main.launch_scan")
def test_handler_assemblyline_scan_event(mock_launch_scan, context_fixture):
    main.handler(
        {"task": "assemblyline_scan", "execution_id": 123, "Input": {"scan_id": "123"}},
        context_fixture,
    )
    mock_launch_scan.assert_called_once()


@patch("main.poll_for_results")
@patch("main.get_scan_result")
def test_handler_assemblyline_result_event(
    mock_get_scan_result, mock_poll_for_results, context_fixture
):
    main.handler(
        {
            "task": "assemblyline_result",
            "execution_id": 123,
            "Input": {"scan_id": "123"},
        },
        context_fixture,
    )
    mock_poll_for_results.assert_called_once()
    mock_get_scan_result.assert_called_once()


@patch("main.poll_for_results")
@patch("main.get_scan_result")
def test_handler_assemblyline_result_event_scan_not_complete(
    mock_get_scan_result, mock_poll_for_results, context_fixture
):
    mock_poll_for_results.return_value = False
    main.handler(
        {
            "task": "assemblyline_result",
            "execution_id": 123,
            "Input": {"scan_id": "123"},
        },
        context_fixture,
    )
    mock_poll_for_results.assert_called_once()
    assert not mock_get_scan_result.called


@patch("main.resubmit_stale_scans")
def test_handler_assemblyline_resubmit_stale_event(
    mock_resubmit_stale_scans, context_fixture
):
    main.handler({"task": "assemblyline_resubmit_stale"}, context_fixture)
    mock_resubmit_stale_scans.assert_called_once()


@patch("main.migrate_head")
def test_handler_migrate_event_failed(mock_migrate_head, context_fixture):
    mock_migrate_head.side_effect = Exception()
    assert main.handler({"task": "migrate"}, context_fixture) == "Error"
    mock_migrate_head.assert_called_once()


@patch("main.clamav_launch_scan")
def test_handler_clamav_scan_event(mock_launch_scan, context_fixture):
    main.handler(
        {
            "task": CLAMAV_LAMBDA_SCAN_TASK_NAME,
            "file_path": 123,
            "scan_id": "123",
            "aws_account": "123",
            "sns_arn": "123",
        },
        context_fixture,
    )
    mock_launch_scan.assert_called_once()
