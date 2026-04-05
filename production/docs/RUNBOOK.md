# Incident Response Runbooks

## Overview
This document contains incident response runbooks for the Customer Success FTE system. Each runbook provides step-by-step procedures for handling specific production incidents.

## Runbook Index
| Runbook | Priority | Trigger |
|---------|----------|---------|
| [P0 - Database Outage](runbooks/p0-database-outage.md) | P0 - Critical | PostgreSQL unavailable, all ticket operations fail |
| [P0 - Kafka Cluster Failure](runbooks/p0-kafka-failure.md) | P0 - Critical | Message processing halted, tickets not being ingested |
| [P1 - OpenAI API Degradation](runbooks/p1-openai-api-degradation.md) | P1 - High | Agent responses failing or timing out |
| [P1 - Channel Webhook Failures](runbooks/p1-channel-webhook-failures.md) | P1 - High | Gmail/WhatsApp/Web form webhooks returning errors |
| [P2 - High Escalation Rate](runbooks/p2-high-escalation-rate.md) | P2 - Medium | Escalation rate exceeds 25% threshold |

## Escalation Matrix
| Priority | Response Time | Resolution Target | Notification |
|----------|---------------|-------------------|--------------|
| P0 - Critical | 5 minutes | 1 hour | PagerDuty + Slack #incidents |
| P1 - High | 15 minutes | 4 hours | Slack #incidents + Email |
| P2 - Medium | 1 hour | 24 hours | Slack #fte-alerts |
| P3 - Low | 4 hours | 72 hours | Jira ticket created |

## General Incident Response Procedure

### 1. Detect & Acknowledge
- Monitor alerts in Grafana/Prometheus
- Acknowledge alert within SLA
- Create incident ticket in Jira with label `fte-incident`

### 2. Assess & Communicate
- Determine severity and scope
- Notify stakeholders via appropriate channel
- Update status page if customer-facing impact

### 3. Investigate & Resolve
- Follow appropriate runbook below
- Document all actions taken
- Escalate to next level if not resolved within SLA

### 4. Post-Incident
- Conduct post-mortem within 48 hours
- Document root cause and resolution
- Create action items to prevent recurrence
- Update runbooks if needed

## Common Diagnostic Commands

```bash
# Check pod status
kubectl get pods -n customer-success-fte

# Check pod logs
kubectl logs -n customer-success-fte -l app=customer-success-fte --tail=100

# Check database connectivity
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "SELECT 1"

# Check Kafka topics
kubectl exec -n customer-success-fte -it <kafka-pod> -- kafka-topics.sh --bootstrap-server localhost:9092 --list

# Check API health
curl http://localhost:8000/health

# Check resource usage
kubectl top pods -n customer-success-fte
```

## Contact Information
| Role | Contact | Escalation Method |
|------|---------|-------------------|
| On-Call Engineer | PagerDuty rotation | Phone + SMS |
| FTE Team Lead | Slack @fte-lead | Direct message |
| Database Admin | dba-team @company.com | Email + Slack |
| Infrastructure | infra-oncall @company.com | PagerDuty |
| OpenAI Support | support.openai.com | Support ticket |
