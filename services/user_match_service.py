# services/user_match_service.py
from __future__ import annotations

from uuid import UUID
import requests
import random
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_user_pool_from_service(user_id: UUID, pools_service_url: str):
    """
    Query the pools service to get pool information for a user.
    Uses /pools/members?user_id={user_id} to find the user's pool membership,
    then retrieves the pool details.
    Returns pool data or raises an exception.
    """
    try:
        # Step 1: Get the user's pool membership
        members_response = requests.get(
            f"{pools_service_url}/pools/members?user_id={user_id}"
        )
        members_response.raise_for_status()
        members = members_response.json()
        
        if not members or len(members) == 0:
            raise ValueError("User is not a member of any pool")
        
        user_member = members[0]  # Should only be one membership per user
        pool_id = user_member.get("pool_id")
        
        # Step 2: Fetch pool details
        pool_response = requests.get(f"{pools_service_url}/pools/{pool_id}")
        pool_response.raise_for_status()
        user_pool = pool_response.json()
        
        # Step 3: Return combined pool and member information
        return {
            "pool_id": user_pool["id"],
            "pool_name": user_pool["name"],
            "location": user_pool.get("location"),
            "member_count": user_pool.get("member_count"),
            "joined_at": user_member["joined_at"],
            "user_id": user_member["user_id"],
        }

    except ValueError:
        raise
    except requests.RequestException as e:
        raise RuntimeError(f"Service communication error: {str(e)}")


def add_user_to_pool_service(
    user_id: str,
    location: str,
    coord_x: Optional[float],
    coord_y: Optional[float],
    pools_service_url: str,
    max_pool_size: int = 20,
):
    """
    Add a user to a pool by location via the pools service.
    Creates a new pool if none exists or all are full.
    Returns pool and member information.
    """
    try:
        # Find pools at the specified location that are not full
        pools_response = requests.get(f"{pools_service_url}/pools?location={location}")
        pools_response.raise_for_status()
        pools = pools_response.json()

        # Filter out full pools
        pools = [p for p in pools if p.get("member_count", 0) < max_pool_size]

        if not pools or len(pools) == 0:
            # No pools exist for this location, create a new one
            pool_name = f"Pool for {location}"
            pool_response = requests.post(
                f"{pools_service_url}/pools",
                json={
                    "name": pool_name,
                    "location": location,
                },
            )
            pool_response.raise_for_status()
            pool = pool_response.json()
        else:
            # Select a random pool from the available pools at this location
            pool = random.choice(pools)

        # Add the user to the selected/created pool
        member_payload = {"user_id": user_id}
        if coord_x is not None:
            member_payload["coord_x"] = coord_x
        if coord_y is not None:
            member_payload["coord_y"] = coord_y

        member_response = requests.post(
            f'{pools_service_url}/pools/{pool["id"]}/members', json=member_payload
        )
        member_response.raise_for_status()
        member = member_response.json()

        return {
            "user_id": user_id,
            "pool_id": pool["id"],
            "location": location,
            "member": member,
        }

    except requests.RequestException as e:
        raise RuntimeError(f"Service communication error: {str(e)}")


def get_user_matches_from_service(user_id: UUID, matches_service_url: str):
    """
    Get all matches for a user from the matches service.
    Returns a list of matches where the user is a participant.
    """
    try:
        matches_response = requests.get(
            f"{matches_service_url}/matches?user_id={user_id}"
        )
        matches_response.raise_for_status()
        matches = matches_response.json()

        return matches

    except requests.RequestException as e:
        if hasattr(e, "response") and e.response and e.response.status_code == 404:
            return []  # No matches found
        raise RuntimeError(f"Service communication error: {str(e)}")


