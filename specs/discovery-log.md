# Discovery Log - Hackathon 5

**Date:** April 1, 2026  
**Company:** TechNova (AI-powered project management SaaS)  
**Analysis Scope:** 60 sample support tickets across 3 channels

---

## 1. Sample Ticket Analysis

### 1.1 Channel Distribution

| Channel | Count | Percentage | Avg Length | Characteristics |
|---------|-------|------------|------------|-----------------|
| Email | 20 | 33.3% | 250-400 words | Formal, detailed, structured |
| WhatsApp | 20 | 33.3% | 5-15 words | Casual, urgent, emoji usage |
| Web Form | 20 | 33.3% | 50-100 words | Semi-formal, concise, structured |

### 1.2 Email Channel Patterns

**Characteristics:**
- **Length:** Long-form (150-400 words)
- **Structure:** Greeting → Context → Problem → Details → Sign-off
- **Tone:** Professional, formal salutations ("Dear", "Best regards")
- **Content:** Rich context, transaction IDs, technical details, attachments mentioned

**Common Patterns:**
```
Email Structure:
1. Formal greeting ("Dear TechNova Team", "Hi there")
2. Customer introduction (role, company)
3. Detailed problem description
4. Supporting evidence (transaction IDs, error messages, steps to reproduce)
5. Clear ask/expectation
6. Professional sign-off with contact info
```

**Email Categories (from 20 tickets):**
- Technical Integration: 4 (SSO, API, SAP, Webhooks)
- Billing/Refund: 3
- Feature Requests: 2
- Compliance/Security: 2
- Training/Onboarding: 2
- Performance Issues: 2
- Sales/Pricing: 2
- Account Management: 2
- Mobile Bugs: 1

**Example Email Indicators:**
- Contains newline characters (`\n`)
- Has signature block (name, title, company, phone)
- Multiple paragraphs
- Transaction IDs (TXN-XXXXXXX)
- Formal language ("Could someone please", "I would appreciate")

### 1.3 WhatsApp Channel Patterns

**Characteristics:**
- **Length:** Ultra-short (3-15 words)
- **Structure:** Direct question/statement, no formal structure
- **Tone:** Casual, conversational, emotional
- **Content:** Immediate problems, quick questions, emotional expressions

**Common Patterns:**
```
WhatsApp Structure:
1. Optional greeting ("hey", "hi")
2. Direct problem statement or question
3. Optional emoji (😤, 😕, 🙏, 🎉)
4. No sign-off
```

**WhatsApp Categories (from 20 tickets):**
- How-to Questions: 4
- Technical Bugs: 4
- Billing/Payment: 3
- Account Access: 2
- Feature Requests: 2
- Integration Issues: 1
- Plan/Pricing: 2
- Cancellation: 1
- Positive Feedback: 1

**Example WhatsApp Indicators:**
- Lowercase text ("hey", "can u", "pls")
- Abbreviations ("u" for you, "pls" for please)
- Emoji usage (😤, 😕, 🙏, 🎉, ✅)
- Multiple exclamation marks ("urgent!!", "THANK YOU!!!")
- No formal greeting or sign-off
- Phone number format: +1-555-XXXX

**WhatsApp Sentiment Distribution:**
- Neutral/Casual: 12 (60%)
- Frustrated/Urgent: 5 (25%)
- Happy/Appreciative: 2 (10%)
- Angry: 1 (5%)

### 1.4 Web Form Channel Patterns

**Characteristics:**
- **Length:** Medium (30-100 words)
- **Structure:** Subject line + structured message
- **Tone:** Semi-formal, direct
- **Content:** Specific issues, technical details, browser/device info

**Common Patterns:**
```
Web Form Structure:
1. Subject line (specific topic)
2. Problem statement
3. Technical context (browser, version, account type)
4. Specific ask
5. No formal greeting/sign-off
```

**Web Form Categories (from 20 tickets):**
- Technical Bugs: 5
- Feature Requests/Inquiries: 4
- Billing/Payment: 3
- Enterprise/Sales: 3
- Compliance/Security: 2
- Settings/Configuration: 2
- Data Migration: 1

**Example Web Form Indicators:**
- Has subject line field
- Mentions browser versions ("Chrome 122", "Firefox 123")
- Account type mentioned ("Pro plan", "Enterprise")
- Technical specifications included
- No emotional language
- Concise, factual tone

---

## 2. Hidden Requirements Discovery

### 2.1 Cross-Channel Memory Requirements

**Discovery:** Customers contact support through multiple channels, and context must persist.

**Requirements:**
1. **Customer Identity Resolution:**
   - Same customer may use email (jennifer.martinez@acmecorp.com) and WhatsApp (+1-555-0101)
   - Need to link accounts via email/phone/company name
   - Historical tickets must be accessible regardless of channel

