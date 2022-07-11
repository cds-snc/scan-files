import logging
import re
from uuid import uuid4
from pythonjsonlogger import jsonlogger

CUSTOM_FORMAT = "[%(request_id)s][%(asctime)s %(filename)s %(funcName)s %(levelname)1.1s %(module)s:%(lineno)d] %(message)s %(name)s %(pathname)s %(process)s %(processName)s %(threadName)s"


class CustomLogger:
    def __init__(self, logger_name, scanning_request_id):
        self.scanning_request_id = scanning_request_id
        self.old_factory = logging.getLogRecordFactory()
        self.log = self.get_named_instance(logger_name, scanning_request_id)

    def record_factory(self, *args, **kwargs):
        record = self.old_factory(*args, **kwargs)
        record.request_id = self.scanning_request_id
        return record

    def get_named_instance(self, name, scanning_request_id):
        if not scanning_request_id or not re.match(r"^[\w-]+$", scanning_request_id):
            self.scanning_request_id = "scan-request-{}".format(uuid4())

        logging.setLogRecordFactory(self.record_factory)
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = jsonlogger.JsonFormatter(CUSTOM_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def get_scanning_request_id(self):
        return self.scanning_request_id


log = logging.getLogger("scan-files")
log.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
log.addHandler(logHandler)
