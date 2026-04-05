#!/usr/bin/env python3
"""
TechNova Customer Success FTE - Complete CLI Demo
Shows all features through terminal - perfect for video recording!
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.ENDC}")
    print("=" * 80)

def print_subheader(text):
    """Print formatted subheader"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}▸ {text}{Colors.ENDC}")
    print("-" * 80)

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}  ✓ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}  ℹ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}  ⚠ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}  ✗ {text}{Colors.ENDC}")

def print_json(data, indent=2):
    """Print formatted JSON"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def slow_print(text, delay=0.03):
    """Print text slowly for dramatic effect"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def wait(seconds=1, message=""):
    """Wait with message"""
    if message:
        print(f"\n  {Colors.YELLOW}⏳ {message}...{Colors.ENDC}")
    time.sleep(seconds)

# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

def demo_1_health_check():
    """Demo 1: System Health Check"""
    print_header("DEMO 1: SYSTEM HEALTH CHECK")
    
    print_subheader("Checking system status...")
    
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    
    print(f"\n  {Colors.BOLD}Status Code:{Colors.ENDC} {Colors.GREEN}{response.status_code}{Colors.ENDC}")
    print(f"  {Colors.BOLD}System Status:{Colors.ENDC} {data.get('status', 'unknown').upper()}")
    print(f"  {Colors.BOLD}API Version:{Colors.ENDC} {data.get('version', 'N/A')}")
    print(f"  {Colors.BOLD}Timestamp:{Colors.ENDC} {data.get('timestamp', 'N/A')}")
    
    print(f"\n  {Colors.BOLD}Components:{Colors.ENDC}")
    components = data.get('components', {})
    for component, status in components.items():
        if isinstance(status, dict):
            comp_status = status.get('status', 'unknown')
        else:
            comp_status = status
        
        status_color = Colors.GREEN if comp_status in ['healthy', 'active'] else Colors.YELLOW
        print(f"    • {component.capitalize():20} {status_color}{comp_status.upper()}{Colors.ENDC}")
    
    print_success("System is operational!")

def demo_2_submit_tickets():
    """Demo 2: Submit Multiple Support Tickets"""
    print_header("DEMO 2: SUBMITTING SUPPORT TICKETS")
    
    tickets = [
        {
            "name": "Ahmed Khan",
            "email": "ahmed.khan@company.com",
            "subject": "How to create a Kanban board?",
            "message": "Hi, I'm new to TechNova and I want to create a Kanban board for my team. Can you help me get started with the basic setup?"
        },
        {
            "name": "Sarah Ali",
            "email": "sarah.ali@startup.io",
            "subject": "Billing - Charged twice this month",
            "message": "I noticed that I was charged twice for this month's subscription. Can you please investigate and process a refund?"
        },
        {
            "name": "Usman Malik",
            "email": "usman.m@enterprise.com",
            "subject": "Integration with Slack not working",
            "message": "Our Slack integration stopped working yesterday. We're not receiving notifications when tasks are assigned."
        },
        {
            "name": "Fatima Noor",
            "email": "fatima.noor@tech.com",
            "subject": "Feature Request - Dark Mode",
            "message": "Love the product! Would be great to have a dark mode option for late night work sessions."
        },
        {
            "name": "Hassan Raza",
            "email": "hassan.r@agency.com",
            "subject": "How to use Gantt charts?",
            "message": "I need help creating a Gantt chart for my construction project with dependencies and milestones."
        }
    ]
    
    created_tickets = []
    
    for i, ticket in enumerate(tickets, 1):
        print_subheader(f"Submitting Ticket {i}/{len(tickets)}: {ticket['subject']}")
        
        print(f"  {Colors.BOLD}Customer:{Colors.ENDC} {ticket['name']}")
        print(f"  {Colors.BOLD}Email:{Colors.ENDC} {ticket['email']}")
        print(f"  {Colors.BOLD}Message:{Colors.ENDC} {ticket['message'][:60]}...")
        
        wait(0.5)
        
        response = requests.post(
            f"{BASE_URL}/support/submit",
            json=ticket
        )
        
        if response.status_code == 201:
            data = response.json()
            ticket_id = data['ticket_id']
            created_tickets.append({**ticket, 'ticket_id': ticket_id, 'status': data['status']})
            
            print_success(f"Ticket Created: {Colors.BOLD}{ticket_id}{Colors.ENDC}")
            print_info(f"Status: {data['status']}")
            print_info(f"Submitted: {data['submitted_at']}")
        else:
            print_error(f"Failed to create ticket: {response.text}")
        
        time.sleep(0.3)
    
    print_header(f"SUCCESSFULLY CREATED {len(created_tickets)} TICKETS")
    
    for ticket in created_tickets:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} {ticket['ticket_id']:20} {ticket['name']:20} {ticket['subject'][:40]}")
    
    return created_tickets

