from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import List

from ..models.availability import (
    # Availability models
    AvailabilityCreate,
    AvailabilityRead,
    AvailabilityUpdate,
    AvailabilityRemove,
    # AvailabilityPool models
    AvailabilityPoolCreate,
    AvailabilityPoolRead,
    AvailabilityPoolUpdate,
)
router = APIRouter()


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
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


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


@router.patch("/availability/{availability_id}", response_model=AvailabilityPoolRead)
def update_availability_pool(
    pool_id: UUID, pool: AvailabilityPoolUpdate
) -> AvailabilityPoolRead:
    """Update an availability pool."""
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
