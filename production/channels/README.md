# Channel Handlers

Multi-channel customer support ingestion handlers.

## Files

### Python Handlers

| File | Purpose | Lines |
|------|---------|-------|
| `gmail_handler.py` | Gmail API + Pub/Sub | 450+ |
| `whatsapp_handler.py` | Twilio WhatsApp API | 500+ |
| `web_form_handler.py` | REST API for web forms | 400+ |
| `__init__.py` | Module exports | - |

### React Components

| File | Purpose | Lines |
|------|---------|-------|
| `SupportForm.jsx` | Complete support form | 450+ |
| `SupportForm.css` | Form styling | 400+ |

---

## Gmail Handler

### Features

- ✅ OAuth 2.0 authentication (service account)
- ✅ Real-time email notifications via Pub/Sub
- ✅ Email parsing (headers, body, attachments)
- ✅ Multi-part MIME handling
- ✅ Attachment download
- ✅ HTML to plain text conversion
- ✅ Threading support (In-Reply-To, References)

### Setup

```bash
# 1. Create GCP project and enable Gmail API
# 2. Create service account and download JSON key
# 3. Enable domain-wide delegation
# 4. Set environment variables
export GMAIL_SERVICE_ACCOUNT_FILE="credentials/gmail-service-account.json"
export GCP_PROJECT_ID="your-project-id"
export SUPPORT_EMAIL="support@yourdomain.com"
```

### Usage

```python
from channels import GmailHandler

# Option 1: Real-time with Pub/Sub
def process_email(email_data):
    print(f"From: {email_data['from']['email']}")
    print(f"Subject: {email_data['subject']}")

GmailHandler.start_pubsub_listener(process_email)

# Option 2: Polling (fallback)
GmailHandler.poll_emails(process_email, interval_seconds=60)

# Send email
GmailHandler.send_email(
    to="customer@example.com",
    subject="Re: Your request",
    body="Thank you for contacting us..."
)
```

---

## WhatsApp Handler

### Features

- ✅ Twilio WhatsApp Business API
- ✅ Webhook signature validation
- ✅ Message validation and sanitization
- ✅ Rate limiting (10 messages/minute)
- ✅ Session management
- ✅ Media attachment handling
- ✅ Phone number validation

### Setup

```bash
export TWILIO_ACCOUNT_SID="ACxxxx"
export TWILIO_AUTH_TOKEN="your-token"
export TWILIO_WHATSAPP_NUMBER="+14155238886"
export TWILIO_WEBHOOK_URL="https://your-domain.com/api/whatsapp/webhook"
```

### Usage

```python
from channels import WhatsAppHandler

# Run as Flask webhook app
from channels import create_whatsapp_webhook_app

app = create_whatsapp_webhook_app()
app.run(host="0.0.0.0", port=5000)

# Send message
result = WhatsAppHandler.send_message(
    to="+1234567890",
    body="Hello from TechNova!"
)

# Send with media
WhatsAppHandler.send_message(
    to="+1234567890",
    body="Here's your guide",
    media_url="https://example.com/guide.pdf",
    media_type="application/pdf"
)
```

---

## Web Form Handler

### Features

- ✅ REST API endpoint
- ✅ Form validation (email, subject, message)
- ✅ File upload with validation
- ✅ CSRF protection
- ✅ Rate limiting (5 submissions/hour)
- ✅ Browser/device detection
- ✅ Ticket auto-creation

### Setup

```bash
export UPLOAD_FOLDER="uploads/tickets"
export MAX_UPLOAD_SIZE=16777216  # 16MB
export CSRF_SECRET="change-me-in-production"
```

### Usage

```python
from channels import WebFormHandler, create_webform_app

# Run as Flask API
app = create_webform_app()
app.run(host="0.0.0.0", port=5001)

# Process submission
result = WebFormHandler.process_submission(
    data={
        "email": "customer@example.com",
        "subject": "Help needed",
        "message": "I need help with..."
    },
    files=request.files,
    user_agent=request.headers.get("User-Agent"),
    ip_address=request.remote_addr
)

if result["success"]:
    print(f"Ticket: {result['ticket_id']}")
```

---

## React Support Form

### Features

- ✅ Real-time validation
- ✅ File upload with preview
- ✅ Success screen with ticket ID
- ✅ Character counters
- ✅ Error handling
- ✅ Responsive design
- ✅ Dark mode support
- ✅ Accessible (WCAG 2.1)

### Usage

```jsx
import SupportForm from './channels/SupportForm';

function App() {
  const handleSubmit = (ticketId) => {
    console.log('Ticket created:', ticketId);
  };

  return (
    <SupportForm 
      onSubmit={handleSubmit}
      apiEndpoint="/api/webform/submit"
    />
  );
}
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onSubmit` | function | - | Callback with ticket ID |
| `apiEndpoint` | string | `/api/webform/submit` | API endpoint |
| `className` | string | `''` | Additional CSS class |

---

## API Endpoints

### Gmail

| Endpoint | Method | Purpose |
|----------|--------|---------|
| N/A (Pub/Sub) | - | Real-time email ingestion |

### WhatsApp

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/whatsapp/webhook` | POST | Incoming messages |
| `/api/whatsapp/health` | GET | Health check |

### Web Form

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/webform/submit` | POST | Submit form |
| `/api/webform/validate` | POST | Validate data |
| `/api/webform/status/:id` | GET | Ticket status |
| `/api/webform/health` | GET | Health check |

---

## Rate Limits

| Channel | Limit | Window |
|---------|-------|--------|
| Gmail (Pub/Sub) | Unlimited | - |
| Gmail (Polling) | 50 emails | per poll |
| WhatsApp | 10 messages | per minute |
| Web Form | 5 submissions | per hour |

---

## File Upload Limits

| Type | Max Size | Allowed Extensions |
|------|----------|-------------------|
| Documents | 16MB | PDF, DOC, DOCX, TXT |
| Images | 16MB | PNG, JPG, JPEG, GIF |
| Total | 5 files | per submission |

---

## Security

- ✅ OAuth 2.0 (Gmail)
- ✅ Webhook signature validation (WhatsApp)
- ✅ CSRF protection (Web Form)
- ✅ Input sanitization
- ✅ File type validation
- ✅ Rate limiting
- ✅ IP tracking
