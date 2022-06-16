import errno
import pytest
from unittest.mock import patch

from clamav_scanner.common import create_dir


@patch("clamav_scanner.common.os.path")
@patch("clamav_scanner.common.os")
def test_create_dir_already_exists(mock_os, mock_path):
    mock_path.exists.return_value = True
    create_dir("testpath")
    assert mock_os.makedirs.called is False


@patch("clamav_scanner.common.os.path")
@patch("clamav_scanner.common.os")
def test_create_dir_doesnt_exist(mock_os, mock_path):
    mock_path.exists.return_value = False
    create_dir("testpath")
    assert mock_os.makedirs.called is True


@patch("clamav_scanner.common.os.path")
@patch("clamav_scanner.common.os")
def test_create_dir_doesnt_exist_no_raises(mock_os, mock_path):
    mock_path.exists.return_value = False
    mock_os.makedirs.side_effect = OSError(errno.EEXIST, "exists")
    create_dir("testpath")
    assert mock_os.makedirs.called is True


@patch("clamav_scanner.common.os.path")
@patch("clamav_scanner.common.os")
def test_create_dir_doesnt_exist_but_raises(mock_os, mock_path):
    mock_path.exists.return_value = False
    mock_os.makedirs.side_effect = OSError(errno.ENAMETOOLONG, "nametoolong")
    with pytest.raises(OSError):
        create_dir("testpath")

    mock_os.makedirs.called is True
