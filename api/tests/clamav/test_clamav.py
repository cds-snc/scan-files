import botocore.session
import datetime
import os
import re
import textwrap

from botocore.stub import Stubber
from unittest.mock import patch, MagicMock

from clamav_scanner.clamav import rd_ld
from clamav_scanner.clamav import scan_output_to_json
from clamav_scanner.clamav import md5_from_s3_tags
from clamav_scanner.clamav import time_from_s3
from clamav_scanner.clamav import update_defs_from_s3
from clamav_scanner.common import AV_DEFINITION_FILE_PREFIXES
from clamav_scanner.common import AV_DEFINITION_FILE_SUFFIXES
from clamav_scanner.common import AV_DEFINITION_S3_PREFIX
from clamav_scanner.common import AV_SIGNATURE_OK


s3_bucket_name = "test_bucket"
s3_key_name = "test_key"
s3_client = botocore.session.get_session().create_client("s3")


def test_current_library_search_path():
    # Calling `ld --verbose` returns a lot of text but the line to check is this one:
    search_path = """SEARCH_DIR("=/usr/x86_64-redhat-linux/lib64"); SEARCH_DIR("=/usr/lib64"); SEARCH_DIR("=/usr/local/lib64"); SEARCH_DIR("=/lib64"); SEARCH_DIR("=/usr/x86_64-redhat-linux/lib"); SEARCH_DIR("=/usr/local/lib"); SEARCH_DIR("=/lib"); SEARCH_DIR("=/usr/lib");"""  # noqa
    all_search_paths = rd_ld.findall(search_path)
    expected_search_paths = [
        "/usr/x86_64-redhat-linux/lib64",
        "/usr/lib64",
        "/usr/local/lib64",
        "/lib64",
        "/usr/x86_64-redhat-linux/lib",
        "/usr/local/lib",
        "/lib",
        "/usr/lib",
    ]

    assert all_search_paths == expected_search_paths


def test_scan_output_to_json_clean():
    file_path = "/clamav/test.txt"
    signature = AV_SIGNATURE_OK
    output = textwrap.dedent(
        """\
  Scanning {0}
  {0}: {1}
  ----------- SCAN SUMMARY -----------
  Known viruses: 6305127
  Engine version: 0.101.4
  Scanned directories: 0
  Scanned files: 1
  Infected files: 0
  Data scanned: 0.00 MB
  Data read: 0.00 MB (ratio 0.00:1)
  Time: 80.299 sec (1 m 20 s)
  """.format(
            file_path, signature
        )
    )
    summary = scan_output_to_json(output)
    assert summary[file_path] == "OK"
    assert summary["Infected files"] == "0"


def test_scan_output_to_json_infected():
    file_path = "/clamav/eicar.com.txt"
    signature = "Eicar-Test-Signature FOUND"
    output = textwrap.dedent(
        """\
  Scanning {0}
  {0}: {1}
  {0}!(0): {1}
  ----------- SCAN SUMMARY -----------
  Known viruses: 6305127
  Engine version: 0.101.4
  Scanned directories: 0
  Scanned files: 1
  Infected files: 1
  Data scanned: 0.00 MB
  Data read: 0.00 MB (ratio 0.00:1)
  Time: 80.299 sec (1 m 20 s)
  """.format(
            file_path, signature
        )
    )
    summary = scan_output_to_json(output)
    assert summary[file_path] == signature
    assert summary["Infected files"] == "1"


def test_md5_from_s3_tags_no_md5():
    tag_set = {"TagSet": []}

    mock_s3_client = MagicMock()
    mock_s3_client.return_value.get_object_tagging.return_value = tag_set
    md5_hash = md5_from_s3_tags(mock_s3_client, s3_bucket_name, s3_key_name)

    mock_s3_client.get_object_tagging.assert_called_once_with(
        Bucket=s3_bucket_name, Key=s3_key_name
    )
    assert md5_hash == ""


def test_md5_from_s3_tags_has_md5():
    expected_md5_hash = "d41d8cd98f00b204e9800998ecf8427e"
    tag_set = [{"Key": "md5", "Value": expected_md5_hash}]

    mock_s3_client = MagicMock()

    mock_s3_client.get_object_tagging().__getitem__.return_value = tag_set
    md5_hash = md5_from_s3_tags(mock_s3_client, s3_bucket_name, s3_key_name)

    assert md5_hash == expected_md5_hash


def test_time_from_s3():
    expected_s3_time = datetime.datetime(2019, 1, 1)

    mock_s3_client = MagicMock()
    mock_s3_client.head_object().__getitem__.return_value = expected_s3_time

    s3_time = time_from_s3(mock_s3_client, s3_bucket_name, s3_key_name)

    assert s3_time == expected_s3_time


