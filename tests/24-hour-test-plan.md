# 24-Hour Multi-Channel Test Plan

## Overview
This document defines the comprehensive 24-hour continuous operation test for the Customer Success FTE. The test validates that the system can handle real-world traffic across all channels while maintaining reliability, performance, and accuracy.

## Test Objectives
- ✅ Validate 24/7 operational readiness
- ✅ Test multi-channel intake and response
- ✅ Verify cross-channel conversation continuity
- ✅ Measure performance under sustained load
- ✅ Test chaos resilience (pod failures, restarts)
- ✅ Validate monitoring and alerting
- ✅ Ensure zero message loss

## Test Duration
**24 hours continuous operation**

## Traffic Requirements

### Web Form Traffic (100+ submissions)
- **Rate:** ~4-5 submissions per hour
- **Pattern:** Random intervals (every 10-20 minutes)
- **Categories:** Mix of technical, billing, general, feedback, bug reports
- **Expected:** All submissions receive AI response within 5 minutes

### Email Simulation (50+ messages)
- **Rate:** ~2-3 messages per hour
- **Pattern:** Simulated Gmail Pub/Sub notifications
- **Types:** How-to questions, bug reports, feature inquiries
- **Expected:** All emails processed and responded to within 30 seconds

### WhatsApp Simulation (50+ messages)
- **Rate:** ~2-3 messages per hour
- **Pattern:** Simulated Twilio webhooks
- **Types:** Short questions, status checks, casual inquiries
- **Expected:** All messages processed with concise responses

### Cross-Channel (10+ customers)
- **Scenario:** Same customer contacts via multiple channels
- **Expected:** Conversation history preserved, context maintained
- **Validation:** Customer identified correctly across channels (>95% accuracy)

## Performance Metrics

### Uptime
- **Target:** >99.9%
- **Measurement:** Health check endpoint polled every 30 seconds
- **Acceptable Downtime:** <2.6 minutes total

### Response Latency
- **P50 (Median):** <1.5 seconds
- **P95:** <3 seconds
- **P99:** <5 seconds
- **Measurement:** Agent processing time (excluding delivery)

### Escalation Rate
- **Target:** <25%
- **Measurement:** Escalated tickets / Total tickets
- **Expected:** 15-20% for test dataset

### Cross-Channel Identification
- **Target:** >95% accuracy
- **Measurement:** Correctly identified customers / Total cross-channel interactions
- **Validation:** Customer ID matches across channels

### Message Loss
- **Target:** 0 messages lost
- **Measurement:** Messages received vs. messages processed
- **Validation:** All webhooks result in tickets created

## Chaos Testing

### Pod Kills (Every 2 hours)
**Schedule:**
- Hour 2: Kill 1 API pod
- Hour 4: Kill 1 worker pod
- Hour 6: Kill 2 API pods simultaneously
- Hour 8: Kill database pod (test recovery)
- Hour 10: Kill Kafka pod (test recovery)
- Hour 12: Kill all worker pods (test scaling)
- Hour 14: Kill 1 API + 1 worker pod
- Hour 16: Kill database pod again
- Hour 18: Kill Kafka pod again
- Hour 20: Kill 2 API + 1 worker pod
- Hour 22: Kill random pod (any component)

**Expected Behavior:**
- System recovers within 2 minutes
- No message loss during pod kills
- Health checks fail briefly, then recover
- HPA scales up pods automatically

### Network Partition Simulation
**Test:** Block network access to OpenAI API for 5 minutes (Hour 12)
**Expected:**
- Fallback mode activates
- Apologetic responses sent
- Escalations created for affected tickets
- System recovers when network restored

### Database Connection Loss
**Test:** Kill database connections for 1 minute (Hour 16)
**Expected:**
- Error responses sent to customers
- Messages queued in Kafka
- System recovers when database back online
- Queued messages processed

## Monitoring Checklist

### Continuous Monitoring (Every 5 minutes)
- [ ] Health endpoint returning 200 OK
- [ ] All pods in Running state
- [ ] No CrashLoopBackOff pods
- [ ] CPU usage <70% average
- [ ] Memory usage <80% average
- [ ] Database connections <80
- [ ] Kafka consumer lag <1000
- [ ] Error rate <5%

### Hourly Checks
- [ ] Total tickets processed in last hour
- [ ] Average response time in last hour
- [ ] Escalation rate in last hour
- [ ] Channel breakdown (email/whatsapp/web)
- [ ] Sentiment distribution
- [ ] No alerts firing in Prometheus

### Every 6 Hours
- [ ] Database disk space >20% free
- [ ] Kafka disk space >20% free
- [ ] Log files rotating properly
- [ ] Backup completed (if scheduled)
- [ ] Review error logs for patterns

## Test Execution Procedure

### Pre-Test Setup (1 hour before)

1. **Deploy fresh instance:**
```bash
cd production
./scripts/deploy.sh
```

2. **Verify deployment:**
```bash
kubectl get pods -n customer-success-fte
kubectl get svc -n customer-success-fte
curl http://localhost:8000/health
```

3. **Seed knowledge base:**
```bash
python scripts/seed_kb.py
```

4. **Run baseline tests:**
```bash
cd tests
python -m pytest test_multichannel_e2e.py -v
```

5. **Start monitoring:**
```bash
# Port-forward Prometheus/Grafana
kubectl port-forward svc/prometheus -n customer-success-fte 9090:9090
kubectl port-forward svc/grafana -n customer-success-fte 3000:3000
```

### Test Execution (24 hours)

#### Hour 0: Start Test
```bash
# Start traffic generation
python tests/generate_traffic.py --duration 24h --config tests/24h-test-config.yaml

# Start monitoring script
python tests/monitor.py --interval 5m --output tests/24h-results.json
```

