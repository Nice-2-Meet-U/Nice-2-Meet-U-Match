from __future__ import annotations

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


# =========================
# Availability
# =========================


class AvailabilityBase(BaseModel):
    availability_id: UUID = Field(
        ...,
        description="Unique identifier of the person this availability",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    person_id: UUID = Field(
        ...,
        description="Unique identifier of the person this availability belongs to.",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    location: str = Field(
        ...,
        description="Geographical or logical location used for matching.",
        json_schema_extra={"example": "NYC"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "availability_id": "99999999-9999-4999-8999-999999999999",
                    "person_id": "99999999-9999-4999-8999-999999999999",
                    "location": "NYC",
                }
            ]
        }
    }


class AvailabilityCreate(AvailabilityBase):
    """Creation payload for adding someone to the availability pool."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "availability_id": "99999999-9999-4999-8999-999999999999",
                    "person_id": "99999999-9999-4999-8999-999999999999",
                    "location": "SF",
                }
            ]
        }
    }


class AvailabilityUpdate(AvailabilityBase):
    """Partial update for an availability; provide only fields to change."""

    person_id: Optional[UUID] = Field(
        None,
        description="Person ID associated with this availability (optional on update).",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    location: Optional[str] = Field(None, json_schema_extra={"example": "NYC"})

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"person_id": "99999999-9999-4999-8999-999999999999", "location": "SF"},
                {"location": "2025-06-02T12:00:00Z"},
            ]
        }
    }


class AvailabilityRead(AvailabilityBase):
    """Read representation; mirrors base with server-side identifiers and timestamps."""


    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-06-01T11:00:00Z"},
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC).",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "availabilityid": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                    "person_id": "99999999-9999-4999-8999-999999999999",
                    "location": "NYC",
                    "created_at": "2025-06-01T10:00:00Z",
                    "updated_at": "2025-06-01T11:00:00Z",
                }
            ]
        }
    }


# =========================
# Availability Pool (container)
# =========================
class AvailabilityPoolBase(BaseModel):
    """Current pool of active availabilities (simple container)."""
    availability_pool_id: UUID = Field(
        ...,
        description="Unique identifier of availability pool",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    location: str = Field(
        ...,
        description="Name or code of the location for this availability pool.",
        json_schema_extra={"example": "NYC"},
    )

    availabilities: List[AvailabilityRead] = Field(
        default_factory=list,
        description="All currently active availabilities in the given location.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "location": "NYC",
                    "availabilities": [
                        {
                            "id": "11111111-1111-4111-8111-111111111111",
                            "person_id": "99999999-9999-4999-8999-999999999999",
                            "location": "NYC",
                            "time_added": "2025-06-01T10:00:00Z",
                            "updated_at": "2025-06-01T11:00:00Z",
                        }
                    ],
                }
            ]
        }
    }


class AvailabilityPoolCreate(AvailabilityPoolBase):
    """Creation payload for initializing a new availability pool."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "location": "SF",
                    "availabilities": [],
                }
            ]
        }
    }


class AvailabilityPoolUpdate(BaseModel):
    """Partial update for an availability pool; provide only fields to change."""

    location: Optional[str] = Field(None, json_schema_extra={"example": "LA"})
    availabilities: Optional[List[AvailabilityRead]] = Field(
        None,
        description="Updated list of availabilities (optional on update).",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"location": "LA"},
                {
                    "availabilities": [
                        {
                            "id": "22222222-2222-4222-8222-222222222222",
                            "person_id": "88888888-8888-4888-8888-888888888888",
                            "location": "NYC",
                            "time_added": "2025-06-01T14:00:00Z",
                            "updated_at": "2025-06-01T14:00:00Z",
                        }
                    ]
                },
            ]
        }
    }


class AvailabilityPoolRead(AvailabilityPoolBase):
    """Read representation of an availability pool with server-side metadata."""

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this pool was created (UTC).",
        json_schema_extra={"example": "2025-06-01T08:00:00Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-06-01T11:00:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "availability_pool_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                    "location": "NYC",
                    "availabilities": [
                        {
                            "id": "11111111-1111-4111-8111-111111111111",
                            "person_id": "99999999-9999-4999-8999-999999999999",
                            "location": "NYC",
                            "time_added": "2025-06-01T10:00:00Z",
                            "updated_at": "2025-06-01T11:00:00Z",
                        }
                    ],
                    "created_at": "2025-06-01T08:00:00Z",
                    "updated_at": "2025-06-01T11:00:00Z",
                }
            ]
        }
    }
