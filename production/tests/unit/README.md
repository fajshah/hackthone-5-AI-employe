# Unit Tests

**Purpose:** Test individual components in isolation

## Test Files to Create

### `test_intent_classifier.py`
- Test classification accuracy on 60-ticket test set
- Test confidence scoring
- Test edge cases (ambiguous intent)
- Test multi-label scenarios

### `test_sentiment_analyzer.py`
- Test sentiment scoring accuracy
- Test emotion detection
- Test urgency classification
- Test emoji handling (WhatsApp)

### `test_escalation_engine.py`
- Test all 10 escalation rules
- Test priority assignment
- Test edge cases (multiple rules match)
- Test no-escalation scenarios

### `test_response_generator.py`
- Test template selection
- Test brand voice compliance
- Test channel-specific formatting
- Test variable substitution

### `test_customer_profile.py`
- Test identity resolution
- Test profile unification
- Test preference tracking
- Test history retrieval

### `test_pii_handler.py`
- Test PII detection
- Test redaction accuracy
- Test secure storage
- Test GDPR compliance

## Running Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_intent_classifier.py

# Run with verbose output
pytest tests/unit/ -v
```

## Coverage Target
- Minimum 80% code coverage
- Critical paths: 95% coverage (routing, escalation)
