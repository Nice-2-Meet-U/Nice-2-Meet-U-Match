"""User service layer - orchestrates other microservices."""
from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
import random
from fastapi import HTTPException

from frameworks.db import models
from user.user_exceptions import UserNotInPoolError

# Import services directly for monolith deployment
from pool.pool_services import create_pool, list_pools, add_pool_member, list_pool_members
from match.match_services import create_match
from decision.decision_services import list_decisions


def add_user_to_pool(
    db: Session, *, user_id: UUID, location: str
):
    """Add user to a pool by location, creating one if needed."""
    try:
        # List pools at location
        pools = list_pools(db, location=location)
        
        if not pools:
            # Create a new pool
            pool_name = f"Pool for {location}"
            pool_data = create_pool(db, name=pool_name, location=location)
        else:
            pool_data = random.choice(pools)
        
        pool_id = UUID(pool_data.id)
        
        # Add member to pool
        try:
            member_data = add_pool_member(db, pool_id=pool_id, user_id=user_id)
        except Exception as e:
            # Member might already exist, fetch it
            from pool.pool_exceptions import MemberAlreadyExistsError
            if isinstance(e, MemberAlreadyExistsError):
                members = list_pool_members(db, pool_id=pool_id)
                member_data = next((m for m in members if UUID(m.user_id) == user_id), None)
                if not member_data:
                    raise
            else:
                raise
        
        return {
            "pool": {
                "id": str(pool_data.id),
                "name": pool_data.name,
                "location": pool_data.location,
                "member_count": pool_data.member_count,
                "created_at": pool_data.created_at,
            },
            "member": {
                "user_id": str(member_data.user_id),
                "pool_id": str(member_data.pool_id),
                "joined_at": member_data.joined_at,
            },
            "message": f"User added to pool at {location}"
        }
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
    """Generate random matches for user with other pool members."""
    # Find user's pool membership
    user_membership = (
        db.query(models.PoolMember)
        .filter(models.PoolMember.user_id == str(user_id))
        .first()
    )
    
    if not user_membership:
        raise UserNotInPoolError(user_id)
    
    pool_id = UUID(user_membership.pool_id)
    
    # Get pool members
    pool_members = list_pool_members(db, pool_id=pool_id)
    
    other_members = [
        member for member in pool_members 
        if UUID(member.user_id) != user_id
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
    
    # Create matches
    created_matches = []
    
    for member in selected_members:
        try:
            match_data = create_match(
                db,
                pool_id=pool_id,
                user1_id=user_id,
                user2_id=UUID(member.user_id)
            )
            
            # Get decisions for this match
            decisions = list_decisions(db, match_id=UUID(match_data.match_id))
            
            user1_decision = next(
                (d for d in decisions if UUID(d.user_id) == UUID(match_data.user1_id)), 
                None
            )
            user2_decision = next(
                (d for d in decisions if UUID(d.user_id) == UUID(match_data.user2_id)), 
                None
            )
            
            # Convert to dict format
            match_dict = {
                "match_id": str(match_data.match_id),
                "pool_id": str(match_data.pool_id),
                "user1_id": str(match_data.user1_id),
                "user2_id": str(match_data.user2_id),
                "status": match_data.status,
                "created_at": match_data.created_at,
                "updated_at": match_data.updated_at,
            }
            
            user1_dec_dict = None
            if user1_decision:
                user1_dec_dict = {
                    "match_id": str(user1_decision.match_id),
                    "user_id": str(user1_decision.user_id),
                    "decision": user1_decision.decision,
                    "decided_at": user1_decision.decided_at,
                }
            
            user2_dec_dict = None
            if user2_decision:
                user2_dec_dict = {
                    "match_id": str(user2_decision.match_id),
                    "user_id": str(user2_decision.user_id),
                    "decision": user2_decision.decision,
                    "decided_at": user2_decision.decided_at,
                }
            
            created_matches.append({
                "match": match_dict,
                "user1_decision": user1_dec_dict,
                "user2_decision": user2_dec_dict,
            })
        except Exception as e:
            # Skip if match already exists or other validation errors
            from match.match_exceptions import DuplicateMatchError, InvalidMatchError
            if isinstance(e, (DuplicateMatchError, InvalidMatchError)):
                continue
            raise
    
    return {
        "pool_id": str(pool_id),
        "matches_created": len(created_matches),
        "matches": created_matches,
        "message": f"Generated {len(created_matches)} matches"
    }
