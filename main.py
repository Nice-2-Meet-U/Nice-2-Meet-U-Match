from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import os
from fastapi import FastAPI

# Routers
from services.match import router as match_router

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
app.include_router(match_router)
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
