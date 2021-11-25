from assemblyline_client import get_client
from boto3wrapper.wrapper import get_session
from database.db import get_db_session
from database.dynamodb import log_scan_result
from json import dumps
from logger import log
from models.Scan import Scan, ScanProviders, ScanVerdicts
from os import environ
from storage.storage import get_file


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
        }

        meta_data = {
            "git_sha": environ.get("GIT_SHA", "latest"),
            "requestor": state_machine,
            "scan_id": str(scan.id),
            "save_path": scan.save_path,
            "execution_id": execution_id,
        }

        file.seek(0)
        al_client.ingest(
            content=file.read(),
            nq="cds_snc_queue",
            params=settings,
            metadata=meta_data,
        )

    except Exception as err:
        log.error({"error": "error sending file to assemblyline"})
        log.error(err)
        return False

    return True


def poll_for_results():

    try:
        al_client = get_assemblyline_client()
        session = next(get_db_session())
        message = None
        while True:
            message = al_client.ingest.get_message("cds_snc_queue")
            # Results of completed scans are retrieved one at a time until "None" is returned
            # indicating no additional results are available
            if message is None:
                break

            submission_details = al_client.submission(message["submission"]["sid"])
            log_scan_result(message["submission"]["metadata"]["execution_id"])
            scan = (
                session.query(Scan)
                .filter(Scan.id == message["submission"]["metadata"]["scan_id"])
                .one_or_none()
            )

            if scan and scan.completed is None:
                if "max_score" in submission_details:
                    verdict = determine_verdict(
                        ScanProviders.ASSEMBLYLINE.value,
                        submission_details["max_score"],
                    )
                    scan.completed = submission_details["times"]["completed"]
                    scan.file_size = submission_details["files"][0]["size"]
                    scan.sha256 = submission_details["files"][0]["sha256"]
                else:
                    verdict = ScanVerdicts.ERROR.value

                scan.verdict = verdict
                scan.meta_data = submission_details
                session.commit()
            else:
                log.error(
                    f"Received results for scan_id not in database: {message['submission']['metadata']['scan_id']}"
                )
                return False

            if environ.get("CI"):
                break
    except Exception as err:
        log.error({"error": "error sending file to assemblyline"})
        log.error(err)
        return False

    return True


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
