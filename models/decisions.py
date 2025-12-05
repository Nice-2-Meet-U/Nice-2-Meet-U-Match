from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


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
    """Partial update of a decision (typically just changing the decision value)."""

    decision: DecisionValue = Field(
        ...,
        description="Update to 'accept' or 'reject'.",
        json_schema_extra={"example": "accept"},
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"decision": "accept"},
                {"decision": "reject"}
            ]
        }
    )


class DecisionGet(DecisionBase):
    """Server representation of a decision."""

    decided_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the decision was recorded (UTC).",
        json_schema_extra={"example": "2025-06-01T10:10:00Z"},
    )

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
