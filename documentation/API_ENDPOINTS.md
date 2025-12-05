# API Endpoints

## Pools Service

Base path: `/pools`

### Pool Management

**POST /pools/**
- Creates a new pool
- Request: `PoolCreate` (name, location)
- Response: `PoolRead` (201)
- Initializes member_count to 0

**GET /pools/**
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

**GET /pools/members**
- Lists all pool members across all pools
- Query params: `user_id` (optional UUID) - filter by user
- Response: `List[PoolMemberRead]` (200)
- Used to find which pool a user belongs to

**DELETE /pools/members/{user_id}**
- Removes a user from their pool (finds pool automatically)
- Path params: `user_id` (UUID)
- Response: `PoolMemberDeleteResponse` (200)
- Decrements pool member_count
- Publishes `pool_member_removed` event to Pub/Sub
- Error: 404 if user not in any pool

## Matches Service

Base path: `/matches`

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

**GET /matches/**
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
- Response: Statistics (deleted_matches, deleted_decisions)
- Called by Cloud Function via Pub/Sub trigger
- Deletes matches where:
  - User is participant
  - Match is in specified pool
  - Status is "waiting" or "rejected" (keeps "accepted")
- Cascade deletes associated decisions

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
- Response: `UserPoolInfoResponse` (200)
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
- Response: `UserPoolInfoResponse` (200)
- Error: 501 not implemented, 404 if user not in pool

**DELETE /users/{user_id}/pool**
- Removes user from their pool
- Path params: `user_id` (UUID)
- Response: `UserPoolDeleteResponse` (200)
- Triggers Pub/Sub event for match cleanup
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
- Triggered: DELETE /pools/members/{user_id}
- Topic: `user_left_pool`
- Payload: `{event_type, pool_id, user_id}`
- Handler: Cloud Function → DELETE /matches/internal/cleanup

## Cross-Service Communication

User-Match composite service aggregates data from:
- Pools service: Pool and member operations
- Matches service: Match and decision operations

Default service URL: `http://localhost:8000` (configurable via `POOLS_SERVICE_URL`)
