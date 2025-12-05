# Testing Guide: Event-Driven Match Cleanup

## Prerequisites Checklist

Before testing, ensure:

1. **Cloud Function Deployed**
   ```bash
   cd cloud_functions
   gcloud functions deploy match-cleanup-handler \
     --gen2 \
     --runtime python311 \
     --region us-central1 \
     --source . \
     --entry-point handle_pool_event \
     --trigger-topic user_left_pool \
     --set-env-vars MATCHES_SERVICE_URL='https://matches-service-s556fwc6ua-uc.a.run.app' \
     --timeout 60s \
     --memory 256MB
   ```

2. **Matches Service Deployed**
   ```bash
   # Use the deployment script
   ./deploy.sh
   ```

3. **Service URL**
   ```
   https://matches-service-s556fwc6ua-uc.a.run.app
   ```

## Test Scenarios

### Test 1: Direct Cleanup Endpoint Testing

Test the cleanup endpoint directly:

```bash
# Service URL
export SERVICE_URL="https://matches-service-s556fwc6ua-uc.a.run.app"

# Test UUIDs
export TEST_USER_ID="ffffffff-ffff-4fff-8fff-ffffffffffff"
export TEST_POOL_ID="0d47b7c6-a0cd-4783-aeee-18f93295503f"

# 1. Join a pool
curl -X POST "$SERVICE_URL/users/$TEST_USER_ID/pool" \
  -H "Content-Type: application/json" \
  -d '{"location": "NYC", "coord_x": 1.0, "coord_y": 1.0}'

# 2. Generate matches
curl -X POST "$SERVICE_URL/users/$TEST_USER_ID/matches" \
  -H "Content-Type: application/json" \
  -d '{"max_matches": 5}'

# 3. Get matches (note the match IDs)
curl "$SERVICE_URL/matches/?user_id=$TEST_USER_ID"

# 4. Test cleanup endpoint directly
curl -X DELETE \
  "$SERVICE_URL/matches/internal/cleanup/user/$TEST_USER_ID/pool/$TEST_POOL_ID"

# 5. Verify matches were deleted
curl "$SERVICE_URL/matches/?user_id=$TEST_USER_ID"
```

### Test 2: Event Publishing Test

Test if events are published when users leave pools:

```bash
# Service URL
export SERVICE_URL="https://matches-service-s556fwc6ua-uc.a.run.app"

# Monitor Pub/Sub messages (optional - create a test subscription)
gcloud pubsub subscriptions create test-sub --topic=user_left_pool --project=cloudexploration-477701

# In one terminal, pull messages
gcloud pubsub subscriptions pull test-sub --auto-ack --limit=10 --project=cloudexploration-477701

# In another terminal, use the user-match composite endpoint to leave pool
curl -X DELETE "$SERVICE_URL/users/$TEST_USER_ID/pool"

# You should see a message in the subscription with:
# {
#   "event_type": "pool_member_removed",
#   "user_id": "...",
#   "pool_id": "...",
#   "timestamp": "..."
# }

### Test 3: End-to-End Event Flow

Test the complete flow: leave pool → Pub/Sub event → Cloud Function → match cleanup

**Setup:**
```bash
export SERVICE_URL="https://matches-service-s556fwc6ua-uc.a.run.app"
export TEST_USER_ID="cccccccc-cccc-4ccc-8ccc-cccccccccccc"

# 1. Join a pool
curl -X POST "$SERVICE_URL/users/$TEST_USER_ID/pool" \
  -H "Content-Type: application/json" \
  -d '{"location": "NYC", "coord_x": 2.0, "coord_y": 2.0}' '{
    "name": "Test Pool",
    "location": {"latitude": 37.7749, "longitude": -122.4194},
    "max_distance_km": 5
  }'

# Save the pool_id from response

# 2. Add users to pool (repeat for user2, user3)
curl -X POST "https://matches-service-870022169527.us-central1.run.app/pools/{pool_id}/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "current_location": {"latitude": 37.7749, "longitude": -122.4194}}'

# 3. Create matches between users (some accepted, some pending)
curl -X POST "https://matches-service-870022169527.us-central1.run.app/matches" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pool_id": "{pool_id}",
    "user1_id": "user1",
    "user2_id": "user2"
  }'

# 4. Accept one match
curl -X POST "https://matches-service-870022169527.us-central1.run.app/matches/{match_id}/decide" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "decision": "accept"}'

curl -X POST "https://matches-service-870022169527.us-central1.run.app/matches/{match_id}/decide" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user2", "decision": "accept"}'

# 5. Leave some other matches pending

# 6. Query matches before cleanup
curl -X GET "https://matches-service-870022169527.us-central1.run.app/matches?pool_id={pool_id}" \
  -H "Authorization: Bearer $TOKEN"
# Note the number of matches involving user1
```

**Execute Test:**
```bash
# Remove user1 from pool
curl -X DELETE \
  "https://matches-service-870022169527.us-central1.run.app/pools/{pool_id}/members/user1" \
  -H "Authorization: Bearer $TOKEN"

# Wait 5-10 seconds for event processing

