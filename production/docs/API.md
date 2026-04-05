# Customer Success FTE API Documentation

## Overview
RESTful API for the Customer Success FTE system, providing endpoints for multi-channel customer support (Email, WhatsApp, Web Form), ticket management, and monitoring.

**Base URL:** `https://support-api.technova.com` (production)  
**Local URL:** `http://localhost:8000`  
**Version:** 2.0.0  
**OpenAPI Spec:** Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

---

## Authentication
Most endpoints are internal and rely on Kubernetes network policies. For external integrations:
```
Authorization: Bearer <API_KEY>
```

---

## Endpoints

### Health & Monitoring

#### Health Check
```
GET /health
```

**Description:** Check system health and channel status

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2026-04-05T10:30:00Z",
  "channels": {
    "email": "active",
    "whatsapp": "active",
    "web_form": "active"
  }
}
```

---

### Web Form Support

#### Submit Support Request
```
POST /support/submit
```

**Description:** Submit a support request via the web form. Creates a ticket and publishes to Kafka for processing.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Help with API authentication",
  "category": "technical",
  "priority": "medium",
  "message": "I'm having trouble authenticating with the API. Getting 401 errors."
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Customer name (min 2 characters) |
| email | string (EmailStr) | Yes | Valid email address |
| subject | string | Yes | Subject line (min 5 characters) |
| category | string | Yes | One of: `general`, `technical`, `billing`, `feedback`, `bug_report` |
| priority | string | No | One of: `low`, `medium`, `high` (default: `medium`) |
| message | string | Yes | Detailed message (min 10 characters) |
| attachments | array[string] | No | Base64 encoded files or URLs |

**Response:** `200 OK`
```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Thank you for contacting us! Our AI assistant will respond shortly.",
  "estimated_response_time": "Usually within 5 minutes"
}
```

**Validation Errors:** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error"
    }
  ]
}
```

---

#### Get Ticket Status
```
GET /support/ticket/{ticket_id}
```

**Description:** Retrieve status and conversation history for a support ticket

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| ticket_id | UUID | The ticket ID returned from submission |

**Response:** `200 OK`
```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "resolved",
  "messages": [
    {
      "id": "msg-001",
      "role": "customer",
      "channel": "web_form",
      "content": "I'm having trouble with API authentication",
      "created_at": "2026-04-05T10:00:00Z"
    },
    {
      "id": "msg-002",
      "role": "agent",
      "channel": "web_form",
      "content": "Hi John, I can help with that. Please check your API key...",
      "created_at": "2026-04-05T10:00:03Z"
    }
  ],
  "created_at": "2026-04-05T10:00:00Z",
  "last_updated": "2026-04-05T10:00:03Z"
}
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "Ticket not found"
}
```

---

### Webhooks

#### Gmail Webhook
```
POST /webhooks/gmail
```

**Description:** Handle Gmail push notifications via Google Pub/Sub. Processes incoming emails and creates tickets.

**Request Body:** (Google Pub/Sub format)
```json
{
  "message": {
    "data": "base64_encoded_notification",
    "messageId": "msg-123",
    "publishTime": "2026-04-05T10:00:00Z"
  },
  "subscription": "projects/technova/subscriptions/gmail-push"
}
```

**Response:** `200 OK`
```json
{
  "status": "processed",
  "count": 1
}
```

**Error Response:** `500 Internal Server Error`
```json
{
  "detail": "Failed to process Gmail notification: [error message]"
}
```

---

#### WhatsApp Webhook
```
POST /webhooks/whatsapp
```

**Description:** Handle incoming WhatsApp messages via Twilio webhook. Validates Twilio signature and processes messages.

**Request Body:** (Twilio form-data format)
```
MessageSid: SM123456
From: whatsapp:+1234567890
Body: Hello, I need help with my account
ProfileName: John Doe
WaId: 1234567890
```

**Headers:**
| Header | Description |
|--------|-------------|
| X-Twilio-Signature | Required. Webhook signature for validation |

**Response:** `200 OK` (TwiML)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

**Error Response:** `403 Forbidden`
```json
{
  "detail": "Invalid signature"
}
```

---

#### WhatsApp Status Webhook
```
POST /webhooks/whatsapp/status
```

**Description:** Handle WhatsApp message status updates (delivered, read, failed, etc.)

**Request Body:** (Twilio form-data format)
```
MessageSid: SM123456
MessageStatus: delivered
SmsStatus: delivered
```

**Response:** `200 OK`
```json
{
  "status": "received"
}
```

---

### Customer Management

#### Lookup Customer
```
GET /customers/lookup
```

**Description:** Look up a customer by email or phone across all channels

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | No* | Customer email address |
| phone | string | No* | Customer phone number |

*At least one of email or phone is required

**Response:** `200 OK`
```json
{
  "id": "cust-123",
  "email": "john@example.com",
  "phone": "+1234567890",
  "name": "John Doe",
  "created_at": "2026-03-01T10:00:00Z",
  "conversations": [
    {
      "id": "conv-456",
      "initial_channel": "web_form",
      "started_at": "2026-04-05T10:00:00Z",
      "status": "active",
      "sentiment_score": 0.75
    }
  ],
  "total_tickets": 5,
  "escalated_tickets": 1
}
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "Customer not found"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "detail": "Provide email or phone"
}
```

