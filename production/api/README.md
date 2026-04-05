# TechNova Support API

Complete REST API for customer support automation.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export API_KEY="your-api-key"
export DATABASE_URL="postgresql://postgres:password@localhost:5432/technova"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"

# Run server
python -m api.main
```

## Endpoints

### Support

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/support/submit` | Submit support request |
| GET | `/support/status/{ticket_id}` | Get ticket status |
| GET | `/support/tickets` | List user tickets |

### Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/customers/{customer_id}` | Get customer |
| PUT | `/customers/{customer_id}` | Update customer |
| GET | `/customers/{customer_id}/history` | Get history |

### Tickets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tickets` | List tickets |
| GET | `/tickets/{ticket_id}` | Get ticket |
| PUT | `/tickets/{ticket_id}` | Update ticket |
| POST | `/tickets/{ticket_id}/escalate` | Escalate ticket |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/gmail` | Gmail webhook |
| POST | `/webhooks/whatsapp` | WhatsApp webhook |
| POST | `/webhooks/twilio` | Twilio webhook |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/stats` | System statistics |
| GET | `/admin/metrics` | Detailed metrics |
| GET | `/admin/escalations` | List escalations |

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe |
| GET | `/metrics` | API metrics |
| GET | `/metrics/prometheus` | Prometheus metrics |
| GET | `/docs` | Swagger docs |
| GET | `/redoc` | ReDoc docs |

## Usage Examples

### Submit Support Request

```bash
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "email": "customer@example.com",
    "name": "John Doe",
    "subject": "Integration Help",
    "message": "How do I integrate with Slack?"
  }'
```

Response:
```json
{
  "ticket_id": "TKT-ABC123",
  "status": "received",
  "message": "Your support request has been submitted successfully.",
  "email": "customer@example.com",
  "submitted_at": "2024-01-01T10:00:00Z"
}
```

### Get Ticket Status

```bash
curl http://localhost:8000/support/status/TKT-ABC123 \
  -H "X-API-Key: your-api-key"
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Configuration

```bash
# Server
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_DEBUG=false

# Security
API_KEY=your-api-key-change-in-production
API_KEY_HEADER=X-API-Key
ENABLE_CORS=true
CORS_ORIGINS=*
ALLOWED_HOSTS=*

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Kafka
KAFKA_ENABLED=true
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/technova

# Logging
LOG_LEVEL=INFO
LOG_REQUESTS=true
```

## Authentication

Most endpoints require API key authentication:

```bash
# Header
X-API-Key: your-api-key

# Or Bearer token
Authorization: Bearer your-api-key

# Or query param (for webhooks)
?api_key=your-api-key
```

## Rate Limiting

Default: 100 requests per minute per IP

Configure via environment:
```bash
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

## Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY api/requirements.txt .
RUN pip install -r requirements.txt

COPY api/ ./api/
COPY agent/ ./agent/
COPY database/ ./database/
COPY kafka_client.py .

EXPOSE 8000
CMD ["python", "-m", "api.main"]
```

## Kubernetes

```yaml
apiVersion: v1
kind: Service
metadata:
  name: support-api
spec:
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: support-api
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: support-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: support-api
  template:
    spec:
      containers:
      - name: api
        image: technova/support-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secret
              key: api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Testing

```bash
# Run tests
pytest api/tests/

# Test health endpoint
curl http://localhost:8000/health

# Test support submission
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","subject":"Test","message":"Test message"}'
```

## Monitoring

### Prometheus Metrics

```
# HELP technova_api_requests_total Total number of requests
# TYPE technova_api_requests_total counter
technova_api_requests_total 1000

# HELP technova_api_uptime_seconds API uptime in seconds
# TYPE technova_api_uptime_seconds gauge
technova_api_uptime_seconds 3600
```

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "version": "1.0.0",
  "components": {
    "api": {"status": "healthy"},
    "database": {"status": "healthy"},
    "kafka": {"status": "healthy"},
    "agent": {"status": "healthy"}
  }
}
```

---

**API ready for production!** 🚀
