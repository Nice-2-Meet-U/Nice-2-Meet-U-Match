"""User service layer - orchestrates other microservices via HTTP."""
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
import random
from fastapi import HTTPException

from frameworks.db import models
from user.user_exceptions import UserNotInPoolError
from user.service_clients import PoolServiceClient, MatchServiceClient, DecisionServiceClient


def add_user_to_pool(
    db: Session, *, user_id: UUID, location: str
):
    """Add user to a pool by location, creating one if needed via HTTP calls."""
    pool_client = PoolServiceClient()
    
    try:
        # Call pool service to list pools at location
        pools = pool_client.list_pools(location=location)
        
        if not pools:
            # Call pool service to create a new pool
            pool_name = f"Pool for {location}"
            pool_data = pool_client.create_pool(name=pool_name, location=location)
        else:
            pool_data = random.choice(pools)
        
        pool_id = UUID(pool_data["id"])
        
        # Call pool service to add member (handles 409 Conflict if already exists)
        try:
            member_data = pool_client.add_pool_member(pool_id=pool_id, user_id=user_id)
        except HTTPException as e:
            if e.status_code == 409:
                # Member already exists, fetch existing membership via HATEOAS
                members = pool_client.list_pool_members(pool_data)
                member_data = next((m for m in members if m["user_id"] == str(user_id)), None)
                if not member_data:
                    raise
            else:
                raise
        
        return {
            "pool": pool_data,
            "member": member_data,
            "message": f"User added to pool at {location}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to add user to pool: {str(e)}"
        )


def generate_matches_for_user(
    db: Session,
    *,
    user_id: UUID,
    max_matches: int = 10,
):
    """Generate random matches for user with other pool members via HTTP calls."""
    # Find user's pool membership (still use DB for this query)
    user_membership = (
        db.query(models.PoolMember)
        .filter(models.PoolMember.user_id == str(user_id))
        .first()
    )
    
    if not user_membership:
        raise UserNotInPoolError(user_id)
    
    pool_id = UUID(user_membership.pool_id)
    
    # Call pool service to get pool data (with HATEOAS links)
    pool_client = PoolServiceClient()
    pools = pool_client.list_pools()
    pool_data = next((p for p in pools if p["id"] == str(pool_id)), None)
    
    if not pool_data:
        raise UserNotInPoolError(user_id)
    
    # Use HATEOAS link to get pool members
    pool_members = pool_client.list_pool_members(pool_data)
    
    other_members = [
        member for member in pool_members 
        if member["user_id"] != str(user_id)
    ]
    
    if not other_members:
        return {
            "pool_id": str(pool_id),
            "matches_created": 0,
            "matches": [],
            "message": "No other users in pool"
        }
    
    selected_members = random.sample(
        other_members, 
        min(max_matches, len(other_members))
    )
    
    # Call match service to create matches
    match_client = MatchServiceClient()
    decision_client = DecisionServiceClient()
    created_matches = []
    
    for member in selected_members:
        try:
            match_data = match_client.create_match(
                pool_id=pool_id,
                user1_id=user_id,
                user2_id=UUID(member["user_id"])
            )
            
            # Use HATEOAS link to get decisions
            decisions = decision_client.get_decisions_for_match(match_data)
            
            user1_decision = next(
                (d for d in decisions if d["user_id"] == match_data["user1_id"]), 
                None
            )
            user2_decision = next(
                (d for d in decisions if d["user_id"] == match_data["user2_id"]), 
                None
            )
            
            created_matches.append({
                "match": match_data,
                "user1_decision": user1_decision,
                "user2_decision": user2_decision,
            })
        except HTTPException as e:
            # Skip if match already exists (409) or other validation errors (400)
            if e.status_code in [400, 409]:
                continue
            raise
    
    return {
        "pool_id": str(pool_id),
        "matches_created": len(created_matches),
        "matches": created_matches,
        "message": f"Generated {len(created_matches)} matches"
    }
