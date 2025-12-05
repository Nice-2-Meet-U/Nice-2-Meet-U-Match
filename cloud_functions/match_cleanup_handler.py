"""
Google Cloud Function for handling pool events and cleaning up matches.

This function is triggered by Pub/Sub messages from the pools service.
When a user leaves a pool, it calls the matches service API to clean up
their non-accepted matches.

Deploy with:
gcloud functions deploy match-cleanup-handler \
    --runtime python311 \
    --trigger-topic pool-events \
    --entry-point handle_pool_event \
    --set-env-vars MATCHES_SERVICE_URL=https://your-matches-service-url
"""
import base64
import json
import logging
import os
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get matches service URL from environment
MATCHES_SERVICE_URL = os.getenv('MATCHES_SERVICE_URL', 'http://localhost:8000')


def handle_pool_event(event, context):
    """
    Cloud Function triggered by Pub/Sub.
    
    Args:
        event (dict): Event payload (contains 'data' and 'attributes')
        context (google.cloud.functions.Context): Event metadata
    """
    # Decode the Pub/Sub message
    if 'data' in event:
        message_data = base64.b64decode(event['data']).decode('utf-8')
        event_payload = json.loads(message_data)
    else:
        logger.error("No data in event")
        return
    
    event_type = event_payload.get('event_type')
    
    logger.info(f"Received event: {event_type}")
    
    if event_type == 'pool_member_removed':
        handle_pool_member_removed(event_payload)
    else:
        logger.warning(f"Unknown event type: {event_type}")


def handle_pool_member_removed(event_payload):
    """
    Handle pool_member_removed event by calling matches service API.
    
    When a user is removed from a pool, we call the matches service
    to delete all their non-accepted matches in that pool.
    
    Args:
        event_payload (dict): Event data containing pool_id and user_id
    """
    pool_id = event_payload.get('pool_id')
    user_id = event_payload.get('user_id')
    
    if not pool_id or not user_id:
        logger.error("Missing pool_id or user_id in pool_member_removed event")
        return
    
    logger.info(f"Processing pool_member_removed: user {user_id} left pool {pool_id}")
    
    # Call the matches service cleanup endpoint
    cleanup_url = f"{MATCHES_SERVICE_URL}/matches/internal/cleanup/user/{user_id}/pool/{pool_id}"
    
    try:
        response = requests.delete(cleanup_url, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logger.info(
            f"Cleanup complete: deleted {result.get('matches_deleted', 0)} matches "
            f"and {result.get('decisions_deleted', 0)} decisions for user {user_id}"
        )
        
    except requests.RequestException as e:
        logger.error(f"Failed to call matches service: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        raise  # Re-raise to trigger Pub/Sub retry
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")
        raise


# For local testing
if __name__ == '__main__':
    # Simulate a Pub/Sub event
    test_event = {
        'data': base64.b64encode(json.dumps({
            'event_type': 'user_left_pool',
            'pool_id': '11111111-1111-4111-8111-111111111111',
            'user_id': '22222222-2222-4222-8222-222222222222'
        }).encode('utf-8'))
    }
    
    handle_pool_event(test_event, None)
# For local testing
if __name__ == '__main__':
    # Simulate a Pub/Sub event
    test_event = {
        'data': base64.b64encode(json.dumps({
            'event_type': 'pool_member_removed',
            'pool_id': '11111111-1111-4111-8111-111111111111',
            'user_id': '22222222-2222-4222-8222-222222222222'
        }).encode('utf-8'))
    }
    
    handle_pool_event(test_event, None)