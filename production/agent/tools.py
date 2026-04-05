"""
TechNova Customer Support - OpenAI Agents SDK Tools

MCP tools converted to OpenAI Agents SDK @function_tool format.
Features:
- Pydantic BaseModel for input/output validation
- Comprehensive error handling
- PostgreSQL + pgvector semantic search
- Channel-aware response generation
- Escalation decision engine
"""

import os
import json
import re
import uuid
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, validator
from openai.agents import function_tool

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Application configuration"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/technova")
    PGVECTOR_DIMENSION = int(os.getenv("PGVECTOR_DIMENSION", "1536"))  # OpenAI embedding dimension
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MAX_KB_RESULTS = int(os.getenv("MAX_KB_RESULTS", "5"))
    ENABLE_ESCALATION = os.getenv("ENABLE_ESCALATION", "true").lower() == "true"


# ============================================================================
# Enums
# ============================================================================

class Channel(str, Enum):
    """Supported communication channels"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class Priority(str, Enum):
    """Ticket priority levels"""
    P0 = "P0"  # Critical - 15 min response
    P1 = "P1"  # High - 1 hour response
    P2 = "P2"  # Medium - 4 hours response
    P3 = "P3"  # Low - 24 hours response


class Category(str, Enum):
    """Message categories"""
    HOW_TO = "how_to"
    TECHNICAL_ISSUE = "technical_issue"
    FEATURE_INQUIRY = "feature_inquiry"
    BILLING = "billing"
    ESCALATION = "escalation"
    BUG_REPORT = "bug_report"
    COMPLIANCE = "compliance"
    CANCELLATION = "cancellation"
    SALES = "sales"
    ACCOUNT = "account"


class SentimentType(str, Enum):
    """Sentiment types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    URGENT = "urgent"
    ANGRY = "angry"
    FRUSTRATED = "frustrated"


