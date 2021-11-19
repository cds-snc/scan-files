from assemblyline_client import get_client
from api_gateway.custom_middleware import verify_token
from database.db import get_session
from fastapi import APIRouter, Depends, File, Response, status, UploadFile
from logger import log
from models.Scan import Scan, ScanProviders, ScanVerdicts
from os import environ
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from uuid import UUID


router = APIRouter()


def get_assemblyline_client():
    return get_client(
        f"https://{environ.get('MLWR_HOST')}",
        timeout=60000,  # Timeout after 1 minute
        apikey=(environ.get("MLWR_USER"), environ.get("MLWR_KEY")),
    )


@router.post("/assemblyline")
def start_assemblyline_scan(
    response: Response,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _authorized: bool = Depends(verify_token),
):
    try:
        al_client = get_assemblyline_client()
        settings = {
            "classification": "TLP:A//REL TO CDS-SNC.CA",  # classification
            "description": "CDS file scanning api",  # file description
            "name": file.filename,  # file name
            "ttl": 1,
        }

        file.file.seek(0)

        scan = Scan(
            file_name=file.filename, scan_provider=ScanProviders.ASSEMBLYLINE.value
        )
        session.add(scan)

        meta_data = {
            "git_sha": environ.get("GIT_SHA", "latest"),
            "requestor": "scan-files-api",
            "scan_id": str(scan.id),
        }
        response = al_client.ingest(
            content=file.file.read(),
            nq="cds_snc_queue",
            params=settings,
            metadata=meta_data,
        )
        session.commit()
    except Exception as err:
        log.error(err)
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return {"error": "error sending file to assemblyline"}

    return {"status": "OK", "scan_id": str(scan.id)}


@router.get("/assemblyline/{scan_id}")
def get_assemblyline_scan_results(
    response: Response,
    scan_id: UUID,
    session: Session = Depends(get_session),
    _authorized: bool = Depends(verify_token),
):
    try:
        updated_scans = retrieve_assemblyline_messages(session)
        if scan_id in updated_scans:
            scan = updated_scans[scan_id]
            return {"status": "completed", "verdict": scan.verdict}
        else:
            scan = session.query(Scan).filter(Scan.id == scan_id).one_or_none()
            if scan and scan.completed:
                return {"status": "completed", "verdict": scan.verdict}
            else:
                return {"status": ScanVerdicts.IN_PROGRESS.value}

    except SQLAlchemyError as err:
        log.error(err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "error updating scan details"}
    except Exception as err:
        log.error(err)
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return {"error": "error retrieving scan results from assemblyline"}


def retrieve_assemblyline_messages(session):
    scan_results = {}
    al_client = get_assemblyline_client()
    message = None
    while True:
        message = al_client.ingest.get_message("cds_snc_queue")
        if message is None:
            break
        else:
            submission_details = al_client.submission(message["submission"]["sid"])
            scan = (
                session.query(Scan)
                .filter(Scan.id == message["submission"]["metadata"]["scan_id"])
                .one_or_none()
            )

            if scan and scan.completed is None:
                if submission_details["error_count"] > 0:
                    verdict = ScanVerdicts.ERROR.value
                elif submission_details["verdict"]["malicious"] == []:
                    verdict = ScanVerdicts.CLEAN.value
                else:
                    verdict = ScanVerdicts.MALICIOUS.value

                scan.verdict = verdict
                scan.completed = submission_details["times"]["completed"]
                scan.file_size = submission_details["files"][0]["size"]
                scan.sha256 = submission_details["files"][0]["sha256"]
                scan.meta_data = submission_details
                scan_results[scan.id] = scan
                session.commit()
            else:
                log.error(
                    f"Received results for scan_id not in database: {message['submission']['metadata']['scan_id']}"
                )

        if environ.get("CI"):
            break

    return scan_results
