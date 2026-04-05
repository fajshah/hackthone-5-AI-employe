# TechNova Escalation Rules

## Overview
This document defines 10 clear escalation rules for customer support tickets. AI agents should automatically categorize and route tickets based on these rules. Human escalation is required when criteria are met.

---

## Rule 1: Pricing & Enterprise Sales Escalation
**Trigger:** Any inquiry about Enterprise pricing, custom contracts, volume discounts (50+ users), or contract negotiations.

**Keywords:** `enterprise`, `pricing`, `quote`, `contract`, `volume discount`, `50+ users`, `100+ users`, `custom pricing`, `negotiate`

**Action:** 
- Route to: Sales Team (Enterprise)
- SLA: Response within 4 business hours
- Include: Customer company size, current plan, user count in handoff notes

**Do NOT:** Provide custom pricing quotes as AI. Always escalate.

---

## Rule 2: Refund & Billing Disputes
**Trigger:** Refund requests, double charges, payment failures, billing discrepancies over $100.

**Keywords:** `refund`, `charged twice`, `billing error`, `payment failed`, `overcharged`, `dispute`, `chargeback`

**Action:**
- Route to: Billing Specialist
- SLA: Response within 2 business hours
- Include: Transaction IDs, amount in question, customer account tier

**Do NOT:** Promise refunds. Acknowledge and escalate immediately.

---

## Rule 3: Legal & Compliance Requests
**Trigger:** GDPR, HIPAA, SOC 2, data processing agreements, legal inquiries, compliance documentation.

**Keywords:** `GDPR`, `HIPAA`, `SOC 2`, `compliance`, `legal`, `BAA`, `data processing`, `audit`, `lawsuit`, `attorney`, `subpoena`

**Action:**
- Route to: Legal & Compliance Team
- SLA: Response within 1 business hour
- Include: Full ticket content, customer industry, urgency level

**Do NOT:** Provide any legal commitments or interpretations. Escalate immediately.

---

## Rule 4: Angry/Threatening Customers
**Trigger:** Aggressive language, threats to leave, threats of public negative reviews, profanity, all-caps messages.

**Keywords:** `cancel immediately`, `worst service`, `unacceptable`, `useless`, `threaten`, `lawyer`, `sue`, `review bomb`, `twitter`, `social media`

**Sentiment Indicators:**
- Anger score > 0.7 (if sentiment analysis available)
- Multiple exclamation marks (!!!)
- All caps words (URGENT, TERRIBLE)

**Action:**
- Route to: Senior Support Agent / Team Lead
- SLA: Response within 30 minutes
- Include: Sentiment analysis score, customer history, retention risk level

**Do NOT:** Be defensive. Acknowledge frustration, empathize, escalate with urgency.

---

## Rule 5: Technical Bugs Affecting Multiple Users
**Trigger:** Bug reports that may affect multiple customers (system-wide issues, outages, core feature failures).

**Keywords:** `not working`, `broken`, `outage`, `down`, `all users`, `everyone`, `system-wide`, `critical bug`

**Action:**
- Route to: Engineering Team (via PagerDuty if critical)
- SLA: Response within 15 minutes for critical, 2 hours for non-critical
- Include: Steps to reproduce, affected users count, workaround if any

**Do NOT:** Promise fix timelines. Acknowledge, gather details, escalate.

---

## Rule 6: Data Loss or Security Breach Concerns
**Trigger:** Reports of missing data, unauthorized access, suspected security breaches, account hijacking.

**Keywords:** `data lost`, `missing data`, `hacked`, `unauthorized access`, `security breach`, `account compromised`, `deleted permanently`

**Action:**
- Route to: Security Team + Engineering Lead
- SLA: Response within 15 minutes
- Include: Account ID, data affected, timeline of incident, IP addresses if available

**Do NOT:** Speculate on cause or scope. Treat as P0 incident. Escalate immediately.

---

## Rule 7: VIP Customer Issues
**Trigger:** Customers from Enterprise tier, high-value accounts (>$10k ARR), or publicly known companies.

**Identification:**
- Account tier = Enterprise
- ARR > $10,000
- Company in "VIP Accounts" list
- C-level executive contacts (CEO, CTO, CIO)

**Action:**
- Route to: Dedicated Account Manager + Senior Support
- SLA: Response within 1 hour
- Include: Account value, contract renewal date, issue priority

**Do NOT:** Handle as regular ticket. Flag as VIP in all communications.

---

## Rule 8: Integration & API Technical Support
**Trigger:** Complex API issues, custom integration requests, webhook failures, third-party tool connections.

**Keywords:** `API`, `webhook`, `integration`, `developer`, `custom code`, `REST`, `SDK`, `rate limit`, `authentication error`

**Action:**
- Route to: Developer Support / Integration Specialist
- SLA: Response within 4 business hours
- Include: API endpoint, error messages, code snippets, account tier

**Do NOT:** Debug complex code issues. Gather technical details and escalate.

---

## Rule 9: Account Cancellation & Retention
**Trigger:** Cancellation requests, especially from long-term customers or high-value accounts.

**Keywords:** `cancel`, `close account`, `stop subscription`, `leaving`, `switching to competitor`

**Action:**
- Route to: Retention Specialist
- SLA: Response within 2 business hours
- Include: Customer tenure, current plan, cancellation reason, retention offers available

**Do NOT:** Process cancellation immediately. Understand reason, offer alternatives, escalate.

---

## Rule 10: Feature Requests Requiring Product Team Input
**Trigger:** Complex feature requests, roadmap inquiries, requests that require engineering effort estimation.

**Keywords:** `feature request`, `roadmap`, `when will`, `add feature`, `suggestion`, `product idea`, `custom development`

**Action:**
- Route to: Product Management Team
- SLA: Response within 24 hours
- Include: Feature description, use case, customer segment, frequency of request

**Do NOT:** Commit to feature development. Acknowledge value, log in product board, escalate.

---

## Escalation Priority Matrix

| Priority | Response Time | Examples |
|----------|---------------|----------|
| P0 - Critical | 15 minutes | Security breach, system outage, data loss |
| P1 - High | 1 hour | VIP customer, angry customer, billing dispute |
| P2 - Medium | 4 hours | API issues, technical bugs, cancellation |
| P3 - Low | 24 hours | Feature requests, general inquiries |

---

## Escalation Handoff Template

When escalating, include:

```
**Customer:** [Name, Company, Account Tier]
**Issue Summary:** [2-3 sentence description]
**Category:** [Billing/Technical/Legal/etc.]
**Priority:** [P0/P1/P2/P3]
**Customer Sentiment:** [Calm/Frustrated/Angry]
**Actions Taken:** [What AI agent already tried]
**Relevant Details:** [Transaction IDs, error messages, etc.]
**Requested Resolution:** [What customer wants]
**SLA Deadline:** [When response is due]
```

---

## De-escalation Guidelines

Before escalating, AI agents should attempt:

1. **Acknowledge:** Validate customer's concern
2. **Empathize:** Show understanding of their situation
3. **Clarify:** Gather all necessary details
4. **Set Expectations:** Explain next steps and timeline
5. **Assure:** Confirm that appropriate team will handle

Example:
> "I understand how frustrating this must be, especially with your deadline approaching. Let me connect you with our [specialist team] who can resolve this quickly. They'll reach out within [SLA timeframe]. In the meantime, I've documented all the details you've shared."
