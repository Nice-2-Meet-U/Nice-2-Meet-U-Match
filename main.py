from __future__ import annotations

import os
from typing import Dict
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI

from models.availability import AvailabilityPoolRead
from models.match import MatchRead

# Routers
from services import match as match_module
from services import availability as availability_module
from services.db import initialize_schema

load_dotenv()

# In-memory databases
AvailabilityPools: Dict[UUID, AvailabilityPoolRead] = {}
Matches: Dict[UUID, MatchRead] = {}

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
PORT = int(os.environ.get("PORT", 8000))

app = FastAPI(
    title="Match API",
    description="Demo FastAPI app using Pydantic v2 models for Matching/Availability",
    version="0.1.0",
)


# Initialize database schema on startup
@app.on_event("startup")
def startup_event():
    """Initialize database schema on application startup."""
    try:
        initialize_schema()
    except Exception as e:
        print(f"Warning: Could not initialize schema: {e}")


# -------------------------------------------------------------------
# Include Routers
# -------------------------------------------------------------------
app.include_router(match_module.router)
app.include_router(availability_module.router)


# -------------------------------------------------------------------
# Root
# -------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the Match API. See /docs for OpenAPI UI."}


# -------------------------------------------------------------------
# Entrypoint for `python main.py`
# -------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)

