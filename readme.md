# Architecture Overview

## Microservices

### Pools Service
Manages location-based user pools. Users join pools by location, enabling them to be matched with nearby participants. The service handles pool creation, user membership, and coordinates for spatial matching.

### Matches Service
Creates and manages pairwise matches between users within the same pool. Tracks match status based on participant decisions. Handles automated cleanup of non-accepted matches through event-driven architecture.

### User-Match Composite Service
Aggregates operations across pools and matches services to provide user-centric workflows. Simplifies common operations by combining multiple service calls into single composite endpoints.

## Database Models

### Pool
Represents a location-based group of users.

```python
class Pool(Base):
    __tablename__ = "pools"
    id: UUID (primary key)
    name: str
    location: str (nullable)
    member_count: int (default: 0)
    created_at: timestamp
```

**Relationships:**
- One-to-many with PoolMember
- One-to-many with Match
- Cascade delete to members and matches

### PoolMember
Links users to pools with optional coordinate data.

```python
class PoolMember(Base):
    __tablename__ = "pool_members"
    pool_id: UUID (primary key, foreign key to Pool)
    user_id: UUID (primary key)
    coord_x: float (nullable)
    coord_y: float (nullable)
    joined_at: timestamp
```

**Constraints:**
- Composite primary key: (pool_id, user_id)
- Cascade delete when pool is deleted

### Match
Represents a potential match between two users.

```python
class Match(Base):
    __tablename__ = "matches"
    match_id: UUID (primary key)
    pool_id: UUID (foreign key to Pool)
    user1_id: UUID
    user2_id: UUID
    status: str ("waiting" | "accepted" | "rejected")
    created_at: timestamp
    updated_at: timestamp
```

**Constraints:**
- Unique constraint: (pool_id, user1_id, user2_id)
- User pairs are normalized (user1_id < user2_id)
- Cascade delete when pool is deleted
- **CRITICAL**: UUIDs stored as CHAR(36) - database queries must convert UUID objects to strings using `str(uuid)`

**Relationships:**
- Many-to-one with Pool
- One-to-many with MatchDecision

**Status Logic:**
- `waiting`: Initial state, awaiting decisions
- `accepted`: Both users accepted
- `rejected`: At least one user rejected

### MatchDecision
Records individual user decisions on matches.

```python
class MatchDecision(Base):
    __tablename__ = "match_decisions"
    match_id: UUID (primary key, foreign key to Match)
    user_id: UUID (primary key)
    decision: str ("accept" | "reject")
    decided_at: timestamp
```

**Constraints:**
- Composite primary key: (match_id, user_id)
- Unique constraint: (match_id, user_id)
- Cascade delete when match is deleted

**Relationships:**
- Many-to-one with Match

## Pydantic Models

### Pool Models

**PoolBase**
```python
name: str
location: Optional[str]
```

**PoolCreate** (POST)
- Inherits from PoolBase

**PoolPatch** (PATCH)
```python
name: Optional[str]
location: Optional[str]
```

**PoolRead** (GET)
```python
id: UUID
name: str
location: Optional[str]
member_count: int
created_at: datetime
```

### Pool Member Models

**PoolMemberCreate** (POST)
```python
user_id: str
coord_x: Optional[float]
coord_y: Optional[float]
```

**PoolMemberRead** (GET)
```python
pool_id: UUID
user_id: str
coord_x: Optional[float]
coord_y: Optional[float]
joined_at: datetime
```

### Match Models

**MatchBase**
```python
pool_id: UUID
user1_id: UUID
user2_id: UUID
```

**MatchPost** (POST)
- Inherits from MatchBase
- Status automatically set to "waiting"

**MatchPatch** (PATCH)
```python
pool_id: Optional[UUID]
user1_id: Optional[UUID]
user2_id: Optional[UUID]
status: Optional[MatchStatus]
```

**MatchGet** (GET)
```python
match_id: UUID
pool_id: UUID
user1_id: UUID
user2_id: UUID
status: MatchStatus
created_at: datetime
updated_at: datetime
```

### Decision Models

**DecisionBase**
```python
match_id: UUID
user_id: UUID
decision: DecisionValue ("accept" | "reject")
```

**DecisionPost** (POST)
- Inherits from DecisionBase
- Triggers match status recalculation

