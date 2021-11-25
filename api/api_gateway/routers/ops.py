from os import environ
from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database.db import get_db_version, get_db_session
from logger import log

router = APIRouter()

# Dependency


@router.get("/version")
def version():
    return {"version": environ.get("GIT_SHA", "unknown")}


@router.get("/healthcheck")
def healthcheck(session: Session = Depends(get_db_session)):
    try:
        full_name = get_db_version(session)
        db_status = {"able_to_connect": True, "db_version": full_name}
    except SQLAlchemyError as err:
        log.error(err)
        db_status = {"able_to_connect": False}

    return {"database": db_status}
