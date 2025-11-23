# resources/user_match.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from services.user_match_service import (
    get_user_pool_from_service,
    add_user_to_pool_service,
    get_user_matches_from_service,
    generate_matches_for_user_service,
)
from models.user_match import UserPoolPost

router = APIRouter()


@router.get("/{user_id}/pool")
def get_user_pool(user_id: UUID):
    """
    Get the pool information for a specific user.
    Returns the pool details and membership information if the user is in a pool.
    """
    try:
        pool_data = get_user_pool_from_service(
            user_id=user_id,
            pools_service_url="https://matches-service-870022169527.us-central1.run.app",
        )
        return pool_data

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve user pool: {str(e)}"
        )


@router.post("/{user_id}/pool", status_code=status.HTTP_201_CREATED)
def add_user_to_pool(payload: UserPoolPost):
    """
    Add a user to a pool by location. Creates a new pool if none exists for the location,
    otherwise adds to a random existing pool at that location.
    """
    try:
        result = add_user_to_pool_service(
            user_id=payload.user_id,
            location=payload.location,
            coord_x=payload.coord_x,
            coord_y=payload.coord_y,
            pools_service_url="https://matches-service-870022169527.us-central1.run.app",
            max_pool_size=20,
        )
        return result

    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add user to pool: {str(e)}"
        )


@router.post("/{user_id}/matches", status_code=status.HTTP_201_CREATED)
def generate_matches_for_user(user_id: UUID):
    """
    Find the user's pool and generate up to 10 random matches with other pool members.
    """
    try:
        result = generate_matches_for_user_service(
            user_id=user_id,
            matches_service_url="https://matches-service-870022169527.us-central1.run.app",
            pools_service_url="https://matches-service-870022169527.us-central1.run.app",
            max_matches=10,
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate matches: {str(e)}"
        )


@router.get("/{user_id}/matches")
def get_user_matches(user_id: UUID):
    """
    Get all matches for a specific user.
    Returns a list of matches where the user is a participant.
    """
    try:
        matches = get_user_matches_from_service(
            user_id=user_id,
            matches_service_url="https://matches-service-870022169527.us-central1.run.app",
        )
        return {
            "user_id": str(user_id),
            "matches_count": len(matches),
            "matches": matches,
        }

    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve user matches: {str(e)}"
        )
