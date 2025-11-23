# resources/pools.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from frameworks.db.session import get_db
from frameworks.db import models
from services.pool_service import (
    create_pool,
    get_pool,
    list_pools,
    update_pool,
    delete_pool,
    add_pool_member,
    remove_pool_member,
    list_pool_members,
    get_pool_member,
    list_all_pool_members,
)
from models.pool import PoolCreate, PoolRead, PoolPatch, PoolMemberCreate, PoolMemberRead, PoolMemberDeleteResponse

router = APIRouter()


# =========================
# Pool Endpoints
# =========================


@router.post("/", response_model=PoolRead, status_code=status.HTTP_201_CREATED)
def create_pool_endpoint(payload: PoolCreate, db: Session = Depends(get_db)):
    """Create a new pool."""
    try:
        pool = create_pool(
            db,
            name=payload.name,
            location=payload.location,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return pool


@router.get("/", response_model=list[PoolRead])
def list_pools_endpoint(
    location: Optional[str] = Query(None, description="Filter pools by location"),
    db: Session = Depends(get_db),
):
    """List all pools, optionally filtered by location."""
    pools = list_pools(db, location=location)
    return pools


@router.get("/members", response_model=list[PoolMemberRead])
def list_all_pool_members_endpoint(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
):
    """List all pool members across all pools, optionally filtered by user_id."""
    members = list_all_pool_members(db, user_id=user_id)
    return members


@router.delete("/members/{user_id}", response_model=PoolMemberDeleteResponse)
def delete_pool_member_by_user_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Remove a user from their pool by user_id only."""
    # Find which pool the user is in
    member = db.query(models.PoolMember).filter(
        models.PoolMember.user_id == str(user_id)
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="User is not a member of any pool")
    
    pool_id = member.pool_id
    
    try:
        remove_pool_member(db, pool_id=UUID(pool_id), user_id=user_id)
        return PoolMemberDeleteResponse(
            message=f"User {user_id} removed from pool {pool_id}",
            user_id=user_id,
            pool_id=UUID(pool_id),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{pool_id}", response_model=PoolRead)
def get_pool_endpoint(pool_id: UUID, db: Session = Depends(get_db)):
    """Get a pool by ID."""
    pool = get_pool(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return pool


@router.patch("/{pool_id}", response_model=PoolRead)
def update_pool_endpoint(
    pool_id: UUID, payload: PoolPatch, db: Session = Depends(get_db)
):
    """Update a pool (partial update)."""
    try:
        pool = update_pool(
            db,
            pool_id=pool_id,
            name=payload.name,
            location=payload.location,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return pool


@router.delete("/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pool_endpoint(pool_id: UUID, db: Session = Depends(get_db)):
    """Delete a pool (cascades to members and matches)."""
    try:
        delete_pool(db, pool_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None


# =========================
# Pool Member Endpoints
# =========================


@router.post(
    "/{pool_id}/members",
    response_model=PoolMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_pool_member_endpoint(
    pool_id: UUID, payload: PoolMemberCreate, db: Session = Depends(get_db)
):
    """Add a user to a pool."""
    try:
        member = add_pool_member(
            db,
            pool_id=pool_id,
            user_id=payload.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return member


@router.get("/{pool_id}/members", response_model=list[PoolMemberRead])
def list_pool_members_endpoint(pool_id: UUID, db: Session = Depends(get_db)):
    """List all members of a pool."""
    try:
        members = list_pool_members(db, pool_id=pool_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return members


@router.get(
    "/{pool_id}/members/{user_id}", response_model=PoolMemberRead
)
def get_pool_member_endpoint(
    pool_id: UUID, user_id: UUID, db: Session = Depends(get_db)
):
    """Get a specific pool member."""
    member = get_pool_member(db, pool_id=pool_id, user_id=user_id)
    if not member:
        raise HTTPException(status_code=404, detail="User is not a member of this pool")
    return member

