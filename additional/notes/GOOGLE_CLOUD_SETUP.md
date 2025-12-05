# Google Cloud Setup Guide

## Complete Setup Steps

### Prerequisites
- Google Cloud account
- `gcloud` CLI installed
- Project created on Google Cloud Console

---

## Step 1: Install Google Cloud CLI

```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

---

## Step 2: Initialize and Authenticate

```bash
# Login to your Google account
gcloud auth login

# Set your project (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable pubsub.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sqladmin.googleapis.com  # If using Cloud SQL
```

---

## Step 3: Create Pub/Sub Topic

```bash
# Create the topic for pool events
gcloud pubsub topics create pool-events

# Verify it was created
gcloud pubsub topics list

# Create a subscription (optional - for debugging/monitoring)
gcloud pubsub subscriptions create pool-events-debug \
    --topic pool-events \
    --ack-deadline 60
```

---

## Step 4: Setup Service Account Permissions

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")

# The Cloud Function will use this default service account
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant Pub/Sub permissions
gcloud pubsub topics add-iam-policy-binding pool-events \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/pubsub.publisher"

# If using Cloud SQL, grant database access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/cloudsql.client"
```

---

## Step 5: Deploy the Cloud Function

### Option A: Deploy from Local Files

```bash
# Navigate to cloud_functions directory
cd /Users/giovannibianco/Documents/Nice-2-Meet-U-Match/cloud_functions

# Deploy the function
gcloud functions deploy match-cleanup-handler \
    --gen2 \
    --runtime python311 \
    --region us-central1 \
    --source . \
    --entry-point handle_pool_event \
    --trigger-topic pool-events \
    --set-env-vars MATCHES_SERVICE_URL="https://your-matches-service-url.run.app" \
    --timeout 60s \
    --memory 256MB \
    --max-instances 10

# Note: Replace MATCHES_SERVICE_URL with your actual matches service URL
# For local testing: http://localhost:8000
# For Cloud Run: https://matches-service-xxxxx.run.app
```

### Option B: Deploy with Cloud SQL Connection

```bash
# If using Cloud SQL
gcloud functions deploy match-cleanup-handler \
    --gen2 \
    --runtime python311 \
    --region us-central1 \
    --source . \
    --entry-point handle_pool_event \
    --trigger-topic pool-events \
    --set-env-vars MATCHES_SERVICE_URL="https://your-matches-service-url.run.app" \
    --timeout 60s \
    --memory 256MB \
    --max-instances 10
```

---

## Step 6: Configure Your Application

### Update .env file

```bash
# Copy example file
cp .env.example .env

# Edit .env with your values
nano .env
```

Add these values:
```env
GCP_PROJECT_ID=your-actual-project-id
POOL_EVENTS_TOPIC=pool-events
ENABLE_EVENT_PUBLISHING=true
DATABASE_URL=mysql+pymysql://user:password@host:3306/database
```

### Install Dependencies

```bash
# Install the new dependency
pip install google-cloud-pubsub

# Or install all requirements
pip install -r requirements.txt
```

---

## Step 7: Verify the Setup

### Test Event Publishing

```bash
# Test publishing an event manually
gcloud pubsub topics publish pool-events \
    --message '{
        "event_type": "pool_member_removed",
        "pool_id": "11111111-1111-4111-8111-111111111111",
        "user_id": "22222222-2222-4222-8222-222222222222"
    }'
```

### Check Cloud Function Logs

```bash
# View recent logs
gcloud functions logs read match-cleanup-handler \
    --gen2 \
    --region us-central1 \
    --limit 50

# Stream logs in real-time
gcloud functions logs read match-cleanup-handler \
    --gen2 \
    --region us-central1 \
    --follow
```

### Test the Full Flow

```bash
# 1. Start your application locally
uvicorn main:app --reload

# 2. In another terminal, create a test scenario
# Add a user to a pool
curl -X POST http://localhost:8000/users/22222222-2222-4222-8222-222222222222/pool \
  -H "Content-Type: application/json" \
  -d '{"location": "New York", "coord_x": 40.7, "coord_y": -74.0}'

# 3. Generate some matches
curl -X POST http://localhost:8000/users/22222222-2222-4222-8222-222222222222/matches

# 4. Remove the user (this should trigger the event)
curl -X DELETE http://localhost:8000/users/22222222-2222-4222-8222-222222222222/pool

# 5. Check Cloud Function logs
gcloud functions logs read match-cleanup-handler --gen2 --region us-central1 --limit 10
```

