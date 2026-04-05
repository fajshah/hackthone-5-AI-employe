# P1 - OpenAI API Degradation Runbook

## Severity: P1 - High
**Trigger:** OpenAI API responses failing, timing out, or returning errors

## Impact
- Agent cannot generate responses
- Customers receiving error messages or no responses
- Increased escalation rate to human agents
- Degraded customer experience

## Detection
- Alert: `OpenAIApiErrorRate` - >20% of OpenAI API calls failing
- Alert: `OpenAIApiLatency` - P95 latency >10 seconds
- Alert: `AgentResponseFailures` - >15% of agent runs failing
- Symptoms: `RateLimitError`, `APIConnectionError`, `Timeout`, `InvalidRequestError`

## Immediate Actions (0-15 minutes)

### 1. Diagnose the Issue
```bash
# Check agent logs for OpenAI errors
kubectl logs -n customer-success-fte -l component=message-processor --tail=100 | grep -i 'openai\|error'

# Check error types
kubectl logs -n customer-success-fte -l component=message-processor --tail=500 | grep -oE 'RateLimitError|APIConnectionError|Timeout|InvalidRequestError' | sort | uniq -c

# Check current API latency
kubectl logs -n customer-success-fte -l component=message-processor --tail=50 | grep -oE 'latency_ms=[0-9]+' | tail -20
```

### 2. Check OpenAI Status
```bash
# Check OpenAI status page
curl -s https://status.openai.com/api/v2/status.json | python -m json.tool

# Check your API key validity
python -c "
import openai
openai.api_key = 'YOUR_API_KEY'
try:
    response = openai.ChatCompletion.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': 'test'}],
        max_tokens=10
    )
    print('API key is valid')
except Exception as e:
    print(f'API key error: {e}')
"
```

## Recovery Procedures

### Scenario A: Rate Limiting
```bash
# Check current request rate
kubectl logs -n customer-success-fte -l component=message-processor --since=5m | grep -c 'openai'

# Reduce concurrent requests by scaling down
kubectl scale deployment/fte-message-processor -n customer-success-fte --replicas=2

# Implement request queuing in message processor
# Edit workers/message_processor.py to add rate limiting
```

**Code Fix for Rate Limiting:**
```python
# Add to workers/message_processor.py
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    async def acquire(self):
        now = datetime.utcnow()
        # Remove old requests outside the window
        self.requests = [r for r in self.requests if r > now - timedelta(seconds=self.window_seconds)]
        
        if len(self.requests) >= self.max_requests:
            # Wait until the oldest request expires
            wait_time = (self.requests[0] + timedelta(seconds=self.window_seconds) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)

# Initialize rate limiter (adjust based on your tier)
rate_limiter = RateLimiter(max_requests=50, window_seconds=60)

# In process_message(), before calling OpenAI:
await rate_limiter.acquire()
```

### Scenario B: API Outage
```bash
# Enable fallback mode
# Set environment variable to use fallback responses
kubectl set env deployment/fte-message-processor -n customer-success-fte OPENAI_FALLBACK_MODE=true

# Notify customers of delayed responses
# Update web form response message
kubectl edit configmap fte-config -n customer-success-fte
# Change WEBFORM_RESPONSE_MESSAGE to indicate delay
```

**Fallback Response Implementation:**
```python
# Add to workers/message_processor.py
FALLBACK_RESPONSES = {
    'technical': "Thank you for your question. Our AI assistant is temporarily unavailable. A human agent will respond within 30 minutes. Your ticket has been logged.",
    'billing': "Thank you for contacting us. Our billing team will review your inquiry and respond within 2 hours. Your ticket has been logged.",
    'general': "Thank you for reaching out. Our support team will respond to your inquiry shortly. Your ticket has been logged."
}

if openai_fallback_mode:
    category = categorize_message(message)
    response = FALLBACK_RESPONSES.get(category, FALLBACK_RESPONSES['general'])
    await send_response(ticket_id, response, channel)
    await escalate_to_human(ticket_id, reason="openai_api_unavailable")
```

### Scenario C: Invalid API Key or Quota Exceeded
```bash
# Rotate API key
# 1. Get new API key from OpenAI dashboard
# 2. Update Kubernetes secret
kubectl create secret generic fte-secrets -n customer-success-fte \
  --from-literal=OPENAI_API_KEY=new_key_here \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart pods to pick up new secret
kubectl rollout restart deployment/fte-message-processor -n customer-success-fte
kubectl rollout restart deployment/fte-api -n customer-success-fte

# 4. Monitor for successful API calls
kubectl logs -n customer-success-fte -l component=message-processor --tail=50 | grep -i 'openai'
```

### Scenario D: Timeout Issues
```bash
# Increase timeout in agent configuration
# Edit agent/customer_success_agent.py to add timeout parameter

# Add to your OpenAI client initialization:
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
)

# Reduce model complexity (use gpt-4o-mini instead of gpt-4o)
# Edit agent/customer_success_agent.py:
customer_success_agent = Agent(
    name="Customer Success FTE",
    model="gpt-4o-mini",  # Faster, cheaper alternative
    ...
)
```

## Communication Template

### Initial Notification (Slack #fte-alerts)
```
⚠️ P1 INCIDENT: OpenAI API Degradation
- Impact: Agent responses failing/slow
- Error rate: [X]%
- Started: [TIME]
- Investigating: [NAME]
- Fallback mode: [ENABLED/DISABLED]
```

### Update (if resolved)
```
✅ RESOLVED: OpenAI API Degradation
- Root cause: [Rate limiting / Outage / Key issue]
- Resolution: [ACTION TAKEN]
- Duration: [X minutes]
- Failed requests: [COUNT]
- Customer impact: [YES/NO]
```

## Post-Incident Checklist
- [ ] API key rotated (if compromised)
- [ ] Rate limiting implemented in code
- [ ] Fallback mode tested
- [ ] Monitoring alerts adjusted
- [ ] Cost impact assessed
- [ ] Post-mortem completed (if outage >30 minutes)
- [ ] Runbook updated if needed
