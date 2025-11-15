# Reproducible deployment for FastAPI microservice (Cloud Run + Cloud SQL)

This document lists all steps (commands + notes) to reproduce the deployment you ran earlier.

IMPORTANT: Do NOT commit secrets (API keys, DB passwords). If the file `apikey` is in the repo, remove it and use Secret Manager (instructions below). If you accidentally committed a key, rotate/revoke it immediately.

## High-level steps

1. Verify local gcloud and authentication
2. Choose or create a GCP project and enable APIs
3. Create a Cloud SQL Postgres instance, database and user
4. Build the container image and push to registry (Cloud Build)
5. Deploy to Cloud Run with Cloud SQL socket
6. Test endpoints
7. Secure secrets (Secret Manager) and remove local API file
8. Cleanup when finished

---

## 1) Verify local gcloud & auth

```bash
# check gcloud version
gcloud --version

# check which account is active
gcloud auth list

# set account if needed
# gcloud config set account you@yourdomain
```

If `gcloud` is not authenticated, run `gcloud auth login` and follow the browser flow.

## 2) Set project and enable APIs

Replace `YOUR_PROJECT_ID` and `YOUR_REGION` below. Example region: `us-central1`.

```bash
export PROJECT_ID="YOUR_PROJECT_ID"
export REGION="us-central1"

gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com sqladmin.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

Permissions required: you must have roles to create Cloud SQL instances and deploy Cloud Run.

## 3) Create Cloud SQL Postgres instance, DB and user

We create a private instance (no public IP) and use Cloud Run's Cloud SQL support.

```bash
# instance name
export SQL_INSTANCE_NAME="microservice-db"

# create instance (this can take 5-10 minutes)
gcloud sql instances create $SQL_INSTANCE_NAME \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --no-assign-ip

# create database
gcloud sql databases create testdb --instance $SQL_INSTANCE_NAME

# set password for postgres user (example password below — choose a strong password)
export DB_PASSWORD="YOUR_DB_PASSWORD"
gcloud sql users set-password postgres --instance $SQL_INSTANCE_NAME --password "$DB_PASSWORD"

# get instance connection name for Cloud Run (use this in deploy step)
export INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $SQL_INSTANCE_NAME --format="value(connectionName)")
echo $INSTANCE_CONNECTION_NAME
```

Note: The instance is created in the project and region you configured. Instance creation will show `PENDING_CREATE` until done; then `RUNNABLE`.

## 4) Build and push container image

We use Cloud Build to avoid relying on a local Docker daemon.

```bash
# in repo root where Dockerfile exists
gcloud builds submit --tag gcr.io/$PROJECT_ID/microservice:latest --project $PROJECT_ID
```

This builds the image and pushes it to Google Container Registry (or Artifact Registry if you prefer). The build output will show a SUCCESS status when finished.

## 5) Deploy the service to Cloud Run (with Cloud SQL)

Important: the app expects an env var `INSTANCE_CONNECTION_NAME` when running on Cloud Run so it connects via the Cloud SQL Unix socket. We also set DB_USER, DB_PASSWORD and DB_NAME.

```bash
# deploy with Cloud SQL socket support
gcloud run deploy microservice \
  --image gcr.io/$PROJECT_ID/microservice:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars INSTANCE_CONNECTION_NAME="$INSTANCE_CONNECTION_NAME",DB_USER=postgres,DB_PASSWORD="$DB_PASSWORD",DB_NAME=testdb \
  --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
  --project $PROJECT_ID
```

Cloud Run will create a revision and attach the Cloud SQL Proxy socket for you. If deployment fails with "container failed to start and listen on port", check your `CMD`/`ENTRYPOINT` and ensure the container listens on port 8080 (or the port from env var `PORT`).

### IAM and roles

Grant your Cloud Run service account the Cloud SQL Client role so the service can connect to the instance (this is often automatically handled for the default compute service account but verify):

```bash
SERVICE_ACCOUNT=$(gcloud run services describe microservice --region $REGION --format="value(spec.template.spec.serviceAccountName)" )
# grant cloud sql client
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

