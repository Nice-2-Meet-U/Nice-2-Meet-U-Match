from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from frameworks.db.session import get_db
from frameworks.hateoas import build_links
from pool.pool_services import (
    create_pool,
    get_pool,
    list_pools,
    update_pool,
    delete_pool,
    add_pool_member,
    remove_pool_member,
    list_pool_members,
    get_pool_member,
)
from pool.pool_schemas import (
    PoolCreate,
    PoolRead,
    PoolPatch,
    PoolMemberCreate,
    PoolMemberRead,
)
from pool.pool_exceptions import (
    PoolNotFoundError,
    MemberNotFoundError,
    MemberAlreadyExistsError,
)

router = APIRouter()


# =========================
# Pool Endpoints
# =========================


@router.post("/", response_model=PoolRead, status_code=status.HTTP_201_CREATED)
def create_pool_endpoint(
    payload: PoolCreate,
    db: Session = Depends(get_db),
):
    """Create a new pool."""
    pool = create_pool(
        db,
        name=payload.name,
        location=payload.location,
    )
    pool.links = build_links("pool", UUID(pool.id))
    return pool


@router.get("/{pool_id}", response_model=PoolRead)
def get_pool_endpoint(
    pool_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a pool by ID."""
    try:
        pool = get_pool(db, pool_id)
        pool.links = build_links("pool", UUID(pool.id))
        return pool
    except PoolNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pool not found")


@router.get("/", response_model=list[PoolRead])
def list_pools_endpoint(
    location: str | None = Query(None, description="Filter pools by location"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db),
):
    """List all pools, optionally filtered by location."""
    pools = list_pools(db, location=location, skip=skip, limit=limit)
    for pool in pools:
        pool.links = build_links("pool", UUID(pool.id))
    return pools


@router.patch("/{pool_id}", response_model=PoolRead)
def update_pool_endpoint(
    pool_id: UUID,
    payload: PoolPatch,
    db: Session = Depends(get_db),
):
    """Update a pool (partial update)."""
    try:
        pool = update_pool(
            db,
            pool_id=pool_id,
            name=payload.name,
            location=payload.location,
        )
        pool.links = build_links("pool", UUID(pool.id))
        return pool
    except PoolNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pool not found")


@router.delete("/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pool_endpoint(
    pool_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a pool (cascades to members and matches)."""
    try:
        delete_pool(db, pool_id)
    except PoolNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pool not found")


# =========================
# Pool Member Endpoints
# =========================


@router.post(
    "/{pool_id}/members",
    response_model=PoolMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_pool_member_endpoint(
    pool_id: UUID,
    payload: PoolMemberCreate,
    db: Session = Depends(get_db),
):
    """Add a user to a pool."""
    try:
        member = add_pool_member(
            db,
            pool_id=pool_id,
            user_id=payload.user_id,
        )
        member.links = {"pool": build_links("pool", pool_id)["self"]}
        return member
    except PoolNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pool not found")
    except MemberAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already in pool")


@router.get("/{pool_id}/members", response_model=list[PoolMemberRead])
def list_pool_members_endpoint(
    pool_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db),
):
    """List all members of a pool."""
    try:
        members = list_pool_members(db, pool_id=pool_id, skip=skip, limit=limit)
        for member in members:
            member.links = {"pool": build_links("pool", pool_id)["self"]}
        return members
    except PoolNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pool not found")


@router.get("/{pool_id}/members/{user_id}", response_model=PoolMemberRead)
def get_pool_member_endpoint(
    pool_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a specific pool member."""
    try:
        return get_pool_member(db, pool_id=pool_id, user_id=user_id)
    except MemberNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")


@router.delete(
    "/{pool_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_pool_member_endpoint(
    pool_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Remove a user from a pool."""
    try:
        remove_pool_member(db, pool_id=pool_id, user_id=user_id)
    except PoolNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pool not found")
    except MemberNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
