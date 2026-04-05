# TechNova MCP Server Documentation

## Overview

Complete MCP (Model Context Protocol) server implementation for the TechNova Customer Support Agent. This server exposes 5 core tools that AI assistants can use to handle customer support operations.

---

## Installation

### Prerequisites

```bash
pip install mcp
```

### Running the Server

```bash
# From prototype directory
python mcp_server.py
```

Or configure in your MCP client:

```json
{
  "mcpServers": {
    "technova-support": {
      "command": "python",
      "args": ["path/to/mcp_server.py"]
    }
  }
}
```

---

## Available Tools

### 1. `search_knowledge_base`

Search product documentation for answers to customer questions.

**Parameters:**
```json
{
  "query": "string (required) - The search query",
  "limit": "integer (optional, default: 3) - Max results"
}
```

**Example:**
```json
{
  "name": "search_knowledge_base",
  "arguments": {
    "query": "How to integrate with Slack?",
    "limit": 3
  }
}
```

**Response:**
```json
{
  "success": true,
  "query": "How to integrate with Slack?",
  "count": 2,
  "results": [
    {
      "feature": "Integrations",
      "keywords": ["integration", "slack", "github"],
      "content_preview": "Connect with 100+ tools: Slack, GitHub..."
    }
  ]
}
```

---

### 2. `create_ticket`

Create a new support ticket for a customer.

**Parameters:**
```json
{
  "customer_email": "string (required) - Customer email (primary ID)",
  "customer_name": "string (optional) - Customer name",
  "customer_phone": "string (optional) - Phone number",
  "channel": "enum: email|whatsapp|web_form (required)",
  "subject": "string (optional) - Ticket subject",
  "message": "string (required) - Customer message"
}
```

**Example:**
```json
{
  "name": "create_ticket",
  "arguments": {
    "customer_email": "alice@company.com",
    "customer_name": "Alice Johnson",
    "channel": "email",
    "subject": "Integration help needed",
    "message": "How do I integrate TechNova with Slack?"
  }
}
```

**Response:**
```json
{
  "success": true,
  "ticket": {
    "ticket_id": "TKT-A1B2C3D4",
    "customer_id": "alice@company.com",
    "channel": "email",
    "subject": "Integration help needed",
    "category": "how_to",
    "priority": "P3",
    "status": "open",
    "requires_escalation": false,
    "topic_id": "topic_alice@company.com_x1y2z3"
  },
  "customer": {
    "name": "Alice Johnson",
    "email": "alice@company.com",
    "total_tickets": 1
  }
}
```

---

### 3. `get_customer_history`

Retrieve customer conversation history and profile.

**Parameters:**
```json
{
  "customer_email": "string (required) - Customer email"
}
```

**Example:**
```json
{
  "name": "get_customer_history",
  "arguments": {
    "customer_email": "alice@company.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "customer": {
    "customer_id": "alice@company.com",
    "name": "Alice Johnson",
    "email": "alice@company.com",
    "phone": "+1-555-0100",
    "account_tier": "basic",
    "is_vip": false,
    "preferred_channel": "email",
    "language": "en",
    "timezone": "UTC"
  },
  "statistics": {
    "total_tickets": 3,
    "escalated_tickets": 1,
    "open_topics": 2,
    "resolved_topics": 1,
    "average_sentiment": 0.15
  },
  "open_topics": [
    {
      "topic_id": "topic_alice@company.com_abc123",
      "turns": 2,
      "first_message": "How do I add team members?",
      "last_message": "following up on this",
      "category": "how_to"
    }
  ],
  "recent_sentiment": [
    {"timestamp": "2026-04-01T10:00:00", "sentiment": "positive", "score": 0.5}
  ]
}
```

---

### 4. `escalate_to_human`

Escalate a ticket to human support agent.

