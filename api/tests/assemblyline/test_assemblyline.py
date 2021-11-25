import json
import os
from uuid import uuid4
from api_gateway import api
from assemblyline.assemblyline import determine_verdict, launch_scan, poll_for_results
from factories import ScanFactory
from fastapi.testclient import TestClient
from models.Scan import Scan, ScanProviders, ScanVerdicts
from requests import HTTPError
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch, MagicMock

client = TestClient(api.app)


def load_fixture(name):
    fixture = open(f"tests/assemblyline/fixtures/{name}", "r")
    return fixture.read()


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
@patch("database.db.db_session")
def test_send_to_assemblyline_with_file(mock_db_session, mock_client, mock_aws_session):
    os.environ["FILE_QUEUE_BUCKET"] = "foo"
    filename = "tests/api_gateway/fixtures/file.txt"

    response = launch_scan("execution_id", "scan_id", open(filename, "rb"))
    mock_client().ingest.assert_called_once()
    assert response is True


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
@patch("database.db.db_session")
def test_send_to_assemblyline_error(mock_db_session, mock_client, mock_aws_session):
    mock_client().ingest.side_effect = HTTPError()
    filename = "tests/api_gateway/fixtures/file.txt"

    response = launch_scan("execution_id", "scan_id", open(filename, "rb"))
    assert response is False


@patch("storage.storage.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_send_to_assemblyline_retrieve_from_s3(mock_client, mock_aws_session, session):
    scan = ScanFactory(save_path="s3://foo/file.txt")
    session.commit()

    filename = "tests/api_gateway/fixtures/file.txt"
    mock_return = MagicMock()
    mock_return.Object.return_value.download_file.return_value.__getitem__.return_value.read.return_value = open(
        filename, "rb"
    )

    mock_aws_session.return_value.resource.return_value = mock_return

    os.environ["FILE_QUEUE_BUCKET"] = "foo"
    launch_scan("execution_id", str(scan.id))
    mock_client().ingest.assert_called_once()


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_completed(mock_client, mock_aws_session, session):
    scan = ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value)
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(scan.id)

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid

    mock_client().ingest.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = poll_for_results()
    assert response is True

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert updated_scan.verdict == ScanVerdicts.CLEAN.value
    assert updated_scan.sha256 == random_uuid


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_polled_empty(mock_client, mock_aws_session, session):
    scan = ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value)
    session.commit()

    mock_client().ingest.get_message.return_value = None

    response = poll_for_results()
    assert response is True

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert updated_scan.completed is None
    assert updated_scan.verdict == ScanVerdicts.IN_PROGRESS.value


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_inprogress(mock_client, mock_aws_session, session):
    scan = ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value)
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(uuid4())

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid

    mock_client().ingest.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = poll_for_results()
    assert response is False

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert updated_scan.completed is None
    assert updated_scan.verdict == ScanVerdicts.IN_PROGRESS.value


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_upstream_scan_error(
    mock_client, mock_aws_session, session
):
    scan = ScanFactory(sha256=None, verdict=ScanVerdicts.IN_PROGRESS.value)
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(scan.id)

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid
    del al_result["max_score"]

    mock_client().ingest.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = poll_for_results()
    assert response is True

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()
    assert updated_scan.verdict == ScanVerdicts.ERROR.value
    assert updated_scan.sha256 is None


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_upstream_malicious_file(
    mock_client, mock_aws_session, session
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

    response = poll_for_results()
    assert response is True

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()
    assert updated_scan.verdict == ScanVerdicts.MALICIOUS.value
    assert updated_scan.sha256 == random_uuid


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_already_processed(
    mock_client, mock_aws_session, session
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

    response = poll_for_results()
    assert response is False

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()
    assert updated_scan.verdict == ScanVerdicts.CLEAN.value
    assert updated_scan.sha256 == "bar"


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
@patch("database.db.db_session")
def test_get_assemblyline_results_random_sql_error(
    mock_db_session, mock_client, mock_aws_session, session
):
    ScanFactory()
    session.commit()
    mock_db_session.side_effect = SQLAlchemyError()

    response = poll_for_results()

    assert response is False


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_random_assemblyline_error(
    mock_client, mock_aws_session, session
):
    ScanFactory()
    session.commit()
    mock_client().ingest.get_message.side_effect = HTTPError()

    response = poll_for_results()
    assert response is False


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
