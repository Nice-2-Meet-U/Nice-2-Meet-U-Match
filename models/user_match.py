# models/user_match.py
from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Import from other model files for proper typing
from models.pool import PoolMemberRead
from models.match import MatchGet
from models.decisions import DecisionGet


# =========================
# User Pool Models
# =========================


class UserPoolBase(BaseModel):
    """Base model for user pool operations."""

    location: str = Field(..., description="The location where the pool is located")
    coord_x: Optional[float] = Field(None, description="X coordinate (latitude)")
    coord_y: Optional[float] = Field(None, description="Y coordinate (longitude)")


class UserPoolCreate(UserPoolBase):
    """Schema for adding a user to a pool (POST)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "location": "New York",
                    "coord_x": 40.7128,
                    "coord_y": -74.0060
                }
            ]
        }
    )


class UserPoolRead(BaseModel):
    """Schema for detailed user pool information (GET)."""

    pool_id: UUID = Field(..., description="ID of the pool")
    pool_name: str = Field(..., description="Name of the pool")
    location: Optional[str] = Field(None, description="Pool location")
    member_count: int = Field(..., description="Number of members in the pool")
    joined_at: datetime = Field(..., description="When the user joined")
    user_id: UUID = Field(..., description="User ID")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "pool_id": "11111111-1111-4111-8111-111111111111",
                    "pool_name": "NYC Dating Pool",
                    "location": "New York",
                    "member_count": 15,
                    "joined_at": "2025-06-01T10:05:00Z",
                    "user_id": "22222222-2222-4222-8222-222222222222"
                }
            ]
        }
    )


class UserPoolUpdate(BaseModel):
    """Schema for updating user pool coordinates (PATCH)."""

    coord_x: Optional[float] = Field(None, description="Updated X coordinate (latitude)")
    coord_y: Optional[float] = Field(None, description="Updated Y coordinate (longitude)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "coord_x": 40.7580,
                    "coord_y": -73.9855
                }
            ]
        }
    )


class UserPoolDelete(BaseModel):
    """Response model for removing a user from their pool (DELETE)."""

    message: str = Field(..., description="Confirmation message")
    user_id: UUID = Field(..., description="ID of the removed user")
    pool_id: UUID = Field(..., description="ID of the pool")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "User removed from pool successfully",
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "pool_id": "11111111-1111-4111-8111-111111111111"
                }
            ]
        }
    )


class UserPoolResponse(BaseModel):
    """Schema for user pool information response after the post operation."""

    user_id: UUID = Field(..., description="User ID")
    pool_id: UUID = Field(..., description="Pool ID")
    location: Optional[str] = Field(None, description="Pool location")
    member: PoolMemberRead = Field(..., description="Member details from pool service")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "pool_id": "11111111-1111-4111-8111-111111111111",
                    "location": "New York",
                    "member": {
                        "user_id": "22222222-2222-4222-8222-222222222222",
                        "pool_id": "11111111-1111-4111-8111-111111111111",
                        "coord_x": 40.7128,
                        "coord_y": -74.0060,
                        "joined_at": "2025-06-01T10:05:00Z"
                    }
                }
            ]
        }
    )


# =========================
# User Matches Models
# =========================


class UserMatchesBase(BaseModel):
    """Base model for user matches."""

    user_id: UUID = Field(..., description="User ID")
    matches_count: int = Field(..., description="Number of matches")
    matches: List[MatchGet] = Field(default_factory=list, description="List of match objects")


class UserMatchesRead(UserMatchesBase):
    """Schema for user matches response (GET)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "matches_count": 2,
                    "matches": [
                        {
                            "match_id": "44444444-4444-4444-8444-444444444444",
                            "pool_id": "11111111-1111-4111-8111-111111111111",
                            "user1_id": "22222222-2222-4222-8222-222222222222",
                            "user2_id": "33333333-3333-4333-8333-333333333333",
                            "status": "waiting",
                            "created_at": "2025-06-01T10:05:00Z",
                            "updated_at": "2025-06-01T10:20:00Z"
                        }
                    ]
                }
            ]
        }
    )



