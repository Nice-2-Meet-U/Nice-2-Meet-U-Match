"""HTTP clients for calling other microservices using HATEOAS."""
from __future__ import annotations

import os
from typing import Optional, Dict, Any
from uuid import UUID
import httpx
from fastapi import HTTPException


class HATEOASClient:
    """Base client for HATEOAS-based microservice communication."""
    
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    def _get_client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout)
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions."""
        if response.status_code >= 400:
            try:
                error_detail = response.json().get("detail", response.text)
            except Exception:
                error_detail = response.text
            
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Service error: {error_detail}"
            )
        return response.json()
    
    def follow_link(self, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Follow a HATEOAS link."""
        href = link_data.get("href")
        method = link_data.get("method", "GET")
        
        if not href:
            raise ValueError("Link missing href")
        
        with self._get_client() as client:
            if method == "GET":
                response = client.get(href)
            elif method == "POST":
                response = client.post(href)
            elif method == "PATCH":
                response = client.patch(href)
            elif method == "DELETE":
                response = client.delete(href)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return self._handle_response(response)


class PoolServiceClient(HATEOASClient):
    """Client for Pool microservice using HATEOAS."""
    
    def __init__(self):
        # Use POOL_SERVICE_URL if set, otherwise fall back to SERVICE_BASE_URL
        base_url = os.getenv("POOL_SERVICE_URL") or os.getenv("SERVICE_BASE_URL", "http://localhost:8000")
        super().__init__(base_url)
    
    def list_pools(self, location: Optional[str] = None, skip: int = 0, limit: int = 100) -> list[Dict[str, Any]]:
        """List pools, optionally filtered by location."""
        params = {"skip": skip, "limit": limit}
        if location:
            params["location"] = location
        
        with self._get_client() as client:
            response = client.get(f"{self.base_url}/pools", params=params)
            return self._handle_response(response)
    
    def create_pool(self, name: str, location: str) -> Dict[str, Any]:
        """Create a new pool."""
        with self._get_client() as client:
            response = client.post(
                f"{self.base_url}/pools",
                json={"name": name, "location": location}
            )
            return self._handle_response(response)
    
    def get_pool(self, pool_id: UUID) -> Dict[str, Any]:
        """Get a pool by ID."""
        with self._get_client() as client:
            response = client.get(f"{self.base_url}/pools/{pool_id}")
            return self._handle_response(response)
    
    def add_pool_member(self, pool_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Add a user to a pool using HATEOAS link if available."""
        with self._get_client() as client:
            response = client.post(
                f"{self.base_url}/pools/{pool_id}/members",
                json={"user_id": str(user_id)}
            )
            return self._handle_response(response)
    
    def list_pool_members(self, pool_data: Dict[str, Any]) -> list[Dict[str, Any]]:
        """List pool members using HATEOAS link from pool data."""
        links = pool_data.get("_links", {})
        
        # Use HATEOAS link if available
        if "members" in links:
            return self.follow_link(links["members"])
        
        # Fallback to constructing URL
        pool_id = pool_data.get("id")
        with self._get_client() as client:
            response = client.get(f"{self.base_url}/pools/{pool_id}/members")
            return self._handle_response(response)


class MatchServiceClient(HATEOASClient):
    """Client for Match microservice using HATEOAS."""
    
    def __init__(self):
        # Use MATCH_SERVICE_URL if set, otherwise fall back to SERVICE_BASE_URL
        base_url = os.getenv("MATCH_SERVICE_URL") or os.getenv("SERVICE_BASE_URL", "http://localhost:8000")
        super().__init__(base_url)
    
    def create_match(self, pool_id: UUID, user1_id: UUID, user2_id: UUID) -> Dict[str, Any]:
        """Create a new match."""
        with self._get_client() as client:
            response = client.post(
                f"{self.base_url}/matches",
                json={
                    "pool_id": str(pool_id),
                    "user1_id": str(user1_id),
                    "user2_id": str(user2_id)
                }
            )
            return self._handle_response(response)


class DecisionServiceClient(HATEOASClient):
    """Client for Decision microservice using HATEOAS."""
    
    def __init__(self):
        # Use DECISION_SERVICE_URL if set, otherwise fall back to SERVICE_BASE_URL
        base_url = os.getenv("DECISION_SERVICE_URL") or os.getenv("SERVICE_BASE_URL", "http://localhost:8000")
        super().__init__(base_url)
    
    def get_decisions_for_match(self, match_data: Dict[str, Any]) -> list[Dict[str, Any]]:
        """Get decisions for a match using HATEOAS link."""
        links = match_data.get("_links", {})
        
        # Use HATEOAS link if available
        if "decisions" in links:
            return self.follow_link(links["decisions"])
        
        # Fallback to constructing URL
        match_id = match_data.get("match_id")
        with self._get_client() as client:
            response = client.get(
                f"{self.base_url}/decisions",
                params={"match_id": str(match_id)}
            )
            return self._handle_response(response)
