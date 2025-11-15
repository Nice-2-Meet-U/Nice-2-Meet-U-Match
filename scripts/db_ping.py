# routes/debug.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from frameworks.db.session import get_db

router = APIRouter()

@router.get("/db-ping")
def db_ping(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"ok": True}