"""
Simple example: TechNova Customer Support Agent
Standalone version - no module imports needed
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import from run_demo.py (standalone versions)
from run_demo import SentimentAnalyzer, EscalationRules, ResponseGenerator, Channel, Category


async def main():
    """Example: Customer puchta hai Slack integration ke baare mein"""
    
    print("=" * 80)
    print("TECHNOVA SUPPORT AGENT - EXAMPLE")
    print("=" * 80)
    
    # Customer ka message
    customer_message = "Hi, how do I integrate TechNova with Slack?"
    customer_email = "john@company.com"
    customer_name = "John Doe"
    channel = "email"
    
    print(f"\n📩 Customer Message:")
    print(f"   From: {customer_name} <{customer_email}>")
    print(f"   Channel: {channel}")
    print(f"   Message: {customer_message}")
    
    # Step 1: Sentiment analyze karo
    print("\n\n1️⃣ ANALYZING SENTIMENT...")
    sentiment = SentimentAnalyzer.analyze(customer_message)
    print(f"   ✓ Sentiment: {sentiment['sentiment']}")
    print(f"   ✓ Score: {sentiment['score']}")
    print(f"   ✓ Urgency: {sentiment['urgency_detected']}")
    
    # Step 2: Escalation check karo
    print("\n\n2️⃣ CHECKING ESCALATION...")
    escalation = EscalationRules.check_escalation(customer_message)
    if escalation.get('requires_escalation'):
        print(f"   ⚠️  ESCALATION REQUIRED!")
        print(f"   → Reason: {escalation['reason']}")
        print(f"   → Team: {escalation['route_to']}")
        print(f"   → Priority: {escalation['priority']}")
    else:
        print(f"   ✅ No escalation needed - AI can handle")
    
    # Step 3: Response generate karo
    print("\n\n3️⃣ GENERATING RESPONSE...")
    response = ResponseGenerator.generate(
        channel=channel,
        category=Category.HOW_TO.value,
        message=customer_message,
        customer_name=customer_name
    )
    
    print(f"   ✓ Response generated")
    print(f"   ✓ Channel: {response['channel']}")
    print(f"   ✓ Word count: {response['word_count']}")
    print(f"   ✓ Tone: {response['tone']}")
    
    print("\n\n" + "=" * 80)
    print("📧 FINAL RESPONSE TO CUSTOMER:")
    print("=" * 80)
    print(response['text'])
    print("=" * 80)
    
    # Example 2: Angry customer - escalation needed
    print("\n\n\n")
    print("=" * 80)
    print("EXAMPLE 2: ANGRY CUSTOMER (ESCALATION)")
    print("=" * 80)
    
    angry_message = "I was charged twice! This is unacceptable! I want a refund NOW!"
    angry_email = "angry@customer.com"
    
    print(f"\n😠 Customer Message:")
    print(f"   From: {angry_email}")
    print(f"   Message: {angry_message}")
    
    # Sentiment analyze
    angry_sentiment = SentimentAnalyzer.analyze(angry_message)
    print(f"\n📊 Sentiment: {angry_sentiment['sentiment']} (score: {angry_sentiment['score']})")
    print(f"   Anger detected: {angry_sentiment['anger_detected']}")
    
    # Escalation check
    angry_escalation = EscalationRules.check_escalation(angry_message)
    if angry_escalation.get('requires_escalation'):
        print(f"\n⚠️  ESCALATION REQUIRED!")
        print(f"   → Reason: {angry_escalation['reason']}")
        print(f"   → Team: {angry_escalation['route_to']}")
        print(f"   → Priority: {angry_escalation['priority']}")
        print(f"   → SLA: {angry_escalation['sla_hours']} hours")
    else:
        print(f"\n✅ No escalation needed")
    
    # Response generate
    angry_response = ResponseGenerator.generate(
        channel="email",
        category=Category.BILLING.value,
        message=angry_message,
        customer_name="Angry Customer"
    )
    
    print(f"\n📧 RESPONSE:")
    print("-" * 80)
    print(angry_response['text'])
    print("-" * 80)


if __name__ == "__main__":
    print("\n🚀 Running TechNova Support Agent...\n")
    asyncio.run(main())
    print("\n✅ Done!")
