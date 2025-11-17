"""Match service layer - business logic for match operations."""
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from frameworks.db import models
from match.match_exceptions import (
    MatchNotFoundError,
    InvalidMatchError,
    DuplicateMatchError,
    UserNotInPoolError,
)


def _get_match_or_raise(db: Session, match_id: UUID) -> models.Match:
    """Helper to get match or raise MatchNotFoundError."""
    match = db.get(models.Match, str(match_id))
    if not match:
        raise MatchNotFoundError(match_id)
    return match


def create_match(
    db: Session,
    *,
    pool_id: UUID,
    user1_id: UUID,
    user2_id: UUID,
):
    """Create a new match (status starts as 'waiting')."""
    if user1_id == user2_id:
        raise InvalidMatchError("Cannot create a match with the same user on both sides")

    if str(user1_id) > str(user2_id):
        user1_id, user2_id = user2_id, user1_id

    for uid in (user1_id, user2_id):
        exists = db.get(models.PoolMember, (str(pool_id), str(uid)))
        if not exists:
            raise UserNotInPoolError(uid, pool_id)

    match = models.Match(
        pool_id=str(pool_id),
        user1_id=str(user1_id),
        user2_id=str(user2_id),
    )
    db.add(match)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateMatchError(pool_id, user1_id, user2_id)
    db.refresh(match)
    return match


def get_match(db: Session, match_id: UUID):
    """Get a single match by ID."""
    return _get_match_or_raise(db, match_id)


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
    """Partial update of a match."""
    match = _get_match_or_raise(db, match_id)

    if pool_id is not None:
        match.pool_id = str(pool_id)
    if user1_id is not None:
        match.user1_id = str(user1_id)
    if user2_id is not None:
        match.user2_id = str(user2_id)
    if status is not None:
        match.status = status

    db.commit()
    db.refresh(match)
    return match
