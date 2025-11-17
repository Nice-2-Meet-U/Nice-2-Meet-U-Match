"""
Composite operation response models for microservice orchestration.
"""

from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from .pool import PoolRead, PoolMemberRead
from .match import MatchGet


class PoolOperationInfo(BaseModel):
    """Information about the pool operation"""
    action: str  # "found_existing" or "created_new"
    pool: PoolRead  # Use the actual PoolRead model
    member_count_before: int
    member_count_after: int
    selection_criteria: str  # "lowest_members" or "created"


class MemberOperationInfo(BaseModel):
    """Information about adding the member"""
    member: PoolMemberRead  # Use the actual PoolMemberRead model
    operation_status: str


class MatchCandidateInfo(BaseModel):
    """Information about a match candidate"""
    candidate: PoolMemberRead  # Use the actual PoolMemberRead model


class MatchOperationInfo(BaseModel):
    """Information about match generation"""
    total_pool_members: int
    eligible_candidates: int
    matches_requested: int
    matches_created: int
    matches_failed: int
    candidates: List[MatchCandidateInfo]
    created_matches: List[MatchGet]
    failed_matches: List[str]


class CompositeOperationResponse(BaseModel):
    """Complete response for add-to-pool-and-generate-matches operation"""
    message: str
    operation_type: str
    timestamp: datetime
    user_id: UUID
    location: str
    
    # Service call tracking
    services_called: List[Dict[str, Any]]
    total_api_calls: int
    
    # Detailed operation results
    pool_operation: PoolOperationInfo
    member_operation: MemberOperationInfo
    match_operation: MatchOperationInfo
    
    # Summary
    overall_status: str
    next_actions: List[str]
    
    model_config = ConfigDict(from_attributes=True)


# Simpler response models for basic composite operations
class BasicPoolOperationInfo(BaseModel):
    """Basic information about pool operation"""
    pool_id: UUID
    pool_name: str
    location: str
    member_result: Dict[str, Any]


class BasicMatchOperationInfo(BaseModel):
    """Basic information about match operation"""
    status: str
    matches_count: int
    matches: List[Dict[str, Any]]
    error: str | None = None


class BasicCompositeResponse(BaseModel):
    """Basic composite response for simpler operations"""
    message: str
    operation_type: str
    services_called: List[Dict[str, Any]]
    pool_operation: BasicPoolOperationInfo
    match_operation: BasicMatchOperationInfo
    user_id: UUID
    location: str
    next_steps: List[str]
    
    model_config = ConfigDict(from_attributes=True)


# Simple response model for basic add to pool operation
class SimpleAddToPoolResponse(BaseModel):
    """Simple response for basic add user to pool operation"""
    message: str
    pool_id: UUID
    pool_name: str
    location: str
    member_info: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)