@patch("clamav_scanner.clamav.md5_from_file")
@patch("clamav_scanner.common.os.path.exists")
def test_update_defs_from_s3(mock_exists, mock_md5_from_file):
    expected_md5_hash = "d41d8cd98f00b204e9800998ecf8427e"
    different_md5_hash = "d41d8cd98f00b204e9800998ecf8427f"

    mock_md5_from_file.return_value = different_md5_hash

    tag_set = [{"Key": "md5", "Value": expected_md5_hash}]
    expected_s3_time = datetime.datetime(2019, 1, 1)

    mock_s3_client = MagicMock()
    mock_s3_client.head_object().__getitem__.return_value = expected_s3_time
    mock_s3_client.get_object_tagging().__getitem__.return_value = tag_set

    key_names = []
    side_effect = []
    for file_prefix in AV_DEFINITION_FILE_PREFIXES:
        for file_suffix in AV_DEFINITION_FILE_SUFFIXES:
            side_effect.extend([True, True])
            filename = file_prefix + "." + file_suffix
            key_names.append(os.path.join(AV_DEFINITION_S3_PREFIX, filename))
    mock_exists.side_effect = side_effect

    expected_to_download = {
        "bytecode": {
            "local_path": "/clamav/clamav_defs/bytecode.cvd",
            "s3_path": "clamav_defs/bytecode.cvd",
        },
        "daily": {
            "local_path": "/clamav/clamav_defs/daily.cvd",
            "s3_path": "clamav_defs/daily.cvd",
        },
        "main": {
            "local_path": "/clamav/clamav_defs/main.cvd",
            "s3_path": "clamav_defs/main.cvd",
        },
    }

    to_download = update_defs_from_s3(
        mock_s3_client, s3_bucket_name, AV_DEFINITION_S3_PREFIX
    )
    assert expected_to_download == to_download


@patch("clamav_scanner.clamav.md5_from_file")
@patch("clamav_scanner.common.os.path.exists")
def test_update_defs_from_s3_same_hash(mock_exists, mock_md5_from_file):
    expected_md5_hash = "d41d8cd98f00b204e9800998ecf8427e"
    different_md5_hash = expected_md5_hash

    mock_md5_from_file.return_value = different_md5_hash

    tag_set = {"TagSet": [{"Key": "md5", "Value": expected_md5_hash}]}
    expected_s3_time = datetime.datetime(2019, 1, 1)

    s3_stubber = Stubber(s3_client)

    key_names = []
    side_effect = []
    for file_prefix in AV_DEFINITION_FILE_PREFIXES:
        for file_suffix in AV_DEFINITION_FILE_SUFFIXES:
            side_effect.extend([True, True])
            filename = file_prefix + "." + file_suffix
            key_names.append(os.path.join(AV_DEFINITION_S3_PREFIX, filename))
    mock_exists.side_effect = side_effect

    for s3_key_name in key_names:
        get_object_tagging_response = tag_set
        get_object_tagging_expected_params = {
            "Bucket": s3_bucket_name,
            "Key": s3_key_name,
        }
        s3_stubber.add_response(
            "get_object_tagging",
            get_object_tagging_response,
            get_object_tagging_expected_params,
        )
        head_object_response = {"LastModified": expected_s3_time}
        head_object_expected_params = {
            "Bucket": s3_bucket_name,
            "Key": s3_key_name,
        }
        s3_stubber.add_response(
            "head_object", head_object_response, head_object_expected_params
        )

    expected_to_download = {}
    with s3_stubber:
        to_download = update_defs_from_s3(
            s3_client, s3_bucket_name, AV_DEFINITION_S3_PREFIX
        )

        assert expected_to_download == to_download


@patch("clamav_scanner.clamav.md5_from_file")
@patch("clamav_scanner.common.os.path.exists")
def test_update_defs_from_s3_old_files(mock_exists, mock_md5_from_file):
    expected_md5_hash = "d41d8cd98f00b204e9800998ecf8427e"
    different_md5_hash = "d41d8cd98f00b204e9800998ecf8427f"

    mock_md5_from_file.return_value = different_md5_hash

    tag_set = {"TagSet": [{"Key": "md5", "Value": expected_md5_hash}]}
    expected_s3_time = datetime.datetime(2019, 1, 1)

    s3_stubber = Stubber(s3_client)

    key_names = []
    side_effect = []
    for file_prefix in AV_DEFINITION_FILE_PREFIXES:
        for file_suffix in AV_DEFINITION_FILE_SUFFIXES:
            side_effect.extend([True, True])
            filename = file_prefix + "." + file_suffix
            key_names.append(os.path.join(AV_DEFINITION_S3_PREFIX, filename))
    mock_exists.side_effect = side_effect

    count = 0
    for s3_key_name in key_names:
        get_object_tagging_response = tag_set
        get_object_tagging_expected_params = {
            "Bucket": s3_bucket_name,
            "Key": s3_key_name,
        }
        s3_stubber.add_response(
            "get_object_tagging",
            get_object_tagging_response,
            get_object_tagging_expected_params,
        )
        head_object_response = {
            "LastModified": expected_s3_time - datetime.timedelta(hours=count)
        }
        head_object_expected_params = {
            "Bucket": s3_bucket_name,
            "Key": s3_key_name,
        }
        s3_stubber.add_response(
            "head_object", head_object_response, head_object_expected_params
        )
        count += 1

    expected_to_download = {
        "bytecode": {
            "local_path": "/clamav/clamav_defs/bytecode.cld",
            "s3_path": "clamav_defs/bytecode.cld",
        },
        "daily": {
            "local_path": "/clamav/clamav_defs/daily.cld",
            "s3_path": "clamav_defs/daily.cld",
        },
        "main": {
            "local_path": "/clamav/clamav_defs/main.cld",
            "s3_path": "clamav_defs/main.cld",
        },
    }
    with s3_stubber:
        to_download = update_defs_from_s3(
            s3_client, s3_bucket_name, AV_DEFINITION_S3_PREFIX
        )
        assert expected_to_download == to_download
