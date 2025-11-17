from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from frameworks.hateoas import Link


# ---- Base (shared fields that describe a pool) ----
class PoolBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Summer League", "location": "New York, NY"}
            ]
        },
    )

    name: str = Field(..., min_length=1, max_length=100, description="Name of the pool")
    location: str = Field(..., max_length=200, description="Physical location of the pool")


# ---- POST (create) ----
class PoolCreate(PoolBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Winter Championship", "location": "Boston, MA"}
            ]
        },
    )


# ---- PUT (full update/replace). You usually keep same fields as base. ----
class PoolPut(PoolBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"name": "Updated Pool Name", "location": "San Francisco, CA"}]
        },
    )


# ---- PATCH (partial update). All fields optional. ----
class PoolPatch(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Renamed Pool"},
                {"location": "Los Angeles, CA"},
                {"name": "Complete Update", "location": "Chicago, IL"},
            ]
        },
    )

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Name of the pool"
    )
    location: Optional[str] = Field(
        None, max_length=200, description="Physical or virtual location of the pool"
    )



# ---- GET (read) ----
class PoolRead(PoolBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Summer League",
                    "location": "New York, NY",
                    "member_count": 15,
                    "created_at": "2025-01-15T10:30:00Z",
                },
            ]
        },
    )

    id: UUID = Field(..., description="Unique identifier for the pool")
    member_count: int = Field(..., ge=0, description="Number of members in the pool")
    created_at: datetime = Field(..., description="Timestamp when the pool was created")
    links: Dict[str, Link] = Field(default_factory=dict, alias="_links", description="HATEOAS links")








# ---- Pool Member models ----
class PoolMemberBase(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        json_schema_extra={
            "examples": [{"user_id": "987e6543-e21b-12d3-a456-426614174999"}]
        },
    )

    user_id: UUID = Field(..., description="Unique identifier of the user")


class PoolMemberCreate(PoolMemberBase):
    model_config = ConfigDict(
        validate_assignment=True,
        json_schema_extra={
            "examples": [{"user_id": "abc12345-e89b-12d3-a456-426614174111"}]
        },
    )


class PoolMemberRead(PoolMemberBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "987e6543-e21b-12d3-a456-426614174999",
                    "pool_id": "123e4567-e89b-12d3-a456-426614174000",
                    "joined_at": "2025-01-15T14:45:00Z",
                }
            ]
        },
    )

    pool_id: UUID = Field(..., description="Unique identifier of the pool")
    joined_at: datetime = Field(
        ..., description="Timestamp when the member joined the pool"
    )
    links: Dict[str, Link] = Field(default_factory=dict, alias="_links", description="HATEOAS links")
