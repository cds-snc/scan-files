import os
import re
from api_gateway import api
from factories import ScanFactory
from fastapi.testclient import TestClient
from models.Scan import Scan, ScanVerdicts
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import ANY, patch, MagicMock

client = TestClient(api.app)


def load_fixture(name):
    fixture = open(f"tests/api_gateway/fixtures/{name}", "r")
    return fixture.read()


@patch("api_gateway.routers.scans.add_to_scan_queue")
@patch("storage.storage.get_session")
@patch("database.db.get_db_session")
def test_file_upload_success(mock_db_session, mock_aws_session, mock_scan_queue):
    os.environ["FILE_QUEUE_BUCKET"] = "foo"
    filename = "tests/api_gateway/fixtures/file.txt"

    response = client.post(
        "/assemblyline",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.status_code == 200


@patch("database.db.get_db_session")
def test_file_upload_failure_no_file(mock_db_session):
    response = client.post(
        "/assemblyline",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.status_code == 422


@patch("database.db.get_db_session")
def test_file_upload_fail_not_authorized(mock_db_session):
    filename = "tests/api_gateway/fixtures/file.txt"

    response = client.post(
        "/assemblyline",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
    )

    assert response.status_code == 401


@patch("assemblyline.assemblyline.get_session")
@patch("api_gateway.routers.scans.get_db_session")
def test_send_to_scan_queue(mock_db_session, mock_aws_client):
    os.environ["FILE_QUEUE_BUCKET"] = "foo"
    filename = "tests/api_gateway/fixtures/file.txt"

    mock_client = MagicMock()
    mock_aws_client.return_value.client.return_value = mock_client
    mock_aws_client.return_value.client.return_value.list_state_machines.return_value = {
        "stateMachines": [
            {
                "stateMachineArn": "arn",
                "name": "assemblyline-file-scan-queue",
            },
        ]
    }

    client.post(
        "/assemblyline",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    mock_aws_client().client().start_execution.assert_called_once_with(
        stateMachineArn="arn",
        input=ANY,
    )


@patch("api_gateway.routers.scans.get_db_session")
def test_get_results_completed(mock_db_session, session):
    scan = ScanFactory(
        completed="2021-12-12T17:20:03.930469Z",
        verdict=ScanVerdicts.CLEAN.value,
        sha256="bar",
    )
    session.commit()

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.json() == {"status": "completed", "verdict": "clean"}
    assert response.status_code == 200


@patch("api_gateway.routers.scans.get_db_session")
def test_get_results_in_progress(mock_db_session, session):
    scan = ScanFactory()
    session.commit()

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert updated_scan.completed is None
    assert response.json() == {"status": ScanVerdicts.IN_PROGRESS.value}
    assert response.status_code == 200


@patch("database.db.db_session")
def test_get_assemblyline_results_random_sql_error(mock_db_session):

    scan = ScanFactory()

    mock_session = MagicMock()
    mock_session.query.side_effect = SQLAlchemyError()
    mock_db_session.return_value = mock_session

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.json() == {"error": "error retrieving scan details"}
    assert response.status_code == 500


@patch("api_gateway.routers.scans.add_to_scan_queue")
@patch("storage.storage.get_session")
@patch("api_gateway.routers.scans.get_db_session")
def test_send_to_assemblyline_save_to_s3(
    mock_db_session, mock_aws_session, mock_scan_queue, session
):
    os.environ["FILE_QUEUE_BUCKET"] = "foo"
    filename = "tests/api_gateway/fixtures/file.txt"
    response = client.post(
        "/assemblyline",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.status_code == 200

    data = response.json()

    new_scan = session.query(Scan).filter(Scan.id == data["scan_id"]).one_or_none()
    assert re.match("s3://foo/random_file_(.*)", new_scan.save_path)
