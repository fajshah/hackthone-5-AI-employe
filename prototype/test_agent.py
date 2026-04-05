"""
Test script for Customer Support Agent
Run this after each iteration to test improvements
"""

from agent_core import CustomerSupportAgent, CustomerMessage

def test_agent():
    agent = CustomerSupportAgent()
    
    print("=" * 80)
    print("ITERATION TEST SUITE")
    print("=" * 80)
    
    # Test 1: Pricing inquiry (should escalate)
    print("\n\n📋 TEST 1: Pricing Inquiry (Should Escalate)")
    print("-" * 80)
    msg1 = CustomerMessage(
        channel='email',
        customer_name='John Doe',
        customer_email='john@example.com',
        subject='Pricing question',
        message='What is the pricing for 100 users on Enterprise plan?'
    )
    resp1 = agent.process_message(msg1)
    print(f"Message: {msg1.message}")
    print(f"Escalation: {resp1.requires_escalation} ✓" if resp1.requires_escalation else f"Escalation: {resp1.requires_escalation} ✗")
    print(f"Priority: {resp1.priority}")
    print(f"Reason: {resp1.escalation_reason}")
    
    # Test 2: WhatsApp short message
    print("\n\n📋 TEST 2: WhatsApp Short Message")
    print("-" * 80)
    msg2 = CustomerMessage(
        channel='whatsapp',
        customer_name='Alex',
        customer_phone='+1-555-0101',
        message='hey how do i add someone?'
    )
    resp2 = agent.process_message(msg2)
    print(f"Message: {msg2.message}")
    print(f"Response length: {len(resp2.response_text)} chars")
    print(f"Response:\n{resp2.response_text}")
    print(f"Is short (<200 chars): {'✓' if len(resp2.response_text) < 200 else '✗'}")
    
    # Test 3: Email with greeting + signature
    print("\n\n📋 TEST 3: Email Format (Should have greeting + signature)")
    print("-" * 80)
    msg3 = CustomerMessage(
        channel='email',
        customer_name='Sarah Williams',
        customer_email='sarah@company.com',
        subject='Help needed',
        message='How do I create a new project?'
    )
    resp3 = agent.process_message(msg3)
    print(f"Message: {msg3.message}")
    print(f"Response:\n{resp3.response_text}")
    has_greeting = 'Hi' in resp3.response_text or 'Hello' in resp3.response_text
    has_signature = 'TechNova Support' in resp3.response_text
    print(f"Has greeting: {'✓' if has_greeting else '✗'}")
    print(f"Has signature: {'✓' if has_signature else '✗'}")
    
    # Test 4: WhatsApp response conciseness
    print("\n\n📋 TEST 4: WhatsApp Response Conciseness")
    print("-" * 80)
    msg4 = CustomerMessage(
        channel='whatsapp',
        customer_name='Maria',
        customer_phone='+1-555-0102',
        message='app crashing 😤'
    )
    resp4 = agent.process_message(msg4)
    print(f"Message: {msg4.message}")
    print(f"Response:\n{resp4.response_text}")
    print(f"Response length: {len(resp4.response_text)} chars")
    print(f"Is concise (<150 chars): {'✓' if len(resp4.response_text) < 150 else '✗'}")
    
    # Test 5: Bug report categorization
    print("\n\n📋 TEST 5: Bug Report Categorization")
    print("-" * 80)
    msg5 = CustomerMessage(
        channel='web_form',
        customer_name='Nathan',
        customer_email='nathan@test.com',
        subject='Dashboard not working',
        message='Dashboard widgets not loading. Tried clearing cache. Chrome 122.'
    )
    resp5 = agent.process_message(msg5)
    print(f"Message: {msg5.message}")
    print(f"Category: {resp5.category}")
    print(f"Expected: technical_issue")
    print(f"Match: {'✓' if resp5.category == 'technical_issue' else '✗'}")
    
    # Test 6: Angry customer sentiment
    print("\n\n📋 TEST 6: Angry Customer Sentiment")
    print("-" * 80)
    msg6 = CustomerMessage(
        channel='whatsapp',
        customer_name='Angry User',
        customer_phone='+1-555-0103',
        message='This is unacceptable! Worst service ever!!! I want to cancel immediately!'
    )
    resp6 = agent.process_message(msg6)
    print(f"Message: {msg6.message}")
    print(f"Sentiment: {resp6.sentiment}")
    print(f"Escalation: {resp6.requires_escalation}")
    print(f"Priority: {resp6.priority}")
    
    print("\n\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_agent()
