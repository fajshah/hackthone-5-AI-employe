# Production Module: Ingestion

**Purpose:** Multi-channel ticket ingestion and normalization

## Components

### `email_ingestion.py`
- SendGrid/Mailgun API integration
- Email parsing (headers, body, attachments)
- HTML to markdown conversion
- Attachment handling (OCR for images)

### `whatsapp_ingestion.py`
- Twilio API integration
- Message parsing (text, emoji, media)
- Session/thread management
- Rate limiting

### `webform_ingestion.py`
- Custom REST API endpoint
- Form validation
- Subject line extraction
- Browser/device metadata capture

### `normalizer.py`
- Unified ticket schema conversion
- Channel-specific field mapping
- Timestamp normalization (UTC)
- Customer identity resolution

## Input/Output

**Input:** Raw channel data (email, WhatsApp message, web form JSON)

**Output:** Normalized ticket object:
```python
{
    "ticket_id": "TKT-XXXXX",
    "channel": "email|whatsapp|webform",
    "customer_id": "CUST-XXXXX",
    "timestamp": "2026-04-01T10:30:00Z",
    "subject": "Issue summary",
    "message": "Customer message content",
    "attachments": [...],
    "metadata": {
        "email": "customer@example.com",
        "phone": "+1-555-XXXX",
        "company": "Company Name",
        "browser": "Chrome 122",
        "account_tier": "Enterprise"
    }
}
```

## Error Handling
- Retry logic for API failures
- Dead letter queue for unparseable messages
- Alerting on ingestion failures
