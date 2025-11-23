# Composite Microservice Implementation

## Overview

This document describes how the `user_match` composite microservice satisfies the requirement to implement a composite microservice that encapsulates atomic microservices and enforces logical foreign key constraints.

## Requirement 1: Composite Microservice Implementation

### Atomic Microservices

The system consists of three atomic microservices:

1. **Pools Service** (`/pools`) - Manages pool resources and pool membership
2. **Matches Service** (`/matches`) - Manages match resources between users
3. **Decisions Service** (`/decisions`) - Manages user decisions (accept/reject) on matches

### Composite Microservice: User Match (`/users`)

The `user_match` composite microservice encapsulates and exposes functionality from all three atomic microservices through a unified, user-centric API.

#### Architecture

```
┌─────────────────────────────────────┐
│   Composite: user_match (/users)   │
│                                     │
│  - GET /{user_id}/pool             │
│  - POST /{user_id}/pool            │
│  - GET /{user_id}/pool-members     │
│  - GET /{user_id}/matches          │
│  - POST /{user_id}/matches         │
│  - GET /{user_id}/decisions        │
└─────────────────────────────────────┘
           │          │          │
           ▼          ▼          ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  Pools   │ │ Matches  │ │Decisions │
    │ Service  │ │ Service  │ │ Service  │
    └──────────┘ └──────────┘ └──────────┘
```

#### Delegation to Atomic Services

Each composite endpoint delegates to one or more atomic services:

| Composite Endpoint | Atomic Services Used | Operations |
|-------------------|---------------------|------------|
| `GET /users/{user_id}/pool` | Pools | 1. GET /pools (list all)<br>2. GET /pools/{pool_id}/members/{user_id} (for each pool) |
| `POST /users/{user_id}/pool` | Pools | 1. GET /pools?location={location}<br>2. POST /pools (if needed)<br>3. POST /pools/{pool_id}/members |
| `GET /users/{user_id}/pool-members` | Pools | 1. Reuse get_user_pool logic<br>2. GET /pools/{pool_id}/members |
| `GET /users/{user_id}/matches` | Matches | 1. GET /matches?user_id={user_id} |
| `POST /users/{user_id}/matches` | Pools, Matches | 1. Reuse get_user_pool logic<br>2. GET /pools/{pool_id}/members<br>3. POST /matches (multiple) |
| `GET /users/{user_id}/decisions` | Decisions | 1. GET /decisions?user_id={user_id} |

## Requirement 2: Logical Foreign Key Constraints

The composite microservice implements and enforces logical foreign key constraints across the atomic microservices to maintain referential integrity.

### Constraint 1: User Must Be Pool Member Before Generating Matches

**Implementation:** `generate_matches_for_user_service()`

```python
# Step 1: Validate user is in a pool (enforces FK: User → PoolMember)
user_pool_data = get_user_pool_from_service(user_id, pools_service_url)
pool_id = user_pool_data.get("pool_id")

if not pool_id:
    raise ValueError("User is not a member of any pool. Add user to a pool first.")
```

**Constraint Enforced:**
- Logical FK: `Match.user1_id` → `PoolMember.user_id`
- Logical FK: `Match.user2_id` → `PoolMember.user_id`
- **Business Rule:** Matches can only be created between users who are members of the same pool

**Why This Matters:**
The atomic Matches service does not know about pools or pool membership. The composite service enforces this cross-service constraint by validating pool membership before creating matches.

---

### Constraint 2: Only Pool Members Can Access Same-Pool Members

**Implementation:** `get_pool_members_from_service()`

```python
# Step 1: Verify user is a pool member (enforces FK: User → PoolMember)
user_pool_data = get_user_pool_from_service(user_id, pools_service_url)
pool_id = user_pool_data.get("pool_id")

if not pool_id:
    raise ValueError("User is not a member of any pool")

# Step 2: Only then retrieve members of that pool
members_response = requests.get(f"{pools_service_url}/pools/{pool_id}/members")
```

