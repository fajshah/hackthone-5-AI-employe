# P0 - Database Outage Runbook

## Severity: P0 - Critical
**Trigger:** PostgreSQL database unavailable, all ticket operations failing

## Impact
- All ticket creation fails
- Customer responses cannot be stored
- Knowledge base search unavailable
- Customer history inaccessible
- **Complete system outage**

## Detection
- Alert: `PostgreSQLDown` - Database health check failing
- Alert: `HighDatabaseErrorRate` - >50% of database queries failing
- Symptoms in logs: `connection refused`, `could not connect to server`

## Immediate Actions (0-5 minutes)

### 1. Confirm Outage
```bash
# Check database pod status
kubectl get pods -n customer-success-fte -l app=postgres

# Check database logs
kubectl logs -n customer-success-fte -l app=postgres --tail=50

# Test connectivity
kubectl exec -n customer-success-fte -it <any-pod> -- python -c "
import asyncpg
import asyncio

async def test():
    try:
        conn = await asyncpg.connect(
            host='postgres.customer-success-fte.svc.cluster.local',
            database='fte_db',
            user='fte_user',
            password='YOUR_PASSWORD'
        )
        await conn.fetchval('SELECT 1')
        print('Database is reachable')
        await conn.close()
    except Exception as e:
        print(f'Database connection failed: {e}')

asyncio.run(test())
"
```

### 2. If Pod is Down
```bash
# Check if pod is restarting
kubectl describe pod -n customer-success-fte -l app=postgres

# If pod is in CrashLoopBackOff
kubectl logs -n customer-success-fte -l app=postgres --previous

# Restart the database pod
kubectl delete pod -n customer-success-fte -l app=postgres
```

### 3. If Pod is Running but Unresponsive
```bash
# Check database disk space
kubectl exec -n customer-success-fte -it <postgres-pod> -- df -h

# Check for locked tables
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT pid, state, query, wait_event_type, wait_event 
FROM pg_stat_activity 
WHERE state != 'idle';
"

# Check connection count
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT count(*) FROM pg_stat_activity;
"
```

## Recovery Procedures (5-30 minutes)

### Scenario A: Pod Restart Fixes Issue
1. Monitor pod after restart
2. Verify migrations are applied
3. Test basic queries
4. Monitor error rate in Grafana
5. Confirm alert clears

### Scenario B: Disk Space Full
```bash
# Check WAL files
kubectl exec -n customer-success-fte -it <postgres-pod> -- du -sh /var/lib/postgresql/data/pg_wal

# If WAL files are too large, archive them
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT pg_switch_wal();
"

# Clean old WAL files (if archiving is configured)
kubectl exec -n customer-success-fte -it <postgres-pod> -- rm /var/lib/postgresql/data/pg_wal/*.old

# Restart PostgreSQL
kubectl exec -n customer-success-fte -it <postgres-pod> -- pg_ctl restart
```

### Scenario C: Connection Exhaustion
```bash
# Check current connections
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT count(*) FROM pg_stat_activity;
"

# Check max connections
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SHOW max_connections;
"

# Kill idle connections
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND query_start < NOW() - INTERVAL '5 minutes';
"

# If needed, restart database pod to clear all connections
kubectl delete pod -n customer-success-fte -l app=postgres
```

### Scenario D: Data Corruption
```bash
# Check database integrity
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
VACUUM VERBOSE ANALYZE;
"

# Restore from backup if needed
# 1. Get latest backup
kubectl exec -n customer-success-fte -it <backup-pod> -- ls /backups/

# 2. Restore
kubectl exec -n customer-success-fte -it <postgres-pod> -- pg_restore -U fte_user -d fte_db /backups/latest.dump

# 3. Verify restoration
kubectl exec -n customer-success-fte -it <postgres-pod> -- psql -U fte_user -d fte_db -c "
SELECT count(*) FROM customers;
SELECT count(*) FROM tickets;
SELECT count(*) FROM conversations;
"
```

## Communication Template

### Initial Notification (Slack #incidents)
```
🚨 P0 INCIDENT: Database Outage
- Impact: All FTE operations halted
- Started: [TIME]
- Investigating: [NAME]
- ETA for update: 15 minutes
```

### Update (if resolved)
```
✅ RESOLVED: Database Outage
- Root cause: [DESCRIPTION]
- Resolution: [ACTION TAKEN]
- Duration: [X minutes]
- Customer impact: [YES/NO]
- Post-mortem scheduled: [TIME]
```

### Customer-Facing Status Update (if needed)
```
We're experiencing a temporary service disruption affecting our AI support assistant. 
Our team is actively working on a resolution. Expected restoration within [X] minutes. 
For urgent matters, please email support@technova.com.
```

## Post-Incident Checklist
- [ ] Root cause identified and documented
- [ ] Post-mortem scheduled within 48 hours
- [ ] Action items created in Jira
- [ ] Runbook updated if needed
- [ ] Monitoring alerts adjusted
- [ ] Customer communication sent (if impacted)
- [ ] Backup verified (if restoration performed)
