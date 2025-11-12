"""SQLAlchemy ORM models for database tables."""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import uuid

Base = declarative_base()


class MatchIndividual(Base):
    """ORM model for individual participant decision in a match."""
    __tablename__ = "match_individuals"

    # Using CHAR(36) for UUID storage (standard UUID string format)
    match_individual_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id1 = Column(CHAR(36), nullable=False, index=True)  # Person making decision
    id2 = Column(CHAR(36), nullable=False, index=True)  # Counterparty
    accepted = Column(Boolean, nullable=True, default=None)  # None=pending, True=accepted, False=rejected
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Match(Base):
    """ORM model for a match between two participants."""
    __tablename__ = "matches"

    match_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_individual_id1 = Column(CHAR(36), ForeignKey("match_individuals.match_individual_id"), nullable=False)
    match_individual_id2 = Column(CHAR(36), ForeignKey("match_individuals.match_individual_id"), nullable=False)
    accepted_by_both = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Availability(Base):
    """ORM model for a person's availability in the matching pool."""
    __tablename__ = "availabilities"

    availability_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id = Column(CHAR(36), nullable=False, index=True)
    location = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class AvailabilityPool(Base):
    """ORM model for a location-based availability pool."""
    __tablename__ = "availability_pools"

    availability_pool_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
