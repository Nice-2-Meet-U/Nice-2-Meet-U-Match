# resources/matches.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from frameworks.db.session import get_db
from services.match_service import create_match, get_match, list_matches, patch_match
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
    matches = list_matches(
        db,
        pool_id=pool_id,
        user_id=user_id,
        status_filter=status_filter.value if status_filter else None,
    )
    return matches


@router.patch("/{match_id}", response_model=MatchGet)
def patch_match_endpoint(
    match_id: UUID, payload: MatchPatch, db: Session = Depends(get_db)
):
    try:
        match = patch_match(
            db,
            match_id=match_id,
            pool_id=payload.pool_id,
            user1_id=payload.user1_id,
            user2_id=payload.user2_id,
            status=payload.status.value if payload.status else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return match


@router.get("/db-ping")
def db_ping(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"ok": True}