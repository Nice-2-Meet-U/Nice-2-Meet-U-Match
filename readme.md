# API Endpoints Documentation

This FastAPI application provides endpoints for managing availability and matches in what appears to be a matching/pairing system (possibly for dating, networking, or similar use cases).

## Overview

The API has two main resource types:
- **Availability**: Tracks which people are available and in which locations
- **Matches**: Manages pairings between two people and their acceptance status

## Data Storage

Currently uses in-memory storage:
- `_availability_by_location`: Stores availability records indexed by location
- `_matches_by_id`: Stores match records indexed by match UUID

**Note**: All endpoints currently return `501 NOT IMPLEMENTED` - the implementation needs to be completed.

---

## Availability Endpoints

### `GET /availability`
Lists all availability records, with optional location filtering.

**Query Parameters:**
- `location` (optional): Filter results by location (e.g., "new_york", "san_francisco")

**Response:** List of `AvailabilityRead` objects

**Use case:** View all people available for matching, optionally filtered by city/region

---

### `GET /availability/{person_id}`
Retrieves availability information for a specific person.

**Path Parameters:**
- `person_id`: UUID of the person

**Response:** Single `AvailabilityRead` object

**Status Codes:**
- `200`: Success
- `404`: Availability not found

---

### `POST /availability`
Creates a new availability record (adds someone to the matching pool).

**Request Body:** `AvailabilityCreate`
- `person_id`: UUID identifying the person
- `location`: Where they're available for matches

**Response:** `AvailabilityRead` object
**Status Code:** `201 Created`

**Use case:** User signs up and indicates they're available for matching in a specific location

---

### `PATCH /availability/{person_id}`
Updates an existing availability record.

**Path Parameters:**
- `person_id`: UUID of the person

**Request Body:** `AvailabilityUpdate`
- Can update location and other availability fields

**Response:** Updated `AvailabilityRead` object

**Use case:** User changes their location or availability preferences

---

### `DELETE /availability/{person_id}`
Removes someone from the availability pool.

**Path Parameters:**
- `person_id`: UUID of the person

**Status Code:** `204 No Content`

**Use case:** User opts out of matching or leaves the system

---

## Match Endpoints

### `GET /matches`
Lists all matches in the system.

**Response:** List of `MatchRead` objects

**Use case:** Admin view of all matches or user viewing their match history

---

### `GET /matches/{match_id}`
Retrieves a specific match by ID.

**Path Parameters:**
- `match_id`: UUID of the match

**Response:** Single `MatchRead` object

**Status Codes:**
- `200`: Success
- `404`: Match not found

---

### `POST /matches`
Creates a new match between two people.

**Request Body:** `MatchCreate`
- `match_id1`: First participant's details (`MatchIndividualCreate`)
- `match_id2`: Second participant's details (`MatchIndividualCreate`)

**Response:** `MatchRead` object
**Status Code:** `201 Created`

**Use case:** System algorithm creates a pairing between two available people

---

### `PATCH /matches/{match_id}/{person_id}`
Updates a participant's response to a match (accept/reject).

**Path Parameters:**
- `match_id`: UUID of the match
- `person_id`: UUID of the person responding

**Query Parameters:**
- `action`: Must be either "accept" or "reject"

**Response:** Updated `MatchRead` object

**Use case:** User accepts or rejects a proposed match. The system automatically updates `accepted_by_both` if both parties have accepted.

---

### `DELETE /matches/{match_id}`
Deletes a match from the system.

**Path Parameters:**
- `match_id`: UUID of the match

**Status Code:** `204 No Content`

**Use case:** Remove expired or cancelled matches

---

### `GET /matches_individual/{person_id}`
Retrieves all matches associated with a specific person.

