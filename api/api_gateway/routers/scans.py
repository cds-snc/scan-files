from api_gateway.custom_middleware import verify_token
from assemblyline.assemblyline import add_to_scan_queue
from database.db import get_db_session
from fastapi import APIRouter, Depends, File, Response, status, UploadFile
from logger import log
from models.Scan import Scan, ScanProviders, ScanVerdicts
from storage.storage import put_file
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from uuid import UUID

router = APIRouter()


@router.post("/assemblyline")
def start_assemblyline_scan(
    response: Response,
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    _authorized: bool = Depends(verify_token),
):
    try:
        save_path = put_file(file)
        scan = Scan(
            file_name=file.filename,
            save_path=save_path,
            scan_provider=ScanProviders.ASSEMBLYLINE.value,
        )
        session.add(scan)
        session.commit()

        add_to_scan_queue({"scan_id": str(scan.id)})

    except Exception as err:
        log.error(err)
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return {"error": f"error sending file [{file}] to scan queue"}

    return {"status": "OK", "scan_id": str(scan.id)}


@router.get("/assemblyline/{scan_id}")
def get_assemblyline_scan_results(
    response: Response,
    scan_id: UUID,
    session: Session = Depends(get_db_session),
    _authorized: bool = Depends(verify_token),
):
    try:
        scan = session.query(Scan).filter(Scan.id == scan_id).one_or_none()
        if scan and scan.completed:
            return {"status": "completed", "verdict": scan.verdict}
        return {"status": ScanVerdicts.IN_PROGRESS.value}

    except SQLAlchemyError as err:
        log.error(err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "error retrieving scan details"}
