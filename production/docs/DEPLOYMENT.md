# Deployment Runbook

**Purpose:** Step-by-step deployment instructions

---

## Pre-Deployment Checklist

- [ ] All tests passing (unit, integration, e2e)
- [ ] Code review completed
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Rollback plan documented
- [ ] On-call team notified

---

## Staging Deployment

### Step 1: Build & Push

```bash
# Build Docker image
docker build -t technova-agent:staging .

# Push to registry
docker push registry.example.com/technova-agent:staging
```

### Step 2: Deploy to Staging

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/staging/

# Verify deployment
kubectl rollout status deployment/technova-agent-staging
```

### Step 3: Smoke Tests

```bash
# Run smoke tests
pytest tests/e2e/test_e2e_email_flow.py --staging
pytest tests/e2e/test_e2e_whatsapp_flow.py --staging
```

### Step 4: Monitor

- Check metrics dashboard
- Review error logs
- Verify escalation routing
- Test human handoff

**Approval Required:** Product Manager sign-off

---

## Production Deployment

### Step 1: Pre-Deployment

```bash
# Backup production database
pg_dump production_db > backup_$(date +%Y%m%d).sql

# Snapshot current deployment
kubectl get deployment technova-agent-prod -o yaml > prod-backup.yaml
```

### Step 2: Deploy (Canary - 10%)

```bash
# Deploy canary (10% traffic)
kubectl set image deployment/technova-agent-prod \
  agent=registry.example.com/technova-agent:production \
  --record

kubectl patch deployment technova-agent-prod \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent","env":[{"name":"CANARY_WEIGHT","value":"10"}]}]}}}}'
```

### Step 3: Monitor Canary (30 minutes)

**Metrics to Watch:**
- Error rate < 1%
- Response time P95 < 2s
- Escalation accuracy > 85%
- No increase in customer complaints

```bash
# Watch metrics
watch kubectl top pods -l app=technova-agent

# Check logs
kubectl logs -f deployment/technova-agent-prod --tail=100
```

### Step 4: Gradual Rollout

If canary successful:

```bash
# Increase to 50%
kubectl patch deployment technova-agent-prod \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent","env":[{"name":"CANARY_WEIGHT","value":"50"}]}]}}}}'

# Wait 30 minutes, monitor

# Increase to 100%
kubectl patch deployment technova-agent-prod \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent","env":[{"name":"CANARY_WEIGHT","value":"100"}]}]}}}}'
```

### Step 5: Post-Deployment

```bash
# Verify all pods running
kubectl get pods -l app=technova-agent-prod

# Run full E2E test suite
pytest tests/e2e/ --production

# Update documentation
git tag production-v1.0.0
git push origin production-v1.0.0
```

---

## Rollback Procedure

### Immediate Rollback (Emergency)

```bash
# Rollback to previous version
kubectl rollout undo deployment/technova-agent-prod

# Verify rollback
kubectl rollout status deployment/technova-agent-prod
```

### Gradual Rollback (Non-Urgent)

1. Deploy previous version to canary (10%)
2. Monitor for 15 minutes
3. Increase to 50%
4. Increase to 100%

---

## Post-Deployment Validation

### Automated Checks

```bash
# Health check
curl https://api.technova.com/health

# Run smoke tests
pytest tests/e2e/test_e2e_email_flow.py --production
pytest tests/e2e/test_e2e_escalation_flow.py --production
```

### Manual Checks

- [ ] Send test email → verify response
- [ ] Send test WhatsApp → verify response
- [ ] Submit web form → verify response
- [ ] Test escalation (angry sentiment) → verify human handoff
- [ ] Check metrics dashboard
- [ ] Review error logs
- [ ] Verify SLA timers

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| On-Call Engineer | See PagerDuty | PagerDuty alert |
| Product Manager | [Name] | [Phone/Slack] |
| DevOps Lead | [Name] | [Phone/Slack] |
| Security Team | [Name] | [Phone/Slack] |

---

## Deployment Schedule

| Environment | Day | Time | Owner |
|-------------|-----|------|-------|
| Staging | Tuesday | 10:00 AM | DevOps |
| Production (Canary) | Thursday | 10:00 AM | DevOps |
| Production (Full) | Friday | 10:00 AM | DevOps |

**Note:** Avoid deployments on weekends or holidays
