# P0 - Kafka Cluster Failure Runbook

## Severity: P0 - Critical
**Trigger:** Kafka cluster unavailable, message processing halted

## Impact
- Incoming tickets from all channels not being processed
- Webhook handlers returning 500 errors
- No new customer responses generated
- Event streaming stopped
- **Message backlog growing continuously**

## Detection
- Alert: `KafkaDown` - Kafka broker not responding
- Alert: `KafkaConsumerLag` - Consumer lag > 1000 messages
- Alert: `KafkaProducerErrors` - >10% of produce requests failing
- Symptoms: `Connection refused`, `NotLeaderForPartition`, `RequestTimedOut`

## Immediate Actions (0-5 minutes)

### 1. Confirm Kafka Status
```bash
# Check Kafka pod status
kubectl get pods -n customer-success-fte -l app=kafka

# Check Kafka logs
kubectl logs -n customer-success-fte -l app=kafka --tail=100

# Test Kafka connectivity
kubectl exec -n customer-success-fte -it <any-pod> -- python -c "
from kafka import KafkaAdminClient
from kafka.errors import KafkaError

try:
    admin = KafkaAdminClient(bootstrap_servers='kafka.customer-success-fte.svc.cluster.local:9092')
    topics = admin.list_topics()
    print(f'Kafka is reachable. Topics: {topics}')
except KafkaError as e:
    print(f'Kafka connection failed: {e}')
"
```

### 2. Check All Kafka Components
```bash
# List all Kafka-related pods
kubectl get pods -n customer-success-fte | grep -E 'kafka|zookeeper'

# Check Zookeeper status (if using Kafka with Zookeeper)
kubectl logs -n customer-success-fte -l app=zookeeper --tail=50

# Check Kafka service
kubectl get svc -n customer-success-fte kafka
kubectl describe svc -n customer-success-fte kafka
```

## Recovery Procedures (5-30 minutes)

### Scenario A: Single Broker Down
```bash
# Restart the Kafka pod
kubectl delete pod -n customer-success-fte -l app=kafka

# Monitor restart
kubectl get pods -n customer-success-fte -l app=kafka -w

# Verify broker rejoins cluster
kubectl logs -n customer-success-fte -l app=kafka --tail=20 | grep -i 'started\|ready'
```

### Scenario B: Zookeeper Failure
```bash
# Check Zookeeper status
kubectl exec -n customer-success-fte -it <zookeeper-pod> -- zkServer.sh status

# Restart Zookeeper
kubectl delete pod -n customer-success-fte -l app=zookeeper

# Wait for Zookeeper to be ready before restarting Kafka
kubectl wait --for=condition=ready pod -l app=zookeeper -n customer-success-fte --timeout=120s

# Then restart Kafka
kubectl delete pod -n customer-success-fte -l app=kafka
```

### Scenario C: Disk Space Exhaustion
```bash
# Check Kafka disk usage
kubectl exec -n customer-success-fte -it <kafka-pod> -- df -h /var/lib/kafka/data

# Check log retention
kubectl exec -n customer-success-fte -it <kafka-pod> -- du -sh /var/lib/kafka/data/*

# Reduce retention temporarily
kubectl exec -n customer-success-fte -it <kafka-pod> -- kafka-configs.sh \
  --bootstrap-server localhost:9092 \
  --alter --entity-type topics \
  --entity-name fte.tickets.incoming \
  --add-config retention.ms=3600000

# Delete old segments if needed
kubectl exec -n customer-success-fte -it <kafka-pod> -- rm /var/lib/kafka/data/fte.*/*.log

# Restart Kafka to apply changes
kubectl exec -n customer-success-fte -it <kafka-pod> -- kafka-server-stop.sh
kubectl exec -n customer-success-fte -it <kafka-pod> -- kafka-server-start.sh /etc/kafka/server.properties
```

### Scenario D: Consumer Group Issues
```bash
# Check consumer group status
kubectl exec -n customer-success-fte -it <kafka-pod> -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group fte-message-processor

# Check consumer lag
kubectl exec -n customer-success-fte -it <kafka-pod> -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group fte-message-processor \
  --members

# Reset consumer group offset if stuck (LAST RESORT)
kubectl exec -n customer-success-fte -it <kafka-pod> -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group fte-message-processor \
  --reset-offsets \
  --to-latest \
  --topic fte.tickets.incoming \
  --execute

# Restart message processor pods
kubectl rollout restart deployment/fte-message-processor -n customer-success-fte
```

## Message Backlog Recovery

### After Kafka is Restored
```bash
# Monitor consumer lag decreasing
watch -n 5 "kubectl exec -n customer-success-fte -it <kafka-pod> -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group fte-message-processor"

# Check message processor throughput
kubectl logs -n customer-success-fte -l app=customer-success-fte,component=message-processor --tail=100 | grep -i 'processed'

# Scale up message processors if needed
kubectl scale deployment/fte-message-processor -n customer-success-fte --replicas=5

# Monitor until backlog is cleared
```

## Communication Template

### Initial Notification (Slack #incidents)
```
🚨 P0 INCIDENT: Kafka Cluster Failure
- Impact: Ticket processing halted, messages queuing
- Started: [TIME]
- Investigating: [NAME]
- Message backlog: [COUNT] (if available)
- ETA for update: 15 minutes
```

### Update (if resolved)
```
✅ RESOLVED: Kafka Cluster Failure
- Root cause: [DESCRIPTION]
- Resolution: [ACTION TAKEN]
- Messages processed during recovery: [COUNT]
- Duration: [X minutes]
- Post-mortem scheduled: [TIME]
```

## Post-Incident Checklist
- [ ] All consumer groups caught up
- [ ] Message backlog cleared
- [ ] No message loss verified
- [ ] Consumer lag monitoring alerts configured
- [ ] Disk space retention policies adjusted
- [ ] Post-mortem completed
- [ ] Runbook updated if needed