class ResolutionStatus(str, Enum):
    """Ticket resolution status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


# ============================================================================
# Pydantic Models - Inputs
# ============================================================================

class SearchKnowledgeBaseInput(BaseModel):
    """Input for knowledge base search"""
    query: str = Field(..., description="Search query for product documentation")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of results (1-20)")
    category: Optional[str] = Field(default=None, description="Filter by document category")
    min_confidence: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum confidence score")


class CreateTicketInput(BaseModel):
    """Input for creating a support ticket"""
    customer_email: str = Field(..., description="Customer email address")
    customer_name: Optional[str] = Field(default=None, description="Customer name")
    customer_phone: Optional[str] = Field(default=None, description="Customer phone number")
    channel: str = Field(..., description="Communication channel (email, whatsapp, web_form)")
    subject: str = Field(..., description="Ticket subject line")
    message: str = Field(..., description="Customer message content")
    company: Optional[str] = Field(default=None, description="Customer company name")


class GetCustomerHistoryInput(BaseModel):
    """Input for retrieving customer history"""
    customer_email: Optional[str] = Field(default=None, description="Customer email")
    customer_phone: Optional[str] = Field(default=None, description="Customer phone")
    customer_id: Optional[str] = Field(default=None, description="Customer ID")
    limit: int = Field(default=20, ge=1, le=100, description="Number of tickets to retrieve")


class SendResponseInput(BaseModel):
    """Input for sending customer response"""
    customer_email: str = Field(..., description="Customer email address")
    channel: str = Field(..., description="Communication channel")
    message: str = Field(..., description="Original customer message")
    category: str = Field(..., description="Message category")
    customer_name: Optional[str] = Field(default=None, description="Customer name")
    ticket_id: Optional[str] = Field(default=None, description="Associated ticket ID")
    is_followup: bool = Field(default=False, description="Whether this is a follow-up message")
    sentiment: Optional[str] = Field(default="neutral", description="Customer sentiment")


class EscalateToHumanInput(BaseModel):
    """Input for escalating to human agent"""
    ticket_id: str = Field(..., description="Ticket ID to escalate")
    reason: str = Field(..., description="Reason for escalation")
    priority: str = Field(default="P2", description="Escalation priority (P0-P3)")
    notes: Optional[str] = Field(default=None, description="Additional notes for human agent")
    customer_email: Optional[str] = Field(default=None, description="Customer email")


# ============================================================================
# Pydantic Models - Outputs
# ============================================================================

class KBDocument(BaseModel):
    """Knowledge base document result"""
    id: str
    feature: str
    content: str
    category: Optional[str]
    confidence: float
    metadata: Dict[str, Any]


class SearchKnowledgeBaseOutput(BaseModel):
    """Output from knowledge base search"""
    query: str
    results: List[KBDocument]
    count: int
    search_time_ms: float
    used_semantic: bool


class TicketInfo(BaseModel):
    """Ticket information"""
    ticket_id: str
    customer_id: str
    channel: str
    subject: str
    message: str
    category: str
    priority: str
    status: str
    created_at: str
    assigned_to: Optional[str]


class CustomerProfile(BaseModel):
    """Customer profile information"""
    customer_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    account_tier: str
    is_vip: bool
    total_tickets: int
    open_tickets: int


class CreateTicketOutput(BaseModel):
    """Output from ticket creation"""
    ticket: TicketInfo
    customer: CustomerProfile
    escalation_required: bool
    escalation_reason: Optional[str]
    assigned_team: str


class ConversationTurn(BaseModel):
    """Single conversation turn"""
    timestamp: str
    channel: str
    message: str
    response: str
    category: str
    sentiment: str


class CustomerHistoryOutput(BaseModel):
    """Output from customer history retrieval"""
    customer: CustomerProfile
    tickets: List[ConversationTurn]
    statistics: Dict[str, Any]
    sentiment_trend: str


class ResponseInfo(BaseModel):
    """Response information"""
    text: str
    channel: str
    character_count: int
    word_count: int
    tone: str
    template_used: str


class SendResponseOutput(BaseModel):
    """Output from response generation"""
    response: ResponseInfo
    ticket_id: Optional[str]
    requires_followup: bool
    kb_articles_referenced: List[str]


class EscalationInfo(BaseModel):
    """Escalation information"""
    ticket_id: str
    escalated: bool
    routed_to: str
    priority: str
    sla_response_time: str
    escalation_reason: str


class EscalateToHumanOutput(BaseModel):
    """Output from escalation"""
    escalation: EscalationInfo
    handoff_summary: str
    next_steps: List[str]


# ============================================================================
# Database Connection Manager
# ============================================================================

class DatabaseManager:
    """PostgreSQL connection manager with pgvector support"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._connection = None

    def get_connection(self):
        """Get database connection"""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(self.database_url)
                # Register pgvector extension
                with self._connection.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self._connection.commit()
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise
        return self._connection

    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None


# Global database manager instance
db_manager = DatabaseManager(Config.DATABASE_URL)


# ============================================================================
# Knowledge Base Service
# ============================================================================

class KnowledgeBaseService:
    """Knowledge base service with pgvector semantic search"""

    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """Get OpenAI embedding for text"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []  # Fallback to keyword search

    @staticmethod
    def semantic_search(query: str, limit: int = 5, min_confidence: float = 0.3) -> List[Dict]:
        """Semantic search using pgvector"""
        conn = None
        try:
            conn = db_manager.get_connection()
            query_embedding = KnowledgeBaseService.get_embedding(query)

            if not query_embedding:
                # Fallback to keyword search
                return KnowledgeBaseService.keyword_search(query, limit)

            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Cosine similarity search
                cur.execute("""
                    SELECT 
                        id,
                        feature,
                        content,
                        category,
                        1 - (embedding <=> %s::vector) as confidence,
                        metadata
                    FROM knowledge_base
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY confidence DESC
                    LIMIT %s
                """, (embedding_str, embedding_str, min_confidence, limit))

                results = cur.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            # Fallback to keyword search
            return KnowledgeBaseService.keyword_search(query, limit)
        finally:
            if conn:
                conn.close()

    @staticmethod
    def keyword_search(query: str, limit: int = 5) -> List[Dict]:
        """Fallback keyword-based search"""
        conn = None
        try:
            conn = db_manager.get_connection()
            query_lower = query.lower()

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id,
                        feature,
                        content,
                        category,
                        metadata,
                        ts_rank(to_tsvector('english', feature || ' ' || content) 
                               , plainto_tsquery('english', %s)) as confidence
                    FROM knowledge_base
                    WHERE to_tsvector('english', feature || ' ' || content) 
                          @@ plainto_tsquery('english', %s)
                    ORDER BY confidence DESC
                    LIMIT %s
                """, (query_lower, query_lower, limit))

                results = cur.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
        finally:
            if conn:
                conn.close()


