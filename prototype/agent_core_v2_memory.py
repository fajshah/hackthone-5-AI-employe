"""
TechNova Customer Support AI Agent - Core Interaction Loop with Memory
Prototype for Hackathon 5

Iterations:
1. Initial prototype with basic categorization and escalation
2. Fixed product docs path handling
3. Improved WhatsApp response conciseness
4. Better topic extraction and action text generation
5. Added memory: cross-channel continuity, sentiment tracking, conversation history
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ResolutionStatus(Enum):
    """Ticket resolution status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


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
    customer_id: str  # Email is primary key
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    
    # Preferences
    preferred_channel: str = "email"
    communication_style: str = "neutral"  # formal, casual, neutral
    timezone: str = "UTC"
    language: str = "en"
    
    # Account info
    account_tier: str = "basic"  # basic, pro, enterprise
    is_vip: bool = False
    
    # Conversation history
    conversations: Dict[str, List[ConversationTurn]] = field(default_factory=dict)
    # topic_id -> list of turns
    
    # Current state
    open_topics: List[str] = field(default_factory=list)
    resolved_topics: List[str] = field(default_factory=list)
    
    # Sentiment tracking
    sentiment_history: List[Tuple[datetime, str, float]] = field(default_factory=list)
    average_sentiment: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_contact: datetime = None
    total_tickets: int = 0
    escalated_tickets: int = 0
    
    def add_conversation(self, topic_id: str, turn: ConversationTurn):
        """Add a conversation turn to a topic"""
        if topic_id not in self.conversations:
            self.conversations[topic_id] = []
            self.open_topics.append(topic_id)
        
        self.conversations[topic_id].append(turn)
        self.last_contact = turn.timestamp
        self.total_tickets += 1
        
        # Update sentiment tracking
        self.sentiment_history.append((turn.timestamp, turn.sentiment, turn.sentiment_score))
        self._update_average_sentiment()
        
        # Update communication style based on channel usage
        self._update_preferences(turn.channel)
    
    def _update_average_sentiment(self):
        """Calculate rolling average sentiment"""
        if not self.sentiment_history:
            self.average_sentiment = 0.0
            return
        
        # Weight recent sentiments more heavily
        weights = []
        scores = []
        for i, (_, _, score) in enumerate(self.sentiment_history[-10:]):  # Last 10 interactions
            weight = (i + 1) ** 0.5  # Square root weighting
            weights.append(weight)
            scores.append(score)
        
        self.average_sentiment = sum(w * s for w, s in zip(weights, scores)) / sum(weights)
    
    def _update_preferences(self, channel: str):
        """Update customer preferences based on behavior"""
        # Track most used channel
        channel_counts = {}
        for turns in self.conversations.values():
            for turn in turns:
                channel_counts[turn.channel] = channel_counts.get(turn.channel, 0) + 1
        
        if channel_counts:
            self.preferred_channel = max(channel_counts, key=channel_counts.get)
    
    def resolve_topic(self, topic_id: str):
        """Mark a topic as resolved"""
        if topic_id in self.open_topics:
            self.open_topics.remove(topic_id)
        if topic_id not in self.resolved_topics:
            self.resolved_topics.append(topic_id)
    
    def get_topic_summary(self, topic_id: str) -> str:
        """Get summary of a topic conversation"""
        if topic_id not in self.conversations:
            return ""
        
        turns = self.conversations[topic_id]
        if not turns:
            return ""
        
        # Get first and last message
        first_msg = turns[0].message[:100]
        last_msg = turns[-1].message[:100]
        category = turns[0].category
        
        return f"Topic: {topic_id} | Category: {category} | Messages: {len(turns)} | First: {first_msg}..."


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
    topic_id: Optional[str] = None
    is_followup: bool = False
    context_used: Optional[str] = None


