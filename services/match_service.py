# services/match_service.py
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from frameworks.db import models


def create_match(
    db: Session,
    *,
    pool_id: UUID,
    user1_id: UUID,
    user2_id: UUID,
):
    """
    Create a new match (status starts as 'waiting').
    - Ensures user1 != user2
    - Normalizes user order: user1_id < user2_id
    - Ensures both are members of the pool
    - Enforces uniqueness of pair per pool.
    """
    if user1_id == user2_id:
        raise ValueError("Cannot create a match with the same user on both sides")

    # Normalize order: smaller UUID first
    if str(user1_id) > str(user2_id):
        user1_id, user2_id = user2_id, user1_id

    # Check membership
    for uid in (user1_id, user2_id):
        exists = db.get(models.PoolMember, (str(pool_id), str(uid)))
        if not exists:
            raise ValueError(f"User {uid} is not a member of pool {pool_id}")

    match = models.Match(
        pool_id=str(pool_id),
        user1_id=str(user1_id),
        user2_id=str(user2_id),
        # status defaults to 'waiting' via model default
    )
    db.add(match)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # If unique constraint fails, check if there's an existing match for this pair
        existing = (
            db.query(models.Match)
            .filter(
                models.Match.pool_id == str(pool_id),
                models.Match.user1_id == str(user1_id),
                models.Match.user2_id == str(user2_id),
                models.Match.status == models.MatchStatus.waiting,
            )
            .first()
        )
        if existing:
            return existing
        raise e
    db.refresh(match)
    return match


def get_match(db: Session, match_id: UUID):
    """Get a single match by ID."""
    match = db.get(models.Match, str(match_id))
    return match


def list_matches(
    db: Session,
    *,
    pool_id: UUID | None = None,
    user_id: UUID | None = None,
    status_filter: str | None = None,
):
    """List matches with optional filters."""
    q = db.query(models.Match)
    if pool_id:
        q = q.filter(models.Match.pool_id == str(pool_id))
    if user_id:
        q = q.filter(
            (models.Match.user1_id == str(user_id)) | (models.Match.user2_id == str(user_id))
        )
    if status_filter:
        # Validate status against allowed values
        if status_filter not in {s.value for s in models.MatchStatus}:
            raise ValueError(f"Invalid status filter: {status_filter}")
        q = q.filter(models.Match.status == status_filter)
    return q.order_by(models.Match.created_at.desc()).all()


def patch_match(
    db: Session,
    *,
    match_id: UUID,
    pool_id: UUID | None = None,
    user1_id: UUID | None = None,
    user2_id: UUID | None = None,
    status: str | None = None,
):
    """Partial update of a match.
    
    Note: Changing pool_id or user IDs after creation is generally not recommended.
    The primary use case is updating status.
    """
    match = db.get(models.Match, str(match_id))
    if not match:
        raise ValueError("Match not found")

    changed = False
    
    # Update pool_id if provided
    if pool_id is not None:
        match.pool_id = str(pool_id)
        changed = True
    
    # Update user IDs if provided
    if user1_id is not None:
        match.user1_id = str(user1_id)
        changed = True
    if user2_id is not None:
        match.user2_id = str(user2_id)
        changed = True
    
    # Re-normalize user order if either user ID was changed
    if user1_id is not None or user2_id is not None:
        if match.user1_id == match.user2_id:
            raise ValueError("Cannot have the same user on both sides")
        if match.user1_id > match.user2_id:
            match.user1_id, match.user2_id = match.user2_id, match.user1_id
    
    # Update status if provided (with validation)
    if status is not None:
        # Validate status against enum
        if status not in {s.value for s in models.MatchStatus}:
            raise ValueError(f"Invalid status: {status}. Must be one of: {[s.value for s in models.MatchStatus]}")
        match.status = status
        changed = True

    if changed:
        db.add(match)
        db.commit()
        db.refresh(match)
    return match


def delete_match(db: Session, match_id: UUID):
    """Delete a match and its associated decisions (cascades via DB)."""
    match = db.get(models.Match, str(match_id))
    if not match:
        raise ValueError("Match not found")
    
    db.delete(match)
    db.commit()
    return True
