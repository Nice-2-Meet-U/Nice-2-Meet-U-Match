"""User composite schemas that incorporate pool, match, and decision schemas."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from pool.pool_schemas import PoolRead, PoolMemberRead
from match.match_schemas import MatchGet
from decision.decision_schemas import DecisionGet


# =========================
# User Add to Pool Schemas
# =========================


class UserAddToPoolRequest(BaseModel):
    """Request to add a user to a pool by location."""

    location: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Location to add user to",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"location": "New York, NY"},
                {"location": "San Francisco, CA"},
            ]
        }
    )


class UserAddToPoolResponse(BaseModel):
    """Response when adding a user to a pool."""

    message: str = Field(..., description="Success message")
    pool: PoolRead = Field(..., description="Pool the user was added to")
    member: PoolMemberRead = Field(..., description="Pool membership details")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "message": "User added to pool at New York, NY",
                    "pool": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Pool for New York, NY",
                        "location": "New York, NY",
                        "member_count": 15,
                        "created_at": "2025-01-15T10:30:00Z",
                    },
                    "member": {
                        "user_id": "987e6543-e21b-12d3-a456-426614174999",
                        "pool_id": "123e4567-e89b-12d3-a456-426614174000",
                        "joined_at": "2025-01-15T14:45:00Z",
                    },
                }
            ]
        },
    )


# =========================
# User Generate Matches Schemas
# =========================


class UserGenerateMatchesRequest(BaseModel):
    """Request to generate matches for a user."""

    max_matches: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of matches to generate",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"max_matches": 10},
                {"max_matches": 5},
            ]
        }
    )


class MatchSummary(BaseModel):
    """Composite match summary with decisions from both users."""

    match: MatchGet = Field(..., description="Full match details")
    user1_decision: Optional[DecisionGet] = Field(
        None, description="First user's decision, if made"
    )
    user2_decision: Optional[DecisionGet] = Field(
        None, description="Second user's decision, if made"
    )
    both_decided: bool = Field(
        default=False, description="Whether both users have made their decision"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "match": {
                        "match_id": "44444444-4444-4444-8444-444444444444",
                        "pool_id": "11111111-1111-4111-8111-111111111111",
                        "user1_id": "22222222-2222-4222-8222-222222222222",
                        "user2_id": "33333333-3333-4333-8333-333333333333",
                        "status": "waiting",
                        "created_at": "2025-06-01T10:05:00Z",
                        "updated_at": "2025-06-01T10:20:00Z",
                    },
                    "user1_decision": {
                        "match_id": "44444444-4444-4444-8444-444444444444",
                        "user_id": "22222222-2222-4222-8222-222222222222",
                        "decision": "accept",
                        "decided_at": "2025-06-01T10:10:00Z",
                    },
                    "user2_decision": None,
                    "both_decided": False,
                }
            ]
        },
    )


class UserGenerateMatchesResponse(BaseModel):
    """Response when generating matches for a user."""

    message: str = Field(..., description="Success message")
    pool_id: str = Field(..., description="Pool ID where matches were generated")
    matches_created: int = Field(..., ge=0, description="Number of matches created")
    matches: list[MatchSummary] = Field(
        default_factory=list, description="List of created matches"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "Generated 3 matches",
                    "pool_id": "123e4567-e89b-12d3-a456-426614174000",
                    "matches_created": 3,
                    "matches": [
                        {
                            "match_id": "44444444-4444-4444-8444-444444444444",
                            "user1_id": "22222222-2222-4222-8222-222222222222",
                            "user2_id": "33333333-3333-4333-8333-333333333333",
                            "status": "waiting",
                        }
                    ],
                }
            ]
        }
    )


# =========================
# Composite User Profile Schemas
# =========================


class UserPoolMembership(BaseModel):
    """User's pool membership with full pool details."""

    pool: PoolRead = Field(..., description="Full pool details")
    membership: PoolMemberRead = Field(..., description="Membership details")

    model_config = ConfigDict(from_attributes=True)


class UserMatchWithDecision(BaseModel):
    """Match with user's decision if it exists."""

    match: MatchGet = Field(..., description="Full match details")
    user_decision: Optional[DecisionGet] = Field(
        None, description="User's decision on this match, if any"
    )
    other_user_decision: Optional[DecisionGet] = Field(
        None, description="Other participant's decision, if any"
    )

    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    """Complete user profile with pools, matches, and decisions."""

    user_id: UUID = Field(..., description="User identifier")
    pools: list[UserPoolMembership] = Field(
        default_factory=list, description="Pools user is a member of"
    )
    active_matches: list[UserMatchWithDecision] = Field(
        default_factory=list, description="User's active matches with decisions"
    )
    match_statistics: UserMatchStatistics = Field(
        ..., description="User's match statistics"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "987e6543-e21b-12d3-a456-426614174999",
                    "pools": [],
                    "active_matches": [],
                    "match_statistics": {
                        "total_matches": 10,
                        "accepted_matches": 3,
                        "rejected_matches": 2,
                        "waiting_matches": 5,
                        "mutual_accepts": 2,
                    },
                }
            ]
        },
    )


class UserMatchStatistics(BaseModel):
    """Statistics about user's matches."""

    total_matches: int = Field(default=0, ge=0, description="Total number of matches")
    accepted_matches: int = Field(
        default=0, ge=0, description="Matches user accepted"
    )
    rejected_matches: int = Field(
        default=0, ge=0, description="Matches user rejected"
    )
    waiting_matches: int = Field(
        default=0, ge=0, description="Matches awaiting user's decision"
    )
    mutual_accepts: int = Field(
        default=0, ge=0, description="Matches accepted by both users"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_matches": 10,
                    "accepted_matches": 3,
                    "rejected_matches": 2,
                    "waiting_matches": 5,
                    "mutual_accepts": 2,
                }
            ]
        }
    )


# =========================
# Bulk Operations Schemas
# =========================


class BulkAddUsersToPoolRequest(BaseModel):
    """Request to add multiple users to a pool."""

    user_ids: list[UUID] = Field(
        ..., min_length=1, max_length=100, description="List of user IDs to add"
    )
    location: str = Field(
        ..., min_length=1, max_length=200, description="Location for the pool"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_ids": [
                        "22222222-2222-4222-8222-222222222222",
                        "33333333-3333-4333-8333-333333333333",
                    ],
                    "location": "New York, NY",
                }
            ]
        }
    )


class BulkAddUsersToPoolResponse(BaseModel):
    """Response for bulk adding users to pool."""

    message: str = Field(..., description="Success message")
    pool: PoolRead = Field(..., description="Pool users were added to")
    added_count: int = Field(..., ge=0, description="Number of users successfully added")
    failed_count: int = Field(default=0, ge=0, description="Number of users that failed")
    members: list[PoolMemberRead] = Field(
        default_factory=list, description="List of created memberships"
    )

    model_config = ConfigDict(from_attributes=True)
