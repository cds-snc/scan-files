from fastapi import HTTPException, Request
from logger import log
from os import environ
from uuid import uuid4
import time
import types


API_AUTH_TOKEN = environ.get("API_AUTH_TOKEN", uuid4())


async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=63072000; includeSubDomains; preload"
    return response


async def log_requests(request: Request, call_next):

    # This should only happen when the app is not running in Lambda
    if "aws.context" not in request.scope:
        request.scope["aws.context"] = types.SimpleNamespace()
        random_id = str(uuid4())
        request.scope["aws.context"].scanning_request_id = random_id
        log.set_correlation_id(random_id)

    log.info(f"start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    log.info(
        f"completed_in={formatted_process_time}ms status_code={response.status_code}"
    )

    return response


def verify_token(req: Request):
    token = req.headers.get("Authorization", None)
    if token != API_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
