import json
import os
import re
from uuid import uuid4
from api_gateway import api
from api_gateway.routers.scans import determine_verdict
from factories import ScanFactory
from fastapi.testclient import TestClient
from models.Scan import Scan, ScanProviders, ScanVerdicts
from requests import HTTPError
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import ANY, patch

client = TestClient(api.app)


def load_fixture(name):
    fixture = open(f"tests/api_gateway/fixtures/{name}", "r")
    return fixture.read()


@patch("storage.storage.get_session")
@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_file_upload_success(mock_db_session, mock_client, mock_aws_session):
    os.environ["FILE_QUEUE_BUCKET"] = "foo"
    filename = "tests/api_gateway/fixtures/file.txt"

    response = client.post(
        "/assemblyline",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.status_code == 200


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_file_upload_failure_no_file(mock_db_session, mock_client):
    response = client.post(
        "/assemblyline",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.status_code == 422


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_file_upload_fail_not_authorized(mock_db_session, mock_client):
    filename = "tests/api_gateway/fixtures/file.txt"

    response = client.post(
        "/assemblyline",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
    )

    assert response.status_code == 401


@patch("storage.storage.get_session")
@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("api_gateway.routers.scans.get_session")
def test_send_to_assemblyline(mock_db_session, mock_client, mock_aws_session):
    os.environ["FILE_QUEUE_BUCKET"] = "foo"
    filename = "tests/api_gateway/fixtures/file.txt"

    response = client.post(
        "/assemblyline",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    mock_client().ingest.assert_called_once()
    assert response.status_code == 200
    assert response.json() == {"status": "OK", "scan_id": ANY}


@patch("storage.storage.get_session")
@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_send_to_assemblyline_error(mock_db_session, mock_client, mock_aws_session):
    mock_client().ingest.side_effect = HTTPError()
    filename = "tests/api_gateway/fixtures/file.txt"

    response = client.post(
        "/assemblyline",
        files={"file": ("random_file", open(filename, "rb"), "text/plain")},
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.json() == {"error": "error sending file to assemblyline"}
    assert response.status_code == 502


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_get_assemblyline_results_completed(mock_db_session, mock_client, session):
    scan = ScanFactory()
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(scan.id)

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid

    mock_client().ingest.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert response.json() == {"status": "completed", "verdict": "clean"}
    assert response.status_code == 200

    assert updated_scan.sha256 == random_uuid


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_get_assemblyline_results_polled_empty(mock_db_session, mock_client, session):
    scan = ScanFactory()
    session.commit()

    mock_client().ingest.get_message.return_value = None

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert updated_scan.completed is None
    assert response.json() == {"status": ScanVerdicts.IN_PROGRESS.value}
    assert response.status_code == 200


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_get_assemblyline_results_inprogress(mock_db_session, mock_client, session):
    scan = ScanFactory()
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(uuid4())

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid

    mock_client().ingest.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert updated_scan.completed is None
    assert response.json() == {"status": ScanVerdicts.IN_PROGRESS.value}
    assert response.status_code == 200


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_get_assemblyline_results_upstream_scan_error(
    mock_db_session, mock_client, session
):
    scan = ScanFactory(sha256=None)
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(scan.id)

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid
    al_result["error_count"] = 1
    del al_result["max_score"]

    mock_client().ingest.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert response.json() == {
        "status": "completed",
        "verdict": ScanVerdicts.ERROR.value,
    }
    assert response.status_code == 200
    assert updated_scan.sha256 is None


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_get_assemblyline_results_upstream_malicious_file(
    mock_db_session, mock_client, session
):
    scan = ScanFactory()
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(scan.id)

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid
    al_result["max_score"] = 1000

    mock_client().ingest.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert response.json() == {
        "status": "completed",
        "verdict": ScanVerdicts.MALICIOUS.value,
    }
    assert response.status_code == 200
    assert updated_scan.sha256 == random_uuid


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_get_assemblyline_results_already_processed(
    mock_db_session, mock_client, session
):
    scan = ScanFactory(
        completed="2021-12-12T17:20:03.930469Z",
        verdict=ScanVerdicts.CLEAN.value,
        sha256="bar",
    )
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(scan.id)

    al_result = json.loads(load_fixture("assemblyline_results.json"))

    mock_client().ingest.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert response.json() == {
        "status": "completed",
        "verdict": ScanVerdicts.CLEAN.value,
    }
    assert response.status_code == 200
    assert updated_scan.sha256 == "bar"


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_get_assemblyline_results_random_sql_error(
    mock_db_session, mock_client, session
):
    scan = ScanFactory()
    session.commit()
    mock_db_session.side_effect = SQLAlchemyError()

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.json() == {"error": "error updating scan details"}
    assert response.status_code == 500


@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("database.db.get_session")
def test_get_assemblyline_results_random_assemblyline_error(
    mock_db_session, mock_client, session
):
    scan = ScanFactory()
    session.commit()
    mock_client().ingest.get_message.side_effect = HTTPError()

    response = client.get(
        f"/assemblyline/{str(scan.id)}",
        headers={"Authorization": os.environ["API_AUTH_TOKEN"]},
    )

    assert response.json() == {
        "error": "error retrieving scan results from assemblyline"
    }
    assert response.status_code == 502


def test_assemblyline_score_to_verdict():
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, -1000)
        == ScanVerdicts.CLEAN.value
    )
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, 1)
        == ScanVerdicts.CLEAN.value
    )
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, 299)
        == ScanVerdicts.CLEAN.value
    )
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, 300)
        == ScanVerdicts.SUSPICIOUS.value
    )
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, 699)
        == ScanVerdicts.SUSPICIOUS.value
    )
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, 700)
        == ScanVerdicts.SUSPICIOUS.value
    )
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, 999)
        == ScanVerdicts.SUSPICIOUS.value
    )
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, 1000)
        == ScanVerdicts.MALICIOUS.value
    )
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, 10000)
        == ScanVerdicts.MALICIOUS.value
    )

    # Test for error conditions
    assert determine_verdict("foo", -1000) == ScanVerdicts.ERROR.value
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, "foo")
        == ScanVerdicts.ERROR.value
    )
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, -1)
        == ScanVerdicts.UNKNOWN.value
    )
    assert determine_verdict(None, None) == ScanVerdicts.ERROR.value
    assert (
        determine_verdict(ScanProviders.ASSEMBLYLINE.value, None)
        == ScanVerdicts.ERROR.value
    )
    assert determine_verdict(None, 100) == ScanVerdicts.ERROR.value


@patch("storage.storage.get_session")
@patch("api_gateway.routers.scans.get_assemblyline_client")
@patch("api_gateway.routers.scans.get_session")
def test_send_to_assemblyline_save_to_s3(
    mock_db_session, mock_client, mock_aws_session, session
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
