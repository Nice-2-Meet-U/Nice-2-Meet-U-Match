from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Routers
from resources import matches, pools, user_match

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
        
        # Run migration to add coord_x and coord_y if they don't exist
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('pool_members')]
        
        if 'coord_x' not in columns or 'coord_y' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE pool_members ADD COLUMN IF NOT EXISTS coord_x FLOAT NULL"))
                conn.execute(text("ALTER TABLE pool_members ADD COLUMN IF NOT EXISTS coord_y FLOAT NULL"))
                conn.commit()
            logging.info("✅ Added coord_x and coord_y columns to pool_members")
    except Exception as e:
        logging.error(f"⚠️ Could not initialize database tables: {e}")
    
    yield
    
    # Shutdown
    logging.info("🛑 Matches service shutting down.")

app = FastAPI(
    title="Matches Feature",
    version="1.0.0",
    description=(
        "A microservice for handling match pools, pairwise matches, and "
        "user decisions (accept/reject) between participants."
    ),
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# CORS Configuration
# ------------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
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
app.include_router(user_match.router, prefix="/users", tags=["user-match"])

# ------------------------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------------------------


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "matches", "version": "1.0.0"}
