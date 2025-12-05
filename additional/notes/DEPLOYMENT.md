# Deployment Guide: Cloud SQL + Cloud Run

This guide walks you through deploying the Matches microservice to Google Cloud Run with Cloud SQL (MySQL).

## Prerequisites

1. **Google Cloud SDK (gcloud)** installed and authenticated
2. **A GCP project** with billing enabled (Project ID: `cloudexploration-477701`)
3. **Required APIs enabled** (see Step 2)
4. **Python 3.11** runtime compatible codebase

## Step 1: Verify gcloud Setup

```bash
# Check gcloud version
gcloud --version

# Check authentication
gcloud auth list

# If not authenticated, run:
gcloud auth login
gcloud auth application-default login

# Set your project
export PROJECT_ID="your-project-id"
export REGION="us-central1"  # or your preferred region
gcloud config set project $PROJECT_ID
```

## Step 2: Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  pubsub.googleapis.com \
  cloudfunctions.googleapis.com
```

## Step 3: Create Cloud SQL MySQL Instance

```bash
# Set instance name
export SQL_INSTANCE_NAME="matches-db"

# Create MySQL instance (takes 5-10 minutes)
gcloud sql instances create $SQL_INSTANCE_NAME \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=$REGION \
  --no-assign-ip

# Create database
gcloud sql databases create matches --instance $SQL_INSTANCE_NAME

# Set password for root user (choose a strong password)
export DB_PASSWORD="your-secure-password"
gcloud sql users set-password root \
  --instance $SQL_INSTANCE_NAME \
  --password "$DB_PASSWORD"

# Get connection name (needed for Cloud Run)
export INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $SQL_INSTANCE_NAME \
  --format="value(connectionName)")
echo "Connection name: $INSTANCE_CONNECTION_NAME"
```

**Note:** Wait until the instance status is `RUNNABLE` before proceeding.

## Step 4: Build and Push Container Image

```bash
# Build and push to Artifact Registry (or Container Registry)
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/matches-service:latest \
  --project $PROJECT_ID
```

## Step 5: Deploy to Cloud Run

```bash
gcloud run deploy matches-service \
  --image gcr.io/$PROJECT_ID/matches-service:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars \
    INSTANCE_CONNECTION_NAME="$INSTANCE_CONNECTION_NAME",\
    DB_USER=root,\
    DB_PASS="$DB_PASSWORD",\
    DB_NAME=matches,\
    POOLS_SERVICE_URL=https://matches-service-s556fwc6ua-uc.a.run.app \
  --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
  --project $PROJECT_ID
```

**Important:** 
- The service will automatically create database tables on first startup via `Base.metadata.create_all()`.
- The `POOLS_SERVICE_URL` is set to the same service URL since the composite service is integrated into the same deployment.
- The deployment script (`deploy.sh`) handles automatic updating of this environment variable.

## Step 6: Grant Cloud SQL Client Permission

```bash
# Get the service account
SERVICE_ACCOUNT=$(gcloud run services describe matches-service \
  --region $REGION \
  --format="value(spec.template.spec.serviceAccountName)")

# If empty, use the default compute service account
if [ -z "$SERVICE_ACCOUNT" ]; then
  SERVICE_ACCOUNT="${PROJECT_ID}-compute@developer.gserviceaccount.com"
fi

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudsql.client"
```

## Step 7: Get Service URL and Test

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe matches-service \
  --region $REGION \
  --format="value(status.url)")
echo "Service URL: $SERVICE_URL"

# Test health endpoint
curl $SERVICE_URL/

# Test API documentation
echo "API Docs: $SERVICE_URL/docs"
```

## Testing the API

### 1. Health Check

```bash
curl $SERVICE_URL/
```

Expected response:
```json
{"status":"ok","service":"matches","version":"1.0.0"}
```

### 2. Create a Pool (Manual SQL)

First, create a pool in the database:

```bash
# Connect to the database
gcloud sql connect $SQL_INSTANCE_NAME --user=root

# In MySQL prompt:
USE matches;
INSERT INTO pools (name, location, member_count) VALUES ('Test Pool', 'NYC', 0);
# Note the pool ID (e.g., 1)
```

### 3. Create a Match

