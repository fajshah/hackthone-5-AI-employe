# Workers Module

Background workers for message processing with Kafka integration.

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `message_processor.py` | Main Kafka consumer worker | 800+ |
| `__init__.py` | Module exports | - |
| `requirements.txt` | Dependencies | - |
| `README.md` | Documentation | - |

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Kafka     │────▶│ MessageProcessor │────▶│    Agent    │
│  (Topics)   │     │   (This Worker)  │     │  (Agent)    │
└─────────────┘     └──────────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Database   │
                    │ (PostgreSQL)│
                    └─────────────┘
```

---

## Message Processor

### Workflow

```
1. CONSUME from Kafka
   └─→ Topics: channel-email, channel-whatsapp, channel-webform
   
2. RESOLVE Customer
   └─→ Lookup by email/phone
   └─→ Create if new
   
3. GET/CREATE Conversation
   └─→ Find active conversation
   └─→ Create new if needed
   └─→ Session timeout: 30 min
   
4. CALL Agent
   └─→ agent.process_message()
   └─→ Timeout: 30 seconds
   
5. STORE in Database
   └─→ Customer message
   └─→ Agent response
   
6. PUBLISH Response
   └─→ Topic: agent-responses
   └─→ Or: agent-escalations
```

---

## Kafka Topics

### Input Topics

| Topic | Purpose |
|-------|---------|
| `channel-email` | Email messages from Gmail |
| `channel-whatsapp` | WhatsApp messages from Twilio |
| `channel-webform` | Web form submissions |

### Output Topics

| Topic | Purpose |
|-------|---------|
| `agent-responses` | Agent responses to customers |
| `agent-escalations` | Escalations to human agents |
| `{topic}-errors` | Processing errors |

---

## Usage

### Start Worker

```python
from workers import create_message_processor

# Create processor
processor = create_message_processor()

# Start (async)
await processor.start()
```

### Command Line

```bash
# Set environment
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export DATABASE_URL="postgresql://postgres:password@localhost:5432/technova"

# Run worker
python -m workers.message_processor
```

### With Docker

```bash
docker-compose up -d kafka postgres
python workers/message_processor.py
```

---

## Configuration

### Kafka

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:9092,localhost:9093
KAFKA_CONSUMER_GROUP=technova-message-processor
KAFKA_AUTO_OFFSET_RESET=latest
KAFKA_ENABLE_AUTO_COMMIT=false

# Topics
KAFKA_TOPIC_EMAIL=channel-email
KAFKA_TOPIC_WHATSAPP=channel-whatsapp
KAFKA_TOPIC_WEBFORM=channel-webform
KAFKA_TOPIC_RESPONSES=agent-responses
KAFKA_TOPIC_ESCALATIONS=agent-escalations

# Consumer
KAFKA_POLL_TIMEOUT_MS=1000
KAFKA_MAX_POLL_RECORDS=100
```

### Processing

```bash
MAX_CONCURRENT_MESSAGES=10
MESSAGE_PROCESSING_TIMEOUT_SECONDS=30
RETRY_ON_FAILURE=true
MAX_RETRIES=3
SESSION_TIMEOUT_MINUTES=30
HEALTH_CHECK_INTERVAL_SECONDS=30
```

---

## Customer Resolution

### Priority Order

1. **Email address** (highest priority)
2. **Phone number**
3. **Customer ID** (if provided)
4. **Create new customer**

### Example

```python
from workers import CustomerResolver

# From Kafka message
kafka_message = KafkaMessage(...)

# Resolve customer
customer = await CustomerResolver.resolve_customer(kafka_message)

# Returns:
# {
#   "customer_id": "CUST-ABC123",
#   "name": "John Doe",
#   "email": "john@example.com",
#   "phone": "+1234567890",
#   ...
# }
```

---

## Conversation Management

### Features

- **Automatic thread detection** - Links related messages
- **Session timeout** - 30 minutes of inactivity
- **Cache** - In-memory active conversation cache
- **Database persistence** - All conversations stored

### Example

```python
from workers import ConversationManager

# Get or create conversation
conversation = await ConversationManager.get_or_create_conversation(
    customer=customer,
    kafka_message=kafka_message
)

# Returns:
# {
#   "conversation_id": "CONV-XYZ789",
#   "customer_id": "CUST-ABC123",
#   "channel": "email",
#   ...
# }
```

---

## Message Flow Example

### 1. Email Received

