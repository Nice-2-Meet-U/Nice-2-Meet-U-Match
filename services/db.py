import os

from google.cloud.sql.connector import Connector, IPTypes
import pymysql

import sqlalchemy
from models.db import Base


# Global engine instance
_engine: sqlalchemy.engine.base.Engine = None


def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of MySQL.

    Uses the Cloud SQL Python Connector package.
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    # Note: Saving credentials in environment variables is convenient, but not
    # secure - consider a more secure solution such as
    # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
    # keep secrets safe.

    instance_connection_name = os.environ[
        "INSTANCE_CONNECTION_NAME"
    ]  # e.g. 'project:region:instance'
    db_user = os.environ["DB_USER"]  # e.g. 'my-db-user'
    db_pass = os.environ["DB_PASS"]  # e.g. 'my-db-password'
    db_name = os.environ["DB_NAME"]  # e.g. 'my-database'

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    # initialize Cloud SQL Python Connector object
    connector = Connector(ip_type=ip_type, refresh_strategy="LAZY")

    def getconn() -> pymysql.connections.Connection:
        conn: pymysql.connections.Connection = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )
        return conn

    _engine = sqlalchemy.create_engine(
        "mysql+pymysql:///matches",  # Database name is 'matches'
        creator=getconn,
        echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
    )
    return _engine


def initialize_schema() -> None:
    """
    Create all tables in the database based on the SQLAlchemy models.
    This should be called once at application startup.
    """
    engine = connect_with_connector()
    Base.metadata.create_all(engine)
