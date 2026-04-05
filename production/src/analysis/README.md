# Production Module: Analysis

**Purpose:** NLP analysis pipeline for intent, sentiment, and entity extraction

## Components

### `intent_classifier.py`
- 10-category intent classification
- Model: Fine-tuned BERT/RoBERTa or few-shot LLM
- Confidence scoring
- Multi-label support (fallback to highest confidence)

**Categories:**
1. technical-integration
2. billing
3. feature-request
4. bug-report
5. how-to
6. compliance
7. cancellation
8. sales
9. account
10. performance

### `sentiment_analyzer.py`
- Sentiment scoring: -1.0 to +1.0
- Emotion detection (anger, frustration, happiness)
- Urgency level classification
- Recommended tone selection

**Output:**
```python
{
    "sentiment": "frustrated",
    "score": -0.65,
    "confidence": 0.87,
    "urgency_level": "high",
    "emotions": {
        "frustration": 0.72,
        "anger": 0.45
    },
    "recommended_tone": "empathetic"
}
```

### `entity_extractor.py`
- Transaction ID extraction (TXN-XXXXXXX)
- Date/time recognition
- Monetary amount detection
- Product/feature name identification
- Customer info extraction (name, company, email)

### `priority_scorer.py`
- P0-P3 priority assignment
- Based on: sentiment + escalation rules + customer tier
- SLA deadline calculation

## Dependencies
- Hugging Face Transformers
- spaCy (NER)
- Custom training data from discovery phase

## Performance Targets
- Intent accuracy: > 90%
- Sentiment accuracy: > 85%
- Latency: < 500ms per ticket
