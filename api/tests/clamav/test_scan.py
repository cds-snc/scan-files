from unittest.mock import patch, ANY, MagicMock
from clamav_scanner.clamav import determine_verdict
from clamav_scanner.common import AV_SIGNATURE_OK, AV_SIGNATURE_UNKNOWN
from clamav_scanner.scan import launch_scan, sns_scan_results
from factories import ScanFactory
from models.Scan import ScanProviders, ScanVerdicts


@patch("clamav_scanner.scan.log")
@patch("clamav_scanner.scan.sns_scan_results")
@patch("clamav_scanner.scan.scan_file")
def test_clamav_scan(
    mock_scan_file,
    mock_sns_scan_results,
    mock_log,
    session,
):
    scan = ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value, meta_data={"sid": "123"})
    session.commit()
    mock_scan_file.return_value = (
        "123",
        ScanVerdicts.CLEAN.value,
        AV_SIGNATURE_OK,
        "/foo/bar/file.txt",
    )
    scan_verdict = launch_scan(
        "/tmp/foo",  # nosec - [B108:hardcoded_tmp_directory] no risk in tests
        scan.id,
        session=session,
    )

    assert scan_verdict == ScanVerdicts.CLEAN.value
    assert mock_sns_scan_results.called is False
    assert mock_log.info.called is True
    assert mock_log.warning.called is False


@patch("clamav_scanner.scan.log")
@patch("clamav_scanner.scan.sns_scan_results")
@patch("clamav_scanner.scan.scan_file")
def test_clamav_scan_malicious(
    mock_scan_file,
    mock_sns_scan_results,
    mock_log,
    session,
):
    scan = ScanFactory(verdict=ScanVerdicts.IN_PROGRESS.value, meta_data={"sid": "123"})
    session.commit()
    mock_scan_file.return_value = (
        "123",
        ScanVerdicts.MALICIOUS.value,
        AV_SIGNATURE_OK,
        "/foo/bar/file.txt",
    )
    scan_verdict = launch_scan(
        "/tmp/foo",  # nosec - [B108:hardcoded_tmp_directory] no risk in tests
        scan.id,
        session=session,
    )

    assert scan_verdict == ScanVerdicts.MALICIOUS.value
    assert mock_sns_scan_results.called is False
    mock_log.warning.assert_called_once_with("Scan of /tmp/foo resulted in malicious\n")


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
    sns_scan_results(
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
    mock_sns_client = MagicMock()
    sns_scan_results(
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


@patch("clamav_scanner.clamav.log")
def test_determine_verdict_clamav_clean(mock_log):
    provider = ScanProviders.CLAMAV.value
    path = "/test/path"
    summary = {path: "clean", "Time": "1.000"}
    av_proc = MagicMock()
    av_proc.returncode = 0

    verdict, signature = determine_verdict(provider, path, summary, av_proc)
    assert verdict == ScanVerdicts.CLEAN.value
    assert signature == "clean"


@patch("clamav_scanner.clamav.log")
def test_determine_verdict_clamav_false_positive(mock_log):
    provider = ScanProviders.CLAMAV.value
    path = "/test/path"
    false_positive_signature = "PUA.Pdf.Trojan.EmbeddedJavaScript-1 FOUND"
    summary = {path: false_positive_signature, "Time": "1.000"}
    av_proc = MagicMock()
    av_proc.returncode = 1

    verdict, signature = determine_verdict(provider, path, summary, av_proc)
    assert verdict == ScanVerdicts.CLEAN.value
    assert signature == false_positive_signature


@patch("clamav_scanner.clamav.log")
def test_determine_verdict_clamav_malicious(mock_log):
    provider = ScanProviders.CLAMAV.value
    path = "/test/path"
    summary = {path: "malicious", "Time": "1.000"}
    av_proc = MagicMock()
    av_proc.returncode = 1

    verdict, signature = determine_verdict(provider, path, summary, av_proc)
    assert verdict == ScanVerdicts.MALICIOUS.value
    assert signature == "malicious"


@patch("clamav_scanner.clamav.log")
def test_determine_verdict_clamav_unable_to_scan(mock_log):
    provider = ScanProviders.CLAMAV.value
    path = "/test/path"
    summary = {path: "unknown", "Time": "0.000"}
    av_proc = MagicMock()
    av_proc.returncode = 0

    verdict, signature = determine_verdict(provider, path, summary, av_proc)
    assert verdict == ScanVerdicts.UNABLE_TO_SCAN.value
    assert signature == AV_SIGNATURE_UNKNOWN
    mock_log.error.assert_called()


@patch("clamav_scanner.clamav.log")
def test_determine_verdict_clamav_error(mock_log):
    provider = ScanProviders.CLAMAV.value
    path = "/test/path"
    summary = {path: "unknown", "Time": "1.000"}
    av_proc = MagicMock()
    av_proc.returncode = 2

    verdict, signature = determine_verdict(provider, path, summary, av_proc)
    assert verdict == ScanVerdicts.ERROR.value
    assert signature == AV_SIGNATURE_UNKNOWN
    mock_log.error.assert_called()
