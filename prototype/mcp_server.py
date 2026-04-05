"""
TechNova Customer Support MCP Server
Implements the MCP (Model Context Protocol) server for the Hackathon 5 agent.

This server exposes customer support tools to AI assistants:
- search_knowledge_base: Search product documentation
- create_ticket: Create new support tickets
- get_customer_history: Retrieve customer conversation history
- escalate_to_human: Escalate to human agents
- send_response: Send channel-aware responses
"""

import asyncio
import json
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)


# ============================================================================
# Enums
# ============================================================================

class Channel(Enum):
    """Supported communication channels"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class Priority(Enum):
    """Ticket priority levels"""
    P0 = "P0"  # Critical - 15 min response
    P1 = "P1"  # High - 1 hour response
    P2 = "P2"  # Medium - 4 hours response
    P3 = "P3"  # Low - 24 hours response


class Category(Enum):
    """Message categories"""
    HOW_TO = "how_to"
    TECHNICAL_ISSUE = "technical_issue"
    FEATURE_INQUIRY = "feature_inquiry"
    BILLING = "billing"
    ESCALATION = "escalation"
    DEFAULT = "default"


class Sentiment(Enum):
    """Customer sentiment"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    URGENT = "urgent"


class ResolutionStatus(Enum):
    """Ticket resolution status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CustomerMessage:
    """Represents an incoming customer message"""
    channel: str
    message: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    subject: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""
    timestamp: datetime
    channel: str
    message: str
    response: str
    category: str
    sentiment: str
    sentiment_score: float
    priority: str
    requires_escalation: bool
    escalation_reason: Optional[str] = None
    topic: Optional[str] = None


@dataclass
class CustomerProfile:
    """Complete customer profile with history and preferences"""
    customer_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    preferred_channel: str = "email"
    communication_style: str = "neutral"
    timezone: str = "UTC"
    language: str = "en"
    account_tier: str = "basic"
    is_vip: bool = False
    conversations: Dict[str, List[dict]] = field(default_factory=dict)
    open_topics: List[str] = field(default_factory=list)
    resolved_topics: List[str] = field(default_factory=list)
    sentiment_history: List[dict] = field(default_factory=list)
    average_sentiment: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_contact: datetime = None
    total_tickets: int = 0
    escalated_tickets: int = 0


@dataclass
class Ticket:
    """Support ticket"""
    ticket_id: str
    customer_id: str
    channel: str
    subject: str
    message: str
    category: str
    priority: str
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = None
    resolved_at: datetime = None
    escalation_reason: Optional[str] = None


# ============================================================================
# Knowledge Base
# ============================================================================

class KnowledgeBase:
    """Product documentation knowledge base"""
    
    def __init__(self, product_docs_path: str = None):
        self.documents = []
        if product_docs_path is None:
            product_docs_path = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "context", 
                "product-docs.md"
            )
        self.load_product_docs(product_docs_path)
    
    def load_product_docs(self, path: str):
        """Load and parse product documentation"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            feature_sections = re.split(r'## Feature \d+:', content)
            
            for section in feature_sections[1:]:
                lines = section.strip().split('\n')
                if lines:
                    feature_name = lines[0].strip()
                    feature_content = section
                    
                    self.documents.append({
                        'feature': feature_name,
                        'content': feature_content,
                        'keywords': self._extract_keywords(feature_name, feature_content)
                    })
        except FileNotFoundError:
            print(f"Warning: Product docs not found at {path}")
            # Add sample documents
            self._add_sample_documents()
    
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
    
    def _add_sample_documents(self):
        """Add sample documents for demo"""
        self.documents.append({
            'feature': 'Smart Task Creation',
            'content': 'Create tasks instantly with AI-powered auto-filling. Type / to create a task. AI suggests assignee based on workload.',
            'keywords': ['task', 'create', 'ai']
        })
        self.documents.append({
            'feature': 'Kanban Boards',
            'content': 'Visual workflow management with drag-and-drop cards. Custom columns, WIP limits, swimlanes.',
            'keywords': ['kanban', 'board', 'workflow']
        })
        self.documents.append({
            'feature': 'Integrations',
            'content': 'Connect with 100+ tools: Slack, GitHub, Google Drive, Jira, Salesforce.',
            'keywords': ['integration', 'slack', 'github']
        })
    
    def search(self, query: str, limit: int = 3) -> List[Dict]:
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
        return [doc for score, doc in results[:limit]]


