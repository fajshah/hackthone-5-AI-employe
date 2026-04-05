"""
TechNova Customer Support AI Agent - Core Interaction Loop
Prototype for Hackathon 5

Iterations:
1. Initial prototype with basic categorization and escalation
2. Fixed product docs path handling
3. Improved WhatsApp response conciseness
4. Better topic extraction and action text generation
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CustomerMessage:
    """Represents an incoming customer message"""
    channel: str  # 'email', 'whatsapp', 'web_form'
    message: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    subject: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AgentResponse:
    """Represents the agent's response"""
    response_text: str
    channel: str
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None
    priority: str = "P3"  # P0, P1, P2, P3
    category: Optional[str] = None
    sentiment: str = "neutral"


class KnowledgeBase:
    """Simple keyword-based knowledge base search"""
    
    def __init__(self, product_docs_path: str):
        self.documents = []
        self.load_product_docs(product_docs_path)
    
    def load_product_docs(self, path: str):
        """Load and parse product documentation"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by features (simple parsing)
            feature_sections = re.split(r'## Feature \d+:', content)
            
            for section in feature_sections[1:]:  # Skip header
                # Extract feature name and content
                lines = section.strip().split('\n')
                feature_name = lines[0].strip()
                feature_content = section
                
                self.documents.append({
                    'feature': feature_name,
                    'content': feature_content,
                    'keywords': self._extract_keywords(feature_name, feature_content)
                })
        except FileNotFoundError:
            print(f"Warning: Product docs not found at {path}")
    
    def _extract_keywords(self, name: str, content: str) -> List[str]:
        """Extract keywords from feature documentation"""
        text = (name + " " + content).lower()
        keywords = set()
        important_words = [
            'task', 'kanban', 'board', 'ai', 'insight', 'integration',
            'slack', 'github', 'time', 'tracking', 'gantt', 'chart',
            'team', 'collaboration', 'dashboard', 'workflow', 'automation',
            'mobile', 'app', 'report', 'permission', 'role'
        ]
        for word in important_words:
            if word in text:
                keywords.add(word)
        return list(keywords)
    
    def search(self, query: str) -> List[Dict]:
        """Search knowledge base for relevant documents"""
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            score = 0
            for keyword in doc['keywords']:
                if keyword in query_lower:
                    score += 2
            if doc['feature'].lower() in query_lower:
                score += 5
            if any(word in query_lower for word in doc['content'].lower().split()[:50]):
                score += 1
            
            if score > 0:
                results.append((score, doc))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in results[:3]]


class EscalationRules:
    """Handles escalation decision logic"""
    
    RULES = [
        {
            'id': 1,
            'name': 'Pricing & Enterprise Sales',
            'keywords': ['enterprise', 'pricing', 'quote', 'contract', 'volume discount', 
                        '50+ users', '100+ users', 'custom pricing', 'negotiate', 'price'],
            'priority': 'P1',
            'route_to': 'Sales Team (Enterprise)'
        },
        {
            'id': 2,
            'name': 'Refund & Billing Disputes',
            'keywords': ['refund', 'charged twice', 'billing error', 'payment failed', 
                        'overcharged', 'dispute', 'chargeback', 'double charge'],
            'priority': 'P1',
            'route_to': 'Billing Specialist'
        },
        {
            'id': 3,
            'name': 'Legal & Compliance',
            'keywords': ['gdpr', 'hipaa', 'soc 2', 'compliance', 'legal', 'baa', 
                        'data processing', 'audit', 'lawsuit', 'attorney', 'subpoena'],
            'priority': 'P0',
            'route_to': 'Legal & Compliance Team'
        },
        {
            'id': 4,
            'name': 'Angry/Threatening Customers',
            'keywords': ['cancel immediately', 'worst service', 'unacceptable', 'useless', 
                        'threaten', 'lawyer', 'sue', 'review bomb'],
            'priority': 'P1',
            'route_to': 'Senior Support Agent / Team Lead'
        },
        {
            'id': 5,
            'name': 'System-wide Technical Bugs',
            'keywords': ['not working', 'broken', 'outage', 'down', 'all users', 
                        'everyone', 'system-wide', 'critical bug'],
            'priority': 'P0',
            'route_to': 'Engineering Team'
        },
        {
            'id': 6,
            'name': 'Data Loss or Security Breach',
            'keywords': ['data lost', 'missing data', 'hacked', 'unauthorized access', 
                        'security breach', 'account compromised', 'deleted permanently'],
            'priority': 'P0',
            'route_to': 'Security Team + Engineering Lead'
        },
        {
            'id': 7,
            'name': 'VIP Customer',
            'keywords': ['enterprise plan', 'vip', 'premium'],
            'priority': 'P1',
            'route_to': 'Dedicated Account Manager'
        },
        {
            'id': 8,
            'name': 'API & Integration Support',
            'keywords': ['api', 'webhook', 'integration', 'developer', 'custom code', 
                        'rest', 'sdk', 'rate limit', 'authentication error'],
            'priority': 'P2',
            'route_to': 'Developer Support / Integration Specialist'
        },
        {
            'id': 9,
            'name': 'Account Cancellation',
            'keywords': ['cancel', 'close account', 'stop subscription', 'leaving', 
                        'switching to competitor'],
            'priority': 'P2',
            'route_to': 'Retention Specialist'
        },
        {
            'id': 10,
            'name': 'Feature Requests',
            'keywords': ['feature request', 'roadmap', 'when will', 'add feature', 
                        'suggestion', 'product idea', 'custom development'],
            'priority': 'P3',
            'route_to': 'Product Management Team'
        }
    ]
    
    @classmethod
    def check_escalation(cls, message: str) -> Optional[Dict]:
        """Check if message requires escalation"""
        message_lower = message.lower()
        
        for rule in cls.RULES:
            for keyword in rule['keywords']:
                if keyword.lower() in message_lower:
                    return {
                        'requires_escalation': True,
                        'reason': rule['name'],
                        'priority': rule['priority'],
                        'route_to': rule['route_to'],
                        'rule_id': rule['id']
                    }
        
        return None


class SentimentAnalyzer:
    """Simple sentiment analysis"""
    
    POSITIVE_WORDS = ['love', 'great', 'awesome', 'excellent', 'amazing', 'thank', 'thanks',
                      'happy', 'pleased', 'satisfied', 'wonderful', 'fantastic', 'good']
    
    NEGATIVE_WORDS = ['hate', 'terrible', 'awful', 'worst', 'horrible', 'bad', 'angry',
                      'frustrated', 'frustrating', 'disappointed', 'disappointing', 'useless',
                      'broken', 'unacceptable', 'issue', 'problem', 'error']
    
    URGENCY_INDICATORS = ['urgent', 'asap', 'immediately', 'right now', 'deadline', 'emergency',
                          'critical', '!!!', 'URGENT', 'ASAP']
    
    @classmethod
    def analyze(cls, message: str) -> Tuple[str, float]:
        message_lower = message.lower()
        
        positive_count = sum(1 for word in cls.POSITIVE_WORDS if word in message_lower)
        negative_count = sum(1 for word in cls.NEGATIVE_WORDS if word in message_lower)
        urgency_count = sum(1 for indicator in cls.URGENCY_INDICATORS if indicator in message)
        
        total = positive_count + negative_count
        score = (positive_count - negative_count) / total if total > 0 else 0.0
        
        if urgency_count > 0:
            score = min(score - 0.2, 1.0)
        
        if score > 0.3:
            label = 'positive'
        elif score < -0.3:
            label = 'negative'
        elif urgency_count > 0:
            label = 'urgent'
        else:
            label = 'neutral'
        
        return label, score


class ResponseGenerator:
    """Generates channel-aware responses"""
    
    TEMPLATES = {
        'how_to': {
            'email': """Hi {name},