---

## Step 8: Monitor and Debug

### View Pub/Sub Metrics

```bash
# Check topic details
gcloud pubsub topics describe pool-events

# List subscriptions
gcloud pubsub subscriptions list

# Pull messages from debug subscription (if created)
gcloud pubsub subscriptions pull pool-events-debug --limit 5
```

### Cloud Function Monitoring

```bash
# Get function details
gcloud functions describe match-cleanup-handler \
    --gen2 \
    --region us-central1

# View metrics in Cloud Console
# Go to: https://console.cloud.google.com/functions
# Click on your function → Metrics tab
```

### Common Issues

**Issue: Events not being published**
```bash
# Check if event publishing is enabled
echo $ENABLE_EVENT_PUBLISHING

# Check application logs
# Look for "Event publishing disabled" or "Published pool_member_removed event"
```

**Issue: Cloud Function not triggered**
```bash
# Check if subscription exists
gcloud functions describe match-cleanup-handler --gen2 --region us-central1 | grep trigger

# Manually trigger to test
gcloud pubsub topics publish pool-events \
    --message '{"event_type": "pool_member_removed", "pool_id": "test", "user_id": "test"}'
```

**Issue: Database connection fails**
```bash
# For Cloud SQL, ensure:
# 1. Cloud SQL Admin API is enabled
# 2. Service account has cloudsql.client role
# 3. Instance connection name is correct

# Test connection from Cloud Shell
gcloud sql connect YOUR_INSTANCE --user=YOUR_USER
```

---

## Step 9: Production Deployment

### Deploy to Cloud Run (Recommended)

```bash
# Build and deploy your main service
gcloud run deploy matches-service \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID \
    --set-env-vars POOL_EVENTS_TOPIC=pool-events \
    --set-env-vars ENABLE_EVENT_PUBLISHING=true \
    --set-env-vars DATABASE_URL="mysql+pymysql://..." \
    --set-cloud-sql-instances PROJECT_ID:REGION:INSTANCE_NAME
```

### Update Cloud Function for Production

```bash
# Redeploy with production settings
gcloud functions deploy match-cleanup-handler \
    --gen2 \
    --runtime python311 \
    --region us-central1 \
    --source ./cloud_functions \
    --entry-point handle_pool_event \
    --trigger-topic pool-events \
    --set-env-vars DATABASE_URL="production-connection-string" \
    --timeout 120s \
    --memory 512MB \
    --max-instances 100 \
    --min-instances 0
```

---

## Cost Estimation

### Pub/Sub
- **Messages**: $0.40 per million messages
- **Estimated**: ~1,000 user removals/day = $0.012/month

### Cloud Functions
- **Invocations**: $0.40 per million invocations
- **Compute time**: $0.0000025 per GB-second
- **Estimated**: ~1,000 invocations/day @ 256MB, 2s avg = $2-5/month

### Total: ~$5-10/month for moderate usage

---

## Security Best Practices

1. **Use Secret Manager for sensitive data**:
```bash
# Store database password
echo -n "your-db-password" | gcloud secrets create db-password --data-file=-

# Grant access to Cloud Function
gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

# Use in Cloud Function
--set-secrets 'DATABASE_PASSWORD=db-password:latest'
```

2. **Restrict Pub/Sub access**:
```bash
# Only allow your service to publish
gcloud pubsub topics remove-iam-policy-binding pool-events \
    --member="allUsers" \
    --role="roles/pubsub.publisher"
```

3. **Enable VPC connector for private DB access**:
```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create matches-connector \
    --region us-central1 \
    --range 10.8.0.0/28

# Use in Cloud Function
--vpc-connector matches-connector
```

---

## Troubleshooting Commands

```bash
# Check if APIs are enabled
gcloud services list --enabled

# View IAM permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Test Pub/Sub connectivity
gcloud pubsub topics publish pool-events --message "test"

# View Cloud Function source
gcloud functions describe match-cleanup-handler --gen2 --region us-central1

# Download Cloud Function logs
gcloud functions logs read match-cleanup-handler --gen2 --region us-central1 --limit 100 > logs.txt
```

---

## Next Steps

1. ✅ Complete Steps 1-7 above
2. ✅ Test locally with event publishing enabled
3. ✅ Deploy to production
4. 📊 Set up monitoring and alerting
5. 🔒 Implement security best practices
6. 📈 Monitor costs and optimize

---

## Support

- [Cloud Functions Documentation](https://cloud.google.com/functions/docs)
- [Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
