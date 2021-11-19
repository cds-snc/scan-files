from fastapi import HTTPException, Request
from os import environ
from uuid import uuid4

API_AUTH_TOKEN = environ.get("API_AUTH_TOKEN", uuid4())


async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=63072000; includeSubDomains; preload"
    return response


def verify_token(req: Request):
    token = req.headers.get("Authorization", None)
    if token != API_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
