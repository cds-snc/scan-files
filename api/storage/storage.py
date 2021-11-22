from boto3wrapper.wrapper import get_session
from os import environ
from logger import log
from uuid import uuid4


def get_object(record):

    if environ.get("AWS_LOCALSTACK", False):
        client = get_session().resource("s3", endpoint_url="http://localstack:4566")
    else:
        client = get_session().resource("s3")

    obj = client.Object(record["s3"]["bucket"]["name"], record["s3"]["object"]["key"])
    try:
        body = obj.get()["Body"].read()
        log.info(
            f"Downloaded {record['s3']['object']['key']} from {record['s3']['bucket']['name']} with length {len(body)}"
        )
        return body
    except Exception as err:
        log.error(
            f"Error downloading {record['s3']['object']['key']} from {record['s3']['bucket']['name']}"
        )
        log.error(err)
        return False


def put_file(file):

    client = get_session().resource("s3")
    bucket = environ.get("FILE_QUEUE_BUCKET", None)

    try:
        name = str(uuid4())
        obj = client.Object(bucket, name)
        file.file.seek(0)
        obj.put(Body=file.file.read())
        return f"s3://{bucket}/{file.filename}_{name}"
    except Exception as err:
        print(err)
        log.error(f"Error uploading {file.filename} to s3")
        log.error(err)
        return None
