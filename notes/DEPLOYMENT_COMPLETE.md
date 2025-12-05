# ✅ Deployment Complete!

Your Matches microservice has been successfully deployed to Google Cloud Run with Cloud SQL.

## Deployment Details

### Service Information
- **Service URL**: https://matches-service-870022169527.us-central1.run.app
- **Project ID**: cloudexploration-477701
- **Region**: us-central1
- **Service Name**: matches-service

### Database Information
- **Instance Name**: matches-db
- **Database Name**: matches
- **Database Version**: MySQL 8.0
- **Instance Connection Name**: `cloudexploration-477701:us-central1:matches-db`
- **Tier**: db-f1-micro

### API Endpoints
- **Health Check**: `GET /`
- **API Documentation**: `GET /docs` (Swagger UI)
- **OpenAPI Schema**: `GET /openapi.json`
- **Matches**: 
  - `POST /matches/` - Create a match
  - `GET /matches/{match_id}` - Get a match
  - `GET /matches/` - List matches (with filters)
  - `PATCH /matches/{match_id}` - Update a match
- **Decisions**:
  - `POST /decisions/` - Submit a decision
  - `GET /decisions/` - List decisions (with filters)

## Testing the Deployment

### 1. Health Check
```bash
curl https://matches-service-870022169527.us-central1.run.app/
```

Expected response:
```json
{
    "status": "ok",
    "service": "matches",
    "version": "1.0.0"
}
```

### 2. View API Documentation
Open in browser: https://matches-service-870022169527.us-central1.run.app/docs

### 3. Create a Pool (Required First Step)

You need to create a pool in the database first. The pool ID must be a UUID.

**Option A: Using Python with Cloud SQL Connector**
```python
from google.cloud.sql.connector import Connector
import pymysql
from uuid import uuid4

connector = Connector()
def getconn():
    return connector.connect(
        'cloudexploration-477701:us-central1:matches-db',
        'pymysql',
        user='root',
        password='YOUR_PASSWORD',  # Get from /tmp/db_password.txt
        db='matches',
    )

conn = getconn()
cursor = conn.cursor()
pool_id = str(uuid4())
cursor.execute(
    "INSERT INTO pools (id, name, location, member_count) VALUES (%s, %s, %s, %s)",
    (pool_id, 'Test Pool', 'NYC', 0)
)
conn.commit()
print(f"Created pool with ID: {pool_id}")
cursor.close()
conn.close()
connector.close()
```

**Option B: Using Cloud SQL Proxy**
1. Install Cloud SQL Proxy
2. Connect and run SQL directly

### 4. Create a Match

```bash
export POOL_ID="your-pool-uuid-here"
export USER1_ID="11111111-1111-4111-8111-111111111111"
export USER2_ID="22222222-2222-4222-8222-222222222222"

curl -X POST "https://matches-service-870022169527.us-central1.run.app/matches/" \
  -H "Content-Type: application/json" \
  -d "{
    \"pool_id\": \"$POOL_ID\",
    \"user1_id\": \"$USER1_ID\",
    \"user2_id\": \"$USER2_ID\"
  }"
```

### 5. Submit Decisions

```bash
export MATCH_ID="match-uuid-from-step-4"

# User 1 accepts
curl -X POST "https://matches-service-870022169527.us-central1.run.app/decisions/" \
  -H "Content-Type: application/json" \
  -d "{
    \"match_id\": \"$MATCH_ID\",
    \"user_id\": \"$USER1_ID\",
    \"decision\": \"accept\"
  }"

# User 2 accepts (match becomes accepted)
curl -X POST "https://matches-service-870022169527.us-central1.run.app/decisions/" \
  -H "Content-Type: application/json" \
  -d "{
    \"match_id\": \"$MATCH_ID\",
    \"user_id\": \"$USER2_ID\",
    \"decision\": \"accept\"
  }"
```

### 6. Get Match Status

```bash
curl "https://matches-service-870022169527.us-central1.run.app/matches/$MATCH_ID"
```

## Environment Variables

The service is configured with:
- `INSTANCE_CONNECTION_NAME`: `cloudexploration-477701:us-central1:matches-db`
- `DB_USER`: `root`
- `DB_NAME`: `matches`
- `DB_PASS`: (stored securely, see `/tmp/db_password.txt` on deployment machine)

## IAM Permissions

The Cloud Run service account has been granted:
- `roles/cloudsql.client` - To connect to Cloud SQL

## Troubleshooting

### Database Connection Issues

If you see authentication errors in logs:
1. Check the password is correctly set: `cat /tmp/db_password.txt`
2. Verify environment variables: `gcloud run services describe matches-service --region us-central1`
3. Check logs: `gcloud run services logs read matches-service --region us-central1`

### Tables Not Created

The app creates tables on startup. If they're missing:
1. Check startup logs for errors
2. The error might be due to authentication - verify DB_PASS is correct
3. Tables should be created automatically on first successful connection

### View Logs

```bash
gcloud run services logs read matches-service \
  --region us-central1 \
  --project cloudexploration-477701 \
  --limit 50
```

## Cleanup Commands

To remove all resources:

```bash
# Delete Cloud Run service
gcloud run services delete matches-service \
  --region us-central1 \
  --project cloudexploration-477701

# Delete Cloud SQL instance (⚠️ deletes all data)
gcloud sql instances delete matches-db \
  --project cloudexploration-477701

# Delete container image
gcloud container images delete gcr.io/cloudexploration-477701/matches-service:latest
```

## Next Steps

1. **Create initial pools** in the database
2. **Test the API** using the examples above
3. **Set up monitoring** in Cloud Console
4. **Configure custom domain** (optional)
5. **Add authentication** for production use
6. **Use Secret Manager** for DB_PASS (recommended for production)

## Files Created During Deployment

- `/tmp/db_password.txt` - Database password (on deployment machine)
- `/tmp/connection_name.txt` - Connection name (on deployment machine)

---

**Deployment completed successfully!** 🎉

The service is live and ready to accept requests.

