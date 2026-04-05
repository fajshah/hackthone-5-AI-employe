"""
TechNova Customer Support - Load Tests with Locust

Complete load testing suite for:
- Web form submissions
- API endpoints
- Multi-channel scenarios
- Stress testing
- Soak testing

Install: pip install locust
Run: locust -f tests/load_test.py --host=http://localhost:8000

Web UI: http://localhost:8089
"""

import random
import uuid
import json
import time
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_email():
    """Generate random email"""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "company.com", "corp.com"]
    return f"user.{uuid.uuid4().hex[:8]}@{random.choice(domains)}"


def generate_phone():
    """Generate random phone number"""
    return f"+1555{random.randint(1000000, 9999999)}"


def generate_name():
    """Generate random name"""
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Emma", "Chris", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Davis", "Miller"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def generate_company():
    """Generate random company"""
    companies = ["Tech Corp", "Innovation Inc", "Digital Solutions", "Cloud Systems", "Data Dynamics"]
    return random.choice(companies)


def generate_subject():
    """Generate random subject"""
    subjects = [
        "How to integrate with Slack?",
        "App keeps crashing",
        "Billing question",
        "Feature request",
        "Login issue",
        "Export not working",
        "Need help with setup",
        "Enterprise pricing inquiry",
        "GDPR compliance question",
        "Account cancellation"
    ]
    return f"{random.choice(subjects)} - {uuid.uuid4().hex[:6]}"


def generate_message():
    """Generate random message"""
    messages = [
        "Hi, I need help with this issue. Can you please assist?",
        "The application crashes whenever I try to export data. I've tried restarting but it still doesn't work.",
        "I was charged twice for my subscription! I want a refund immediately!",
        "Is TechNova GDPR compliant? We need to ensure data protection.",
        "We're interested in TechNova for our organization of 100+ users.",
        "This is unacceptable! I'm canceling my account immediately!",
        "Just wanted to say I love TechNova! It's amazing!",
        "How do I set up SSO integration with Okta?",
        "The mobile app is not syncing with the web version.",
        "Can you help me understand the pricing for enterprise plans?"
    ]
    return random.choice(messages)


# ============================================================================
# Base User Class
# ============================================================================

class BaseUser(HttpUser):
    """Base user class with common functionality"""
    
    abstract = True
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when user starts"""
        self.customer = {
            "email": generate_email(),
            "name": generate_name(),
            "phone": generate_phone(),
            "company": generate_company()
        }
        
        # Set default headers
        self.client.headers.update({
            "X-API-Key": "dev-api-key",
            "Content-Type": "application/json"
        })
    
    def log_request(self, name, success, response_time):
        """Log request details"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] {name} - {'✓' if success else '✗'} - {response_time:.0f}ms")


# ============================================================================
# Web Form User
# ============================================================================

