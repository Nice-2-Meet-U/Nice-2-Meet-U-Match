from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from resources import matches, decisions, pools

from frameworks.db.session import engine, Base

# ------------------------------------------------------------------------------
# App initialization
# ------------------------------------------------------------------------------

app = FastAPI(
    title="Matches Microservice",
    version="1.0.0",
    description=(
        "A microservice for handling match pools, pairwise matches, and "
        "user decisions (accept/reject) between participants."
    ),
)

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------

# Adjust allowed origins for your environment
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

# Group by resource type
app.include_router(pools.router, prefix="/pools", tags=["pools"])
app.include_router(matches.router, prefix="/matches", tags=["matches"])
app.include_router(decisions.router, prefix="/decisions", tags=["decisions"])

# ------------------------------------------------------------------------------
# Lifespan events (startup/shutdown)
# ------------------------------------------------------------------------------


@app.on_event("startup")
def on_startup():
    """
    Initialize resources when the service starts.
    For dev: optionally auto-create tables if you’re not running Alembic.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("✅ Database tables ensured.")
    except Exception as e:
        logging.error(f"⚠️ Could not initialize database tables: {e}")


@app.on_event("shutdown")
def on_shutdown():
    logging.info("🛑 Matches service shutting down.")


# ------------------------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------------------------


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "matches", "version": "1.0.0"}
