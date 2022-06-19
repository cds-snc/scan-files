import os
import pytest

from alembic.config import Config
from alembic import command
from factories import ScanFactory
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api_gateway import api
from api_gateway.custom_middleware import add_security_headers
from api_gateway.routers import ops
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock


@pytest.fixture(scope="session")
def client():
    client = TestClient(api.app)
    yield client


@pytest.fixture
def assert_new_model_saved():
    def f(model):
        assert model.id is not None
        assert model.created_at is not None
        assert model.updated_at is None

    return f


@pytest.fixture
def context_fixture():
    context = MagicMock()
    context.function_name = "api"
    return context


@pytest.fixture(scope="session")
def assemblyline_results():
    open("tests/api_gateway/fixtures/assemblyline_results.json", "rb")


@pytest.fixture(scope="session")
def session():
    db_engine = create_engine(os.environ.get("SQLALCHEMY_DATABASE_TEST_URI"))
    Session = sessionmaker(bind=db_engine)
    session = Session()
    ScanFactory._meta.sqlalchemy_session = session
    return session


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    os.environ["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "SQLALCHEMY_DATABASE_TEST_URI"
    )
    alembic_cfg = Config("./db_migrations/alembic.ini")
    alembic_cfg.set_main_option("script_location", "./db_migrations")
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")
    yield


# https://github.com/tiangolo/fastapi/issues/1472; has to be tested seperate from Jinja2 routes
@pytest.fixture
def hsts_middleware_client():
    app = FastAPI()
    app.add_middleware(BaseHTTPMiddleware, dispatch=add_security_headers)
    app.include_router(ops.router)
    client = TestClient(app)
    yield client


@pytest.fixture
def mock_s3_download():
    download = {}
    download["s3_path"] = "s3://bucket/prefix/definitions.json"
    download[
        "local_path"
    ] = "/tmp/definitions.json"  # nosec - [B108:hardcoded_tmp_directory] no risk in tests

    return download