**Constraint Enforced:**
- Logical FK: `User` → `PoolMember.user_id`
- **Business Rule:** Only users who are pool members can query other members

**Why This Matters:**
Prevents unauthorized access to pool member information. The atomic Pools service doesn't validate requester identity; the composite service adds this authorization layer.

---

### Constraint 3: User-Pool Relationship Validation

**Implementation:** `get_user_pool_from_service()`

```python
# Search through all pools to find which one contains this user
pools_response = requests.get(f"{pools_service_url}/pools")
all_pools = pools_response.json()

user_pool = None
user_member = None

# Validate FK: PoolMember.pool_id → Pool.id AND User → PoolMember
for pool in all_pools:
    member_response = requests.get(
        f"{pools_service_url}/pools/{pool['id']}/members/{user_id}"
    )
    if member_response.status_code == 200:
        user_member = member_response.json()
        user_pool = pool
        break

if not user_pool or not user_member:
    raise ValueError("User is not a member of any pool")
```

**Constraint Enforced:**
- Logical FK: `PoolMember.pool_id` → `Pool.id`
- Logical FK: `User` → `PoolMember.user_id`
- **Business Rule:** User must exist as a member in exactly one pool

**Why This Matters:**
Validates the integrity of the user-pool relationship across multiple service calls. Ensures data consistency that individual atomic services cannot guarantee.

---

### Constraint 4: Match Participants Must Be in Same Pool

**Implementation:** `generate_matches_for_user_service()`

```python
# Get all members of the user's pool
members_response = requests.get(f"{pools_service_url}/pools/{pool_id}/members")
pool_members = members_response.json()

# Only create matches with other members of the same pool
other_members = [
    member for member in pool_members if member.get("user_id") != str(user_id)
]

# Create matches only between pool members
for member in selected_members:
    match_response = requests.post(
        f"{matches_service_url}/matches",
        json={
            "pool_id": pool_id,
            "user1_id": str(user_id),
            "user2_id": member.get("user_id"),
        },
    )
```

**Constraint Enforced:**
- Logical FK: `Match.pool_id` → `Pool.id`
- Logical FK: `Match.user1_id` → `PoolMember.user_id` (WHERE `pool_id` = `Match.pool_id`)
- Logical FK: `Match.user2_id` → `PoolMember.user_id` (WHERE `pool_id` = `Match.pool_id`)
- **Business Rule:** Both users in a match must be members of the same pool

**Why This Matters:**
The Matches service doesn't validate that users belong to the specified pool. The composite service enforces this multi-table constraint by only selecting match partners from the verified pool member list.

---

## Summary of Logical FK Constraints

| Constraint | Services Involved | Enforcement Point | Validation Method |
|-----------|------------------|-------------------|-------------------|
| User → PoolMember | Pools | All user operations | Check membership exists |
| PoolMember → Pool | Pools | get_user_pool | Verify pool exists for member |
| Match.user1_id → PoolMember | Pools + Matches | generate_matches | Pre-validate pool membership |
| Match.user2_id → PoolMember | Pools + Matches | generate_matches | Filter to pool members only |
| Match.pool_id → Pool | Pools + Matches | generate_matches | Use validated pool_id |

## Benefits of This Architecture

1. **Separation of Concerns**: Atomic services remain simple and focused on their domain
2. **Data Integrity**: Composite service enforces cross-service constraints
3. **Encapsulation**: Clients interact with a single, coherent API
4. **Flexibility**: Atomic services can be reused in other compositions
5. **Validation Layer**: Business rules are enforced at the composition level

## Code References

- **Composite Router**: `resources/user_match.py`
- **Composite Service Logic**: `services/user_match_service.py`
- **Composite Models**: `models/user_match.py`
- **Atomic Services**: `resources/pools.py`, `resources/matches.py`, `resources/decisions.py`