# ============================================================================
# Escalation Rules Engine
# ============================================================================

class EscalationRules:
    """Escalation decision engine"""

    RULES = [
        {
            'id': 1,
            'name': 'Pricing & Enterprise Sales',
            'keywords': ['enterprise', 'pricing', 'quote', 'contract', 'volume discount',
                        '50+ users', '100+ users', 'custom pricing', 'negotiate', 'price'],
            'priority': Priority.P1.value,
            'route_to': 'Sales Team (Enterprise)',
            'sla_hours': 1
        },
        {
            'id': 2,
            'name': 'Refund & Billing Disputes',
            'keywords': ['refund', 'charged twice', 'billing error', 'payment failed',
                        'overcharged', 'dispute', 'chargeback', 'double charge'],
            'priority': Priority.P1.value,
            'route_to': 'Billing Specialist',
            'sla_hours': 1
        },
        {
            'id': 3,
            'name': 'Legal & Compliance',
            'keywords': ['gdpr', 'hipaa', 'soc 2', 'compliance', 'legal', 'baa',
                        'data processing', 'audit', 'lawsuit', 'attorney', 'subpoena'],
            'priority': Priority.P0.value,
            'route_to': 'Legal & Compliance Team',
            'sla_hours': 0.25  # 15 minutes
        },
        {
            'id': 4,
            'name': 'Angry/Threatening Customers',
            'keywords': ['cancel immediately', 'worst service', 'unacceptable', 'useless',
                        'threaten', 'lawyer', 'sue', 'review bomb'],
            'priority': Priority.P1.value,
            'route_to': 'Senior Support Agent / Team Lead',
            'sla_hours': 1
        },
        {
            'id': 5,
            'name': 'System-wide Technical Bugs',
            'keywords': ['not working', 'broken', 'outage', 'down', 'all users',
                        'everyone', 'system-wide', 'critical bug'],
            'priority': Priority.P0.value,
            'route_to': 'Engineering Team',
            'sla_hours': 0.25
        },
        {
            'id': 6,
            'name': 'Data Loss or Security Breach',
            'keywords': ['data lost', 'missing data', 'hacked', 'unauthorized access',
                        'security breach', 'account compromised', 'deleted permanently'],
            'priority': Priority.P0.value,
            'route_to': 'Security Team + Engineering Lead',
            'sla_hours': 0.25
        },
        {
            'id': 7,
            'name': 'VIP Customer',
            'keywords': ['enterprise plan', 'vip', 'premium'],
            'priority': Priority.P1.value,
            'route_to': 'Dedicated Account Manager',
            'sla_hours': 1
        },
        {
            'id': 8,
            'name': 'API & Integration Support',
            'keywords': ['api', 'webhook', 'integration', 'developer', 'custom code',
                        'rest', 'sdk', 'rate limit', 'authentication error'],
            'priority': Priority.P2.value,
            'route_to': 'Developer Support / Integration Specialist',
            'sla_hours': 4
        },
        {
            'id': 9,
            'name': 'Account Cancellation',
            'keywords': ['cancel', 'close account', 'stop subscription', 'leaving',
                        'switching to competitor'],
            'priority': Priority.P2.value,
            'route_to': 'Retention Specialist',
            'sla_hours': 4
        },
        {
            'id': 10,
            'name': 'Feature Requests',
            'keywords': ['feature request', 'roadmap', 'when will', 'add feature',
                        'suggestion', 'product idea', 'custom development'],
            'priority': Priority.P3.value,
            'route_to': 'Product Management Team',
            'sla_hours': 24
        }
    ]

    @classmethod
    def check_escalation(cls, message: str, customer_tier: str = "basic") -> Optional[Dict]:
        """Check if message requires escalation"""
        message_lower = message.lower()
        matched_rules = []

        for rule in cls.RULES:
            for keyword in rule['keywords']:
                if keyword.lower() in message_lower:
                    matched_rules.append(rule)
                    break

        if not matched_rules:
            return None

        # Prioritize by severity (P0 > P1 > P2 > P3)
        priority_order = {Priority.P0.value: 0, Priority.P1.value: 1, 
                         Priority.P2.value: 2, Priority.P3.value: 3}
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
# Sentiment Analyzer
# ============================================================================

