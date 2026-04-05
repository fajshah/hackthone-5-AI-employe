"""
Interactive test console for TechNova Customer Support Agent
Type messages to test the agent in real-time
"""

from agent_core import CustomerSupportAgent, CustomerMessage

def print_separator():
    print("\n" + "=" * 80)

def print_response(response):
    """Pretty print agent response"""
    print(f"\n📊 ANALYSIS:")
    print(f"   Category: {response.category}")
    print(f"   Sentiment: {response.sentiment}")
    print(f"   Priority: {response.priority}")
    print(f"   Escalation: {'YES ✓' if response.requires_escalation else 'No'}")
    if response.requires_escalation:
        print(f"   → Route to: {response.escalation_reason}")
    
    print(f"\n🤖 AGENT RESPONSE:")
    print(f"   {'─'*60}")
    for line in response.response_text.split('\n'):
        print(f"   {line}")
    print(f"   {'─'*60}")

def main():
    agent = CustomerSupportAgent()
    
    print_separator()
    print("TECHNOVA SUPPORT AGENT - INTERACTIVE TEST CONSOLE")
    print_separator()
    print("\nCommands:")
    print("  /help     - Show this help")
    print("  /email    - Switch to email channel (default)")
    print("  /whatsapp - Switch to WhatsApp channel")
    print("  /web      - Switch to web form channel")
    print("  /name X   - Set customer name")
    print("  /quit     - Exit")
    print_separator()
    
    current_channel = 'email'
    customer_name = "Test User"
    
    while True:
        try:
            # Get input
            prompt = f"[{current_channel}] {customer_name} > "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                parts = user_input.split()
                cmd = parts[0].lower()
                
                if cmd == '/quit':
                    print("\nGoodbye! 👋")
                    break
                elif cmd == '/help':
                    print("\nCommands: /email, /whatsapp, /web, /name X, /quit")
                    continue
                elif cmd == '/email':
                    current_channel = 'email'
                    print("→ Channel switched to EMAIL")
                    continue
                elif cmd == '/whatsapp':
                    current_channel = 'whatsapp'
                    print("→ Channel switched to WHATSAPP")
                    continue
                elif cmd == '/web':
                    current_channel = 'web_form'
                    print("→ Channel switched to WEB FORM")
                    continue
                elif cmd == '/name':
                    if len(parts) > 1:
                        customer_name = ' '.join(parts[1:])
                        print(f"→ Customer name set to: {customer_name}")
                    else:
                        print("Usage: /name Your Name")
                    continue
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type /help for commands")
                    continue
            
            # Create message
            msg = CustomerMessage(
                channel=current_channel,
                customer_name=customer_name,
                message=user_input,
                subject=None  # No subject in interactive mode
            )
            
            # Process and show response
            response = agent.process_message(msg)
            print_response(response)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type /quit to exit.")
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