class WebFormUser(BaseUser):
    """Simulates users submitting web forms"""
    
    wait_time = between(2, 5)
    
    @task(10)
    def submit_support_form(self):
        """Submit support form"""
        payload = {
            "email": self.customer["email"],
            "name": self.customer["name"],
            "company": self.customer["company"],
            "subject": generate_subject(),
            "message": generate_message()
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/support/submit",
            json=payload,
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 201:
                response.success()
                self.log_request("WebForm Submit", True, response_time)
            elif response.status_code == 429:
                response.failure("Rate limited")
                self.log_request("WebForm Submit (Rate Limited)", False, response_time)
            else:
                response.failure(f"Status {response.status_code}")
                self.log_request("WebForm Submit (Failed)", False, response_time)
    
    @task(3)
    def check_ticket_status(self):
        """Check ticket status"""
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        
        start_time = time.time()
        
        with self.client.get(
            f"/support/status/{ticket_id}",
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 404]:
                response.success()
                self.log_request("Check Status", True, response_time)
            else:
                response.failure(f"Status {response.status_code}")
                self.log_request("Check Status (Failed)", False, response_time)
    
    @task(1)
    def list_tickets(self):
        """List user tickets"""
        start_time = time.time()
        
        with self.client.get(
            f"/support/tickets?email={self.customer['email']}",
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
                self.log_request("List Tickets", True, response_time)
            else:
                response.failure(f"Status {response.status_code}")
                self.log_request("List Tickets (Failed)", False, response_time)


# ============================================================================
# Email Channel User
# ============================================================================

class EmailChannelUser(BaseUser):
    """Simulates email channel ingestion"""
    
    wait_time = between(3, 8)
    
    @task(10)
    def receive_email(self):
        """Simulate receiving email via Gmail webhook"""
        email_payload = {
            "message_id": f"<{uuid.uuid4().hex}@gmail.com>",
            "from": {
                "email": self.customer["email"],
                "name": self.customer["name"]
            },
            "to": [{"email": "support@technova.com"}],
            "subject": generate_subject(),
            "body_plain": generate_message(),
            "body_html": f"<p>{generate_message()}</p>",
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/webhooks/gmail",
            json=email_payload,
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
                self.log_request("Email Ingestion", True, response_time)
            else:
                response.failure(f"Status {response.status_code}")
                self.log_request("Email Ingestion (Failed)", False, response_time)
    
    @task(3)
    def receive_email_reply(self):
        """Simulate email reply (threading)"""
        original_id = f"<{uuid.uuid4().hex}@gmail.com>"
        
        email_payload = {
            "message_id": f"<{uuid.uuid4().hex}@gmail.com>",
            "in_reply_to": original_id,
            "from": {
                "email": self.customer["email"],
                "name": self.customer["name"]
            },
            "subject": f"Re: {generate_subject()}",
            "body_plain": "Following up on my previous inquiry"
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/webhooks/gmail",
            json=email_payload,
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
                self.log_request("Email Reply", True, response_time)
            else:
                response.failure(f"Status {response.status_code}")
                self.log_request("Email Reply (Failed)", False, response_time)


# ============================================================================
# WhatsApp Channel User
# ============================================================================

class WhatsAppChannelUser(BaseUser):
    """Simulates WhatsApp channel ingestion"""
    
    wait_time = between(1, 4)
    
    @task(10)
    def receive_whatsapp_message(self):
        """Simulate receiving WhatsApp message"""
        whatsapp_payload = {
            "MessageSid": f"MM{uuid.uuid4().hex}",
            "From": f"whatsapp:{self.customer['phone']}",
            "To": "whatsapp:+14155238886",
            "Body": generate_message()
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/webhooks/whatsapp",
            data=whatsapp_payload,
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
                self.log_request("WhatsApp Message", True, response_time)
            else:
                response.failure(f"Status {response.status_code}")
                self.log_request("WhatsApp Message (Failed)", False, response_time)
    
    @task(5)
    def receive_whatsapp_short(self):
        """Simulate short WhatsApp message"""
        short_messages = ["help!", "urgent!!", "thanks!", "how?", "issue"]
        
        whatsapp_payload = {
            "MessageSid": f"MM{uuid.uuid4().hex}",
            "From": f"whatsapp:{self.customer['phone']}",
            "To": "whatsapp:+14155238886",
            "Body": random.choice(short_messages)
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/webhooks/whatsapp",
            data=whatsapp_payload,
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
                self.log_request("WhatsApp Short", True, response_time)
            else:
                response.failure(f"Status {response.status_code}")
                self.log_request("WhatsApp Short (Failed)", False, response_time)


# ============================================================================
# API Health User
# ============================================================================

class HealthCheckUser(BaseUser):
    """Simulates health check requests"""
    
    wait_time = between(5, 10)
    
    @task(5)
    def check_health(self):
        """Check API health"""
        start_time = time.time()
        
        with self.client.get(
            "/health",
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)
    def check_metrics(self):
        """Check API metrics"""
        start_time = time.time()
        
        with self.client.get(
            "/metrics",
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)
    def check_docs(self):
        """Check API docs"""
        start_time = time.time()
        
        with self.client.get(
            "/docs",
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


# ============================================================================
# Stress Test User
# ============================================================================

class StressTestUser(BaseUser):
    """High-frequency user for stress testing"""
    
    wait_time = between(0.1, 0.5)
    
    @task
    def rapid_submit(self):
        """Rapid form submissions"""
        payload = {
            "email": generate_email(),
            "name": generate_name(),
            "subject": generate_subject(),
            "message": generate_message()
        }
        
        self.client.post("/support/submit", json=payload)


# ============================================================================
# Event Handlers
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("\n" + "=" * 80)
    print("LOCUST LOAD TEST STARTING")
    print("=" * 80)
    print(f"Target Host: {environment.host}")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("\n" + "=" * 80)
    print("LOCUST LOAD TEST COMPLETED")
    print("=" * 80)
    print(f"End Time: {datetime.now().isoformat()}")
    
    # Print statistics
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Failed Requests: {stats.total.num_failures}")
    print(f"Requests/sec: {stats.total.current_rps:.2f}")
    print(f"Average Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print("=" * 80 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called on each request"""
    if exception:
        print(f"[ERROR] {name}: {exception}")


# ============================================================================
# Test Scenarios
# ============================================================================

class Scenario_StandardLoad(BaseUser):
    """
    Standard load test scenario
    
    Mix of all user types simulating normal production traffic
    """
    wait_time = between(1, 3)
    
    tasks = {
        WebFormUser: 5,
        EmailChannelUser: 3,
        WhatsAppChannelUser: 2,
        HealthCheckUser: 1
    }


class Scenario_WebFormHeavy(BaseUser):
    """
    Web form heavy scenario
    
    Simulates high web form traffic (e.g., after product launch)
    """
    wait_time = between(1, 2)
    
    tasks = {
        WebFormUser: 10,
        EmailChannelUser: 1,
        WhatsAppChannelUser: 1
    }


class Scenario_EmailSpike(BaseUser):
    """
    Email spike scenario
    
    Simulates sudden email influx (e.g., system outage)
    """
    wait_time = between(0.5, 2)
    
    tasks = {
        EmailChannelUser: 10,
        WebFormUser: 2,
        WhatsAppChannelUser: 1
    }


class Scenario_WhatsAppSurge(BaseUser):
    """
    WhatsApp surge scenario
    
    Simulates high WhatsApp traffic (e.g., marketing campaign)
    """
    wait_time = between(0.5, 1.5)
    
    tasks = {
        WhatsAppChannelUser: 10,
        WebFormUser: 2,
        EmailChannelUser: 1
    }


# ============================================================================
# Configuration
# ============================================================================

# For distributed testing
if isinstance(events.runner, MasterRunner):
    print("Running as Locust Master")
elif isinstance(events.runner, WorkerRunner):
    print("Running as Locust Worker")


# Custom arguments
def add_custom_arguments(parser):
    """Add custom command line arguments"""
    parser.add_argument(
        "--scenario",
        type=str,
        default="standard",
        help="Test scenario: standard, webform-heavy, email-spike, whatsapp-surge"
    )


@events.init_command_line_parser.add_listener
def on_init_command_line_parser(parser, **kwargs):
    add_custom_arguments(parser)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import os
    os.system("locust -f tests/load_test.py --host=http://localhost:8000")
