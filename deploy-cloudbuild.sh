#!/bin/bash
# Deploy 4 microservices using Cloud Build (no local Docker needed)

PROJECT_ID="cloudexploration-477701"
REGION="us-central1"
CLOUD_SQL_INSTANCE="cloudexploration-477701:us-central1:matches-db"
DB_USER="gb2975"
DB_PASS="Ciociaobio26@"
DB_NAME="matches"

echo "🚀 Building and deploying 4 microservices with Cloud Build..."

# 1. Build and deploy Pool Service
echo ""
echo "📦 Building pool-service..."
gcloud builds submit \
  --tag gcr.io/${PROJECT_ID}/pool-service \
  --timeout=20m \
  --project=${PROJECT_ID} \
  --gcs-log-dir=gs://${PROJECT_ID}_cloudbuild/logs \
  --substitutions=_DOCKERFILE_PATH=Dockerfile.pool \
  .

echo "🚀 Deploying pool-service..."
gcloud run deploy pool-service \
  --image=gcr.io/${PROJECT_ID}/pool-service \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="INSTANCE_CONNECTION_NAME=${CLOUD_SQL_INSTANCE},DB_USER=${DB_USER},DB_PASS=${DB_PASS},DB_NAME=${DB_NAME}" \
  --set-cloudsql-instances=${CLOUD_SQL_INSTANCE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated

POOL_URL=$(gcloud run services describe pool-service --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "✅ Pool service deployed: ${POOL_URL}"

# 2. Build and deploy Match Service
echo ""
echo "📦 Building match-service..."
gcloud builds submit \
  --tag gcr.io/${PROJECT_ID}/match-service \
  --timeout=20m \
  --project=${PROJECT_ID} \
  --gcs-log-dir=gs://${PROJECT_ID}_cloudbuild/logs \
  --substitutions=_DOCKERFILE_PATH=Dockerfile.match \
  .

echo "🚀 Deploying match-service..."
gcloud run deploy match-service \
  --image=gcr.io/${PROJECT_ID}/match-service \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="INSTANCE_CONNECTION_NAME=${CLOUD_SQL_INSTANCE},DB_USER=${DB_USER},DB_PASS=${DB_PASS},DB_NAME=${DB_NAME}" \
  --set-cloudsql-instances=${CLOUD_SQL_INSTANCE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated

MATCH_URL=$(gcloud run services describe match-service --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "✅ Match service deployed: ${MATCH_URL}"

# 3. Build and deploy Decision Service
echo ""
echo "📦 Building decision-service..."
gcloud builds submit \
  --tag gcr.io/${PROJECT_ID}/decision-service \
  --timeout=20m \
  --project=${PROJECT_ID} \
  --gcs-log-dir=gs://${PROJECT_ID}_cloudbuild/logs \
  --substitutions=_DOCKERFILE_PATH=Dockerfile.decision \
  .

echo "🚀 Deploying decision-service..."
gcloud run deploy decision-service \
  --image=gcr.io/${PROJECT_ID}/decision-service \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="INSTANCE_CONNECTION_NAME=${CLOUD_SQL_INSTANCE},DB_USER=${DB_USER},DB_PASS=${DB_PASS},DB_NAME=${DB_NAME}" \
  --set-cloudsql-instances=${CLOUD_SQL_INSTANCE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated

DECISION_URL=$(gcloud run services describe decision-service --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "✅ Decision service deployed: ${DECISION_URL}"

# 4. Build and deploy User Service (Orchestrator)
echo ""
echo "📦 Building user-service..."
gcloud builds submit \
  --tag gcr.io/${PROJECT_ID}/user-service \
  --timeout=20m \
  --project=${PROJECT_ID} \
  --gcs-log-dir=gs://${PROJECT_ID}_cloudbuild/logs \
  --substitutions=_DOCKERFILE_PATH=Dockerfile.user \
  .

echo "🚀 Deploying user-service (orchestrator)..."
gcloud run deploy user-service \
  --image=gcr.io/${PROJECT_ID}/user-service \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="POOL_SERVICE_URL=${POOL_URL},MATCH_SERVICE_URL=${MATCH_URL},DECISION_SERVICE_URL=${DECISION_URL},SERVICE_BASE_URL=${POOL_URL},INSTANCE_CONNECTION_NAME=${CLOUD_SQL_INSTANCE},DB_USER=${DB_USER},DB_PASS=${DB_PASS},DB_NAME=${DB_NAME}" \
  --set-cloudsql-instances=${CLOUD_SQL_INSTANCE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated

USER_URL=$(gcloud run services describe user-service --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "✅ User service deployed: ${USER_URL}"

# Update HATEOAS links
echo ""
echo "🔗 Updating HATEOAS SERVICE_BASE_URL for each service..."

gcloud run services update pool-service \
  --update-env-vars SERVICE_BASE_URL=${POOL_URL} \
  --region=${REGION} \
  --project=${PROJECT_ID}

gcloud run services update match-service \
  --update-env-vars SERVICE_BASE_URL=${MATCH_URL} \
  --region=${REGION} \
  --project=${PROJECT_ID}

gcloud run services update decision-service \
  --update-env-vars SERVICE_BASE_URL=${DECISION_URL} \
  --region=${REGION} \
  --project=${PROJECT_ID}

echo ""
echo "🎉 All 4 microservices deployed successfully!"
echo ""
echo "═══════════════════════════════════════════════════════"
echo "Service URLs:"
echo "═══════════════════════════════════════════════════════"
echo "  Pool Service:     ${POOL_URL}"
echo "  Match Service:    ${MATCH_URL}"
echo "  Decision Service: ${DECISION_URL}"
echo "  User Service:     ${USER_URL}"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "API Documentation:"
echo "  Pool:     ${POOL_URL}/docs"
echo "  Match:    ${MATCH_URL}/docs"
echo "  Decision: ${DECISION_URL}/docs"
echo "  User:     ${USER_URL}/docs"
echo ""
