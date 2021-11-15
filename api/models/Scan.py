import datetime
import uuid

from enum import IntEnum
from models import Base
from sqlalchemy import DateTime, Column, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql.sqltypes import Numeric


class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String, nullable=False)
    file_size = Column(Numeric, nullable=False)
    save_path = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    scan_provider = Column(String, nullable=False)
    submitter = Column(String, nullable=False)

    verdict = Column(String, nullable=True)
    quarantine_path = Column(String, nullable=True)
    meta_data = Column(JSONB, nullable=True)

    submitted = Column(
        DateTime,
        index=False,
        unique=False,
        nullable=False,
        default=datetime.datetime.utcnow,
    )
    completed = Column(
        DateTime,
        index=False,
        unique=False,
        nullable=True,
    )
