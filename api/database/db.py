import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if os.environ.get("CI"):
    connection_string = os.environ.get("SQLALCHEMY_DATABASE_TEST_URI")
else:
    connection_string = os.environ.get("SQLALCHEMY_DATABASE_URI")
# Timeout is set to 10 seconds
db_engine = create_engine(
    connection_string,
    connect_args={"connect_timeout": 10},
    pool_size=1,
    pool_pre_ping=True,  # Check that a connection is still active before attempting to use
    pool_recycle=1500,  # Prune connections older than 25 minutes (RDS Proxy has a timeout of 30 minutes)
    pool_use_lifo=True,  # Re-use last connection used (allows server-side timeouts to remove unused connections)
)
db_session = sessionmaker(bind=db_engine)


def get_db_session():
    session = db_session()
    try:
        yield session
    finally:
        session.close()


def get_db_version(session):

    query = "SELECT version_num FROM alembic_version"
    full_name = session.execute(query).fetchone()[0]
    return full_name
