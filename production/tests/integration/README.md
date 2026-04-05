# Integration Tests

**Purpose:** Test component interactions and data flow

## Test Files to Create

### `test_ingestion_pipeline.py`
- Test email → normalized ticket flow
- Test WhatsApp → normalized ticket flow
- Test web form → normalized ticket flow
- Test attachment handling
- Test error scenarios (API failures)

### `test_analysis_pipeline.py`
- Test intent + sentiment + entity extraction chain
- Test priority scoring integration
- Test customer profile enrichment
- Test knowledge base retrieval

### `test_routing_pipeline.py`
- Test escalation rule evaluation
- Test AI vs human decision
- Test queue assignment
- Test SLA deadline calculation

### `test_generation_pipeline.py`
- Test end-to-end response generation
- Test template + RAG integration
- Test brand voice enforcement
- Test channel-specific formatting

### `test_full_pipeline.py`
- Test complete flow: Ingestion → Analysis → Routing → Generation
- Test conversation persistence
- Test metrics logging
- Test error handling & recovery

## Running Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run with docker (for DB dependencies)
docker-compose up -d db redis
pytest tests/integration/

# Run specific test
pytest tests/integration/test_full_pipeline.py
```

## Test Data
- Use 60-ticket discovery dataset
- Mock external APIs (Twilio, SendGrid, LLM)
- Use test database with seed data

## Performance Requirements
- End-to-end latency: < 2 seconds (P95)
- Memory usage: < 512MB per worker
- Concurrent ticket handling: 100 tickets/min
