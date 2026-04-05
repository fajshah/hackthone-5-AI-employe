# Production Module: Generation

**Purpose:** AI-powered response generation with brand voice and templates

## Components

### `response_generator.py`
- LLM-based response generation
- RAG integration (knowledge base)
- Template selection (channel × category × sentiment)
- Brand voice enforcement

### `template_library.py`
- 10 response pattern templates
- Channel-specific formatting
- Variable substitution
- Fallback templates for edge cases

**Template Matrix:**
| Channel | Category | Sentiment | Template ID |
|---------|----------|-----------|-------------|
| Email | Technical | Neutral | email-tech-neutral |
| Email | Billing | Frustrated | email-billing-frustrated |
| WhatsApp | How-to | Neutral | whatsapp-howto-neutral |
| WhatsApp | Bug | Angry | whatsapp-bug-angry |
| Web Form | Technical | Neutral | webform-tech-neutral |
| ... | ... | ... | ... |

### `brand_voice_checker.py`
- Tone validation
- Forbidden phrase detection
- Brand guidelines enforcement
- Quality scoring

### `context_retriever.py`
- Customer history lookup
- Knowledge base semantic search
- Similar ticket retrieval
- Product doc references

## Input/Output

**Input:**
- Normalized ticket
- Analysis results (intent, sentiment, entities)
- Routing decision
- Customer profile

**Output:**
```python
{
    "response_text": "Hi Jennifer,...",
    "channel_format": "email",
    "word_count": 187,
    "tone": "empathetic",
    "template_used": "email-billing-frustrated",
    "brand_voice_score": 4.5,
    "kb_articles_referenced": ["KB-001", "KB-015"],
    "confidence": 0.92
}
```

## LLM Configuration
- Model: GPT-4 / Claude / Llama (configurable)
- Temperature: 0.7 (balanced creativity/accuracy)
- Max tokens: 500
- System prompt: See TRANSITION_CHECKLIST.md §2
