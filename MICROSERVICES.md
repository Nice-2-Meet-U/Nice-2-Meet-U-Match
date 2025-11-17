# Microservices Architecture Guide

## Overview

This application is designed as a **true microservices architecture** where each service communicates via HTTP APIs rather than direct function calls.

## Services

### 1. **Pool Service** (`/pools`)
- Manages pools and pool memberships
- Endpoints:
  - `POST /pools` - Create pool
  - `GET /pools` - List pools
  - `POST /pools/{pool_id}/members` - Add member
  - `GET /pools/{pool_id}/members` - List members

### 2. **Match Service** (`/matches`)
- Manages matches between users
- Endpoints:
  - `POST /matches` - Create match
  - `GET /matches` - List matches
  - `GET /matches/{match_id}` - Get match

### 3. **Decision Service** (`/decisions`)
- Manages user decisions on matches
- Endpoints:
  - `POST /decisions` - Submit decision
  - `GET /decisions` - List decisions

### 4. **User Service** (`/users`) - **Composite/Orchestrator**
- Orchestrates other services via HTTP calls
- Endpoints:
  - `POST /users/{user_id}/add-to-pool` - Adds user to pool (calls Pool Service)
  - `POST /users/{user_id}/generate-matches` - Generates matches (calls Pool + Match + Decision Services)

## Architecture Patterns

### Composite Microservice
The **User Service** acts as a composite/orchestrator:
- Makes HTTP calls to Pool, Match, and Decision services
- Aggregates data from multiple services
- Returns composite responses

### Service Communication
```
┌──────────────┐
│ User Service │ (Orchestrator)
└──────┬───────┘
       │ HTTP
       ├─────────> ┌──────────────┐
       │           │ Pool Service │
       │           └──────────────┘
       │
       ├─────────> ┌───────────────┐
       │           │ Match Service │
       │           └───────────────┘
       │
       └─────────> ┌──────────────────┐
                   │ Decision Service │
                   └──────────────────┘
```

## Deployment Options

### Option 1: Single Process (Development)
Run all services in one process (current setup):
```bash
uvicorn main:app --reload --port 8000
```

All services share the same base URL. Service clients default to `localhost:8000`.

### Option 2: Separate Processes (True Microservices)

#### Terminal 1 - Pool Service
```bash
export SERVICE_NAME=pool
uvicorn main:app --port 8001
```

#### Terminal 2 - Match Service
```bash
export SERVICE_NAME=match
uvicorn main:app --port 8002
```

#### Terminal 3 - Decision Service
```bash
export SERVICE_NAME=decision
uvicorn main:app --port 8003
```

#### Terminal 4 - User Service
```bash
export POOL_SERVICE_URL=http://localhost:8001
export MATCH_SERVICE_URL=http://localhost:8002
export DECISION_SERVICE_URL=http://localhost:8003
uvicorn main:app --port 8004
```

### Option 3: Docker Compose
```yaml
version: '3.8'
services:
  pool:
    build: .
    ports: ["8001:8000"]
    environment:
      - SERVICE_NAME=pool
      
  match:
    build: .
    ports: ["8002:8000"]
    environment:
      - SERVICE_NAME=match
      
  decision:
    build: .
    ports: ["8003:8000"]
    environment:
      - SERVICE_NAME=decision
      
  user:
    build: .
    ports: ["8004:8000"]
    environment:
      - POOL_SERVICE_URL=http://pool:8000
      - MATCH_SERVICE_URL=http://match:8000
      - DECISION_SERVICE_URL=http://decision:8000
```

### Option 4: Kubernetes
Deploy each service as a separate deployment with service discovery.

## Configuration

### Environment Variables

Create `.env` file:
```bash
# Service URLs (for User Service)
POOL_SERVICE_URL=http://pool-service:8000
MATCH_SERVICE_URL=http://match-service:8000
DECISION_SERVICE_URL=http://decision-service:8000

# Database
DATABASE_URL=your_database_connection_string
```

## Benefits of This Architecture

✅ **Independent Scaling** - Scale services independently based on load
✅ **Technology Agnostic** - Services can be rewritten in different languages
✅ **Fault Isolation** - One service failure doesn't bring down the system
✅ **Team Autonomy** - Different teams can own different services
✅ **Flexible Deployment** - Deploy services on different infrastructure

## Trade-offs

⚠️ **Network Latency** - HTTP calls add latency vs direct function calls
⚠️ **Distributed Transactions** - Need to handle eventual consistency
⚠️ **Operational Complexity** - More moving parts to monitor and debug
⚠️ **Service Discovery** - Need to manage service locations

## Next Steps

1. **API Gateway** - Add Kong/Nginx for routing and rate limiting
2. **Service Mesh** - Add Istio for advanced traffic management
3. **Circuit Breakers** - Add resilience with retry/timeout patterns
4. **Observability** - Add distributed tracing (Jaeger/Zipkin)
5. **Message Queue** - Use RabbitMQ/Kafka for async communication
