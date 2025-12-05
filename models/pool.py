from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ---- Base (shared fields that describe a pool) ----
class PoolBase(BaseModel):
    """Core fields for a pool."""
    
    name: str = Field(..., description="Name of the pool")
    location: Optional[str] = Field(None, description="Location where the pool is located")


# ---- POST (create) ----
class PoolCreate(PoolBase):
    """Request model for creating a new pool."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "NYC Dating Pool",
                    "location": "New York"
                }
            ]
        }
    )


# ---- PUT (full update/replace). You usually keep same fields as base. ----
class PoolPut(PoolBase):
    """Request model for full pool replacement."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "NYC Dating Pool",
                    "location": "New York"
                }
            ]
        }
    )


# ---- PATCH (partial update). All fields optional. ----
class PoolPatch(BaseModel):
    """Request model for partial pool update."""
    
    name: Optional[str] = Field(None, description="Updated pool name")
    location: Optional[str] = Field(None, description="Updated pool location")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Updated Pool Name"},
                {"location": "San Francisco"}
            ]
        }
    )


# ---- GET (read) ----
class PoolRead(PoolBase):
    """Response model for pool retrieval."""
    
    id: UUID = Field(..., description="Unique pool identifier")
    member_count: int = Field(..., description="Number of members in the pool")
    created_at: datetime = Field(..., description="When the pool was created")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "name": "NYC Dating Pool",
                    "location": "New York",
                    "member_count": 15,
                    "created_at": "2025-06-01T10:00:00Z"
                }
            ]
        }
    )


# ---- Pool Member models ----
class PoolMemberBase(BaseModel):
    """Base model for pool membership."""
    
    user_id: UUID = Field(..., description="User ID of the pool member")


class PoolMemberCreate(PoolMemberBase):
    """Request model for adding a member to a pool."""
    
    coord_x: Optional[float] = Field(None, description="X coordinate (latitude)")
    coord_y: Optional[float] = Field(None, description="Y coordinate (longitude)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "coord_x": 40.7128,
                    "coord_y": -74.0060
                }
            ]
        }
    )


class PoolMemberPatch(BaseModel):
    """Request model for partially updating a pool member (coordinates only)."""
    
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


class PoolMemberRead(PoolMemberBase):
    """Response model for pool member retrieval."""
    
    pool_id: UUID = Field(..., description="Pool the member belongs to")
    coord_x: Optional[float] = Field(None, description="X coordinate (latitude)")
    coord_y: Optional[float] = Field(None, description="Y coordinate (longitude)")
    joined_at: datetime = Field(..., description="When the member joined the pool")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "pool_id": "11111111-1111-4111-8111-111111111111",
                    "coord_x": 40.7128,
                    "coord_y": -74.0060,
                    "joined_at": "2025-06-01T10:05:00Z"
                }
            ]
        }
    )


class PoolMemberDeleteResponse(BaseModel):
    """Response model for deleting a pool member."""
    
    message: str = Field(..., description="Confirmation message")
    user_id: UUID = Field(..., description="ID of the removed user")
    pool_id: UUID = Field(..., description="ID of the pool")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "User 22222222-2222-4222-8222-222222222222 removed from pool 11111111-1111-4111-8111-111111111111",
                    "user_id": "22222222-2222-4222-8222-222222222222",
                    "pool_id": "11111111-1111-4111-8111-111111111111"
                }
            ]
        }
    )