def generate_matches_for_user_service(
    user_id: UUID,
    matches_service_url: str,
    pools_service_url: str,
    max_matches: int = 10,
):
    """
    Generate matches for a user by:
    1. Finding the user's pool by searching pool_members
    2. Getting all pool members from that pool
    3. Creating matches with random members via matches service
    Returns information about created matches.
    """
    try:
        # Step 1: Find which pool the user is in
        user_pool_data = get_user_pool_from_service(user_id, pools_service_url)
        pool_id = user_pool_data.get("pool_id")

        if not pool_id:
            raise ValueError(
                "User is not a member of any pool. Add user to a pool first."
            )

        # Step 2: Get all members of that pool
        members_response = requests.get(
            f"{pools_service_url}/pools/{pool_id}/members"
        )
        members_response.raise_for_status()
        pool_members = members_response.json()

        # Filter out the current user
        other_members = [
            member for member in pool_members if member.get("user_id") != str(user_id)
        ]

        if not other_members:
            return {
                "message": "No other users in the pool to match with",
                "pool_id": pool_id,
                "matches_created": 0,
                "matches": [],
            }

        # Select up to max_matches random other members
        selected_members = random.sample(
            other_members, min(max_matches, len(other_members))
        )

        # Create matches via matches service using threading for parallel creation
        created_matches = []
        
        def create_match(member):
            """Helper function to create a single match."""
            try:
                match_response = requests.post(
                    f"{matches_service_url}/matches",
                    json={
                        "pool_id": pool_id,
                        "user1_id": str(user_id),
                        "user2_id": member.get("user_id"),
                    },
                )
                match_response.raise_for_status()
                return match_response.json()
            except requests.RequestException:
                # Skip if match already exists or other error
                return None
        
        # Use ThreadPoolExecutor to create matches in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_member = {executor.submit(create_match, member): member for member in selected_members}
            for future in as_completed(future_to_member):
                match = future.result()
                if match:
                    created_matches.append(match)

        return {
            "message": f"Generated {len(created_matches)} matches for user {user_id}",
            "pool_id": pool_id,
            "matches_created": len(created_matches),
            "matches": created_matches,
        }

    except ValueError:
        raise
    except requests.RequestException as e:
        raise RuntimeError(f"Service communication error: {str(e)}")


def get_pool_members_from_service(user_id: UUID, pools_service_url: str):
    """
    Get all members in the same pool as the specified user.
    First finds which pool the user is in, then gets all members of that pool.
    Returns a list of pool members.
    """
    try:
        # Step 1: Find which pool the user is in
        user_pool_data = get_user_pool_from_service(user_id, pools_service_url)
        pool_id = user_pool_data.get("pool_id")
        
        if not pool_id:
            raise ValueError("User is not a member of any pool")
        
        # Step 2: Get all members of that pool
        members_response = requests.get(
            f"{pools_service_url}/pools/{pool_id}/members"
        )
        members_response.raise_for_status()
        members = members_response.json()

        return members

    except ValueError:
        raise
    except requests.RequestException as e:
        raise RuntimeError(f"Service communication error: {str(e)}")


def get_user_decisions_from_service(user_id: UUID, base_url: str):
    """
    Get all decisions made by a specific user.
    Now calls the dedicated decisions endpoint which requires user_id.
    Returns a list of decisions.
    """
    try:
        decisions_response = requests.get(
            f"{base_url}/decisions?user_id={user_id}"
        )
        decisions_response.raise_for_status()
        decisions = decisions_response.json()

        return decisions

    except requests.RequestException as e:
        if hasattr(e, "response") and e.response and e.response.status_code == 404:
            return []  # No decisions found
        raise RuntimeError(f"Service communication error: {str(e)}")


def delete_user_from_pool_service(user_id: UUID, pools_service_url: str):
    """
    Remove a user from their pool.
    First finds which pool the user is in, then removes them.
    This cascades - removing the pool member will also affect related matches.
    """
    try:
        # Step 1: Find which pool the user is in
        user_pool_data = get_user_pool_from_service(user_id, pools_service_url)
        pool_id = user_pool_data.get("pool_id")
        
        if not pool_id:
            raise ValueError("User is not a member of any pool")
        
        # Step 2: Remove the user from that pool
        delete_response = requests.delete(
            f"{pools_service_url}/pools/{pool_id}/members/{user_id}"
        )
        delete_response.raise_for_status()
        
        return {
            "message": f"User {user_id} removed from pool {pool_id}",
            "user_id": str(user_id),
            "pool_id": pool_id,
        }

    except ValueError:
        raise
    except requests.RequestException as e:
        if hasattr(e, "response") and e.response and e.response.status_code == 404:
            raise ValueError("User or pool not found")
        raise RuntimeError(f"Service communication error: {str(e)}")


def update_user_pool_coordinates_service(
    user_id: UUID,
    coord_x: Optional[float],
    coord_y: Optional[float],
    pools_service_url: str,
):
    """
    Update a user's coordinates in their pool.
    First finds which pool the user is in, then updates their member record.
    Note: This is a partial update - only coordinates can be changed.
    """
    try:
        # Step 1: Find which pool the user is in
        user_pool_data = get_user_pool_from_service(user_id, pools_service_url)
        pool_id = user_pool_data.get("pool_id")
        
        if not pool_id:
            raise ValueError("User is not a member of any pool")
        
        # Step 2: Update the pool member coordinates
        # Note: The pool member table doesn't have a PATCH endpoint in the atomic service
        # We need to use the pool PATCH endpoint or re-implement member updates
        # For now, we'll document this limitation
        raise NotImplementedError(
            "Pool member coordinate updates not supported by atomic service. "
            "Use DELETE + POST to update member location."
        )

    except (ValueError, NotImplementedError):
        raise
    except requests.RequestException as e:
        raise RuntimeError(f"Service communication error: {str(e)}")