2. **Conversation Continuity:**
   - If customer starts on WhatsApp and follows up via email, agent must see full history
   - Escalation notes from one channel must visible in all channels
   - Status updates must sync across channels

3. **Preference Learning:**
   - Track customer's preferred channel
   - Remember communication style (formal vs casual)
   - Store timezone, language preferences

**Implementation Notes:**
```
Customer Profile Schema:
{
  customer_id: "CUST-001",
  email: "jennifer.martinez@acmecorp.com",
  phone: "+1-555-0101",
  company: "Acme Corporation",
  preferred_channel: "email",
  communication_style: "formal",
  timezone: "EST",
  account_tier: "Enterprise",
  ticket_history: ["TKT-001", "TKT-015", ...],
  sentiment_trend: "neutral",
  vip_status: true
}
```

### 2.2 Sentiment Analysis Requirements

**Discovery:** Customer emotional state varies significantly and affects response strategy.

**Sentiment Categories Identified:**

| Sentiment | Indicators | Count | Response Strategy |
|-----------|------------| 3 | Empathy + Urgent Action |
| Frustrated | "frustrating", "not acceptable", "issues" | 8 | Acknowledge + Solution |
| Neutral | Factual questions, how-to | 35 | Direct + Helpful |
| Happy | "love", "thank you", "great" | 3 | Appreciate + Upsell opportunity |
| Urgent | "urgent", "ASAP", "deadline", multiple ! | 11 | Priority routing |

**Sentiment Detection Signals:**
- **Text-based:** Keyword matching ("frustrated", "angry", "love", "hate")
- **Punctuation:** Multiple exclamation marks (!!!), all caps (URGENT)
- **Emoji:** 😤 (anger), 😕 (confusion), 🙏 (pleading), 🎉 (happy)
- **Message Length:** Very short + abrupt = frustration; very long = detailed concern
- **Time References:** "deadline tomorrow", "needed yesterday" = urgency

**Sentiment Scoring System:**
```
Sentiment Score: -1.0 to +1.0
- -1.0 to -0.7: Angry (escalate immediately)
- -0.7 to -0.3: Frustrated (empathy + priority)
- -0.3 to +0.3: Neutral (standard handling)
- +0.3 to +0.7: Satisfied (maintain relationship)
- +0.7 to +1.0: Delighted (upsell/referral opportunity)
```

### 2.3 Escalation Points Analysis

**Discovery:** 10 escalation rules map to specific ticket patterns.

**Escalation Triggers Found in Sample:**

| Rule | Trigger Keywords Found | Sample Tickets | Escalation Rate |
|------|------------------------|----------------|-----------------|
| Pricing/Enterprise | "enterprise", "50+ users", "quote", "custom pricing" | TKT-001, TKT-055, TKT-035 | ~15% |
| Refund/Billing | "refund", "charged twice", "payment failed" | TKT-002, TKT-027, TKT-044 | ~12% |
| Legal/Compliance | "GDPR", "HIPAA", "SOC 2", "compliance" | TKT-004, TKT-009, TKT-045 | ~8% |
| Angry Customer | "unacceptable", "worst", "cancel immediately" | TKT-031, TKT-006 | ~5% |
| Technical Bug (System-wide) | "not working", "broken", "outage" | TKT-012, TKT-042, TKT-053 | ~18% |
| Data Loss/Security | "data lost", "hacked", "unauthorized" | TKT-060 | ~3% |
| VIP Customer | Enterprise tier, high ARR | TKT-001, TKT-009, TKT-055 | ~10% |
| API/Integration | "API", "webhook", "integration", "developer" | TKT-007, TKT-012, TKT-016 | ~10% |
| Cancellation | "cancel", "close account", "leaving" | TKT-011, TKT-037 | ~5% |
| Feature Request | "feature request", "roadmap", "when will" | TKT-003, TKT-048, TKT-050 | ~14% |

**Escalation Priority Matrix (from actual tickets):**

**P0 - Critical (15 min response):**
- TKT-009: HIPAA compliance (legal + enterprise)
- TKT-031: "urgent!! project deadline tomorrow"
- TKT-053: "Lost 2 hours of work" (data loss)

**P1 - High (1 hour response):**
- TKT-001: SSO integration blocking rollout (enterprise)
- TKT-002: Double charge (billing)
- TKT-006: Performance issues affecting operations
- TKT-055: Enterprise quote request (sales)

**P2 - Medium (4 hours response):**
- TKT-003: Feature request
- TKT-007: API rate limit question
- TKT-012: Webhook not working

