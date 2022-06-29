import os

from api_gateway import api
from factories import ScanFactory
from fastapi.testclient import TestClient
from models.Scan import Scan, ScanVerdicts
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import ANY, patch, MagicMock
from clamav_scanner.common import create_dir
from tempfile import TemporaryFile

client = TestClient(api.app)


class AnyStringWith(str):
    def __eq__(self, other):
        return self in other


def load_fixture(name):
    fixture = open(f"tests/api_gateway/fixtures/{name}", "r")
    return fixture.read()


@patch("api_gateway.routers.clamav.launch_scan")
@patch("storage.storage.get_session")
@patch("database.db.get_db_session")
def test_clamav_file_upload_success(mock_db_session, mock_aws_session, mock_scan_queue):
    create_dir(
        "/tmp/clamav/quarantine"  # nosec - [B108:hardcoded_tmp_directory] no risk in tests
    )
    filename = "tests/api_gateway/fixtures/file.txt"

    response = client.post(
        "/clamav",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.status_code == 200


@patch("database.db.get_db_session")
def test_clamav_file_upload_failure_no_file(mock_db_session):
    response = client.post(
        "/clamav",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.status_code == 422


@patch("database.db.get_db_session")
def test_clamav_file_upload_fail_not_authorized(mock_db_session):
    filename = "tests/api_gateway/fixtures/file.txt"

    response = client.post(
        "/clamav",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
    )

    assert response.status_code == 401


@patch("api_gateway.routers.clamav.launch_scan")
@patch("api_gateway.routers.clamav.get_db_session")
def test_clamav_start_scan(mock_db_session, mock_launch_scan):
    create_dir(
        "/tmp/clamav/quarantine"  # nosec - [B108:hardcoded_tmp_directory] no risk in tests
    )
    filename = "tests/api_gateway/fixtures/file.txt"

    client.post(
        "/clamav",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    mock_launch_scan.assert_called_once()


@patch("api_gateway.routers.clamav.launch_scan")
@patch("api_gateway.routers.clamav.get_db_session")
def test_clamav_start_scan_with_exception(mock_db_session, mock_launch_scan):
    create_dir(
        "/tmp/clamav/quarantine"  # nosec - [B108:hardcoded_tmp_directory] no risk in tests
    )
    filename = "tests/api_gateway/fixtures/file.txt"

    mock_launch_scan.side_effect = OSError

    response = client.post(
        "/clamav",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.json() == {"error": "error scanning file [random_file] with clamav"}
    assert response.status_code == 502


@patch("boto3wrapper.wrapper.AWS_ROLE_TO_ASSUME")
@patch("boto3wrapper.wrapper.get_session")
@patch("clamav_scanner.clamav.get_file")
@patch("clamav_scanner.clamav.subprocess")
@patch("clamav_scanner.scan.update_defs_from_s3")
@patch("clamav_scanner.scan.get_session")
@patch("api_gateway.routers.clamav.get_db_session")
def test_clamav_start_scan_from_s3(
    mock_db_session,
    mock_aws_session,
    mock_update_defs_from_s3,
    mock_subprocess,
    mock_get_file,
    mock_s3_download,
    session,
):
    create_dir(
        "/tmp/clamav/quarantine"  # nosec - [B108:hardcoded_tmp_directory] no risk in tests
    )

    mock_update_defs_from_s3.return_value.values.return_value = [mock_s3_download]
    mock_subprocess.run.return_value.returncode = 0
    mock_subprocess.run.return_value.stdout = "scan complete".encode("utf-8")

    file = TemporaryFile()
    mock_get_file.return_value = file
    mock_account_id = "123456789012"
    mock_sns_arn = "arn:aws:sns:us-east-1:123456789012:sns-topic"
    mock_file_path = "s3://bucket/file.txt"

    new_env = os.environ.copy()
    new_env["AWS_LAMBDA_FUNCTION_NAME"] = "foo"

    with patch.dict(os.environ, new_env, clear=True):
        response = client.post(
            "/clamav/s3",
            json={
                "aws_account": mock_account_id,
                "s3_key": mock_file_path,
                "sns_arn": mock_sns_arn,
            },
            headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
        )

    mock_aws_session().client().invoke.assert_called_once_with(
        FunctionName="foo",
        InvocationType="Event",
        Payload=AnyStringWith(mock_account_id),
    )

    assert response.status_code == 200
    assert response.json() == {"scan_id": ANY, "status": "OK"}


@patch("boto3wrapper.wrapper.AWS_ROLE_TO_ASSUME")
@patch("boto3wrapper.wrapper.get_session")
@patch("clamav_scanner.clamav.get_file")
@patch("clamav_scanner.clamav.subprocess")
@patch("clamav_scanner.scan.update_defs_from_s3")
@patch("clamav_scanner.scan.get_session")
@patch("api_gateway.routers.clamav.get_db_session")
def test_clamav_start_scan_with_s3_and_exception(
    mock_db_session,
    mock_aws_session,
    mock_update_defs_from_s3,
    mock_subprocess,
    mock_get_file,
    mock_session,
    mock_role,
    mock_s3_download,
    session,
):
    create_dir(
        "/tmp/clamav/quarantine"  # nosec - [B108:hardcoded_tmp_directory] no risk in tests
    )

    mock_role.return_value = "foo"
    mock_update_defs_from_s3.return_value.values.return_value = [mock_s3_download]
    mock_subprocess.run.return_value.returncode = 0
    mock_subprocess.run.return_value.stdout = "scan complete".encode("utf-8")

    mock_get_file.side_effect = Exception("error")
    response = client.post(
        "/clamav/s3",
        json={
            "aws_account": "123456789012",
            "s3_key": "s3://bucket/file.txt",
            "sns_arn": "arn:aws:sns:us-east-1:123456789012:sns-topic",
        },
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.json() == {"scan_id": ANY, "status": "OK"}
    assert response.status_code == 200


@patch("api_gateway.routers.clamav.get_db_session")
def test_clamav_get_results_completed(mock_db_session, session):
    scan = ScanFactory(
        completed="2021-12-12T17:20:03.930469Z",
        verdict=ScanVerdicts.CLEAN.value,
        checksum="bar",
    )
    session.commit()

    response = client.get(
        f"/clamav/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.json() == {"status": "completed", "verdict": "clean"}
    assert response.status_code == 200


@patch("api_gateway.routers.clamav.get_db_session")
def test_clamav_get_results_in_progress(mock_db_session, session):
    scan = ScanFactory()
    session.commit()

    response = client.get(
        f"/clamav/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert updated_scan.completed is None
    assert response.json() == {"status": ScanVerdicts.IN_PROGRESS.value}
    assert response.status_code == 200


@patch("database.db.db_session")
def test_get_clamav_results_random_sql_error(mock_db_session, session):

    scan = ScanFactory()

    mock_session = MagicMock()
    mock_session.query.side_effect = SQLAlchemyError()
    mock_db_session.return_value = mock_session

    response = client.get(
        f"/clamav/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.json() == {"error": "error retrieving scan details"}
    assert response.status_code == 500