---

### Conversations

#### Get Conversation History
```
GET /conversations/{conversation_id}
```

**Description:** Retrieve full conversation history with cross-channel context

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| conversation_id | UUID | The conversation ID |

**Response:** `200 OK`
```json
{
  "id": "conv-456",
  "customer_id": "cust-123",
  "initial_channel": "web_form",
  "status": "active",
  "started_at": "2026-04-05T10:00:00Z",
  "messages": [
    {
      "id": "msg-001",
      "channel": "web_form",
      "direction": "inbound",
      "role": "customer",
      "content": "I need help with the API",
      "created_at": "2026-04-05T10:00:00Z"
    },
    {
      "id": "msg-002",
      "channel": "web_form",
      "direction": "outbound",
      "role": "agent",
      "content": "Hi! I'd be happy to help with the API...",
      "created_at": "2026-04-05T10:00:03Z",
      "latency_ms": 2500,
      "tool_calls": ["create_ticket", "search_knowledge_base", "send_response"]
    }
  ],
  "sentiment_score": 0.75,
  "channel_switches": []
}
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "Conversation not found"
}
```

---

### Metrics & Analytics

#### Channel Metrics
```
GET /metrics/channels
```

**Description:** Get performance metrics broken down by channel for the last 24 hours

**Response:** `200 OK`
```json
{
  "email": {
    "channel": "email",
    "total_conversations": 150,
    "avg_sentiment": 0.72,
    "escalations": 18
  },
  "whatsapp": {
    "channel": "whatsapp",
    "total_conversations": 230,
    "avg_sentiment": 0.68,
    "escalations": 35
  },
  "web_form": {
    "channel": "web_form",
    "total_conversations": 180,
    "avg_sentiment": 0.75,
    "escalations": 22
  }
}
```

---

## Error Codes

| HTTP Code | Meaning | Common Causes |
|-----------|---------|---------------|
| 400 | Bad Request | Missing required parameters |
| 403 | Forbidden | Invalid webhook signature |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error (invalid email, short message, etc.) |
| 500 | Internal Server Error | Database error, Kafka error, unhandled exception |
| 503 | Service Unavailable | System maintenance, database down |

---

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/support/submit` | 100 requests | per minute per IP |
| `/webhooks/*` | No limit (internal only) | - |
| `/customers/lookup` | 50 requests | per minute |
| `/conversations/*` | 50 requests | per minute |
| `/metrics/*` | 20 requests | per minute |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1617187200
```

---

## CORS Configuration

The API supports CORS for web form integration:
```python
allow_origins=["*"]  # Configure appropriately for production
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

**Production Recommendation:** Replace `["*"]` with specific domains:
```python
allow_origins=["https://technova.com", "https://app.technova.com"]
```

---

## Example Integrations

### Web Form Integration (JavaScript)
```javascript
async function submitSupportForm(formData) {
  const response = await fetch('https://support-api.technova.com/support/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Submission failed');
  }
  
  return await response.json();
}

// Usage
const result = await submitSupportForm({
  name: 'John Doe',
  email: 'john@example.com',
  subject: 'API Help',
  category: 'technical',
  message: 'I need help with authentication'
});

console.log(`Ticket created: ${result.ticket_id}`);
```

### Check Ticket Status (Python)
```python
import requests

def check_ticket_status(ticket_id):
    response = requests.get(f'https://support-api.technova.com/support/ticket/{ticket_id}')
    response.raise_for_status()
    return response.json()

# Usage
ticket = check_ticket_status('550e8400-e29b-41d4-a716-446655440000')
print(f"Status: {ticket['status']}")
print(f"Messages: {len(ticket['messages'])}")
```

### Lookup Customer (cURL)
```bash
curl -X GET "https://support-api.technova.com/customers/lookup?email=john@example.com"
```

---

## Webhook Setup Guides

### Gmail Pub/Sub Setup
1. Enable Gmail API in Google Cloud Console
2. Create a service account with Gmail API access
3. Create a Pub/Sub topic: `gmail-notifications`
4. Create a subscription with push endpoint: `https://your-domain.com/webhooks/gmail`
5. Watch inbox: `gmail.users().watch(userId='me', body={'topicName': 'projects/YOUR_PROJECT/topics/gmail-notifications'})`

### Twilio WhatsApp Setup
1. Create Twilio account and enable WhatsApp Sandbox
2. Get Account SID and Auth Token
3. Set webhook URL in Twilio console: `https://your-domain.com/webhooks/whatsapp`
4. Set status callback URL: `https://your-domain.com/webhooks/whatsapp/status`
5. Join sandbox by sending code to Twilio's WhatsApp number

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-04-05 | Multi-channel support, Kafka integration, Kubernetes deployment |
| 1.0.0 | 2026-03-01 | Initial release with web form support |
