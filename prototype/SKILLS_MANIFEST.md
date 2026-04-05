# Agent Skills Manifest

This document defines the core skills for the customer support agent system.

---

## 1. Knowledge Retrieval Skill

**Purpose:** Retrieve relevant information from company documentation, product docs, and historical tickets to answer customer queries accurately.

### When to Use
- Customer asks a question about products, services, or policies
- Need to verify company procedures or guidelines
- Looking for similar past tickets for reference
- Agent needs context-specific information to formulate a response

### Inputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | The customer's question or topic to search for |
| `context` | object | Optional context (customer tier, product category, urgency) |
| `sources` | string[] | Preferred knowledge sources (e.g., ["product-docs", "sample-tickets"]) |

### Outputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `results` | array | List of relevant documents/snippets with relevance scores |
| `confidence` | number | Overall confidence score (0-1) of retrieved information |
| `source_used` | string[] | Which knowledge sources were queried |

---

## 2. Sentiment Analysis Skill

**Purpose:** Analyze customer情绪 (emotion/tone) to understand their state and adapt responses accordingly.

### When to Use
- Incoming customer message needs emotional context
- Determining if a customer is frustrated, angry, or satisfied
- Deciding response tone and urgency level
- Monitoring conversation flow for sentiment changes

### Inputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | string | The customer's message text |
| `conversation_history` | array | Previous messages in the conversation (optional) |
| `customer_profile` | object | Customer tier, past interactions (optional) |

### Outputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `sentiment` | string | Overall sentiment: "positive", "neutral", "negative", "angry", "frustrated" |
| `confidence` | number | Confidence score (0-1) |
| `urgency_level` | string | "low", "medium", "high", "critical" |
| `emotions` | object | Detected emotions with scores (e.g., {anger: 0.8, frustration: 0.6}) |
| `recommended_tone` | string | Suggested agent response tone: "empathetic", "professional", "friendly", "apologetic" |

---

## 3. Escalation Decision Skill

**Purpose:** Determine when a ticket or conversation should be escalated to a human agent or higher support tier.

### When to Use
- Customer explicitly requests escalation
- Issue exceeds agent's capability or authority
- Sentiment indicates high frustration/anger
- Complex technical or billing issue detected
- SLA or compliance requirements trigger escalation

### Inputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `ticket_content` | string | Full ticket or conversation content |
| `sentiment_analysis` | object | Output from Sentiment Analysis Skill |
| `customer_tier` | string | Customer level (e.g., "standard", "premium", "enterprise") |
| `issue_category` | string | Classified issue type (e.g., "billing", "technical", "complaint") |
| `resolution_attempts` | number | Number of attempted solutions |
| `conversation_duration` | number | Time spent on current conversation (minutes) |

### Outputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `should_escalate` | boolean | Decision to escalate (true/false) |
| `escalation_reason` | string | Reason for escalation decision |
| `priority` | string | "low", "medium", "high", "urgent" |
| `target_team` | string | Recommended team (e.g., "technical-support", "billing", "manager") |
| `context_summary` | string | Summary to pass to human agent |
| `confidence` | number | Confidence in escalation decision (0-1) |

---

## 4. Channel Adaptation Skill

**Purpose:** Adapt response format, tone, and content based on the communication channel (email, chat, phone, social media).

### When to Use
- Preparing a response for a specific channel
- Adjusting message length and formality
- Determining appropriate media (text, images, links)
- Multi-channel conversation handoff

### Inputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `channel` | string | Communication channel: "email", "chat", "phone", "social-media", "sms" |
| `response_content` | string | Base response content to adapt |
| `customer_preferences` | object | Customer's channel preferences and history |
| `urgency` | string | Urgency level from sentiment analysis |
| `media_attachments` | array | Optional attachments to include |

### Outputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `adapted_response` | string | Channel-optimized response text |
| `format` | object | Formatting specifications (length, structure, style) |
| `media_recommendations` | array | Suggested media to include (screenshots, links, documents) |
| `timing` | object | Recommended send time/delay for this channel |
| `follow_up_needed` | boolean | Whether follow-up is expected on this channel |

---

## 5. Customer Identification Skill

**Purpose:** Identify and verify customer identity, retrieve their profile, and personalize the interaction.

### When to Use
- Customer initiates contact
- Verification is required before accessing account information
- Personalizing responses based on customer history
- Determining customer tier and associated privileges

### Inputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `identifier` | string | Customer-provided identifier (email, phone, account ID, name) |
| `identifier_type` | string | Type of identifier: "email", "phone", "account_id", "name" |
| `verification_data` | object | Additional verification info (order number, last purchase, etc.) |
| `channel` | string | Communication channel being used |

### Outputs
| Parameter | Type | Description |
|-----------|------|-------------|
| `customer_found` | boolean | Whether customer was identified |
| `customer_id` | string | Unique customer identifier |
| `customer_profile` | object | Full customer profile (tier, history, preferences) |
| `verification_status` | string | "verified", "partial", "unverified", "failed" |
| `personalization_context` | object | Context for personalizing response (name, tier benefits, recent activity) |
| `recommended_actions` | array | Suggested actions based on customer profile |

---

## Skill Interaction Flow

```
┌─────────────────────────┐
│  Customer Identification │
│       (Skill 5)          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Sentiment Analysis    │
│       (Skill 2)          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Knowledge Retrieval   │
│       (Skill 1)          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Escalation Decision   │
│       (Skill 3)          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Channel Adaptation    │
│       (Skill 4)          │
└───────────┴─────────────┘
            │
            ▼
    ┌───────────────┐
    │   Response    │
    │   to Customer │
    └───────────────┘
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-01 | Initial skills manifest creation |
