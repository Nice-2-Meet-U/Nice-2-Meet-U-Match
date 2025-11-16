# resources/decisions.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import random

from frameworks.db.session import get_db
from services.decision_service import submit_decision, list_decisions
from services.pool_service import create_pool, list_pools, add_pool_member, list_pool_members
from services.match_service import create_match
from models.decisions import DecisionPost, DecisionGet
from frameworks.db import models

router = APIRouter()


@router.post("/", response_model=DecisionGet, status_code=status.HTTP_201_CREATED)
def submit_decision_endpoint(payload: DecisionPost, db: Session = Depends(get_db)):
    try:
        # submit_decision updates DB and returns the updated Match, we don't need
        # the return value here because the endpoint returns the decision row.
        submit_decision(
            db,
            match_id=payload.match_id,
            user_id=payload.user_id,
            decision=payload.decision,  # Already DecisionValue enum
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Return this user's current decision row as confirmation
    # Use Session.get instead of Query.get (deprecated)
    d = db.get(models.MatchDecision, (str(payload.match_id), str(payload.user_id)))
    if not d:
        # This should not happen; defensive
        raise HTTPException(status_code=500, detail="Decision not recorded")
    return d


@router.get("/", response_model=list[DecisionGet])
def list_decisions_endpoint(
    match_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    decisions = list_decisions(db, match_id=match_id, user_id=user_id)
    return decisions


@router.post("/users/{user_id}/add-to-pool", status_code=status.HTTP_201_CREATED)
def add_user_to_pool(user_id: UUID, location: str, db: Session = Depends(get_db)):
    """
    Add a user to a pool by location. Creates a new pool if none exists for the location,
    otherwise adds to a random existing pool at that location.
    """
    try:
        # Find pools at the specified location
        pools = list_pools(db, location=location)
        
        if not pools:
            # No pools exist for this location, create a new one
            pool_name = f"Pool for {location}"
            pool = create_pool(db, name=pool_name, location=location)
        else:
            # Select a random pool from the available pools at this location
            pool = random.choice(pools)
        
        # Add the user to the selected/created pool
        member = add_pool_member(db, pool_id=pool.id, user_id=user_id)
        
        return {
            "message": f"User {user_id} added to pool {pool.id} at location {location}",
            "pool_id": pool.id,
            "pool_name": pool.name,
            "location": location,
            "member_info": member
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add user to pool: {str(e)}")


@router.post("/users/{user_id}/generate-matches", status_code=status.HTTP_201_CREATED)
def generate_matches_for_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Find the user's pool and generate up to 10 random matches with other pool members.
    """
    try:
        # Find the user's pool membership
        user_membership = (
            db.query(models.PoolMember)
            .filter(models.PoolMember.user_id == str(user_id))
            .first()
        )
        
        if not user_membership:
            raise HTTPException(
                status_code=404, 
                detail="User is not a member of any pool. Add user to a pool first."
            )
        
        pool_id = user_membership.pool_id
        
        # Get all other members of the same pool
        pool_members = list_pool_members(db, pool_id=UUID(pool_id))
        other_members = [
            member for member in pool_members 
            if member.user_id != str(user_id)
        ]
        
        if not other_members:
            return {
                "message": "No other users in the pool to match with",
                "pool_id": pool_id,
                "matches_created": 0,
                "matches": []
            }
        
        # Select up to 10 random other members
        selected_members = random.sample(
            other_members, 
            min(10, len(other_members))
        )
        
        created_matches = []
        for member in selected_members:
            try:
                match = create_match(
                    db,
                    pool_id=UUID(pool_id),
                    user1_id=user_id,
                    user2_id=UUID(member.user_id)
                )
                created_matches.append({
                    "match_id": match.id,
                    "user1_id": match.user1_id,
                    "user2_id": match.user2_id,
                    "status": match.status
                })
            except ValueError:
                # Skip if match already exists or other validation error
                continue
        
        return {
            "message": f"Generated {len(created_matches)} matches for user {user_id}",
            "pool_id": pool_id,
            "matches_created": len(created_matches),
            "matches": created_matches
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate matches: {str(e)}")