Thanks for reaching out! I'd be happy to help you with {topic}.

Here's how to do it:

{steps}

If you need any further assistance, feel free to reach out.

Best regards,
TechNova Support Team""",
            
            'whatsapp': """Hey! 👋 {action_text}

Need more help?""",
            
            'web_form': """Hi {name},

Thanks for your question about {topic}.

{steps}

Let us know if you need further assistance.

Best,
TechNova Support"""
        },
        
        'technical_issue': {
            'email': """Hi {name},

Thank you for reporting this issue. I understand how frustrating this must be, especially when you're trying to get work done.

Let me help you troubleshoot this:

{steps}

If the issue persists after trying these steps, please let me know and I'll escalate this to our technical team.

Best regards,
TechNova Support Team""",
            
            'whatsapp': """Hi! Sorry you're facing this issue 😕

{action_text}

Let me know if it works!""",
            
            'web_form': """Hi {name},

Thanks for reporting this technical issue.

Please try the following steps:

{steps}

If the problem continues, please reply with:
- Browser version
- Screenshot of the error
- Console logs (F12 → Console)

Best,
TechNova Support"""
        },
        
        'feature_inquiry': {
            'email': """Hi {name},

Great question! Yes, TechNova does support {topic}.

{explanation}

You can find more details in our documentation at: https://docs.technova.com/{topic_slug}

