# P1 - Channel Webhook Failures Runbook

## Severity: P1 - High
**Trigger:** Gmail, WhatsApp, or Web Form webhooks returning errors

## Impact
- Incoming tickets from affected channel not being processed
- Customers not receiving responses
- Potential message loss if webhooks not retried
- Channel-specific outage

## Detection
- Alert: `WebhookErrorRate` - >10% of webhook requests returning 4xx/5xx
- Alert: `ChannelDown` - Specific channel not receiving messages for >5 minutes
- Symptoms: `403 Forbidden`, `500 Internal Server Error`, `502 Bad Gateway`, `504 Gateway Timeout`

## Immediate Actions (0-15 minutes)

### 1. Identify Affected Channel(s)
```bash
# Check API logs for webhook errors
kubectl logs -n customer-success-fte -l component=api --tail=100 | grep -i 'webhook\|error'

# Check error rates by channel
kubectl logs -n customer-success-fte -l component=api --since=10m | grep -oE 'webhook/(gmail|whatsapp)' | sort | uniq -c

# Check health endpoint
curl http://localhost:8000/health | python -m json.tool
```

### 2. Test Each Channel
```bash
# Test web form endpoint
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Webhook Test",
    "category": "general",
    "message": "Testing webhook endpoint"
  }'

# Test Gmail webhook (simulate Pub/Sub notification)
curl -X POST http://localhost:8000/webhooks/gmail \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "data": "dGVzdA==",
      "messageId": "test-123"
    }
  }'

# Test WhatsApp webhook (simulate Twilio webhook)
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -d "MessageSid=SM123" \
  -d "From=whatsapp:+1234567890" \
  -d "Body=Test message"
```

## Recovery Procedures

### Scenario A: Gmail Webhook Failures

**Issue:** 403 Forbidden or authentication errors
```bash
# Check Gmail credentials
kubectl get secret fte-secrets -n customer-success-fte -o jsonpath='{.data.GMAIL_CREDENTIALS}' | base64 -d

# Verify Gmail API is enabled in Google Cloud Console
# Check if service account has Gmail API scope

# Refresh OAuth tokens
kubectl exec -n customer-success-fte -it <api-pod> -- python -c "
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Re-authenticate and update credentials
flow = InstalledAppFlow.from_client_secrets_file(
    '/path/to/credentials.json',
    scopes=['https://www.googleapis.com/auth/gmail.modify']
)
creds = flow.run_local_server(port=0)
print(creds.to_json())
"

# Update Pub/Sub subscription
kubectl exec -n customer-success-fte -it <api-pod> -- python -c "
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('your-project', 'gmail-notifications')

# Verify subscription exists
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path('your-project', 'gmail-push-sub')

try:
    subscription = subscriber.get_subscription(request={'subscription': subscription_path})
    print(f'Subscription exists: {subscription_path}')
except Exception as e:
    print(f'Subscription error: {e}')
"
```

**Issue:** Gmail API rate limiting
```bash
# Gmail API has rate limits, implement exponential backoff
# Check channels/gmail_handler.py for retry logic

# Add retry decorator if missing:
from tenacity import retry, stop_after_attempt, wait_exponential

class GmailHandler:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def process_notification(self, pubsub_message: dict) -> dict:
        # Existing implementation
        pass
```

### Scenario B: WhatsApp/Twilio Webhook Failures

**Issue:** Invalid signature validation
```bash
# Check Twilio credentials
kubectl get secret fte-secrets -n customer-success-fte -o jsonpath='{.data.TWILIO_AUTH_TOKEN}' | base64 -d

# Verify webhook URL in Twilio console matches your endpoint
# Should be: https://your-domain.com/webhooks/whatsapp

# Check webhook validation logic
kubectl logs -n customer-success-fte -l component=api --tail=50 | grep -i 'twilio\|signature'

# Test signature validation
python -c "
from twilio.request_validator import RequestValidator

validator = RequestValidator('YOUR_AUTH_TOKEN')
url = 'https://your-domain.com/webhooks/whatsapp'
params = {
    'MessageSid': 'SM123',
    'From': 'whatsapp:+1234567890',
    'Body': 'Test'
}
signature = 'SIGNATURE_FROM_HEADERS'

is_valid = validator.validate(url, params, signature)
print(f'Signature valid: {is_valid}')
"
```

**Issue:** Twilio account issues (suspended, quota exceeded)
```bash
# Check Twilio account status
# Login to Twilio console: https://console.twilio.com

# Verify WhatsApp sandbox is still active
# Check if you've exceeded message quota

# Update Twilio webhook URL if domain changed
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/YOUR_SID/Messages/IncomingPhoneNumbers.json" \
  -u "YOUR_SID:YOUR_TOKEN" \
  -d "PhoneNumber=YOUR_WHATSAPP_NUMBER" \
  -d "SmsUrl=https://your-domain.com/webhooks/whatsapp"
```

### Scenario C: Web Form Endpoint Failures

**Issue:** 500 Internal Server Error
```bash
# Check API pod logs
kubectl logs -n customer-success-fte -l component=api --tail=100

# Check for database connection issues
kubectl exec -n customer-success-fte -it <api-pod> -- python -c "
import asyncpg
import asyncio

async def test_db():
    try:
        conn = await asyncpg.connect(
            host='postgres.customer-success-fte.svc.cluster.local',
            database='fte_db',
            user='fte_user'
        )
        await conn.fetchval('SELECT 1')
        print('Database connection OK')
        await conn.close()
    except Exception as e:
        print(f'Database error: {e}')

asyncio.run(test_db())
"

# Check for Kafka connection issues
kubectl exec -n customer-success-fte -it <api-pod> -- python -c "
from kafka import KafkaProducer
import json

try:
    producer = KafkaProducer(
        bootstrap_servers='kafka.customer-success-fte.svc.cluster.local:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    producer.send('fte.tickets.incoming', {'test': 'message'})
    producer.flush()
    print('Kafka connection OK')
except Exception as e:
    print(f'Kafka error: {e}')
"
```

**Issue:** CORS errors from web form
```bash
# Check CORS configuration in api/main.py
# Ensure your domain is in allowed origins

# Update CORS settings
kubectl edit configmap fte-config -n customer-success-fte
# Add/modify: ALLOWED_ORIGINS=https://your-domain.com

# Restart API pods
kubectl rollout restart deployment/fte-api -n customer-success-fte
```

## Communication Template

### Initial Notification (Slack #fte-alerts)
```
⚠️ P1 INCIDENT: Channel Webhook Failures
- Affected channel(s): [Gmail / WhatsApp / Web Form]
- Error rate: [X]%
- Started: [TIME]
- Investigating: [NAME]
- Customer impact: [YES/NO]
```

### Update (if resolved)
```
✅ RESOLVED: Channel Webhook Failures
- Affected channel: [CHANNEL]
- Root cause: [DESCRIPTION]
- Resolution: [ACTION TAKEN]
- Duration: [X minutes]
- Messages affected: [COUNT]
```

## Post-Incident Checklist
- [ ] All channels tested and working
- [ ] Webhook signatures validated
- [ ] Credentials rotated (if compromised)
- [ ] Retry logic implemented for all channels
- [ ] Monitoring alerts adjusted
- [ ] Post-mortem completed (if outage >1 hour)
- [ ] Runbook updated if needed
