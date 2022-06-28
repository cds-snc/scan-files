from api_gateway import api
from assemblyline.assemblyline import (
    launch_scan,
    poll_for_results,
    resubmit_stale_scans,
)

from clamav_scanner.update import update_virus_defs
from clamav_scanner.common import CLAMAV_LAMBDA_SCAN_TASK_NAME
from clamav_scanner.scan import launch_scan as clamav_launch_scan
from aws_lambda_powertools import Metrics
from database.dynamodb import get_scan_result
from database.migrate import migrate_head
from logger import log
from mangum import Mangum
from os import environ


app = api.app
metrics = Metrics(namespace="ScanFiles", service="api")

if environ.get("CI"):
    connection_string = environ.get("SQLALCHEMY_DATABASE_TEST_URI")
else:
    connection_string = environ.get("SQLALCHEMY_DATABASE_URI")


@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event, context):
    if "requestContext" in event and "http" in event["requestContext"]:
        # Assume it is a request to the lambda function url
        asgi_handler = Mangum(app)
        response = asgi_handler(event, context)
        return response

    elif event.get("task", "") == "assemblyline_scan":
        return launch_scan(event["execution_id"], event["Input"]["scan_id"])

    elif event.get("task", "") == "assemblyline_result":
        success = poll_for_results(event["Input"]["scan_id"])
        if success:
            return get_scan_result(event["execution_id"])
        return success

    elif event.get("task", "") == "assemblyline_resubmit_stale":
        return resubmit_stale_scans()

    elif event.get("task", "") == CLAMAV_LAMBDA_SCAN_TASK_NAME:
        return clamav_launch_scan(
            file_path=event.get("file_path"),
            scan_id=event.get("scan_id"),
            aws_account=event.get("aws_account"),
            sns_arn=event.get("sns_arn"),
        )

    elif event.get("task", "") == "clamav_update_virus_defs":
        return update_virus_defs()

    elif event.get("task", "") == "migrate":
        try:
            migrate_head()
            return "Success"
        except Exception as err:
            log.error(err)
            return "Error"

    elif event.get("task", "") == "heartbeat":
        return "Success"

    else:
        log.warning("Handler received unrecognised event")

    return False
