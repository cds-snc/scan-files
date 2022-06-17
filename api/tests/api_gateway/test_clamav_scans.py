import os

from api_gateway import api
from factories import ScanFactory
from fastapi.testclient import TestClient
from models.Scan import Scan, ScanVerdicts
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch, MagicMock
from clamav_scanner.common import create_dir

client = TestClient(api.app)


def load_fixture(name):
    fixture = open(f"tests/api_gateway/fixtures/{name}", "r")
    return fixture.read()


@patch("api_gateway.routers.clamav.launch_scan")
@patch("storage.storage.get_session")
@patch("database.db.get_db_session")
def test_clamav_file_upload_success(mock_db_session, mock_aws_session, mock_scan_queue):
    create_dir("/tmp/clamav/quarantine")
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
    create_dir("/tmp/clamav/quarantine")
    filename = "tests/api_gateway/fixtures/file.txt"

    client.post(
        "/clamav",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    mock_launch_scan.assert_called_once()


@patch("api_gateway.routers.clamav.get_db_session")
def test_clamav_get_results_completed(mock_db_session, session):
    scan = ScanFactory(
        completed="2021-12-12T17:20:03.930469Z",
        verdict=ScanVerdicts.CLEAN.value,
        sha256="bar",
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
