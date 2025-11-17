"""User Microservice - Entrypoint (Orchestrator)"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from user import user_resources
from frameworks.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("✅ User service: Database tables ensured.")
    except Exception as e:
        logging.error(f"⚠️ Could not initialize database tables: {e}")
    
    yield
    
    # Shutdown
    logging.info("🛑 User service shutting down.")


app = FastAPI(
    title="User Microservice (Orchestrator)",
    version="1.0.0",
    description="Orchestrates pool, match, and decision services",
    lifespan=lifespan,
)

app.include_router(user_resources.router, prefix="/users", tags=["users"])


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "user-orchestrator", "version": "1.0.0"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy", "service": "user-orchestrator"}