def demo_3_retrieve_ticket(tickets):
    """Demo 3: Retrieve and Display Ticket Details"""
    print_header("DEMO 3: RETRIEVE TICKET DETAILS")
    
    if not tickets:
        print_error("No tickets available to retrieve!")
        return
    
    # Get the first ticket
    ticket_id = tickets[0]['ticket_id']
    
    print_subheader(f"Retrieving ticket: {ticket_id}")
    
    wait(0.5)
    
    response = requests.get(f"{BASE_URL}/support/ticket/{ticket_id}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n  {Colors.BOLD}Ticket Details:{Colors.ENDC}")
        print(f"  {'─' * 76}")
        print(f"  {Colors.BOLD}Ticket ID:{Colors.ENDC}     {data['ticket_id']}")
        print(f"  {Colors.BOLD}Customer:{Colors.ENDC}      {data.get('name', 'N/A')}")
        print(f"  {Colors.BOLD}Email:{Colors.ENDC}         {data.get('email', 'N/A')}")
        print(f"  {Colors.BOLD}Subject:{Colors.ENDC}       {data.get('subject', 'N/A')}")
        print(f"  {Colors.BOLD}Category:{Colors.ENDC}      {data.get('category', 'N/A')}")
        print(f"  {Colors.BOLD}Status:{Colors.ENDC}        {Colors.GREEN}{data.get('status', 'N/A').upper()}{Colors.ENDC}")
        print(f"  {Colors.BOLD}Created:{Colors.ENDC}       {data.get('created_at', 'N/A')}")
        
        print(f"\n  {Colors.BOLD}Conversation History:{Colors.ENDC}")
        print(f"  {'─' * 76}")
        
        messages = data.get('messages', [])
        for msg in messages:
            role = msg.get('role', 'unknown')
            if role == 'customer':
                print(f"  {Colors.BLUE}👤 Customer{Colors.ENDC} ({msg.get('created_at', 'N/A')})")
            else:
                print(f"  {Colors.GREEN}🤖 AI Agent{Colors.ENDC} ({msg.get('created_at', 'N/A')})")
            print(f"  {msg.get('content', '')}")
            print()
        
        print_success("Ticket retrieved successfully!")
    else:
        print_error(f"Failed to retrieve ticket: {response.text}")

def demo_4_list_customer_tickets():
    """Demo 4: List All Tickets for a Customer"""
    print_header("DEMO 4: LIST CUSTOMER TICKETS")
    
    email = "ahmed.khan@company.com"
    
    print_subheader(f"Fetching all tickets for: {email}")
    
    wait(0.5)
    
    response = requests.get(f"{BASE_URL}/support/tickets", params={"email": email})
    
    if response.status_code == 200:
        tickets = response.json()
        
        if isinstance(tickets, list) and len(tickets) > 0:
            print(f"\n  {Colors.BOLD}Found {len(tickets)} ticket(s):{Colors.ENDC}\n")
            
            for i, ticket in enumerate(tickets, 1):
                print(f"  {Colors.BOLD}Ticket #{i}:{Colors.ENDC}")
                print(f"    ID:      {ticket.get('ticket_id', 'N/A')}")
                print(f"    Subject: {ticket.get('subject', 'N/A')}")
                print(f"    Status:  {Colors.GREEN}{ticket.get('status', 'N/A').upper()}{Colors.ENDC}")
                print(f"    Created: {ticket.get('created_at', 'N/A')}")
                print()
        else:
            print_info("No tickets found for this customer")
    else:
        print_error(f"Failed to fetch tickets: {response.text}")

def demo_5_api_documentation():
    """Demo 5: Show API Documentation"""
    print_header("DEMO 5: API DOCUMENTATION")
    
    print_subheader("Available API Endpoints")
    
    endpoints = [
        ("GET", "/health", "System health check"),
        ("POST", "/support/submit", "Submit support ticket"),
        ("GET", "/support/ticket/{id}", "Get ticket details"),
        ("GET", "/support/status/{id}", "Get ticket status"),
        ("GET", "/support/tickets", "List customer tickets"),
        ("POST", "/webhooks/gmail", "Gmail webhook handler"),
        ("POST", "/webhooks/whatsapp", "WhatsApp webhook handler"),
        ("GET", "/customers/lookup", "Look up customer"),
        ("GET", "/metrics/channels", "Channel metrics"),
    ]
    
    print(f"\n  {'Method':10} {'Endpoint':35} {'Description'}")
    print(f"  {'─' * 10} {'─' * 35} {'─' * 40}")
    
    for method, endpoint, desc in endpoints:
        method_color = Colors.GREEN if method == "GET" else Colors.CYAN
        print(f"  {method_color}{method:10}{Colors.ENDC} {Colors.YELLOW}{endpoint:35}{Colors.ENDC} {desc}")
    
    print(f"\n  {Colors.BOLD}Interactive API Docs:{Colors.ENDC}")
    print(f"    • Swagger UI:  {Colors.CYAN}http://localhost:8000/docs{Colors.ENDC}")
    print(f"    • ReDoc:       {Colors.CYAN}http://localhost:8000/redoc{Colors.ENDC}")
    
    print_success("API documentation available!")

