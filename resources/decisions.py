# resources/decisions.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from frameworks.db.session import get_db
from services.decision_service import submit_decision
from models.decisions import DecisionPost, DecisionGet
from frameworks.db import models

router = APIRouter()


@router.post("/", response_model=DecisionGet, status_code=status.HTTP_201_CREATED)
def submit_decision_endpoint(payload: DecisionPost, db: Session = Depends(get_db)):
    try:
        # submit_decision updates DB and returns the updated Match, we don't need
        # the return value here because the endpoint returns the decision row.
        submit_decision(
            db,
            match_id=payload.match_id,
            user_id=payload.user_id,
            decision=models.DecisionValue(payload.decision.value),
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


@router.get("/", response_model=list[DecisionGet])
def list_decisions_endpoint(
    match_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.MatchDecision)
    if match_id:
        q = q.filter(models.MatchDecision.match_id == str(match_id))
    if user_id:
        q = q.filter(models.MatchDecision.user_id == str(user_id))
    return q.order_by(models.MatchDecision.decided_at.desc()).all()
