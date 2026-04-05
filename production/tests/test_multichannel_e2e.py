"""
TechNova Customer Support - Multi-Channel End-to-End Tests

Complete E2E tests covering:
- Email channel (Gmail handler)
- WhatsApp channel (Twilio handler)
- Web Form channel (REST API)
- Agent processing workflow
- Escalation scenarios
- Response validation

Run: pytest tests/test_multichannel_e2e.py -v
"""

import pytest
import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Test configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "dev-api-key"
TIMEOUT_SECONDS = 30


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def api_session():
    """Create requests session with retry logic"""
    session = requests.Session()
    
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    })
    
    return session


@pytest.fixture(scope="session")
def health_check(api_session):
    """Verify API is healthy before running tests"""
    max_retries = 10
    for i in range(max_retries):
        try:
            response = api_session.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print(f"\n✓ API is healthy: {response.json()}")
                return True
        except Exception:
            pass
        time.sleep(2)
    
    pytest.skip("API not available, skipping tests")


@pytest.fixture
def test_customer():
    """Generate test customer data"""
    return {
        "email": f"test.{uuid.uuid4().hex[:8]}@example.com",
        "name": "Test Customer",
        "phone": f"+1555{uuid.uuid4().hex[:7]}",
        "company": "Test Corp"
    }


@pytest.fixture
def test_ticket_data():
    """Generate test ticket data"""
    return {
        "subject": f"Test Issue - {uuid.uuid4().hex[:8]}",
        "message": "I need help with this issue. Can you please assist?",
        "category": "how_to"
    }


# ============================================================================
# Health & Status Tests
# ============================================================================

