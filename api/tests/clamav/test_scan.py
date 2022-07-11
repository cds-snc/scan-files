from unittest.mock import patch, ANY, MagicMock
from clamav_scanner.common import AV_SIGNATURE_OK
from clamav_scanner.scan import launch_scan, sns_scan_results
from factories import ScanFactory
from models.Scan import ScanVerdicts


@patch("clamav_scanner.scan.sns_scan_results")
@patch("clamav_scanner.scan.scan_file")
@patch("clamav_scanner.scan.get_session")
@patch("clamav_scanner.scan.get_db_session")
def test_clamav_scan(
    mock_db_session,
    mock_aws_session,
    mock_scan_file,
    mock_sns_scan_results,
    session,
):
    scan = ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value, meta_data={"sid": "123"})
    session.commit()
    mock_logger = MagicMock()
    mock_scan_file.return_value = (
        "123",
        ScanVerdicts.CLEAN.value,
        AV_SIGNATURE_OK,
        "/foo/bar/file.txt",
    )
    scan_verdict = launch_scan(
        mock_logger,
        "/tmp/foo",  # nosec - [B108:hardcoded_tmp_directory] no risk in tests
        scan.id,
        session=session,
    )

    assert scan_verdict == ScanVerdicts.CLEAN.value
    assert scan.verdict == ScanVerdicts.CLEAN.value
    assert mock_sns_scan_results.called is False


@patch("clamav_scanner.scan.get_session")
@patch("clamav_scanner.scan.get_db_session")
def test_sns_scan_results(mock_db_session, mock_aws_session, session):
    scan = ScanFactory(
        verdict=ScanVerdicts.CLEAN.value,
        meta_data={"sid": "123"},
        completed="2021-12-12T17:20:03.930469Z",
        checksum="123",
    )
    session.commit()
    mock_sns_client = MagicMock()
    mock_logger = MagicMock()
    sns_scan_results(
        mock_logger,
        mock_sns_client,
        scan,
        "arn:aws:sns:ca-central-1:000000000000:clamav_scan-topic",
        AV_SIGNATURE_OK,
        "/foo/bar/file.txt",
        "123456789012",
    )
    mock_sns_client.publish.assert_called_once_with(
        TargetArn="arn:aws:sns:ca-central-1:000000000000:clamav_scan-topic",
        Message=ANY,
        MessageStructure="json",
        MessageAttributes={
            "av-filepath": {"DataType": "String", "StringValue": "/foo/bar/file.txt"},
            "av-checksum": {"DataType": "String", "StringValue": "123"},
            "av-status": {"DataType": "String", "StringValue": "clean"},
            "av-signature": {"DataType": "String", "StringValue": "OK"},
            "aws-account": {"DataType": "String", "StringValue": "123456789012"},
        },
    )


@patch("clamav_scanner.scan.get_session")
@patch("clamav_scanner.scan.get_db_session")
def test_sns_scan_results_error(mock_db_session, mock_aws_session, session):
    scan = ScanFactory(
        verdict=ScanVerdicts.ERROR.value,
        meta_data={"sid": "123"},
        completed="2021-12-12T17:20:03.930469Z",
        checksum="",
    )
    session.commit()
    mock_logger = MagicMock()
    mock_sns_client = MagicMock()
    sns_scan_results(
        mock_logger,
        mock_sns_client,
        scan,
        "arn:aws:sns:ca-central-1:000000000000:clamav_scan-topic",
        AV_SIGNATURE_OK,
        "/foo/bar/file.txt",
        "210987654321",
    )
    mock_sns_client.publish.assert_called_once_with(
        TargetArn="arn:aws:sns:ca-central-1:000000000000:clamav_scan-topic",
        Message=ANY,
        MessageStructure="json",
        MessageAttributes={
            "av-filepath": {"DataType": "String", "StringValue": "/foo/bar/file.txt"},
            "av-checksum": {"DataType": "String", "StringValue": "None"},
            "av-status": {"DataType": "String", "StringValue": "error"},
            "av-signature": {"DataType": "String", "StringValue": "OK"},
            "aws-account": {"DataType": "String", "StringValue": "210987654321"},
        },
    )