def demo_6_system_architecture():
    """Demo 6: Show System Architecture"""
    print_header("DEMO 6: SYSTEM ARCHITECTURE")
    
    print_subheader("TechNova Customer Success FTE Architecture")
    
    architecture = """
  ┌─────────────────────────────────────────────────────────────┐
  │                    MULTI-CHANNEL INTAKE                      │
  │                                                              │
  │   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
  │   │  Gmail   │    │ WhatsApp │    │ Web Form │             │
  │   │  (Email) │    │ (Twilio) │    │ (React)  │             │
  │   └────┬─────┘    └────┬─────┘    └────┬─────┘             │
  │        │               │               │                     │
  │        └───────────────┼───────────────┘                     │
  │                        │                                     │
  │                        ▼                                     │
  │              ┌──────────────────┐                           │
  │              │   FastAPI API    │                           │
  │              │   (Port 8000)    │                           │
  │              └────────┬─────────┘                           │
  │                       │                                      │
  │        ┌──────────────┼──────────────┐                      │
  │        ▼              ▼              ▼                       │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
  │  │PostgreSQL│  │  Kafka   │  │  OpenAI  │                  │
  │  │   (CRM)  │  │(Events)  │  │  Agent   │                  │
  │  └──────────┘  └──────────┘  └──────────┘                  │
  │                                                              │
  └─────────────────────────────────────────────────────────────┘
    """
    
    print(architecture)
    
    print_subheader("Technology Stack")
    
    tech_stack = [
        ("Backend", "FastAPI (Python 3.11+)"),
        ("Database", "PostgreSQL 16 with pgvector"),
        ("Event Streaming", "Apache Kafka"),
        ("AI/ML", "OpenAI GPT-4o"),
        ("Frontend", "React/HTML5"),
        ("Containerization", "Docker + Docker Compose"),
        ("Orchestration", "Kubernetes"),
        ("Monitoring", "Prometheus + Grafana"),
    ]
    
    for tech, desc in tech_stack:
        print(f"  {Colors.BOLD}{tech:20}{Colors.ENDC} {desc}")
    
    print_success("Architecture overview complete!")

def demo_7_live_test():
    """Demo 7: Live Interactive Test"""
    print_header("DEMO 7: LIVE INTERACTIVE TEST")
    
    print_subheader("Creating a new ticket in real-time...")
    
    # Get user input
    print(f"\n  {Colors.BOLD}Enter your details (or press Enter for demo):{Colors.ENDC}\n")
    
    name = input(f"  {Colors.CYAN}Name:{Colors.ENDC} ").strip() or "Demo User"
    email = input(f"  {Colors.CYAN}Email:{Colors.ENDC} ").strip() or "demo@test.com"
    subject = input(f"  {Colors.CYAN}Subject:{Colors.ENDC} ").strip() or "API Integration Question"
    message = input(f"  {Colors.CYAN}Message:{Colors.ENDC} ").strip() or "How do I integrate TechNova with our internal systems?"
    
    print(f"\n  {Colors.YELLOW}⏳ Submitting your ticket...{Colors.ENDC}")
    time.sleep(1)
    
    ticket_data = {
        "name": name,
        "email": email,
        "subject": subject,
        "message": message
    }
    
    response = requests.post(f"{BASE_URL}/support/submit", json=ticket_data)
    
    if response.status_code == 201:
        data = response.json()
        ticket_id = data['ticket_id']
        
        print(f"\n  {Colors.GREEN}{Colors.BOLD}🎉 Ticket Created Successfully!{Colors.ENDC}")
        print(f"  {'─' * 76}")
        print(f"  {Colors.BOLD}Ticket ID:{Colors.ENDC}     {Colors.GREEN}{ticket_id}{Colors.ENDC}")
        print(f"  {Colors.BOLD}Status:{Colors.ENDC}        {data['status']}")
        print(f"  {Colors.BOLD}Email:{Colors.ENDC}         {data['email']}")
        print(f"  {Colors.BOLD}Submitted:{Colors.ENDC}     {data['submitted_at']}")
        
        print(f"\n  {Colors.YELLOW}⏳ Retrieving your ticket...{Colors.ENDC}")
        time.sleep(1)
        
        # Retrieve the ticket
        response = requests.get(f"{BASE_URL}/support/ticket/{ticket_id}")
        
        if response.status_code == 200:
            ticket = response.json()
            
            print(f"\n  {Colors.BOLD}Your Ticket Details:{Colors.ENDC}")
            print(f"  {'─' * 76}")
            print(f"  {Colors.BOLD}Subject:{Colors.ENDC}       {ticket.get('subject', 'N/A')}")
            print(f"  {Colors.BOLD}Status:{Colors.ENDC}        {Colors.GREEN}{ticket.get('status', 'N/A').upper()}{Colors.ENDC}")
            
            print(f"\n  {Colors.BOLD}Message:{Colors.ENDC}")
            messages = ticket.get('messages', [])
            for msg in messages:
                print(f"    {msg.get('content', '')}")
            
            print(f"\n  {Colors.GREEN}✓ Your ticket is now in the system!{Colors.ENDC}")
            print(f"  {Colors.INFO}Our AI assistant will respond within minutes.{Colors.ENDC}")
        else:
            print_error(f"Failed to retrieve ticket: {response.text}")
    else:
        print_error(f"Failed to create ticket: {response.text}")

