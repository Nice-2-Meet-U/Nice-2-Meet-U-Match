from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


# ---- Base (shared fields that describe a pool) ----
class PoolBase(BaseModel):
    name: str
    location: Optional[str] = None


# ---- POST (create) ----
class PoolCreate(PoolBase):
    pass


# ---- PUT (full update/replace). You usually keep same fields as base. ----
class PoolPut(PoolBase):
    pass


# ---- PATCH (partial update). All fields optional. ----
class PoolPatch(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None


# ---- GET (read) ----
class PoolRead(PoolBase):
    id: UUID
    member_count: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )  # <- pydantic v2: accepts ORM objects


# ---- Pool Member models ----
class PoolMemberBase(BaseModel):
    user_id: str


class PoolMemberCreate(PoolMemberBase):
    coord_x: Optional[float] = None
    coord_y: Optional[float] = None


class PoolMemberRead(PoolMemberBase):
    pool_id: UUID
    coord_x: Optional[float] = None
    coord_y: Optional[float] = None
    joined_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class PoolMemberDeleteResponse(BaseModel):
    """Response model for deleting a pool member."""
    message: str
    user_id: UUID
    pool_id: UUID