Let me know if you need help setting this up!

Best regards,
TechNova Support Team""",
            
            'whatsapp': """Yep, we have {feature_name}! ✅

{action_text}

Want me to send you a guide?""",
            
            'web_form': """Hi {name},

Yes, TechNova supports {topic}.

{explanation}

For detailed documentation, visit: https://docs.technova.com

Best,
TechNova Support"""
        },
        
        'default': {
            'email': """Hi {name},

Thank you for contacting TechNova Support.

I've received your message about: {topic}

I'm looking into this for you and will get back to you shortly with a solution.

If this is urgent, please reply with "URGENT" and I'll prioritize your request.

Best regards,
TechNova Support Team""",
            
            'whatsapp': """Hi! 👋 Got your message. Checking this for you now - one sec!""",
            
            'web_form': """Hi {name},

Thanks for contacting TechNova Support.

We've received your request about: {topic}

Our team will respond within 4 hours.

Best,
TechNova Support"""
        }
    }
    
    @classmethod
    def generate(cls, channel: str, category: str, message: str, 
                 customer_name: Optional[str] = None,
                 kb_results: Optional[List[Dict]] = None) -> str:
        
        if category in cls.TEMPLATES:
            template = cls.TEMPLATES[category][channel]
        else:
            template = cls.TEMPLATES['default'][channel]
        
        name = customer_name.split()[0] if customer_name else "there"
        topic = cls._extract_topic(message)
        
        if kb_results and len(kb_results) > 0:
            steps = cls._format_steps(kb_results, channel)
            action_text = cls._generate_action_text(category, channel, kb_results)
            feature_name = kb_results[0]['feature']
            explanation = kb_results[0]['content'][:300]
        else:
            steps = cls._get_generic_steps(category, channel)
            action_text = cls._get_generic_action_text(category, channel)
            feature_name = "this feature"
            explanation = "This feature helps you manage your projects more efficiently."
        
        response = template.format(
            name=name,
            topic=topic,
            steps=steps.get('long', ''),
            action_text=action_text,
            explanation=explanation,
            topic_slug=topic.replace(' ', '-').lower(),
            feature_name=feature_name
        )
        
        return response
    
    @classmethod
    def _extract_topic(cls, message: str) -> str:
        """Extract the main topic from the message - cleaned up"""
        cleaned = message.strip()
        starters = ['how do i', 'how to', 'how can i', 'what is', 'what are', 
                   'where do i', 'can you help', 'i need', 'i want to']
        for starter in starters:
            if cleaned.lower().startswith(starter):
                cleaned = cleaned[len(starter):].strip()
                break
        
        cleaned = cleaned.rstrip('?.!')
        
        if len(cleaned) > 60:
            cleaned = cleaned[:57] + "..."
        
        return cleaned if cleaned else "your request"
    
    @classmethod
    def _generate_action_text(cls, category: str, channel: str, kb_results: List[Dict]) -> str:
        """Generate concise action text - optimized for WhatsApp"""
        doc = kb_results[0]
        
        if channel == 'whatsapp':
            content = doc['content']
            
            # Try numbered steps
            numbered = re.findall(r'\d+\.\s*([^\n]+)', content)
            if numbered:
                steps = numbered[:2]
                clean_steps = [re.sub(r'\*\*|\*', '', s).strip()[:60] for s in steps]
                if len(clean_steps) == 1:
                    return f"Try: {clean_steps[0]}"
                return f"1. {clean_steps[0]}\n2. {clean_steps[1]}"
            
            # Try bullet points
            bullets = re.findall(r'[-•*]\s*([^\n]+)', content)
            if bullets:
                steps = bullets[:2]
                clean_steps = [re.sub(r'\*\*|\*', '', s).strip()[:60] for s in steps]
                if len(clean_steps) == 1:
                    return f"• {clean_steps[0]}"
                return f"• {clean_steps[0]}\n• {clean_steps[1]}"
            
            return f"Check {doc['feature']} in your dashboard!"
        
        return cls._format_steps(kb_results, channel).get('long', 'See documentation.')
    
    @classmethod
    def _get_generic_action_text(cls, category: str, channel: str) -> str:
        """Get generic action text for WhatsApp"""
        if channel == 'whatsapp':
            generic = {
                'how_to': "1. Open your project\n2. Click the + button\n3. Follow prompts",
                'technical_issue': "1. Refresh (Ctrl+Shift+R)\n2. Clear cache\n3. Try incognito",
                'feature_inquiry': "Check Settings → Features!",
                'default': "Let me check this real quick!"
            }
            return generic.get(category, "Let me help you with that!")
        return "Please check our documentation for more details."
    
    @classmethod
    def _format_steps(cls, kb_results: List[Dict], channel: str) -> Dict[str, str]:
        """Format KB results into steps"""
        if not kb_results:
            return {'long': 'No specific steps available.', 'short': 'Check docs'}
        
        doc = kb_results[0]
        content = doc['content']
        steps_long = []
        
        # Numbered steps
        numbered = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)', content, re.DOTALL)
        if numbered:
            steps_long = [re.sub(r'\*\*|\*', '', s.strip()) for s in numbered[:5]]
        
        # Bullet points
        if not steps_long:
            bullets = re.findall(r'[-•*]\s*(.+?)(?=\n[-•*]|\n\n|$)', content, re.DOTALL)
            if bullets:
                steps_long = [re.sub(r'\*\*|\*', '', s.strip()) for s in bullets[:5]]
        
        # Fallback
        if not steps_long:
            lines = content.split('\n')[:5]
            steps_long = [re.sub(r'\*\*|\*', '', line.strip()) for line in lines if line.strip()]
        
        long_formatted = '\n'.join([f"{i+1}. {step}" for i, step in enumerate(steps_long)])
        
        return {
            'long': long_formatted,
            'short': steps_long[0] if steps_long else 'Check docs'
        }
    
    @classmethod
    def _get_generic_steps(cls, category: str, channel: str) -> Dict[str, str]:
        """Get generic steps"""
        generic = {
            'how_to': {
                'long': "1. Log in to your TechNova account\n2. Navigate to the relevant project\n3. Look for the action button\n4. Follow the instructions",
                'short': "1. Open project\n2. Click action button\n3. Follow prompts"
            },
            'technical_issue': {
                'long': "1. Try refreshing (Ctrl+Shift+R)\n2. Clear browser cache\n3. Try incognito mode\n4. Test in different browser",
                'short': "1. Refresh\n2. Clear cache\n3. Try incognito"
            },
            'feature_inquiry': {
                'long': "This feature is in your dashboard. Go to Settings → Features.",
                'short': "Check Settings → Features"
            }
        }
        return generic.get(category, generic['how_to'])


class CustomerSupportAgent:
    """Main agent class"""
    
    def __init__(self, product_docs_path: str = None):
        if product_docs_path is None:
            # Try multiple paths
            paths = [
                "../context/product-docs.md",
                "context/product-docs.md",
                os.path.join(os.path.dirname(__file__), "..", "context", "product-docs.md")
            ]
            for p in paths:
                if os.path.exists(p):
                    product_docs_path = p
                    break
        
        self.kb = KnowledgeBase(product_docs_path) if product_docs_path else KnowledgeBase("../context/product-docs.md")
        self.escalation_checker = EscalationRules()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.response_generator = ResponseGenerator()
    
    def process_message(self, message: CustomerMessage) -> AgentResponse:
        full_text = f"{message.subject or ''} {message.message}".strip()
        
        sentiment_label, sentiment_score = self.sentiment_analyzer.analyze(full_text)
        kb_results = self.kb.search(full_text)
        escalation_info = self.escalation_checker.check_escalation(full_text)
        category = self._categorize_message(full_text, kb_results)
        
        response_text = self.response_generator.generate(
            channel=message.channel,
            category=category,
            message=full_text,
            customer_name=message.customer_name,
            kb_results=kb_results
        )
        
        return AgentResponse(
            response_text=response_text,
            channel=message.channel,
            requires_escalation=escalation_info['requires_escalation'] if escalation_info else False,
            escalation_reason=escalation_info['reason'] if escalation_info else None,
            priority=escalation_info['priority'] if escalation_info else 'P3',
            category=category,
            sentiment=sentiment_label
        )
    
    def _categorize_message(self, message: str, kb_results: List[Dict]) -> str:
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['how', 'how to', 'how do', 'help me']):
            return 'how_to'
        elif any(word in message_lower for word in ['not working', 'broken', 'error', 'issue', 'problem']):
            return 'technical_issue'
        elif any(word in message_lower for word in ['what is', 'does it have', 'can i', 'is there']):
            return 'feature_inquiry'
        else:
            return 'default'


def main():
    """Demo/test the agent"""
    agent = CustomerSupportAgent()
    
    test_messages = [
        CustomerMessage(
            channel='email',
            customer_name='Jennifer Martinez',
            customer_email='jennifer.martinez@acmecorp.com',
            subject='How do I set up integrations?',
            message='Hi, I just signed up for TechNova and I want to integrate it with Slack. Can you help me?'
        ),
        CustomerMessage(
            channel='whatsapp',
            customer_name='Alex Johnson',
            customer_phone='+1-555-0101',
            message='hey, how do I add someone to my project?'
        ),
        CustomerMessage(
            channel='whatsapp',
            customer_name='Maria Garcia',
            customer_phone='+1-555-0102',
            message='my app keeps crashing when I open the dashboard 😤'
        ),
        CustomerMessage(
            channel='email',
            customer_name='Tom Harris',
            customer_email='tom.harris@enterprise.com',
            subject='Enterprise pricing inquiry',
            message='We need a quote for 75 users on Enterprise plan with custom integrations.'
        ),
        CustomerMessage(
            channel='web_form',
            customer_name='Nathan Brooks',
            customer_email='nbrooks@innovate.io',
            subject='Dashboard widgets not loading',
            message='Dashboard widgets show loading spinner indefinitely. Tried clearing cache, different browsers.'
        )
    ]
    
    print("=" * 80)
    print("TECHNOVA CUSTOMER SUPPORT AGENT - DEMO")
    print("=" * 80)
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}: {msg.channel.upper()}")
        print(f"{'='*80}")
        print(f"\n📩 FROM: {msg.customer_name} ({msg.channel})")
        if msg.subject:
            print(f"📋 SUBJECT: {msg.subject}")
        print(f"💬 MESSAGE: {msg.message[:100]}...")
        
        response = agent.process_message(msg)
        
        print(f"\n📊 ANALYSIS:")
        print(f"   Category: {response.category}")
        print(f"   Sentiment: {response.sentiment}")
        print(f"   Priority: {response.priority}")
        print(f"   Escalation: {'YES ✓' if response.requires_escalation else 'No'}")
        if response.requires_escalation:
            print(f"   → Route to: {response.escalation_reason}")
        
        print(f"\n🤖 AGENT RESPONSE:")
        print(f"   {'-'*60}")
        for line in response.response_text.split('\n'):
            print(f"   {line}")
        print(f"   {'-'*60}")


if __name__ == "__main__":
    main()
