# services/pool_service.py
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from frameworks.db import models


def create_pool(
    db: Session,
    *,
    name: str,
    location: str | None = None,
):
    """
    Create a new pool.
    """
    pool = models.Pool(
        name=name,
        location=location,
        member_count=0,  # Will be updated when members are added
    )
    db.add(pool)
    db.commit()
    db.refresh(pool)
    return pool


def get_pool(db: Session, pool_id: UUID):
    """Get a pool by ID."""
    pool = db.get(models.Pool, str(pool_id))
    return pool


def list_pools(
    db: Session,
    *,
    location: str | None = None,
):
    """List pools, optionally filtered by location."""
    q = db.query(models.Pool)
    if location:
        q = q.filter(models.Pool.location == location)
    return q.order_by(models.Pool.created_at.desc()).all()


def update_pool(
    db: Session,
    *,
    pool_id: UUID,
    name: str | None = None,
    location: str | None = None,
):
    """Update pool fields (partial update)."""
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise ValueError("Pool not found")
    
    if name is not None:
        pool.name = name
    if location is not None:
        pool.location = location
    
    db.add(pool)
    db.commit()
    db.refresh(pool)
    return pool


def delete_pool(db: Session, pool_id: UUID):
    """Delete a pool (cascades to members and matches)."""
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise ValueError("Pool not found")
    
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
    """
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise ValueError("Pool not found")
    
    # Check if already a member
    existing = db.get(models.PoolMember, (str(pool_id), str(user_id)))
    if existing:
        return existing  # Idempotent - return existing member
    
    member = models.PoolMember(
        pool_id=str(pool_id),
        user_id=str(user_id),
    )
    db.add(member)
    
    try:
        db.flush()  # Flush to get the member in the DB for counting
        # Update member count
        pool.member_count = (
            db.query(func.count(models.PoolMember.user_id))
            .filter(models.PoolMember.pool_id == str(pool_id))
            .scalar()
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Failed to add member to pool")
    
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
    """
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise ValueError("Pool not found")
    
    member = db.get(models.PoolMember, (str(pool_id), str(user_id)))
    if not member:
        raise ValueError("User is not a member of this pool")
    
    db.delete(member)
    db.flush()  # Flush to remove the member from DB for counting
    
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
):
    """List all members of a pool."""
    pool = db.get(models.Pool, str(pool_id))
    if not pool:
        raise ValueError("Pool not found")
    
    return db.query(models.PoolMember).filter(
        models.PoolMember.pool_id == str(pool_id)
    ).order_by(models.PoolMember.joined_at.asc()).all()


def get_pool_member(
    db: Session,
    *,
    pool_id: UUID,
    user_id: UUID,
):
    """Get a specific pool member."""
    member = db.get(models.PoolMember, (str(pool_id), str(user_id)))
    return member


def get_pool_by_user_id(db: Session, user_id: UUID):
    """
    Get the pool that a user belongs to by checking pool_members table.
    Returns dict with pool and member info, or None if user is not in any pool.
    """
    member = db.query(models.PoolMember).filter(
        models.PoolMember.user_id == str(user_id)
    ).first()
    
    if not member:
        return None
    
    pool = db.get(models.Pool, member.pool_id)
    return {"pool": pool, "member": member}


def get_members_by_user_id(db: Session, user_id: UUID):
    """
    Get all members in the same pool as the specified user.
    Returns list of pool members, or None if user is not in any pool.
    """
    # First find which pool the user is in
    user_member = db.query(models.PoolMember).filter(
        models.PoolMember.user_id == str(user_id)
    ).first()
    
    if not user_member:
        return None
    
    # Get all members of that pool
    members = db.query(models.PoolMember).filter(
        models.PoolMember.pool_id == user_member.pool_id
    ).order_by(models.PoolMember.joined_at.asc()).all()
    
    return members


def list_all_pool_members(db: Session, user_id: UUID | None = None):
    """
    List all pool members across all pools.
    Optionally filter by user_id to find a specific user's membership.
    """
    q = db.query(models.PoolMember)
    if user_id:
        q = q.filter(models.PoolMember.user_id == str(user_id))
    return q.order_by(models.PoolMember.joined_at.asc()).all()

