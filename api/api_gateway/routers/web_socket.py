from database.db import get_db_version, get_session
from fastapi import APIRouter, Depends, WebSocket
from logger import log
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

router = APIRouter()


@router.websocket("/healthcheck")
async def healthcheck(websocket: WebSocket, session: Session = Depends(get_session)):
    await websocket.accept()
    try:
        full_name = get_db_version(session)
        db_status = {"able_to_connect": True, "db_version": full_name}
    except SQLAlchemyError as err:
        log.error(err)
        db_status = {"able_to_connect": False}
    await websocket.send_text({"database": db_status})
    await websocket.close()
