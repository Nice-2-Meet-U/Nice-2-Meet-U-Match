#!/bin/bash
set -e

PROJECT_ID="cloudexploration-477701"
REGION="us-central1"
SERVICE_NAME="matches-service"
INSTANCE_CONNECTION_NAME="$PROJECT_ID:$REGION:matches-db"
TOPIC_NAME="user_left_pool"
FUNCTION_NAME="match-cleanup-handler"

# Note: Secrets should be stored in Secret Manager, not hardcoded
# TODO: Replace DB_PASS with Secret Manager reference
DB_USER="gb2975"
DB_PASS="Ciociaobio26@"  # SECURITY WARNING: Move to Secret Manager
DB_NAME="matches"

echo "🚀 Deploying Nice-2-Meet-U-Match Infrastructure..."
echo ""

# ------------------------------------------------------------------------------
# 1. Deploy Cloud Function (only if it doesn't exist)
# ------------------------------------------------------------------------------
echo "1️⃣ Checking Cloud Function status..."

FUNCTION_EXISTS=$(gcloud functions list \
  --gen2 \
  --regions="$REGION" \
  --filter="name:$FUNCTION_NAME" \
  --format="value(name)" \
  --project="$PROJECT_ID" 2>/dev/null || echo "")

if [ -z "$FUNCTION_EXISTS" ]; then
  echo "📦 Cloud Function not found. Deploying for the first time..."
  echo ""
  
  # Enable required APIs
  echo "   Enabling Cloud Functions API..."
  gcloud services enable cloudfunctions.googleapis.com --project="$PROJECT_ID" --quiet
  gcloud services enable cloudbuild.googleapis.com --project="$PROJECT_ID" --quiet
  
  # Verify Pub/Sub topic exists
  echo "   Verifying Pub/Sub topic: $TOPIC_NAME..."
  if ! gcloud pubsub topics describe "$TOPIC_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo "   ⚠️  Topic $TOPIC_NAME doesn't exist. Creating it..."
    gcloud pubsub topics create "$TOPIC_NAME" --project="$PROJECT_ID"
  fi
  
  # Deploy Cloud Function
  echo "   Deploying Cloud Function: $FUNCTION_NAME..."
  cd cloud_functions
  gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --source . \
    --entry-point handle_pool_event \
    --trigger-topic "$TOPIC_NAME" \
    --set-env-vars MATCHES_SERVICE_URL="https://$SERVICE_NAME-$PROJECT_ID.a.run.app" \
    --timeout 60s \
    --memory 256MB \
    --max-instances 10 \
    --project "$PROJECT_ID" \
    --quiet
  cd ..
  echo "   ✅ Cloud Function deployed successfully!"
else
  echo "   ✅ Cloud Function already exists. Skipping deployment."
  echo "   💡 To update it, delete first: gcloud functions delete $FUNCTION_NAME --gen2 --region=$REGION"
fi

echo ""

# ------------------------------------------------------------------------------
# 2. Build and Deploy Cloud Run Service
# ------------------------------------------------------------------------------
echo "2️⃣ Building container image..."
gcloud builds submit \
  --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME:latest" \
  --project "$PROJECT_ID"

echo ""
echo "3️⃣ Deploying to Cloud Run..."

# Get service URL if it already exists
EXISTING_SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format="value(status.url)" 2>/dev/null || echo "")

# If service doesn't exist yet, we'll use a placeholder and update after first deploy
if [ -z "$EXISTING_SERVICE_URL" ]; then
  POOLS_SERVICE_URL="https://$SERVICE_NAME-$PROJECT_ID.a.run.app"
else
  POOLS_SERVICE_URL="$EXISTING_SERVICE_URL"
fi

gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME:latest" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME,DB_USER=$DB_USER,DB_PASS=$DB_PASS,DB_NAME=$DB_NAME,GCP_PROJECT_ID=$PROJECT_ID,POOL_EVENTS_TOPIC=$TOPIC_NAME,ENABLE_EVENT_PUBLISHING=true,POOLS_SERVICE_URL=$POOLS_SERVICE_URL" \
  --add-cloudsql-instances "$INSTANCE_CONNECTION_NAME" \
  --timeout=300 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --project "$PROJECT_ID"

# ------------------------------------------------------------------------------
# 3. Get Service Information & Update if needed
# ------------------------------------------------------------------------------
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format="value(status.url)")

# If this was a first deployment and URL differs from placeholder, update the env var
if [ -z "$EXISTING_SERVICE_URL" ] && [ "$SERVICE_URL" != "$POOLS_SERVICE_URL" ]; then
  echo ""
  echo "4️⃣ Updating POOLS_SERVICE_URL with actual service URL..."
  gcloud run services update "$SERVICE_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --update-env-vars "POOLS_SERVICE_URL=$SERVICE_URL" \
    --quiet
  echo "   ✅ Service URL updated!"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo "🌐 Service URL: $SERVICE_URL"
echo "📚 API Docs: $SERVICE_URL/docs"
echo ""
echo "📋 Infrastructure Summary:"
echo "   • Cloud Run Service: $SERVICE_NAME"
echo "   • Cloud Function: $FUNCTION_NAME"
echo "   • Pub/Sub Topic: $TOPIC_NAME"
echo "   • Region: $REGION"
echo ""
echo "🔍 Useful Commands:"
echo "   View logs: gcloud run services logs tail $SERVICE_NAME --region=$REGION"
echo "   Function logs: gcloud functions logs read $FUNCTION_NAME --gen2 --region=$REGION --limit=50"
echo "   Test event: gcloud pubsub topics publish $TOPIC_NAME --message='{\"event_type\":\"pool_member_removed\",\"pool_id\":\"test\",\"user_id\":\"test\"}'"
echo ""