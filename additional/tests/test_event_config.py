#!/usr/bin/env python3
"""
Test if event publishing is working when a user leaves a pool.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check environment variables
print("🔍 Checking Event Publishing Configuration...")
print(f"GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID', 'NOT SET')}")
print(f"POOL_EVENTS_TOPIC: {os.getenv('POOL_EVENTS_TOPIC', 'NOT SET')}")
print(f"ENABLE_EVENT_PUBLISHING: {os.getenv('ENABLE_EVENT_PUBLISHING', 'NOT SET')}")

# Check if google-cloud-pubsub is installed
print("\n📦 Checking Dependencies...")
try:
    from google.cloud import pubsub_v1
    print("✅ google-cloud-pubsub is installed")
except ImportError:
    print("❌ google-cloud-pubsub is NOT installed")
    print("   Run: pip install google-cloud-pubsub")
    sys.exit(1)

# Check if topic exists
print("\n🔍 Checking Pub/Sub Topic...")
project_id = os.getenv('GCP_PROJECT_ID')
topic_name = os.getenv('POOL_EVENTS_TOPIC', 'user_left_pool')

if not project_id:
    print("❌ GCP_PROJECT_ID not set")
    sys.exit(1)

try:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)
    
    # Try to get topic (will fail if doesn't exist)
    from google.cloud.pubsub_v1 import types
    request = types.GetTopicRequest(topic=topic_path)
    topic = publisher.get_topic(request=request)
    print(f"✅ Topic exists: {topic.name}")
    
except Exception as e:
    print(f"❌ Topic check failed: {e}")
    print(f"   Make sure topic '{topic_name}' exists in project '{project_id}'")
    sys.exit(1)

# Check Cloud Function deployment
print("\n🔍 Checking Cloud Function...")
print("Run this command to check if function is deployed:")
print(f"  gcloud functions list --project={project_id} --filter='name:match-cleanup-handler'")

print("\n✅ Event publishing configuration looks good!")
print("\nTo test the full flow:")
print("1. Leave a pool via the frontend")
print("2. Check Cloud Function logs:")
print(f"   gcloud functions logs read match-cleanup-handler --region=us-central1 --project={project_id} --limit=50")
print("3. Check Pub/Sub topic for messages:")
print(f"   gcloud pubsub topics list --project={project_id}")
