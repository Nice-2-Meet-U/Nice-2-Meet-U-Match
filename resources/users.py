# resources/users.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
import random
import httpx

from frameworks.db.session import get_db
from services.decision_service import submit_decision, list_decisions
from services.pool_service import (
    create_pool,
    list_pools,
    add_pool_member,
    list_pool_members,
)
from services.match_service import create_match
from models.decisions import DecisionPost, DecisionGet
from models.match import MatchGet
from models.pool import PoolRead, PoolMemberRead
from models.composite import (
    CompositeOperationResponse, PoolOperationInfo, MemberOperationInfo,
    MatchOperationInfo, MatchCandidateInfo, BasicCompositeResponse,
    BasicPoolOperationInfo, BasicMatchOperationInfo, SimpleAddToPoolResponse
)
from frameworks.db import models
from datetime import datetime

router = APIRouter()


@router.post("/", response_model=DecisionGet, status_code=status.HTTP_201_CREATED)
def submit_decision_endpoint(payload: DecisionPost, db: Session = Depends(get_db)):
    try:
        submit_decision(
            db,
            match_id=payload.match_id,
            user_id=payload.user_id,
            decision=payload.decision,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    d = db.get(models.MatchDecision, (str(payload.match_id), str(payload.user_id)))
    if not d:
        raise HTTPException(status_code=500, detail="Decision not recorded")
    return d


@router.get("/", response_model=list[DecisionGet])
def list_decisions_endpoint(
    match_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    return list_decisions(db, match_id=match_id, user_id=user_id)


@router.post("/users/{user_id}/add-to-pool", 
              response_model=SimpleAddToPoolResponse,
              status_code=status.HTTP_201_CREATED)
def add_user_to_pool(user_id: UUID, location: str, db: Session = Depends(get_db)) -> SimpleAddToPoolResponse:
    """
    Add a user to a pool by location. Creates a new pool if none exists for the location,
    otherwise adds to a random existing pool at that location.
    """
    try:
        pools = list_pools(db, location=location)
        if not pools:
            pool = create_pool(db, name=f"Pool for {location}", location=location)
        else:
            pool = random.choice(pools)

        member = add_pool_member(db, pool_id=pool.id, user_id=user_id)
        return SimpleAddToPoolResponse(
            message=f"User {user_id} added to pool {pool.id} at location {location}",
            pool_id=pool.id,
            pool_name=pool.name,
            location=location,
            member_info=member.__dict__ if hasattr(member, '__dict__') else member
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add user to pool: {str(e)}"
        )


# -------------------------------
# Helper Functions for Composite Operations
# -------------------------------

def select_optimal_pool(pools_data: List[Dict]) -> Dict:
    """
    Select the pool with the lowest number of members.
    If multiple pools have the same lowest count, pick the first one.
    """
    if not pools_data:
        raise ValueError("No pools available for selection")
    
    # Sort by member_count ascending, then by created_at for tie-breaking
    optimal_pool = min(pools_data, key=lambda p: (p.get('member_count', 0), p.get('created_at', '')))
    return optimal_pool


def pick_match_candidates_from_members(members_data: List[Dict], user_id: UUID, max_candidates: int = 10) -> List[Dict]:
    """
    Select match candidates from pool members data, excluding the user.
    """
    # Filter out the current user
    candidates = [
        member for member in members_data 
        if member.get('user_id') != str(user_id)
    ]
    
    # Limit to max candidates
    if len(candidates) > max_candidates:
        import random
        candidates = random.sample(candidates, max_candidates)
    
    return candidates


# -------------------------------
# Individual Service Operations  
# -------------------------------


def pick_candidates(db: Session, pool_id: UUID, user_id: UUID, limit: int = 10):
    """
    Return up to `limit` random members from the same pool,
    excluding the requesting user.
    """
    pool_members = list_pool_members(db, pool_id=pool_id)
    other_members = [m for m in pool_members if m.user_id != str(user_id)]
    if not other_members:
        return []
    return random.sample(other_members, min(limit, len(other_members)))


# -------------------------------
# Match generation
# -------------------------------


@router.post(
    "/users/{user_id}/generate-matches",
    response_model=List[MatchGet],
    status_code=status.HTTP_201_CREATED,
)
def generate_matches_for_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Find the user's pool and generate up to 10 random matches with other pool members.
    """
    try:
        user_membership = (
            db.query(models.PoolMember)
            .filter(models.PoolMember.user_id == str(user_id))
            .first()
        )
        if not user_membership:
            raise HTTPException(
                status_code=404,
                detail="User is not a member of any pool. Add user to a pool first.",
            )

        pool_id = user_membership.pool_id
        selected_members = pick_candidates(db, pool_id=UUID(pool_id), user_id=user_id)

        if not selected_members:
            return []

        created_matches: List[MatchGet] = []
        for member in selected_members:
            try:
                match = create_match(
                    db,
                    pool_id=UUID(pool_id),
                    user1_id=user_id,
                    user2_id=UUID(member.user_id),
                )
                created_matches.append(
                    MatchGet(
                        match_id=UUID(match.id),
                        pool_id=UUID(match.pool_id),
                        user1_id=UUID(match.user1_id),
                        user2_id=UUID(match.user2_id),
                        status=match.status,
                        created_at=match.created_at,
                        updated_at=match.updated_at,
                    )
                )
            except ValueError:
                continue

        return created_matches

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate matches: {str(e)}"
        )


# -------------------------------
# 🎯 COMPLETE COMPOSITE MICROSERVICE
# -------------------------------

@router.post(
    "/users/{user_id}/add-to-pool-and-generate-matches-complete",
    response_model=CompositeOperationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_to_pool_and_generate_matches_complete(
    user_id: UUID,
    request: Request,
    location: str = Query(..., description="Location for pool assignment"),
    max_matches: int = Query(default=10, ge=1, le=50, description="Maximum matches to generate"),
    db: Session = Depends(get_db)
) -> CompositeOperationResponse:
    """
    🎯 COMPLETE COMPOSITE MICROSERVICE: Uses ALL existing endpoints properly
    
    Workflow:
    1. GET /pools?location={location} - Find pools at location
    2. POST /pools (if needed) - Create pool if none exist
    3. POST /pools/{pool_id}/members - Add user to optimal pool
    4. GET /pools/{pool_id}/members - Get pool members for matching
    5. POST /matches (multiple) - Create matches with candidates
    
    Pool Selection Strategy: Chooses pool with lowest member count
    """
    services_called = []
    start_time = datetime.now()
    
    try:
        # 📍 STEP 1: Get pools by location
        pools_response = await call_internal_endpoint(
            request, "GET", "/pools", params={"location": location}
        )
        services_called.append({
            "service": "pools_service",
            "endpoint": f"/pools?location={location}",
            "method": "GET",
            "status": "success"
        })
        
        # 📍 STEP 2: Find or create optimal pool
        if not pools_response:
            # Create new pool
            new_pool_response = await call_internal_endpoint(
                request, "POST", "/pools",
                json={"name": f"Pool for {location}", "location": location}
            )
            # Convert to PoolRead model
            pool_model = PoolRead(**new_pool_response)
            pool_action = "created_new"
            selection_criteria = "created"
            member_count_before = 0
            
            services_called.append({
                "service": "pools_service",
                "endpoint": "/pools",
                "method": "POST", 
                "status": "success"
            })
        else:
            # Select optimal existing pool (lowest member count)
            pool_data = select_optimal_pool(pools_response)
            # Convert to PoolRead model  
            pool_model = PoolRead(**pool_data)
            pool_action = "found_existing"
            selection_criteria = "lowest_members"
            member_count_before = pool_data.get('member_count', 0)
        
        # 📍 STEP 3: Add user to selected pool
        member_response = await call_internal_endpoint(
            request, "POST", f"/pools/{pool_model.id}/members",
            json={"user_id": str(user_id)}
        )
        # Convert to PoolMemberRead model
        member_model = PoolMemberRead(**member_response)
        
        services_called.append({
            "service": "pools_service",
            "endpoint": f"/pools/{pool_model.id}/members",
            "method": "POST",
            "status": "success"
        })
        
        # 📍 STEP 4: Get all pool members for match generation
        members_response = await call_internal_endpoint(
            request, "GET", f"/pools/{pool_model.id}/members"
        )
        # Convert to PoolMemberRead models
        member_models = [PoolMemberRead(**member) for member in members_response]
        
        services_called.append({
            "service": "pools_service", 
            "endpoint": f"/pools/{pool_model.id}/members",
            "method": "GET",
            "status": "success"
        })
        
        # 📍 STEP 5: Generate matches with candidates
        candidates = pick_match_candidates_from_members(members_response, user_id, max_matches)
        candidate_models = [PoolMemberRead(**candidate) for candidate in candidates]
        
        created_matches = []
        failed_matches = []
        
        for candidate in candidates:
            try:
                match_response = await call_internal_endpoint(
                    request, "POST", "/matches",
                    json={
                        "pool_id": str(pool_model.id),
                        "user1_id": str(user_id),
                        "user2_id": candidate['user_id']
                    }
                )
                
                # Convert to MatchGet Pydantic model
                match_model = MatchGet(**match_response)
                created_matches.append(match_model)
                
                services_called.append({
                    "service": "matches_service",
                    "endpoint": "/matches",
                    "method": "POST",
                    "status": "success"
                })
            except Exception as e:
                failed_matches.append(f"Failed to create match with {candidate['user_id']}: {str(e)}")
                services_called.append({
                    "service": "matches_service", 
                    "endpoint": "/matches",
                    "method": "POST",
                    "status": "failed",
                    "error": str(e)
                })
        
        # 📊 COMPREHENSIVE RESPONSE
        return CompositeOperationResponse(
            message=f"User {user_id} added to pool and {len(created_matches)} matches generated",
            operation_type="complete_composite_microservice",
            timestamp=start_time,
            user_id=user_id,
            location=location,
            
            services_called=services_called,
            total_api_calls=len(services_called),
            
            pool_operation=PoolOperationInfo(
                action=pool_action,
                pool=pool_model,
                member_count_before=member_count_before,
                member_count_after=len(member_models),
                selection_criteria=selection_criteria
            ),
            
            member_operation=MemberOperationInfo(
                member=member_model,
                operation_status="success"
            ),
            
            match_operation=MatchOperationInfo(
                total_pool_members=len(member_models),
                eligible_candidates=len(candidate_models),
                matches_requested=len(candidate_models),
                matches_created=len(created_matches),
                matches_failed=len(failed_matches),
                candidates=[
                    MatchCandidateInfo(candidate=PoolMemberRead(**c)) 
                    for c in candidates
                ],
                created_matches=created_matches,
                failed_matches=failed_matches
            ),
            
            overall_status="success" if not failed_matches else "partial_success",
            next_actions=[
                "View your new matches in the app",
                f"Submit decisions on {len(created_matches)} pending matches", 
                "Generate additional matches if needed",
                f"Explore your pool '{pool_model.name}' with {len(member_models)} members"
            ]
        )
        
    except Exception as e:
        services_called.append({
            "service": "composite_orchestrator",
            "endpoint": "internal_error", 
            "method": "ERROR",
            "status": "failed",
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail=f"Complete composite operation failed: {str(e)}"
        )

async def call_internal_endpoint(request: Request, method: str, path: str, **kwargs) -> Dict[str, Any]:
    """Helper to make internal API calls to our own endpoints"""
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    async with httpx.AsyncClient() as client:
        if method.upper() == "POST":
            response = await client.post(f"{base_url}{path}", **kwargs)
        elif method.upper() == "GET":
            response = await client.get(f"{base_url}{path}", **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Internal service call to {path} failed: {response.text}"
            )
        
        return response.json()


@router.post(
    "/users/{user_id}/add-to-pool-and-generate-matches-composite",
    response_model=BasicCompositeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_to_pool_and_generate_matches_composite(
    user_id: UUID,
    request: Request,
    location: str = Query(..., description="Location for pool assignment"),
    db: Session = Depends(get_db)
) -> BasicCompositeResponse:
    """
    🎯 TRUE COMPOSITE MICROSERVICE: Orchestrates existing endpoints
    
    This is a pure orchestration service that calls:
    1. /pools/{pool_id}/members (pools service) 
    2. /users/{user_id}/generate-matches (match service)
    
    Benefits:
    - Reuses existing tested endpoints
    - Follows microservice orchestration pattern
    - Single transaction across multiple services
    - Consistent error handling and validation
    """
    try:
        # 📍 STEP 1: Find or create pool for location
        pools = list_pools(db, location=location)
        if not pools:
            pool = create_pool(db, name=f"Pool for {location}", location=location)
        else:
            pool = random.choice(pools)
        
        # 📍 STEP 2: Call Pools Service to add member via proper endpoint
        pool_member_response = await call_internal_endpoint(
            request, 
            "POST", 
            f"/pools/{pool.id}/members",
            json={"user_id": str(user_id)}
        )
        
        # 🎯 STEP 3: Call Match Generation Service via internal API
        try:
            matches_response = await call_internal_endpoint(
                request,
                "POST",
                f"/users/{user_id}/generate-matches"
            )
        except HTTPException as e:
            # If match generation fails, it's not critical - user is still in pool
            if e.status_code == 404:
                matches_response = []
                match_error = "No other users in pool to match with"
            else:
                matches_response = []
                match_error = f"Match generation failed: {e.detail}"
        else:
            match_error = None

        # 📊 COMPOSITE RESPONSE: Combine responses from both services
        return BasicCompositeResponse(
            message=f"Composite operation completed: User added to pool {pool.id}, {len(matches_response) if isinstance(matches_response, list) else 0} matches generated",
            operation_type="composite_microservice",
            services_called=[
                {
                    "service": "pools_service", 
                    "endpoint": f"/pools/{pool.id}/members",
                    "status": "success"
                },
                {
                    "service": "match_service", 
                    "endpoint": f"/users/{user_id}/generate-matches",
                    "status": "success" if match_error is None else "partial_failure",
                    "error": match_error
                }
            ],
            pool_operation=BasicPoolOperationInfo(
                pool_id=pool.id,
                pool_name=pool.name,
                location=location,
                member_result=pool_member_response
            ),
            match_operation=BasicMatchOperationInfo(
                status="success" if match_error is None else "partial_failure", 
                matches_count=len(matches_response) if isinstance(matches_response, list) else 0,
                matches=matches_response if isinstance(matches_response, list) else [],
                error=match_error
            ),
            user_id=user_id,
            location=location,
            next_steps=[
                "User can view generated matches",
                "User can submit decisions on matches", 
                "User can generate additional matches if needed"
            ]
        )

    except HTTPException as pool_error:
        # If pool addition fails, the whole composite operation fails
        raise HTTPException(
            status_code=pool_error.status_code,
            detail=f"Composite operation failed at pools service: {pool_error.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Composite microservice orchestration failed: {str(e)}"
        )