class SentimentAnalyzer:
    """Advanced sentiment analysis"""

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
        """Analyze sentiment of message"""
        message_lower = message.lower()
        words = re.findall(r'\b\w+\b', message_lower)

        positive_score = sum(cls.POSITIVE_WORDS.get(word, 0) for word in words)
        negative_score = sum(cls.NEGATIVE_WORDS.get(word, 0) for word in words)
        urgency_score = sum(score for indicator, score in cls.URGENCY_INDICATORS.items() 
                           if indicator in message_lower)

        # Check for multi-word anger indicators
        anger_score = sum(-0.5 for indicator in cls.ANGER_INDICATORS 
                         if indicator in message_lower)

        total_sentiment = positive_score + negative_score + urgency_score + anger_score

        # Normalize score to -1.0 to 1.0 range
        normalized_score = max(-1.0, min(1.0, total_sentiment / max(1, len(words) * 0.1)))

        # Determine sentiment type
        if any(indicator in message_lower for indicator in ['urgent', 'asap', 'emergency']):
            sentiment_type = SentimentType.URGENT.value
        elif anger_score < -0.5:
            sentiment_type = SentimentType.ANGRY.value
        elif negative_score < -1.0:
            sentiment_type = SentimentType.FRustrated.value
        elif normalized_score > 0.3:
            sentiment_type = SentimentType.POSITIVE.value
        elif normalized_score < -0.3:
            sentiment_type = SentimentType.NEGATIVE.value
        else:
            sentiment_type = SentimentType.NEUTRAL.value

        return {
            'sentiment': sentiment_type,
            'score': round(normalized_score, 3),
            'positive_indicators': [w for w in words if w in cls.POSITIVE_WORDS],
            'negative_indicators': [w for w in words if w in cls.NEGATIVE_WORDS],
            'urgency_detected': urgency_score < 0,
            'anger_detected': anger_score < -0.3
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

    @classmethod
    def generate(cls, channel: str, category: str, message: str,
                 customer_name: Optional[str] = None,
                 kb_results: Optional[List[Dict]] = None,
                 is_followup: bool = False,
                 context: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response based on channel, category, and context"""

        # Get template
        template_dict = cls.TEMPLATES.get(category, cls.TEMPLATES[Category.DEFAULT.value])
        template = template_dict.get(channel, template_dict[Channel.EMAIL.value])

        # Prepare variables
        name = customer_name.split()[0] if customer_name else "there"
        topic = cls._extract_topic(message)

        # Get steps from KB
        if kb_results and len(kb_results) > 0:
            steps = cls._format_steps(kb_results, channel)
            action_text = cls._generate_action_text(category, channel, kb_results)
            feature_name = kb_results[0]['feature']
            explanation = kb_results[0]['content'][:300]
            kb_articles = [kb_results[0]['feature']]
        else:
            steps = cls._get_generic_steps(category, channel)
            action_text = cls._get_generic_action_text(category, channel)
            feature_name = "this feature"
            explanation = "This feature helps you manage your projects."
            kb_articles = []

        # Fill template
        response_text = template.format(
            name=name,
            topic=topic,
            steps=steps.get('long', ''),
            action_text=action_text,
            explanation=explanation,
            topic_slug=topic.replace(' ', '-').lower()[:50],
            feature_name=feature_name
        )

        # Calculate metrics
        word_count = len(response_text.split())
        char_count = len(response_text)

        # Determine tone
        tone_map = {
            Category.HOW_TO.value: "helpful",
            Category.TECHNICAL_ISSUE.value: "empathetic",
            Category.DEFAULT.value: "professional"
        }
        tone = tone_map.get(category, "professional")

        return {
            'text': response_text,
            'channel': channel,
            'character_count': char_count,
            'word_count': word_count,
            'tone': tone,
            'template_used': f"{channel}-{category}",
            'kb_articles_referenced': kb_articles
        }

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
        if not kb_results:
            return cls._get_generic_action_text(category, channel)

        doc = kb_results[0]
        content = doc['content']

        if channel == Channel.WHATSAPP.value:
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
# OpenAI Agents SDK Tools
# ============================================================================

@function_tool
async def search_knowledge_base(input: SearchKnowledgeBaseInput) -> SearchKnowledgeBaseOutput:
    """
    Search the TechNova knowledge base for product documentation and guides.
    
    Use this tool when:
    - Customer asks about features or functionality
    - You need to provide step-by-step instructions
    - Customer needs documentation or guides
    
    Returns semantically-relevant documents using pgvector embeddings.
    """
    start_time = datetime.now()
    
    try:
        # Perform semantic search with pgvector
        results = KnowledgeBaseService.semantic_search(
            query=input.query,
            limit=input.limit,
            min_confidence=input.min_confidence
        )

        # Convert to output format
        kb_documents = [
            KBDocument(
                id=str(doc['id']),
                feature=doc['feature'],
                content=doc['content'][:500],  # Truncate long content
                category=doc.get('category'),
                confidence=float(doc['confidence']),
                metadata=doc.get('metadata', {})
            )
            for doc in results
        ]

        search_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        used_semantic = len(results) > 0 and 'confidence' in results[0]

        return SearchKnowledgeBaseOutput(
            query=input.query,
            results=kb_documents,
            count=len(kb_documents),
            search_time_ms=round(search_time_ms, 2),
            used_semantic=used_semantic
        )

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return SearchKnowledgeBaseOutput(
            query=input.query,
            results=[],
            count=0,
            search_time_ms=0,
            used_semantic=False
        )


@function_tool
async def create_ticket(input: CreateTicketInput) -> CreateTicketOutput:
    """
    Create a new support ticket in the system.
    
    Use this tool when:
    - Customer initiates a new support request
    - You need to track a customer issue
    - Escalation is required
    
    Automatically categorizes the ticket and checks for escalation.
    """
    conn = None
    try:
        conn = db_manager.get_connection()
        customer_id = input.customer_email.lower() if input.customer_email else f"anon:{uuid.uuid4().hex[:8]}"

        # Analyze sentiment
        sentiment_result = SentimentAnalyzer.analyze(input.message)

        # Check escalation
        escalation_result = EscalationRules.check_escalation(input.message)

        # Determine category (simple keyword-based for now)
        category = Category.HOW_TO.value
        message_lower = input.message.lower()
        if any(word in message_lower for word in ['bug', 'error', 'broken', 'not working']):
            category = Category.BUG_REPORT.value
        elif any(word in message_lower for word in ['billing', 'refund', 'charge', 'payment']):
            category = Category.BILLING.value
        elif any(word in message_lower for word in ['feature', 'request', 'roadmap']):
            category = Category.FEATURE_INQUIRY.value
        elif any(word in message_lower for word in ['gdpr', 'hipaa', 'compliance', 'legal']):
            category = Category.COMPLIANCE.value

        # Determine priority
        priority = Priority.P3.value
        if escalation_result:
            priority = escalation_result['priority']
        elif sentiment_result['sentiment'] in [SentimentType.ANGRY.value, SentimentType.URGENT.value]:
            priority = Priority.P2.value

        # Insert ticket into database
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Ensure customer exists
            cur.execute("""
                INSERT INTO customers (customer_id, email, name, phone, company, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (customer_id) DO UPDATE SET 
                    name = EXCLUDED.name,
                    phone = EXCLUDED.phone,
                    company = EXCLUDED.company
                RETURNING customer_id
            """, (
                customer_id,
                input.customer_email,
                input.customer_name,
                input.customer_phone,
                input.company
            ))
            customer_row = cur.fetchone()

            # Create ticket
            ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
            cur.execute("""
                INSERT INTO tickets 
                (ticket_id, customer_id, channel, subject, message, category, priority, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING *
            """, (
                ticket_id,
                customer_id,
                input.channel,
                input.subject,
                input.message,
                category,
                priority,
                ResolutionStatus.OPEN.value
            ))
            ticket_row = cur.fetchone()

            # Get customer stats
            cur.execute("""
                SELECT 
                    COUNT(*) as total_tickets,
                    COUNT(*) FILTER (WHERE status != 'resolved') as open_tickets
                FROM tickets
                WHERE customer_id = %s
            """, (customer_id,))
            stats = cur.fetchone()

        conn.commit()

        # Build output
        ticket_info = TicketInfo(
            ticket_id=ticket_row['ticket_id'],
            customer_id=ticket_row['customer_id'],
            channel=ticket_row['channel'],
            subject=ticket_row['subject'],
            message=ticket_row['message'],
            category=ticket_row['category'],
            priority=ticket_row['priority'],
            status=ticket_row['status'],
            created_at=ticket_row['created_at'].isoformat(),
            assigned_to=ticket_row.get('assigned_to')
        )

        customer_profile = CustomerProfile(
            customer_id=customer_id,
            name=input.customer_name or "Unknown",
            email=input.customer_email,
            phone=input.customer_phone,
            company=input.company,
            account_tier="basic",  # Would lookup from DB
            is_vip=False,
            total_tickets=stats['total_tickets'],
            open_tickets=stats['open_tickets']
        )

        return CreateTicketOutput(
            ticket=ticket_info,
            customer=customer_profile,
            escalation_required=escalation_result is not None,
            escalation_reason=escalation_result['reason'] if escalation_result else None,
            assigned_team=escalation_result['route_to'] if escalation_result else "Support Team"
        )

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


@function_tool
async def get_customer_history(input: GetCustomerHistoryInput) -> CustomerHistoryOutput:
    """
    Retrieve customer conversation history and profile.
    
    Use this tool when:
    - You need context about previous interactions
    - Customer contacts support again
    - Understanding customer sentiment trends
    
    Returns full conversation history and customer statistics.
    """
    conn = None
    try:
        conn = db_manager.get_connection()

        # Determine customer ID
        customer_id = None
        if input.customer_email:
            customer_id = input.customer_email.lower()
        elif input.customer_phone:
            customer_id = f"phone:{input.customer_phone}"
        elif input.customer_id:
            customer_id = input.customer_id

        if not customer_id:
            raise ValueError("Must provide email, phone, or customer_id")

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get customer profile
            cur.execute("""
                SELECT 
                    customer_id, name, email, phone, company,
                    account_tier, is_vip, created_at
                FROM customers
                WHERE customer_id = %s
            """, (customer_id,))
            customer_row = cur.fetchone()

            if not customer_row:
                # Create minimal profile
                customer_profile = CustomerProfile(
                    customer_id=customer_id,
                    name="Unknown",
                    email=input.customer_email,
                    phone=input.customer_phone,
                    company=None,
                    account_tier="basic",
                    is_vip=False,
                    total_tickets=0,
                    open_tickets=0
                )
                return CustomerHistoryOutput(
                    customer=customer_profile,
                    tickets=[],
                    statistics={'total_tickets': 0, 'open_tickets': 0, 'resolved_tickets': 0},
                    sentiment_trend="neutral"
                )

            # Get recent tickets
            cur.execute("""
                SELECT 
                    ticket_id, channel, message, response, category, 
                    sentiment, sentiment_score, created_at
                FROM tickets
                WHERE customer_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (customer_id, input.limit))
            ticket_rows = cur.fetchall()

            # Get statistics
            cur.execute("""
                SELECT 
                    COUNT(*) as total_tickets,
                    COUNT(*) FILTER (WHERE status != 'resolved') as open_tickets,
                    COUNT(*) FILTER (WHERE status = 'resolved') as resolved_tickets,
                    AVG(sentiment_score) as avg_sentiment
                FROM tickets
                WHERE customer_id = %s
            """, (customer_id,))
            stats_row = cur.fetchone()

        # Convert tickets to conversation turns
        conversation_turns = [
            ConversationTurn(
                timestamp=row['created_at'].isoformat(),
                channel=row['channel'],
                message=row['message'],
                response=row.get('response', ''),
                category=row['category'],
                sentiment=row.get('sentiment', 'neutral')
            )
            for row in ticket_rows
        ]

        # Determine sentiment trend
        avg_sentiment = stats_row['avg_sentiment'] or 0
        if avg_sentiment > 0.3:
            sentiment_trend = "positive"
        elif avg_sentiment < -0.3:
            sentiment_trend = "negative"
        else:
            sentiment_trend = "neutral"

        customer_profile = CustomerProfile(
            customer_id=customer_row['customer_id'],
            name=customer_row['name'],
            email=customer_row.get('email'),
            phone=customer_row.get('phone'),
            company=customer_row.get('company'),
            account_tier=customer_row.get('account_tier', 'basic'),
            is_vip=customer_row.get('is_vip', False),
            total_tickets=stats_row['total_tickets'],
            open_tickets=stats_row['open_tickets']
        )

        return CustomerHistoryOutput(
            customer=customer_profile,
            tickets=conversation_turns,
            statistics={
                'total_tickets': stats_row['total_tickets'],
                'open_tickets': stats_row['open_tickets'],
                'resolved_tickets': stats_row['resolved_tickets'],
                'avg_sentiment': round(avg_sentiment, 3)
            },
            sentiment_trend=sentiment_trend
        )

    except Exception as e:
        logger.error(f"Customer history retrieval failed: {e}")
        raise
    finally:
        if conn:
            conn.close()


@function_tool
async def send_response(input: SendResponseInput) -> SendResponseOutput:
    """
    Generate and send a channel-aware response to the customer.
    
    Use this tool when:
    - You need to respond to a customer message
    - Response should match channel format (email/whatsapp/web_form)
    - Including knowledge base articles in response
    
    Automatically adapts tone, length, and formatting to the channel.
    """
    try:
        # Search knowledge base for context
        kb_results = KnowledgeBaseService.semantic_search(
            query=input.message,
            limit=3,
            min_confidence=0.3
        )

        # Generate response
        response_data = ResponseGenerator.generate(
            channel=input.channel,
            category=input.category,
            message=input.message,
            customer_name=input.customer_name,
            kb_results=kb_results,
            is_followup=input.is_followup
        )

        # Determine if followup needed
        requires_followup = input.category in [
            Category.TECHNICAL_ISSUE.value, 
            Category.BUG_REPORT.value
        ]

        return SendResponseOutput(
            response=ResponseInfo(**response_data),
            ticket_id=input.ticket_id,
            requires_followup=requires_followup,
            kb_articles_referenced=response_data['kb_articles_referenced']
        )

    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        raise


@function_tool
async def escalate_to_human(input: EscalateToHumanInput) -> EscalateToHumanOutput:
    """
    Escalate a ticket to a human support agent.
    
    Use this tool when:
    - Customer requests human agent
    - Issue exceeds AI capabilities
    - Billing/legal/security issues
    - Angry/frustrated customer
    
    Routes to appropriate team based on escalation rules.
    """
    conn = None
    try:
        conn = db_manager.get_connection()

        # Get ticket details
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT t.*, c.name as customer_name, c.email as customer_email
                FROM tickets t
                JOIN customers c ON t.customer_id = c.customer_id
                WHERE t.ticket_id = %s
            """, (input.ticket_id,))
            ticket_row = cur.fetchone()

            if not ticket_row:
                raise ValueError(f"Ticket {input.ticket_id} not found")

            # Update ticket status
            cur.execute("""
                UPDATE tickets
                SET 
                    status = %s,
                    priority = %s,
                    updated_at = NOW()
                WHERE ticket_id = %s
                RETURNING *
            """, (ResolutionStatus.ESCALATED.value, input.priority, input.ticket_id))
            updated_ticket = cur.fetchone()

        conn.commit()

        # Determine routing
        escalation_result = EscalationRules.check_escalation(
            ticket_row['message'] + " " + (input.reason or "")
        )

        if escalation_result:
            routed_to = escalation_result['route_to']
            sla_hours = escalation_result['sla_hours']
        else:
            routed_to = "Support Team"
            sla_hours = 24

        # Calculate SLA deadline
        from datetime import timedelta
        sla_deadline = datetime.now() + timedelta(hours=sla_hours)

        # Generate handoff summary
        handoff_summary = f"""
TICKET ESCALATION SUMMARY
=========================
Ticket ID: {input.ticket_id}
Customer: {ticket_row['customer_name']} ({ticket_row['customer_email']})
Channel: {ticket_row['channel']}
Priority: {input.priority}

ISSUE:
{ticket_row['message'][:300]}

ESCALATION REASON:
{input.reason}

ADDITIONAL NOTES:
{input.notes or 'None'}

SENTIMENT: {SentimentAnalyzer.analyze(ticket_row['message'])['sentiment']}
        """.strip()

        escalation_info = EscalationInfo(
            ticket_id=input.ticket_id,
            escalated=True,
            routed_to=routed_to,
            priority=input.priority,
            sla_response_time=f"{sla_hours} hours",
            escalation_reason=input.reason
        )

        next_steps = [
            f"Contact customer within {sla_hours} hours",
            "Review full conversation history",
            f"Route to {routed_to} queue",
            "Update ticket with resolution"
        ]

        return EscalateToHumanOutput(
            escalation=escalation_info,
            handoff_summary=handoff_summary,
            next_steps=next_steps
        )

    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


# ============================================================================
# Tool Registry
# ============================================================================

# List of all available tools for OpenAI Agents SDK
ALL_TOOLS = [
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    send_response,
    escalate_to_human
]

TOOL_DESCRIPTIONS = {
    "search_knowledge_base": "Search product documentation using semantic search",
    "create_ticket": "Create and track support tickets",
    "get_customer_history": "Retrieve customer profile and conversation history",
    "send_response": "Generate channel-aware customer responses",
    "escalate_to_human": "Escalate tickets to human agents"
}


# ============================================================================
# Database Schema (for reference)
# ============================================================================

"""
-- PostgreSQL schema with pgvector support

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE customers (
    customer_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    account_tier VARCHAR(50) DEFAULT 'basic',
    is_vip BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    feature VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    embedding vector(1536),  -- OpenAI embeddings
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kb_embedding ON knowledge_base 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE TABLE tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(255) REFERENCES customers(customer_id),
    channel VARCHAR(50) NOT NULL,
    subject VARCHAR(500),
    message TEXT NOT NULL,
    response TEXT,
    category VARCHAR(100),
    sentiment VARCHAR(50),
    sentiment_score FLOAT,
    priority VARCHAR(10) DEFAULT 'P3',
    status VARCHAR(50) DEFAULT 'open',
    assigned_to VARCHAR(255),
    escalation_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_created ON tickets(created_at DESC);
"""
