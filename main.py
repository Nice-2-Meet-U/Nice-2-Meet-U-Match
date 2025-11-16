from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from resources import matches, decisions, pools

from frameworks.db.session import engine, Base

# ------------------------------------------------------------------------------
# App initialization
# ------------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    """
    # Startup
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("✅ Database tables ensured.")
    except Exception as e:
        logging.error(f"⚠️ Could not initialize database tables: {e}")
    
    yield
    
    # Shutdown
    logging.info("🛑 Matches service shutting down.")

app = FastAPI(
    title="Matches Microservice",
    version="1.0.0",
    description=(
        "A microservice for handling match pools, pairwise matches, and "
        "user decisions (accept/reject) between participants."
    ),
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

# Group by resource type
app.include_router(pools.router, prefix="/pools", tags=["pools"])
app.include_router(matches.router, prefix="/matches", tags=["matches"])
app.include_router(decisions.router, prefix="/decisions", tags=["decisions"])

# ------------------------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------------------------


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "matches", "version": "1.0.0"}
