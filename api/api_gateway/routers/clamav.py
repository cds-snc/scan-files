from api_gateway.custom_middleware import verify_token
from clamav_scanner.common import AV_DEFINITION_PATH, create_dir
from clamav_scanner.scan import launch_scan, launch_background_scan
from database.db import get_db_session
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Query,
    Response,
    Request,
    status,
    UploadFile,
)
from logger import log
from models.Scan import Scan, ScanProviders, ScanVerdicts
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID, uuid4

router = APIRouter()


@router.post("")
def start_clamav_scan(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    ignore_cache: Optional[bool] = Query(False),
    session: Session = Depends(get_db_session),
    _authorized: bool = Depends(verify_token),
):
    log.info("start_clamav_scan")
    try:
        save_path = f"{AV_DEFINITION_PATH}/quarantine/{str(uuid4())}"
        create_dir(f"{AV_DEFINITION_PATH}/quarantine")
        with open(save_path, "wb") as file_on_disk:
            file.file.seek(0)
            file_on_disk.write(file.file.read())

        scan = Scan(
            file_name=file.filename,
            scan_provider=ScanProviders.CLAMAV.value,
        )
        session.add(scan)
        session.commit()

        scan_verdict = launch_scan(save_path, scan.id, ignore_cache=ignore_cache)
        return {"scan_id": str(scan.id), "status": "completed", "verdict": scan_verdict}
    except Exception as err:
        log.error(err)
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return {"error": f"error scanning file [{file.filename}] with clamav"}


@router.post("/s3")
def start_clamav_scan_from_s3(
    request: Request,
    response: Response,
    aws_account: str = Body(...),
    s3_key: str = Body(...),
    sns_arn: str = Body(...),
    session: Session = Depends(get_db_session),
    _authorized: bool = Depends(verify_token),
):
    log.info(f"start_clamav_scan_from_s3: aws_account={aws_account}")
    try:
        filename = s3_key.split("/")[-1]

        scan = Scan(
            file_name=filename,
            scan_provider=ScanProviders.CLAMAV.value,
        )
        session.add(scan)
        session.commit()

        launch_background_scan(
            log.get_correlation_id(),
            s3_key,
            scan.id,
            session=session,
            aws_account=aws_account,
            sns_arn=sns_arn,
        )
        return {"status": "OK", "scan_id": str(scan.id)}

    except Exception as err:
        log.error(err)
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return {"error": f"error scanning file [{s3_key}] with clamav"}


@router.get("/{scan_id}")
def get_clamav_scan_results(
    request: Request,
    response: Response,
    scan_id: UUID,
    session: Session = Depends(get_db_session),
    _authorized: bool = Depends(verify_token),
):
    log.info(f"get_clamav_scan_results: scan_id={scan_id}")
    try:
        scan = session.query(Scan).filter(Scan.id == scan_id).one_or_none()
        if scan and scan.completed:
            return {"status": "completed", "verdict": scan.verdict}
        return {"status": ScanVerdicts.IN_PROGRESS.value}

    except SQLAlchemyError as err:
        log.error(err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "error retrieving scan details"}
