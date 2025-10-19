# Match Microservice

A FastAPI-based microservice for managing user availability and matches. This service provides APIs for managing user availability in different locations and facilitating matches between users.

## Overview

This microservice is built using:
- FastAPI for the API framework
- Pydantic v2 for data validation and serialization
- Python 3.x
- uvicorn as the ASGI server

## Models

### Availability Models

#### AvailabilityBase
- `availability_id`: Unique identifier (UUID)
- `person_id`: UUID of the person
- `location`: String representing geographical location (e.g., "NYC")

#### Derived Availability Models
- `AvailabilityCreate`: For creating new availability records
- `AvailabilityUpdate`: For updating existing availability records
- `AvailabilityRead`: Includes additional fields:
  - `updated_at`: Last update timestamp
  - `created_at`: Creation timestamp

#### AvailabilityPool Models
Manages groups of availabilities by location:
- `AvailabilityPoolBase`:
  - `availability_pool_id`: Unique identifier
  - `location`: Location name/code
  - `availabilities`: List of `AvailabilityRead` objects

### Match Models

#### MatchIndividual
Represents one person's decision in a potential match:
- `match_individual_id`: Unique identifier
- `id1`: Person making the decision
- `id2`: Potential match partner
- `accepted`: Boolean (null = pending, true = accepted, false = rejected)

#### Match
Represents a complete match between two people:
- Contains two `MatchIndividual` records
- `match_id`: Unique identifier
- `accepted_by_both`: Boolean indicating mutual acceptance
- Includes timestamps for creation and updates

## Services

### Availability Service

#### Availability Endpoints
- `POST /availabilities`: Create new availability
- `GET /availabilities/{availability_id}`: Get specific availability
- `GET /availabilities`: List all availabilities
- `PATCH /availabilities/{availability_id}`: Update availability
- `DELETE /availabilities/{availability_id}`: Remove availability

#### Availability Pool Endpoints
- `POST /availability-pools`: Create new pool
- `GET /availability-pools/{pool_id}`: Get specific pool
- `GET /availability-pools`: List all pools
- `GET /availability-pools/location/{location}`: Get pool by location
- `PATCH /availability-pools/{pool_id}`: Update pool
- `DELETE /availability-pools/{pool_id}`: Delete pool

### Match Service

#### Match Individual Endpoints
- `POST /match-individuals`: Create decision record
- `GET /match-individuals/{person_id}/{counterparty_id}`: Get specific decision
- `GET /match-individuals/person/{person_id}`: List person's decisions
- `PATCH /match-individuals/{person_id}/{counterparty_id}`: Update decision
- `DELETE /match-individuals/{person_id}/{counterparty_id}`: Delete decision

#### Match Endpoints
- `POST /matches`: Create new match
- `GET /matches/{match_id}`: Get specific match
- `GET /matches`: List all matches
- `GET /matches/person/{person_id}`: List person's matches
- `GET /matches/accepted`: List accepted matches
- `PATCH /matches/{match_id}`: Update match
- `DELETE /matches/{match_id}`: Delete match

## Setup and Running

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
- `FASTAPIPORT`: Port number (default: 8000)

3. Run the service:
```bash
python main.py
```

The API will be available at `http://localhost:8000` with OpenAPI documentation at `/docs`.

## Data Storage

The service currently uses in-memory storage:
- `AvailabilityPools`: Dictionary storing availability pools
- `Matches`: Dictionary storing matches

Note: This is a demo implementation and should be replaced with a persistent database for production use.

## API Documentation

Full OpenAPI documentation is available at the `/docs` endpoint when running the service.

## Status

This is a demo implementation (v0.1.0) with endpoints defined but not yet implemented. All endpoints currently return a 501 Not Implemented status.