# Kafka Client Module

Complete Kafka client with producers, consumers, and all topic definitions.

## File

| File | Purpose | Lines |
|------|---------|-------|
| `kafka_client.py` | Complete Kafka client | 1000+ |

---

## Topics (20 Topics)

### Channel Ingestion
- `channel-email` - Email messages
- `channel-whatsapp` - WhatsApp messages
- `channel-webform` - Web form submissions

### Agent
- `agent-requests` - Agent processing requests
- `agent-responses` - Agent responses
- `agent-escalations` - Escalations to humans

### System
- `system-events` - System events
- `system-logs` - System logs
- `system-metrics` - Metrics

### Customer Events
- `customer-created` - New customer
- `customer-updated` - Customer update
- `conversation-started` - New conversation
- `conversation-closed` - Conversation ended

### Ticket Events
- `ticket-created` - New ticket
- `ticket-updated` - Ticket update
- `ticket-resolved` - Ticket resolved
- `ticket-escalated` - Ticket escalated

### Dead Letter Queues
- `dlq-channel-email` - Email DLQ
- `dlq-channel-whatsapp` - WhatsApp DLQ
- `dlq-channel-webform` - Web form DLQ
- `dlq-agent` - Agent DLQ

### Error Topics
- `errors-processing` - Processing errors
- `errors-validation` - Validation errors

---

## Usage

### Synchronous Producer

```python
from kafka_client import SyncKafkaProducer

with SyncKafkaProducer() as producer:
    # Send email
    result = producer.send_email({
        "from": "customer@example.com",
        "subject": "Help needed",
        "body": "How do I integrate..."
    })
    print(f"Sent: {result}")
    
    # Send WhatsApp
    producer.send_whatsapp({
        "from": "+1234567890",
        "body": "Quick question"
    })
    
    # Send escalation
    producer.send_escalation({
        "ticket_id": "TKT-001",
        "reason": "Billing dispute"
    })
```

### Asynchronous Producer

```python
from kafka_client import AsyncKafkaProducer

async with AsyncKafkaProducer() as producer:
    # Send message
    await producer.send(
        topic="channel-email",
        value={"email": "test@example.com"}
    )
    
    # Send with transaction
    async with producer.transaction():
        await producer.send("topic1", {"data": "value1"})
        await producer.send("topic2", {"data": "value2"})
```

### Synchronous Consumer

```python
from kafka_client import SyncKafkaConsumer

def process_message(msg):
    print(f"Received: {msg['value']}")

with SyncKafkaConsumer("channel-email", group_id="my-group") as consumer:
    consumer.consume(process_message)
```

### Asynchronous Consumer

```python
from kafka_client import AsyncKafkaConsumer

async def process_message(msg):
    print(f"Received: {msg['value']}")

async with AsyncKafkaConsumer("channel-email", group_id="my-group") as consumer:
    async for message in consumer.consume(process_message):
        print(f"Processed: {message['message_id']}")
```

### Kafka Client Factory

```python
from kafka_client import KafkaClient

client = KafkaClient()

# Get producer
producer = client.get_sync_producer()
producer.send_email({...})

# Get consumer
consumer = client.get_async_consumer(
    topics=["channel-email", "channel-whatsapp"],
    group_id="processor-group"
)
```

---

## Message Format

All messages follow standard envelope:

```json
{
  "message_id": "uuid-here",
  "message_type": "email",
  "payload": {
    "from": "customer@example.com",
    "subject": "Help",
    "body": "Message content"
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "source": "gmail-handler",
  "correlation_id": "uuid-here",
  "reply_to": "agent-responses",
  "headers": {
    "message_type": "email",
    "source": "gmail-handler",
    "created_at": "2024-01-01T10:00:00Z"
  },
  "metadata": {}
}
```

---

## Configuration

