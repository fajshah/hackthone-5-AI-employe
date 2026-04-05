# Production Module: Utils

**Purpose:** Shared utilities and helper functions

## Components

### `logging.py`
- Structured logging (JSON format)
- Log levels (DEBUG, INFO, WARN, ERROR)
- Correlation IDs for request tracing
- Log aggregation (ELK/Datadog)

### `metrics.py`
- Prometheus metrics export
- Custom metrics tracking
- Performance monitoring
- Alert thresholds

**Key Metrics:**
- `tickets_processed_total`
- `intent_classification_accuracy`
- `sentiment_analysis_accuracy`
- `escalation_rate`
- `response_time_seconds`
- `error_rate`

### `validators.py`
- Input validation
- Schema validation (Pydantic)
- Email/phone format validation
- Sanitization (XSS, injection prevention)

### `pii_handler.py`
- PII detection (email, phone, credit card)
- Redaction utilities
- Secure storage
- GDPR compliance helpers

### `retry.py`
- Retry logic with exponential backoff
- Circuit breaker pattern
- Timeout handling
- Fallback mechanisms

### `formatters.py`
- Date/time formatting
- Currency formatting
- Channel-specific text formatting
- HTML ↔ Markdown conversion

## Usage Example

```python
from utils.logging import get_logger
from utils.metrics import track_metric
from utils.validators import validate_ticket

logger = get_logger(__name__)

@track_metric('ticket_processing_time')
def process_ticket(ticket):
    logger.info(f"Processing ticket {ticket.id}")
    validate_ticket(ticket)
    # ... processing logic
```
