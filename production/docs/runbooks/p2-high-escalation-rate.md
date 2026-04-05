# P2 - High Escalation Rate Runbook

## Severity: P2 - Medium
**Trigger:** Escalation rate exceeds 25% threshold

## Impact
- More tickets being escalated to human agents than expected
- Increased workload for human support team
- Potential issues with AI agent accuracy or knowledge base
- Customer experience degradation

## Detection
- Alert: `HighEscalationRate` - Escalation rate >25% over 1-hour window
- Alert: `EscalationSpike` - Sudden increase in escalations (>50% above baseline)
- Metrics: Check `/metrics/channels` endpoint for escalation counts

## Immediate Actions (0-1 hour)

### 1. Analyze Escalation Patterns
```bash
# Get current escalation rate
curl http://localhost:8000/metrics/channels | python -m json.tool

# Check recent escalations in database
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT 
    source_channel,
    COUNT(*) as total_tickets,
    COUNT(*) FILTER (WHERE status = 'escalated') as escalated,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'escalated') / COUNT(*), 2) as escalation_rate
FROM tickets
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY source_channel;
"

# Check escalation reasons
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT 
    resolution_notes,
    COUNT(*) as count
FROM tickets
WHERE status = 'escalated' 
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY resolution_notes
ORDER BY count DESC
LIMIT 20;
"
```

### 2. Identify Root Cause
```bash
# Check agent logs for common escalation triggers
kubectl logs -n customer-success-fte -l component=message-processor --since=1h | grep -i 'escalat' | head -20

# Check if knowledge base search is failing
kubectl logs -n customer-success-fte -l component=message-processor --since=1h | grep -i 'no relevant\|not found' | wc -l

# Check sentiment analysis results
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT 
    CASE 
        WHEN sentiment_score >= 0.7 THEN 'positive'
        WHEN sentiment_score >= 0.4 THEN 'neutral'
        WHEN sentiment_score >= 0.3 THEN 'frustrated'
        ELSE 'angry'
    END as sentiment_category,
    COUNT(*) as count
FROM conversations
WHERE started_at > NOW() - INTERVAL '1 hour'
GROUP BY sentiment_category;
"
```

## Recovery Procedures

### Scenario A: Knowledge Base Gaps
```bash
# Identify common queries that aren't being answered
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT 
    m.content as customer_message,
    t.category,
    t.source_channel
FROM messages m
JOIN tickets t ON t.conversation_id = m.conversation_id
WHERE m.role = 'customer'
  AND t.status = 'escalated'
  AND m.created_at > NOW() - INTERVAL '1 hour'
ORDER BY m.created_at DESC
LIMIT 50;
"

# Add missing knowledge base entries
# Edit context/product-docs.md with missing information
# Then re-seed the knowledge base
kubectl exec -n customer-success-fte -it <api-pod> -- python scripts/seed_kb.py

# Verify new entries are searchable
kubectl exec -n customer-success-fte -it <api-pod> -- python -c "
# Test search for previously failing queries
from agent.tools import search_knowledge_base, KnowledgeSearchInput
import asyncio

async def test():
    result = await search_knowledge_base(KnowledgeSearchInput(query='YOUR_QUERY_HERE', max_results=5))
    print(result)

asyncio.run(test())
"
```

### Scenario B: Sentiment Analysis Too Sensitive
```bash
# Check if too many customers are being flagged as angry
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE sentiment_score < 0.3) as angry,
    ROUND(100.0 * COUNT(*) FILTER (WHERE sentiment_score < 0.3) / COUNT(*), 2) as angry_percent
FROM conversations
WHERE started_at > NOW() - INTERVAL '1 hour';
"

# If angry percent is abnormally high (>30%), sentiment analysis may be broken
# Check sentiment analysis implementation in agent/tools.py

# Temporary fix: Adjust escalation threshold
# Edit agent/customer_success_agent.py instructions:
# Change "sentiment < 0.3" to "sentiment < 0.2" temporarily
```

### Scenario C: Agent Instructions Too Restrictive
```bash
# Review agent instructions
kubectl exec -n customer-success-fte -it <api-pod> -- python -c "
from agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
print(CUSTOMER_SUCCESS_SYSTEM_PROMPT)
"

# Common issues to check:
# 1. Too many escalation triggers
# 2. Overly strict constraints
# 3. Missing response templates for common scenarios

# Update instructions if needed
# Edit agent/prompts.py and reduce escalation triggers
# Then restart message processor
kubectl rollout restart deployment/fte-message-processor -n customer-success-fte
```

### Scenario D: Product Change Causing Confusion
```bash
# Check if there's a recent product update causing customer confusion
# Review recent escalations for common themes

kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT 
    resolution_notes,
    source_channel,
    created_at
FROM tickets
WHERE status = 'escalated'
  AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC
LIMIT 30;
"

# If common theme emerges, update knowledge base
# Create announcement or FAQ in product docs
# Update brand voice guidelines if needed
```

## Long-Term Improvements

### 1. Implement Escalation Rate Dashboard
```yaml
# Add to Grafana dashboard
- title: "Escalation Rate by Channel"
  type: graph
  targets:
    - expr: rate(tickets_escalated_total[1h]) / rate(tickets_created_total[1h]) * 100
      legendFormat: "{{channel}}"
```

### 2. Add Escalation Feedback Loop
```python
# Add to workers/message_processor.py
async def analyze_escalations():
    """Review recent escalations and identify patterns."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get recent escalations
        escalations = await conn.fetch("""
            SELECT t.resolution_notes, c.initial_channel, 
                   m.content as customer_message
            FROM tickets t
            JOIN conversations c ON c.id = t.conversation_id
            JOIN messages m ON m.conversation_id = c.id
            WHERE t.status = 'escalated'
              AND t.created_at > NOW() - INTERVAL '24 hours'
              AND m.role = 'customer'
            ORDER BY t.created_at DESC
            LIMIT 100
        """)
        
        # Analyze patterns
        reasons = {}
        for esc in escalations:
            reason = esc['resolution_notes']
            reasons[reason] = reasons.get(reason, 0) + 1
        
        # Alert if any reason exceeds threshold
        for reason, count in reasons.items():
            if count > 10:  # More than 10 escalations for same reason
                await send_alert(f"High escalation count for: {reason} ({count} times)")

# Run this analysis every hour
```

### 3. Implement A/B Testing for Instructions
```python
# Test different instruction sets to find optimal configuration
# Route 50% of traffic to current instructions
# Route 50% to modified instructions
# Compare escalation rates after 24 hours
```

## Communication Template

### Initial Notification (Slack #fte-alerts)
```
⚠️ P2 ALERT: High Escalation Rate
- Current rate: [X]%
- Threshold: 25%
- Time period: Last [1 hour / 24 hours]
- Most common reason: [REASON]
- Investigating: [NAME]
```

### Update (if resolved)
```
✅ RESOLVED: High Escalation Rate
- Root cause: [DESCRIPTION]
- Resolution: [ACTION TAKEN]
- Current rate: [X]% (back to normal)
- Duration: [X hours]
- Follow-up: [Knowledge base update / Instruction change / etc.]
```

## Post-Incident Checklist
- [ ] Root cause identified
- [ ] Knowledge base updated with missing information
- [ ] Agent instructions optimized if needed
- [ ] Escalation rate monitoring improved
- [ ] Feedback loop implemented
- [ ] Post-mortem completed (if rate >30% for >4 hours)
- [ ] Runbook updated if needed
