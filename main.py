from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()
import os

port = int(os.environ.get("FASTAPIPORT", 8000))


import socket
from datetime import datetime

from typing import Dict
from fastapi import FastAPI
from uuid import UUID
from models.availability import AvailabilityRead
from models.availability import AvailabilityPoolRead
from models.match import MatchRead
from models.match import MatchIndividualRead


# Routers
from services import match as match_module
from services import availability as availability_module

# In-memory databases
AvailabilityPools: Dict[UUID, AvailabilityPoolRead] = {}
Matches : Dict[UUID, MatchRead] = {}
# If you have a health router, uncomment the next line:
# from services.health import router as health_router

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
PORT = int(os.environ.get("FASTAPIPORT", 8000))

app = FastAPI(
    title="Match API",
    description="Demo FastAPI app using Pydantic v2 models for Matching/Availability",
    version="0.1.0",
)

# -------------------------------------------------------------------
# Include Routers
# -------------------------------------------------------------------
app.include_router(match_module.router)
app.include_router(availability_module.router)
# app.include_router(health_router)


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