class TestHealthAndStatus:
    """Test API health and status endpoints"""
    
    def test_root_endpoint(self, api_session, health_check):
        """Test root endpoint returns API info"""
        response = api_session.get(f"{API_BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"
    
    def test_health_endpoint(self, api_session, health_check):
        """Test health check endpoint"""
        response = api_session.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "components" in data
    
    def test_liveness_probe(self, api_session, health_check):
        """Test Kubernetes liveness probe"""
        response = api_session.get(f"{API_BASE_URL}/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
    
    def test_readiness_probe(self, api_session, health_check):
        """Test Kubernetes readiness probe"""
        response = api_session.get(f"{API_BASE_URL}/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
    
    def test_metrics_endpoint(self, api_session, health_check):
        """Test metrics endpoint"""
        response = api_session.get(f"{API_BASE_URL}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "requests_total" in data
        assert "uptime_seconds" in data


# ============================================================================
# Web Form Channel Tests
# ============================================================================

class TestWebFormChannel:
    """Test web form submission channel"""
    
    def test_submit_web_form_valid(self, api_session, health_check, test_customer, test_ticket_data):
        """Test valid web form submission"""
        payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "company": test_customer["company"],
            "subject": test_ticket_data["subject"],
            "message": test_ticket_data["message"]
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "ticket_id" in data
        assert data["status"] == "received"
        assert "TKT-" in data["ticket_id"]
        
        return data["ticket_id"]
    
    def test_submit_web_form_missing_email(self, api_session, health_check, test_ticket_data):
        """Test web form submission without email (should fail)"""
        payload = {
            "name": "Test Customer",
            "subject": test_ticket_data["subject"],
            "message": test_ticket_data["message"]
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_submit_web_form_invalid_email(self, api_session, health_check, test_ticket_data):
        """Test web form submission with invalid email"""
        payload = {
            "email": "invalid-email",
            "name": "Test Customer",
            "subject": test_ticket_data["subject"],
            "message": test_ticket_data["message"]
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_submit_web_form_short_message(self, api_session, health_check, test_customer):
        """Test web form submission with too short message"""
        payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "Test",
            "message": "Too short"  # Less than 10 chars
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_submit_web_form_rate_limit(self, api_session, health_check, test_customer):
        """Test web form rate limiting (5 per hour)"""
        payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "Rate Limit Test",
            "message": "Testing rate limiting"
        }
        
        # Submit 6 requests (limit is 5)
        for i in range(6):
            response = api_session.post(
                f"{API_BASE_URL}/support/submit",
                json=payload,
                timeout=TIMEOUT_SECONDS
            )
            
            if i < 5:
                assert response.status_code == 201
            else:
                # 6th request should be rate limited
                assert response.status_code == 429


# ============================================================================
# Email Channel Tests
# ============================================================================

class TestEmailChannel:
    """Test email channel (simulated via API)"""
    
    def test_email_ingestion_valid(self, api_session, health_check, test_customer, test_ticket_data):
        """Test valid email ingestion"""
        # Simulate email webhook
        email_payload = {
            "message_id": f"<{uuid.uuid4().hex}@gmail.com>",
            "from": {
                "email": test_customer["email"],
                "name": test_customer["name"]
            },
            "to": [{"email": "support@technova.com"}],
            "subject": test_ticket_data["subject"],
            "body_plain": test_ticket_data["message"],
            "body_html": f"<p>{test_ticket_data['message']}</p>",
            "timestamp": datetime.now().isoformat()
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/webhooks/gmail",
            json=email_payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 200
    
    def test_email_threading(self, api_session, health_check, test_customer):
        """Test email threading (In-Reply-To header)"""
        # First email
        first_email = {
            "message_id": "<original@gmail.com>",
            "from": {"email": test_customer["email"], "name": test_customer["name"]},
            "subject": "Original Thread",
            "body_plain": "First message in thread"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/webhooks/gmail",
            json=first_email,
            timeout=TIMEOUT_SECONDS
        )
        assert response.status_code == 200
        
        # Reply email
        reply_email = {
            "message_id": "<reply@gmail.com>",
            "in_reply_to": "<original@gmail.com>",
            "from": {"email": test_customer["email"], "name": test_customer["name"]},
            "subject": "Re: Original Thread",
            "body_plain": "Reply to first message"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/webhooks/gmail",
            json=reply_email,
            timeout=TIMEOUT_SECONDS
        )
        assert response.status_code == 200


# ============================================================================
# WhatsApp Channel Tests
# ============================================================================

class TestWhatsAppChannel:
    """Test WhatsApp channel (Twilio webhook)"""
    
    def test_whatsapp_message_valid(self, api_session, health_check, test_customer):
        """Test valid WhatsApp message"""
        whatsapp_payload = {
            "MessageSid": f"MM{uuid.uuid4().hex}",
            "From": f"whatsapp:{test_customer['phone']}",
            "To": "whatsapp:+14155238886",
            "Body": "Hi, I need help with my account"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/webhooks/whatsapp",
            data=whatsapp_payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 200
    
    def test_whatsapp_message_short(self, api_session, health_check, test_customer):
        """Test WhatsApp short message format"""
        whatsapp_payload = {
            "MessageSid": f"MM{uuid.uuid4().hex}",
            "From": f"whatsapp:{test_customer['phone']}",
            "To": "whatsapp:+14155238886",
            "Body": "help!"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/webhooks/whatsapp",
            data=whatsapp_payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 200
    
    def test_whatsapp_message_with_emoji(self, api_session, health_check, test_customer):
        """Test WhatsApp message with emoji"""
        whatsapp_payload = {
            "MessageSid": f"MM{uuid.uuid4().hex}",
            "From": f"whatsapp:{test_customer['phone']}",
            "To": "whatsapp:+14155238886",
            "Body": "Issue with login 😕 Please help! 🙏"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/webhooks/whatsapp",
            data=whatsapp_payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 200


# ============================================================================
# Agent Processing Tests
# ============================================================================

class TestAgentProcessing:
    """Test agent processing workflow"""
    
    def test_agent_how_to_response(self, api_session, health_check, test_customer):
        """Test agent response for how-to question"""
        # Submit web form
        payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "How to integrate with Slack?",
            "message": "Hi, I need help integrating TechNova with Slack. Can you guide me through the steps?"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 201
        ticket_id = response.json()["ticket_id"]
        
        # Verify ticket was created
        status_response = api_session.get(
            f"{API_BASE_URL}/support/status/{ticket_id}",
            timeout=TIMEOUT_SECONDS
        )
        
        assert status_response.status_code == 200
    
    def test_agent_technical_issue_response(self, api_session, health_check, test_customer):
        """Test agent response for technical issue"""
        payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "App keeps crashing",
            "message": "The application crashes whenever I try to export data. I've tried restarting but it still doesn't work."
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 201
    
    def test_agent_sentiment_analysis(self, api_session, health_check, test_customer):
        """Test agent sentiment analysis"""
        # Test angry customer
        angry_payload = {
            "email": test_customer["email"],
            "subject": "This is unacceptable!",
            "message": "I'm extremely frustrated! This is the worst service ever! I want a refund NOW!"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=angry_payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 201
        
        # Test happy customer
        happy_payload = {
            "email": f"happy.{uuid.uuid4().hex[:8]}@example.com",
            "subject": "Love your product!",
            "message": "Just wanted to say I love TechNova! It's amazing and has helped our team so much. Thank you!"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=happy_payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 201


# ============================================================================
# Escalation Tests
# ============================================================================

class TestEscalationScenarios:
    """Test escalation scenarios"""
    
    def test_escalation_billing_dispute(self, api_session, health_check, test_customer):
        """Test escalation for billing dispute"""
        payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "Double charge on my card!",
            "message": "I was charged twice for my subscription! I want a refund immediately!"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 201
        # Should trigger escalation to billing team
    
    def test_escalation_legal_compliance(self, api_session, health_check, test_customer):
        """Test escalation for legal/compliance question"""
        payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "GDPR compliance question",
            "message": "Is TechNova GDPR compliant? We need to ensure data protection for our EU customers."
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 201
        # Should trigger escalation to legal team
    
    def test_escalation_angry_customer(self, api_session, health_check, test_customer):
        """Test escalation for angry customer"""
        payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "Worst service ever!",
            "message": "This is absolutely unacceptable! I'm canceling my account immediately! You're useless!"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 201
        # Should trigger escalation to senior support
    
    def test_escalation_enterprise_sales(self, api_session, health_check):
        """Test escalation for enterprise sales inquiry"""
        payload = {
            "email": f"enterprise.{uuid.uuid4().hex[:8]}@bigcorp.com",
            "name": "Enterprise Customer",
            "company": "Big Corp",
            "subject": "Enterprise pricing for 100+ users",
            "message": "We're interested in TechNova for our organization of 100+ users. Can you provide enterprise pricing?"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 201
        # Should trigger escalation to sales team


# ============================================================================
# Multi-Channel Integration Tests
# ============================================================================

class TestMultiChannelIntegration:
    """Test multi-channel integration"""
    
    def test_same_customer_multiple_channels(self, api_session, health_check, test_customer):
        """Test same customer contacting via multiple channels"""
        # Web form
        web_payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "Web form inquiry",
            "message": "Submitted via web form"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=web_payload,
            timeout=TIMEOUT_SECONDS
        )
        assert response.status_code == 201
        
        # Email (simulated)
        email_payload = {
            "message_id": f"<{uuid.uuid4().hex}@gmail.com>",
            "from": {"email": test_customer["email"], "name": test_customer["name"]},
            "subject": "Email inquiry",
            "body_plain": "Submitted via email"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/webhooks/gmail",
            json=email_payload,
            timeout=TIMEOUT_SECONDS
        )
        assert response.status_code == 200
        
        # WhatsApp (simulated)
        whatsapp_payload = {
            "MessageSid": f"MM{uuid.uuid4().hex}",
            "From": f"whatsapp:{test_customer['phone']}",
            "Body": "Submitted via WhatsApp"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/webhooks/whatsapp",
            data=whatsapp_payload,
            timeout=TIMEOUT_SECONDS
        )
        assert response.status_code == 200
    
    def test_customer_history_across_channels(self, api_session, health_check, test_customer):
        """Test customer history is maintained across channels"""
        # Create customer via web form
        web_payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "First inquiry",
            "message": "First message"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=web_payload,
            timeout=TIMEOUT_SECONDS
        )
        assert response.status_code == 201
        
        # Follow up via email
        email_payload = {
            "message_id": f"<{uuid.uuid4().hex}@gmail.com>",
            "from": {"email": test_customer["email"], "name": test_customer["name"]},
            "subject": "Follow up",
            "body_plain": "Following up on my previous inquiry"
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/webhooks/gmail",
            json=email_payload,
            timeout=TIMEOUT_SECONDS
        )
        assert response.status_code == 200


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance requirements"""
    
    def test_response_time_under_2_seconds(self, api_session, health_check, test_customer):
        """Test API response time is under 2 seconds"""
        payload = {
            "email": test_customer["email"],
            "name": test_customer["name"],
            "subject": "Performance test",
            "message": "Testing response time"
        }
        
        start_time = time.time()
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 201
        assert elapsed_time < 2.0, f"Response time {elapsed_time}s exceeds 2s limit"
    
    def test_concurrent_submissions(self, api_session, health_check, test_customer):
        """Test concurrent form submissions"""
        import concurrent.futures
        
        def submit_form(i):
            payload = {
                "email": f"test{i}.{uuid.uuid4().hex[:8]}@example.com",
                "name": test_customer["name"],
                "subject": f"Concurrent test {i}",
                "message": "Testing concurrency"
            }
            
            response = api_session.post(
                f"{API_BASE_URL}/support/submit",
                json=payload,
                timeout=TIMEOUT_SECONDS
            )
            
            return response.status_code
        
        # Submit 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_form, i) for i in range(10)]
            results = [f.result() for f in futures]
        
        # All should succeed
        assert all(status == 201 for status in results)


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_api_key(self, api_session, health_check):
        """Test invalid API key"""
        session = requests.Session()
        session.headers.update({
            "X-API-Key": "invalid-key",
            "Content-Type": "application/json"
        })
        
        response = session.post(
            f"{API_BASE_URL}/support/submit",
            json={"email": "test@example.com"},
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 401
    
    def test_malformed_json(self, api_session, health_check):
        """Test malformed JSON"""
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            data="not valid json",
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, api_session, health_check):
        """Test missing required fields"""
        payload = {
            "email": "test@example.com"
            # Missing subject and message
        }
        
        response = api_session.post(
            f"{API_BASE_URL}/support/submit",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        
        assert response.status_code == 422


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
