import datetime
import hashlib
import os
import pwd
import re
import subprocess
import socket
import errno

import botocore
from pytz import utc

from .common import AWS_ENDPOINT_URL
from .common import CLAMD_PATH
from .common import AV_DEFINITION_S3_BUCKET
from .common import AV_DEFINITION_S3_PREFIX
from .common import AV_DEFINITION_PATH
from .common import AV_DEFINITION_FILE_PREFIXES
from .common import AV_DEFINITION_FILE_SUFFIXES
from .common import AV_SCAN_USE_CACHE
from .common import AV_SIGNATURE_UNKNOWN
from .common import AV_SIGNATURE_METADATA
from .common import CLAMD_STARTUP_LOCK
from .common import CLAMD_SOCKET
from .common import CLAMAVLIB_PATH
from .common import CLAMDSCAN_PATH
from .common import FRESHCLAM_PATH
from .common import create_dir, kill_process_by_pid

from boto3wrapper.wrapper import get_session
from filelock import FileLock
from logger import log
from models.Scan import Scan, ScanProviders, ScanVerdicts
from storage.storage import get_file
from uuid import uuid4


rd_ld = re.compile(r"SEARCH_DIR\(\"=([A-z0-9\/\-_]*)\"\)")


def current_library_search_path():
    ld_verbose = subprocess.check_output(["ld", "--verbose"]).decode("utf-8")
    return rd_ld.findall(ld_verbose)


def update_defs_from_s3(s3_client, bucket, prefix):
    create_dir(AV_DEFINITION_PATH)
    to_download = {}
    for file_prefix in AV_DEFINITION_FILE_PREFIXES:
        s3_best_time = None
        for file_suffix in AV_DEFINITION_FILE_SUFFIXES:
            filename = file_prefix + "." + file_suffix
            s3_path = os.path.join(AV_DEFINITION_S3_PREFIX, filename)
            local_path = os.path.join(AV_DEFINITION_PATH, filename)
            s3_md5 = md5_from_s3_tags(s3_client, bucket, s3_path)
            s3_time = time_from_s3(s3_client, bucket, s3_path)

            if s3_best_time is not None and s3_time < s3_best_time:
                log.info("Not downloading older file in series: %s" % filename)
                continue
            else:
                s3_best_time = s3_time

            if os.path.exists(local_path) and md5_from_file(local_path) == s3_md5:
                log.info("Not downloading %s because local md5 matches s3." % filename)
                continue
            if s3_md5:
                to_download[file_prefix] = {
                    "s3_path": s3_path,
                    "local_path": local_path,
                }
    return to_download


def upload_defs_to_s3(s3_client, bucket, prefix, local_path):
    for file_prefix in AV_DEFINITION_FILE_PREFIXES:
        for file_suffix in AV_DEFINITION_FILE_SUFFIXES:
            filename = file_prefix + "." + file_suffix
            local_file_path = os.path.join(local_path, filename)
            log.info("search for file %s" % local_file_path)
            if os.path.exists(local_file_path):
                local_file_md5 = md5_from_file(local_file_path)
                if local_file_md5 != md5_from_s3_tags(
                    s3_client, bucket, os.path.join(prefix, filename)
                ):
                    log.info(
                        "Uploading %s to s3://%s"
                        % (local_file_path, os.path.join(bucket, prefix, filename))
                    )
                    s3 = get_session().resource("s3", endpoint_url=AWS_ENDPOINT_URL)

                    s3_object = s3.Object(bucket, os.path.join(prefix, filename))
                    s3_object.upload_file(os.path.join(local_path, filename))
                    s3_client.put_object_tagging(
                        Bucket=s3_object.bucket_name,
                        Key=s3_object.key,
                        Tagging={"TagSet": [{"Key": "md5", "Value": local_file_md5}]},
                    )
                else:
                    log.info(
                        "Not uploading %s because md5 on remote matches local."
                        % filename
                    )
            else:
                log.info("File does not exist: %s" % filename)


