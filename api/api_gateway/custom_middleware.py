from fastapi import HTTPException, Request
from os import environ
from uuid import uuid4
from logger import CustomLogger
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

    # Inject a custom logger into the request object if API wasn't invoked by a lambda function
    if "aws.context" not in request.scope:
        request.scope["aws.context"] = types.SimpleNamespace()
        request.scope["aws.context"].logger = CustomLogger("scan-files", None)

    log = request.scope["aws.context"].logger.log
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
