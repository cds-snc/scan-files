import os
from fastapi.testclient import TestClient
from unittest.mock import patch
from importlib import reload

from api_gateway import api
from sqlalchemy.exc import SQLAlchemyError

client = TestClient(api.app)


def test_version_with_no_GIT_SHA():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "unknown"}


@patch.dict(os.environ, {"GIT_SHA": "foo"}, clear=True)
def test_version_with_GIT_SHA():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "foo"}


@patch("api_gateway.routers.ops.get_db_version")
def test_healthcheck_success(mock_get_db_version):
    mock_get_db_version.return_value = "foo"
    response = client.get("/healthcheck")
    assert response.status_code == 200
    expected_val = {"database": {"able_to_connect": True, "db_version": "foo"}}
    assert response.json() == expected_val


@patch("api_gateway.routers.ops.get_db_version")
@patch("api_gateway.routers.ops.log")
def test_healthcheck_failure(mock_log, mock_get_db_version):
    mock_get_db_version.side_effect = SQLAlchemyError()
    response = client.get("/healthcheck")
    assert response.status_code == 200
    expected_val = {"database": {"able_to_connect": False}}
    assert response.json() == expected_val


@patch.dict(os.environ, {"OPENAPI_URL": "", "API_AUTH_TOKEN": "secret"}, clear=True)
def test_api_docs_disabled_via_environ():
    reload(api)

    response = client.get("/docs")
    assert response.status_code == 404

    response = client.get("/redoc")
    assert response.status_code == 404

    response = client.get("/openapi.json")
    assert response.status_code == 404


@patch.dict(
    os.environ, {"OPENAPI_URL": "/openapi.json", "API_AUTH_TOKEN": "secret"}, clear=True
)
def test_api_docs_enabled_via_environ():
    reload(api)

    my_client = TestClient(api.app)
    response = my_client.get("/docs")
    assert response.status_code == 200

    response = my_client.get("/redoc")
    assert response.status_code == 200

    response = my_client.get("/openapi.json")
    assert response.status_code == 200


def test_security_headers_in_response(hsts_middleware_client):
    response = hsts_middleware_client.get("/version")
    assert response.status_code == 200
    assert (
        response.headers["Strict-Transport-Security"]
        == "max-age=63072000; includeSubDomains; preload"
    )

    assert (
        response.headers["Content-Security-Policy"]
        == "report-uri https://csp-report-to.security.cdssandbox.xyz/report; default-src 'none'; script-src 'self'; script-src-elem https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/ 'sha256-QOOQu4W1oxGqd2nbXbxiA1Di6OHQOLQD+o+G9oWL8YY='; connect-src 'self'; img-src 'self' https://fastapi.tiangolo.com/img/ data: 'unsafe-eval'; style-src 'self'; style-src-elem 'self' https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/; frame-ancestors 'self'; form-action 'self';"
    )
