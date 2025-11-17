"""Pool service layer - business logic for pool operations."""
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from frameworks.db import models
from pool.pool_exceptions import PoolNotFoundError, MemberNotFoundError, MemberAlreadyExistsError


def _get_pool_or_raise(db: Session, pool_id: UUID) -> models.Pool:
    """Helper to get pool or raise PoolNotFoundError."""
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise PoolNotFoundError(pool_id)
    return pool


def create_pool(
    db: Session,
    *,
    name: str,
    location: str | None = None,
):
    """Create a new pool."""
    pool = models.Pool(
        name=name,
        location=location,
        member_count=0,
    )
    db.add(pool)
    db.commit()
    db.refresh(pool)
    return pool


def get_pool(db: Session, pool_id: UUID):
    """Get a pool by ID."""
    return _get_pool_or_raise(db, pool_id)


def list_pools(
    db: Session,
    *,
    location: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """List pools, optionally filtered by location."""
    q = db.query(models.Pool)
    if location:
        q = q.filter(models.Pool.location == location)
    return q.order_by(models.Pool.created_at.desc()).offset(skip).limit(limit).all()


def update_pool(
    db: Session,
    *,
    pool_id: UUID,
    name: str | None = None,
    location: str | None = None,
):
    """Update pool fields (partial update)."""
    pool = _get_pool_or_raise(db, pool_id)

    if name is not None:
        pool.name = name
    if location is not None:
        pool.location = location

    db.commit()
    db.refresh(pool)
    return pool


def delete_pool(db: Session, pool_id: UUID):
    """Delete a pool (cascades to members and matches)."""
    pool = _get_pool_or_raise(db, pool_id)
    db.delete(pool)
    db.commit()


def add_pool_member(
    db: Session,
    *,
    pool_id: UUID,
    user_id: UUID,
):
    """Add a user to a pool and increment member count."""
    pool = _get_pool_or_raise(db, pool_id)

    existing = db.get(models.PoolMember, (str(pool_id), str(user_id)))
    if existing:
        raise MemberAlreadyExistsError(pool_id, user_id)

    member = models.PoolMember(
        pool_id=str(pool_id),
        user_id=str(user_id),
    )
    db.add(member)
    pool.member_count += 1

    db.commit()
    db.refresh(member)
    return member


def remove_pool_member(
    db: Session,
    *,
    pool_id: UUID,
    user_id: UUID,
):
    """Remove a user from a pool and decrement member count."""
    pool = _get_pool_or_raise(db, pool_id)

    member = db.get(models.PoolMember, (str(pool_id), str(user_id)))
    if not member:
        raise MemberNotFoundError(pool_id, user_id)

    db.delete(member)
    pool.member_count -= 1

    db.commit()


def list_pool_members(
    db: Session,
    *,
    pool_id: UUID,
    skip: int = 0,
    limit: int = 100,
):
    """List all members of a pool."""
    _get_pool_or_raise(db, pool_id)

    return (
        db.query(models.PoolMember)
        .filter(models.PoolMember.pool_id == str(pool_id))
        .order_by(models.PoolMember.joined_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_pool_member(
    db: Session,
    *,
    pool_id: UUID,
    user_id: UUID,
):
    """Get a specific pool member."""
    member = db.get(models.PoolMember, (str(pool_id), str(user_id)))
    if not member:
        raise MemberNotFoundError(pool_id, user_id)
    return member
