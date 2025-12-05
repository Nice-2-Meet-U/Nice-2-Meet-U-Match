#!/bin/bash

# Quick Setup Script for Google Cloud Event System
# Run this after you've created your Pub/Sub topic

PROJECT_ID="cloudexploration-477701"
TOPIC_NAME="user_left_pool"
REGION="us-central1"

echo "🚀 Setting up Google Cloud for Match Cleanup Events..."
echo ""

# 1. Set project
echo "1️⃣ Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# 2. Enable required APIs
echo ""
echo "2️⃣ Enabling required APIs..."
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 3. Verify topic exists
echo ""
echo "3️⃣ Verifying Pub/Sub topic exists..."
gcloud pubsub topics describe ${TOPIC_NAME}

# 4. Deploy Cloud Function
echo ""
echo "4️⃣ Deploying Cloud Function..."
echo "⚠️  You need to set MATCHES_SERVICE_URL"
echo ""
read -p "Enter your Matches Service URL (e.g., http://localhost:8000 or https://matches-service.run.app): " MATCHES_URL

cd cloud_functions

gcloud functions deploy match-cleanup-handler \
    --gen2 \
    --runtime python311 \
    --region ${REGION} \
    --source . \
    --entry-point handle_pool_event \
    --trigger-topic ${TOPIC_NAME} \
    --set-env-vars MATCHES_SERVICE_URL="${MATCHES_URL}" \
    --timeout 60s \
    --memory 256MB \
    --max-instances 10

cd ..

# 5. Update local .env
echo ""
echo "5️⃣ Updating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
fi

# Update or add the GCP configuration
if grep -q "GCP_PROJECT_ID" .env; then
    sed -i '' "s|GCP_PROJECT_ID=.*|GCP_PROJECT_ID=${PROJECT_ID}|" .env
    sed -i '' "s|POOL_EVENTS_TOPIC=.*|POOL_EVENTS_TOPIC=${TOPIC_NAME}|" .env
    sed -i '' "s|ENABLE_EVENT_PUBLISHING=.*|ENABLE_EVENT_PUBLISHING=true|" .env
else
    echo "" >> .env
    echo "# Google Cloud Configuration" >> .env
    echo "GCP_PROJECT_ID=${PROJECT_ID}" >> .env
    echo "POOL_EVENTS_TOPIC=${TOPIC_NAME}" >> .env
    echo "ENABLE_EVENT_PUBLISHING=true" >> .env
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Install dependencies: pip install google-cloud-pubsub"
echo "2. Test locally by removing a user from a pool"
echo "3. Check Cloud Function logs: gcloud functions logs read match-cleanup-handler --gen2 --region ${REGION} --limit 10"
echo ""
echo "🔍 Useful commands:"
echo "  View function details: gcloud functions describe match-cleanup-handler --gen2 --region ${REGION}"
echo "  View logs: gcloud functions logs read match-cleanup-handler --gen2 --region ${REGION} --follow"
echo "  Test publish: gcloud pubsub topics publish ${TOPIC_NAME} --message '{\"event_type\":\"pool_member_removed\",\"pool_id\":\"test\",\"user_id\":\"test\"}'"