(If you used a custom service account when deploying, grant the role to that SA.)

## 6) Test endpoints

After deploy completes, Cloud Run prints the service URL. You can also fetch it:

```bash
SERVICE_URL=$(gcloud run services describe microservice --region $REGION --format="value(status.url)")
echo $SERVICE_URL

# health
curl $SERVICE_URL/health

# create an item
curl -X POST $SERVICE_URL/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","description":"Testing Cloud SQL"}'

# list items
curl $SERVICE_URL/items

# get item
curl $SERVICE_URL/items/1
```

If items persist across requests, the Cloud SQL integration is working.

## 7) Secure secrets and remove local API file

If you have an `apikey` file in your repo with a real API key, remove it and store the key in Secret Manager instead. DO NOT commit secrets.

Steps:

```bash
# create secret for DB password
gcloud secrets create db-password --replication-policy="automatic" --project $PROJECT_ID
printf "%s" "$DB_PASSWORD" | gcloud secrets versions add db-password --project $PROJECT_ID --data-file=-

# create secret for any API key (if you have one)
# gcloud secrets create my-api-key --replication-policy="automatic"
# printf "%s" "<YOUR_API_KEY>" | gcloud secrets versions add my-api-key --data-file=-

# grant Cloud Run service account access to read the secret
# replace SERVICE_ACCOUNT if needed
SERVICE_ACCOUNT_EMAIL=$(gcloud run services describe microservice --region $REGION --format="value(spec.template.spec.serviceAccount)" --project $PROJECT_ID)
# (Sometimes the returned value may be blank; check in console and substitute the correct SA.)

# Example grant
# gcloud secrets add-iam-policy-binding db-password \
#   --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
#   --role="roles/secretmanager.secretAccessor" --project $PROJECT_ID

# Remove the apikey file from git (if present) and add to .gitignore
git rm --cached apikey || true
echo "apikey" >> .gitignore
git add .gitignore
git commit -m "Remove local API key and ignore it"

# Optionally: remove apikey file from disk
# rm apikey
```

To have Cloud Run read secrets into environment variables at deployment, use `--set-secrets`:

```bash
# example: load secret version into env var DB_PASSWORD
gcloud run deploy microservice \
  --image gcr.io/$PROJECT_ID/microservice:latest \
  --region $REGION \
  --platform managed \
  --set-secrets DB_PASSWORD=projects/$PROJECT_ID/secrets/db-password:latest \
  --add-cloudsql-instances $INSTANCE_CONNECTION_NAME
```

(When you use `--set-secrets`, you no longer need to set DB_PASSWORD directly with `--set-env-vars`.)

## 8) Cleanup resources

When you're done testing, delete resources to avoid ongoing charges:

```bash
# delete Cloud Run service
gcloud run services delete microservice --region $REGION --project $PROJECT_ID

# delete Cloud SQL instance (this deletes data)
gcloud sql instances delete $SQL_INSTANCE_NAME --project $PROJECT_ID

# delete image from Container Registry (optional)
# gcloud container images delete gcr.io/$PROJECT_ID/microservice:latest --project $PROJECT_ID --quiet
```

---

## Notes & troubleshooting

- If the Cloud Run revision fails to start: check container logs in Cloud Run logs and ensure your app listens on `0.0.0.0:$PORT` (uvicorn default is fine if you used the recommended `CMD` in the Dockerfile). The sample Dockerfile in this repo runs `uvicorn main:app --host 0.0.0.0 --port 8080`.

- If database connection fails: verify `INSTANCE_CONNECTION_NAME` is correct, the Cloud Run service has `roles/cloudsql.client`, and the Cloud SQL instance is `RUNNABLE`.

- If you need faster iteration, deploy a temporary in-memory version locally then switch to Cloud SQL once validated.

- If you accidentally committed a real API key (the file `apikey`), rotate it immediately.

---

If you want, I can also:
- Add `--set-secrets` deploy examples and automate Secret Manager binding in `deploy.sh`.
- Remove `apikey` from git history (use git filter-repo or BFG) — note this rewrites history and should be used carefully.

gcloud auth list
gcloud config get-value project