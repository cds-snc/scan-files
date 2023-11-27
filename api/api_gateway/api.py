from aws_lambda_powertools import Metrics
from fastapi import FastAPI
from os import environ
from pydantic_settings import BaseSettings
from starlette.middleware.base import BaseHTTPMiddleware

from .custom_middleware import add_security_headers, log_requests
from .routers import ops, assemblyline, clamav


class Settings(BaseSettings):
    openapi_url: str = environ.get("OPENAPI_URL", "")


settings = Settings()
API_AUTH_TOKEN = environ.get("API_AUTH_TOKEN")
MLWR_HOST = environ.get("MLWR_HOST")
MLWR_USER = environ.get("MLWR_USER")
MLWR_KEY = environ.get("MLWR_KEY")

if not API_AUTH_TOKEN:
    raise Exception("API_AUTH_TOKEN environment variable is not set")

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
app.include_router(assemblyline.router, prefix="/assemblyline", tags=["assemblyline"])
app.include_router(clamav.router, prefix="/clamav", tags=["clamav"])
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)
app.add_middleware(BaseHTTPMiddleware, dispatch=add_security_headers)

metrics = Metrics(namespace="ScanFiles", service="api")
