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
    - Optional: ensure both are members of the pool (if you have PoolMember w/ UUIDs)
    - Enforces uniqueness of pair per pool if you added a unique index (u_low/u_high) at the DB level.
    """
    if user1_id == user2_id:
        raise ValueError("Cannot create a match with the same user on both sides")

    # (Optional) membership check; uncomment if PoolMember uses UUIDs
    # for uid in (user1_id, user2_id):
    #     exists = db.query(models.PoolMember).get((pool_id, uid))
    #     if not exists:
    #         raise ValueError(f"User {uid} is not a member of pool {pool_id}")

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
        # If you have a unique constraint (pool_id, u_low, u_high) waiting-only,
        # you can choose to fetch and return the existing row to make it idempotent:
        existing = (
            db.query(models.Match)
            .filter(
                models.Match.pool_id == str(pool_id),
                # If you added u_low/u_high generated columns, use them here
                # Otherwise, just look for any active 'waiting' pair in either order:
                (
                    (models.Match.user1_id == str(user1_id))
                    & (models.Match.user2_id == str(user2_id))
                )
                | (
                    (models.Match.user1_id == str(user2_id))
                    & (models.Match.user2_id == str(user1_id))
                ),
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
    m = db.get(models.Match, str(match_id))
    return m