**P3 - Low (24 hours response):**
- TKT-015: Template request
- TKT-025: Student discount question
- TKT-048: Language support inquiry

### 2.4 Response Style Requirements

**Discovery:** Response style must adapt to channel + category + sentiment.

**Response Style Matrix:**

| Channel | Category | Sentiment | Response Style |
|---------|----------|-----------|----------------|
| Email | Technical | Neutral | Detailed, step-by-step, screenshots |
| Email | Billing | Frustrated | Empathetic, clear timeline, reassurance |
| Email | Sales | Positive | Professional, value proposition, CTA |
| WhatsApp | How-to | Neutral | 1-3 steps, emoji, casual |
| WhatsApp | Bug | Angry | Empathy + urgency, emoji, quick update promise |
| WhatsApp | Billing | Urgent | Immediate action confirmation, timeline |
| Web Form | Technical | Neutral | Structured, browser-specific steps |
| Web Form | Legal | Formal | Precise language, documentation references |
| Web Form | Feature | Curious | Roadmap info, workaround suggestions |

**Response Length Guidelines:**
- **Email:** 150-300 words, multiple paragraphs, structured
- **WhatsApp:** 20-60 words, 1-3 sentences, emoji OK
- **Web Form:** 80-150 words, concise but complete

### 2.5 Context Switching Patterns

**Discovery:** Customers often switch channels mid-conversation.

**Observed Patterns:**
1. **WhatsApp → Email:** Quick question becomes complex technical issue
2. **Email → WhatsApp:** Formal complaint followed by urgent ping
3. **Web Form → Email:** Initial report followed by detailed technical info

**Requirements:**
- Unified conversation thread across channels
- Automatic channel preference detection
- Context preservation during channel switches
- Agent handoff notes visible in all channels

---

## 3. System Architecture - High-Level Plan

### 3.1 Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Customer Support AI Agent                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Channel    │  │   Channel    │  │   Channel    │      │
│  │   Ingestion  │  │   Ingestion  │  │   Ingestion  │      │
│  │   (Email)    │  │  (WhatsApp)  │  │  (Web Form)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│                  ┌────────▼────────┐                        │
│                  │  Normalization  │                        │
│                  │     Layer       │                        │
│                  └────────┬────────┘                        │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐              │
│         │                 │                 │               │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐      │
│  │  Intent &    │  │   Sentiment  │  │   Entity     │      │
│  │  Category    │  │   Analysis   │  │  Extraction  │      │
│  │  Classifier  │  │              │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│                  ┌────────▼────────┐                        │
│                  │   Escalation    │                        │
│                  │   Router        │                        │
│                  └────────┬────────┘                        │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐              │
│         │                 │                 │               │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐      │
│  │   AI Draft   │  │   Human      │  │   Knowledge  │      │
│  │   Generator  │  │   Handoff    │  │   Base       │      │
│  │              │  │              │  │   Search     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
1. TICKET INGESTION
   Email API → Raw Email → Parser → Structured Data
   WhatsApp API → Raw Message → Parser → Structured Data
   Web Form API → Form Data → Parser → Structured Data

2. NORMALIZATION
   All channels → Unified Ticket Schema
   {
     ticket_id, channel, customer_id, timestamp,
     subject, message, attachments[], metadata
   }

3. ANALYSIS PIPELINE
   a) Intent Classification (10 categories)
   b) Sentiment Analysis (-1.0 to +1.0)
   c) Entity Extraction (IDs, names, dates, amounts)
   d) Priority Scoring (P0-P3)
   e) Escalation Rule Matching (10 rules)

4. ROUTING DECISION
   IF escalation_required → Human Queue
   ELSE → AI Response Generator

5. RESPONSE GENERATION
   a) Retrieve context (customer history, KB articles)
   b) Select response template (channel × category × sentiment)
   c) Generate personalized response
   d) Apply brand voice guidelines
   e) Quality check

6. DELIVERY
   Send via original channel
   Log conversation
   Update customer profile
