from api_gateway.custom_middleware import verify_token
from api_gateway import run_in_background
from clamav_scanner.common import AV_DEFINITION_PATH, create_dir
from clamav_scanner.scan import launch_scan
from database.db import get_db_session
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    File,
    Response,
    status,
    UploadFile,
)
from logger import log
from models.Scan import Scan, ScanProviders, ScanVerdicts
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

router = APIRouter()


@router.post("")
def start_clamav_scan(
    response: Response,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sns_arn: str = Body(default=None),
    session: Session = Depends(get_db_session),
    _authorized: bool = Depends(verify_token),
):
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

        if sns_arn not in [None, ""]:
            log.info("Processing scan with sns_arn: %s" % sns_arn)
            background_tasks.add_task(launch_scan, save_path, scan.id, sns_arn=sns_arn)
            return {"status": "OK", "scan_id": str(scan.id)}
        else:
            scan_verdict = launch_scan(save_path, scan.id, sns_arn=sns_arn)
            return {"status": "completed", "verdict": scan_verdict}
    except Exception as err:
        log.error(err)
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return {"error": f"error scanning file [{file.filename}] with clamav"}


@router.post("/s3")
def start_clamav_scan_from_s3(
    response: Response,
    background_tasks: BackgroundTasks,
    aws_account: str = Body(...),
    s3_key: str = Body(...),
    sns_arn: str = Body(...),
    session: Session = Depends(get_db_session),
    _authorized: bool = Depends(verify_token),
):
    try:

        filename = s3_key.split("/")[-1]

        scan = Scan(
            file_name=filename,
            scan_provider=ScanProviders.CLAMAV.value,
        )
        session.add(scan)
        session.commit()

        run_in_background(launch_scan, s3_key, scan.id, aws_account, session, sns_arn)
        return {"status": "OK", "scan_id": str(scan.id)}

    except Exception as err:
        print(err)
        log.error(err)
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return {"error": f"error scanning file [{s3_key}] with clamav"}


@router.get("/{scan_id}")
def get_clamav_scan_results(
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
