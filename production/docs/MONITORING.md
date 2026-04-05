# Monitoring & Alerting Setup

**Purpose:** Observability configuration for production

---

## Metrics Collection

### Prometheus Configuration

File: `config/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'technova-agent'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Key Metrics

**Business Metrics:**
- `tickets_total` - Total tickets processed
- `tickets_by_channel` - Channel distribution
- `tickets_by_intent` - Intent category distribution
- `escalations_total` - Total escalations
- `escalation_accuracy` - Correct escalation rate

**Performance Metrics:**
- `response_time_seconds` - Response latency (histogram)
- `intent_classification_latency` - Intent analysis time
- `sentiment_analysis_latency` - Sentiment analysis time
- `llm_request_duration` - LLM API call duration

**Quality Metrics:**
- `intent_accuracy` - Intent classification accuracy
- `sentiment_accuracy` - Sentiment analysis accuracy
- `response_quality_score` - Human-reviewed quality score
- `brand_voice_compliance` - Brand voice adherence rate

**Error Metrics:**
- `errors_total` - Total errors
- `errors_by_type` - Error categorization
- `api_failures_total` - External API failures
- `timeout_total` - Request timeouts

---

## Alerting Rules

File: `config/alerts.yml`

```yaml
groups:
  - name: technova-alerts
    rules:
      # Critical Alerts (Page Immediately)
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% (threshold: 5%)"

      - alert: ServiceDown
        expr: up{job="technova-agent"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "Technova agent service is not responding"

      - alert: EscalationQueueBacklog
        expr: escalation_queue_depth > 50
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Escalation queue backlog"
          description: "{{ $value }} tickets waiting in escalation queue"

      # Warning Alerts (Notify Slack)
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(response_time_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "P95 response time is {{ $value }}s (threshold: 2s)"

      - alert: LowIntentAccuracy
        expr: intent_accuracy < 0.85
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Low intent classification accuracy"
          description: "Intent accuracy is {{ $value }}% (threshold: 85%)"

      - alert: DatabaseConnectionPoolExhausted
        expr: db_connection_pool_used / db_connection_pool_total > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "{{ $value }}% of connections in use"

      # Info Alerts (Log Only)
      - alert: HighTicketVolume
        expr: rate(tickets_total[1h]) > 1000
        for: 15m
        labels:
          severity: info
        annotations:
          summary: "High ticket volume"
          description: "{{ $value }} tickets per hour"
```

---

## Log Aggregation

### ELK Stack Configuration

**Filebeat Configuration:** `config/filebeat.yml`

```yaml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/technova-agent/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  indices:
    - index: "technova-agent-%{+yyyy.MM.dd}"

processors:
  - add_fields:
      fields:
        service: technova-agent
      target: ''
```

### Log Format

```json
{
  "timestamp": "2026-04-01T10:30:00Z",
  "level": "INFO",
  "service": "technova-agent",
  "trace_id": "abc123",
  "ticket_id": "TKT-001",
  "customer_id": "CUST-001",
  "message": "Ticket processed successfully",
  "intent": "billing",
  "sentiment": -0.45,
  "escalated": true,
  "response_time_ms": 1250
}
```

---

## Dashboard Configuration

### Grafana Dashboard

File: `config/grafana-dashboard.json`

**Panels:**

1. **Overview**
   - Tickets processed (last 1h, 24h, 7d)
   - Current error rate
   - Average response time
   - Active escalations

2. **Channel Distribution**
   - Pie chart: Email vs WhatsApp vs Web Form
   - Trend line: Tickets per channel over time

3. **Intent Analysis**
   - Bar chart: Tickets by intent category
   - Heatmap: Intent distribution over time

4. **Sentiment Trends**
   - Line graph: Average sentiment score over time
   - Distribution: Sentiment buckets (angry, frustrated, neutral, happy)

5. **Escalation Metrics**
   - Escalation rate (%)
   - Escalation by reason (pie chart)
   - Average time to escalate

6. **Performance**
   - Response time histogram
   - P50, P95, P99 latency
   - LLM API latency

7. **Quality**
   - Intent accuracy trend
   - Sentiment accuracy trend
   - Response quality score

8. **Errors**
   - Error rate over time
   - Errors by type
   - Top error messages

---

## Notification Channels

### PagerDuty (Critical)

```yaml
receivers:
  - name: pagerduty-critical
    pagerduty_configs:
      - service_key: YOUR_PAGERDUTY_SERVICE_KEY
        severity: critical
        description: "{{ .CommonAnnotations.summary }}"
```

### Slack (Warning)

```yaml
receivers:
  - name: slack-warnings
    slack_configs:
      - api_url: YOUR_SLACK_WEBHOOK_URL
        channel: '#support-alerts'
        title: "⚠️ {{ .CommonAnnotations.summary }}"
        text: "{{ .CommonAnnotations.description }}"
```

### Email (Info)

```yaml
receivers:
  - name: email-info
    email_configs:
      - to: support-team@technova.com
        from: alerts@technova.com
        smarthost: smtp.sendgrid.net:587
        auth_username: apikey
        auth_password: YOUR_SENDGRID_KEY
```

---

## Runbook Links

Each alert should link to relevant runbook:

| Alert | Runbook |
|-------|---------|
| HighErrorRate | `docs/runbooks/high-error-rate.md` |
| ServiceDown | `docs/runbooks/service-down.md` |
| EscalationQueueBacklog | `docs/runbooks/escalation-backlog.md` |
| HighResponseTime | `docs/runbooks/high-latency.md` |
| LowIntentAccuracy | `docs/runbooks/model-retrain.md` |

---

## Testing Alerts

```bash
# Test alertmanager configuration
amtool check-config config/alertmanager.yml

# Trigger test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "Test alert",
      "description": "This is a test"
    }
  }]'
```
