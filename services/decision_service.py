# services/decision_service.py
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from frameworks.db import models
import logging

logger = logging.getLogger(__name__)


def submit_decision(
    db: Session,
    *,
    match_id: UUID,
    user_id: UUID,
    decision: models.DecisionValue,
) -> models.Match:
    """
    Upsert a decision (match_id, user_id) and atomically recompute match.status.
    Returns the updated Match row.
    
    Args:
        db: Database session
        match_id: UUID of the match
        user_id: UUID of the user making the decision
        decision: Accept or reject decision
        
    Returns:
        Updated Match object
        
    Raises:
        ValueError: If match not found
        PermissionError: If user is not a participant in the match
        SQLAlchemyError: For database operation failures
    """
    try:
        # Ensure the decider is a participant (cheap guard; DB trigger would be stronger)
        match = db.get(models.Match, str(match_id))
        if not match:
            raise ValueError(f"Match {match_id} not found")
        
        if str(user_id) not in (match.user1_id, match.user2_id):
            raise PermissionError(f"User {user_id} is not a participant in match {match_id}")

        # MySQL-compatible upsert and status update in a single transaction
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
            upsert_sql, 
            {
                "mid": str(match_id), 
                "uid": str(user_id), 
                "decision": decision.value
            }
        )
        
        # Then, compute and update match status atomically
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
        
        result = db.execute(status_sql, {"mid": str(match_id)})
        
        # Check if the update actually affected any rows
        if result.rowcount == 0:
            logger.warning(f"Match status update affected 0 rows for match_id: {match_id}")
        
        # Commit the transaction
        db.commit()
        
        # Refresh and return the updated match
        db.refresh(match)
        
        logger.info(
            f"Decision submitted: user_id={user_id}, match_id={match_id}, "
            f"decision={decision.value}, new_status={match.status}"
        )
        
        return match
        
    except (ValueError, PermissionError):
        # Re-raise business logic errors as-is
        db.rollback()
        raise
    except SQLAlchemyError as e:
        # Handle database errors
        db.rollback()
        logger.error(f"Database error in submit_decision: {e}")
        raise SQLAlchemyError(f"Failed to submit decision: {str(e)}") from e
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        logger.error(f"Unexpected error in submit_decision: {e}")
        raise RuntimeError(f"Unexpected error submitting decision: {str(e)}") from e


def list_decisions(
    db: Session,
    *,
    match_id: UUID | None = None,
    user_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[models.MatchDecision]:
    """
    List decisions with optional filters and pagination.
    
    Args:
        db: Database session
        match_id: Optional filter by match ID
        user_id: Optional filter by user ID
        limit: Maximum number of results (default: 100, max: 1000)
        offset: Number of results to skip (default: 0)
        
    Returns:
        List of MatchDecision objects
    """
    try:
        # Validate pagination parameters
        limit = min(max(1, limit), 1000)  # Ensure between 1 and 1000
        offset = max(0, offset)  # Ensure non-negative
        
        q = db.query(models.MatchDecision)
        
        if match_id:
            q = q.filter(models.MatchDecision.match_id == str(match_id))
        if user_id:
            q = q.filter(models.MatchDecision.user_id == str(user_id))
            
        decisions = (
            q.order_by(models.MatchDecision.decided_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        logger.debug(
            f"Listed {len(decisions)} decisions with filters: "
            f"match_id={match_id}, user_id={user_id}, limit={limit}, offset={offset}"
        )
        
        return decisions
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in list_decisions: {e}")
        raise SQLAlchemyError(f"Failed to list decisions: {str(e)}") from e


def get_match_decisions_summary(
    db: Session,
    match_id: UUID,
) -> dict[str, int]:
    """
    Get a summary of decisions for a specific match.
    
    Args:
        db: Database session
        match_id: UUID of the match
        
    Returns:
        Dictionary with decision counts: {'accept': int, 'reject': int, 'pending': int}
    """
    try:
        # Raw SQL for efficient aggregation
        summary_sql = text(
            """
            SELECT 
                COALESCE(SUM(CASE WHEN md.decision = 'accept' THEN 1 ELSE 0 END), 0) as accept_count,
                COALESCE(SUM(CASE WHEN md.decision = 'reject' THEN 1 ELSE 0 END), 0) as reject_count,
                (2 - COALESCE(COUNT(md.decision), 0)) as pending_count
            FROM matches m
            LEFT JOIN match_decisions md ON m.id = md.match_id
            WHERE m.id = :mid
            GROUP BY m.id
            """
        )
        
        result = db.execute(summary_sql, {"mid": str(match_id)}).fetchone()
        
        if not result:
            raise ValueError(f"Match {match_id} not found")
            
        return {
            "accept": result.accept_count,
            "reject": result.reject_count, 
            "pending": result.pending_count
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_match_decisions_summary: {e}")
        raise SQLAlchemyError(f"Failed to get match summary: {str(e)}") from e