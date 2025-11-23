# models/user_match.py
from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime


class UserPoolPost(BaseModel):
    """Schema for adding a user to a pool."""

    user_id: str = Field(..., description="The user ID to add to the pool")
    location: str = Field(..., description="The location where the pool is located")
    coord_x: Optional[float] = Field(None, description="X coordinate of the user")
    coord_y: Optional[float] = Field(None, description="Y coordinate of the user")


class UserPoolResponse(BaseModel):
    """Schema for user pool information response after the post operation."""

    user_id: str
    pool_id: str
    location: Optional[str] = None
    member: dict  # Contains member details from the pool service

    model_config = ConfigDict(from_attributes=True)


class UserPoolInfoResponse(BaseModel):
    """Schema for detailed user pool information."""

    pool_id: str
    pool_name: str
    location: Optional[str] = None
    member_count: int
    joined_at: datetime
    user_id: str

    model_config = ConfigDict(from_attributes=True)


class UserMatchesResponse(BaseModel):
    """Schema for user matches response."""

    user_id: str
    matches_count: int
    matches: List[Any]  # List of match objects from matches service

    model_config = ConfigDict(from_attributes=True)


class GenerateMatchesResponse(BaseModel):
    """Schema for generate matches response."""

    message: str
    pool_id: str
    matches_created: int
    matches: List[Any]  # List of created match objects

    model_config = ConfigDict(from_attributes=True)


class UserPoolMembersResponse(BaseModel):
    """Schema for user pool members response."""

    user_id: str
    members_count: int
    members: List[Any]  # List of pool member objects

    model_config = ConfigDict(from_attributes=True)


class UserDecisionsResponse(BaseModel):
    """Schema for user decisions response."""

    user_id: str
    decisions_count: int
    decisions: List[Any]  # List of decision objects

    model_config = ConfigDict(from_attributes=True)


class UserPoolDeleteResponse(BaseModel):
    """Response model for removing a user from their pool."""

    message: str
    user_id: str
    pool_id: str


class UserPoolCoordinatesPatch(BaseModel):
    """Request model for updating user coordinates in pool."""

    coord_x: Optional[float] = None
    coord_y: Optional[float] = None