**Path Parameters:**
- `person_id`: UUID of the person (note: there's a typo in the code - parameter is named `mperson_id`)

**Response:** `MatchRead` object

**Use case:** User views their current matches and match history

---



## Data Models

All models are defined in `models.match` using Pydantic for validation and serialization.

### Availability Models

#### `AvailabilityBase`
Base model containing core availability fields:
- `person_id` (UUID): Unique identifier for the person
- `location` (str): Geographic or logical location for matching (e.g., "NYC", "SF")
- `time_added` (datetime): When the person became available (UTC, auto-generated)

#### `AvailabilityCreate`
Used when adding someone to the availability pool.
- Inherits all fields from `AvailabilityBase`
- Example: `{"person_id": "...", "location": "SF", "time_added": "2025-07-01T09:30:00Z"}`

#### `AvailabilityUpdate`
Partial update model - all fields optional:
- `person_id` (Optional[UUID]): Change the associated person
- `location` (Optional[str]): Update location
- `time_added` (Optional[datetime]): Adjust the timestamp
- Example: `{"location": "SF"}` (only update location)

#### `AvailabilityRemove`
Used when removing someone from the pool:
- `person_id` (UUID): Person to remove
- `id` (UUID): Internal record ID (auto-generated)
- `time_removed` (datetime): When removed (UTC, auto-generated)

#### `AvailabilityRead`
Full server representation returned by GET requests:
- All fields from `AvailabilityBase` plus:
- `id` (UUID): Server-generated record ID
- `updated_at` (datetime): Last modification timestamp (UTC)

#### `AvailabilityPoolBase`
Container for viewing all availabilities in a location:
- `location` (str): Location identifier
- `availabilities` (List[AvailabilityRead]): All active availabilities in that location

---

### Match Individual Models

These models represent one participant's side of a match.

#### `MatchIndividualBase`
Base model for a participant's match state:
- `id1` (UUID): This participant's person ID
- `id2` (UUID): The other participant's person ID
- `accepted` (Optional[bool]): Decision state
  - `None` = pending/no decision yet
  - `True` = accepted
  - `False` = rejected

#### `MatchIndividualCreate`
Used when creating a new match participant record:
- Inherits all fields from `MatchIndividualBase`
- Typically starts with `accepted=None` (pending)

#### `MatchIndividualUpdate`
Partial update for changing a participant's decision:
- `accepted` (Optional[bool]): New acceptance state
- Example: `{"accepted": True}` to accept a match

#### `MatchIndividualRead`
Full server representation of a participant's match state:
- All fields from `MatchIndividualBase` plus:
- `created_at` (datetime): When this decision record was created (UTC)
- `updated_at` (datetime): When last modified (UTC)

---

### Match Models

These models represent the complete match between two people.

#### `MatchBase`
Base model containing the core match structure:
- `match_id1` (MatchIndividualRead): First participant's decision record
- `match_id2` (MatchIndividualRead): Second participant's decision record
- `accepted_by_both` (bool): True only if both participants accepted (auto-calculated)

#### `MatchCreate`
Used when creating a new match:
- `match_id1` (MatchIndividualCreate): First participant's initial state
- `match_id2` (MatchIndividualCreate): Second participant's initial state
- Both typically start with `accepted=None`
- Example:
  ```json
  {
    "match_id1": {
      "id1": "22222222-2222-4222-8222-222222222222",
      "id2": "33333333-3333-4333-8333-333333333333",
      "accepted": null
    },
    "match_id2": {
      "id1": "33333333-3333-4333-8333-333333333333",
      "id2": "22222222-2222-4222-8222-222222222222",
      "accepted": null
    }
  }
  ```

#### `MatchUpdate`
Partial update for modifying match state - all fields optional:
- `match_id1` (Optional[MatchIndividualUpdate]): Update first participant's decision
- `match_id2` (Optional[MatchIndividualUpdate]): Update second participant's decision
- `accepted_by_both` (Optional[bool]): Override flag (usually auto-calculated)
- Example: `{"match_id1": {"accepted": true}}` to have participant 1 accept

#### `MatchRemove`
Used when deleting a match:
- Inherits from `MatchBase` plus:
- `match_id` (UUID): ID of the match to remove
- `time_removed` (datetime): When removed (UTC, auto-generated)

#### `MatchRead`
Full server representation returned by GET requests:
- All fields from `MatchBase` plus:
- `match_id` (UUID): Unique match identifier (server-generated)
- `created_at` (datetime): When the match was created (UTC)
- `updated_at` (datetime): When the match status last changed (UTC)
- Example of a fully accepted match:
  ```json
  {
    "match_id": "44444444-4444-4444-8444-444444444444",
    "match_id1": {
      "id1": "22222222-2222-4222-8222-222222222222",
      "id2": "33333333-3333-4333-8333-333333333333",
      "accepted": true,
      "created_at": "2025-06-01T10:05:00Z",
      "updated_at": "2025-06-01T10:10:00Z"
    },
    "match_id2": {
      "id1": "33333333-3333-4333-8333-333333333333",
      "id2": "22222222-2222-4222-8222-222222222222",
      "accepted": true,
      "created_at": "2025-06-01T10:06:00Z",
      "updated_at": "2025-06-01T10:11:00Z"
    },
    "accepted_by_both": true,
    "created_at": "2025-06-01T10:05:00Z",
    "updated_at": "2025-06-01T10:20:00Z"
  }
  ```

---

### Model Hierarchy Summary

```
Availability Models:
  AvailabilityBase (core fields)
    ├── AvailabilityCreate (for POST)
    └── AvailabilityRead (for GET, adds id + updated_at)
  AvailabilityUpdate (partial, all optional)
  AvailabilityRemove (for deletion tracking)
  AvailabilityPoolBase (container/aggregation)

Match Individual Models:
  MatchIndividualBase (participant state)
    ├── MatchIndividualCreate (for POST)
    └── MatchIndividualRead (for GET, adds timestamps)
  MatchIndividualUpdate (partial decision update)

Match Models:
  MatchBase (two participants + acceptance flag)
    ├── MatchCreate (for POST, uses MatchIndividualCreate)
    ├── MatchRead (for GET, adds match_id + timestamps)
    └── MatchRemove (for deletion tracking)
  MatchUpdate (partial, all optional)
```

## Implementation Notes

1. **All endpoints need implementation** - they currently raise `501 NOT IMPLEMENTED`
2. **Match acceptance flow** should work like:
   - Match is created with both participants' `accepted` status as `None`
   - Each participant calls `PATCH /matches/{match_id}/{person_id}?action=accept` 
   - System automatically sets `accepted_by_both=True` when both accept and removes the match if one rejects. 