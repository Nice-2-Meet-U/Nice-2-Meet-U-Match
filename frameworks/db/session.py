# framework/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# --- Declarative base for models ---
Base = declarative_base()

# --- Database connection ---
# Use Cloud SQL Python Connector if DATABASE_URL not set
from google.cloud.sql.connector import Connector, IPTypes

instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
db_user = os.environ.get("DB_USER", "root")
db_name = os.environ.get("DB_NAME", "matches")
db_pass = os.environ.get("DB_PASS", "")

if not instance_connection_name:
    raise ValueError(
        "Either DATABASE_URL or INSTANCE_CONNECTION_NAME must be set"
    )

ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC
connector = Connector(ip_type=ip_type, refresh_strategy="LAZY")

def getconn():
    # Use password-based authentication
    return connector.connect(
        instance_connection_name,
        "pymysql",
        user=db_user,
        password=db_pass,
        db=db_name,
    )

engine = create_engine(
    f"mysql+pymysql:///{db_name}",
    creator=getconn,
    echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    future=True,
)


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


# --- FastAPI dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