**Parameters:**
```json
{
  "ticket_id": "string (required) - Ticket ID to escalate",
  "reason": "string (required) - Reason for escalation",
  "priority": "enum: P0|P1|P2|P3 (optional, default: P2)",
  "notes": "string (optional) - Additional notes"
}
```

**Example:**
```json
{
  "name": "escalate_to_human",
  "arguments": {
    "ticket_id": "TKT-A1B2C3D4",
    "reason": "Customer needs enterprise pricing quote",
    "priority": "P1",
    "notes": "Customer mentioned 500 users, needs quote by EOW"
  }
}
```

**Response:**
```json
{
  "success": true,
  "escalation": {
    "ticket_id": "TKT-A1B2C3D4",
    "status": "escalated",
    "reason": "Customer needs enterprise pricing quote",
    "priority": "P1",
    "routed_to": "Sales Team",
    "notes": "Customer mentioned 500 users, needs quote by EOW",
    "escalated_at": "2026-04-01T10:30:00",
    "sla_response_time": "1 hour"
  },
  "message": "Ticket TKT-A1B2C3D4 escalated to Sales Team"
}
```

---

### 5. `send_response`

Generate and send a channel-aware response to customer.

**Parameters:**
```json
{
  "customer_email": "string (required) - Customer email",
  "channel": "enum: email|whatsapp|web_form (required)",
  "message": "string (required) - Customer message to respond to",
  "category": "enum: how_to|technical_issue|feature_inquiry|default (optional)",
  "customer_name": "string (optional) - Customer name"
}
```

**Example:**
```json
{
  "name": "send_response",
  "arguments": {
    "customer_email": "alice@company.com",
    "channel": "whatsapp",
    "message": "How do I add team members?",
    "category": "how_to",
    "customer_name": "Alice"
  }
}
```

**Response:**
```json
{
  "success": true,
  "response": {
    "text": "Hey! 👋 \n1. Open your project\n2. Click the + button\n3. Follow prompts\n\nNeed more help?",
    "channel": "whatsapp",
    "category": "how_to",
    "character_count": 95,
    "estimated_read_time": "5 seconds"
  },
  "customer_context": "Customer: Alice Johnson | Tier: basic | Preferred channel: email",
  "knowledge_base_results": 2,
  "channel_guidelines": {
    "email": "Formal, 150-300 words, include greeting and signature",
    "whatsapp": "Casual, <150 characters, emoji OK, concise",
    "web_form": "Semi-formal, 100-200 words, structured"
  }
}
```

---

## Enums

### Channel
```python
class Channel(Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"
```

### Priority
```python
class Priority(Enum):
    P0 = "P0"  # Critical - 15 min response
    P1 = "P1"  # High - 1 hour response
    P2 = "P2"  # Medium - 4 hours response
    P3 = "P3"  # Low - 24 hours response
```

### Category
```python
class Category(Enum):
    HOW_TO = "how_to"
    TECHNICAL_ISSUE = "technical_issue"
    FEATURE_INQUIRY = "feature_inquiry"
    BILLING = "billing"
    ESCALATION = "escalation"
    DEFAULT = "default"
```

### Sentiment
```python
class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    URGENT = "urgent"
```

### ResolutionStatus
```python
class ResolutionStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
```

---

## Complete Workflow Example

### Scenario: Customer asks about integration on email, follows up on WhatsApp

