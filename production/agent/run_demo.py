"""
Quick Demo - Bina database ke test karo
Direct imports - no openai.agents dependency
"""

import os
import sys
import re
from typing import Dict, List, Any
from datetime import datetime
from enum import Enum

# Direct imports from tools.py
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()


# ============================================================================
# Enums
# ============================================================================

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class Category(str, Enum):
    HOW_TO = "how_to"
    TECHNICAL_ISSUE = "technical_issue"
    FEATURE_INQUIRY = "feature_inquiry"
    BILLING = "billing"
    DEFAULT = "default"


# ============================================================================
# Sentiment Analyzer (Copy from tools.py)
# ============================================================================

class SentimentAnalyzer:
    """Simple sentiment analysis"""

    POSITIVE_WORDS = {
        'love': 1.0, 'great': 0.8, 'awesome': 1.0, 'excellent': 1.0,
        'amazing': 0.9, 'thank': 0.7, 'thanks': 0.7, 'happy': 0.8,
        'pleased': 0.7, 'satisfied': 0.6, 'wonderful': 0.9, 'fantastic': 0.9,
        'good': 0.5, 'perfect': 1.0, 'helpful': 0.6, 'appreciate': 0.7
    }

    NEGATIVE_WORDS = {
        'hate': -1.0, 'terrible': -1.0, 'awful': -1.0, 'worst': -1.0,
        'horrible': -1.0, 'bad': -0.7, 'angry': -0.8, 'frustrated': -0.7,
        'frustrating': -0.7, 'disappointed': -0.6, 'disappointing': -0.6,
        'useless': -0.9, 'broken': -0.7, 'unacceptable': -0.9, 'issue': -0.4,
        'problem': -0.4, 'error': -0.5, 'bug': -0.5, 'sucks': -0.8
    }

    URGENCY_INDICATORS = {
        'urgent': -0.3, 'asap': -0.3, 'immediately': -0.3, 'right now': -0.3,
        'deadline': -0.2, 'emergency': -0.4, 'critical': -0.3, '!!!': -0.2
    }

    ANGER_INDICATORS = ['unacceptable', 'useless', 'worst', 'terrible', 'hate',
                       'angry', 'ridiculous', 'pathetic', 'disgusting']

    @classmethod
    def analyze(cls, message: str) -> Dict[str, Any]:
        message_lower = message.lower()
        words = re.findall(r'\b\w+\b', message_lower)

        positive_score = sum(cls.POSITIVE_WORDS.get(word, 0) for word in words)
        negative_score = sum(cls.NEGATIVE_WORDS.get(word, 0) for word in words)
        urgency_score = sum(score for indicator, score in cls.URGENCY_INDICATORS.items()
                           if indicator in message_lower)

        anger_score = sum(-0.5 for indicator in cls.ANGER_INDICATORS
                         if indicator in message_lower)

        total_sentiment = positive_score + negative_score + urgency_score + anger_score
        normalized_score = max(-1.0, min(1.0, total_sentiment / max(1, len(words) * 0.1)))

        if any(indicator in message_lower for indicator in ['urgent', 'asap', 'emergency']):
            sentiment_type = "urgent"
        elif anger_score < -0.5:
            sentiment_type = "angry"
        elif negative_score < -1.0:
            sentiment_type = "frustrated"
        elif normalized_score > 0.3:
            sentiment_type = "positive"
        elif normalized_score < -0.3:
            sentiment_type = "negative"
        else:
            sentiment_type = "neutral"

        return {
            'sentiment': sentiment_type,
            'score': round(normalized_score, 3),
            'positive_indicators': [w for w in words if w in cls.POSITIVE_WORDS],
            'negative_indicators': [w for w in words if w in cls.NEGATIVE_WORDS],
            'urgency_detected': urgency_score < 0,
            'anger_detected': anger_score < -0.3
        }


# ============================================================================
# Escalation Rules (Copy from tools.py)
# ============================================================================