class ConversationMemory:
    """Manages conversation history and customer profiles"""
    
    def __init__(self):
        # Primary index: customer_id (email) -> profile
        self.customers: Dict[str, CustomerProfile] = {}
        
        # Secondary index: phone -> customer_id
        self.phone_to_customer: Dict[str, str] = {}
        
        # Topic index: topic_id -> customer_id
        self.topic_to_customer: Dict[str, str] = {}
        
        # Active conversations: customer_id -> current_topic_id
        self.active_conversations: Dict[str, str] = {}
    
    def get_or_create_customer(self, message: CustomerMessage) -> CustomerProfile:
        """Get existing customer or create new one"""
        # Try to find by email (primary key)
        if message.customer_email:
            customer_id = message.customer_email.lower()
            if customer_id in self.customers:
                return self.customers[customer_id]
            
            # Create new customer
            profile = CustomerProfile(
                customer_id=customer_id,
                name=message.customer_name or "Unknown",
                email=message.customer_email,
                phone=message.customer_phone
            )
            self.customers[customer_id] = profile
            
            # Index by phone if available
            if message.customer_phone:
                self.phone_to_customer[message.customer_phone] = customer_id
            
            return profile
        
        # Try to find by phone
        if message.customer_phone:
            if message.customer_phone in self.phone_to_customer:
                customer_id = self.phone_to_customer[message.customer_phone]
                return self.customers[customer_id]
            
            # Create new customer with phone
            customer_id = f"phone:{message.customer_phone}"
            profile = CustomerProfile(
                customer_id=customer_id,
                name=message.customer_name or "Unknown",
                phone=message.customer_phone
            )
            self.customers[customer_id] = profile
            self.phone_to_customer[message.customer_phone] = customer_id
            return profile
        
        # Anonymous customer (no email or phone)
        customer_id = f"anon:{id(message)}"
        profile = CustomerProfile(
            customer_id=customer_id,
            name=message.customer_name or "Anonymous"
        )
        self.customers[customer_id] = profile
        return profile
    
    def get_customer_by_id(self, customer_id: str) -> Optional[CustomerProfile]:
        """Get customer by ID"""
        return self.customers.get(customer_id)
    
    def get_conversation_context(self, customer_id: str, topic_id: Optional[str] = None) -> Optional[str]:
        """Get conversation context for continuity"""
        customer = self.customers.get(customer_id)
        if not customer:
            return None
        
        # If topic specified, get that topic's context
        if topic_id and topic_id in customer.conversations:
            turns = customer.conversations[topic_id]
            if turns:
                last_turn = turns[-1]
                return f"Previous discussion about {last_turn.category}: {last_turn.message[:100]}"
        
        # Otherwise, get most recent conversation
        if customer.open_topics:
            most_recent = customer.open_topics[-1]
            turns = customer.conversations[most_recent]
            if turns:
                last_turn = turns[-1]
                return f"Continuing from {last_turn.channel}: {last_turn.message[:100]}"
        
        return None
    
    def detect_followup(self, customer_id: str, message: str) -> Tuple[bool, Optional[str]]:
        """Detect if message is a followup to previous conversation"""
        customer = self.customers.get(customer_id)
        if not customer:
            return False, None
        
        # Check for followup indicators
        followup_indicators = [
            'follow up', 'following up', 'update', 'still', 'any update',
            'what about', 'regarding', 're:', 'back to', 'continue',
            'as i said', 'as i mentioned', 'my previous', 'earlier'
        ]
        
        message_lower = message.lower()
        is_followup = any(indicator in message_lower for indicator in followup_indicators)
        
        # If followup detected, find relevant topic
        if is_followup and customer.open_topics:
            # Return most recent open topic
            return True, customer.open_topics[-1]
        
        # Check if message references previous topic
        for topic_id, turns in customer.conversations.items():
            if topic_id in customer.resolved_topics:
                continue
            
            # Check for keyword overlap
            for turn in turns[-2:]:  # Last 2 turns
                topic_words = set(turn.message.lower().split())
                message_words = set(message_lower.split())
                overlap = len(topic_words & message_words)
                
                if overlap >= 3:  # 3+ common words
                    return True, topic_id
        
        return is_followup, customer.open_topics[-1] if customer.open_topics else None
    
    def add_conversation(self, customer_id: str, topic_id: str, turn: ConversationTurn):
        """Add conversation turn to memory"""
        customer = self.customers.get(customer_id)
        if not customer:
            return
        
        customer.add_conversation(topic_id, turn)
        
        # Update indexes
        self.topic_to_customer[topic_id] = customer_id
        
        # Update active conversation
        if turn.requires_escalation:
            customer.account_tier = "escalated"
        
        # Auto-resolve if simple how-to was answered
        if turn.category == 'how_to' and not turn.requires_escalation:
            customer.resolve_topic(topic_id)
    
    def get_customer_summary(self, customer_id: str) -> str:
        """Get customer summary for context"""
        customer = self.customers.get(customer_id)
        if not customer:
            return ""
        
        summary_parts = [
            f"Customer: {customer.name}",
            f"Tier: {customer.account_tier}",
            f"Preferred channel: {customer.preferred_channel}",
            f"Total interactions: {customer.total_tickets}",
            f"Escalated: {customer.escalated_tickets}",
            f"Average sentiment: {customer.average_sentiment:.2f}",
        ]
        
        if customer.open_topics:
            summary_parts.append(f"Open topics: {len(customer.open_topics)}")
        
        return " | ".join(summary_parts)


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
            
            feature_sections = re.split(r'## Feature \d+:', content)
            
            for section in feature_sections[1:]:
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
        
        'followup': {
            'email': """Hi {name},

Thanks for following up on this!

{context_reference}

{response_body}

Best regards,
TechNova Support Team""",
            
            'whatsapp': """Hi! Following up on this 👍

{response_body}""",
            
            'web_form': """Hi {name},

Thanks for the follow-up.

{context_reference}

{response_body}

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
                 kb_results: Optional[List[Dict]] = None,
                 is_followup: bool = False,
                 context: Optional[str] = None) -> str:
        
        # Use followup template if this is a followup message
        if is_followup:
            template = cls.TEMPLATES.get('followup', {}).get(channel, cls.TEMPLATES['default'][channel])
        elif category in cls.TEMPLATES:
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
        
        # Build context reference for followups
        context_reference = ""
        if context and is_followup:
            context_reference = f"Regarding our previous discussion: {context[:150]}\n\n"
        
        response_body = ""
        if is_followup:
            response_body = f"I'm checking on this for you. {action_text if channel == 'whatsapp' else steps.get('long', '')}"
        
        response = template.format(
            name=name,
            topic=topic,
            steps=steps.get('long', ''),
            action_text=action_text,
            explanation=explanation,
            topic_slug=topic.replace(' ', '-').lower(),
            feature_name=feature_name,
            context_reference=context_reference,
            response_body=response_body
        )
        
        return response
    
    @classmethod
    def _extract_topic(cls, message: str) -> str:
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
        doc = kb_results[0]
        
        if channel == 'whatsapp':
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
    """Main agent class with memory"""
    
    def __init__(self, product_docs_path: str = None):
        if product_docs_path is None:
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
        
        # Initialize memory
        self.memory = ConversationMemory()
    
    def process_message(self, message: CustomerMessage) -> AgentResponse:
        full_text = f"{message.subject or ''} {message.message}".strip()
        
        # Get or create customer profile
        customer = self.memory.get_or_create_customer(message)
        
        # Analyze sentiment
        sentiment_label, sentiment_score = self.sentiment_analyzer.analyze(full_text)
        
        # Search knowledge base
        kb_results = self.kb.search(full_text)
        
        # Check escalation rules
        escalation_info = self.escalation_checker.check_escalation(full_text)
        
        # Categorize message
        category = self._categorize_message(full_text, kb_results)
        
        # Check if this is a followup (using memory!)
        is_followup, related_topic = self.memory.detect_followup(customer.customer_id, full_text)
        
        # Get conversation context if available
        context = None
        if related_topic:
            context = self.memory.get_conversation_context(customer.customer_id, related_topic)
            if context:
                is_followup = True
        
        # Generate topic ID if new conversation
        import uuid
        topic_id = related_topic or f"topic_{customer.customer_id}_{uuid.uuid4().hex[:8]}"
        
        # Generate response (with memory context!)
        response_text = self.response_generator.generate(
            channel=message.channel,
            category='followup' if is_followup else category,
            message=full_text,
            customer_name=message.customer_name,
            kb_results=kb_results,
            is_followup=is_followup,
            context=context
        )
        
        # Create conversation turn
        turn = ConversationTurn(
            timestamp=datetime.now(),
            channel=message.channel,
            message=full_text,
            response=response_text,
            category=category,
            sentiment=sentiment_label,
            sentiment_score=sentiment_score,
            priority=escalation_info['priority'] if escalation_info else 'P3',
            requires_escalation=escalation_info['requires_escalation'] if escalation_info else False,
            escalation_reason=escalation_info['reason'] if escalation_info else None,
            topic=topic_id
        )
        
        # Store in memory
        self.memory.add_conversation(customer.customer_id, topic_id, turn)
        
        # Update customer VIP status if needed
        if escalation_info and escalation_info.get('rule_id') == 7:
            customer.is_vip = True
        
        # Build response object
        return AgentResponse(
            response_text=response_text,
            channel=message.channel,
            requires_escalation=turn.requires_escalation,
            escalation_reason=turn.escalation_reason,
            priority=turn.priority,
            category=category,
            sentiment=sentiment_label,
            topic_id=topic_id,
            is_followup=is_followup,
            context_used=context
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
    
    def get_customer_profile(self, customer_email: str) -> Optional[CustomerProfile]:
        """Get customer profile by email"""
        return self.memory.get_customer_by_id(customer_email.lower())
    
    def get_customer_summary(self, customer_email: str) -> str:
        """Get customer summary"""
        return self.memory.get_customer_summary(customer_email.lower())


def main():
    """Demo/test the agent with memory"""
    agent = CustomerSupportAgent()
    
    print("=" * 80)
    print("TECHNOVA CUSTOMER SUPPORT AGENT - WITH MEMORY")
    print("=" * 80)
    
    # Scenario 1: Customer starts on email
    print("\n\n📧 SCENARIO 1: Initial Email")
    print("-" * 80)
    msg1 = CustomerMessage(
        channel='email',
        customer_name='Sarah Williams',
        customer_email='sarah@company.com',
        subject='How do I set up integrations?',
        message='Hi, I just signed up for TechNova and I want to integrate it with Slack. Can you help me?'
    )
    resp1 = agent.process_message(msg1)
    print(f"Customer: {msg1.customer_name} ({msg1.customer_email})")
    print(f"Topic ID: {resp1.topic_id}")
    print(f"Category: {resp1.category}")
    print(f"Response preview: {resp1.response_text[:150]}...")
    
    # Scenario 2: Same customer follows up on WhatsApp
    print("\n\n📱 SCENARIO 2: Follow-up on WhatsApp (Same Customer)")
    print("-" * 80)
    msg2 = CustomerMessage(
        channel='whatsapp',
        customer_name='Sarah Williams',
        customer_phone='+1-555-0123',
        message='any update on the slack integration? still not working'
    )
    resp2 = agent.process_message(msg2)
    print(f"Customer: {msg2.customer_name} (same person, different channel)")
    print(f"Topic ID: {resp2.topic_id}")
    print(f"Is Follow-up: {resp2.is_followup}")
    print(f"Context Used: {resp2.context_used}")
    print(f"Response preview: {resp2.response_text[:150]}...")
    
    # Scenario 3: Customer asks about different topic
    print("\n\n📧 SCENARIO 3: New Topic - Pricing")
    print("-" * 80)
    msg3 = CustomerMessage(
        channel='email',
        customer_name='Sarah Williams',
        customer_email='sarah@company.com',
        subject='Enterprise pricing',
        message='What is the pricing for 100 users on Enterprise plan?'
    )
    resp3 = agent.process_message(msg3)
    print(f"Customer: {msg3.customer_name}")
    print(f"Topic ID: {resp3.topic_id}")
    print(f"Category: {resp3.category}")
    print(f"Escalation: {resp3.requires_escalation}")
    print(f"Customer Summary: {agent.get_customer_summary('sarah@company.com')}")
    
    # Scenario 4: Different customer entirely
    print("\n\n📧 SCENARIO 4: Different Customer")
    print("-" * 80)
    msg4 = CustomerMessage(
        channel='email',
        customer_name='John Doe',
        customer_email='john@example.com',
        subject='Bug report',
        message='Dashboard not working, shows blank page'
    )
    resp4 = agent.process_message(msg4)
    print(f"Customer: {msg4.customer_name} ({msg4.customer_email})")
    print(f"Topic ID: {resp4.topic_id}")
    print(f"Category: {resp4.category}")
    
    # Show memory state
    print("\n\n💾 MEMORY STATE")
    print("=" * 80)
    print(f"Total Customers in Memory: {len(agent.memory.customers)}")
    for cid, profile in agent.memory.customers.items():
        print(f"\n  Customer: {cid}")
        print(f"    Name: {profile.name}")
        print(f"    Total Interactions: {profile.total_tickets}")
        print(f"    Open Topics: {profile.open_topics}")
        print(f"    Preferred Channel: {profile.preferred_channel}")
        print(f"    Avg Sentiment: {profile.average_sentiment:.2f}")


if __name__ == "__main__":
    main()