def update_defs_from_freshclam(path, library_path=""):
    create_dir(path)
    fc_env = os.environ.copy()
    if library_path:
        fc_env["LD_LIBRARY_PATH"] = "%s:%s" % (
            ":".join(current_library_search_path()),
            CLAMAVLIB_PATH,
        )
    log.info("Starting freshclam with defs in %s." % path)

    fc_proc = subprocess.run(
        [
            FRESHCLAM_PATH,
            "--config-file=%s/freshclam.conf" % CLAMAVLIB_PATH,
            "-u %s" % pwd.getpwuid(os.getuid())[0],
            "--datadir=%s" % path,
        ],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        env=fc_env,
    )

    if fc_proc.returncode != 0:
        log.error("Unexpected exit code from freshclam: %s." % fc_proc.returncode)
    log.info("freshclam output:: %s" % fc_proc.stdout.decode("utf-8"))

    return fc_proc.returncode


def md5_from_file(filename):
    hash_md5 = hashlib.md5()  # nosec - [B303:blacklist] MD5 being used for file hashing
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def md5_from_s3_tags(s3_client, bucket, key):
    try:
        tags = s3_client.get_object_tagging(Bucket=bucket, Key=key)["TagSet"]
    except botocore.exceptions.ClientError as e:
        expected_errors = {
            "404",  # Object does not exist
            "AccessDenied",  # Object cannot be accessed
            "NoSuchKey",  # Object does not exist
            "MethodNotAllowed",  # Object deleted in bucket with versioning
        }
        if e.response["Error"]["Code"] in expected_errors:
            return ""
        else:
            raise
    for tag in tags:
        if tag["Key"] == "md5":
            return tag["Value"]
    return ""


def time_from_s3(s3_client, bucket, key):
    try:
        time = s3_client.head_object(Bucket=bucket, Key=key)["LastModified"]
    except botocore.exceptions.ClientError as e:
        expected_errors = {"404", "AccessDenied", "NoSuchKey"}
        if e.response["Error"]["Code"] in expected_errors:
            return datetime.datetime.fromtimestamp(0, utc)
        else:
            raise
    return time


# Turn ClamAV Scan output into a JSON formatted data object
def scan_output_to_json(output):
    summary = {}
    for line in output.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            summary[key] = value.strip()
    return summary


def scan_file(log, session, path, ignore_cache=False, aws_account=None):
    av_env = os.environ.copy()
    av_env["LD_LIBRARY_PATH"] = CLAMAVLIB_PATH
    log.info("Starting clamscan of %s." % path)

    if path.startswith("s3://"):
        try:
            save_path = f"{AV_DEFINITION_PATH}/quarantine/{str(uuid4())}"
            create_dir(f"{AV_DEFINITION_PATH}/quarantine")
            file = get_file(path, aws_account=aws_account, ref_only=True)
            with open(save_path, "wb") as file_on_disk:
                file.seek(0)
                file_on_disk.write(file.read())
            path = save_path
        except Exception as err:
            msg = "Error retrieving file: [%s] from s3. Reason: %s.\n" % (
                path,
                str(err),
            )
            log.error(msg)
            raise Exception(msg)

    checksum = md5_from_file(path)

    # Check for previously cached scan results
    previous_scan = None
    if AV_SCAN_USE_CACHE and not ignore_cache:
        current_time = datetime.datetime.utcnow()
        one_day_ago = current_time - datetime.timedelta(days=1)

        previous_scan = (
            session.query(Scan)
            .filter(
                Scan.checksum == checksum,
                Scan.scan_provider == ScanProviders.CLAMAV.value,
                Scan.submitted >= one_day_ago,
            )
            .first()
        )

    if previous_scan:
        return (
            checksum,
            previous_scan.verdict,
            previous_scan.meta_data[AV_SIGNATURE_METADATA],
            path,
        )
    else:
        av_proc = subprocess.run(
            [
                CLAMDSCAN_PATH,
                "-v",
                "--stdout",
                "--config-file",
                "%s/clamd.conf" % CLAMAVLIB_PATH,
                path,
            ],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            env=av_env,
        )
        output = av_proc.stdout.decode("utf-8")
        log.info("clamscan output:\n%s" % output)

    # Turn the output into a data source we can read
    summary = scan_output_to_json(output)
    verdict, signature = determine_verdict(
        log, ScanProviders.CLAMAV.value, path, summary, av_proc
    )
    return checksum, verdict, signature, path


