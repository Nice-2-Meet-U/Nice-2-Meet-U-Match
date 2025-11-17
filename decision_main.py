"""Decision Microservice - Entrypoint"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from decision import decision_resources
from frameworks.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("✅ Decision service: Database tables ensured.")
    except Exception as e:
        logging.error(f"⚠️ Could not initialize database tables: {e}")
    
    yield
    
    # Shutdown
    logging.info("🛑 Decision service shutting down.")


app = FastAPI(
    title="Decision Microservice",
    version="1.0.0",
    description="Manages user decisions on matches",
    lifespan=lifespan,
)

app.include_router(decision_resources.router, prefix="/decisions", tags=["decisions"])


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "decision", "version": "1.0.0"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy", "service": "decision"}
