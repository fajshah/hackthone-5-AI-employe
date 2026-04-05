# Benchmark Test Set (60 Tickets)

**Purpose:** Standardized test set for model evaluation

---

## Dataset Overview

| Channel | Count | Percentage |
|---------|-------|------------|
| Email | 20 | 33.3% |
| WhatsApp | 20 | 33.3% |
| Web Form | 20 | 33.3% |

---

## Ground Truth Labels

### Email Tickets (20)

| ID | Subject | Expected Intent | Expected Sentiment | Escalation Rule | Priority |
|----|---------|-----------------|-------------------|-----------------|----------|
| TKT-001 | SSO Integration for Enterprise | technical-integration | neutral (-0.1) | ESC-001 | P1 |
| TKT-002 | Double Charge on Credit Card | billing | frustrated (-0.6) | ESC-002 | P1 |
| TKT-003 | Feature Request: Custom Fields | feature-request | positive (+0.4) | ESC-010 | P3 |
| TKT-004 | GDPR Compliance Question | compliance | neutral (0.0) | ESC-003 | P0 |
| TKT-005 | Training Session Request | how-to | neutral (+0.1) | None | - |
| TKT-006 | Performance Issues | performance | frustrated (-0.5) | ESC-005 | P2 |
| TKT-007 | API Rate Limit Question | technical-integration | neutral (0.0) | ESC-008 | P2 |
| TKT-008 | Invoice Download Issue | billing | neutral (-0.2) | ESC-002 | P1 |
| TKT-009 | HIPAA Compliance for Healthcare | compliance | neutral (0.0) | ESC-003 | P0 |
| TKT-010 | Mobile App Bug | bug-report | frustrated (-0.4) | None | - |
| TKT-011 | Account Cancellation | cancellation | negative (-0.3) | ESC-009 | P1 |
| TKT-012 | Webhook Not Working | technical-integration | frustrated (-0.5) | ESC-008 | P2 |
| TKT-013 | Template Request | how-to | neutral (+0.2) | None | - |
| TKT-014 | Enterprise Pricing Inquiry | sales | neutral (+0.1) | ESC-001 | P1 |
| TKT-015 | Password Reset Issue | account | neutral (0.0) | None | - |
| TKT-016 | Custom Integration Question | technical-integration | neutral (+0.1) | ESC-008 | P2 |
| TKT-017 | Refund Status Check | billing | neutral (-0.1) | ESC-002 | P1 |
| TKT-018 | Dashboard Loading Slowly | performance | frustrated (-0.4) | ESC-005 | P2 |
| TKT-019 | Team Onboarding Help | how-to | positive (+0.3) | None | - |
| TKT-020 | SOC 2 Documentation Request | compliance | neutral (0.0) | ESC-003 | P0 |

### WhatsApp Tickets (20)

| ID | Message | Expected Intent | Expected Sentiment | Escalation Rule | Priority |
|----|---------|-----------------|-------------------|-----------------|----------|
| TKT-021 | "hey how do I add a member?" | how-to | neutral (0.0) | None | - |
| TKT-022 | "urgent!! app not working 😤" | bug-report | angry (-0.8) | ESC-004 | P0 |
| TKT-023 | "is there a mobile app?" | how-to | neutral (+0.1) | None | - |
| TKT-024 | "charged twice!! fix this" | billing | angry (-0.75) | ESC-002 | P1 |
| TKT-025 | "student discount available?" | sales | neutral (+0.2) | None | - |
| TKT-026 | "can u help with SSO setup?" | technical-integration | neutral (+0.1) | ESC-001 | P1 |
| TKT-027 | "refund not processed" | billing | frustrated (-0.5) | ESC-002 | P1 |
| TKT-028 | "love the new update! 🎉" | feature-request | positive (+0.9) | None | - |
| TKT-029 | "how to export data?" | how-to | neutral (0.0) | None | - |
| TKT-030 | "app crashing on startup" | bug-report | frustrated (-0.6) | None | - |
| TKT-031 | "urgent!! project deadline tomorrow" | performance | angry (-0.85) | ESC-004 | P0 |
| TKT-032 | "can I customize notifications?" | how-to | neutral (+0.1) | None | - |
| TKT-033 | "payment failed but money deducted" | billing | frustrated (-0.65) | ESC-002 | P1 |
| TKT-034 | "integration with Slack?" | technical-integration | neutral (+0.2) | ESC-008 | P2 |
| TKT-035 | "enterprise plan for 50 users" | sales | neutral (+0.1) | ESC-001 | P1 |
| TKT-036 | "forgot password, need help" | account | neutral (-0.1) | None | - |
| TKT-037 | "want to cancel my subscription" | cancellation | negative (-0.4) | ESC-009 | P1 |
| TKT-038 | "bug: can't save changes" | bug-report | frustrated (-0.5) | None | - |
| TKT-039 | "how to set up recurring tasks?" | how-to | neutral (+0.1) | None | - |
| TKT-040 | "THANK YOU!!! fixed my issue 🙏" | feature-request | positive (+0.95) | None | - |

