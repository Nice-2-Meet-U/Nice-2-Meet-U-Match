"""HATEOAS utilities for building hypermedia links."""
from __future__ import annotations

import os
from typing import Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class Link(BaseModel):
    """A hypermedia link."""
    
    href: str = Field(..., description="URL to the resource")
    method: str = Field(default="GET", description="HTTP method")
    rel: Optional[str] = Field(None, description="Relationship type")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "href": "http://localhost:8000/pools/123",
                    "method": "GET",
                    "rel": "self"
                }
            ]
        }
    )


class LinkBuilder:
    """Builds HATEOAS links for resources."""
    
    def __init__(self):
        self.base_url = os.getenv("SERVICE_BASE_URL", "http://localhost:8000")
    
    # Pool Links
    def pool_self(self, pool_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/pools/{pool_id}",
            method="GET",
            rel="self"
        )
    
    def pool_list(self, location: Optional[str] = None) -> Link:
        href = f"{self.base_url}/pools"
        if location:
            href += f"?location={location}"
        return Link(href=href, method="GET", rel="collection")
    
    def pool_create(self) -> Link:
        return Link(
            href=f"{self.base_url}/pools",
            method="POST",
            rel="create"
        )
    
    def pool_update(self, pool_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/pools/{pool_id}",
            method="PATCH",
            rel="update"
        )
    
    def pool_delete(self, pool_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/pools/{pool_id}",
            method="DELETE",
            rel="delete"
        )
    
    def pool_members(self, pool_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/pools/{pool_id}/members",
            method="GET",
            rel="members"
        )
    
    def pool_add_member(self, pool_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/pools/{pool_id}/members",
            method="POST",
            rel="add-member"
        )
    
    def pool_remove_member(self, pool_id: UUID, user_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/pools/{pool_id}/members/{user_id}",
            method="DELETE",
            rel="remove-member"
        )
    
    # Match Links
    def match_self(self, match_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/matches/{match_id}",
            method="GET",
            rel="self"
        )
    
    def match_list(self, pool_id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> Link:
        href = f"{self.base_url}/matches"
        params = []
        if pool_id:
            params.append(f"pool_id={pool_id}")
        if user_id:
            params.append(f"user_id={user_id}")
        if params:
            href += "?" + "&".join(params)
        return Link(href=href, method="GET", rel="collection")
    
    def match_create(self) -> Link:
        return Link(
            href=f"{self.base_url}/matches",
            method="POST",
            rel="create"
        )
    
    def match_update(self, match_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/matches/{match_id}",
            method="PATCH",
            rel="update"
        )
    
    def match_decisions(self, match_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/decisions?match_id={match_id}",
            method="GET",
            rel="decisions"
        )
    
    # Decision Links
    def decision_submit(self) -> Link:
        return Link(
            href=f"{self.base_url}/decisions",
            method="POST",
            rel="submit-decision"
        )
    
    def decision_list(self, match_id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> Link:
        href = f"{self.base_url}/decisions"
        params = []
        if match_id:
            params.append(f"match_id={match_id}")
        if user_id:
            params.append(f"user_id={user_id}")
        if params:
            href += "?" + "&".join(params)
        return Link(href=href, method="GET", rel="collection")
    
    # User Links
    def user_add_to_pool(self, user_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/users/{user_id}/add-to-pool",
            method="POST",
            rel="add-to-pool"
        )
    
    def user_generate_matches(self, user_id: UUID) -> Link:
        return Link(
            href=f"{self.base_url}/users/{user_id}/generate-matches",
            method="POST",
            rel="generate-matches"
        )


def build_links(resource_type: str, resource_id: Optional[UUID] = None, **context) -> Dict[str, Link]:
    """
    Build common links for a resource type.
    
    Args:
        resource_type: Type of resource (pool, match, decision, user)
        resource_id: ID of the specific resource
        **context: Additional context for building links
    
    Returns:
        Dictionary of links
    """
    builder = LinkBuilder()
    links = {}
    
    if resource_type == "pool" and resource_id:
        links["self"] = builder.pool_self(resource_id)
        links["members"] = builder.pool_members(resource_id)
        links["add-member"] = builder.pool_add_member(resource_id)
        links["update"] = builder.pool_update(resource_id)
        links["delete"] = builder.pool_delete(resource_id)
        
    elif resource_type == "match" and resource_id:
        links["self"] = builder.match_self(resource_id)
        links["decisions"] = builder.match_decisions(resource_id)
        links["update"] = builder.match_update(resource_id)
        
    elif resource_type == "user" and resource_id:
        links["add-to-pool"] = builder.user_add_to_pool(resource_id)
        links["generate-matches"] = builder.user_generate_matches(resource_id)
    
    return links
