# models/user_match.py
from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime


# =========================
# User Pool Models
# =========================


class UserPoolBase(BaseModel):
    """Base model for user pool operations."""

    user_id: str = Field(..., description="The user ID")
    location: str = Field(..., description="The location where the pool is located")
    coord_x: Optional[float] = Field(None, description="X coordinate of the user")
    coord_y: Optional[float] = Field(None, description="Y coordinate of the user")


class UserPoolCreate(UserPoolBase):
    """Schema for adding a user to a pool (POST)."""

    pass


class UserPoolRead(BaseModel):
    """Schema for detailed user pool information (GET)."""

    pool_id: str
    pool_name: str
    location: Optional[str] = None
    member_count: int
    joined_at: datetime
    user_id: str

    model_config = ConfigDict(from_attributes=True)


class UserPoolUpdate(BaseModel):
    """Schema for updating user pool information (PATCH)."""

    coord_x: Optional[float] = None
    coord_y: Optional[float] = None


class UserPoolDelete(BaseModel):
    """Response model for removing a user from their pool (DELETE)."""

    message: str
    user_id: str
    pool_id: str


# Legacy aliases for backward compatibility
UserPoolPost = UserPoolCreate
UserPoolInfoResponse = UserPoolRead
UserPoolCoordinatesPatch = UserPoolUpdate
UserPoolDeleteResponse = UserPoolDelete


class UserPoolResponse(BaseModel):
    """Schema for user pool information response after the post operation."""

    user_id: str
    pool_id: str
    location: Optional[str] = None
    member: dict  # Contains member details from the pool service

    model_config = ConfigDict(from_attributes=True)


# =========================
# User Matches Models
# =========================


class UserMatchesBase(BaseModel):
    """Base model for user matches."""

    user_id: str
    matches_count: int
    matches: List[Any]  # List of match objects from matches service


class UserMatchesRead(UserMatchesBase):
    """Schema for user matches response (GET)."""

    model_config = ConfigDict(from_attributes=True)


# Legacy alias
UserMatchesResponse = UserMatchesRead


class GenerateMatchesBase(BaseModel):
    """Base model for match generation."""

    message: str
    pool_id: str
    matches_created: int
    matches: List[Any]  # List of created match objects


class GenerateMatchesCreate(GenerateMatchesBase):
    """Schema for generate matches response (POST)."""

    model_config = ConfigDict(from_attributes=True)


# Legacy alias
GenerateMatchesResponse = GenerateMatchesCreate


# =========================
# User Pool Members Models
# =========================


class UserPoolMembersBase(BaseModel):
    """Base model for user pool members."""

    user_id: str
    members_count: int
    members: List[Any]  # List of pool member objects


class UserPoolMembersRead(UserPoolMembersBase):
    """Schema for user pool members response (GET)."""

    model_config = ConfigDict(from_attributes=True)


# Legacy alias
UserPoolMembersResponse = UserPoolMembersRead


# =========================
# User Decisions Models
# =========================


class UserDecisionsBase(BaseModel):
    """Base model for user decisions."""

    user_id: str
    decisions_count: int
    decisions: List[Any]  # List of decision objects


class UserDecisionsRead(UserDecisionsBase):
    """Schema for user decisions response (GET)."""

    model_config = ConfigDict(from_attributes=True)


# Legacy alias
UserDecisionsResponse = UserDecisionsRead


class UserDecisionBase(BaseModel):
    """Base model for a single decision."""

    decision: str = Field(..., description="'accept' or 'reject'")


class UserDecisionCreate(UserDecisionBase):
    """Request model for submitting a decision via user_match composite (POST)."""

    pass


# Legacy alias
UserDecisionPost = UserDecisionCreate