```bash
# Connection
KAFKA_BOOTSTRAP_SERVERS=localhost:9092,localhost:9093
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# Producer
KAFKA_PRODUCER_ACKS=all
KAFKA_PRODUCER_RETRIES=3
KAFKA_PRODUCER_BATCH_SIZE=16384
KAFKA_PRODUCER_LINGER_MS=1
KAFKA_PRODUCER_COMPRESSION=gzip

# Consumer
KAFKA_CONSUMER_GROUP=technova-group
KAFKA_AUTO_OFFSET_RESET=latest
KAFKA_ENABLE_AUTO_COMMIT=false
KAFKA_MAX_POLL_RECORDS=500
KAFKA_SESSION_TIMEOUT_MS=30000

# Topics
KAFKA_REPLICATION_FACTOR=1
KAFKA_NUM_PARTITIONS=3

# Retry
KAFKA_RETRY_BACKOFF_MS=100
KAFKA_RETRY_MAX_MS=10000
```

---

## Features

### Producer

- ✅ Sync and async modes
- ✅ Automatic serialization
- ✅ Compression (gzip)
- ✅ Retry logic
- ✅ Transactions (async)
- ✅ Convenience methods per topic

### Consumer

- ✅ Sync and async modes
- ✅ Automatic deserialization
- ✅ Manual/auto commit
- ✅ Seek (beginning/end)
- ✅ Multi-topic subscription
- ✅ Consumer groups

### Message

- ✅ Standardized envelope
- ✅ Headers support
- ✅ Correlation ID
- ✅ Reply-to routing
- ✅ JSON serialization

---

## Error Handling

### Producer Errors

```python
from kafka_client import SyncKafkaProducer
from kafka.errors import KafkaTimeoutError, KafkaError

producer = SyncKafkaProducer()

try:
    producer.send_email({...})
except KafkaTimeoutError:
    print("Send timeout")
except KafkaError as e:
    print(f"Kafka error: {e}")
finally:
    producer.close()
```

### Consumer Errors

```python
from kafka_client import SyncKafkaConsumer

def safe_callback(msg):
    try:
        process(msg)
    except Exception as e:
        logger.error(f"Processing error: {e}")
        # Don't re-raise, continue processing

consumer = SyncKafkaConsumer("channel-email")
consumer.consume(safe_callback)
```

---

## Dead Letter Queue

```python
from kafka_client import SyncKafkaProducer

producer = SyncKafkaProducer()

# Send to DLQ on processing failure
try:
    process_message(msg)
except Exception as e:
    producer.send_to_dlq(
        original_topic=msg['topic'],
        message_data=msg['value'],
        error=str(e)
    )
```

---

## Monitoring

### Producer Stats

```python
producer = SyncKafkaProducer()
result = producer.send_email({...})

print(f"Topic: {result['topic']}")
print(f"Partition: {result['partition']}")
print(f"Offset: {result['offset']}")
```

### Consumer Lag

```python
from kafka import KafkaConsumer
from kafka.structs import TopicPartition

consumer = KafkaConsumer('channel-email', group_id='my-group')

# Get current position
position = consumer.position(TopicPartition('channel-email', 0))

# Get end offsets
end_offsets = consumer.end_offsets([TopicPartition('channel-email', 0)])

# Lag = end - position
lag = end_offsets[TopicPartition('channel-email', 0)] - position
```

---

## Testing

```python
import pytest
from kafka_client import SyncKafkaProducer, SyncKafkaConsumer

def test_producer_consumer():
    producer = SyncKafkaProducer()
    consumer = SyncKafkaConsumer("test-topic", group_id="test-group")
    
    # Send
    result = producer.send("test-topic", {"test": "data"})
    
    # Receive
    messages = consumer.poll(timeout_ms=1000)
    
    assert len(messages) == 1
    assert messages[0]['value']['test'] == 'data'
```

---

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

RUN pip install kafka-python aiokafka

COPY kafka_client.py /app/
COPY workers/ /app/workers/

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
        image: technova/processor:latest
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka-headless:9092"
```

---

**Complete Kafka client ready!** 🚀
