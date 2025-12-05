from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    TIMESTAMP,
    Float,
    func,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import CHAR, ENUM as MySQLEnum
from sqlalchemy.orm import relationship
import enum
from uuid import uuid4
from frameworks.db.session import Base


# --- ENUMS ---
class MatchStatus(str, enum.Enum):
    waiting = "waiting"
    accepted = "accepted"
    rejected = "rejected"


class DecisionValue(str, enum.Enum):
    accept = "accept"
    reject = "reject"


# --- TABLES ---
class Pool(Base):
    __tablename__ = "pools"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    member_count = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    members = relationship(
        "PoolMember", back_populates="pool", cascade="all, delete-orphan"
    )
    matches = relationship("Match", back_populates="pool", cascade="all, delete-orphan")


class PoolMember(Base):
    __tablename__ = "pool_members"
    pool_id = Column(
        CHAR(36), ForeignKey("pools.id", ondelete="CASCADE"), primary_key=True
    )
    user_id = Column(CHAR(36), primary_key=True)
    coord_x = Column(Float, nullable=True)
    coord_y = Column(Float, nullable=True)
    joined_at = Column(TIMESTAMP, server_default=func.now())

    pool = relationship("Pool", back_populates="members")


class Match(Base):
    __tablename__ = "matches"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    pool_id = Column(
        CHAR(36), ForeignKey("pools.id", ondelete="CASCADE"), nullable=False
    )
    user1_id = Column(CHAR(36), nullable=False)
    user2_id = Column(CHAR(36), nullable=False)
    status = Column(
        String(20),  # Changed from Enum to String with length
        nullable=False,
        default=MatchStatus.waiting.value,
    )
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    pool = relationship("Pool", back_populates="matches")
    decisions = relationship(
        "MatchDecision", back_populates="match", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("pool_id", "user1_id", "user2_id", name="uq_pool_pair"),
    )


class MatchDecision(Base):
    __tablename__ = "match_decisions"
    match_id = Column(
        CHAR(36), ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True
    )
    user_id = Column(CHAR(36), primary_key=True)
    decision = Column(
        String(10), nullable=False  # Changed from Enum to String with length
    )
    decided_at = Column(TIMESTAMP, server_default=func.now())

    match = relationship("Match", back_populates="decisions")

    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_decision"),
    )