# ============================================================================
# Escalation Rules Engine
# ============================================================================

class EscalationRules:
    """Handles escalation decision logic"""
    
    RULES = [
        {
            'id': 1,
            'name': 'Pricing & Enterprise Sales',
            'keywords': ['enterprise', 'pricing', 'quote', 'contract', 'volume discount', 
                        '50+ users', '100+ users', 'custom pricing', 'negotiate', 'price'],
            'priority': Priority.P1.value,
            'route_to': 'Sales Team (Enterprise)'
        },
        {
            'id': 2,
            'name': 'Refund & Billing Disputes',
            'keywords': ['refund', 'charged twice', 'billing error', 'payment failed', 
                        'overcharged', 'dispute', 'chargeback', 'double charge'],
            'priority': Priority.P1.value,
            'route_to': 'Billing Specialist'
        },
        {
            'id': 3,
            'name': 'Legal & Compliance',
            'keywords': ['gdpr', 'hipaa', 'soc 2', 'compliance', 'legal', 'baa', 
                        'data processing', 'audit', 'lawsuit', 'attorney', 'subpoena'],
            'priority': Priority.P0.value,
            'route_to': 'Legal & Compliance Team'
        },
        {
            'id': 4,
            'name': 'Angry/Threatening Customers',
            'keywords': ['cancel immediately', 'worst service', 'unacceptable', 'useless', 
                        'threaten', 'lawyer', 'sue', 'review bomb'],
            'priority': Priority.P1.value,
            'route_to': 'Senior Support Agent / Team Lead'
        },
        {
            'id': 5,
            'name': 'System-wide Technical Bugs',
            'keywords': ['not working', 'broken', 'outage', 'down', 'all users', 
                        'everyone', 'system-wide', 'critical bug'],
            'priority': Priority.P0.value,
            'route_to': 'Engineering Team'
        },
        {
            'id': 6,
            'name': 'Data Loss or Security Breach',
            'keywords': ['data lost', 'missing data', 'hacked', 'unauthorized access', 
                        'security breach', 'account compromised', 'deleted permanently'],
            'priority': Priority.P0.value,
            'route_to': 'Security Team + Engineering Lead'
        },
        {
            'id': 7,
            'name': 'VIP Customer',
            'keywords': ['enterprise plan', 'vip', 'premium'],
            'priority': Priority.P1.value,
            'route_to': 'Dedicated Account Manager'
        },
        {
            'id': 8,
            'name': 'API & Integration Support',
            'keywords': ['api', 'webhook', 'integration', 'developer', 'custom code', 
                        'rest', 'sdk', 'rate limit', 'authentication error'],
            'priority': Priority.P2.value,
            'route_to': 'Developer Support / Integration Specialist'
        },
        {
            'id': 9,
            'name': 'Account Cancellation',
            'keywords': ['cancel', 'close account', 'stop subscription', 'leaving', 
                        'switching to competitor'],
            'priority': Priority.P2.value,
            'route_to': 'Retention Specialist'
        },
        {
            'id': 10,
            'name': 'Feature Requests',
            'keywords': ['feature request', 'roadmap', 'when will', 'add feature', 
                        'suggestion', 'product idea', 'custom development'],
            'priority': Priority.P3.value,
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


# ============================================================================
# Sentiment Analyzer
# ============================================================================

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
        """Analyze sentiment of message"""
        message_lower = message.lower()
        
        positive_count = sum(1 for word in cls.POSITIVE_WORDS if word in message_lower)
        negative_count = sum(1 for word in cls.NEGATIVE_WORDS if word in message_lower)
        urgency_count = sum(1 for indicator in cls.URGENCY_INDICATORS if indicator in message)
        
        total = positive_count + negative_count
        score = (positive_count - negative_count) / total if total > 0 else 0.0
        
        if urgency_count > 0:
            score = min(score - 0.2, 1.0)
        
        if score > 0.3:
            label = Sentiment.POSITIVE.value
        elif score < -0.3:
            label = Sentiment.NEGATIVE.value
        elif urgency_count > 0:
            label = Sentiment.URGENT.value
        else:
            label = Sentiment.NEUTRAL.value
        
        return label, score


# ============================================================================
# Response Generator
# ============================================================================

class ResponseGenerator:
    """Generates channel-aware responses"""
    
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
        
        Category.FEATURE_INQUIRY.value: {
            Channel.EMAIL.value: """Hi {name},

Great question! Yes, TechNova does support {topic}.

{explanation}

Documentation: https://docs.technova.com/{topic_slug}

Best regards,
TechNova Support Team""",
            
            Channel.WHATSAPP.value: """Yep, we have {feature_name}! ✅

{action_text}

Want me to send you a guide?""",
            
            Channel.WEB_FORM.value: """Hi {name},

Yes, TechNova supports {topic}.

{explanation}

Docs: https://docs.technova.com

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
    
    @classmethod
    def generate(cls, channel: str, category: str, message: str,
                 customer_name: Optional[str] = None,
                 kb_results: Optional[List[Dict]] = None,
                 is_followup: bool = False,
                 context: Optional[str] = None) -> str:
        """Generate a response based on channel, category, and context"""
        
        # Get template
        if category in cls.TEMPLATES and channel in cls.TEMPLATES[category]:
            template = cls.TEMPLATES[category][channel]
        else:
            template = cls.TEMPLATES[Category.DEFAULT.value][channel]
        
        # Prepare variables
        name = customer_name.split()[0] if customer_name else "there"
        topic = cls._extract_topic(message)
        
        # Get steps from KB
        if kb_results and len(kb_results) > 0:
            steps = cls._format_steps(kb_results, channel)
            action_text = cls._generate_action_text(category, channel, kb_results)
            feature_name = kb_results[0]['feature']
            explanation = kb_results[0]['content'][:300]
        else:
            steps = cls._get_generic_steps(category, channel)
            action_text = cls._get_generic_action_text(category, channel)
            feature_name = "this feature"
            explanation = "This feature helps you manage your projects."
        
        # Fill template
        response = template.format(
            name=name,
            topic=topic,
            steps=steps.get('long', ''),
            action_text=action_text,
            explanation=explanation,
            topic_slug=topic.replace(' ', '-').lower()[:50],
            feature_name=feature_name
        )
        
        return response
    
    @classmethod
    def _extract_topic(cls, message: str) -> str:
        """Extract the main topic from the message"""
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
        """Generate concise action text for WhatsApp"""
        doc = kb_results[0]
        
        if channel == Channel.WHATSAPP.value:
            content = doc['content']
            
            numbered = re.findall(r'\d+\.\s*([^\n]+)', content)
            if numbered:
                steps = numbered[:2]
                clean_steps = [re.sub(r'\*\*|\*', '', s).strip()[:60] for s in steps]
                if len(clean_steps) == 1:
                    return f"Try: {clean_steps[0]}"
                return f"1. {clean_steps[0]}\n2. {clean_steps[1]}"
            
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
        if channel == Channel.WHATSAPP.value:
            generic = {
                Category.HOW_TO.value: "1. Open your project\n2. Click the + button\n3. Follow prompts",
                Category.TECHNICAL_ISSUE.value: "1. Refresh (Ctrl+Shift+R)\n2. Clear cache\n3. Try incognito",
                Category.FEATURE_INQUIRY.value: "Check Settings → Features!",
                Category.DEFAULT.value: "Let me check this real quick!"
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
        
        numbered = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)', content, re.DOTALL)
        if numbered:
            steps_long = [re.sub(r'\*\*|\*', '', s.strip()) for s in numbered[:5]]
        
        if not steps_long:
            bullets = re.findall(r'[-•*]\s*(.+?)(?=\n[-•*]|\n\n|$)', content, re.DOTALL)
            if bullets:
                steps_long = [re.sub(r'\*\*|\*', '', s.strip()) for s in bullets[:5]]
        
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
            Category.HOW_TO.value: {
                'long': "1. Log in to your TechNova account\n2. Navigate to the relevant project\n3. Look for the action button\n4. Follow the instructions",
                'short': "1. Open project\n2. Click action button\n3. Follow prompts"
            },
            Category.TECHNICAL_ISSUE.value: {
                'long': "1. Try refreshing (Ctrl+Shift+R)\n2. Clear browser cache\n3. Try incognito mode\n4. Test in different browser",
                'short': "1. Refresh\n2. Clear cache\n3. Try incognito"
            },
            Category.FEATURE_INQUIRY.value: {
                'long': "This feature is in your dashboard. Go to Settings → Features.",
                'short': "Check Settings → Features"
            }
        }
        return generic.get(category, generic[Category.HOW_TO.value])


# ============================================================================
# Conversation Memory
# ============================================================================

class ConversationMemory:
    """Manages conversation history and customer profiles"""
    
    def __init__(self):
        self.customers: Dict[str, CustomerProfile] = {}
        self.phone_to_customer: Dict[str, str] = {}
        self.topic_to_customer: Dict[str, str] = {}
        self.tickets: Dict[str, Ticket] = {}
    
    def get_or_create_customer(self, message: CustomerMessage) -> CustomerProfile:
        """Get existing customer or create new one"""
        if message.customer_email:
            customer_id = message.customer_email.lower()
            if customer_id in self.customers:
                return self.customers[customer_id]
            
            profile = CustomerProfile(
                customer_id=customer_id,
                name=message.customer_name or "Unknown",
                email=message.customer_email,
                phone=message.customer_phone
            )
            self.customers[customer_id] = profile
            
            if message.customer_phone:
                self.phone_to_customer[message.customer_phone] = customer_id
            
            return profile
        
        if message.customer_phone:
            if message.customer_phone in self.phone_to_customer:
                customer_id = self.phone_to_customer[message.customer_phone]
                return self.customers[customer_id]
            
            customer_id = f"phone:{message.customer_phone}"
            profile = CustomerProfile(
                customer_id=customer_id,
                name=message.customer_name or "Unknown",
                phone=message.customer_phone
            )
            self.customers[customer_id] = profile
            self.phone_to_customer[message.customer_phone] = customer_id
            return profile
        
        customer_id = f"anon:{uuid.uuid4().hex[:8]}"
        profile = CustomerProfile(
            customer_id=customer_id,
            name=message.customer_name or "Anonymous"
        )
        self.customers[customer_id] = profile
        return profile
    
    def get_customer_by_id(self, customer_id: str) -> Optional[CustomerProfile]:
        """Get customer by ID"""
        return self.customers.get(customer_id)
    
    def detect_followup(self, customer_id: str, message: str) -> Tuple[bool, Optional[str]]:
        """Detect if message is a followup"""
        customer = self.customers.get(customer_id)
        if not customer:
            return False, None
        
        followup_indicators = [
            'follow up', 'following up', 'update', 'still', 'any update',
            'what about', 'regarding', 're:', 'back to', 'continue',
            'as i said', 'as i mentioned', 'my previous', 'earlier'
        ]
        
        message_lower = message.lower()
        is_followup = any(indicator in message_lower for indicator in followup_indicators)
        
        if is_followup and customer.open_topics:
            return True, customer.open_topics[-1]
        
        for topic_id, turns in customer.conversations.items():
            if topic_id in customer.resolved_topics:
                continue
            
            for turn in turns[-2:]:
                topic_words = set(turn.get('message', '').lower().split())
                message_words = set(message_lower.split())
                overlap = len(topic_words & message_words)
                
                if overlap >= 3:
                    return True, topic_id
        
        return is_followup, customer.open_topics[-1] if customer.open_topics else None
    
    def add_conversation(self, customer_id: str, topic_id: str, turn: dict):
        """Add conversation turn to memory"""
        customer = self.customers.get(customer_id)
        if not customer:
            return
        
        if topic_id not in customer.conversations:
            customer.conversations[topic_id] = []
            customer.open_topics.append(topic_id)
        
        customer.conversations[topic_id].append(turn)
        customer.last_contact = datetime.now()
        customer.total_tickets += 1
        
        # Update sentiment
        customer.sentiment_history.append({
            'timestamp': datetime.now().isoformat(),
            'sentiment': turn['sentiment'],
            'score': turn['sentiment_score']
        })
        self._update_average_sentiment(customer)
        
        # Auto-resolve simple how-to
        if turn['category'] == Category.HOW_TO.value and not turn['requires_escalation']:
            if topic_id in customer.open_topics:
                customer.open_topics.remove(topic_id)
            if topic_id not in customer.resolved_topics:
                customer.resolved_topics.append(topic_id)
        
        self.topic_to_customer[topic_id] = customer_id
    
    def _update_average_sentiment(self, customer: CustomerProfile):
        """Calculate rolling average sentiment"""
        if not customer.sentiment_history:
            customer.average_sentiment = 0.0
            return
        
        weights = []
        scores = []
        for i, record in enumerate(customer.sentiment_history[-10:]):
            weight = (i + 1) ** 0.5
            weights.append(weight)
            scores.append(record['score'])
        
        customer.average_sentiment = sum(w * s for w, s in zip(weights, scores)) / sum(weights)
    
    def create_ticket(self, customer_id: str, message: CustomerMessage, 
                     category: str, priority: str, escalation_reason: Optional[str] = None) -> Ticket:
        """Create a support ticket"""
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            channel=message.channel,
            subject=message.subject or "Support Request",
            message=message.message,
            category=category,
            priority=priority,
            status=ResolutionStatus.ESCALATED.value if escalation_reason else ResolutionStatus.OPEN.value,
            escalation_reason=escalation_reason
        )
        
        self.tickets[ticket_id] = ticket
        return ticket
    
    def get_customer_summary(self, customer_id: str) -> str:
        """Get customer summary"""
        customer = self.customers.get(customer_id)
        if not customer:
            return ""
        
        parts = [
            f"Customer: {customer.name}",
            f"Tier: {customer.account_tier}",
            f"Preferred channel: {customer.preferred_channel}",
            f"Total interactions: {customer.total_tickets}",
            f"Escalated: {customer.escalated_tickets}",
            f"Average sentiment: {customer.average_sentiment:.2f}",
        ]
        
        if customer.open_topics:
            parts.append(f"Open topics: {len(customer.open_topics)}")
        
        return " | ".join(parts)


# ============================================================================
# MCP Server
# ============================================================================

app = Server("technova-support-agent")

# Initialize components
kb = KnowledgeBase()
memory = ConversationMemory()
escalation_checker = EscalationRules()
sentiment_analyzer = SentimentAnalyzer()
response_generator = ResponseGenerator()


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_knowledge_base",
            description="Search product documentation for answers to customer questions",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (customer question or topic)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="create_ticket",
            description="Create a new support ticket for a customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_email": {
                        "type": "string",
                        "description": "Customer email address (primary identifier)"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name"
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer phone number (optional)"
                    },
                    "channel": {
                        "type": "string",
                        "enum": ["email", "whatsapp", "web_form"],
                        "description": "Communication channel"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Ticket subject"
                    },
                    "message": {
                        "type": "string",
                        "description": "Customer message"
                    }
                },
                "required": ["customer_email", "channel", "message"]
            }
        ),
        Tool(
            name="get_customer_history",
            description="Retrieve customer conversation history and profile",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_email": {
                        "type": "string",
                        "description": "Customer email address"
                    }
                },
                "required": ["customer_email"]
            }
        ),
        Tool(
            name="escalate_to_human",
            description="Escalate a ticket to human support agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID to escalate"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for escalation"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["P0", "P1", "P2", "P3"],
                        "description": "Priority level"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes for human agent"
                    }
                },
                "required": ["ticket_id", "reason"]
            }
        ),
        Tool(
            name="send_response",
            description="Generate and send a channel-aware response to customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_email": {
                        "type": "string",
                        "description": "Customer email address"
                    },
                    "channel": {
                        "type": "string",
                        "enum": ["email", "whatsapp", "web_form"],
                        "description": "Communication channel"
                    },
                    "message": {
                        "type": "string",
                        "description": "Customer message to respond to"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["how_to", "technical_issue", "feature_inquiry", "default"],
                        "description": "Message category"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name for personalization"
                    }
                },
                "required": ["customer_email", "channel", "message"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[Any]:
    """Handle tool calls"""
    
    if name == "search_knowledge_base":
        return await search_knowledge_base(
            query=arguments.get("query", ""),
            limit=arguments.get("limit", 3)
        )
    
    elif name == "create_ticket":
        return await create_ticket(
            customer_email=arguments.get("customer_email"),
            customer_name=arguments.get("customer_name"),
            customer_phone=arguments.get("customer_phone"),
            channel=arguments.get("channel", "email"),
            subject=arguments.get("subject"),
            message=arguments.get("message")
        )
    
    elif name == "get_customer_history":
        return await get_customer_history(
            customer_email=arguments.get("customer_email")
        )
    
    elif name == "escalate_to_human":
        return await escalate_to_human(
            ticket_id=arguments.get("ticket_id"),
            reason=arguments.get("reason"),
            priority=arguments.get("priority", "P2"),
            notes=arguments.get("notes")
        )
    
    elif name == "send_response":
        return await send_response(
            customer_email=arguments.get("customer_email"),
            channel=arguments.get("channel", "email"),
            message=arguments.get("message"),
            category=arguments.get("category", "default"),
            customer_name=arguments.get("customer_name")
        )
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def search_knowledge_base(query: str, limit: int = 3) -> List[Any]:
    """Search product documentation"""
    results = kb.search(query, limit)
    
    if not results:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "query": query,
                "results": [],
                "message": "No relevant documents found"
            }, indent=2)
        )]
    
    formatted_results = []
    for doc in results:
        formatted_results.append({
            "feature": doc['feature'],
            "keywords": doc['keywords'],
            "content_preview": doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content']
        })
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "query": query,
            "count": len(formatted_results),
            "results": formatted_results
        }, indent=2)
    )]


async def create_ticket(
    customer_email: str,
    channel: str,
    message: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    subject: Optional[str] = None
) -> List[Any]:
    """Create a new support ticket"""
    try:
        # Create message object
        msg = CustomerMessage(
            channel=channel,
            message=message,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            subject=subject
        )
        
        # Get or create customer
        customer = memory.get_or_create_customer(msg)
        
        # Analyze message
        sentiment_label, sentiment_score = sentiment_analyzer.analyze(message)
        escalation_info = escalation_checker.check_escalation(message)
        
        # Determine category
        category = Category.DEFAULT.value
        message_lower = message.lower()
        if any(word in message_lower for word in ['how', 'how to', 'how do', 'help me']):
            category = Category.HOW_TO.value
        elif any(word in message_lower for word in ['not working', 'broken', 'error', 'issue', 'problem']):
            category = Category.TECHNICAL_ISSUE.value
        elif any(word in message_lower for word in ['what is', 'does it have', 'can i', 'is there']):
            category = Category.FEATURE_INQUIRY.value
        
        # Create ticket
        ticket = memory.create_ticket(
            customer_id=customer.customer_id,
            message=msg,
            category=category,
            priority=escalation_info['priority'] if escalation_info else Priority.P3.value,
            escalation_reason=escalation_info['reason'] if escalation_info else None
        )
        
        # Generate topic ID
        topic_id = f"topic_{customer.customer_id}_{uuid.uuid4().hex[:8]}"
        
        # Store conversation turn
        turn = {
            'timestamp': datetime.now().isoformat(),
            'channel': channel,
            'message': message,
            'category': category,
            'sentiment': sentiment_label,
            'sentiment_score': sentiment_score,
            'priority': ticket.priority,
            'requires_escalation': escalation_info['requires_escalation'] if escalation_info else False,
            'escalation_reason': escalation_info['reason'] if escalation_info else None,
            'topic': topic_id,
            'ticket_id': ticket.ticket_id
        }
        
        memory.add_conversation(customer.customer_id, topic_id, turn)
        
        # Update VIP status
        if escalation_info and escalation_info.get('rule_id') == 7:
            customer.is_vip = True
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "ticket": {
                    "ticket_id": ticket.ticket_id,
                    "customer_id": customer.customer_id,
                    "channel": channel,
                    "subject": ticket.subject,
                    "category": category,
                    "priority": ticket.priority,
                    "status": ticket.status,
                    "requires_escalation": escalation_info['requires_escalation'] if escalation_info else False,
                    "escalation_reason": escalation_info['reason'] if escalation_info else None,
                    "topic_id": topic_id
                },
                "customer": {
                    "name": customer.name,
                    "email": customer.email,
                    "total_tickets": customer.total_tickets
                }
            }, indent=2)
        )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def get_customer_history(customer_email: str) -> List[Any]:
    """Retrieve customer conversation history"""
    try:
        customer = memory.get_customer_by_id(customer_email.lower())
        
        if not customer:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Customer not found",
                    "customer_email": customer_email
                }, indent=2)
            )]
        
        # Build summary
        summary = {
            "success": True,
            "customer": {
                "customer_id": customer.customer_id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "company": customer.company,
                "account_tier": customer.account_tier,
                "is_vip": customer.is_vip,
                "preferred_channel": customer.preferred_channel,
                "language": customer.language,
                "timezone": customer.timezone
            },
            "statistics": {
                "total_tickets": customer.total_tickets,
                "escalated_tickets": customer.escalated_tickets,
                "open_topics": len(customer.open_topics),
                "resolved_topics": len(customer.resolved_topics),
                "average_sentiment": round(customer.average_sentiment, 2)
            },
            "open_topics": [],
            "recent_sentiment": customer.sentiment_history[-5:] if customer.sentiment_history else []
        }
        
        # Add open topics
        for topic_id in customer.open_topics:
            if topic_id in customer.conversations:
                turns = customer.conversations[topic_id]
                if turns:
                    summary["open_topics"].append({
                        "topic_id": topic_id,
                        "turns": len(turns),
                        "first_message": turns[0]['message'][:100],
                        "last_message": turns[-1]['message'][:100],
                        "category": turns[0]['category']
                    })
        
        return [TextContent(
            type="text",
            text=json.dumps(summary, indent=2)
        )]
    
    except Exception as e:
        return [ErrorContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def escalate_to_human(
    ticket_id: str,
    reason: str,
    priority: str = "P2",
    notes: Optional[str] = None
) -> List[Any]:
    """Escalate ticket to human agent"""
    try:
        ticket = memory.tickets.get(ticket_id)
        
        if not ticket:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Ticket {ticket_id} not found"
                }, indent=2)
            )]
        
        # Update ticket
        ticket.status = ResolutionStatus.ESCALATED.value
        ticket.priority = priority
        ticket.escalation_reason = reason
        ticket.updated_at = datetime.now()
        
        # Determine routing based on reason
        route_to = "Support Team"
        if "billing" in reason.lower() or "refund" in reason.lower():
            route_to = "Billing Specialist"
        elif "technical" in reason.lower() or "bug" in reason.lower():
            route_to = "Engineering Team"
        elif "enterprise" in reason.lower() or "pricing" in reason.lower():
            route_to = "Sales Team"
        elif "legal" in reason.lower() or "compliance" in reason.lower():
            route_to = "Legal Team"
        
        escalation = {
            "ticket_id": ticket_id,
            "status": "escalated",
            "reason": reason,
            "priority": priority,
            "routed_to": route_to,
            "notes": notes,
            "escalated_at": datetime.now().isoformat(),
            "sla_response_time": {
                "P0": "15 minutes",
                "P1": "1 hour",
                "P2": "4 hours",
                "P3": "24 hours"
            }.get(priority, "24 hours")
        }
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "escalation": escalation,
                "message": f"Ticket {ticket_id} escalated to {route_to}"
            }, indent=2)
        )]
    
    except Exception as e:
        return [ErrorContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def send_response(
    customer_email: str,
    channel: str,
    message: str,
    category: str = "default",
    customer_name: Optional[str] = None
) -> List[Any]:
    """Generate and send channel-aware response"""
    try:
        # Search knowledge base
        kb_results = kb.search(message, limit=3)
        
        # Generate response
        response_text = response_generator.generate(
            channel=channel,
            category=category,
            message=message,
            customer_name=customer_name,
            kb_results=kb_results if kb_results else None
        )
        
        # Get customer for context
        customer = memory.get_customer_by_id(customer_email.lower())
        customer_summary = memory.get_customer_summary(customer_email.lower()) if customer else ""
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "response": {
                    "text": response_text,
                    "channel": channel,
                    "category": category,
                    "character_count": len(response_text),
                    "estimated_read_time": f"{len(response_text.split()) * 0.5:.0f} seconds"
                },
                "customer_context": customer_summary,
                "knowledge_base_results": len(kb_results),
                "channel_guidelines": {
                    "email": "Formal, 150-300 words, include greeting and signature",
                    "whatsapp": "Casual, <150 characters, emoji OK, concise",
                    "web_form": "Semi-formal, 100-200 words, structured"
                }
            }, indent=2)
        )]
    
    except Exception as e:
        return [ErrorContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
