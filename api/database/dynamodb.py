from boto3wrapper.wrapper import get_session
from os import environ
from logger import log

DYNAMODB_TABLE = "completed-scans"


def log_scan_result(execution_id):
    if environ.get("AWS_LOCALSTACK", False):
        client = get_session().resource(
            "dynamodb", endpoint_url="http://localstack:4566"
        )
    else:
        client = get_session().resource("dynamodb")

    try:
        table = client.Table(DYNAMODB_TABLE)
        table.put_item(Item={"EXECUTION_ID": execution_id})
        return True
    except Exception as err:
        log.error(f"Error storing execution_id {execution_id} to dynamodb")
        log.error(err)
        return False


def get_scan_result(execution_id):
    if environ.get("AWS_LOCALSTACK", False):
        client = get_session().resource(
            "dynamodb", endpoint_url="http://localstack:4566"
        )
    else:
        client = get_session().resource("dynamodb")

    table = client.Table(DYNAMODB_TABLE)

    try:
        response = table.get_item(Key={"EXECUTION_ID": execution_id})
        if "Item" in response:
            table.delete_item(Key={"EXECUTION_ID": execution_id})
            return True
        return False

    except Exception as err:
        log.error(f"Error retrieving execution_id {execution_id} from dynamodb")
        log.error(err)
        return False
