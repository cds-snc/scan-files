from mangum import Mangum
from api_gateway import api
from logger import log
from os import environ
from database.migrate import migrate_head
from aws_lambda_powertools import Metrics

app = api.app
metrics = Metrics(namespace="ScanFiles", service="api")

if environ.get("CI"):
    connection_string = environ.get("SQLALCHEMY_DATABASE_TEST_URI")
else:
    connection_string = environ.get("SQLALCHEMY_DATABASE_URI")


@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event, context):
    if "requestContext" in event:
        # Assume it is an API Gateway event
        asgi_handler = Mangum(app, dsn=connection_string)
        response = asgi_handler(event, context)
        return response

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