```

### 3.3 Technology Stack Recommendations

| Component | Technology Options |
|-----------|-------------------|
| Channel Ingestion | Twilio (WhatsApp), SendGrid/Mailgun (Email), Custom API (Web Form) |
| NLP/ML | Hugging Face Transformers, spaCy, custom fine-tuned model |
| Sentiment Analysis | VADER, TextBlob, or custom classifier |
| Intent Classification | Fine-tuned BERT/RoBERTa, or few-shot LLM |
| Response Generation | LLM (GPT-4, Claude, or open-source Llama) with RAG |
| Knowledge Base | Vector DB (Pinecone, Weaviate) + semantic search |
| Customer Profile | PostgreSQL or MongoDB |
| Message Queue | Redis/RabbitMQ for async processing |
| Escalation Routing | Rule engine (Drools) or custom logic |

### 3.4 Key Metrics to Track

**Operational Metrics:**
- Average Response Time (by channel, by category)
- First Contact Resolution Rate
- Escalation Rate (by category)
- Customer Satisfaction Score (CSAT)
- Agent Utilization Rate

**AI Performance Metrics:**
- Intent Classification Accuracy
- Sentiment Analysis Accuracy
- Response Quality Score (human review)
- False Positive Escalation Rate
- Response Draft Acceptance Rate

**Business Metrics:**
- Support Cost per Ticket
- Customer Retention Rate (post-support)
- Upsell Conversion Rate (from support interactions)
- VIP Customer Satisfaction

---

## 4. Implementation Priorities

### Phase 1: MVP (Week 1-2)
- [ ] Email ingestion and parsing
- [ ] Basic intent classification (10 categories)
- [ ] Simple sentiment analysis (positive/negative/neutral)
- [ ] Rule-based escalation routing (10 rules)
- [ ] Template-based response generation
- [ ] Single-channel (email) support

### Phase 2: Multi-Channel (Week 3-4)
- [ ] WhatsApp integration
- [ ] Web form integration
- [ ] Channel-specific response templates
- [ ] Customer profile unification
- [ ] Conversation history tracking

### Phase 3: Intelligence (Week 5-6)
- [ ] Advanced sentiment analysis (fine-grained scores)
- [ ] Entity extraction (transaction IDs, dates, amounts)
- [ ] Priority scoring algorithm
- [ ] Knowledge base integration
- [ ] Response quality scoring

### Phase 4: Optimization (Week 7-8)
- [ ] A/B testing for response templates
- [ ] Continuous learning from human corrections
- [ ] Analytics dashboard
- [ ] Performance optimization
- [ ] Scale testing

---

## 5. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Incorrect escalation | High customer dissatisfaction | Human review for P0/P1 escalations, feedback loop |
| Wrong response tone | Brand damage | Template validation, brand voice checker |
| Data privacy breach | Legal/compliance issues | PII detection, secure storage, access controls |
| AI hallucination | Incorrect information | RAG with verified KB, confidence thresholds |
| Channel integration failure | Customer frustration | Fallback to human agents, monitoring alerts |

---

## 6. Open Questions

1. **Customer Identity:** How to handle customers with multiple emails/phones?
2. **Language Support:** Sample shows international customers - need multi-language responses?
3. **Attachment Handling:** How to process screenshots/PDFs attached to emails?
4. **Human Handoff:** What's the exact workflow for escalating to human agents?
5. **Learning Loop:** How will human corrections feed back into model improvement?
6. **SLA Enforcement:** How to track and alert on SLA breaches?
7. **Quality Assurance:** What percentage of AI responses should be human-reviewed?

---

## 7. Appendix: Ticket Pattern Summary

### Email Ticket Patterns (20 tickets)
```
Pattern 1: Technical Integration Request
- Keywords: "integration", "API", "SSO", "SAML", "webhook"
- Structure: Problem → Technical details → Request for help
- Escalation: Rule 1 (Enterprise) or Rule 8 (API)
- Response: Detailed technical steps

Pattern 2: Billing Dispute
- Keywords: "charged", "refund", "transaction", "invoice"
- Structure: Issue → Transaction IDs → Refund request
- Escalation: Rule 2 (Refund)
- Response: Empathetic + timeline

Pattern 3: Feature Request
- Keywords: "feature request", "would be amazing", "roadmap"
- Structure: Current limitation → Desired feature → Use case
- Escalation: Rule 10 (Product Team)
- Response: Appreciative + realistic expectations
```

### WhatsApp Ticket Patterns (20 tickets)
```
Pattern 1: Quick How-to
- Format: "how do I [action]?"
- Response: 1-3 step instructions + emoji

Pattern 2: Urgent Problem
- Format: "urgent!! [problem] 😤"
- Response: Empathy + urgent action confirmation

Pattern 3: Casual Inquiry
- Format: "is there [feature]?"
- Response: Friendly + informative
```

### Web Form Ticket Patterns (20 tickets)
```
Pattern 1: Bug Report
- Format: Subject + technical details (browser, version)
- Response: Troubleshooting steps + request for more info

Pattern 2: Enterprise Request
- Format: Formal + business context + timeline
- Escalation: Rule 1 (Enterprise Sales)
- Response: Professional + sales handoff

Pattern 3: Compliance Question
- Format: Regulatory framework + specific requirements
- Escalation: Rule 3 (Legal)
- Response: Precise + documentation references
```

---

**End of Discovery Log**