**DecisionGet** (GET)
```python
match_id: UUID
user_id: UUID
decision: DecisionValue
decided_at: datetime
```

### User-Match Composite Models

**UserPoolCreate** (POST)
```python
location: str
coord_x: Optional[float]
coord_y: Optional[float]
```

**UserPoolRead** (GET)
```python
pool_id: str
pool_name: str
location: Optional[str]
member_count: int
joined_at: datetime
user_id: str
```

**UserPoolUpdate** (PATCH)
```python
coord_x: Optional[float]
coord_y: Optional[float]
```

**UserMatchesRead** (GET)
```python
user_id: str
matches_count: int
matches: List[Any]
```

**UserDecisionCreate** (POST)
```python
decision: str ("accept" | "reject")
```

**UserDecisionsRead** (GET)
```python
user_id: str
decisions_count: int
decisions: List[Any]
```

**UserPoolMembersRead** (GET)
```python
user_id: str
members_count: int
members: List[Any]
```

**GenerateMatchesResponse** (POST)
```python
message: str
pool_id: str
matches_created: int
matches: List[Any]
```

## Service Layer Logic

### Pool Service
- Creates pools with configurable locations
- Manages pool membership with coordinate tracking
- Maintains member count through database triggers or updates
- Publishes events when members leave pools

### Match Service
- Creates matches with automatic user ID normalization
- Validates both users are pool members
- Enforces uniqueness per pool-user pair
- Computes match status based on decisions
- Supports filtered queries by pool, user, or status

### Decision Service
- Records user acceptance/rejection decisions
- Automatically recalculates match status
- Ensures one decision per user per match
- Updates match timestamps on decision changes

### User-Match Service
- Aggregates pool and match operations
- Automatically assigns users to non-full pools
- Creates new pools when necessary
- Generates matches for pool members
- Provides unified view of user data across services

### Match Cleanup Service
- Deletes non-accepted matches when users leave pools
- Preserves accepted matches
- Triggered by Pub/Sub events on topic `user_left_pool`
- Executes via Cloud Function (match-cleanup-handler)
- Called by Cloud Function via HTTP: `DELETE /matches/internal/cleanup/user/{user_id}/pool/{pool_id}`

## Event-Driven Architecture

### Event Flow
1. User leaves pool via `DELETE /users/{user_id}/pool`
2. User-Match Service calls Pools Service to remove member
3. User-Match Service publishes `pool_member_removed` event to Pub/Sub topic `user_left_pool`
4. Cloud Function `match-cleanup-handler` receives event
5. Cloud Function calls Matches Service cleanup endpoint
6. Matches Service deletes non-accepted matches and associated decisions

### Pub/Sub Configuration
- **Topic**: `user_left_pool`
- **Event Type**: `pool_member_removed`
- **Project**: `cloudexploration-477701`
- **Cloud Function**: Gen2, Python 3.11, Region: us-central1

### Event Payload
```json
{
  "event_type": "pool_member_removed",
  "pool_id": "uuid-string",
  "user_id": "uuid-string",
  "timestamp": "ISO-8601-datetime"
}
```



# API Endpoints

## Pools Service

Base path: `/pools`

**Note on Trailing Slashes**: Routes with query parameters use trailing slashes (e.g., `/pools/?location=`). Collection POST endpoints use trailing slashes (`/pools/`). Sub-resource endpoints do not use trailing slashes (e.g., `/pools/{id}/members`).

### Pool Management

