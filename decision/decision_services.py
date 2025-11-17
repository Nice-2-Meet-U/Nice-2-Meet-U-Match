"""Decision service layer - business logic for decision operations."""
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text
from frameworks.db import models
from decision.decision_exceptions import (
    MatchNotFoundError,
    UnauthorizedDecisionError,
)


def submit_decision(
    db: Session,
    *,
    match_id: UUID,
    user_id: UUID,
    decision: models.DecisionValue,
):
    """Upsert a decision and atomically recompute match status."""
    match = db.get(models.Match, str(match_id))
    if not match:
        raise MatchNotFoundError(match_id)
    if str(user_id) not in (match.user1_id, match.user2_id):
        raise UnauthorizedDecisionError(user_id, match_id)

    upsert_sql = text(
        """
        INSERT INTO match_decisions (match_id, user_id, decision, decided_at)
        VALUES (:mid, :uid, :decision, NOW())
        ON DUPLICATE KEY UPDATE
            decision = VALUES(decision),
            decided_at = NOW()
        """
    )
    db.execute(
        upsert_sql, {"mid": str(match_id), "uid": str(user_id), "decision": decision.value}
    )
    
    status_sql = text(
        """
        UPDATE matches m
        SET status = CASE
            WHEN EXISTS (
                SELECT 1 FROM match_decisions md
                WHERE md.match_id = m.id AND md.decision = 'reject'
            ) THEN 'rejected'
            WHEN (
                SELECT COUNT(*) FROM match_decisions md
                WHERE md.match_id = m.id AND md.decision = 'accept'
            ) = 2 THEN 'accepted'
            ELSE 'waiting'
        END,
        updated_at = NOW()
        WHERE m.id = :mid
        """
    )
    db.execute(status_sql, {"mid": str(match_id)})
    db.commit()

def list_decisions(
    db: Session,
    *,
    match_id: UUID | None = None,
    user_id: UUID | None = None,
):
    """List decisions with optional filters."""
    q = db.query(models.MatchDecision)
    if match_id:
        q = q.filter(models.MatchDecision.match_id == str(match_id))
    if user_id:
        q = q.filter(models.MatchDecision.user_id == str(user_id))
    return q.order_by(models.MatchDecision.decided_at.desc()).all()
