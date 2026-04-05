# TechNova Customer Support - Testing Guide

Complete testing documentation with run commands for all test types.

## Quick Start

```bash
# Navigate to production directory
cd production

# Install test dependencies
pip install -r tests/requirements.txt
```

---

## Table of Contents

1. [Unit Tests](#unit-tests)
2. [Integration Tests](#integration-tests)
3. [E2E Tests](#e2e-tests)
4. [Load Tests](#load-tests)
5. [Performance Tests](#performance-tests)
6. [CI/CD Integration](#cicd-integration)

---

## Unit Tests

### Run All Unit Tests

```bash
# Basic run
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ -v --cov=agent --cov-report=html

# Parallel execution (faster)
pytest tests/unit/ -v -n auto

# Generate HTML report
pytest tests/unit/ -v --html=reports/unit-tests.html
```

### Run Specific Test Files

```bash
# Sentiment analysis tests
pytest tests/unit/test_sentiment.py -v

# Escalation tests
pytest tests/unit/test_escalation.py -v

# Response generator tests
pytest tests/unit/test_response_generator.py -v
```

### Run Specific Tests

```bash
# By test name
pytest tests/unit/test_sentiment.py::test_positive_sentiment -v

# By keyword
pytest tests/unit/ -k "positive" -v

# By marker
pytest tests/unit/ -m "critical" -v
```

---

## Integration Tests

### Prerequisites

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Or use existing services
# Ensure API is running on http://localhost:8000
```

### Run Integration Tests

```bash
# All integration tests
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ -v --cov=api --cov-report=xml

# With detailed output
pytest tests/integration/ -v -s --tb=long

# Stop on first failure
pytest tests/integration/ -v -x
```

### Specific Integration Tests

```bash
# Database tests
pytest tests/integration/test_database.py -v

# Kafka tests
pytest tests/integration/test_kafka.py -v

# Agent integration tests
pytest tests/integration/test_agent.py -v
```

---

## E2E Tests (Multi-Channel)

### Prerequisites

```bash
# Ensure API is running
python -m api.main

# Or use Docker
docker-compose up -d api
```

### Run E2E Tests

```bash
# All E2E tests
pytest tests/test_multichannel_e2e.py -v

# With detailed output
pytest tests/test_multichannel_e2e.py -v -s

# With coverage
pytest tests/test_multichannel_e2e.py -v --cov=api --cov=agent

# Generate HTML report
pytest tests/test_multichannel_e2e.py -v --html=reports/e2e-tests.html

# Parallel execution
pytest tests/test_multichannel_e2e.py -v -n 4
```

### Run Specific E2E Test Classes

```bash
# Health tests
pytest tests/test_multichannel_e2e.py::TestHealthAndStatus -v

# Web form tests
pytest tests/test_multichannel_e2e.py::TestWebFormChannel -v

# Email tests
pytest tests/test_multichannel_e2e.py::TestEmailChannel -v

# WhatsApp tests
pytest tests/test_multichannel_e2e.py::TestWhatsAppChannel -v

# Agent processing tests
pytest tests/test_multichannel_e2e.py::TestAgentProcessing -v

# Escalation tests
pytest tests/test_multichannel_e2e.py::TestEscalationScenarios -v

# Performance tests
pytest tests/test_multichannel_e2e.py::TestPerformance -v
```

### Run Specific E2E Tests

```bash
# Single test
pytest tests/test_multichannel_e2e.py::TestWebFormChannel::test_submit_web_form_valid -v

# Multiple tests by pattern
pytest tests/test_multichannel_e2e.py -k "web_form" -v

# Skip slow tests
pytest tests/test_multichannel_e2e.py -v -m "not slow"
```

---

## Load Tests (Locust)

### Install Locust

```bash
pip install locust
```

### Run Load Tests

```bash
# Start Locust web UI
locust -f tests/load_test.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Set number of users and spawn rate
# Click "Start swarming"
```

### Command Line Load Tests

```bash
# Headless mode (no UI)
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --stop-timeout 30

# With specific scenario
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 3m \
  --scenario standard

# Export results to CSV
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --csv=reports/load_test
```

### Load Test Scenarios

```bash
# Standard load (mixed traffic)
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --scenario standard

# Web form heavy (high web traffic)
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 200 \
  --spawn-rate 20 \
  --run-time 5m \
  --scenario webform-heavy

# Email spike (sudden email influx)
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 150 \
  --spawn-rate 30 \
  --run-time 5m \
  --scenario email-spike

# WhatsApp surge (high WhatsApp traffic)
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 200 \
  --spawn-rate 40 \
  --run-time 5m \
  --scenario whatsapp-surge
```

### Stress Testing

```bash
# Ramp up to 500 users
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 500 \
  --spawn-rate 50 \
  --run-time 10m

# Find breaking point
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 1000 \
  --spawn-rate 100 \
  --run-time 15m
```

### Soak Testing (Endurance)

```bash
# Long-running test (1 hour)
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 60m \
  --csv=reports/soak_test
```

---

## Performance Tests

### API Response Time Tests

```bash
# Test response times
pytest tests/test_multichannel_e2e.py::TestPerformance -v

# With detailed timing
pytest tests/test_multichannel_e2e.py::TestPerformance::test_response_time_under_2_seconds -v -s
```

### Concurrent Request Tests

```bash
# Test concurrency
pytest tests/test_multichannel_e2e.py::TestPerformance::test_concurrent_submissions -v -s
```

---

## Complete Test Suite

### Run All Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=html --cov-report=xml

# Parallel execution
pytest tests/ -v -n auto

# Generate comprehensive report
pytest tests/ -v \
  --cov=. \
  --cov-report=html:reports/coverage \
  --cov-report=xml:reports/coverage.xml \
  --html=reports/all-tests.html \
  --self-contained-html
```

### Test Phases

```bash
# Phase 1: Unit tests (fast)
pytest tests/unit/ -v --tb=short

# Phase 2: Integration tests (medium)
pytest tests/integration/ -v --tb=short

# Phase 3: E2E tests (slow)
pytest tests/test_multichannel_e2e.py -v --tb=short

# Phase 4: Load tests (very slow)
locust -f tests/load_test.py --headless --users 100 --spawn-rate 10 --run-time 5m
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      kafka:
        image: confluentinc/cp-kafka:7.5.0
        env:
          KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
        ports:
          - 9092:9092
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt
      
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=. --cov-report=xml
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
      
      - name: Run E2E tests
        run: pytest tests/test_multichannel_e2e.py -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Unit Tests') {
            steps {
                sh 'pytest tests/unit/ -v --cov=. --cov-report=xml'
            }
            post {
                always {
                    junit 'reports/unit-tests.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh 'pytest tests/integration/ -v'
            }
        }
        
        stage('E2E Tests') {
            steps {
                sh 'pytest tests/test_multichannel_e2e.py -v'
            }
        }
        
        stage('Load Tests') {
            steps {
                sh '''
                    locust -f tests/load_test.py \
                        --headless \
                        --users 100 \
                        --spawn-rate 10 \
                        --run-time 5m \
                        --csv=reports/load_test
                '''
            }
        }
    }
}
```

---

## Test Reports

### Generate Reports

```bash
# HTML report
pytest tests/ -v --html=reports/test-report.html --self-contained-html

# Allure report
pytest tests/ -v --alluredir=allure-results
allure serve allure-results

# Coverage report
pytest tests/ -v --cov=. --cov-report=html:reports/coverage
open reports/coverage/index.html
```

### View Reports

```bash
# Open HTML report
open reports/test-report.html

# Open coverage report
open reports/coverage/index.html

# View Allure report
allure open allure-results
```

---

## Troubleshooting

### Common Issues

**API not responding:**
```bash
# Check if API is running
curl http://localhost:8000/health

# Start API
python -m api.main
```

**Database connection failed:**
```bash
# Check PostgreSQL
docker-compose ps postgres

# View logs
docker-compose logs postgres
```

**Kafka connection failed:**
```bash
# Check Kafka
docker-compose ps kafka

# View topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

**Tests timing out:**
```bash
# Increase timeout
pytest tests/ -v --timeout=60

# Run tests in parallel
pytest tests/ -v -n auto
```

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Acceptable |
|--------|--------|------------|
| API Response Time | < 500ms | < 1000ms |
| 95th Percentile | < 1000ms | < 2000ms |
| Error Rate | < 0.1% | < 1% |
| Throughput | > 100 req/s | > 50 req/s |

### Run Benchmark

```bash
# Benchmark test
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m

# Check results
# - Average response time
# - 95th percentile
# - Requests per second
# - Failure rate
```

---

**Happy Testing!** 🚀
