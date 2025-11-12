from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import List
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import and_

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
from models.db import Match, MatchIndividual
from services.db import connect_with_connector

router = APIRouter()


def get_db_session() -> Session:
    """Get a database session."""
    engine = connect_with_connector()
    return Session(engine)


# Helper functions
def match_individual_to_read(db_match_individual: MatchIndividual) -> MatchIndividualRead:
    """Convert database MatchIndividual to Pydantic MatchIndividualRead."""
    return MatchIndividualRead(
        match_individual_id=UUID(db_match_individual.match_individual_id),
        id1=UUID(db_match_individual.id1),
        id2=UUID(db_match_individual.id2),
        accepted=db_match_individual.accepted,
        created_at=db_match_individual.created_at,
        updated_at=db_match_individual.updated_at,
    )


def match_to_read(db_match: Match, session: Session) -> MatchRead:
    """Convert database Match to Pydantic MatchRead."""
    mi1 = session.query(MatchIndividual).filter(
        MatchIndividual.match_individual_id == db_match.match_individual_id1
    ).first()
    mi2 = session.query(MatchIndividual).filter(
        MatchIndividual.match_individual_id == db_match.match_individual_id2
    ).first()
    
    return MatchRead(
        match_id=UUID(db_match.match_id),
        match_id1=match_individual_to_read(mi1),
        match_id2=match_individual_to_read(mi2),
        accepted_by_both=db_match.accepted_by_both,
        created_at=db_match.created_at,
        updated_at=db_match.updated_at,
    )


# =========================
# MatchIndividual Endpoints
# =========================


@router.post("/match-individuals", response_model=MatchIndividualRead, status_code=status.HTTP_201_CREATED)
def create_match_individual(match_individual: MatchIndividualCreate) -> MatchIndividualRead:
    """Create a participant decision record."""
    session = get_db_session()
    try:
        db_match_individual = MatchIndividual(
            match_individual_id=str(match_individual.match_individual_id),
            id1=str(match_individual.id1),
            id2=str(match_individual.id2),
            accepted=match_individual.accepted,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(db_match_individual)
        session.commit()
        session.refresh(db_match_individual)
        return match_individual_to_read(db_match_individual)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        session.close()


@router.get("/match-individuals/{person_id}/{counterparty_id}", response_model=MatchIndividualRead)
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


@router.patch("/match-individuals/{person_id}/{counterparty_id}", response_model=MatchIndividualRead)
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


