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
- Triggered by Pub/Sub events
- Executes via Cloud Function
