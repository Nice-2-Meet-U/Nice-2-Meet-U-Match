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
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from models.decisions import DecisionPost, DecisionGet
from services.user_match_service import submit_decision, list_decisions


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

# ------
@router.post("/decisions", response_model=DecisionGet, status_code=status.HTTP_201_CREATED)
def create_decision_endpoint(payload: DecisionPost, db: Session = Depends(get_db)):
    try:
        # submit_decision updates DB and returns the updated Match, we don't need
        # the return value here because the endpoint returns the decision row.
        submit_decision(
            db,
            match_id=payload.match_id,
            user_id=payload.user_id,
            decision=payload.decision,  # Already DecisionValue enum
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Return this user's current decision row as confirmation
    # Use Session.get instead of Query.get (deprecated)
    d = db.get(models.MatchDecision, (str(payload.match_id), str(payload.user_id)))
    if not d:
        # This should not happen; defensive
        raise HTTPException(status_code=500, detail="Decision not recorded")
    return d


@router.get("/decisions", response_model=list[DecisionGet])
def list_decisions_endpoint(
    match_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """List decisions with optional filters by match_id or user_id."""
    decisions = list_decisions(db, match_id=match_id, user_id=user_id)
    return decisions
