# services/decision_service.py
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text
from frameworks.db import models


def submit_decision(
    db: Session,
    *,
    match_id: UUID,
    user_id: UUID,
    decision: models.DecisionValue,  # Enum on your ORM
):
    """
    Upsert a decision (match_id, user_id) and atomically recompute match.status.
    Returns the updated Match row.
    """
    # Ensure the decider is a participant (cheap guard; DB trigger would be stronger)
    match = db.get(models.Match, str(match_id))
    if not match:
        raise ValueError("Match not found")
    if str(user_id) not in (match.user1_id, match.user2_id):
        raise PermissionError("User is not a participant in this match")

    # MySQL-compatible upsert and status update
    # First, upsert the decision
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
    
    # Then, compute and update match status
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

    # Return updated state
    db.refresh(match)
    return match
