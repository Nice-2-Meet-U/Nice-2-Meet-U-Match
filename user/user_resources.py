"""User API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from frameworks.db.session import get_db
from user.user_services import add_user_to_pool, generate_matches_for_user
from user.user_exceptions import UserNotInPoolError
from user.user_schemas import (
    UserAddToPoolResponse,
    UserGenerateMatchesResponse,
    MatchSummary,
)
from pool.pool_schemas import PoolRead, PoolMemberRead

router = APIRouter()


@router.post(
    "/{user_id}/add-to-pool",
    response_model=UserAddToPoolResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_user_to_pool_endpoint(
    user_id: UUID, 
    location: str = Query(..., description="Location to add user to"),
    db: Session = Depends(get_db)
):
    """Add user to a pool by location, creating one if needed."""
    result = add_user_to_pool(db, user_id=user_id, location=location)
    
    pool_data = result["pool"]
    member_data = result["member"]
    
    return UserAddToPoolResponse(
        message=result["message"],
        pool=PoolRead(
            id=UUID(pool_data["id"]),
            name=pool_data["name"],
            location=pool_data["location"],
            member_count=pool_data["member_count"],
            created_at=pool_data["created_at"],
        ),
        member=PoolMemberRead(
            user_id=UUID(member_data["user_id"]),
            pool_id=UUID(member_data["pool_id"]),
            joined_at=member_data["joined_at"],
        ),
    )


@router.post(
    "/{user_id}/generate-matches",
    response_model=UserGenerateMatchesResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_matches_for_user_endpoint(
    user_id: UUID,
    max_matches: int = Query(10, ge=1, le=50, description="Maximum number of matches to generate"),
    db: Session = Depends(get_db)
):
    """Generate random matches for user with other pool members."""
    try:
        result = generate_matches_for_user(db, user_id=user_id, max_matches=max_matches)
        
        return UserGenerateMatchesResponse(
            message=result["message"],
            pool_id=result["pool_id"],
            matches_created=result["matches_created"],
            matches=[
                MatchSummary(
                    match=match_data["match"],
                    user1_decision=match_data.get("user1_decision"),
                    user2_decision=match_data.get("user2_decision"),
                    both_decided=(
                        match_data.get("user1_decision") is not None 
                        and match_data.get("user2_decision") is not None
                    ),
                )
                for match_data in result["matches"]
            ],
        )
    except UserNotInPoolError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not in any pool")