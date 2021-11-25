from boto3wrapper.wrapper import get_session
from os import environ
from logger import log
from urllib.parse import urlparse
from uuid import uuid4


def get_file(save_path, ref_only=False):
    parsed_save_path = urlparse(save_path)
    bucket = parsed_save_path.netloc
    key = parsed_save_path.path.lstrip("/")

    if environ.get("AWS_LOCALSTACK", False):
        client = get_session().resource("s3", endpoint_url="http://localstack:4566")
    else:
        client = get_session().resource("s3")

    obj = client.Object(bucket, key)

    try:
        basename = key.split("/")[-1].strip()

        if ref_only:
            body = obj.download_file(basename)["Body"]
        else:
            body = obj.download_file(basename)["Body"].read()

        log.info(f"Downloaded {key} from {bucket}")
        return body
    except Exception as err:
        print(err)
        log.error(f"Error downloading {key} from {bucket}")
        log.error(err)
        return False


def get_object(record, ref_only=False):

    if environ.get("AWS_LOCALSTACK", False):
        client = get_session().resource("s3", endpoint_url="http://localstack:4566")
    else:
        client = get_session().resource("s3")

    obj = client.Object(record["s3"]["bucket"]["name"], record["s3"]["object"]["key"])
    try:
        if ref_only:
            body = obj.get()["Body"]
        else:
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

    if environ.get("AWS_LOCALSTACK", False):
        client = get_session().resource("s3", endpoint_url="http://localstack:4566")
    else:
        client = get_session().resource("s3")

    bucket = environ.get("FILE_QUEUE_BUCKET", None)

    try:
        name = str(uuid4())
        obj = client.Object(bucket, name)
        file.file.seek(0)
        obj.put(Body=file.file.read())
        return f"s3://{bucket}/{file.filename}_{name}"
    except Exception as err:
        log.error(f"Error uploading {file.filename} to s3")
        log.error(err)
        return None