```json
{
  "message_id": "MSG-001",
  "topic": "channel-email",
  "data": {
    "from": "john@example.com",
    "subject": "Integration Help",
    "body": "How do I integrate with Slack?"
  }
}
```

### 2. Customer Resolved

```python
customer = {
    "customer_id": "CUST-ABC123",
    "name": "John Doe",
    "email": "john@example.com"
}
```

### 3. Conversation Created

```python
conversation = {
    "conversation_id": "CONV-XYZ789",
    "customer_id": "CUST-ABC123",
    "channel": "email"
}
```

### 4. Agent Processes

```python
response = await agent.process_message(message)
# response.response_text = "Hi John, Here's how to integrate..."
# response.ticket_id = "TKT-001"
```

### 5. Response Published

```json
{
  "message_id": "MSG-001",
  "ticket_id": "TKT-001",
  "response": "Hi John, Here's how to integrate with Slack...",
  "channel": "email"
}
```

---

## Error Handling

### Retry Logic

```python
# Automatic retry on failure
RETRY_ON_FAILURE=true
MAX_RETRIES=3

# Retry count tracked in headers
headers = {
    "retry_count": "1",
    "original_timestamp": "2024-01-01T10:00:00Z"
}
```

### Timeout

```python
# Message processing timeout
MESSAGE_PROCESSING_TIMEOUT_SECONDS=30

# Raises asyncio.TimeoutError if exceeded
```

### Error Publishing

```python
# Errors published to {topic}-errors
{
  "message_id": "MSG-001",
  "error": "Failed to resolve customer",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

---

## Statistics

### Get Stats

```python
stats = processor.get_stats()

# Returns:
# {
#   "messages_processed": 1000,
#   "messages_failed": 5,
#   "escalations": 23,
#   "start_time": datetime(...),
#   "uptime_seconds": 3600,
#   "is_running": True
# }
```

### Health Check

```bash
# Stats logged every 30 seconds
INFO - Stats | Processed: 1000 | Failed: 5 | Escalations: 23 | Uptime: 1:00:00
```

---

## Database Schema

### Tables Used

| Table | Purpose |
|-------|---------|
| `customers` | Customer profiles |
| `conversations` | Conversation threads |
| `messages` | Individual messages |
| `tickets` | Support tickets |

### Message Storage

```python
# Customer message
MessageQueries.create_message(
    message_id="MSG-001",
    conversation_id="CONV-XYZ",
    customer_id="CUST-ABC",
    role="customer",
    content="How do I integrate...",
    channel="email"
)

# Agent response
MessageQueries.create_message(
    message_id="MSG-002",
    conversation_id="CONV-XYZ",
    customer_id="CUST-ABC",
    role="agent",
    content="Hi! Here's how...",
    channel="email"
)
```

---

## Scaling

### Horizontal Scaling

```bash
# Run multiple workers (same consumer group)
python workers/message_processor.py  # Worker 1
python workers/message_processor.py  # Worker 2
python workers/message_processor.py  # Worker 3

# Kafka distributes messages across workers
```

### Concurrency

```bash
# Messages processed concurrently
MAX_CONCURRENT_MESSAGES=10

# Each worker can process 10 messages in parallel
```

---

## Monitoring

### Logs

```bash
# Processing logs
INFO - Processing message MSG-001 from channel-email
INFO - Customer resolved: CUST-ABC123
INFO - Conversation: CONV-XYZ789
INFO - Message MSG-001 processed in 450ms (ticket: TKT-001)

# Stats logs
INFO - Stats | Processed: 1000 | Failed: 5 | Escalations: 23 | Uptime: 1:00:00
```

### Metrics to Track

- Messages processed per second
- Average processing time
- Error rate
- Escalation rate
- Consumer lag

---

## Testing

### Unit Test

```python
import pytest
from workers import MessageProcessor, KafkaMessage

async def test_message_processor():
    processor = create_message_processor()
    
    # Create test message
    message = KafkaMessage(
        message_id="TEST-001",
        source=MessageSource.EMAIL,
        raw_data={"email": "test@example.com", "body": "Help!"},
        ...
    )
    
    # Process
    await processor._process_message(message)
    
    # Assert
    assert processor.stats['messages_processed'] == 1
```

---

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY workers/ ./workers/
COPY agent/ ./agent/
COPY database/ ./database/

CMD ["python", "-m", "workers.message_processor"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: message-processor
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: processor
        image: technova/message-processor:latest
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

---

**Ready for production!** 🚀
