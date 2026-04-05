# Test Configuration and Fixtures
# Shared fixtures for all test suites

import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from httpx import AsyncClient
from datetime import datetime
import json

# Base URL for API tests
BASE_URL = "http://localhost:8000"


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(base_url=BASE_URL) as ac:
        yield ac


@pytest.fixture
def sample_customer() -> Dict[str, Any]:
    """Sample customer data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+1234567890",
        "subject": "Help with API authentication",
        "category": "technical",
        "message": "I'm having trouble authenticating with the API. Getting 401 errors."
    }


@pytest.fixture
def sample_email_ticket() -> Dict[str, Any]:
    """Sample email ticket for testing."""
    return {
        "channel": "email",
        "customer_email": "john@example.com",
        "customer_name": "John Doe",
        "subject": "Question about Kanban boards",
        "content": "How do I create a Kanban board in TechNova?",
        "received_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_whatsapp_message() -> Dict[str, Any]:
    """Sample WhatsApp message for testing."""
    return {
        "channel": "whatsapp",
        "customer_phone": "+1234567890",
        "customer_name": "Jane Smith",
        "content": "hey, how do I add someone to my project?",
        "received_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_webform_submission() -> Dict[str, Any]:
    """Sample web form submission for testing."""
    return {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "subject": "Billing inquiry",
        "category": "billing",
        "message": "I was charged twice this month. Can you help?"
    }


@pytest.fixture
def escalation_scenarios() -> Dict[str, str]:
    """Test scenarios that should trigger escalation."""
    return {
        "pricing_inquiry": "How much does Enterprise plan cost for 100 users?",
        "refund_request": "I want a refund for the duplicate charge",
        "legal_request": "I need to speak to your legal team about GDPR compliance",
        "angry_customer": "This is UNACCEPTABLE! Your service is TERRIBLE!",
        "security_breach": "I think my account was hacked and data is missing",
        "cancellation": "I want to cancel my subscription immediately"
    }


@pytest.fixture
def channel_response_limits() -> Dict[str, int]:
    """Response character/word limits by channel."""
    return {
        "email": 500,  # words
        "whatsapp": 300,  # characters
        "web_form": 300  # words
    }


@pytest.fixture
def test_tickets() -> list:
    """Load test tickets from sample-tickets.json."""
    import json
    from pathlib import Path
    
    tickets_file = Path(__file__).parent.parent / "context" / "sample-tickets.json"
    
    if not tickets_file.exists():
        return []
    
    with open(tickets_file, 'r') as f:
        data = json.load(f)
    
    return data.get("tickets", [])
