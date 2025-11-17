from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from frameworks.db.session import get_db
from frameworks.hateoas import build_links
from match.match_services import create_match, get_match, list_matches, patch_match
from match.match_schemas import MatchPost, MatchGet, MatchPatch, MatchStatus
from match.match_exceptions import (
    MatchNotFoundError,
    InvalidMatchError,
    DuplicateMatchError,
    UserNotInPoolError,
)

router = APIRouter()


@router.post("/", response_model=MatchGet, status_code=status.HTTP_201_CREATED)
def create_match_endpoint(payload: MatchPost, db: Session = Depends(get_db)):
    """Create a new match."""
    try:
        match = create_match(
            db,
            pool_id=payload.pool_id,
            user1_id=payload.user1_id,
            user2_id=payload.user2_id,
        )
        match.links = build_links("match", UUID(match.match_id))
        return match
    except InvalidMatchError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserNotInPoolError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateMatchError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match already exists")


@router.get("/{match_id}", response_model=MatchGet)
def get_match_endpoint(match_id: UUID, db: Session = Depends(get_db)):
    """Get a match by ID."""
    try:
        match = get_match(db, match_id)
        match.links = build_links("match", UUID(match.match_id))
        return match
    except MatchNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")


@router.get("/", response_model=list[MatchGet])
def list_matches_endpoint(
    pool_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(
        None, description="Filter matches where this user is a participant"
    ),
    status_filter: Optional[MatchStatus] = Query(None),
    db: Session = Depends(get_db),
):
    """List matches with optional filters."""
    matches = list_matches(
        db,
        pool_id=pool_id,
        user_id=user_id,
        status_filter=status_filter.value if status_filter else None,
    )
    for match in matches:
        match.links = build_links("match", UUID(match.match_id))
    return matches


@router.patch("/{match_id}", response_model=MatchGet)
def patch_match_endpoint(
    match_id: UUID, payload: MatchPatch, db: Session = Depends(get_db)
):
    """Update a match (partial update)."""
    try:
        match = patch_match(
            db,
            match_id=match_id,
            pool_id=payload.pool_id,
            user1_id=payload.user1_id,
            user2_id=payload.user2_id,
            status=payload.status.value if payload.status else None,
        )
        match.links = build_links("match", UUID(match.match_id))
        return match
    except MatchNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