```bash
curl -X POST "$SERVICE_URL/matches/" \
  -H "Content-Type: application/json" \
  -d '{
    "pool_id": 1,
    "user1_id": 100,
    "user2_id": 200
  }'
```

Expected response includes `match_id`, `status: "waiting"`, etc.

### 4. Submit Decisions

```bash
# User 100 accepts
curl -X POST "$SERVICE_URL/decisions/" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "user_id": 100,
    "decision": "accept"
  }'

# User 200 accepts (match becomes "accepted")
curl -X POST "$SERVICE_URL/decisions/" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "user_id": 200,
    "decision": "accept"
  }'
```

### 5. Get Match Status

```bash
curl "$SERVICE_URL/matches/1"
```

Should show `"status": "accepted"` after both users accept.

### 6. List Matches

```bash
# List all matches
curl "$SERVICE_URL/matches/"

# Filter by pool
curl "$SERVICE_URL/matches/?pool_id=1"

# Filter by user
curl "$SERVICE_URL/matches/?user_id=100"

# Filter by status
curl "$SERVICE_URL/matches/?status_filter=accepted"
```

### 7. List Decisions

```bash
# List all decisions for a match
curl "$SERVICE_URL/decisions/?match_id=1"

# List all decisions by a user
curl "$SERVICE_URL/decisions/?user_id=100"
```

## Troubleshooting

### Service won't start

1. **Check logs:**
   ```bash
   gcloud run services logs read matches-service --region $REGION
   ```

2. **Common issues:**
   - Missing `INSTANCE_CONNECTION_NAME` env var
   - Incorrect `DB_PASS` or `DB_NAME`
   - Service account lacks `roles/cloudsql.client`
   - Database instance not `RUNNABLE`

### Database connection errors

1. **Verify connection name:**
   ```bash
   echo $INSTANCE_CONNECTION_NAME
   ```

2. **Test connection manually:**
   ```bash
   gcloud sql connect $SQL_INSTANCE_NAME --user=root
   ```

3. **Check IAM permissions:**
   ```bash
   gcloud projects get-iam-policy $PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:*compute*"
   ```

### Tables not created

The app creates tables on startup. If they're missing:

1. Check startup logs for errors
2. Manually create tables (see schema in `frameworks/db/models.py`)
3. Or use Alembic migrations (not included in this setup)

## Cleanup

To avoid ongoing charges:

```bash
# Delete Cloud Run service
gcloud run services delete matches-service --region $REGION

# Delete Cloud SQL instance (⚠️ deletes all data)
gcloud sql instances delete $SQL_INSTANCE_NAME

# Delete container image (optional)
gcloud container images delete gcr.io/$PROJECT_ID/matches-service:latest
```

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `INSTANCE_CONNECTION_NAME` | Cloud SQL connection name (e.g., cloudexploration-477701:us-central1:matches-db) | Yes (if no DATABASE_URL) |
| `DB_USER` | Database username | Yes (default: root) |
| `DB_PASS` | Database password | Yes |
| `DB_NAME` | Database name | Yes (default: matches) |
| `POOLS_SERVICE_URL` | URL to pools/composite service (same as service URL) | Yes |
| `DATABASE_URL` | Direct connection string | Alternative to Cloud SQL |
| `SQL_ECHO` | Log SQL queries | No (default: false) |
| `PRIVATE_IP` | Use private IP | No (default: false) |

## Event-Driven Match Cleanup Setup

After deploying the main service, set up the Cloud Function for automatic match cleanup:

```bash
# Create Pub/Sub topic
gcloud pubsub topics create user_left_pool

# Deploy Cloud Function
gcloud functions deploy match-cleanup-handler \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=./cloud_functions \
  --entry-point=handle_pool_event \
  --trigger-topic=user_left_pool \
  --set-env-vars=MATCHES_SERVICE_URL=$SERVICE_URL

# Test the function (optional)
gcloud pubsub topics publish user_left_pool \
  --message='{"event_type":"pool_member_removed","pool_id":"test-pool","user_id":"test-user","timestamp":"2025-01-01T00:00:00Z"}'
```

See `EVENTS_ARCHITECTURE.md` for detailed event flow documentation.

## Next Steps

- Set up Secret Manager for `DB_PASS` (recommended for production)
- Add Alembic for database migrations
- Set up monitoring and alerting
- Configure custom domain
- Add authentication/authorization