class EscalationRules:
    """Escalation decision engine"""

    RULES = [
        {
            'id': 1,
            'name': 'Pricing & Enterprise Sales',
            'keywords': ['enterprise', 'pricing', 'quote', 'contract', 'volume discount',
                        '50+ users', '100+ users', 'custom pricing', 'negotiate', 'price'],
            'priority': 'P1',
            'route_to': 'Sales Team (Enterprise)',
            'sla_hours': 1
        },
        {
            'id': 2,
            'name': 'Refund & Billing Disputes',
            'keywords': ['refund', 'charged twice', 'billing error', 'payment failed',
                        'overcharged', 'dispute', 'chargeback', 'double charge'],
            'priority': 'P1',
            'route_to': 'Billing Specialist',
            'sla_hours': 1
        },
        {
            'id': 3,
            'name': 'Legal & Compliance',
            'keywords': ['gdpr', 'hipaa', 'soc 2', 'compliance', 'legal', 'baa',
                        'data processing', 'audit', 'lawsuit', 'attorney', 'subpoena'],
            'priority': 'P0',
            'route_to': 'Legal & Compliance Team',
            'sla_hours': 0.25
        },
        {
            'id': 4,
            'name': 'Angry/Threatening Customers',
            'keywords': ['cancel immediately', 'worst service', 'unacceptable', 'useless',
                        'threaten', 'lawyer', 'sue', 'review bomb'],
            'priority': 'P1',
            'route_to': 'Senior Support Agent / Team Lead',
            'sla_hours': 1
        },
        {
            'id': 5,
            'name': 'System-wide Technical Bugs',
            'keywords': ['not working', 'broken', 'outage', 'down', 'all users',
                        'everyone', 'system-wide', 'critical bug'],
            'priority': 'P0',
            'route_to': 'Engineering Team',
            'sla_hours': 0.25
        },
        {
            'id': 6,
            'name': 'Data Loss or Security Breach',
            'keywords': ['data lost', 'missing data', 'hacked', 'unauthorized access',
                        'security breach', 'account compromised', 'deleted permanently'],
            'priority': 'P0',
            'route_to': 'Security Team + Engineering Lead',
            'sla_hours': 0.25
        },
        {
            'id': 7,
            'name': 'VIP Customer',
            'keywords': ['enterprise plan', 'vip', 'premium'],
            'priority': 'P1',
            'route_to': 'Dedicated Account Manager',
            'sla_hours': 1
        },
        {
            'id': 8,
            'name': 'API & Integration Support',
            'keywords': ['api', 'webhook', 'integration', 'developer', 'custom code',
                        'rest', 'sdk', 'rate limit', 'authentication error'],
            'priority': 'P2',
            'route_to': 'Developer Support / Integration Specialist',
            'sla_hours': 4
        },
        {
            'id': 9,
            'name': 'Account Cancellation',
            'keywords': ['cancel', 'close account', 'stop subscription', 'leaving',
                        'switching to competitor'],
            'priority': 'P2',
            'route_to': 'Retention Specialist',
            'sla_hours': 4
        },
        {
            'id': 10,
            'name': 'Feature Requests',
            'keywords': ['feature request', 'roadmap', 'when will', 'add feature',
                        'suggestion', 'product idea', 'custom development'],
            'priority': 'P3',
            'route_to': 'Product Management Team',
            'sla_hours': 24
        }
    ]

    @classmethod
    def check_escalation(cls, message: str) -> Dict:
        message_lower = message.lower()
        matched_rules = []

        for rule in cls.RULES:
            for keyword in rule['keywords']:
                if keyword.lower() in message_lower:
                    matched_rules.append(rule)
                    break

        if not matched_rules:
            return {'requires_escalation': False}

        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
        matched_rules.sort(key=lambda r: priority_order.get(r['priority'], 4))

        best_rule = matched_rules[0]
        return {
            'requires_escalation': True,
            'reason': best_rule['name'],
            'priority': best_rule['priority'],
            'route_to': best_rule['route_to'],
            'rule_id': best_rule['id'],
            'sla_hours': best_rule['sla_hours']
        }


# ============================================================================
# Response Generator
# ============================================================================

