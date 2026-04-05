# End-to-End Tests

**Purpose:** Test complete system with real external dependencies

## Test Scenarios

### `test_e2e_email_flow.py`
**Scenario:** Customer sends email → AI responds

1. Send test email via SendGrid
2. System ingests and processes
3. AI generates response
4. Response sent to customer
5. Conversation logged

**Assertions:**
- Email received within 5 seconds
- Intent correctly classified
- Response sent within 2 seconds
- Response matches brand voice
- Conversation stored in DB

### `test_e2e_whatsapp_flow.py`
**Scenario:** Customer sends WhatsApp message → AI responds

1. Send test WhatsApp message via Twilio
2. System ingests and processes
3. AI generates response
4. Response sent via WhatsApp
5. Session maintained

**Assertions:**
- Message received within 3 seconds
- Sentiment correctly analyzed
- Response format appropriate for WhatsApp
- Emoji handling correct
- Session continuity maintained

### `test_e2e_webform_flow.py`
**Scenario:** Customer submits web form → AI responds

1. POST to web form endpoint
2. System processes ticket
3. AI generates response
4. Email response sent
5. Ticket status updated

**Assertions:**
- Form validated correctly
- Subject line extracted
- Response addresses all questions
- Browser metadata captured

### `test_e2e_escalation_flow.py`
**Scenario:** Angry enterprise customer → Human escalation

1. Send email with angry sentiment + enterprise context
2. System detects escalation trigger
3. Ticket routed to human queue
4. Escalation summary generated
5. SLA timer started

**Assertions:**
- Escalation rule matched (ESC-001 or ESC-004)
- Priority set to P0/P1
- Target team assigned correctly
- Handoff summary complete
- SLA deadline calculated

### `test_e2e_channel_switch.py`
**Scenario:** Customer starts on WhatsApp → follows up via email

1. Initial WhatsApp message
2. AI responds
3. Same customer sends email
4. System links conversations
5. AI has full context

**Assertions:**
- Customer identity resolved
- Conversation threads merged
- Context preserved
- Response references prior interaction

## Running Tests

```bash
# Prerequisites
export TEST_MODE=true
export SENDGRID_TEST_KEY=xxx
export TWILIO_TEST_SID=xxx
export TWILIO_TEST_TOKEN=xxx

# Run all E2E tests
pytest tests/e2e/

# Run with live monitoring
pytest tests/e2e/ --live-logs

# Run specific scenario
pytest tests/e2e/test_e2e_escalation_flow.py
```

## Test Environment
- Separate test database
- Sandbox API keys (SendGrid, Twilio)
- Mock LLM (or test mode with cached responses)
- Clean state before each test

## Success Criteria
- All scenarios pass
- Response time < 2 seconds
- No data loss
- Correct escalation decisions
- Brand voice compliance > 90%
