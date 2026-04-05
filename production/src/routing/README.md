# Production Module: Routing

**Purpose:** Escalation decision and ticket routing

## Components

### `escalation_engine.py`
- 10 escalation rule evaluation
- Priority matrix implementation
- Target team assignment
- Escalation confidence scoring

**Rules:**
| Rule ID | Name | Priority | Target |
|---------|------|----------|--------|
| ESC-001 | Enterprise Integration | P1 | Solutions Engineering |
| ESC-002 | Refund/Billing Dispute | P1 | Billing Team |
| ESC-003 | Legal/Compliance | P0 | Legal Team |
| ESC-004 | Angry Customer | P0 | Senior Support |
| ESC-005 | System Outage | P0 | Engineering |
| ESC-006 | Data Loss/Security | P0 | Security Team |
| ESC-007 | VIP Customer | P1 | Dedicated Support |
| ESC-008 | API/Integration Issue | P2 | Technical Support |
| ESC-009 | Cancellation Request | P1 | Retention Team |
| ESC-010 | Feature Request | P3 | Product Team |

### `router.py`
- AI vs human decision
- Queue assignment
- Load balancing across agents
- Round-robin for human queues

### `sla_tracker.py`
- SLA deadline calculation per priority
- Breach prediction & alerting
- Escalation timeout monitoring

## Input/Output

**Input:** Analyzed ticket (intent, sentiment, entities, priority)

**Output:**
```python
{
    "should_escalate": True,
    "escalation_rule": "ESC-002",
    "priority": "P1",
    "target_team": "billing",
    "target_queue": "billing-queue-1",
    "sla_deadline": "2026-04-01T11:30:00Z",
    "ai_can_handle": False,
    "handoff_summary": "..."
}
```

## Decision Logic
```
IF escalation_rule_matched AND rule.requires_human:
    → Human Queue
ELSE IF sentiment < -0.7:
    → Human Queue (with AI draft)
ELSE IF confidence < 0.6:
    → Human Queue
ELSE:
    → AI Response Generator
```