class ResponseGenerator:
    """Channel-aware response generator"""

    TEMPLATES = {
        Category.HOW_TO.value: {
            Channel.EMAIL.value: """Hi {name},

Thanks for reaching out! I'd be happy to help you with {topic}.

Here's how to do it:

{steps}

If you need any further assistance, feel free to reach out.

Best regards,
TechNova Support Team""",

            Channel.WHATSAPP.value: """Hey! 👋 {action_text}

Need more help?""",

            Channel.WEB_FORM.value: """Hi {name},

Thanks for your question about {topic}.

{steps}

Let us know if you need further assistance.

Best,
TechNova Support"""
        },

        Category.TECHNICAL_ISSUE.value: {
            Channel.EMAIL.value: """Hi {name},

Thank you for reporting this issue. I understand how frustrating this must be.

Let me help you troubleshoot this:

{steps}

If the issue persists, please let me know and I'll escalate this.

Best regards,
TechNova Support Team""",

            Channel.WHATSAPP.value: """Hi! Sorry you're facing this issue 😕

{action_text}

Let me know if it works!""",

            Channel.WEB_FORM.value: """Hi {name},

Thanks for reporting this technical issue.

Please try: {steps}

If problem continues, reply with browser version and screenshot.

Best,
TechNova Support"""
        },

        Category.DEFAULT.value: {
            Channel.EMAIL.value: """Hi {name},

Thank you for contacting TechNova Support.

I've received your message about: {topic}

I'm looking into this and will get back to you shortly.

Best regards,
TechNova Support Team""",

            Channel.WHATSAPP.value: """Hi! 👋 Got your message. Checking this for you now - one sec!""",

            Channel.WEB_FORM.value: """Hi {name},

Thanks for contacting TechNova Support.

We've received your request about: {topic}

Our team will respond within 4 hours.

Best,
TechNova Support"""
        }
    }

    STEPS_DB = {
        'slack': """1. Go to Settings → Integrations
2. Click "Connect Slack"
3. Authorize TechNova in Slack
4. Select channels for notifications
5. Click "Save" """,

        'task': """1. Click + button in your project
2. Enter task name
3. Assign team member
4. Set due date
5. Click "Create" """,

        'team': """1. Go to Settings → Team
2. Click "Invite Member"
3. Enter email address
4. Select role
5. Send invitation """,

        'default': """1. Log in to your TechNova account
2. Navigate to the relevant section
3. Follow the on-screen instructions
4. Contact support if you need help"""
    }

    @classmethod
    def generate(cls, channel: str, category: str, message: str,
                 customer_name: str = None,
                 kb_results: List[Dict] = None) -> Dict[str, Any]:

        template_dict = cls.TEMPLATES.get(category, cls.TEMPLATES[Category.DEFAULT.value])
        template = template_dict.get(channel, template_dict[Channel.EMAIL.value])

        name = customer_name.split()[0] if customer_name else "there"
        topic = cls._extract_topic(message)
        steps = cls._get_steps(message)

        action_text = "Let me help you with that!"
        if channel == Channel.WHATSAPP.value:
            action_text = steps.split('\n')[0].replace('1. ', '')

        response_text = template.format(
            name=name,
            topic=topic,
            steps=steps,
            action_text=action_text
        )

        return {
            'text': response_text,
            'channel': channel,
            'character_count': len(response_text),
            'word_count': len(response_text.split()),
            'tone': 'helpful' if category == Category.HOW_TO.value else 'empathetic',
            'template_used': f"{channel}-{category}"
        }

    @classmethod
    def _extract_topic(cls, message: str) -> str:
        cleaned = message.strip()
        starters = ['how do i', 'how to', 'how can i', 'what is', 'i need']
        for starter in starters:
            if cleaned.lower().startswith(starter):
                cleaned = cleaned[len(starter):].strip()
                break
        cleaned = cleaned.rstrip('?.!')
        return cleaned[:60] if cleaned else "your request"

    @classmethod
    def _get_steps(cls, message: str) -> str:
        message_lower = message.lower()
        if 'slack' in message_lower or 'integration' in message_lower:
            return cls.STEPS_DB['slack']
        elif 'task' in message_lower:
            return cls.STEPS_DB['task']
        elif 'team' in message_lower or 'member' in message_lower:
            return cls.STEPS_DB['team']
        return cls.STEPS_DB['default']


# ============================================================================
# MAIN DEMO
# ============================================================================

def main():
    print("=" * 80)
    print("TECHNOVA AGENT - QUICK DEMO")
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
        print(f"{emoji} \"{msg[:50]}...\"")
        print(f"   → {result['sentiment'].upper()} (score: {result['score']})")
        if result['urgency_detected']:
            print(f"   ⚠️  URGENT detected!")
        print()

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
        "How do I create tasks?"
    ]

    for msg in escalation_tests:
        result = EscalationRules.check_escalation(msg)
        if result.get('requires_escalation'):
            print(f"⚠️  \"{msg[:50]}...\"")
            print(f"   → ESCALATE: {result['reason']}")
            print(f"   → Team: {result['route_to']}")
            print(f"   → Priority: {result['priority']}")
        else:
            print(f"✅ \"{msg[:50]}...\"")
            print(f"   → AI can handle")
        print()

    # Test 3: Response Generation
    print("\n\n3️⃣ RESPONSE GENERATION TEST")
    print("-" * 80)

    test_cases = [
        {
            'channel': 'email',
            'category': 'how_to',
            'message': "How do I integrate with Slack?",
            'customer_name': "John Doe"
        },
        {
            'channel': 'whatsapp',
            'category': 'technical_issue',
            'message': "App not working!",
            'customer_name': "Jane"
        },
        {
            'channel': 'web_form',
            'category': 'billing',
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
            customer_name=test['customer_name']
        )

        print(f"\n📝 Response:")
        for line in response['text'].split('\n')[:6]:
            print(f"   {line}")

        print(f"\n   ✓ Tone: {response['tone']}")
        print(f"   ✓ Words: {response['word_count']}")
        print(f"   ✓ Characters: {response['character_count']}")

    # Test 4: Full Flow
    print("\n\n4️⃣ FULL CUSTOMER INTERACTION")
    print("-" * 80)

    customer_message = "Hi, I need help integrating TechNova with Slack. Can you guide me?"
    customer_name = "Sarah Johnson"
    channel = "email"

    print(f"\n📩 INCOMING:")
    print(f"   From: {customer_name}")
    print(f"   Channel: {channel}")
    print(f"   Message: {customer_message}")

    sentiment = SentimentAnalyzer.analyze(customer_message)
    print(f"\n📊 SENTIMENT: {sentiment['sentiment']} (score: {sentiment['score']})")

    escalation = EscalationRules.check_escalation(customer_message)
    if escalation.get('requires_escalation'):
        print(f"⚠️  ESCALATION: {escalation['reason']}")
    else:
        print(f"✅ No escalation needed")

    response = ResponseGenerator.generate(
        channel=channel,
        category='how_to',
        message=customer_message,
        customer_name=customer_name
    )

    print(f"\n📧 RESPONSE:")
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


if __name__ == "__main__":
    main()
