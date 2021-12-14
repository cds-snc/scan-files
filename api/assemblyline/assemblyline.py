from assemblyline_client import get_client
from boto3wrapper.wrapper import get_session
from database.db import get_db_session
from database.dynamodb import log_scan_result
from datetime import datetime, timedelta
from json import dumps
from logger import log
from models.Scan import Scan, ScanProviders, ScanVerdicts
from os import environ
from storage.storage import get_file
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError


def get_assemblyline_client():
    return get_client(
        f"https://{environ.get('MLWR_HOST')}",
        timeout=60000,  # Timeout after 1 minute
        apikey=(environ.get("MLWR_USER"), environ.get("MLWR_KEY")),
    )


def add_to_scan_queue(payload):
    client = get_session().client("stepfunctions")
    response = client.list_state_machines()
    state_machine = environ.get("SCAN_QUEUE_STATEMACHINE_NAME")

    stateMachine = [
        stateMachine
        for stateMachine in response["stateMachines"]
        if stateMachine.get("name") == state_machine
    ]

    if stateMachine:
        response = client.start_execution(
            stateMachineArn=stateMachine[0]["stateMachineArn"],
            input=dumps(payload),
        )
    else:
        log.error(f"State machine: {state_machine} is not defined")
        raise ValueError(f"State machine: {state_machine} is not defined")


def launch_scan(execution_id, scan_id, file=None):
    try:
        al_client = get_assemblyline_client()
        session = next(get_db_session())
        state_machine = environ.get("SCAN_QUEUE_STATEMACHINE_NAME")

        scan = session.query(Scan).filter(Scan.id == scan_id).one_or_none()
        if file is None:
            file = get_file(scan.save_path, True)

        settings = {
            "classification": "TLP:A//REL TO CDS-SNC.CA",  # classification
            "description": "CDS file scanning api",  # file description
            "name": scan.file_name,  # file name
            "ttl": 1,
            "services": {
                "excluded": [],
                "resubmit": [],
                "runtime_excluded": [],
                "selected": [
                    "Filtering",
                    "Antivirus",
                    "Cuckoo",
                    "Static Analysis",
                    "Extraction",
                    "Networking",
                ],
            },
        }

        meta_data = {
            "git_sha": environ.get("GIT_SHA") or "latest",
            "requestor": state_machine,
            "scan_id": str(scan.id),
            "save_path": scan.save_path,
            "execution_id": execution_id,
        }

        file.seek(0)
        response = al_client.submit(
            content=file.read(),
            params=settings,
            metadata=meta_data,
        )
        log.info(response)
        scan.meta_data = response
        session.commit()

    except Exception as err:
        log.error({"error": "error sending file to assemblyline"})
        log.error(err)
        return False

    return True


def poll_for_results(scan_id):
    try:
        al_client = get_assemblyline_client()
        session = next(get_db_session())

        scan = session.query(Scan).filter(Scan.id == scan_id).one_or_none()
        if scan:
            submission_details = al_client.submission(scan.meta_data["sid"])
            log_scan_result(submission_details["metadata"]["execution_id"])
            if submission_details["state"] == "completed" and scan.completed is None:
                verdict = determine_verdict(
                    ScanProviders.ASSEMBLYLINE.value,
                    submission_details["max_score"],
                )
                scan.completed = submission_details["times"]["completed"]
                scan.file_size = submission_details["files"][0]["size"]
                scan.sha256 = submission_details["files"][0]["sha256"]
                scan.verdict = verdict
                scan.meta_data = submission_details
                session.commit()
            else:
                return False
        else:
            log.error(f"Received request for scan_id not in database: {scan_id}")
            return False

    except Exception as err:
        log.error({"error": "error sending file to assemblyline"})
        log.error(err)
        return False

    return True


def resubmit_stale_scans():
    session = next(get_db_session())
    current_time = datetime.utcnow()
    one_day_ago = current_time - timedelta(days=1)
    try:
        scans_in_progress = (
            session.query(Scan)
            .filter(
                and_(
                    Scan.verdict == None,  # noqa
                    Scan.submitted < one_day_ago,
                )
            )
            .all()
        )
        for scan in scans_in_progress:
            status_or_file = get_file(scan.save_path, True)
            if status_or_file is False:
                log.error(
                    {
                        "error": f"{scan.save_path} does not exist. No further retries will be attempted"
                    }
                )
                scan.verdict = ScanVerdicts.ERROR.value
                scan.completed = datetime.utcnow()
                session.commit()
            else:
                add_to_scan_queue({"scan_id": str(scan.id)})
        return True

    except SQLAlchemyError as err:
        log.error({"error": "error retriving in-progress scans > 1 day"})
        log.error(err)
    except Exception as err:
        log.error({"error": "error sending file to assemblyline"})
        log.error(err)

    return False


def determine_verdict(provider, value):
    if provider is None or value is None:
        log.error(
            f"Provider({provider}) and Value({value}) are required to calculate scan verdicts"
        )
        return ScanVerdicts.ERROR.value

    if provider == ScanProviders.ASSEMBLYLINE.value:
        if not isinstance(value, int):
            return ScanVerdicts.ERROR.value
        if (
            value == -1000 or 0 <= value <= 299
        ):  # Ignore informational ratings and merge with clean
            return ScanVerdicts.CLEAN.value
        elif 300 <= value <= 999:
            return ScanVerdicts.SUSPICIOUS.value
        elif value >= 1000:
            return ScanVerdicts.MALICIOUS.value
        else:
            return ScanVerdicts.UNKNOWN.value
    else:
        log.error("Unsupported provider: ", provider)
        return ScanVerdicts.ERROR.value
