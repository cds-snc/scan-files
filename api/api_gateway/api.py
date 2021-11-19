from aws_lambda_powertools import Metrics
from fastapi import FastAPI
from os import environ
from pydantic import BaseSettings
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4

from .custom_middleware import add_security_headers
from .routers import ops, scans


class Settings(BaseSettings):
    openapi_url: str = environ.get("OPENAPI_URL", "")


settings = Settings()
API_AUTH_TOKEN = environ.get("API_AUTH_TOKEN", uuid4())
MLWR_HOST = environ.get("MLWR_HOST")
MLWR_USER = environ.get("MLWR_USER")
MLWR_KEY = environ.get("MLWR_KEY")


description = """
Scan files 📁 API. Submit files for malware scanning
"""
app = FastAPI(
    title="Scan Files",
    description=description,
    version="0.0.1",
    openapi_url=settings.openapi_url,
)

app.include_router(ops.router)
app.include_router(scans.router)

# https://github.com/tiangolo/fastapi/issues/1472; can't include custom middlware when running tests
if environ.get("CI") is None:
    app.add_middleware(BaseHTTPMiddleware, dispatch=add_security_headers)

metrics = Metrics(namespace="ScanFiles", service="api")
