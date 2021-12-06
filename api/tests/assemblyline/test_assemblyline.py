import json
import os
from uuid import uuid4
from api_gateway import api
from assemblyline.assemblyline import (
    determine_verdict,
    launch_scan,
    poll_for_results,
    resubmit_stale_scans,
)
from datetime import datetime, timedelta
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
    mock_client().submit.assert_called_once()
    assert response is True


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
@patch("database.db.db_session")
def test_send_to_assemblyline_error(mock_db_session, mock_client, mock_aws_session):
    mock_client().submit.side_effect = HTTPError()
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
    mock_client().submit.assert_called_once()


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_completed(mock_client, mock_aws_session, session):
    scan = ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value, meta_data={"sid": "123"})
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(scan.id)

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid

    mock_client().submit.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = poll_for_results(str(scan.id))
    assert response is True

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert updated_scan.verdict == ScanVerdicts.CLEAN.value
    assert updated_scan.sha256 == random_uuid


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_invalid_scan_id(
    mock_client, mock_aws_session, session
):
    ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value, meta_data={"sid": "123"})
    session.commit()

    response = poll_for_results(str(uuid4()))
    assert response is False


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_inprogress(mock_client, mock_aws_session, session):
    scan = ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value, meta_data={"sid": "123"})
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(uuid4())

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid
    al_result["state"] = "scanning"

    mock_client().submit.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = poll_for_results(str(scan.id))
    assert response is False

    updated_scan = session.query(Scan).filter(Scan.id == scan.id).one_or_none()

    assert updated_scan.completed is None
    assert updated_scan.verdict == ScanVerdicts.IN_PROGRESS.value


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_upstream_malicious_file(
    mock_client, mock_aws_session, session
):
    scan = ScanFactory(meta_data={"sid": "123"})
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(scan.id)

    al_result = json.loads(load_fixture("assemblyline_results.json"))
    random_uuid = str(uuid4())
    al_result["files"][0]["sha256"] = random_uuid
    al_result["max_score"] = 1000

    mock_client().submit.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = poll_for_results(str(scan.id))
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
        meta_data={"sid": "123"},
    )
    session.commit()

    al_request = json.loads(load_fixture("assemblyline_request.json"))
    al_request["submission"]["metadata"]["scan_id"] = str(scan.id)

    al_result = json.loads(load_fixture("assemblyline_results.json"))

    mock_client().submit.get_message.return_value = al_request
    mock_client().submission.return_value = al_result

    response = poll_for_results(str(scan.id))
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
    scan = ScanFactory(meta_data={"sid": "123"})
    session.commit()
    mock_db_session.side_effect = SQLAlchemyError()

    response = poll_for_results(str(scan.id))

    assert response is False


@patch("assemblyline.assemblyline.get_session")
@patch("assemblyline.assemblyline.get_client")
def test_get_assemblyline_results_random_assemblyline_error(
    mock_client, mock_aws_session, session
):
    scan = ScanFactory(meta_data={"sid": "123"})
    session.commit()
    mock_client().submit.get_message.side_effect = HTTPError()

    response = poll_for_results(str(scan.id))
    assert response is False


@patch("assemblyline.assemblyline.add_to_scan_queue")
def test_rescan_to_scan_queue(mock_scan_queue, session):
    current_time = datetime.utcnow()
    four_weeks_ago = current_time - timedelta(weeks=4)
    two_days_ago = current_time - timedelta(days=2)
    one_day_ago = current_time - timedelta(days=1)

    ScanFactory(verdict=None, submitted=four_weeks_ago)
    ScanFactory(verdict=None, submitted=two_days_ago)
    ScanFactory(verdict=None, submitted=one_day_ago)
    ScanFactory(verdict=None, submitted=current_time)
    ScanFactory(verdict=ScanVerdicts.CLEAN.value, submitted=two_days_ago)
    session.commit()
    assert resubmit_stale_scans() is True

    assert mock_scan_queue.call_count == 3


@patch("assemblyline.assemblyline.add_to_scan_queue")
@patch("assemblyline.assemblyline.get_db_session")
def test_rescan_to_scan_queue_sql_error(mock_db_session, mock_scan_queue):
    mock_db_session().__next__().query.side_effect = SQLAlchemyError()

    assert resubmit_stale_scans() is False
    assert mock_scan_queue.call_count == 0


@patch("assemblyline.assemblyline.add_to_scan_queue")
def test_rescan_to_scan_queue_random_error(mock_scan_queue):
    mock_scan_queue.side_effect = HTTPError()
    assert resubmit_stale_scans() is False


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
