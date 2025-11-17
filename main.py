from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Routers
from pool import pool_resources
from match import match_resources
from decision import decision_resources
from user import user_resources

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
app.include_router(pool_resources.router, prefix="/pools", tags=["pools"])
app.include_router(match_resources.router, prefix="/matches", tags=["matches"])
app.include_router(decision_resources.router, prefix="/decisions", tags=["decisions"])
app.include_router(user_resources.router, prefix="/users", tags=["users"])
# ------------------------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------------------------


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "matches", "version": "1.0.0"}
