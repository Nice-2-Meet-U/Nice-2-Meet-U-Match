# Resources Documentation - Nice 2 Meet U Match Service

## Overview
This document lists all API resources and their attributes organized by microservice/domain.

---

## 1. Pools Microservice
**Base Path:** `/pools`

### 1.1 Pool Resource

#### Attributes:
- **id** (UUID, read-only) - Unique pool identifier
- **name** (string, required) - Name of the pool
- **location** (string, optional) - Geographic location of the pool
- **member_count** (integer, read-only) - Number of members in the pool
- **created_at** (datetime, read-only) - Timestamp when pool was created

#### Endpoints:
- **POST /pools/** - Create a new pool
  - Request: `PoolCreate` (name, location)
  - Response: `PoolRead`
  
- **GET /pools/** - List all pools
  - Query Params: `location` (optional filter)
  - Response: `list[PoolRead]`
  
- **GET /pools/{pool_id}** - Get a specific pool
  - Response: `PoolRead`
  
- **PATCH /pools/{pool_id}** - Update pool (partial)
  - Request: `PoolPatch` (name, location - all optional)
  - Response: `PoolRead`
  
- **DELETE /pools/{pool_id}** - Delete a pool
  - Response: 204 No Content
  - Note: Cascades to members and matches

---

### 1.2 Pool Member Resource

#### Attributes:
- **pool_id** (UUID, required) - Pool the member belongs to
- **user_id** (string, required) - Unique user identifier
- **coord_x** (float, optional) - X coordinate of the user
- **coord_y** (float, optional) - Y coordinate of the user
- **joined_at** (datetime, read-only) - Timestamp when user joined the pool

#### Endpoints:
- **POST /pools/{pool_id}/members** - Add a user to a pool
  - Request: `PoolMemberCreate` (user_id, coord_x, coord_y)
  - Response: `PoolMemberRead`
  
- **GET /pools/{pool_id}/members** - List all members of a pool
  - Response: `list[PoolMemberRead]`
  
- **GET /pools/{pool_id}/members/{user_id}** - Get a specific pool member
  - Response: `PoolMemberRead`
  
- **GET /pools/members** - List all pool members across all pools
  - Query Params: `user_id` (optional filter)
  - Response: `list[PoolMemberRead]`
  
- **DELETE /pools/members/{user_id}** - Remove a user from their pool
  - Response: `PoolMemberDeleteResponse`
  - Note: Automatically finds which pool the user is in

---

## 2. Matches Microservice
**Base Path:** `/matches`

### 2.1 Match Resource

#### Attributes:
- **match_id** (UUID, read-only) - Unique match identifier
- **pool_id** (UUID, required) - Pool this match belongs to
- **user1_id** (UUID, required) - First participant
- **user2_id** (UUID, required) - Second participant
- **status** (enum, read-only) - Match status: `waiting`, `accepted`, `rejected`
- **created_at** (datetime, read-only) - When match was created
- **updated_at** (datetime, read-only) - When match was last updated

#### Endpoints:
- **POST /matches/** - Create a new match
  - Request: `MatchPost` (pool_id, user1_id, user2_id)
  - Response: `MatchGet`
  - Note: Status defaults to "waiting"
  
- **GET /matches/{match_id}** - Get a specific match
  - Response: `MatchGet`
  
- **GET /matches/** - List all matches
  - Query Params: 
    - `pool_id` (optional filter)
    - `user_id` (optional - filter matches where user is a participant)
    - `status_filter` (optional - filter by status)
  - Response: `list[MatchGet]`
  
- **PATCH /matches/{match_id}** - Update a match (partial)
  - Request: `MatchPatch` (pool_id, user1_id, user2_id, status - all optional)
  - Response: `MatchGet`
  - Note: Status is typically admin-only

---

### 2.2 Match Decision Resource

#### Attributes:
- **match_id** (UUID, required) - The match being decided on
- **user_id** (UUID, required) - User making the decision
- **decision** (enum, required) - Decision value: `accept` or `reject`
- **decided_at** (datetime, read-only) - When decision was made

#### Endpoints:
- **POST /matches/{match_id}/decisions** - Submit a decision for a match
  - Request: `DecisionPost` (match_id, user_id, decision)
  - Response: `DecisionGet`
  - Note: Updates match status based on both users' decisions
  
- **GET /matches/{match_id}/decisions** - List all decisions for a match
  - Response: `list[DecisionGet]`
  
- **GET /matches/{match_id}/decisions/{user_id}** - Get specific user's decision
  - Response: `DecisionGet`

---

## 3. User-Match Composite Microservice
**Base Path:** `/users`
**Note:** This is a composite service that orchestrates calls to Pools and Matches services

### 3.1 User Pool Operations

#### User Pool Info Attributes:
- **pool_id** (string) - Pool the user belongs to
- **pool_name** (string) - Name of the pool
- **location** (string, optional) - Location of the pool
- **member_count** (integer) - Total members in the pool
- **joined_at** (datetime) - When user joined
- **user_id** (string) - User identifier

#### Endpoints:
- **GET /users/{user_id}/pool** - Get user's pool information
  - Response: `UserPoolInfoResponse`
  
- **POST /users/{user_id}/pool** - Add user to a pool by location
  - Request: `UserPoolPost` (location, coord_x, coord_y)
  - Response: `UserPoolResponse`
  - Note: Creates new pool if none exist at location, or adds to existing pool
  
- **PATCH /users/{user_id}/pool** - Update user's coordinates in pool
  - Request: `UserPoolCoordinatesPatch` (coord_x, coord_y)
  - Response: `UserPoolInfoResponse`
  - Note: Currently not fully implemented
  
- **DELETE /users/{user_id}/pool** - Remove user from their pool
  - Response: `UserPoolDeleteResponse`
  - Note: Cascades to matches and decisions

---

### 3.2 User Pool Members

#### User Pool Members Attributes:
- **user_id** (string) - Requesting user's ID
- **members_count** (integer) - Number of members in the pool
- **members** (array) - List of pool member objects with:
  - pool_id
  - user_id
  - coord_x
  - coord_y
  - joined_at

#### Endpoints:
- **GET /users/{user_id}/pool/members** - Get all members in user's pool
  - Response: `UserPoolMembersResponse`

---

### 3.3 User Matches Operations

#### User Matches Attributes:
- **user_id** (string) - User identifier
- **matches_count** (integer) - Number of matches
- **matches** (array) - List of match objects

#### Generate Matches Attributes:
- **message** (string) - Status message
- **pool_id** (string) - Pool where matches were created
- **matches_created** (integer) - Number of matches created
- **matches** (array) - List of created match objects

#### Endpoints:
- **GET /users/{user_id}/matches** - Get all matches for a user
  - Response: `UserMatchesResponse`
  
- **POST /users/{user_id}/matches** - Generate random matches for user
  - Response: `GenerateMatchesResponse`
  - Note: Creates up to 10 random matches with other pool members

---

### 3.4 User Decisions Operations

#### User Decisions Attributes:
- **user_id** (string) - User identifier
- **decisions_count** (integer) - Number of decisions made
- **decisions** (array) - List of decision objects

#### Endpoints:
- **GET /users/{user_id}/decisions** - Get all decisions made by user
  - Response: `UserDecisionsResponse`
  
- **POST /users/{user_id}/matches/{match_id}/decisions** - Submit decision for a match
  - Request: `UserDecisionPost` (decision: "accept" or "reject")
  - Response: Decision object
  - Note: Validates user is participant in the match

---

## 4. Data Models Summary

### Enums:
- **MatchStatus**: `waiting`, `accepted`, `rejected`
- **DecisionValue**: `accept`, `reject`

### Key Relationships:
- **Pool → PoolMember** (one-to-many)
- **Pool → Match** (one-to-many)
- **Match → MatchDecision** (one-to-many)
- **PoolMember** has unique constraint on (pool_id, user_id)
- **Match** has unique constraint on (pool_id, user1_id, user2_id)
- **MatchDecision** has unique constraint on (match_id, user_id)

### Cascading Deletes:
- Deleting a **Pool** cascades to **PoolMembers** and **Matches**
- Deleting a **Match** cascades to **MatchDecisions**
- Deleting a **PoolMember** cascades to related **Matches** and **MatchDecisions**

---

## 5. Common Patterns

### Request/Response Models:
- **Base** - Shared fields
- **Create/Post** - Creation payload (excludes auto-generated fields)
- **Read/Get** - Full representation (includes all fields)
- **Patch** - Partial update (all fields optional)
- **Put** - Full replacement (rare, not used in current implementation)

### UUID vs String:
- Database uses **CHAR(36)** for UUIDs stored as strings
- API accepts and returns **UUID** type (validated by Pydantic)
- Some composite endpoints use **string** for user_id for flexibility

### Timestamps:
- All timestamps are **UTC**
- Created with `server_default=func.now()`
- Updated timestamps use `onupdate=func.now()`

---

## 6. Service Architecture Notes

### Atomic Services:
- **Pools Service** - Manages pools and pool members
- **Matches Service** - Manages matches and decisions

### Composite Service:
- **User-Match Service** - User-centric facade that orchestrates:
  - Pool operations
  - Match generation
  - Decision submission
  - Provides simplified user experience

### Service Communication:
- Uses HTTP REST calls between services
- Configurable via `POOLS_SERVICE_URL` environment variable
- Defaults to `http://localhost:8000` for local development
