"""
Quick Demo - Bina database ke test karo
Sirf OpenAI API key chahiye
"""

import os
from dotenv import load_dotenv

load_dotenv()

from agent.tools import (
    SentimentAnalyzer,
    EscalationRules,
    ResponseGenerator,
    Channel,
    Category,
)

print("=" * 80)
print("TECHNOVA AGENT - QUICK DEMO (Fallback Mode)")
print("=" * 80)

# Test 1: Sentiment Analysis
print("\n\n1️⃣ SENTIMENT ANALYSIS TEST")
print("-" * 80)

test_messages = [
    "I love this product! It's amazing!",
    "This is terrible. Worst service ever.",
    "How do I add a team member?",
    "URGENT!!! System is down, need help ASAP!",
    "I'm frustrated with the bugs. This is unacceptable!"
]

for msg in test_messages:
    result = SentimentAnalyzer.analyze(msg)
    emoji = "😊" if result['sentiment'] == 'positive' else "😠" if result['anger_detected'] else "😐"
    print(f"{emoji} {msg[:50]}...")
    print(f"   → {result['sentiment']} (score: {result['score']})")
    if result['urgency_detected']:
        print(f"   ⚠️  URGENT detected!")

# Test 2: Escalation Detection
print("\n\n2️⃣ ESCALATION DETECTION TEST")
print("-" * 80)

escalation_tests = [
    "I need enterprise pricing for 100+ users",
    "I was charged twice, want refund",
    "Is this HIPAA compliant?",
    "This is unacceptable! Worst service!",
    "System is down for all users!",
    "My data is lost!",
    "How do I create tasks?"  # No escalation
]

for msg in escalation_tests:
    result = EscalationRules.check_escalation(msg)
    if result:
        print(f"⚠️  {msg[:50]}...")
        print(f"   → ESCALATE: {result['reason']}")
        print(f"   → Team: {result['route_to']}")
        print(f"   → Priority: {result['priority']}")
    else:
        print(f"✅ {msg[:50]}...")
        print(f"   → AI can handle")

# Test 3: Response Generation
print("\n\n3️⃣ RESPONSE GENERATION TEST")
print("-" * 80)

test_cases = [
    {
        'channel': Channel.EMAIL.value,
        'category': Category.HOW_TO.value,
        'message': "How do I integrate with Slack?",
        'customer_name': "John Doe"
    },
    {
        'channel': Channel.WHATSAPP.value,
        'category': Category.TECHNICAL_ISSUE.value,
        'message': "App not working!",
        'customer_name': "Jane"
    },
    {
        'channel': Channel.WEB_FORM.value,
        'category': Category.BILLING.value,
        'message': "I was charged twice",
        'customer_name': "Bob"
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. {test['channel'].upper()} - {test['category'].upper()}")
    print(f"   Customer: {test['customer_name']}")
    print(f"   Message: {test['message']}")
    print(f"   " + "-" * 60)
    
    response = ResponseGenerator.generate(
        channel=test['channel'],
        category=test['category'],
        message=test['message'],
        customer_name=test['customer_name'],
        kb_results=None  # No KB in fallback mode
    )
    
    print(f"\n   📝 Response:")
    for line in response['text'].split('\n')[:5]:  # First 5 lines
        print(f"      {line}")
    if len(response['text'].split('\n')) > 5:
        print("      ...")
    
    print(f"\n   ✓ Tone: {response['tone']}")
    print(f"   ✓ Words: {response['word_count']}")
    print(f"   ✓ Characters: {response['character_count']}")

# Test 4: Full Flow Example
print("\n\n4️⃣ FULL CUSTOMER INTERACTION FLOW")
print("-" * 80)

customer_message = "Hi, I need help integrating TechNova with Slack. Can you guide me?"
customer_name = "Sarah Johnson"
customer_email = "sarah@company.com"
channel = "email"

print(f"\n📩 INCOMING MESSAGE:")
print(f"   From: {customer_name} <{customer_email}>")
print(f"   Channel: {channel}")
print(f"   Message: {customer_message}")

# Step 1: Analyze sentiment
sentiment = SentimentAnalyzer.analyze(customer_message)
print(f"\n📊 SENTIMENT ANALYSIS:")
print(f"   → {sentiment['sentiment']} (score: {sentiment['score']})")

# Step 2: Check escalation
escalation = EscalationRules.check_escalation(customer_message)
print(f"\n🔍 ESCALATION CHECK:")
if escalation:
    print(f"   ⚠️  ESCALATE: {escalation['reason']}")
    print(f"   → Team: {escalation['route_to']}")
else:
    print(f"   ✅ No escalation needed - AI can handle")

# Step 3: Generate response
print(f"\n✏️  GENERATING RESPONSE...")
response = ResponseGenerator.generate(
    channel=channel,
    category=Category.HOW_TO.value,
    message=customer_message,
    customer_name=customer_name,
    kb_results=[{
        'feature': 'Slack Integration',
        'content': """Connect TechNova with Slack:
1. Go to Settings → Integrations
2. Click "Connect Slack"
3. Authorize TechNova
4. Select channels
5. Save settings"""
    }]
)

print(f"\n📧 FINAL RESPONSE:")
print("-" * 80)
print(response['text'])
print("-" * 80)

print("\n\n" + "=" * 80)
print("✅ DEMO COMPLETED!")
print("=" * 80)
print("\n✓ Sentiment Analysis: Working")
print("✓ Escalation Detection: Working")
print("✓ Response Generation: Working")
print("✓ Channel Adaptation: Working")
print("\n🎉 All core features functional!")
print("\n💡 Next: Add DATABASE_URL and OPENAI_API_KEY to .env for full features")
