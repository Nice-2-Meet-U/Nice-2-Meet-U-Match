# Decisions Refactoring: Nested Under Matches

## Overview

Decisions have been moved from a standalone resource (`/decisions`) to a nested resource under matches (`/matches/{match_id}/decisions`). This refactoring improves REST semantics and better represents the tight coupling between decisions and matches.

## Rationale

### Why Move Decisions Under Matches?

1. **Database Relationship**: `MatchDecision` has a foreign key to `Match.id`, making decisions inherently dependent on matches
2. **REST Best Practices**: Decisions are sub-resources of matches in the domain model
3. **Improved Semantics**: The URL structure now clearly shows the hierarchy: matches contain decisions
4. **Atomic Operations**: Decision submission updates match status, reinforcing their tight coupling

## API Changes

### Before (Old Endpoints)

```http
POST /decisions
GET /decisions?match_id={match_id}
GET /decisions?user_id={user_id}
```

### After (New Endpoints)

#### Match-Specific Decision Endpoints (Primary)

```http
POST /matches/{match_id}/decisions
GET /matches/{match_id}/decisions
GET /matches/{match_id}/decisions/{user_id}
```

#### User-Specific Decision Endpoint (Composite Service)

```http
GET /users/{user_id}/decisions
```

#### Legacy Endpoint (Deprecated)

```http
GET /decisions?user_id={user_id}
```

This endpoint is kept for backward compatibility but should be considered deprecated. Use `/users/{user_id}/decisions` instead.

## Implementation Details

### File Structure

```
resources/
├── matches.py          # Now contains decision endpoints
├── decisions.py        # Minimal - only user-specific query
└── user_match.py       # Composite service - unchanged

services/
├── decision_service.py # Business logic - unchanged
└── user_match_service.py # Calls /decisions?user_id=x

models/
└── decisions.py        # Request/response models - unchanged
```

### Endpoint Mapping

| New Endpoint | Purpose | Request Body | Query Params |
|--------------|---------|--------------|--------------|
| `POST /matches/{match_id}/decisions` | Submit decision for a match | `DecisionPost` | - |
| `GET /matches/{match_id}/decisions` | List all decisions for a match | - | - |
| `GET /matches/{match_id}/decisions/{user_id}` | Get specific user's decision | - | - |
| `GET /users/{user_id}/decisions` | Get all decisions by user | - | - |
| `GET /decisions` | **[Deprecated]** User decisions | - | `user_id` (required) |

### Request/Response Models

#### DecisionPost

```python
{
  "match_id": "uuid",
  "user_id": "uuid", 
  "decision": "accept" | "reject"
}
```

**Note**: When using `POST /matches/{match_id}/decisions`, the `match_id` in the request body must match the URL parameter.

#### DecisionGet

```python
{
  "match_id": "uuid",
  "user_id": "uuid",
  "decision": "accept" | "reject",
  "decided_at": "timestamp"
}
```

## Coherence with Architecture

### Maintains Microservice Patterns

1. **Atomic Services**: 
   - `matches` service handles match-specific decision operations
   - `decisions` service provides user-centric queries (deprecated path)

2. **Composite Service**:
   - `user_match` calls `/decisions?user_id={user_id}` for user-specific queries
   - Provides clean `/users/{user_id}/decisions` interface

3. **Separation of Concerns**:
   - Match-centric operations: `/matches/{match_id}/decisions`
   - User-centric operations: `/users/{user_id}/decisions`
   - Cross-service logic: handled by composite service

### Database Integrity Preserved

- FK constraint validation in `submit_decision` unchanged
- Atomic match status updates still enforced
- User must be match participant (validation preserved)

### Type Safety Maintained

All endpoints continue using Pydantic models:
- Input validation via `DecisionPost`
- Output serialization via `DecisionGet`
- No breaking changes to model definitions

## Migration Guide

### For API Consumers

#### Submitting Decisions

**Before:**
```bash
POST /decisions
{
  "match_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "987f6543-e21c-34d5-b789-426614174111",
  "decision": "accept"
}
```

**After:**
```bash
POST /matches/123e4567-e89b-12d3-a456-426614174000/decisions
{
  "match_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "987f6543-e21c-34d5-b789-426614174111",
  "decision": "accept"
}
```

#### Getting Match Decisions

**Before:**
```bash
GET /decisions?match_id=123e4567-e89b-12d3-a456-426614174000
```

**After:**
```bash
GET /matches/123e4567-e89b-12d3-a456-426614174000/decisions
```

#### Getting User Decisions

**Before:**
```bash
GET /decisions?user_id=987f6543-e21c-34d5-b789-426614174111
```

**After (Preferred - Composite Service):**
```bash
GET /users/987f6543-e21c-34d5-b789-426614174111/decisions
```

**After (Backward Compatible - Deprecated):**
```bash
GET /decisions?user_id=987f6543-e21c-34d5-b789-426614174111
```

### Breaking Changes

None - all functionality preserved. The old `/decisions` endpoint still exists for user queries but is deprecated.

## Testing Considerations

### Unit Tests

No changes needed to `decision_service.py` logic - all business rules preserved.

### Integration Tests

Update test URLs:
- Match decision submission: use `/matches/{match_id}/decisions`
- Match decision listing: use `/matches/{match_id}/decisions`
- User decision listing: use `/users/{user_id}/decisions` or `/decisions?user_id=x`

### Validation Scenarios

1. **Match ID Consistency**: Verify POST request rejects mismatched match_id between URL and body
2. **User Authorization**: Verify user must be match participant
3. **Match Status Updates**: Verify decisions trigger atomic status changes
4. **Composite Service**: Verify `/users/{user_id}/decisions` calls `/decisions` correctly

## Benefits of This Refactoring

1. **Clearer API Hierarchy**: URL structure matches domain model
2. **Better REST Semantics**: Nested resources properly represented
3. **Improved Discoverability**: Decision endpoints logically grouped under matches
4. **Maintained Coherence**: Composite service pattern preserved
5. **Backward Compatible**: Deprecated endpoint available during transition

## Future Considerations

- Remove `/decisions` endpoint entirely in v2.0
- Consider adding `/users/{user_id}/matches/{match_id}/decisions` for extra specificity
- Add pagination to decision lists when datasets grow large
