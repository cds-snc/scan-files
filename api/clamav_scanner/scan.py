import datetime
import json
import os

from .common import AV_DEFINITION_S3_BUCKET
from .common import AV_DEFINITION_S3_PREFIX
from .common import AV_SIGNATURE_METADATA
from .common import AV_STATUS_METADATA
from .common import AV_TIMESTAMP_METADATA
from .common import AWS_ENDPOINT_URL
from .common import AV_SIGNATURE_UNKNOWN
from .common import CLAMAV_LAMBDA_SCAN_TASK_NAME

from boto3wrapper.wrapper import get_session, get_credentials
from clamav_scanner.clamav import determine_verdict, update_defs_from_s3, scan_file
from database.db import get_db_session
from logger import log
from models.Scan import Scan, ScanProviders, ScanVerdicts


def sns_scan_results(sns_client, scan, sns_arn, scan_signature, file_path):

    message = {
        "scan_id": str(scan.id),
        "file_path": file_path,
        AV_SIGNATURE_METADATA: scan_signature,
        AV_STATUS_METADATA: scan.verdict,
        AV_TIMESTAMP_METADATA: scan.completed.isoformat(),
    }

    log.info("Publishing to sns arn: %s; message: %s" % (sns_arn, str(message)))
    sns_client.publish(
        TargetArn=sns_arn,
        Message=json.dumps({"default": json.dumps(message, default=str)}),
        MessageStructure="json",
        MessageAttributes={
            "av-filepath": {"DataType": "String", "StringValue": file_path},
            AV_STATUS_METADATA: {"DataType": "String", "StringValue": scan.verdict},
            AV_SIGNATURE_METADATA: {
                "DataType": "String",
                "StringValue": scan_signature,
            },
        },
    )


def launch_background_scan(
    file_path, scan_id, aws_account=None, session=None, sns_arn=None
):
    lambda_client = get_session().client("lambda", endpoint_url=AWS_ENDPOINT_URL)
    lambda_client.invoke(
        FunctionName=os.environ.get("AWS_LAMBDA_FUNCTION_NAME"),
        InvocationType="Event",
        Payload=json.dumps(
            {
                "task": CLAMAV_LAMBDA_SCAN_TASK_NAME,
                "file_path": file_path,
                "scan_id": str(scan_id),
                "aws_account": aws_account,
                "sns_arn": sns_arn,
            }
        ),
    )


def launch_scan(file_path, scan_id, aws_account=None, session=None, sns_arn=None):
    if session is None:
        session = next(get_db_session())
    s3 = get_session().resource("s3", endpoint_url=AWS_ENDPOINT_URL)
    s3_client = get_session().client("s3", endpoint_url=AWS_ENDPOINT_URL)

    credentials = get_credentials(aws_account)
    sns_client = get_session(credentials).client("sns", endpoint_url=AWS_ENDPOINT_URL)

    to_download = update_defs_from_s3(
        s3_client, AV_DEFINITION_S3_BUCKET, AV_DEFINITION_S3_PREFIX
    )

    for download in to_download.values():
        s3_path = download["s3_path"]
        local_path = download["local_path"]
        log.info("Downloading definition file %s from s3://%s" % (local_path, s3_path))
        s3.Bucket(AV_DEFINITION_S3_BUCKET).download_file(s3_path, local_path)
        log.info("Downloading definition file %s complete!" % (local_path))

    scan = session.query(Scan).filter(Scan.id == scan_id).one_or_none()
    try:
        checksum, scan_result, scan_signature, scanned_path = scan_file(
            session, file_path, aws_account
        )
        scan.completed = datetime.datetime.utcnow()
        scan.verdict = determine_verdict(ScanProviders.CLAMAV.value, scan_result)
        scan.checksum = checksum
        scan.meta_data = {AV_SIGNATURE_METADATA: scan_signature}
        log.info("Scan of %s resulted in %s\n" % (file_path, scan_result))
    except Exception as err:
        log.error("Scan %s failed. Reason %s" % (str(scan.id), str(err)))
        scan.completed = datetime.datetime.utcnow()
        scan.verdict = ScanVerdicts.ERROR.value
        scan_signature = AV_SIGNATURE_UNKNOWN
        scan.meta_data = {AV_SIGNATURE_METADATA: scan_signature, "ERROR": str(err)}
        scanned_path = ""

    session.commit()

    # Publish the scan results
    if sns_arn not in [None, ""]:
        sns_scan_results(sns_client, scan, sns_arn, scan_signature, file_path)

    # Delete downloaded file to free up room on re-usable lambda function container
    try:
        os.remove(scanned_path)
    except OSError:
        pass

    return scan.verdict
