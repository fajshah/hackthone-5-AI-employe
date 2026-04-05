# Database Module

PostgreSQL database module with pgvector support for semantic search.

## Files

- `schema.sql` - Complete database schema with all tables, indexes, functions
- `queries.py` - Helper functions for database operations
- `__init__.py` - Module exports
- `requirements.txt` - Python dependencies

## Setup

### 1. Install PostgreSQL 14+

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-14 postgresql-contrib-14

# Windows
# Download from https://www.postgresql.org/download/windows/
```

### 2. Install pgvector

```bash
# Clone and build pgvector
cd /tmp
git clone --branch v0.6.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### 3. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE technova;

# Connect to database
\c technova

# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Run Schema

```bash
# Apply schema
psql -U postgres -d technova -f database/schema.sql
```

### 5. Install Python Dependencies

```bash
pip install -r database/requirements.txt
```

### 6. Set Environment Variables

```bash
export DATABASE_URL=postgresql://postgres:password@localhost:5432/technova
export PGVECTOR_DIMENSION=1536
export DB_MIN_CONNECTIONS=2
export DB_MAX_CONNECTIONS=10
```

## Usage

```python
from database import (
    init_database,
    close_database,
    CustomerQueries,
    TicketQueries,
    KnowledgeBaseQueries,
)

# Initialize
init_database()

# Create customer
customer = CustomerQueries.create_or_update_customer(
    customer_id="CUST-001",
    name="John Doe",
    email="john@example.com",
    account_tier="pro"
)

# Create ticket
ticket = TicketQueries.create_ticket(
    ticket_id="TKT-001",
    customer_id="CUST-001",
    subject="Integration Help",
    description="Need help with Slack integration",
    channel="email",
    category="how_to"
)

# Search knowledge base
from openai import OpenAI
client = OpenAI()

embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input="Slack integration"
).data[0].embedding

results = KnowledgeBaseQueries.search_semantic(embedding, limit=5)

# Close
close_database()
```

## Schema Overview

### Core Tables

| Table | Purpose |
|-------|---------|
| `customers` | Customer profiles and preferences |
| `conversations` | Conversation threads across channels |
| `messages` | Individual messages with analysis |
| `tickets` | Support tickets with SLA tracking |
| `knowledge_base` | KB articles with pgvector embeddings |
| `escalations` | Escalation tracking and handoff |
| `agent_sessions` | Agent performance tracking |
| `system_logs` | System logging |

### Key Features

- **pgvector semantic search** - 1536-dimensional embeddings
- **Multi-channel support** - Email, WhatsApp, Web Form
- **Sentiment tracking** - Per message, conversation, and customer
- **SLA management** - Priority-based deadlines
- **Escalation workflow** - 10 escalation rules
- **Analytics views** - Pre-built reporting views

### Indexes

- B-tree indexes on all foreign keys
- pgvector IVFFlat index for semantic search
- Partial indexes for open tickets and pending escalations
- Composite indexes for common query patterns

## Database Functions

- `update_updated_at_column()` - Auto-update timestamps
- `get_customer_sentiment_trend()` - Customer sentiment analysis
- `get_open_tickets_by_priority()` - Ticket dashboard
- `search_knowledge_base()` - Semantic search function

## Views

- `customer_summary` - Customer overview with stats
- `ticket_dashboard` - Ticket analytics by date/channel
- `escalation_summary` - Escalation statistics
