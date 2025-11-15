# resources/matches.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from frameworks.db.session import get_db
from services.match_service import create_match, get_match
from models.match import MatchPost, MatchGet, MatchPatch, MatchStatus
from frameworks.db import models
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

router = APIRouter()


@router.post("/", response_model=MatchGet, status_code=status.HTTP_201_CREATED)
def create_match_endpoint(payload: MatchPost, db: Session = Depends(get_db)):
    try:
        # create_match will handle uniqueness and commit; return the row it provides
        match = create_match(
            db,
            pool_id=payload.pool_id,
            user1_id=payload.user1_id,
            user2_id=payload.user2_id,
        )
        return match

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate or invalid match.")

    except OperationalError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Database unavailable (check Cloud SQL credentials/network).",
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error.")


@router.get("/{match_id}", response_model=MatchGet)
def get_match_endpoint(match_id: UUID, db: Session = Depends(get_db)):
    m = get_match(db, match_id)
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    return m


@router.get("/", response_model=list[MatchGet])
def list_matches_endpoint(
    pool_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(
        None, description="Filter matches where this user is a participant"
    ),
    status_filter: Optional[MatchStatus] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.Match)
    if pool_id:
        q = q.filter(models.Match.pool_id == str(pool_id))
    if user_id:
        q = q.filter(
            (models.Match.user1_id == str(user_id)) | (models.Match.user2_id == str(user_id))
        )
    if status_filter:
        q = q.filter(models.Match.status == status_filter)
    return q.order_by(models.Match.created_at.desc()).all()


@router.patch("/{match_id}", response_model=MatchGet)
def patch_match_endpoint(
    match_id: UUID, payload: MatchPatch, db: Session = Depends(get_db)
):
    m = db.get(models.Match, str(match_id))
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")

    # Admin-style patch (only fields provided)
    changed = False
    if payload.pool_id is not None:
        m.pool_id = str(payload.pool_id)
        changed = True
    if payload.user1_id is not None:
        m.user1_id = str(payload.user1_id)
        changed = True
    if payload.user2_id is not None:
        m.user2_id = str(payload.user2_id)
        changed = True
    if payload.status is not None:
        # careful: this overrides computed status
        m.status = models.MatchStatus(payload.status.value)
        changed = True

    if not changed:
        return m

    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/db-ping")
def db_ping(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"ok": True}