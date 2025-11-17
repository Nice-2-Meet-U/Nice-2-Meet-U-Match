# services/pool_service.py
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from frameworks.db import models
from exceptions import PoolNotFoundError, MemberNotFoundError, MemberAlreadyExistsError


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
    """
    Get a pool by ID.

    Raises:
        PoolNotFoundError: If pool doesn't exist
    """
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise PoolNotFoundError(pool_id)
    return pool


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
    """
    Update pool fields (partial update).

    Raises:
        PoolNotFoundError: If pool doesn't exist
    """
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise PoolNotFoundError(pool_id)

    if name is not None:
        pool.name = name
    if location is not None:
        pool.location = location

    db.commit()
    db.refresh(pool)
    return pool


def delete_pool(db: Session, pool_id: UUID):
    """
    Delete a pool (cascades to members and matches).

    Raises:
        PoolNotFoundError: If pool doesn't exist
    """
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise PoolNotFoundError(pool_id)

    db.delete(pool)
    db.commit()
    return True


def add_pool_member(
    db: Session,
    *,
    pool_id: UUID,
    user_id: UUID,
):
    """
    Add a user to a pool.
    Updates the pool's member_count.

    Raises:
        PoolNotFoundError: If pool doesn't exist
        MemberAlreadyExistsError: If user is already a member
    """
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise PoolNotFoundError(pool_id)

    # Check if already a member
    existing = db.get(models.PoolMember, (str(pool_id), str(user_id)))
    if existing:
        raise MemberAlreadyExistsError(pool_id, user_id)

    member = models.PoolMember(
        pool_id=str(pool_id),
        user_id=str(user_id),
    )
    db.add(member)
    db.flush()

    # Update member count
    pool.member_count = (
        db.query(func.count(models.PoolMember.user_id))
        .filter(models.PoolMember.pool_id == str(pool_id))
        .scalar()
    )

    db.commit()
    db.refresh(member)
    return member


def remove_pool_member(
    db: Session,
    *,
    pool_id: UUID,
    user_id: UUID,
):
    """
    Remove a user from a pool.
    Updates the pool's member_count.

    Raises:
        PoolNotFoundError: If pool doesn't exist
        MemberNotFoundError: If user is not a member
    """
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise PoolNotFoundError(pool_id)

    member = db.get(models.PoolMember, (str(pool_id), str(user_id)))
    if not member:
        raise MemberNotFoundError(pool_id, user_id)

    db.delete(member)
    db.flush()

    # Update member count
    pool.member_count = (
        db.query(func.count(models.PoolMember.user_id))
        .filter(models.PoolMember.pool_id == str(pool_id))
        .scalar()
    )

    db.commit()
    return True


def list_pool_members(
    db: Session,
    *,
    pool_id: UUID,
    skip: int = 0,
    limit: int = 100,
):
    """
    List all members of a pool.

    Raises:
        PoolNotFoundError: If pool doesn't exist
    """
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise PoolNotFoundError(pool_id)

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
    """
    Get a specific pool member.

    Raises:
        MemberNotFoundError: If user is not a member
    """
    member = db.get(models.PoolMember, (str(pool_id), str(user_id)))
    if not member:
        raise MemberNotFoundError(pool_id, user_id)
    return member
