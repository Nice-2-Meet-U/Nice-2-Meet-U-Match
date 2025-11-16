#!/bin/bash
set -e

PROJECT_ID="cloudexploration-477701"
REGION="us-central1"
SERVICE_NAME="matches-service"
INSTANCE_CONNECTION_NAME="$PROJECT_ID:$REGION:matches-db"

echo "🚀 Building and deploying $SERVICE_NAME..."

# Build and push image
echo "📦 Building container image..."
gcloud builds submit \
  --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME:latest" \
  --project "$PROJECT_ID"

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME:latest" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME,DB_USER=gb2975,DB_PASS=Ciociaobio26@,DB_NAME=matches" \
  --add-cloudsql-instances "$INSTANCE_CONNECTION_NAME" \
  --timeout=300 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --project "$PROJECT_ID"

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format="value(status.url)")

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📚 API Docs: $SERVICE_URL/docs"