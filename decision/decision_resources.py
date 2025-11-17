"""Decision API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from frameworks.db.session import get_db
from frameworks.hateoas import build_links
from decision.decision_services import submit_decision, list_decisions
from decision.decision_schemas import DecisionPost, DecisionGet
from decision.decision_exceptions import (
    MatchNotFoundError,
    UnauthorizedDecisionError,
)
from frameworks.db import models

router = APIRouter()


@router.post("/", response_model=DecisionGet, status_code=status.HTTP_201_CREATED)
def submit_decision_endpoint(payload: DecisionPost, db: Session = Depends(get_db)):
    """Submit a decision for a match."""
    try:
        submit_decision(
            db,
            match_id=payload.match_id,
            user_id=payload.user_id,
            decision=payload.decision,
        )
    except MatchNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    except UnauthorizedDecisionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not authorized")

    decision = db.get(models.MatchDecision, (str(payload.match_id), str(payload.user_id)))
    if not decision:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Decision not recorded")
    decision.links = {"match": build_links("match", payload.match_id)["self"]}
    return decision


@router.get("/", response_model=list[DecisionGet])
def list_decisions_endpoint(
    match_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """List decisions with optional filters."""
    decisions = list_decisions(db, match_id=match_id, user_id=user_id)
    for decision in decisions:
        decision.links = {"match": build_links("match", UUID(decision.match_id))["self"]}
    return decisions