**POST /pools/**
- Creates a new pool
- Request: `PoolCreate` (name, location)
- Response: `PoolRead` (201)
- Initializes member_count to 0

**GET /pools/?location={location}**
- Lists all pools with optional location filter
- Query params: `location` (optional)
- Response: `List[PoolRead]` (200)
- Ordered by creation date descending

**GET /pools/{pool_id}**
- Retrieves a specific pool by ID
- Path params: `pool_id` (UUID)
- Response: `PoolRead` (200)
- Error: 404 if pool not found

**PATCH /pools/{pool_id}**
- Partially updates pool fields
- Path params: `pool_id` (UUID)
- Request: `PoolPatch` (name, location - all optional)
- Response: `PoolRead` (200)
- Error: 404 if pool not found

**DELETE /pools/{pool_id}**
- Deletes a pool and cascades to members and matches
- Path params: `pool_id` (UUID)
- Response: 204 No Content
- Error: 404 if pool not found

### Pool Member Management

**POST /pools/{pool_id}/members**
- Adds a user to a pool
- Path params: `pool_id` (UUID)
- Request: `PoolMemberCreate` (user_id, coord_x, coord_y)
- Response: `PoolMemberRead` (201)
- Increments pool member_count
- Publishes event on success
- Error: 400 if user already in pool or pool not found

**GET /pools/{pool_id}/members**
- Lists all members of a specific pool
- Path params: `pool_id` (UUID)
- Response: `List[PoolMemberRead]` (200)
- Error: 404 if pool not found

**GET /pools/{pool_id}/members/{user_id}**
- Retrieves a specific pool member
- Path params: `pool_id` (UUID), `user_id` (UUID)
- Response: `PoolMemberRead` (200)
- Error: 404 if member not found

**GET /pools/members?user_id={user_id}**
- Lists all pool members across all pools
- Query params: `user_id` (optional UUID) - filter by user
- Response: `List[PoolMemberRead]` (200)
- Used to find which pool a user belongs to

**DELETE /pools/members/{user_id}**
- Removes a user from their pool (finds pool automatically)
- Path params: `user_id` (UUID)
- Response: `PoolMemberDeleteResponse` (200)
- Decrements pool member_count
- **CRITICAL**: Converts UUID to string for database query using `str(user_id)`
- Does NOT publish events directly (composite service handles event publishing)
- Error: 404 if user not in any pool

## Matches Service

Base path: `/matches`

**Note on Trailing Slashes**: Routes with query parameters use trailing slashes (e.g., `/matches/?user_id=`). Collection POST endpoints use trailing slashes (`/matches/`). Sub-resource endpoints do not use trailing slashes (e.g., `/matches/{id}/decisions`).

### Match Management

**POST /matches/**
- Creates a new match between two users
- Request: `MatchPost` (pool_id, user1_id, user2_id)
- Response: `MatchGet` (201)
- Validates both users are pool members
- Normalizes user order (user1_id < user2_id)
- Sets initial status to "waiting"
- Enforces uniqueness per pool-user pair
- Error: 400 if same user, 409 if duplicate match, 503 if database unavailable

**GET /matches/{match_id}**
- Retrieves a specific match
- Path params: `match_id` (UUID)
- Response: `MatchGet` (200)
- Error: 404 if match not found

**GET /matches/?user_id={user_id}&pool_id={pool_id}&status_filter={status}**
- Lists matches with optional filters
- Query params:
  - `pool_id` (optional UUID)
  - `user_id` (optional UUID) - matches where user is participant
  - `status_filter` (optional MatchStatus)
- Response: `List[MatchGet]` (200)
- Ordered by creation date descending

**PATCH /matches/{match_id}**
- Partially updates a match
- Path params: `match_id` (UUID)
- Request: `MatchPatch` (pool_id, user1_id, user2_id, status - all optional)
- Response: `MatchGet` (200)
- Typically used for admin status overrides
- Error: 404 if match not found

### Match Decision Management

**POST /matches/{match_id}/decisions**
- Submits a user decision for a match
- Path params: `match_id` (UUID)
- Request: `DecisionPost` (match_id, user_id, decision)
- Response: `DecisionGet` (201)
- Validates user is match participant
- Upserts decision (updates if exists)
- Automatically recalculates match status:
  - Both accept → status = "accepted"
  - Any reject → status = "rejected"
  - Otherwise → status = "waiting"
- Error: 400 if match_id mismatch, 403 if user not participant, 404 if match not found

**GET /matches/{match_id}/decisions**
- Lists all decisions for a match
- Path params: `match_id` (UUID)
- Response: `List[DecisionGet]` (200)

**GET /matches/{match_id}/decisions/{user_id}**
- Retrieves a specific user's decision for a match
- Path params: `match_id` (UUID), `user_id` (UUID)
- Response: `DecisionGet` (200)
- Error: 404 if decision not found

### Internal Cleanup Endpoints

**DELETE /matches/internal/cleanup/user/{user_id}/pool/{pool_id}**
- Cleans up non-accepted matches when user leaves pool
- Path params: `user_id` (UUID), `pool_id` (UUID)
- Response: `CleanupResponse` with statistics (deleted_matches, deleted_decisions)
- **Called by Cloud Function** `match-cleanup-handler` via HTTP request
- Triggered by Pub/Sub event on topic `user_left_pool`
- Deletes matches where:
  - User is participant (user1_id or user2_id)
  - Match is in specified pool
  - Status is "waiting" or "rejected" (preserves "accepted" matches)
- Cascade deletes associated decisions
- No authentication required (internal endpoint)

### Utility Endpoints

**GET /matches/db-ping**
- Database health check
- Response: `{"ok": true}` (200)

## User-Match Composite Service

Base path: `/users`

### User Pool Operations

**GET /users/{user_id}/pool**
- Gets user's pool information
- Path params: `user_id` (UUID)
- Response: `UserPoolRead` (200)
- Aggregates pool and membership data
- Error: 404 if user not in any pool, 502 if service unavailable

**POST /users/{user_id}/pool**
- Adds user to a pool by location
- Path params: `user_id` (UUID)
- Request: `UserPoolCreate` (location, coord_x, coord_y)
- Response: `UserPoolResponse` (201)
- Finds existing non-full pool or creates new one
- Max pool size: 20 members
- Randomly selects pool if multiple available
- Error: 400 for invalid data, 502 if service unavailable

**PATCH /users/{user_id}/pool**
- Updates user's coordinates in pool
- Path params: `user_id` (UUID)
- Request: `UserPoolUpdate` (coord_x, coord_y)
- Response: `UserPoolRead` (200)
- Error: 501 not implemented, 404 if user not in pool

**DELETE /users/{user_id}/pool**
- Removes user from their pool
- Path params: `user_id` (UUID)
- Response: `UserPoolDelete` (200)
- **Triggers Pub/Sub event**: Publishes `pool_member_removed` to topic `user_left_pool`
- **Event-driven cleanup**: Cloud Function receives event and deletes non-accepted matches
- Workflow: Call Pools Service → Publish event → Return response (async cleanup)
- Error: 404 if user not in pool, 502 if service unavailable

### User Pool Member Operations

**GET /users/{user_id}/pool/members**
- Lists all members in user's pool
- Path params: `user_id` (UUID)
- Response: `UserPoolMembersRead` (200)
- Returns members excluding the requesting user
- Error: 404 if user not in pool, 502 if service unavailable

### User Match Operations

**GET /users/{user_id}/matches**
- Lists all matches for a user
- Path params: `user_id` (UUID)
- Response: `UserMatchesRead` (200)
- Includes matches_count and full match objects
- Error: 502 if service unavailable

**POST /users/{user_id}/matches**
- Generates random matches for user with pool members
- Path params: `user_id` (UUID)
- Response: `GenerateMatchesResponse` (201)
- Creates up to 10 matches
- Selects random pool members
- Skips existing matches
- Returns created match objects and count
- Error: 404 if user not in pool, 502 if service unavailable

### User Decision Operations

**GET /users/{user_id}/decisions**
- Lists all decisions made by user
- Path params: `user_id` (UUID)
- Response: `UserDecisionsRead` (200)
- Includes decisions_count and full decision objects
- Error: 502 if service unavailable

**POST /users/{user_id}/matches/{match_id}/decisions**
- Submits decision for a match on behalf of user
- Path params: `user_id` (UUID), `match_id` (UUID)
- Request: `UserDecisionCreate` (decision: "accept" | "reject")
- Response: Decision confirmation (201)
- Delegates to matches service decision endpoint
- Error: 400 for invalid data, 403 if user not participant, 502 if service unavailable

## HTTP Status Codes

**Success:**
- 200 OK - Successful GET, PATCH, DELETE with content
- 201 Created - Successful POST
- 204 No Content - Successful DELETE without content

**Client Errors:**
- 400 Bad Request - Invalid input data
- 403 Forbidden - User not authorized for action
- 404 Not Found - Resource does not exist
- 409 Conflict - Duplicate resource

**Server Errors:**
- 500 Internal Server Error - Unexpected server error
- 501 Not Implemented - Feature not yet available
- 502 Bad Gateway - Downstream service error
- 503 Service Unavailable - Database connection failed

## Query Parameter Conventions

- Filters are optional and use snake_case
- UUIDs validated automatically
- Multiple filters combined with AND logic
- Empty results return empty arrays, not errors

## Event Publishing

**pool_member_removed**
- **Triggered by**: `DELETE /users/{user_id}/pool` (User-Match composite service)
- **Topic**: `user_left_pool`
- **Payload**: `{event_type, pool_id, user_id, timestamp}`
- **Handler**: Cloud Function `match-cleanup-handler` → `DELETE /matches/internal/cleanup/user/{user_id}/pool/{pool_id}`
- **Publisher**: User-Match Service (`services/event_publisher.py`)
- **Environment**: Requires `GCP_PROJECT_ID` and Pub/Sub topic configured

## Cross-Service Communication

User-Match composite service aggregates data from:
- Pools service: Pool and member operations
- Matches service: Match and decision operations

**Service URLs**:
- **Production**: `https://matches-service-s556fwc6ua-uc.a.run.app`
- **Local**: `http://localhost:8000`
- **Configuration**: Set via `POOLS_SERVICE_URL` environment variable
- **Note**: In production, all services are deployed as a single Cloud Run service

**Trailing Slash Rules**:
- Collection GET with query params: `/pools/?location=`, `/matches/?user_id=`
- Collection POST: `/pools/`, `/matches/`
- Sub-resources: `/pools/{id}/members`, `/matches/{id}/decisions` (no trailing slash)
- FastAPI redirects (307) if trailing slash is incorrect, converting POST to GET

## Deployment

### Technology Stack
- **Platform**: Google Cloud Run
- **Database**: Cloud SQL (MySQL 8.0)
- **Instance**: `cloudexploration-477701:us-central1:matches-db`
- **Runtime**: Python 3.11
- **Container**: Multi-stage Docker build (python:3.11 → python:3.11-slim)
- **Package Manager**: uv with lock file
- **Events**: Google Cloud Pub/Sub + Cloud Functions Gen2

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `INSTANCE_CONNECTION_NAME` | Cloud SQL connection name | Yes |
| `DB_USER` | Database username (default: root) | Yes |
| `DB_PASS` | Database password | Yes |
| `DB_NAME` | Database name (default: matches) | Yes |
| `POOLS_SERVICE_URL` | Service URL (same as deployed URL) | Yes |
| `GCP_PROJECT_ID` | Google Cloud project ID | Yes (for events) |

### Deployment Commands

**Deploy Main Service**:
```bash
# Using deployment script (recommended)
./deploy.sh

# Manual deployment
gcloud run deploy matches-service \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances cloudexploration-477701:us-central1:matches-db \
  --set-env-vars INSTANCE_CONNECTION_NAME=cloudexploration-477701:us-central1:matches-db,\
DB_USER=root,\
DB_PASS=<password>,\
DB_NAME=matches,\
POOLS_SERVICE_URL=https://matches-service-s556fwc6ua-uc.a.run.app
```

**Deploy Cloud Function**:
```bash
# Create Pub/Sub topic (first time only)
gcloud pubsub topics create user_left_pool

# Deploy Cloud Function
gcloud functions deploy match-cleanup-handler \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./cloud_functions \
  --entry-point=handle_pool_event \
  --trigger-topic=user_left_pool \
  --set-env-vars=MATCHES_SERVICE_URL=https://matches-service-s556fwc6ua-uc.a.run.app
```

### Current Deployment Status
- **Service**: matches-service-00076-rnp
- **Cloud Function**: match-cleanup-handler-00015-kon
- **Service URL**: https://matches-service-s556fwc6ua-uc.a.run.app
- **Region**: us-central1
- **Status**: Active and operational

## Documentation

See `additional/notes/` directory for detailed documentation:
- `EVENTS_ARCHITECTURE.md` - Event-driven architecture and Pub/Sub flow
- `RESOURCES_DOCUMENTATION.md` - Complete API reference with all endpoints
- `DEPLOYMENT.md` - Detailed deployment guide with troubleshooting
- `TESTING_GUIDE.md` - Testing procedures and example workflows
- `COMPOSITE_MICROSERVICE.md` - User-Match composite service design
