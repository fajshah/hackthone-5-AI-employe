# TechNova Customer Support Agent Prototype

## Overview

This is the core customer interaction loop prototype for Hackathon 5. It demonstrates:
- Multi-channel message handling (Email, WhatsApp, Web Form)
- Intent categorization
- Sentiment analysis
- Knowledge base search
- Escalation rule evaluation
- Channel-aware response generation

## Files

```
prototype/
├── agent_core.py        # Main agent implementation
├── test_agent.py        # Automated test suite
├── interactive_test.py  # Interactive console for testing
└── README.md            # This file
```

## Quick Start

### Run Interactive Test Console
```bash
cd prototype
python interactive_test.py
```

### Run Automated Tests
```bash
cd prototype
python test_agent.py
```

### Run Demo
```bash
cd prototype
python agent_core.py
```

## Usage Examples

### Interactive Console Commands

```
/email              - Switch to email channel
/whatsapp           - Switch to WhatsApp channel  
/web                - Switch to web form channel
/name John Doe      - Set customer name
/quit               - Exit

# Then just type your message:
"how do I add team members?"
"app crashing 😤"
"Enterprise pricing for 100 users?"
```

### Programmatic Usage

```python
from agent_core import CustomerSupportAgent, CustomerMessage

# Initialize agent
agent = CustomerSupportAgent()

# Create a message
msg = CustomerMessage(
    channel='whatsapp',
    customer_name='Alex Johnson',
    customer_phone='+1-555-0101',
    message='hey, how do I add someone to my project?'
)

# Process and get response
response = agent.process_message(msg)

print(f"Category: {response.category}")
print(f"Escalation: {response.requires_escalation}")
print(f"Response: {response.response_text}")
```

## Features

### 1. Channel-Aware Responses

**Email** (Formal, Detailed):
```
Hi Sarah,

Thanks for reaching out! I'd be happy to help you with creating a new project.

Here's how to do it:

1. Log in to your TechNova account
2. Navigate to the relevant project
3. Look for the action button in the top-right corner
4. Follow the on-screen instructions

If you need any further assistance, feel free to reach out.

Best regards,
TechNova Support Team
```

**WhatsApp** (Casual, Concise):
```
Hey! 👋 
• Open your project
• Click the + button

Need more help?
```

### 2. Escalation Rules

The agent automatically escalates based on 10 rules:

| Rule | Trigger | Priority |
|------|---------|----------|
| Pricing & Enterprise | "enterprise", "pricing", "quote" | P1 |
| Refund & Billing | "refund", "charged twice" | P1 |
| Legal & Compliance | "gdpr", "hipaa", "soc 2" | P0 |
| Angry Customer | "unacceptable", "worst" | P1 |
| System Bugs | "not working", "broken" | P0 |
| Data Loss | "data lost", "hacked" | P0 |
| VIP Customer | "enterprise plan" | P1 |
| API Support | "api", "webhook" | P2 |
| Cancellation | "cancel", "leaving" | P2 |
| Feature Requests | "feature request" | P3 |

### 3. Sentiment Analysis

Detects: positive, negative, neutral, urgent

Based on:
- Keyword matching
- Urgency indicators (!!!, "ASAP", "URGENT")
- Emoji detection

### 4. Intent Categorization

Automatically categorizes messages into:
- `how_to` - Questions about using features
- `technical_issue` - Bug reports and problems
- `feature_inquiry` - Questions about capabilities
- `default` - Everything else

## Iteration History

### Iteration 1: Initial Prototype
- Basic message processing loop
- Simple keyword-based categorization
- 10 escalation rules
- Template-based responses

### Iteration 2: Path Handling Fix
- Fixed product docs loading from multiple paths
- Added fallback paths for flexibility

### Iteration 3: WhatsApp Optimization
- Made WhatsApp responses more concise (<150 chars)
- Added action text generation
- Improved bullet point formatting

### Iteration 4: Topic Extraction
- Better topic extraction from questions
- Removed question starters from topics
- Cleaner response formatting

## Testing

### Test Categories

1. **Pricing Inquiry** - Should escalate to Sales
2. **WhatsApp Short** - Response should be <200 chars
3. **Email Format** - Should have greeting + signature
4. **WhatsApp Concise** - Response should be <150 chars
5. **Bug Report** - Should categorize as technical_issue
6. **Angry Customer** - Should detect negative sentiment + escalate

### Adding New Tests

Edit `test_agent.py` and add a new test case:

```python
# Test X: Description
msg = CustomerMessage(
    channel='email',
    customer_name='Test User',
    message='Your test message here'
)
resp = agent.process_message(msg)
print(f"Result: {resp.response_text}")
```

## Next Steps (Future Iterations)

1. **Better KB Search** - Implement semantic search with embeddings
2. **LLM Integration** - Use LLM for response generation
3. **Conversation History** - Track multi-turn conversations
4. **Customer Profile** - Store customer preferences and history
5. **Analytics Dashboard** - Track response quality and metrics
6. **Human Handoff** - Implement escalation to human agents
7. **Multi-language** - Support for multiple languages

## Known Limitations

1. KB search is keyword-based (not semantic)
2. Responses are template-based (not generated)
3. No conversation memory across messages
4. Sentiment analysis is basic (rule-based)
5. No support for attachments/images

## Troubleshooting

**"Product docs not found" warning:**
- Make sure `context/product-docs.md` exists
- Run from the `prototype` directory
- Check file path in `CustomerSupportAgent.__init__()`

**Responses too generic:**
- Check if KB search is finding relevant documents
- Add more keywords to feature documentation
- Verify categorization is working correctly

## Contact

For questions about this prototype, refer to the `specs/discovery-log.md` for detailed requirements analysis.
