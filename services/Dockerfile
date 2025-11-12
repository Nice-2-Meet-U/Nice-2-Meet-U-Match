(# Minimal, production-ready Dockerfile for the FastAPI app in the repository root.
# It expects `requirements.txt` at the project root and the FastAPI app module to be
# importable as `main:app` (per `main.py`). Adjust `PORT` env var if needed.)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies (kept minimal). Add extras if your requirements need them.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker layer caching
COPY ../requirements.txt ./requirements.txt

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY .. .

# Create a non-root user and give ownership of the app directory
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Use a POSIX shell so the ${PORT} env var expands at container start.
# We use 1 worker by default; increase with --workers for more concurrency.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
