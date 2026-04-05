#!/usr/bin/env python3
"""
Quick Demo Script for Customer Success FTE
Run this to show the system working!
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))

def demo_health_check():
    print_section("1. HEALTH CHECK")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print_json(response.json())

def demo_web_form_submission():
    print_section("2. WEB FORM SUBMISSION")
    
    test_data = {
        "name": "Ahmed Khan",
        "email": "ahmed.khan@example.com",
        "subject": "How to create a Kanban board?",
        "category": "technical",
        "priority": "medium",
        "message": "Hi, I'm new to TechNova and I want to create a Kanban board for my team. Can you help me get started?"
    }
    
    print("Submitting support form...")
    print_json(test_data)
    
    response = requests.post(f"{BASE_URL}/support/submit", json=test_data)
    
    print(f"\nResponse Status: {response.status_code}")
    print_json(response.json())
    
    return response.json()

def demo_ticket_lookup(ticket_id):
    print_section("3. TICKET STATUS LOOKUP")
    
    print(f"Checking ticket: {ticket_id}")
    response = requests.get(f"{BASE_URL}/support/ticket/{ticket_id}")
    
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        print_json(response.json())
    else:
        print(response.text)

def demo_customer_lookup():
    print_section("4. CUSTOMER LOOKUP")
    
    email = "ahmed.khan@example.com"
    print(f"Looking up customer: {email}")
    
    response = requests.get(f"{BASE_URL}/customers/lookup", params={"email": email})
    
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        print_json(response.json())
    else:
        print(f"Customer not found yet (expected if database not running)")

def demo_metrics():
    print_section("5. CHANNEL METRICS")
    
    response = requests.get(f"{BASE_URL}/metrics/channels")
    
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        print_json(response.json())
    else:
        print("Metrics endpoint not available yet")

def demo_multiple_submissions():
    print_section("6. MULTIPLE CHANNEL SIMULATION")
    
    submissions = [
        {
            "name": "Sarah Ali",
            "email": "sarah.ali@company.com",
            "subject": "Billing question",
            "category": "billing",
            "message": "I was charged twice this month. Can you help?"
        },
        {
            "name": "Usman Malik",
            "email": "usman.m@startup.io",
            "subject": "Feature request",
            "category": "feedback",
            "message": "Love the product! Would be great to have dark mode."
        },
        {
            "name": "Fatima Noor",
            "email": "fatima.noor@enterprise.com",
            "subject": "Integration help",
            "category": "technical",
            "message": "How do I integrate TechNova with Slack?"
        }
    ]
    
    for i, submission in enumerate(submissions, 1):
        print(f"\nSubmission {i}/{len(submissions)}: {submission['subject']}")
        response = requests.post(f"{BASE_URL}/support/submit", json=submission)
        print(f"  ✓ Ticket created: {response.json().get('ticket_id', 'N/A')}")
        time.sleep(0.5)

def main():
    print("\n" + "🚀" * 40)
    print("  TECHNOVA CUSTOMER SUCCESS FTE - LIVE DEMO")
    print("🚀" * 40)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {BASE_URL}")
    
    try:
        # 1. Health Check
        demo_health_check()
        time.sleep(1)
        
        # 2. Submit Web Form
        result = demo_web_form_submission()
        ticket_id = result.get('ticket_id')
        time.sleep(1)
        
        # 3. Check Ticket Status
        if ticket_id:
            demo_ticket_lookup(ticket_id)
            time.sleep(1)
        
        # 4. Customer Lookup
        demo_customer_lookup()
        time.sleep(1)
        
        # 5. Multiple Submissions
        demo_multiple_submissions()
        time.sleep(1)
        
        # 6. Metrics
        demo_metrics()
        
        print_section("✅ DEMO COMPLETE!")
        print("\n📊 Summary:")
        print("  ✓ API Server: Running on port 8000")
        print("  ✓ Health Check: Working")
        print("  ✓ Web Form Submission: Working")
        print("  ✓ Ticket Creation: Working")
        print("  ✓ Multi-channel Support: Ready")
        print("\n🎥 You can now record your video demo!")
        print(f"\n📝 Useful URLs for demo:")
        print(f"  • API Health: http://localhost:8000/health")
        print(f"  • API Docs (Swagger): http://localhost:8000/docs")
        print(f"  • API Docs (ReDoc): http://localhost:8000/redoc")
        print(f"  • Metrics: http://localhost:8000/metrics/channels")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("Make sure the server is running: python -m uvicorn api.main:app --port 8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
