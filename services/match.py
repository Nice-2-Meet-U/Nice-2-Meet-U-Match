from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import List


from models.match import (
# Match models
    MatchCreate,
    MatchRead,
    MatchUpdate,
    # MatchIndividual models
    MatchIndividualCreate,
    MatchIndividualRead,
    MatchIndividualUpdate,
)

router = APIRouter()


# =========================
# MatchIndividual Endpoints
# =========================


@router.post("/match-individuals", response_model=MatchIndividualRead, status_code=status.HTTP_201_CREATED,
)
def create_match_individual(match_individual: MatchIndividualCreate) -> MatchIndividualRead:
    """Create a participant decision record."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )




@router.get("/match-individuals/{person_id}/{counterparty_id}",response_model=MatchIndividualRead)
def get_match_individual(person_id: UUID, counterparty_id: UUID) -> MatchIndividualRead:
    """Retrieve a participant decision record."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/match-individuals/person/{person_id}", response_model=List[MatchIndividualRead])
def list_match_individuals_by_person(person_id: UUID) -> List[MatchIndividualRead]:
    """List all match decisions for a specific person."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.patch(
    "/match-individuals/{person_id}/{counterparty_id}",
    response_model=MatchIndividualRead,
)
def update_match_individual(
    person_id: UUID, counterparty_id: UUID, match_individual: MatchIndividualUpdate
) -> MatchIndividualRead:
    """Update a participant decision (accept/reject)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.delete(
    "/match-individuals/{person_id}/{counterparty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_match_individual(person_id: UUID, counterparty_id: UUID) -> None:
    """Delete a participant decision record."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


# =========================
# Match Endpoints
# =========================


@router.post("/matches", response_model=MatchRead, status_code=status.HTTP_201_CREATED)
def create_match(match: MatchCreate) -> MatchRead:
    """Create a new match between two participants."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/matches/{match_id}", response_model=MatchRead)
def get_match(match_id: UUID) -> MatchRead:
    """Retrieve a match by its ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/matches", response_model=List[MatchRead])
def list_matches() -> List[MatchRead]:
    """List all matches."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/matches/person/{person_id}", response_model=List[MatchRead])
def list_matches_by_person(person_id: UUID) -> List[MatchRead]:
    """List all matches involving a specific person."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/matches/accepted", response_model=List[MatchRead])
def list_accepted_matches() -> List[MatchRead]:
    """List all matches accepted by both participants."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.patch("/matches/{match_id}", response_model=MatchRead)
def update_match(match_id: UUID, match: MatchUpdate) -> MatchRead:
    """Update a match (participant decisions)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.delete("/matches/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(match_id: UUID) -> None:
    """Delete a match."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


