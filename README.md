# 🚀 TechNova Customer Success FTE - AI Employee

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-10a37f.svg)](https://openai.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-7.5.0-231f20.svg)](https://kafka.apache.org/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326ce5.svg)](https://kubernetes.io/)

> **Hackathon 5 Submission**: Build Your First 24/7 AI Employee - From Incubation to Production

A production-ready **Digital Full-Time Equivalent (FTE)** - an AI customer success agent that works 24/7 without breaks, handling customer inquiries across **Email (Gmail)**, **WhatsApp**, and **Web Form** channels with intelligent triage, escalation, and cross-channel conversation continuity.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Demo](#-demo)
- [Hackathon Deliverables](#-hackathon-deliverables)
- [Team](#-team)

---

## 🎯 Overview

TechNova is a fast-growing SaaS company drowning in customer inquiries (2,000+ weekly tickets). This project builds a **Digital Customer Success FTE** that:

- ✅ Handles routine customer queries 24/7 across 3 channels
- ✅ Intelligently triages and escalates complex issues
- ✅ Maintains conversation continuity across channels
- ✅ Tracks all interactions in a PostgreSQL-based CRM
- ✅ Generates real-time metrics and sentiment analysis
- ✅ Operates at <$1,000/year vs $75,000/year for human FTE

### Agent Maturity Model

This project follows the complete **Agent Maturity Model**:

1. **Stage 1 - Incubation**: Explored requirements, built prototype with MCP server
2. **Stage 2 - Specialization**: Transformed to production-grade system with OpenAI Agents SDK, FastAPI, PostgreSQL, Kafka, Kubernetes
3. **Stage 3 - Integration**: Complete E2E testing, load testing, 24-hour continuous operation plan

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MULTI-CHANNEL INTAKE ARCHITECTURE                 │
│                                                                      │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│   │    Gmail     │    │   WhatsApp   │    │   Web Form   │         │
│   │   (Email)    │    │  (Twilio)    │    │  (React UI)  │         │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘         │
│          │                   │                   │                  │
│          └───────────────────┼───────────────────┘                  │
│                              ▼                                      │
│                    ┌─────────────────┐                              │
│                    │   FastAPI API   │                              │
│                    │   (Port 8000)   │                              │
│                    └────────┬────────┘                              │
│                             │                                       │
│              ┌──────────────┼──────────────┐                       │
│              ▼              ▼              ▼                        │
│        ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│        │PostgreSQL│  │  Kafka   │  │  OpenAI  │                   │
│        │  (CRM)   │  │(Events)  │  │  Agent   │                   │
│        └──────────┘  └──────────┘  └──────────┘                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Multi-Channel Flow

1. **Customer submits inquiry** via Email, WhatsApp, or Web Form
2. **Webhook handler** normalizes message and publishes to Kafka
3. **Message processor** consumes from Kafka, runs AI agent
4. **AI agent** searches knowledge base, generates response
5. **Response** sent back via appropriate channel
6. **All interactions** stored in PostgreSQL for analytics

---

## ✨ Features

### Core Capabilities

- 🤖 **AI-Powered Responses**: GPT-4o generates accurate, context-aware responses
- 📧 **Multi-Channel Support**: Email (Gmail), WhatsApp (Twilio), Web Form
- 🔄 **Cross-Channel Continuity**: Conversations persist across channels
- 🎯 **Intelligent Escalation**: 10 escalation rules with priority routing
- 📊 **Real-Time Metrics**: Dashboard with channel-specific analytics
- 💬 **Sentiment Analysis**: Detects customer mood and adjusts responses
- 🗄️ **Built-in CRM**: PostgreSQL-based customer and ticket management
- 📈 **Knowledge Base**: Semantic search over product documentation

### Guardrails & Safety

- ✅ Never discusses pricing (escalates immediately)
- ✅ Never promises features not in documentation
- ✅ Never processes refunds (escalates to billing)
- ✅ Always creates ticket before responding
- ✅ Always checks sentiment before closing
- ✅ Channel-appropriate tone and length

### Performance Targets

| Metric | Target |
|--------|--------|
| Response Time | <3 seconds (processing) |
| Accuracy | >85% on test set |
| Escalation Rate | <20% |
| Cross-Channel ID | >95% accuracy |
| Uptime | >99.9% |

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Backend** | FastAPI (Python 3.11+) |
| **AI/ML** | OpenAI GPT-4o, Agents SDK |
| **Database** | PostgreSQL 16 with pgvector |
| **Event Streaming** | Apache Kafka 7.5.0 |
| **Frontend** | HTML5, React, CSS3 |
| **Containerization** | Docker + Docker Compose |
| **Orchestration** | Kubernetes |
| **Monitoring** | Prometheus + Grafana |
| **Testing** | pytest, Locust |
| **CI/CD** | GitHub Actions |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key

### 1. Clone Repository

```bash
git clone https://github.com/fajshah/hackthone-5-AI-employe.git
cd hackthone-5-AI-employe
```

### 2. Setup Environment

```bash
cd production
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Start Infrastructure

```bash
docker-compose up -d postgres kafka redis
```

### 4. Run API Server

```bash
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open Frontend

```bash
# Open in browser
open frontend/index.html  # Mac/Linux
start frontend/index.html  # Windows
```

### 6. Run CLI Demo

```bash
python cli_demo.py
```

---

## 📁 Project Structure

```
digital-fte-hackathon/
├── context/                      # Company context and documentation
│   ├── company-profile.md
│   ├── product-docs.md
│   ├── brand-voice.md
│   ├── escalation-rules.md
│   └── sample-tickets.json       # 50+ sample tickets
│
├── prototype/                    # Stage 1: Incubation
│   ├── agent_core.py             # Core agent logic
│   ├── agent_core_v2_memory.py   # With conversation memory
│   ├── mcp_server.py             # MCP server with 5 tools
│   ├── test_*.py                 # Test suites
│   └── SKILLS_MANIFEST.md        # Agent skills definition
│
├── production/                   # Stage 2: Specialization
│   ├── agent/                    # OpenAI Agents SDK
│   │   ├── customer_success_agent.py
│   │   ├── tools.py              # Function tools
│   │   ├── prompts.py            # System prompts
│   │   └── formatters.py         # Channel formatting
│   │
│   ├── api/                      # FastAPI service
│   │   ├── main.py               # Application entry
│   │   ├── routes/               # API endpoints
│   │   ├── models.py             # Pydantic models
│   │   └── storage.py            # Ticket storage
│   │
│   ├── channels/                 # Channel integrations
│   │   ├── gmail_handler.py
│   │   ├── whatsapp_handler.py
│   │   ├── web_form_handler.py
│   │   └── SupportForm.jsx       # React component
│   │
│   ├── database/                 # PostgreSQL CRM
│   │   ├── schema.sql            # Complete CRM schema
│   │   └── queries.py
│   │
│   ├── workers/                  # Background workers
│   │   └── message_processor.py  # Kafka consumer
│   │
│   ├── config/                   # Configuration
│   │   ├── escalation_rules.yaml
│   │   ├── templates.yaml
│   │   └── prometheus.yml
│   │
│   ├── k8s/                      # Kubernetes manifests
│   │   ├── 00-namespace.yaml
│   │   ├── 05-api-deployment.yaml
│   │   ├── 06-worker-deployment.yaml
│   │   └── ... (13 files total)
│   │
│   ├── docs/                     # Documentation
│   │   ├── API.md
│   │   ├── DEPLOYMENT.md
│   │   ├── RUNBOOK.md
│   │   └── runbooks/             # Incident runbooks
│   │
│   ├── scripts/                  # Utility scripts
│   │   ├── migrate.py
│   │   ├── seed_kb.py
│   │   ├── backup_db.py
│   │   └── deploy.sh
│   │
│   ├── tests/                    # Test suites
│   │   ├── test_transition.py
│   │   ├── test_multichannel_e2e.py
│   │   └── load_test.py
│   │
│   ├── frontend/                 # Web UI
│   │   └── index.html
│   │
│   ├── cli_demo.py               # CLI demo script
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── specs/                        # Specifications
│   ├── discovery-log.md
│   └── customer-success-fte-spec.md
│
└── tests/                        # Root test directory
    ├── conftest.py
    ├── run_tests.py
    └── 24-hour-test-plan.md
```

---

## 📚 API Documentation

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `POST` | `/support/submit` | Submit support ticket |
| `GET` | `/support/ticket/{id}` | Get ticket details |
| `GET` | `/support/tickets` | List customer tickets |
| `POST` | `/webhooks/gmail` | Gmail webhook handler |
| `POST` | `/webhooks/whatsapp` | WhatsApp webhook handler |
| `GET` | `/customers/lookup` | Look up customer |
| `GET` | `/metrics/channels` | Channel metrics |

### Interactive API Docs

Once server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example: Submit Ticket

```bash
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "subject": "How to create Kanban board?",
    "message": "I need help setting up Kanban boards for my team."
  }'
```

**Response:**
```json
{
  "ticket_id": "TKT-AE011FC9",
  "status": "received",
  "message": "Your support request has been submitted successfully.",
  "email": "john@example.com",
  "submitted_at": "2026-04-05T16:54:05.571648"
}
```

---

## 🧪 Testing

### Run Test Suite

```bash
cd production/tests
pytest test_transition.py -v
pytest test_multichannel_e2e.py -v
```

### Load Testing

```bash
# Install Locust
pip install locust

# Run load test
locust -f load_test.py --host=http://localhost:8000
```

### 24-Hour Continuous Test

See [tests/24-hour-test-plan.md](tests/24-hour-test-plan.md) for complete test plan including:
- 100+ web form submissions
- 50+ email simulations
- 50+ WhatsApp messages
- Chaos testing (pod kills every 2 hours)
- Performance validation

---

## 🚢 Deployment

### Local Development

```bash
docker-compose up -d
```

### Kubernetes Deployment

```bash
cd production
./scripts/deploy.sh
```

### Manual K8s Deploy

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secrets.yaml
kubectl apply -f k8s/05-api-deployment.yaml
kubectl apply -f k8s/06-worker-deployment.yaml
kubectl apply -f k8s/07-services.yaml
```

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
POSTGRES_HOST=localhost
POSTGRES_DB=technova
POSTGRES_USER=technova
POSTGRES_PASSWORD=technova_password

# Optional
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
LOG_LEVEL=INFO
```

---

## 📊 Monitoring

### Prometheus Metrics

- Request rate and latency
- Error rates by endpoint
- Ticket volume by channel
- Escalation rates
- Agent response times
- Kafka consumer lag

### Grafana Dashboards

- System health overview
- Channel performance
- Customer sentiment
- Escalation trends

### Alerts

| Alert | Severity | Threshold |
|-------|----------|-----------|
| PostgreSQLDown | P0 | Database unreachable |
| KafkaDown | P0 | No brokers available |
| HighAPIErrorRate | P1 | >10% errors |
| OpenAIApiErrorRate | P1 | >20% failures |
| HighEscalationRate | P2 | >25% escalations |
| HighResponseLatency | P2 | P95 >3s |

---

## 🎬 Demo

### CLI Demo (Recommended for Video)

```bash
cd production
python cli_demo.py
```

This runs a complete automated demo showing:
1. ✅ Health check
2. ✅ 5 ticket submissions
3. ✅ Ticket retrieval
4. ✅ Customer lookup
5. ✅ API documentation
6. ✅ System architecture
7. ✅ Live interactive test

### Web Frontend

Open `production/frontend/index.html` in browser to see:
- Beautiful support form
- Ticket status checker
- Real-time dashboard

### API Documentation

Visit http://localhost:8000/docs for interactive API testing.

---

## 📦 Hackathon Deliverables

### ✅ Stage 1: Incubation (Hours 1-16)

- [x] Working prototype handling customer queries
- [x] `specs/discovery-log.md` - Requirements discovered
- [x] MCP server with 5+ tools
- [x] Agent skills manifest
- [x] Edge cases documented
- [x] Escalation rules crystallized
- [x] Channel-specific response templates
- [x] Performance baseline measured

### ✅ Stage 2: Specialization (Hours 17-40)

- [x] PostgreSQL schema with multi-channel support
- [x] OpenAI Agents SDK implementation
- [x] FastAPI service with all endpoints
- [x] Gmail integration (webhook + send)
- [x] WhatsApp/Twilio integration
- [x] Web Support Form (React component)
- [x] Kafka event streaming
- [x] Kubernetes manifests (13 files)
- [x] Monitoring configuration

### ✅ Stage 3: Integration (Hours 41-48)

- [x] Multi-channel E2E test suite
- [x] Load test configuration
- [x] 24-hour test plan
- [x] CLI demo script
- [x] Complete documentation
- [x] Incident runbooks (5 scenarios)

---

## 👥 Team

**Developer**: [Your Name]  
**Hackathon**: CRM Digital FTE Factory - Hackathon 5  
**Duration**: 48-72 Hours  
**Difficulty**: Advanced

---

## 📄 License

This project is built for educational purposes as part of the CRM Digital FTE Factory Hackathon 5.

---

## 🙏 Acknowledgments

- [Agent Maturity Model](https://agentfactory.panaversity.org/docs/General-Agents-Foundations/agent-factory-paradigm/the-2025-inflection-point#the-agent-maturity-model)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Apache Kafka](https://kafka.apache.org/)
- [Kubernetes](https://kubernetes.io/)

---

<div align="center">

**Built with ❤️ for Hackathon 5**

[⭐ Star this repo](https://github.com/fajshah/hackthone-5-AI-employe) | [🐛 Report Bug](https://github.com/fajshah/hackthone-5-AI-employe/issues) | [💡 Request Feature](https://github.com/fajshah/hackthone-5-AI-employe/issues)

</div>
