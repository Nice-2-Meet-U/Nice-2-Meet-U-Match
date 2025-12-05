# models/health.py
"""
Health check Pydantic models for monitoring endpoints.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoints."""
    
    ok: bool = Field(..., description="Health status indicator")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"ok": True}]
        }
    )

