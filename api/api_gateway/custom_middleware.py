from fastapi import HTTPException, Request
from logger import log
from os import environ
import time


API_AUTH_TOKEN = environ.get("API_AUTH_TOKEN")


async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = (
        "max-age=63072000; includeSubDomains; preload"
    )

    response.headers["Content-Security-Policy"] = (
        "report-uri https://csp-report-to.security.cdssandbox.xyz/report; default-src 'none'; script-src 'self'; script-src-elem https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/ 'sha256-QOOQu4W1oxGqd2nbXbxiA1Di6OHQOLQD+o+G9oWL8YY='; connect-src 'self'; img-src 'self' https://fastapi.tiangolo.com/img/ data: 'unsafe-eval'; style-src 'self'; style-src-elem 'self' https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/; frame-ancestors 'self'; form-action 'self';"
    )
    return response


async def log_requests(request: Request, call_next):
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
        log.info(
            f"Unauthorized: token '{redact(token)}' != expected '{redact(API_AUTH_TOKEN)}'"
        )
        raise HTTPException(status_code=401, detail="Unauthorized API request")
    return True


def redact(value: str):
    "Redact value if it is a string and longer than 6 characters"
    show_chars = 6
    if isinstance(value, str) and len(value) > show_chars:
        return (len(value) - show_chars) * "*" + value[-show_chars:]
    else:
        return value
