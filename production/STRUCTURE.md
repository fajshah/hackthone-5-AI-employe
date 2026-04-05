# Production Folder Structure

```
production/
│
├── README.md                          # Main documentation
├── STRUCTURE.md                       # This file - folder structure documentation
├── requirements.txt                   # Python dependencies
├── .env.example                      # Environment variable template
├── Dockerfile                        # Container configuration
├── Dockerfile.worker                 # Worker container configuration
├── docker-compose.yml                # Local development setup
├── kafka_client.py                   # Kafka producer/consumer utilities
│
├── agent/                            # OpenAI Agents SDK implementation
│   ├── __init__.py
│   ├── customer_success_agent.py     # Main agent definition
│   ├── tools.py                      # @function_tool definitions
│   ├── prompts.py                    # System prompts
│   ├── formatters.py                 # Channel-specific formatting
│   ├── demo.py                       # Demo script
│   ├── simple_agent.py               # Simplified agent for testing
│   ├── seed_kb.py                    # Knowledge base seeding
│   └── test_tools.py                 # Tool tests
│
├── channels/                         # Channel integrations
│   ├── __init__.py
│   ├── gmail_handler.py              # Gmail API + Pub/Sub handler
│   ├── whatsapp_handler.py           # Twilio WhatsApp webhook handler
│   ├── web_form_handler.py           # Web form API + React component
│   └── SupportForm.jsx               # React support form component
│   └── SupportForm.css               # Form styles
│
├── api/                              # FastAPI service
│   ├── __init__.py
│   ├── main.py                       # FastAPI application
│   ├── schemas.py                    # Pydantic models
│   ├── models.py                     # Database models
│   ├── middleware.py                 # API middleware
│   └── routes/
│       ├── __init__.py
│       ├── support.py                # Web form endpoints
│       ├── webhooks.py               # Channel webhook endpoints
│       ├── customers.py              # Customer lookup endpoints
│       ├── tickets.py                # Ticket management endpoints
│       └── admin.py                  # Admin/monitoring endpoints
│
├── workers/                          # Background workers
│   ├── __init__.py
│   └── message_processor.py          # Kafka consumer + agent runner
│
├── database/                         # Database schema and queries
│   ├── __init__.py
│   ├── schema.sql                    # PostgreSQL schema (YOUR CRM)
│   ├── queries.py                    # Database access functions
│   └── migrations/                   # Database migrations
│       └── (migration files)
│
├── config/                           # Configuration
│   ├── config.yaml                   # Main configuration
│   ├── escalation_rules.yaml         # Escalation rule definitions
│   ├── templates.yaml                # Response templates
│   ├── prometheus.yml                # Prometheus monitoring config
│   └── alerts.yml                    # Alerting rules
│
├── tests/                            # Test suites
│   ├── test_transition.py            # Transition tests (incubation → production)
│   ├── test_multichannel_e2e.py      # Multi-channel E2E tests
│   └── load_test.py                  # Locust load testing configuration
│
├── scripts/                          # Utility scripts
│   ├── migrate.py                    # Database migrations
│   ├── seed_kb.py                    # Seed knowledge base
│   ├── backup_db.py                  # Database backup
│   └── deploy.sh                     # Deployment script
│
├── docs/                             # Documentation
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── MONITORING.md                 # Monitoring setup
│   ├── RUNBOOK.md                    # Main incident response guide
│   ├── API.md                        # API endpoint documentation
│   └── runbooks/                     # Incident runbooks
│       ├── p0-database-outage.md
│       ├── p0-kafka-failure.md
│       ├── p1-openai-api-degradation.md
│       ├── p1-channel-webhook-failures.md
│       └── p2-high-escalation-rate.md
│
├── k8s/                              # Kubernetes manifests
│   ├── 00-namespace.yaml
│   ├── 01-configmap.yaml
│   ├── 02-secrets.yaml
│   ├── 03-database-statefulset.yaml
│   ├── 04-kafka-deployment.yaml
│   ├── 05-api-deployment.yaml
│   ├── 06-worker-deployment.yaml
│   ├── 07-services.yaml
│   ├── 08-ingress.yaml
│   ├── 09-hpa.yaml                   # Horizontal Pod Autoscaler
│   ├── 10-network-policy.yaml
│   └── 11-service-account.yaml
│
├── logs/                             # Log files (gitignored)
│   └── (application logs)
│
└── data/                             # Data files
    └── test-set/                     # Benchmark test set
        └── README.md
```

---

## Key Files Description

| File | Purpose |
|------|---------|
| `src/main.py` | Application entry point, FastAPI/Flask app initialization |
| `src/core/orchestrator.py` | Main pipeline coordination logic |
| `config/config.yaml` | All configurable parameters (rules, templates, thresholds) |
| `tests/conftest.py` | Shared pytest fixtures and test utilities |
| `scripts/evaluate_model.py` | Model evaluation against benchmark test set |
| `docs/RUNBOOK.md` | Operational procedures and troubleshooting |
| `Dockerfile` | Container image build instructions |
| `docker-compose.yml` | Local development environment setup |

---

## Module Dependencies

```
main.py
  │
  └── orchestrator.py
        │
        ├── ingestion/
        │     └── normalizer.py
        │
        ├── analysis/
        │     ├── intent_classifier.py
        │     ├── sentiment_analyzer.py
        │     └── entity_extractor.py
        │
        ├── routing/
        │     └── escalation_engine.py
        │
        └── generation/
              ├── response_generator.py
              ├── template_library.py
              └── context_retriever.py
                    └── knowledge_base.py
```

---

## Git Ignore Rules

```gitignore
# Environment
.env
venv/
__pycache__/
*.pyc

# Logs
logs/
*.log

# Data
data/knowledge-base/embeddings/
data/test-set/temp/

# IDE
.vscode/
.idea/
*.swp

# Build
dist/
build/
*.egg-info/
```
