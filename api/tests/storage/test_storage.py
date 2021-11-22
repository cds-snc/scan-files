import os
import re

from storage import storage
from unittest.mock import MagicMock, patch, call


def load_fixture(name):
    fixture = open(f"tests/storage/fixtures/{name}", "r")
    return fixture.read()


def mock_record(name="bucket_name"):
    return {"s3": {"bucket": {"name": name}, "object": {"key": "key"}}}


@patch("storage.storage.log")
@patch("storage.storage.get_session")
def test_get_object(mock_get_session, mock_log):
    mock_client = MagicMock()
    mock_client.Object.return_value.get.return_value.__getitem__.return_value.read.return_value = (
        "body"
    )

    mock_get_session.return_value.resource.return_value = mock_client

    assert storage.get_object(mock_record()) == "body"
    mock_client.Object.assert_called_once_with("bucket_name", "key")
    mock_client.Object().get().__getitem__.assert_called_once_with("Body")
    mock_log.info.assert_called_once_with(
        "Downloaded key from bucket_name with length 4"
    )


@patch("storage.storage.log")
@patch("storage.storage.get_session")
def test_get_object_catch_exception(mock_get_session, mock_log):
    mock_object = MagicMock()
    mock_object.get.side_effect = Exception

    mock_client = MagicMock()
    mock_client.Object.return_value = mock_object

    mock_get_session.return_value.resource.return_value = mock_client

    assert storage.get_object(mock_record()) is False
    mock_log.error.assert_has_calls([call("Error downloading key from bucket_name")])


@patch("storage.storage.log")
@patch("storage.storage.get_session")
@patch.dict(os.environ, {"FILE_QUEUE_BUCKET": "file_queue"}, clear=True)
def test_put_file(mock_get_session, mock_log):
    mock_file = MagicMock()
    mock_file.filename = "file.txt"
    assert re.match("s3://file_queue/file.txt_(.*)", storage.put_file(mock_file))


@patch("storage.storage.log")
@patch("storage.storage.get_session")
@patch.dict(os.environ, {"FILE_QUEUE_BUCKET": "file_queue"}, clear=True)
def test_put_file_catch_exception(mock_get_session, mock_log):
    mock_object = MagicMock()
    mock_object.put.side_effect = Exception

    mock_client = MagicMock()
    mock_client.Object.return_value = mock_object

    mock_get_session.return_value.resource.return_value = mock_client

    mock_file = MagicMock()
    mock_file.filename = "file.txt"

    mock_get_session.return_value.resource.return_value = mock_client

    storage.put_file(mock_file)
    assert storage.put_file(mock_file) is None
    mock_log.error.assert_has_calls([call("Error uploading file.txt to s3")])