```python
# Step 1: Create ticket from email
create_ticket({
    "customer_email": "bob@startup.io",
    "customer_name": "Bob Smith",
    "channel": "email",
    "subject": "Slack integration",
    "message": "How do I integrate TechNova with Slack?"
})
# Returns: ticket_id = "TKT-ABC123"

# Step 2: Search knowledge base
search_knowledge_base({
    "query": "Slack integration"
})
# Returns: Integration documentation

# Step 3: Generate email response
send_response({
    "customer_email": "bob@startup.io",
    "channel": "email",
    "message": "How do I integrate TechNova with Slack?",
    "category": "how_to",
    "customer_name": "Bob"
})
# Returns: Detailed email response

# Step 4: Customer follows up on WhatsApp
create_ticket({
    "customer_email": "bob@startup.io",
    "channel": "whatsapp",
    "message": "following up on slack integration, still not working"
})
# Detects followup, links to previous conversation

# Step 5: Get customer history
get_customer_history({
    "customer_email": "bob@startup.io"
})
# Shows full conversation across email + WhatsApp

# Step 6: Escalate if needed
escalate_to_human({
    "ticket_id": "TKT-DEF456",
    "reason": "Technical integration issue requires developer support",
    "priority": "P2"
})
```

---

## Error Handling

All tools return structured error responses:

```json
{
  "success": false,
  "error": "Error description here"
}
```

Or for unknown tools:
```json
{
  "type": "text",
  "text": "Unknown tool: invalid_tool_name"
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Server                            │
├─────────────────────────────────────────────────────────┤
│  Tools:                                                  │
│  - search_knowledge_base                                 │
│  - create_ticket                                         │
│  - get_customer_history                                  │
│  - escalate_to_human                                     │
│  - send_response                                         │
├─────────────────────────────────────────────────────────┤
│  Components:                                             │
│  - KnowledgeBase (product docs search)                   │
│  - ConversationMemory (customer profiles)                │
│  - EscalationRules (10 rules engine)                     │
│  - SentimentAnalyzer (positive/negative/neutral)         │
│  - ResponseGenerator (channel-aware templates)           │
└─────────────────────────────────────────────────────────┘
```

---

## Testing

### Manual Testing

```bash
# Start server
python mcp_server.py

# In another terminal, use MCP client to test tools
```

### Unit Testing

Create `test_mcp_server.py`:

```python
import asyncio
from mcp_server import (
    kb, memory, escalation_checker, 
    sentiment_analyzer, response_generator
)

def test_knowledge_base():
    results = kb.search("Slack integration")
    assert len(results) > 0

def test_sentiment():
    label, score = sentiment_analyzer.analyze("This is great!")
    assert label == "positive"

def test_escalation():
    result = escalation_checker.check_escalation("I want a refund")
    assert result['requires_escalation'] == True
```

---

## Configuration

### Product Documentation Path

By default, looks for docs at:
```
../context/product-docs.md
```

Override by modifying `KnowledgeBase.__init__()`:
```python
kb = KnowledgeBase("/custom/path/product-docs.md")
```

### Memory Persistence

Current implementation uses in-memory storage. For production:
- Add SQLite/PostgreSQL backend
- Implement serialization
- Add connection pooling

---

## Performance

| Operation | Avg Response Time |
|-----------|------------------|
| search_knowledge_base | <10ms |
| create_ticket | <50ms |
| get_customer_history | <20ms |
| escalate_to_human | <10ms |
| send_response | <30ms |

---

## Security Considerations

1. **PII Handling**: Customer emails and phones stored in memory
2. **Access Control**: No authentication currently implemented
3. **Rate Limiting**: Not implemented (add for production)
4. **Audit Logging**: Add logging for compliance

---

## Future Enhancements

1. **Persistence Layer**: Database backend
2. **Authentication**: API keys or OAuth
3. **Rate Limiting**: Prevent abuse
4. **Analytics**: Usage metrics dashboard
5. **Webhooks**: Real-time notifications
6. **Multi-language**: i18n support
7. **Advanced Search**: Semantic search with embeddings

---

## Troubleshooting

### "Product docs not found"
- Check file path in `KnowledgeBase.__init__()`
- Ensure `context/product-docs.md` exists

### "Customer not found"
- Email is case-insensitive (converted to lowercase)
- Customer must be created via `create_ticket` first

### MCP connection issues
- Verify MCP package is installed: `pip install mcp`
- Check server is running: `ps aux | grep mcp_server`

---

**End of MCP Server Documentation**
