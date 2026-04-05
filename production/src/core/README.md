# Production Module: Core

**Purpose:** Core orchestration and shared infrastructure

## Components

### `orchestrator.py`
- End-to-end pipeline coordination
- Module integration
- Error handling & recovery
- Logging & metrics

**Pipeline Flow:**
```
1. Ingestion → 2. Analysis → 3. Routing → 4. Generation → 5. Delivery
```

### `customer_profile.py`
- Customer identity management
- Profile unification (email + phone + company)
- Preference tracking (channel, tone, timezone)
- Ticket history management

**Schema:**
```python
{
    "customer_id": "CUST-XXXXX",
    "email": "customer@example.com",
    "phone": "+1-555-XXXX",
    "company": "Company Name",
    "account_tier": "Enterprise",
    "arr": 75000,
    "preferred_channel": "email",
    "communication_style": "formal",
    "timezone": "EST",
    "ticket_history": ["TKT-001", "TKT-015"],
    "sentiment_trend": "neutral",
    "vip_status": True
}
```

### `knowledge_base.py`
- Vector database integration
- Semantic search
- Document embedding management
- KB article CRUD

### `conversation_store.py`
- Conversation history persistence
- Cross-channel thread merging
- Audit trail logging
- Data retention policies

### `config.py`
- Environment configuration
- Feature flags
- API key management
- Rate limiting config

## Dependencies
- PostgreSQL/MongoDB (customer profiles)
- Redis (caching, sessions)
- Vector DB (Pinecone/Weaviate)