def determine_verdict(log, provider, path, summary, av_proc):
    if None in (provider, path, summary, av_proc):
        log.error(
            f"determine_verdict called with missing arguments: {provider}, {path}, {summary}, {av_proc}"
        )
        return ScanVerdicts.ERROR.value, AV_SIGNATURE_UNKNOWN

    signature = summary.get(path, AV_SIGNATURE_UNKNOWN)
    if provider == ScanProviders.CLAMAV.value:
        # ClamAV will return a OK verdict even if it did not scan the file due to file limits
        # We need to check the scan time to determine if the file was scanned
        if "0.000" in summary.get("Time", "").strip():
            log.error("Unable to scan file: %s" % path)
            return ScanVerdicts.UNABLE_TO_SCAN.value, AV_SIGNATURE_UNKNOWN

        if av_proc.returncode == 0:
            return ScanVerdicts.CLEAN.value, signature
        elif av_proc.returncode == 1:
            return ScanVerdicts.MALICIOUS.value, signature
        else:
            log.error("Unexpected exit code from clamscan: %s.\n" % av_proc.returncode)
            return ScanVerdicts.ERROR.value, AV_SIGNATURE_UNKNOWN
    else:
        log.error("Unsupported provider or wrong type: ", provider)
        return ScanVerdicts.ERROR.value, AV_SIGNATURE_UNKNOWN


def get_clamd_pid():
    try:
        clamd_pid = subprocess.check_output(["pidof", "clamd"]).decode("utf-8").strip()
        return int(clamd_pid)
    except ValueError:
        log.error("Failed to convert PID: %s into an integer" % clamd_pid)
        pass
    except Exception:
        log.error("Failed to get PID of clamd")
        pass

    return None


def is_clamd_running():
    log.info("Checking if clamd is running on %s" % CLAMD_SOCKET)

    if os.path.exists(CLAMD_SOCKET):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(10)
                s.connect(CLAMD_SOCKET)
                s.send(b"PING")
                data = s.recv(32)
            except (socket.timeout, socket.error) as e:
                log.error("Failed to read from socket: %s\n" % e)
                return False

        log.info("Received %s in response to PING" % repr(data))
        return data == b"PONG\n"

    log.error("Clamd is not running on %s" % CLAMD_SOCKET)
    return False


def setup_clamd_daemon():
    clamd_pid = get_clamd_pid()
    lock = FileLock(CLAMD_STARTUP_LOCK, timeout=120)
    lock.acquire(poll_interval=5)
    try:
        if not is_clamd_running():
            if clamd_pid is not None:
                kill_process_by_pid(clamd_pid)

            clamd_pid = start_clamd_daemon()
            log.info("Clamd PID: %s" % clamd_pid)
        else:
            clamd_pid = get_clamd_pid()
    except Exception as e:
        log.error("Failed to start clamd daemon: %s" % e)
        raise e
    finally:
        lock.release()

    return clamd_pid


def start_clamd_daemon():
    s3 = get_session().resource("s3", endpoint_url=AWS_ENDPOINT_URL)
    s3_client = get_session().client("s3", endpoint_url=AWS_ENDPOINT_URL)

    to_download = update_defs_from_s3(
        s3_client, AV_DEFINITION_S3_BUCKET, AV_DEFINITION_S3_PREFIX
    )

    for download in to_download.values():
        s3_path = download["s3_path"]
        local_path = download["local_path"]
        print("Downloading definition file %s from s3://%s" % (local_path, s3_path))
        s3.Bucket(AV_DEFINITION_S3_BUCKET).download_file(s3_path, local_path)
        print("Downloading definition file %s complete!" % (local_path))

    av_env = os.environ.copy()
    av_env["LD_LIBRARY_PATH"] = CLAMAVLIB_PATH

    log.info("Starting clamd")

    if os.path.exists(CLAMD_SOCKET):
        try:
            os.unlink(CLAMD_SOCKET)
        except OSError as e:
            if e.errno != errno.ENOENT:
                print("Could not unlink clamd socket %s" % CLAMD_SOCKET)
                raise

    clamd_proc = subprocess.Popen(
        ["%s" % CLAMD_PATH, "-c", "%s/clamd.conf" % CLAMAVLIB_PATH],
        env=av_env,
    )

    clamd_proc.wait()

    clamd_log_file = open(
        "/tmp/clamav.log"  # nosec - [B108:hardcoded_tmp_directory] Lambda only allows write to /tmp
    )
    log.info(clamd_log_file.read())
    return clamd_proc.pid