#### Hour 2-22: Chaos Events
```bash
# Automated chaos script runs on schedule
python tests/chaos_monkey.py --schedule tests/chaos-schedule.yaml
```

#### Continuous: Monitor Dashboard
- Grafana dashboard: http://localhost:3000/d/fte-dashboard
- Prometheus alerts: http://localhost:9090/alerts
- API health: http://localhost:8000/health

### Post-Test Analysis (1 hour after)

1. **Stop traffic generation:**
```bash
# Kill traffic generation process
pkill -f generate_traffic
```

2. **Collect metrics:**
```bash
curl http://localhost:8000/metrics/channels > tests/final-metrics.json
```

3. **Generate report:**
```bash
python tests/generate_report.py --input tests/24h-results.json --output tests/24h-report.md
```

4. **Validate results:**
- [ ] Uptime >99.9%
- [ ] P95 latency <3 seconds
- [ ] Escalation rate <25%
- [ ] Cross-channel ID >95%
- [ ] Zero message loss
- [ ] All chaos events survived

5. **Clean up:**
```bash
# Optionally delete test namespace
kubectl delete namespace customer-success-fte-test
```

## Traffic Generation Script

```python
# tests/generate_traffic.py
import asyncio
import httpx
import random
import time
from datetime import datetime

CATEGORIES = ['general', 'technical', 'billing', 'feedback', 'bug_report']
PRIORITIES = ['low', 'medium', 'high']

TEST_MESSAGES = {
    'technical': [
        "How do I create a Kanban board?",
        "Can you explain how Gantt charts work?",
        "I need help setting up integrations",
        "How do I use the AI insights feature?"
    ],
    'billing': [
        "I have a question about my subscription",
        "How do I upgrade my plan?",
        "Can I get an invoice for last month?",
        "What payment methods do you accept?"
    ],
    'general': [
        "What features are available?",
        "How many projects can I create?",
        "Can I export my data?",
        "Is there a mobile app?"
    ],
    'feedback': [
        "Love the new update! Any plans for dark mode?",
        "Great product, but could you add X feature?",
        "The UI is really intuitive, thanks!",
        "Would be nice to have more customization options"
    ],
    'bug_report': [
        "The dashboard widget isn't loading",
        "I'm getting an error when I try to upload files",
        "Mobile app crashes when I open large projects",
        "Notifications stopped working yesterday"
    ]
}

async def submit_web_form(client: httpx.AsyncClient):
    """Submit a support form."""
    category = random.choice(CATEGORIES)
    message = random.choice(TEST_MESSAGES[category])
    
    response = await client.post("/support/submit", json={
        "name": f"Test User {random.randint(1, 10000)}",
        "email": f"test{random.randint(1, 10000)}@example.com",
        "subject": f"Test: {category.title()}",
        "category": category,
        "priority": random.choice(PRIORITIES),
        "message": message
    })
    
    return response.status_code == 200

async def simulate_email(client: httpx.AsyncClient):
    """Simulate incoming email via webhook."""
    category = random.choice(CATEGORIES)
    message = random.choice(TEST_MESSAGES[category])
    
    response = await client.post("/webhooks/gmail", json={
        "message": {
            "data": "base64_encoded_test_data",
            "messageId": f"test-{int(time.time())}"
        }
    })
    
    return response.status_code == 200

async def simulate_whatsapp(client: httpx.AsyncClient):
    """Simulate incoming WhatsApp via webhook."""
    short_messages = [
        "how do I add a task?",
        "can I upgrade my plan?",
        "app keeps crashing 😕",
        "need help with billing",
        "love the product! 🎉"
    ]
    
    response = await client.post("/webhooks/whatsapp", data={
        "MessageSid": f"SM{int(time.time())}",
        "From": f"whatsapp:+1{random.randint(1000000000, 9999999999)}",
        "Body": random.choice(short_messages)
    })
    
    return response.status_code in [200, 403]  # 403 is expected without valid signature

async def run_test(duration_hours: int = 24):
    """Run 24-hour traffic generation."""
    start_time = time.time()
    duration_seconds = duration_hours * 3600
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        while time.time() - start_time < duration_seconds:
            # Submit web form (every 10-20 minutes)
            if random.random() < 0.1:  # ~10% chance per minute
                await submit_web_form(client)
            
            # Simulate email (every 20-30 minutes)
            if random.random() < 0.05:
                await simulate_email(client)
            
            # Simulate WhatsApp (every 20-30 minutes)
            if random.random() < 0.05:
                await simulate_whatsapp(client)
            
            await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    asyncio.run(run_test(duration_hours=24))
```

## Success Criteria

The test is considered **PASSED** if ALL criteria are met:

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| Uptime | >99.9% | [FILLED] | [ ] |
| P95 Latency | <3 seconds | [FILLED] | [ ] |
| Escalation Rate | <25% | [FILLED] | [ ] |
| Cross-Channel ID | >95% | [FILLED] | [ ] |
| Message Loss | 0 | [FILLED] | [ ] |
| Chaos Survival | 100% | [FILLED] | [ ] |
| Web Form Submissions | 100+ | [FILLED] | [ ] |
| Email Messages | 50+ | [FILLED] | [ ] |
| WhatsApp Messages | 50+ | [FILLED] | [ ] |
| Cross-Channel Customers | 10+ | [FILLED] | [ ] |

## Sign-Off

**Test Executed By:** _________________  
**Date:** _________________  
**Result:** ☐ PASSED  ☐ FAILED  

**Notes:**
_____________________________________________
_____________________________________________
_____________________________________________

**Approved By:** _________________  
**Date:** _________________
