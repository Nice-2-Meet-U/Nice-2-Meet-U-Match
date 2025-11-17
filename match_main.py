"""Match Microservice - Entrypoint"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from match import match_resources
from frameworks.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("✅ Match service: Database tables ensured.")
    except Exception as e:
        logging.error(f"⚠️ Could not initialize database tables: {e}")
    
    yield
    
    # Shutdown
    logging.info("🛑 Match service shutting down.")


app = FastAPI(
    title="Match Microservice",
    version="1.0.0",
    description="Manages matches between users",
    lifespan=lifespan,
)

app.include_router(match_resources.router, prefix="/matches", tags=["matches"])


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "match", "version": "1.0.0"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy", "service": "match"}