### Web Form Tickets (20)

| ID | Subject | Message Summary | Expected Intent | Expected Sentiment | Escalation Rule | Priority |
|----|---------|-----------------|-----------------|-------------------|-----------------|----------|
| TKT-041 | "Feature Request: Dark Mode" | Request for dark theme | feature-request | neutral (+0.3) | ESC-010 | P3 |
| TKT-042 | "Bug: Export to CSV Not Working" | CSV export fails | bug-report | neutral (-0.2) | None | - |
| TKT-043 | "Enterprise Demo Request" | Request product demo | sales | neutral (+0.2) | ESC-001 | P1 |
| TKT-044 | "Duplicate Charge on Invoice" | Charged twice for subscription | billing | frustrated (-0.55) | ESC-002 | P1 |
| TKT-045 | "GDPR Data Export Request" | Request personal data export | compliance | neutral (0.0) | ESC-003 | P0 |
| TKT-046 | "Integration with Jira" | How to integrate with Jira | technical-integration | neutral (+0.1) | ESC-008 | P2 |
| TKT-047 | "Page Loading Very Slow" | Dashboard performance issue | performance | frustrated (-0.45) | ESC-005 | P2 |
| TKT-048 | "When Will Mobile App Launch?" | iOS app availability question | feature-request | neutral (+0.1) | ESC-010 | P3 |
| TKT-049 | "Cannot Login with SSO" | SSO authentication failing | technical-integration | frustrated (-0.5) | ESC-001 | P1 |
| TKT-050 | "Custom Field Feature Request" | Request custom field support | feature-request | neutral (+0.2) | ESC-010 | P3 |
| TKT-051 | "Browser Compatibility Issue" | Not working on Firefox | bug-report | neutral (-0.2) | None | - |
| TKT-052 | "Enterprise Pricing for 100 Users" | Quote request for large team | sales | neutral (+0.1) | ESC-001 | P1 |
| TKT-053 | "Lost 2 Hours of Work" | Data not saved, work lost | bug-report | angry (-0.8) | ESC-006 | P0 |
| TKT-054 | "How to Set Up Automated Workflows?" | Automation setup help | how-to | neutral (+0.1) | None | - |
| TKT-055 | "Custom Integration for CRM" | Need custom CRM integration | technical-integration | neutral (+0.1) | ESC-001 | P1 |
| TKT-056 | "Account Upgrade Question" | How to upgrade to Pro plan | account | neutral (+0.2) | None | - |
| TKT-057 | "Security Audit Documentation" | Request security documentation | compliance | neutral (0.0) | ESC-003 | P0 |
| TKT-058 | "Notification Settings Not Saving" | Settings reset after save | bug-report | frustrated (-0.4) | None | - |
| TKT-059 | "API Documentation Clarification" | Question about API endpoints | technical-integration | neutral (+0.1) | ESC-008 | P2 |
| TKT-060 | "Unauthorized Access Detected" | Suspicious login activity | compliance | angry (-0.7) | ESC-006 | P0 |

---

## Evaluation Metrics

### Intent Classification

```python
def evaluate_intent(predictions, ground_truth):
    from sklearn.metrics import accuracy_score, classification_report
    
    accuracy = accuracy_score(ground_truth, predictions)
    report = classification_report(ground_truth, predictions)
    
    return {
        'accuracy': accuracy,
        'report': report
    }
```

**Target:** > 90% accuracy

### Sentiment Analysis

```python
def evaluate_sentiment(predictions, ground_truth):
    from sklearn.metrics import mean_absolute_error, correlation
    
    mae = mean_absolute_error(ground_truth, predictions)
    corr = correlation(ground_truth, predictions)[0]
    
    # Also evaluate sentiment bucket accuracy
    buckets_gt = [bucketize(s) for s in ground_truth]
    buckets_pred = [bucketize(s) for s in predictions]
    bucket_accuracy = accuracy_score(buckets_gt, buckets_pred)
    
    return {
        'mae': mae,
        'correlation': corr,
        'bucket_accuracy': bucket_accuracy
    }
```

**Target:** 
- MAE < 0.2
- Correlation > 0.8
- Bucket accuracy > 85%

### Escalation Decision

```python
def evaluate_escalation(predictions, ground_truth):
    from sklearn.metrics import precision_score, recall_score, f1_score
    
    precision = precision_score(ground_truth, predictions)
    recall = recall_score(ground_truth, predictions)
    f1 = f1_score(ground_truth, predictions)
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }
```

**Target:**
- Precision > 90%
- Recall > 85%
- F1 > 0.87

---

## Running Evaluation

```bash
# Run full evaluation
python scripts/evaluate_model.py --test-set data/test-set/60-tickets.json

# Run specific metric
python scripts/evaluate_model.py --metric intent
python scripts/evaluate_model.py --metric sentiment
python scripts/evaluate_model.py --metric escalation

# Generate report
python scripts/evaluate_model.py --report html
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-01 | Initial test set from discovery phase |
