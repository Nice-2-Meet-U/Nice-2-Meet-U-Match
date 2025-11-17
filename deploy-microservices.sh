#!/bin/bash
# Deploy 4 microservices to Google Cloud Run

PROJECT_ID="cloudexploration-477701"
REGION="us-central1"
CLOUD_SQL_INSTANCE="cloudexploration-477701:us-central1:matches-db"
DB_USER="gb2975"
DB_PASS="Ciociaobio26@"
DB_NAME="matches"

echo "🚀 Building and deploying 4 microservices..."

# Build and deploy Pool Service
echo "📦 Building pool-service..."
docker build -t gcr.io/${PROJECT_ID}/pool-service -f Dockerfile.pool .
docker push gcr.io/${PROJECT_ID}/pool-service

echo "🚀 Deploying pool-service..."
gcloud run deploy pool-service \
  --image=gcr.io/${PROJECT_ID}/pool-service \
  --min-instances=0 \
  --set-env-vars="INSTANCE_CONNECTION_NAME=${CLOUD_SQL_INSTANCE},DB_USER=${DB_USER},DB_PASS=${DB_PASS},DB_NAME=${DB_NAME}" \
  --set-cloudsql-instances=${CLOUD_SQL_INSTANCE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated

POOL_URL=$(gcloud run services describe pool-service --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "✅ Pool service deployed: ${POOL_URL}"

# Build and deploy Match Service
echo "📦 Building match-service..."
docker build -t gcr.io/${PROJECT_ID}/match-service -f Dockerfile.match .
docker push gcr.io/${PROJECT_ID}/match-service

echo "🚀 Deploying match-service..."
gcloud run deploy match-service \
  --image=gcr.io/${PROJECT_ID}/match-service \
  --min-instances=0 \
  --set-env-vars="INSTANCE_CONNECTION_NAME=${CLOUD_SQL_INSTANCE},DB_USER=${DB_USER},DB_PASS=${DB_PASS},DB_NAME=${DB_NAME}" \
  --set-cloudsql-instances=${CLOUD_SQL_INSTANCE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated

MATCH_URL=$(gcloud run services describe match-service --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "✅ Match service deployed: ${MATCH_URL}"

# Build and deploy Decision Service
echo "📦 Building decision-service..."
docker build -t gcr.io/${PROJECT_ID}/decision-service -f Dockerfile.decision .
docker push gcr.io/${PROJECT_ID}/decision-service

echo "🚀 Deploying decision-service..."
gcloud run deploy decision-service \
  --image=gcr.io/${PROJECT_ID}/decision-service \
  --min-instances=0 \
  --set-env-vars="INSTANCE_CONNECTION_NAME=${CLOUD_SQL_INSTANCE},DB_USER=${DB_USER},DB_PASS=${DB_PASS},DB_NAME=${DB_NAME}" \
  --set-cloudsql-instances=${CLOUD_SQL_INSTANCE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated

DECISION_URL=$(gcloud run services describe decision-service --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "✅ Decision service deployed: ${DECISION_URL}"

# Build and deploy User Service (Orchestrator) - NO DATABASE CONNECTION
echo "📦 Building user-service..."
docker build -t gcr.io/${PROJECT_ID}/user-service -f Dockerfile.user .
docker push gcr.io/${PROJECT_ID}/user-service

echo "🚀 Deploying user-service..."
gcloud run deploy user-service \
  --image=gcr.io/${PROJECT_ID}/user-service \
  --min-instances=0 \
  --set-env-vars="POOL_SERVICE_URL=${POOL_URL},MATCH_SERVICE_URL=${MATCH_URL},DECISION_SERVICE_URL=${DECISION_URL},SERVICE_BASE_URL=${POOL_URL}" \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated

USER_URL=$(gcloud run services describe user-service --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "✅ User service deployed: ${USER_URL}"

echo ""
echo "🎉 All services deployed successfully!"
echo ""
echo "Service URLs:"
echo "  Pool:     ${POOL_URL}"
echo "  Match:    ${MATCH_URL}"
echo "  Decision: ${DECISION_URL}"
echo "  User:     ${USER_URL}"
echo ""
echo "Update HATEOAS links:"
echo "gcloud run services update pool-service --set-env-vars SERVICE_BASE_URL=${POOL_URL} --region=${REGION} --project=${PROJECT_ID}"
echo "gcloud run services update match-service --set-env-vars SERVICE_BASE_URL=${MATCH_URL} --region=${REGION} --project=${PROJECT_ID}"
echo "gcloud run services update decision-service --set-env-vars SERVICE_BASE_URL=${DECISION_URL} --region=${REGION} --project=${PROJECT_ID}"
