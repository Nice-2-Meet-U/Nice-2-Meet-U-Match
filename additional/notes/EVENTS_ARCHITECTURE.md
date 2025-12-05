# Event-Driven Architecture for Match Cleanup

## Overview
This system uses Google Cloud Pub/Sub to implement an event-driven architecture where the Pools service publishes events and the Matches service subscribes to clean up non-accepted matches.

## Architecture

```
┌─────────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  User-Match Service │ ─────> │  Google Cloud    │ ─────> │ Cloud Function  │
│  (DELETE /users/    │ publish │    Pub/Sub       │ trigger│  match-cleanup- │
│   {id}/pool)        │         │  (user_left_pool)│         │    handler      │
└─────────────────────┘         └──────────────────┘         └────────┬────────┘
                                                                       │ HTTP DELETE
                                                                       ▼
                                                              ┌─────────────────┐
                                                              │ Matches Service │
                                                              │ /matches/       │
                                                              │  internal/      │
                                                              │   cleanup       │
                                                              └─────────────────┘
```

## Components

### 1. Event Publisher (`services/event_publisher.py`)
- **Location**: User-Match Service
- **Purpose**: Publishes events to Google Cloud Pub/Sub
- **Events Published**:
  - `pool_member_removed`: When a user leaves a pool (DELETE /users/{user_id}/pool)

**Configuration**:
```bash
# Environment variables
GCP_PROJECT_ID=cloudexploration-477701
PUBSUB_TOPIC=user_left_pool
```

### 2. Match Cleanup Service (`services/match_cleanup_service.py`)
- **Location**: Matches Service / Cloud Function
- **Purpose**: Business logic for cleaning up matches
- **Functions**:
  - `cleanup_user_matches()`: Deletes non-accepted matches for a user
  - `cleanup_pool_matches()`: Deletes all non-accepted matches in a pool

**Cleanup Logic**:
- ✅ **Keeps**: Matches with status = `accepted`
- ❌ **Deletes**: Matches with status = `waiting` or `rejected`
- 🗑️ **Cascades**: Deletes associated match decisions
### 3. Cloud Function Handler (`cloud_functions/match_cleanup_handler.py`)
### 3. Cloud Function Handler (`cloud_functions/match_cleanup_handler.py`)
- **Location**: Google Cloud Functions Gen2
- **Trigger**: Pub/Sub topic `user_left_pool`
- **Purpose**: Receives events and calls matches service cleanup endpoint via HTTP
- **Runtime**: Python 3.11
- **Dependencies**: `google-cloud-pubsub`, `requests`, `functions-framework`
- **Environment Variables**:
  - `MATCHES_SERVICE_URL`: `https://matches-service-s556fwc6ua-uc.a.run.app`

**Note**: No database access needed - calls HTTP API instead
## Event Flow
## Event Flow

### Pool Member Removed

1. **User calls**: `DELETE /users/{user_id}/pool`
2. **User-Match Service** (`services/user_match_service.py`):
   - Calls pools service: `DELETE /pools/members/{user_id}`
   - Pools service removes user from pool_members table
   - Pools service updates pool member count
   - Pools service commits database transaction
   - **User-Match Service** publishes `pool_member_removed` event to Pub/Sub
3. **Cloud Pub/Sub**:
   - Receives event on topic `user_left_pool`
   - Triggers Cloud Function
4. **Cloud Function** (`cloud_functions/match_cleanup_handler.py`):
   - Receives Pub/Sub message
   - Decodes event payload
   - Calls matches service: `DELETE /matches/internal/cleanup/user/{user_id}/pool/{pool_id}`
5. **Matches Service** (`resources/matches.py`):
   - Calls `cleanup_user_matches(pool_id, user_id)`
   - Queries matches where:
### Event Message Format

```json
{
  "event_type": "pool_member_removed",
  "pool_id": "11111111-1111-4111-8111-111111111111",
**Attributes** (for message filtering):
- `event_type`: `pool_member_removed`
- `pool_id`: UUID of the pool
- `user_id`: UUID of the user who was removed
- `version`: `1` (event schema version)
  "event_type": "user_left_pool",
  "pool_id": "11111111-1111-4111-8111-111111111111",
  "user_id": "22222222-2222-4222-8222-222222222222",
  "timestamp": "2025-12-05T10:30:00Z"
}
```

## Deployment

### 1. Install Dependencies

**Main Service**:
```bash
pip install google-cloud-pubsub
```

**Cloud Function** (automatically handled):
```bash
# See cloud_functions/requirements.txt
```

### 2. Setup Google Cloud Pub/Sub

```bash
# Create Pub/Sub topic
gcloud pubsub topics create pool-events

# Create subscription (optional, for debugging)
gcloud pubsub subscriptions create pool-events-sub \
    --topic pool-events
```

