from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import List
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.availability import (
    # Availability models
    AvailabilityCreate,
    AvailabilityRead,
    AvailabilityUpdate,
    # AvailabilityPool models
    AvailabilityPoolCreate,
    AvailabilityPoolRead,
    AvailabilityPoolUpdate,
)
from models.db import Availability, AvailabilityPool
from services.db import connect_with_connector

router = APIRouter()


def get_db_session() -> Session:
    """Get a database session."""
    engine = connect_with_connector()
    return Session(engine)


# Helper functions
def availability_to_read(db_availability: Availability) -> AvailabilityRead:
    """Convert database Availability to Pydantic AvailabilityRead."""
    return AvailabilityRead(
        availability_id=UUID(db_availability.availability_id),
        person_id=UUID(db_availability.person_id),
        location=db_availability.location,
        created_at=db_availability.created_at,
        updated_at=db_availability.updated_at,
    )


def availability_pool_to_read(db_pool: AvailabilityPool, session: Session) -> AvailabilityPoolRead:
    """Convert database AvailabilityPool to Pydantic AvailabilityPoolRead."""
    availabilities = session.query(Availability).filter(
        Availability.location == db_pool.location
    ).all()
    
    return AvailabilityPoolRead(
        availability_pool_id=UUID(db_pool.availability_pool_id),
        location=db_pool.location,
        availabilities=[availability_to_read(a) for a in availabilities],
        created_at=db_pool.created_at,
        updated_at=db_pool.updated_at,
    )


# =========================
# Availability Endpoints
# =========================


@router.post(
    "/availabilities",
    response_model=AvailabilityRead,
    status_code=status.HTTP_201_CREATED,
)
def create_availability(availability: AvailabilityCreate) -> AvailabilityRead:
    """Add a person to the availability pool."""
    session = get_db_session()
    try:
        db_availability = Availability(
            availability_id=str(availability.availability_id),
            person_id=str(availability.person_id),
            location=availability.location,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(db_availability)
        session.commit()
        session.refresh(db_availability)
        
        # Ensure availability pool exists for this location
        pool = session.query(AvailabilityPool).filter(
            AvailabilityPool.location == availability.location
        ).first()
        if not pool:
            pool = AvailabilityPool(
                availability_pool_id=None,  # Will be auto-generated
                location=availability.location,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(pool)
            session.commit()
        
        return availability_to_read(db_availability)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        session.close()


@router.get("/availabilities/{availability_id}", response_model=AvailabilityRead)
def get_availability(availability_id: UUID) -> AvailabilityRead:
    """Retrieve an availability record by its ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/availabilities", response_model=List[AvailabilityRead])
def list_availabilities() -> List[AvailabilityRead]:
    """List all availability records."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.patch("/availabilities/{availability_id}", response_model=AvailabilityRead)
def update_availability(
    availability_id: UUID, availability: AvailabilityUpdate
) -> AvailabilityRead:
    """Update an availability record."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )



@router.delete("/availabilities/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability(availability_id: UUID) -> None:
    """Remove a person from the availability pool."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )



# =========================
# AvailabilityPool Endpoints
# =========================


@router.post(
    "/availability-pools",
    response_model=AvailabilityPoolRead,
    status_code=status.HTTP_201_CREATED,
)
def create_availability_pool(pool: AvailabilityPoolCreate) -> AvailabilityPoolRead:
    """Create a new availability pool."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/availability-pools/{pool_id}", response_model=AvailabilityPoolRead)
def get_availability_pool(pool_id: UUID) -> AvailabilityPoolRead:
    """Retrieve an availability pool by its ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/availability-pools", response_model=List[AvailabilityPoolRead])
def list_availability_pools() -> List[AvailabilityPoolRead]:
    """List all availability pools."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get(
    "/availability-pools/location/{location}", response_model=AvailabilityPoolRead
)
def get_availability_pool_by_location(location: str) -> AvailabilityPoolRead:
    """Retrieve an availability pool by location."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.patch("/availability-pools/{pool_id}", response_model=AvailabilityPoolRead)
def update_availability_pool(
    pool_id: UUID, pool: AvailabilityPoolUpdate
) -> AvailabilityPoolRead:
    """Update an availability pool."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.delete("/availability-pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability_pool(pool_id: UUID) -> None:
    """Delete an availability pool."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
