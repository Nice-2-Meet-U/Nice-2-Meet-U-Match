# models/user_match.py
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class UserPoolPost(BaseModel):
    """Schema for adding a user to a pool."""

    user_id: str = Field(..., description="The user ID to add to the pool")
    location: str = Field(..., description="The location where the pool is located")
    coord_x: Optional[float] = Field(None, description="X coordinate of the user")
    coord_y: Optional[float] = Field(None, description="Y coordinate of the user")


class UserPoolRead(BaseModel):
    """Schema for reading user pool information."""

    user_id: str
    pool_id: str
    location: str
    member: dict

    class Config:
        from_attributes = True