### 3. Deploy Cloud Function

```bash
cd cloud_functions

gcloud functions deploy match-cleanup-handler \
    --runtime python311 \
    --trigger-topic pool-events \
    --entry-point handle_pool_event \
    --set-env-vars DATABASE_URL=your-mysql-connection-string \
    --timeout 60s \
    --memory 256MB \
    --region us-central1
```

### 4. Configure Pools Service

```bash
# .env file
GCP_PROJECT_ID=your-project-id
POOL_EVENTS_TOPIC=pool-events
ENABLE_EVENT_PUBLISHING=true
```

### 5. Grant Permissions

```bash
# Allow Cloud Function to access database
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member serviceAccount:YOUR_PROJECT_ID@appspot.gserviceaccount.com \
    --role roles/cloudsql.client
```

## Benefits

### 1. **Loose Coupling**
- Pools service and matches service are completely independent
- No shared database access
- Services communicate via events and HTTP APIs
- Can be deployed and scaled independently

### 2. **Microservices Compliance**
- Each service owns its own data
- Cloud Function acts as event-driven orchestrator
- Clean separation of concerns

### 2. **Reliability**
- Events are persisted in Pub/Sub
- Automatic retries if function fails
- Dead letter queue for failed events

### 3. **Scalability**
- Cloud Function auto-scales based on event volume
- No impact on pools service performance

### 4. **Auditability**
- All events are logged
- Can track cleanup statistics
- Easy to add monitoring/alerting

## Error Handling

### Event Publishing Fails
- Pools service logs error but continues
- User is still removed from pool
- Cleanup won't happen automatically
- Can manually trigger cleanup or retry event

### Cloud Function Fails
- Pub/Sub automatically retries (up to 7 days)
- Function logs error details
- Dead letter queue catches persistent failures
- Manual intervention may be needed

### Database Transaction Fails
- Cloud Function rolls back changes
- Pub/Sub retries the event
- Match data remains consistent

## Monitoring

### Key Metrics
- Event publish success rate
- Cloud Function invocation count
- Cloud Function error rate
- Cleanup statistics (matches deleted, decisions deleted)
- Function execution time

### Logging
```bash
# View Cloud Function logs
gcloud functions logs read match-cleanup-handler --limit 50

# View Pub/Sub metrics
gcloud pubsub topics list
gcloud pubsub subscriptions list
```

## Testing

### Local Testing (Without Pub/Sub)
```bash
# Disable event publishing
export ENABLE_EVENT_PUBLISHING=false

# Events will be logged but not published
```

### Test Cloud Function Locally
### Test Event Flow
```bash
# Publish test event
gcloud pubsub topics publish pool-events \
    --message '{"event_type":"pool_member_removed","pool_id":"11111111-1111-4111-8111-111111111111","user_id":"22222222-2222-4222-8222-222222222222"}'

# Check function was triggered
gcloud functions logs read match-cleanup-handler --limit 5
```oud pubsub topics publish pool-events \
    --message '{"event_type":"user_left_pool","pool_id":"test-pool","user_id":"test-user"}'
## Why Not Trigger on Pool Deletion?

When a pool is deleted (`DELETE /pools/{pool_id}`):
- The database **CASCADE** on the `pool_id` foreign key in the `matches` table automatically deletes all matches
- This includes ALL matches (accepted, waiting, rejected)
- No event is needed because the database handles it atomically

The event is only needed for **member removal** because:
- Pool member removal doesn't have a direct foreign key to matches
- We want **selective deletion** (keep accepted, delete non-accepted)
- The business logic is more complex than simple CASCADE

## Future Enhancements

1. **Additional Events**:
   - `match_accepted`: Notify users of successful matches
   - `pool_full`: Trigger creation of new pools
   - `user_joined_pool`: Welcome messages or analytics

2. **Dead Letter Handling**:
   - `match_accepted`: Notify users of successful matches
   - `pool_full`: Trigger creation of new pools
   - `user_joined_pool`: Welcome messages or analytics

2. **Dead Letter Handling**:
   - Automatic retry with exponential backoff
   - Admin notifications for persistent failures
   - Dashboard for failed events

3. **Analytics**:
   - Track cleanup statistics
   - Monitor pool churn rates
   - Identify popular pools/locations

4. **Multi-region Support**:
   - Regional Pub/Sub topics
   - Geo-distributed Cloud Functions
   - Lower latency for global users

## Cost Considerations

- **Pub/Sub**: $0.40 per million messages
- **Cloud Functions**: Pay per invocation + compute time
- **Database**: Cleanup reduces storage costs
- **Estimated**: ~$5-20/month for moderate usage

## Security

- Events contain only IDs (no sensitive data)
- Cloud Function uses service account with minimal permissions
- Database credentials stored in Secret Manager
- TLS encryption for all communications
