"""Pool Microservice - Entrypoint"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from pool import pool_resources
from frameworks.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("✅ Pool service: Database tables ensured.")
    except Exception as e:
        logging.error(f"⚠️ Could not initialize database tables: {e}")
    
    yield
    
    # Shutdown
    logging.info("🛑 Pool service shutting down.")


app = FastAPI(
    title="Pool Microservice",
    version="1.0.0",
    description="Manages pools and pool memberships",
    lifespan=lifespan,
)

app.include_router(pool_resources.router, prefix="/pools", tags=["pools"])


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "pool", "version": "1.0.0"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy", "service": "pool"}
