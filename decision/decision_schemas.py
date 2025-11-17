from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from frameworks.hateoas import Link


class DecisionValue(str, Enum):
    accept = "accept"
    reject = "reject"


# =========================
# Decision (Base / Post / Put / Patch / Get)
# =========================


class DecisionBase(BaseModel):
    """A single participant's decision for a match."""

    match_id: UUID = Field(
        ...,
        description="The match this decision belongs to.",
        json_schema_extra={"example": "44444444-4444-4444-8444-444444444444"},
    )
    user_id: UUID = Field(
        ...,
        description="The user making the decision.",
        json_schema_extra={"example": "22222222-2222-4222-8222-222222222222"},
    )
    decision: DecisionValue = Field(
        ...,
        description="'accept' or 'reject'.",
        json_schema_extra={"example": "accept"},
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "match_id": "44444444-4444-4444-8444-444444444444",
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "decision": "accept",
                }
            ]
        }
    )


class DecisionPost(DecisionBase):
    """Create/submit a decision (server upserts + recomputes match status)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "match_id": "44444444-4444-4444-8444-444444444444",
                    "user_id": "33333333-3333-4333-8333-333333333333",
                    "decision": "reject",
                }
            ]
        }
    )


class DecisionPut(DecisionBase):
    """Full replace of a decision (idempotent upsert semantics)."""

    pass


class DecisionPatch(BaseModel):
    """Partial update of a decision."""

    match_id: Optional[UUID] = Field(
        None,
        description="If moving the decision to another match (rare).",
        json_schema_extra={"example": "55555555-5555-4555-8555-555555555555"},
    )
    user_id: Optional[UUID] = Field(
        None,
        description="Change the decider (admin only).",
        json_schema_extra={"example": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"},
    )
    decision: Optional[DecisionValue] = Field(
        None,
        description="Update to 'accept' or 'reject'.",
        json_schema_extra={"example": "accept"},
    )

    model_config = ConfigDict(json_schema_extra={"examples": [{"decision": "accept"}]})


class DecisionGet(DecisionBase):
    """Server representation of a decision."""

    decided_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the decision was recorded (UTC).",
        json_schema_extra={"example": "2025-06-01T10:10:00Z"},
    )
    links: Dict[str, Link] = Field(default_factory=dict, alias="_links", description="HATEOAS links")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "match_id": "44444444-4444-4444-8444-444444444444",
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "decision": "accept",
                    "decided_at": "2025-06-01T10:10:00Z",
                }
            ]
        },
    )
