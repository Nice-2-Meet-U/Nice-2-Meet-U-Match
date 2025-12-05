# services/event_publisher.py
"""
Event publisher for Google Cloud Pub/Sub.
Publishes pool-related events to notify other microservices.
"""
from __future__ import annotations

import os
import json
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import Google Cloud Pub/Sub (optional dependency)
try:
    from google.cloud import pubsub_v1
    PUBSUB_AVAILABLE = True
except ImportError:
    PUBSUB_AVAILABLE = False
    logger.warning("google-cloud-pubsub not installed. Event publishing disabled.")


class EventPublisher:
    """Publisher for pool events to Google Cloud Pub/Sub."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.topic_name = os.getenv("POOL_EVENTS_TOPIC", "pool-events")
        self.enabled = os.getenv("ENABLE_EVENT_PUBLISHING", "false").lower() == "true"
        
        if self.enabled and PUBSUB_AVAILABLE and self.project_id:
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
            logger.info(f"Event publisher initialized for topic: {self.topic_path}")
        else:
            self.publisher = None
            if self.enabled:
                # More detailed misconfiguration logging
                reasons = []
                if not PUBSUB_AVAILABLE:
                    reasons.append("google-cloud-pubsub library not installed")
                if not self.project_id:
                    reasons.append("GCP_PROJECT_ID not set")
                logger.warning(f"Event publishing enabled but not properly configured: {', '.join(reasons)}")
    
    def publish_user_left_pool(self, pool_id: UUID, user_id: UUID) -> Optional[str]:
        """
        Publish an event when a pool member is removed.
        This triggers cleanup of non-accepted matches for that user in the pool.
        
        Args:
            pool_id: The pool the user is leaving
            user_id: The user who is leaving
            
        Returns:
            Message ID if published, None otherwise
        """
        if not self.enabled or not self.publisher:
            logger.debug(f"Event publishing disabled. Would publish: user {user_id} left pool {pool_id}")
            return None
        
        event_data = {
            "version": "1",
            "event_type": "pool_member_removed",
            "pool_id": str(pool_id),
            "user_id": str(user_id),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Publish message to Pub/Sub
            message_json = json.dumps(event_data)
            message_bytes = message_json.encode("utf-8")
            
            future = self.publisher.publish(
                self.topic_path,
                message_bytes,
                event_type="pool_member_removed",
                pool_id=str(pool_id),
                user_id=str(user_id)
            )
            
            message_id = future.result(timeout=5.0)
            logger.info(f"Published pool_member_removed event: pool={pool_id}, user={user_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish pool_member_removed event: {e}")
            # Don't fail the main operation if event publishing fails
            return None


# Global publisher instance
_publisher_instance: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get or create the global event publisher instance."""
    global _publisher_instance
    if _publisher_instance is None:
        _publisher_instance = EventPublisher()
    return _publisher_instance
