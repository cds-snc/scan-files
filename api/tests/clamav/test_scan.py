from unittest.mock import patch, ANY, MagicMock
from clamav_scanner.common import AV_SIGNATURE_OK, AV_STATUS_CLEAN
from clamav_scanner.scan import launch_scan, sns_scan_results
from factories import ScanFactory
from models.Scan import ScanVerdicts


@patch("clamav_scanner.scan.sns_scan_results")
@patch("clamav_scanner.scan.scan_file")
@patch("clamav_scanner.scan.update_defs_from_s3")
@patch("clamav_scanner.scan.get_session")
@patch("clamav_scanner.scan.get_db_session")
def test_clamav_scan(
    mock_db_session,
    mock_aws_session,
    mock_update_defs_from_s3,
    mock_scan_file,
    mock_sns_scan_results,
    mock_s3_download,
    session,
):
    scan = ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value, meta_data={"sid": "123"})
    session.commit()

    mock_update_defs_from_s3.return_value.values.return_value = [mock_s3_download]
    mock_scan_file.return_value = (
        AV_STATUS_CLEAN,
        AV_SIGNATURE_OK,
        "/foo/bar/file.txt",
    )
    scan_verdict = launch_scan(
        "/tmp/foo",  # nosec - [B108:hardcoded_tmp_directory] no risk in tests
        scan.id,
        session=session,
    )

    mock_aws_session().resource().Bucket().download_file.assert_called_once_with(
        mock_s3_download["s3_path"],
        mock_s3_download["local_path"],
    )

    assert scan_verdict == ScanVerdicts.CLEAN.value
    assert scan.verdict == ScanVerdicts.CLEAN.value
    assert mock_sns_scan_results.called is False


@patch("clamav_scanner.scan.get_session")
@patch("clamav_scanner.scan.get_db_session")
def test_sns_scan_results(mock_db_session, mock_aws_session, session):
    scan = ScanFactory(verdict=ScanVerdicts.CLEAN.value, meta_data={"sid": "123"}, completed="2021-12-12T17:20:03.930469Z")
    session.commit()
    mock_sns_client = MagicMock()
    sns_scan_results(
        mock_sns_client,
        scan,
        "arn:aws:sns:ca-central-1:000000000000:clamav_scan-topic",
        AV_SIGNATURE_OK,
        "/foo/bar/file.txt",
    )
    mock_sns_client.publish.assert_called_once_with(
        TargetArn="arn:aws:sns:ca-central-1:000000000000:clamav_scan-topic",
        Message=ANY,
        MessageStructure="json",
        MessageAttributes={
            "av-filepath": {"DataType": "String", "StringValue": "/foo/bar/file.txt"},
            "av-status": {"DataType": "String", "StringValue": "clean"},
            "av-signature": {"DataType": "String", "StringValue": "OK"},
        },
    )