# Check Cloud Function logs
gcloud functions logs read match-cleanup-handler \
  --region us-central1 \
  --limit 50 \
  --project=cloudexploration-477701

# Query matches after cleanup
curl -X GET "https://matches-service-870022169527.us-central1.run.app/matches?pool_id={pool_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Results:**
- ✅ User1 removed from pool successfully
- ✅ Pub/Sub message published to `user_left_pool` topic
- ✅ Cloud Function triggered and executed
- ✅ Cloud Function called cleanup endpoint
- ✅ Only non-accepted matches involving user1 in that pool were deleted
- ✅ Accepted matches remain intact
- ✅ Matches in other pools not affected

### Test 4: Verify Cleanup Logic

**Note:** Current implementation deletes ALL non-accepted matches (status != 'accepted') when a user leaves a pool.

**Test Case: Waiting matches should be deleted**
```bash
# Create match, don't submit any decisions
# Remove user from pool
# Expected: Match is deleted (status='waiting')

export SERVICE_URL="https://matches-service-s556fwc6ua-uc.a.run.app"
export TEST_USER="eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"

# Join, generate match, leave
curl -X POST "$SERVICE_URL/users/$TEST_USER/pool" \
  -H "Content-Type: application/json" \
  -d '{"location": "NYC", "coord_x": 3.0, "coord_y": 3.0}'

curl -X POST "$SERVICE_URL/users/$TEST_USER/matches" \
  -H "Content-Type: application/json" \
  -d '{"max_matches": 1}'

# Note the match ID, then leave
curl -X DELETE "$SERVICE_URL/users/$TEST_USER/pool"

# Verify match deleted
curl "$SERVICE_URL/matches/{match_id}"
# Expected: 404 Not Found
```

**Test Case: Matches in other pools not affected**
```bash
# User is in multiple locations (not supported by current API)
# Cleanup only affects the specific pool they left
```
# user1 has matches in both pools
# Remove user1 from pool_A
# Expected: Only pool_A matches deleted, pool_B matches intact
```

## Debugging Tips

### Check Pub/Sub Messages
```bash
# List subscriptions
gcloud pubsub subscriptions list --project=cloudexploration-477701

# Pull recent messages
gcloud pubsub subscriptions pull test-sub --limit=10 --project=cloudexploration-477701
```

### Check Cloud Function Logs
```bash
# Recent logs
gcloud functions logs read match-cleanup-handler \
  --region us-central1 \
  --limit 100 \
  --project=cloudexploration-477701

# Live logs (tail)
gcloud functions logs read match-cleanup-handler \
  --region us-central1 \
  --limit 100 \
  --project=cloudexploration-477701 \
  --follow
```

### Check Cloud Run Service Logs
```bash
# Matches service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=matches-service" \
  --limit 50 \
  --project=cloudexploration-477701 \
  --format json
```

### Common Issues

**Issue: No event published**
- Check: `ENABLE_EVENT_PUBLISHING=true` in .env
- Check: Service redeployed with new environment variable
- Check: `event_publisher.py` is imported correctly

**Issue: Cloud Function not triggered**
- Check: Function deployed successfully
- Check: Topic name matches: `user_left_pool`
- Check: Function has trigger configured

**Issue: Cleanup endpoint returns 401/403**
- Check: Cloud Function has `MATCHES_SERVICE_URL` set correctly
- Check: Internal endpoint doesn't require auth (or configure service-to-service auth)

**Issue: Cleanup deletes too many matches**
- Check: Query filters for specific pool_id
- Check: Query filters for specific user_id
- Check: Logic only deletes non-accepted matches

## Quick Test Script

Create a test file `test_event_flow.sh`:

```bash
#!/bin/bash

# Configuration
POOL_ID="your-pool-id"
USER_ID="user1"
TOKEN="your-token"
BASE_URL="https://matches-service-870022169527.us-central1.run.app"

echo "=== Testing Event-Driven Cleanup ==="

echo -e "\n1. Querying matches before cleanup..."
curl -s -X GET "$BASE_URL/matches?pool_id=$POOL_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo -e "\n2. Removing user from pool (triggers event)..."
curl -s -X DELETE "$BASE_URL/pools/$POOL_ID/members/$USER_ID" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n3. Waiting 10 seconds for event processing..."
sleep 10

echo -e "\n4. Checking Cloud Function logs..."
gcloud functions logs read match-cleanup-handler \
  --region us-central1 \
  --limit 10 \
  --project=cloudexploration-477701

echo -e "\n5. Querying matches after cleanup..."
curl -s -X GET "$BASE_URL/matches?pool_id=$POOL_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo -e "\n=== Test Complete ==="
```

Make it executable:
```bash
chmod +x test_event_flow.sh
./test_event_flow.sh
```

## Success Criteria

✅ **All systems working correctly when:**

1. Removing user from pool publishes event to Pub/Sub
2. Cloud Function receives event and executes
3. Cloud Function successfully calls cleanup endpoint
4. Only non-accepted matches deleted (accepted matches preserved)
5. Only matches for specific user + pool deleted (other pools unaffected)
6. Cloud Function logs show successful execution
7. No errors in Cloud Run logs
8. Database state is correct after cleanup
