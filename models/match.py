from __future__ import annotations

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


# =========================
# MatchIndividual
# =========================


class MatchIndividualBase(BaseModel):
    """Per-participant decision state within a match."""
    match_individual_id: UUID = Field(
        ...,
        description=" ID for this match_individual",
        json_schema_extra={"example": "22222222-2222-4222-8222-222222222222"},
    )
    id1: UUID = Field(
        ...,
        description="Person ID for this decision holder.",
        json_schema_extra={"example": "22222222-2222-4222-8222-222222222222"},
    )
    id2: UUID = Field(
        ...,
        description="Counterparty person ID.",
        json_schema_extra={"example": "33333333-3333-4333-8333-333333333333"},
    )
    accepted: Optional[bool] = Field(
        None,
        description="None = pending, True = accepted, False = rejected.",
        json_schema_extra={"example": None},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id1": "22222222-2222-4222-8222-222222222222",
                    "id2": "33333333-3333-4333-8333-333333333333",
                    "accepted": None,
                }
            ]
        }
    }


class MatchIndividualCreate(MatchIndividualBase):
    """Creation payload for a participant's match state."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id1": "22222222-2222-4222-8222-222222222222",
                    "id2": "33333333-3333-4333-8333-333333333333",
                    "accepted": None,
                }
            ]
        }
    }


class MatchIndividualUpdate(MatchIndividualBase):
    """Partial update for a participant decision record."""

    accepted: Optional[bool] = Field(
        None,
        description="None = pending, True = accepted, False = rejected.",
        json_schema_extra={"example": True},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"accepted": True},
            ]
        }
    }


class MatchIndividualRead(MatchIndividualBase):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this participant decision record was created (UTC).",
        json_schema_extra={"example": "2025-06-01T10:05:00Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this participant decision record was last updated (UTC).",
        json_schema_extra={"example": "2025-06-01T10:10:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id1": "22222222-2222-4222-8222-222222222222",
                    "id2": "33333333-3333-4333-8333-333333333333",
                    "accepted": None,
                    "created_at": "2025-06-01T10:05:00Z",
                    "updated_at": "2025-06-01T10:10:00Z",
                }
            ]
        }
    }


# =========================
# Match
# =========================


class MatchBase(BaseModel):
    match_id1: MatchIndividualRead = Field(
        ...,
        description="First participant match record.",
        json_schema_extra= {
            "examples": [
                {
                    "id1": "22222222-2222-4222-8222-222222222222",
                    "id2": "33333333-3333-4333-8333-333333333333",
                    "accepted": None,
                    "created_at": "2025-06-01T10:05:00Z",
                    "updated_at": "2025-06-01T10:10:00Z",
                }
            ]
        }
    )
    match_id2: MatchIndividualRead = Field(
        ...,
        description="Second participant match record.",
        json_schema_extra={
            "examples": [
                {
                    "id1": "22222222-2222-4222-8222-222222222222",
                    "id2": "33333333-3333-4333-8333-333333333333",
                    "accepted": None,
                    "created_at": "2025-06-01T10:05:00Z",
                    "updated_at": "2025-06-01T10:10:00Z",
                }
            ]
        },
    )
    accepted_by_both: bool = Field(
        False,
        description="True if both participants accepted.",
        json_schema_extra={"example": False},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "match_id1": {
                        "id1": "22222222-2222-4222-8222-222222222222",
                        "id2": "33333333-3333-4333-8333-333333333333",
                        "accepted": None,
                        "created_at": "2025-06-01T10:05:00Z",
                        "updated_at": "2025-06-01T10:05:00Z",
                    },
                    "match_id2": {
                        "id1": "33333333-3333-4333-8333-333333333333",
                        "id2": "22222222-2222-4222-8222-222222222222",
                        "accepted": None,
                        "created_at": "2025-06-01T10:05:10Z",
                        "updated_at": "2025-06-01T10:05:10Z",
                    },
                    "accepted_by_both": False,
                }
            ]
        }
    }


class MatchCreate(BaseModel):
    """Creation payload for a new match attempt (participants start pending)."""

    match_id1: MatchIndividualCreate = Field(
        ...,
        description="Initial decision state for participant 1.",
    )
    match_id2: MatchIndividualCreate = Field(
        ...,
        description="Initial decision state for participant 2.",
    )
    accepted_by_both: bool = Field(
        False,
        description="True if both participants accepted.",
        json_schema_extra={"example": False},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "match_id1": {
                        "id1": "22222222-2222-4222-8222-222222222222",
                        "id2": "33333333-3333-4333-8333-333333333333",
                        "accepted": None,
                    },
                    "match_id2": {
                        "id1": "33333333-3333-4333-8333-333333333333",
                        "id2": "22222222-2222-4222-8222-222222222222",
                        "accepted": None,
                    },
                    "accepted_by_both": False,
                }
            ]
        }
    }


class MatchUpdate(BaseModel):
    """Update payload for modifying an existing match's participant decisions."""

    match_id1: Optional[MatchIndividualUpdate] = Field(
        None,
        description="Optional updates to participant 1's decision state.",
    )
    match_id2: Optional[MatchIndividualUpdate] = Field(
        None,
        description="Optional updates to participant 2's decision state.",
    )
    accepted_by_both: Optional[bool] = Field(
        None,
        description="Override for accepted_by_both status (usually auto-calculated).",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "match_id1": {
                        "id1": "22222222-2222-4222-8222-222222222222",
                        "id2": "33333333-3333-4333-8333-333333333333",
                        "accepted": True,
                        "created_at": "2025-06-01T10:05:00Z",
                        "updated_at": "2025-06-01T10:05:00Z",
                    },
                },
                {
                    "match_id1": {
                        "id1": "22222222-2222-4222-8222-222222222222",
                        "id2": "33333333-3333-4333-8333-333333333333",
                        "accepted": True,
                        "created_at": "2025-06-01T10:05:00Z",
                        "updated_at": "2025-06-01T10:05:00Z",
                    },
                    "accepted_by_both": True,
                },
            ]
        }
    }



class MatchRead(MatchBase):
    match_id: UUID = Field(
        default_factory=uuid4,
        description="Persistent Match ID (server-generated).",
        json_schema_extra={"example": "44444444-4444-4444-8444-444444444444"},
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the match was created (UTC).",
        json_schema_extra={"example": "2025-06-01T10:05:00Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the match status last changed (UTC).",
        json_schema_extra={"example": "2025-06-01T10:20:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "match_id": "44444444-4444-4444-8444-444444444444",
                    "match_id1": {
                        "id1": "22222222-2222-4222-8222-222222222222",
                        "id2": "33333333-3333-4333-8333-333333333333",
                        "accepted": True,
                        "created_at": "2025-06-01T10:05:00Z",
                        "updated_at": "2025-06-01T10:10:00Z",
                    },
                    "match_id2": {
                        "id1": "33333333-3333-4333-8333-333333333333",
                        "id2": "22222222-2222-4222-8222-222222222222",
                        "accepted": True,
                        "created_at": "2025-06-01T10:06:00Z",
                        "updated_at": "2025-06-01T10:11:00Z",
                    },
                    "accepted_by_both": True,
                    "created_at": "2025-06-01T10:05:00Z",
                    "updated_at": "2025-06-01T10:20:00Z",
                }
            ]
        }
    }