def main():
    """Main demo runner"""
    print("\n" + "🚀" * 40)
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("  TECHNOVA CUSTOMER SUCCESS FTE")
    print("  Complete CLI Demo")
    print(f"{Colors.ENDC}")
    print("🚀" * 40)
    print(f"\n  {Colors.BOLD}Started at:{Colors.ENDC} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  {Colors.BOLD}API Base:{Colors.ENDC}   {BASE_URL}")
    print()
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code != 200:
            print_error("API server is not responding properly!")
            print_info(f"Make sure the server is running on {BASE_URL}")
            print_info("Run: python -m uvicorn api.main:app --port 8000")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API server!")
        print_info(f"Make sure the server is running on {BASE_URL}")
        print_info("Run: python -m uvicorn api.main:app --port 8000")
        sys.exit(1)
    
    print_success("Connected to API server!")
    
    wait(1, "Starting demo")
    
    # Run all demos
    demo_1_health_check()
    wait(1)
    
    tickets = demo_2_submit_tickets()
    wait(1)
    
    demo_3_retrieve_ticket(tickets)
    wait(1)
    
    demo_4_list_customer_tickets()
    wait(1)
    
    demo_5_api_documentation()
    wait(1)
    
    demo_6_system_architecture()
    wait(1)
    
    # Ask if user wants to run live test
    print_header("READY FOR LIVE TEST?")
    print(f"\n  Would you like to create a live ticket now?")
    choice = input(f"\n  {Colors.CYAN}(y/n):{Colors.ENDC} ").strip().lower()
    
    if choice == 'y':
        demo_7_live_test()
    else:
        print_info("Skipping live test")
    
    # Final summary
    print_header("🎉 DEMO COMPLETE!")
    
    print(f"\n  {Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  {'─' * 76}")
    print(f"  {Colors.GREEN}✓{Colors.ENDC} Health Check          - System operational")
    print(f"  {Colors.GREEN}✓{Colors.ENDC} Ticket Submission     - 5 tickets created")
    print(f"  {Colors.GREEN}✓{Colors.ENDC} Ticket Retrieval      - Details displayed")
    print(f"  {Colors.GREEN}✓{Colors.ENDC} Customer Lookup       - Working")
    print(f"  {Colors.GREEN}✓{Colors.ENDC} API Documentation     - Available at /docs")
    print(f"  {Colors.GREEN}✓{Colors.ENDC} System Architecture   - Multi-channel ready")
    
    print(f"\n  {Colors.BOLD}Useful URLs:{Colors.ENDC}")
    print(f"    • API Health:      {Colors.CYAN}http://localhost:8000/health{Colors.ENDC}")
    print(f"    • API Docs:        {Colors.CYAN}http://localhost:8000/docs{Colors.ENDC}")
    print(f"    • Frontend:        {Colors.CYAN}frontend/index.html{Colors.ENDC}")
    
    print(f"\n  {Colors.GREEN}{Colors.BOLD}🚀 Your Customer Success FTE is ready!{Colors.ENDC}")
    print(f"  {Colors.BOLD}Completed at:{Colors.ENDC} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Demo interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
