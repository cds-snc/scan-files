from fastapi.testclient import TestClient
from unittest.mock import patch

from api_gateway import api
from sqlalchemy.exc import SQLAlchemyError

client = TestClient(api.app)


@patch("api_gateway.routers.web_socket.get_db_version")
def test_healthcheck_success(mock_get_db_version):
    mock_get_db_version.return_value = "foo"
    with client.websocket_connect("/healthcheck") as websocket:
        response = websocket.receive_text()
        expected_val = {"database": {"able_to_connect": True, "db_version": "foo"}}
        assert response == expected_val


@patch("api_gateway.routers.web_socket.get_db_version")
@patch("api_gateway.routers.web_socket.log")
def test_healthcheck_failure(mock_log, mock_get_db_version):
    mock_get_db_version.side_effect = SQLAlchemyError()
    with client.websocket_connect("/healthcheck") as websocket:
        response = websocket.receive_text()
        expected_val = {"database": {"able_to_connect": False}}
        assert response == expected_val
