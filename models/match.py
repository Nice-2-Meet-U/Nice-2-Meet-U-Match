from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class MatchStatus(str, Enum):
    waiting = "waiting"
    accepted = "accepted"
    rejected = "rejected"


# =========================
# Match (Base / Post / Put / Patch / Get)
# =========================


class MatchBase(BaseModel):
    """Core fields for a pairwise match; status is server-driven."""

    pool_id: UUID = Field(
        ...,
        description="Pool this match belongs to.",
        json_schema_extra={"example": "11111111-1111-4111-8111-111111111111"},
    )
    user1_id: UUID = Field(
        ...,
        description="First participant user ID.",
        json_schema_extra={"example": "22222222-2222-4222-8222-222222222222"},
    )
    user2_id: UUID = Field(
        ...,
        description="Second participant user ID.",
        json_schema_extra={"example": "33333333-3333-4333-8333-333333333333"},
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "pool_id": "11111111-1111-4111-8111-111111111111",
                    "user1_id": "22222222-2222-4222-8222-222222222222",
                    "user2_id": "33333333-3333-4333-8333-333333333333",
                }
            ]
        }
    )


class MatchPost(MatchBase):
    """Creation payload for a new match (server sets status='waiting')."""

    # If match IDs are server-generated, you don't send an id here.
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "pool_id": "11111111-1111-4111-8111-111111111111",
                    "user1_id": "22222222-2222-4222-8222-222222222222",
                    "user2_id": "33333333-3333-4333-8333-333333333333",
                }
            ]
        }
    )


class MatchPut(MatchBase):
    """Full replace (rare). Status remains server-driven."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "pool_id": "11111111-1111-4111-8111-111111111111",
                    "user1_id": "22222222-2222-4222-8222-222222222222",
                    "user2_id": "33333333-3333-4333-8333-333333333333",
                }
            ]
        }
    )


class MatchPatch(BaseModel):
    """Partial update; status is optional and typically admin-only."""

    pool_id: Optional[UUID] = Field(
        None,
        description="Change pool (rare).",
        json_schema_extra={"example": "11111111-1111-4111-8111-111111111111"},
    )
    user1_id: Optional[UUID] = Field(
        None,
        description="Replace first participant.",
        json_schema_extra={"example": "22222222-2222-4222-8222-222222222222"},
    )
    user2_id: Optional[UUID] = Field(
        None,
        description="Replace second participant.",
        json_schema_extra={"example": "33333333-3333-4333-8333-333333333333"},
    )
    status: Optional[MatchStatus] = Field(
        None,
        description="Admin override of status (normally computed from decisions).",
        json_schema_extra={"example": "accepted"},
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "rejected"},
                {"user2_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"},
            ]
        }
    )


class MatchGet(MatchBase):
    """Server representation of a match."""

    match_id: UUID = Field(
        default_factory=uuid4,
        description="Persistent match UUID (server-generated).",
        json_schema_extra={"example": "44444444-4444-4444-8444-444444444444"},
    )
    status: MatchStatus = Field(
        default=MatchStatus.waiting,
        description="Waiting until decisions resolve to accepted/rejected.",
        json_schema_extra={"example": "waiting"},
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the match was created (UTC).",
        json_schema_extra={"example": "2025-06-01T10:05:00Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the match last changed (UTC).",
        json_schema_extra={"example": "2025-06-01T10:20:00Z"},
    )
    # Optional: include rollup if you expose it
    # accepted_by_both: bool = Field(False, description="True if both accepted.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "match_id": "44444444-4444-4444-8444-444444444444",
                    "pool_id": "11111111-1111-4111-8111-111111111111",
                    "user1_id": "22222222-2222-4222-8222-222222222222",
                    "user2_id": "33333333-3333-4333-8333-333333333333",
                    "status": "waiting",
                    "created_at": "2025-06-01T10:05:00Z",
                    "updated_at": "2025-06-01T10:20:00Z",
                }
            ]
        },
    )


class MatchCleanupDetail(BaseModel):
    """Details about a single deleted match."""
    
    match_id: UUID = Field(..., description="ID of the deleted match")
    status: MatchStatus = Field(..., description="Status of the match before deletion")
    decisions_deleted: int = Field(..., description="Number of decisions deleted with this match")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "match_id": "44444444-4444-4444-8444-444444444444",
                    "status": "waiting",
                    "decisions_deleted": 2
                }
            ]
        }
    )


class CleanupResponse(BaseModel):
    """Response model for match cleanup operations."""
    
    pool_id: UUID = Field(..., description="Pool from which matches were cleaned")
    user_id: UUID = Field(..., description="User whose matches were cleaned")
    matches_deleted: int = Field(..., description="Total number of matches deleted")
    decisions_deleted: int = Field(..., description="Total number of decisions deleted")
    matches: list[MatchCleanupDetail] = Field(default_factory=list, description="Details of deleted matches")
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "pool_id": "11111111-1111-4111-8111-111111111111",
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "matches_deleted": 3,
                    "decisions_deleted": 5,
                    "matches": [
                        {
                            "match_id": "44444444-4444-4444-8444-444444444444",
                            "status": "waiting",
                            "decisions_deleted": 2
                        }
                    ]
                }
            ]
        }
    )