class GenerateMatchesBase(BaseModel):
    """Base model for match generation."""

    message: str = Field(..., description="Status message")
    pool_id: UUID = Field(..., description="Pool ID where matches were generated")
    matches_created: int = Field(..., description="Number of matches created")
    matches: List[MatchGet] = Field(default_factory=list, description="List of created match objects")


class GenerateMatchesResponse(GenerateMatchesBase):
    """Schema for generate matches response (POST)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "message": "Generated 3 matches for user 22222222-2222-4222-8222-222222222222",
                    "pool_id": "11111111-1111-4111-8111-111111111111",
                    "matches_created": 3,
                    "matches": [
                        {
                            "match_id": "44444444-4444-4444-8444-444444444444",
                            "pool_id": "11111111-1111-4111-8111-111111111111",
                            "user1_id": "22222222-2222-4222-8222-222222222222",
                            "user2_id": "33333333-3333-4333-8333-333333333333",
                            "status": "waiting",
                            "created_at": "2025-06-01T10:05:00Z",
                            "updated_at": "2025-06-01T10:20:00Z"
                        }
                    ]
                }
            ]
        }
    )


# =========================
# User Pool Members Models
# =========================


class UserPoolMembersBase(BaseModel):
    """Base model for user pool members."""

    user_id: UUID = Field(..., description="User ID")
    members_count: int = Field(..., description="Number of pool members")
    members: List[PoolMemberRead] = Field(default_factory=list, description="List of pool member objects")


class UserPoolMembersRead(UserPoolMembersBase):
    """Schema for user pool members response (GET)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "members_count": 3,
                    "members": [
                        {
                            "user_id": "22222222-2222-4222-8222-222222222222",
                            "pool_id": "11111111-1111-4111-8111-111111111111",
                            "coord_x": 40.7128,
                            "coord_y": -74.0060,
                            "joined_at": "2025-06-01T10:05:00Z"
                        },
                        {
                            "user_id": "33333333-3333-4333-8333-333333333333",
                            "pool_id": "11111111-1111-4111-8111-111111111111",
                            "coord_x": 40.7580,
                            "coord_y": -73.9855,
                            "joined_at": "2025-06-01T09:30:00Z"
                        }
                    ]
                }
            ]
        }
    )



# =========================
# User Decisions Models
# =========================


class UserDecisionsBase(BaseModel):
    """Base model for user decisions."""

    user_id: UUID = Field(..., description="User ID")
    decisions_count: int = Field(..., description="Number of decisions made")
    decisions: List[DecisionGet] = Field(default_factory=list, description="List of decision objects")


class UserDecisionsRead(UserDecisionsBase):
    """Schema for user decisions response (GET)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "decisions_count": 2,
                    "decisions": [
                        {
                            "match_id": "44444444-4444-4444-8444-444444444444",
                            "user_id": "22222222-2222-4222-8222-222222222222",
                            "decision": "accept",
                            "decided_at": "2025-06-01T10:10:00Z"
                        },
                        {
                            "match_id": "55555555-5555-4555-8555-555555555555",
                            "user_id": "22222222-2222-4222-8222-222222222222",
                            "decision": "reject",
                            "decided_at": "2025-06-01T10:15:00Z"
                        }
                    ]
                }
            ]
        }
    )



class UserDecisionBase(BaseModel):
    """Base model for a single decision."""

    decision: str = Field(..., description="'accept' or 'reject'")


class UserDecisionCreate(UserDecisionBase):
    """Request model for submitting a decision via user_match composite (POST)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"decision": "accept"},
                {"decision": "reject"}
            ]
        }
    )



class UserDecisionResponse(BaseModel):
    """Response model for user decision submission via composite endpoint."""
    
    match_id: UUID = Field(..., description="ID of the match")
    user_id: UUID = Field(..., description="ID of the user who made the decision")
    decision: str = Field(..., description="The decision made: 'accept' or 'reject'")
    decided_at: str = Field(..., description="Timestamp when decision was made")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "match_id": "44444444-4444-4444-8444-444444444444",
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "decision": "accept",
                    "decided_at": "2025-06-01T10:10:00Z"
                }
            ]
        }
    )
