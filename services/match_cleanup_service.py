# services/match_cleanup_service.py
"""
Service for cleaning up non-accepted matches when users leave pools.
This is triggered by Pub/Sub events from the pools service.
"""
from __future__ import annotations

import logging
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from frameworks.db import models

logger = logging.getLogger(__name__)


def cleanup_user_matches(
    db: Session,
    *,
    pool_id: UUID,
    user_id: UUID,
) -> dict:
    """
    Delete all non-accepted matches for a user in a specific pool.
    
    This is called when a user leaves a pool. We keep accepted matches
    (both users said yes) but delete waiting and rejected matches.
    
    Args:
        db: Database session
        pool_id: The pool the user is leaving
        user_id: The user who is leaving
        
    Returns:
        Dictionary with cleanup statistics
    """
    user_id_str = str(user_id)
    pool_id_str = str(pool_id)
    
    # Find all matches in this pool where the user is a participant
    # and status is NOT 'accepted'
    matches_to_delete = db.query(models.Match).filter(
        and_(
            models.Match.pool_id == pool_id_str,
            or_(
                models.Match.user1_id == user_id_str,
                models.Match.user2_id == user_id_str
            ),
            models.Match.status != models.MatchStatus.accepted.value
        )
    ).all()
    
    deleted_matches = []
    deleted_decisions = 0
    
    for match in matches_to_delete:
        match_id = match.match_id
        
        # Count decisions that will be cascaded
        decision_count = db.query(models.MatchDecision).filter(
            models.MatchDecision.match_id == match_id
        ).count()
        
        deleted_decisions += decision_count
        deleted_matches.append({
            "match_id": match_id,
            "status": match.status,
            "decisions_deleted": decision_count
        })
        
        # Delete the match (decisions will cascade)
        db.delete(match)
    
    db.commit()
    
    result = {
        "pool_id": pool_id_str,
        "user_id": user_id_str,
        "matches_deleted": len(deleted_matches),
        "decisions_deleted": deleted_decisions,
        "matches": deleted_matches
    }
    
    logger.info(
        f"Cleaned up {len(deleted_matches)} matches and {deleted_decisions} decisions "
        f"for user {user_id} leaving pool {pool_id}"
    )
    
    return result


def cleanup_pool_matches(
    db: Session,
    *,
    pool_id: UUID,
) -> dict:
    """
    Delete all non-accepted matches in a pool.
    
    This can be called when a pool is being cleaned up or deleted.
    
    Args:
        db: Database session
        pool_id: The pool to clean up
        
    Returns:
        Dictionary with cleanup statistics
    """
    pool_id_str = str(pool_id)
    
    # Find all non-accepted matches in this pool
    matches_to_delete = db.query(models.Match).filter(
        and_(
            models.Match.pool_id == pool_id_str,
            models.Match.status != models.MatchStatus.accepted.value
        )
    ).all()
    
    deleted_matches = []
    deleted_decisions = 0
    
    for match in matches_to_delete:
        match_id = match.match_id
        
        decision_count = db.query(models.MatchDecision).filter(
            models.MatchDecision.match_id == match_id
        ).count()
        
        deleted_decisions += decision_count
        deleted_matches.append({
            "match_id": match_id,
            "status": match.status,
            "user1_id": match.user1_id,
            "user2_id": match.user2_id,
            "decisions_deleted": decision_count
        })
        
        db.delete(match)
    
    db.commit()
    
    result = {
        "pool_id": pool_id_str,
        "matches_deleted": len(deleted_matches),
        "decisions_deleted": deleted_decisions,
        "matches": deleted_matches
    }
    
    logger.info(
        f"Cleaned up {len(deleted_matches)} non-accepted matches "
        f"and {deleted_decisions} decisions for pool {pool_id}"
    )
    
    return result
