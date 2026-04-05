# TechNova Customer Support - Kubernetes Manifests

Complete Kubernetes configuration for production deployment.

## Files

| File | Purpose |
|------|---------|
| `00-namespace.yaml` | Namespace definition |
| `01-configmap.yaml` | Configuration (non-sensitive) |
| `02-secrets.yaml` | Secrets (sensitive data) |
| `03-database-statefulset.yaml` | PostgreSQL StatefulSet |
| `04-kafka-deployment.yaml` | Kafka deployment |
| `05-api-deployment.yaml` | API server deployment |
| `06-worker-deployment.yaml` | Message processor worker |
| `07-services.yaml` | Service definitions |
| `08-ingress.yaml` | Ingress configuration |
| `09-hpa.yaml` | Horizontal Pod Autoscaler |
| `10-network-policy.yaml` | Network policies |

## Quick Deploy

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply individually
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
...

# Check status
kubectl get all -n technova

# View logs
kubectl logs -n technova -l app=support-api
```

## Quick Undeploy

```bash
# Delete all resources
kubectl delete -f k8s/
```

---

## Configuration

### Environment Variables

Set these before deploying:

```bash
export API_KEY="your-secure-api-key"
export DATABASE_PASSWORD="secure-db-password"
export OPENAI_API_KEY="sk-..."
export KAFKA_PASSWORD="kafka-password"
```

### Resource Customization

Edit `values` in ConfigMap for:
- Replica counts
- Resource limits
- Feature flags

Edit Secrets for:
- API keys
- Database passwords
- OAuth credentials

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     KUBERNETES CLUSTER                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  NAMESPACE: technova                  │   │
│  │                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │  Ingress    │  │   ConfigMap │  │   Secrets   │   │   │
│  │  │  Controller │  │             │  │             │   │   │
│  │  └──────┬──────┘  └─────────────┘  └─────────────┘   │   │
│  │         │                                             │   │
│  │         ▼                                             │   │
│  │  ┌─────────────────────────────────────────────┐     │   │
│  │  │              Services                        │     │   │
│  │  │  ┌─────────┐  ┌──────────┐  ┌──────────┐   │     │   │
│  │  │  │   API   │  │ Database │  │  Kafka   │   │     │   │
│  │  │  │  :8000  │  │  :5432   │  │  :9092   │   │     │   │
│  │  │  └────┬────┘  └────┬─────┘  └────┬─────┘   │     │   │
│  │  │       │            │             │         │     │   │
│  │  │       ▼            ▼             ▼         │     │   │
│  │  │  ┌─────────────┐ ┌──────────┐ ┌────────┐  │     │   │
│  │  │  │ API Pods    │ │ Postgres │ │ Kafka  │  │     │   │
│  │  │  │ (HPA: 3-10) │ │  (1)     │ │  (1)   │  │     │   │
│  │  │  └─────────────┘ └──────────┘ └────────┘  │     │   │
│  │  │                                            │     │   │
│  │  │  ┌─────────────┐                          │     │   │
│  │  │  │ Worker Pods │                          │     │   │
│  │  │  │ (HPA: 2-5)  │                          │     │   │
│  │  │  └─────────────┘                          │     │   │
│  │  └────────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Scaling

### Manual Scaling

```bash
# Scale API
kubectl scale deployment support-api -n technova --replicas=5

# Scale Worker
kubectl scale deployment support-worker -n technova --replicas=3
```

### Auto Scaling (HPA)

HPA automatically scales based on CPU/Memory:

```bash
# View HPA status
kubectl get hpa -n technova

# View metrics
kubectl top pods -n technova
```

---

## Monitoring

```bash
# Get all resources
kubectl get all -n technova

# Get pods
kubectl get pods -n technova

# Get services
kubectl get svc -n technova

# View logs
kubectl logs -n technova deployment/support-api

# Exec into pod
kubectl exec -it -n technova deployment/support-api -- /bin/bash
```

---

## Production Checklist

- [ ] Update ConfigMap with production values
- [ ] Set all Secrets (API keys, passwords)
- [ ] Configure ingress TLS certificates
- [ ] Set up external database (optional)
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Set up log aggregation (ELK/Loki)
- [ ] Configure backup strategy
- [ ] Test failover scenarios
- [ ] Document runbook

---

**Ready for production deployment!** 🚀
