# 🚀 Quick Start Guide - TechNova Agent

## 5-Minute Setup

### 1. Database Setup (2 min)

```bash
# PostgreSQL mein login karo
psql -U postgres

# Database banao
CREATE DATABASE technova;
\c technova

# Extensions aur tables
CREATE EXTENSION IF NOT EXISTS vector;

# Schema copy-paste karo (from tools.py end)
```

### 2. Environment Setup (1 min)

```bash
cd production

# .env file edit karo
notepad .env

# Add your OpenAI API key:
OPENAI_API_KEY=sk-...
```

### 3. Install Dependencies (1 min)

```bash
# Virtual environment
python -m venv venv
venv\Scripts\activate

# Install
pip install openai pydantic psycopg2-binary pgvector python-dotenv
```

### 4. Seed Knowledge Base (1 min)

```bash
python agent/seed_kb.py
```

---

## Run Examples

### Example 1: Simple Customer Query

```bash
python agent/simple_agent.py
```

**Output:**
```
📩 Customer Message:
   From: John Doe <john@company.com>
   Message: Hi, how do I integrate TechNova with Slack?

1️⃣ Creating ticket...
   ✓ Ticket ID: TKT-ABC123
   ✓ Category: how_to
   ✓ Priority: P3

2️⃣ Searching knowledge base...
   ✓ Found 1 results
   ✓ Top result: Slack Integration

3️⃣ Generating response...
   ✓ Response generated

📧 FINAL RESPONSE TO CUSTOMER:
Hi John,

Thanks for reaching out! I'd be happy to help you with Slack integration.

Here's how to do it:

1. Go to Settings → Integrations
2. Click "Connect Slack"
3. Authorize TechNova in Slack
4. Select channels for notifications
5. Click "Save"

If you need any further assistance, feel free to reach out.

Best regards,
TechNova Support Team
```

### Example 2: Test All Tools

```bash
python agent/test_tools.py
```

---

## OpenAI Agent Ke Saath Use

### Full Agent Example

```python
from openai.agents import Agent
from agent.tools import ALL_TOOLS

# Agent banao
agent = Agent(
    name="TechNova Support",
    tools=ALL_TOOLS,
    instructions="""You are a helpful customer support assistant for TechNova.
    - Use search_knowledge_base to find product information
    - Use create_ticket to track customer issues
    - Use send_response to reply to customers
    - Use escalate_to_human for billing/legal issues"""
)

# Run
response = await agent.run("How do I add team members?")
print(response)
```

### With Conversation History

```python
from openai.agents import Agent
from agent.tools import ALL_TOOLS, get_customer_history, GetCustomerHistoryInput

agent = Agent(
    name="TechNova Support",
    tools=ALL_TOOLS,
)

# Customer history fetch karo
history = await get_customer_history(GetCustomerHistoryInput(
    customer_email="user@company.com"
))

# Context ke saath respond karo
response = await agent.run(
    "Customer asking about Slack integration. "
    f"They have {history.statistics['total_tickets']} previous tickets. "
    f"Sentiment trend: {history.sentiment_trend}"
)
```

---

## Manual Testing

### Tool 1: Knowledge Base Search

```python
from agent.tools import search_knowledge_base, SearchKnowledgeBaseInput

result = await search_knowledge_base(SearchKnowledgeBaseInput(
    query="How to reset password?",
    limit=3
))

for doc in result.results:
    print(f"Feature: {doc.feature}")
    print(f"Confidence: {doc.confidence}")
```

### Tool 2: Create Ticket

```python
from agent.tools import create_ticket, CreateTicketInput

ticket = await create_ticket(CreateTicketInput(
    customer_email="test@example.com",
    customer_name="Test User",
    channel="email",
    subject="Need help",
    message="How do I use this?"
))

print(f"Ticket: {ticket.ticket.ticket_id}")
print(f"Category: {ticket.ticket.category}")
```

### Tool 3: Send Response

```python
from agent.tools import send_response, SendResponseInput

response = await send_response(SendResponseInput(
    customer_email="test@example.com",
    channel="whatsapp",
    message="How do I add tasks?",
    category="how_to",
    customer_name="Test"
))

print(response.response.text)
```

---

## Troubleshooting

### ❌ Database Connection Error

```bash
# Check PostgreSQL is running
pg_ctl status

# Connection string verify karo
echo $DATABASE_URL
# Should be: postgresql://postgres:password@localhost:5432/technova
```

### ❌ OpenAI API Error

```bash
# API key check karo
echo $OPENAI_API_KEY

# Test karo
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### ❌ pgvector Error

```bash
# Extension check karo
psql -U postgres -d technova -c "CREATE EXTENSION IF NOT EXISTS vector;"

# pgvector install karo
pip install pgvector
```

---

## Next Steps

1. ✅ Run `simple_agent.py` - Basic example
2. ✅ Run `test_tools.py` - Test all tools
3. ✅ Add more knowledge base articles
4. ✅ Integrate with your application
5. ✅ Deploy to production

---

## File Structure

```
production/
├── .env                          # Your config
├── agent/
│   ├── tools.py                  # Main tools (5 @function_tool)
│   ├── simple_agent.py           # Example to run
│   ├── test_tools.py             # Test suite
│   ├── seed_kb.py                # Seed database
│   └── README.md                 # Full docs
└── ...
```

---

## Help

- Full docs: `agent/README.md`
- Test: `python agent/test_tools.py`
- Example: `python agent/simple_agent.py`

**Happy Coding!** 🎉
