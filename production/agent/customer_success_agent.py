"""
TechNova Customer Success Agent

Main agent class that orchestrates all tools for customer support.
Implements the complete workflow from discovery doc:
1. Customer Identification
2. Sentiment Analysis
3. Knowledge Retrieval
4. Escalation Decision
5. Channel-Aware Response Generation
"""

import os
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict

from .tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    send_response,
    escalate_to_human,
    SearchKnowledgeBaseInput,
    CreateTicketInput,
    GetCustomerHistoryInput,
    SendResponseInput,
    EscalateToHumanInput,
)

from .prompts import (
    SYSTEM_PROMPT,
    CHANNEL_PROMPTS,
    ESCALATION_RULES,
    RESPONSE_TEMPLATES,
)

from .formatters import (
    ChannelFormatter,
    ResponseFormatter,
    TicketFormatter,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CustomerMessage:
    """Represents an incoming customer message"""
    message: str
    channel: str  # email, whatsapp, web_form
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    subject: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Represents the agent's response"""
    response_text: str
    channel: str
    ticket_id: Optional[str] = None
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None
    priority: str = "P3"
    category: Optional[str] = None
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    kb_articles: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class CustomerProfile:
    """Complete customer profile"""
    customer_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    account_tier: str
    is_vip: bool
    total_tickets: int
    open_tickets: int
    sentiment_trend: str
    preferred_channel: str
    communication_style: str


# ============================================================================
# Main Agent Class
# ============================================================================

class CustomerSuccessAgent:
    """
    TechNova AI Customer Success Agent
    
    Complete workflow:
    1. Identify customer (get history)
    2. Analyze sentiment
    3. Check escalation rules
    4. Search knowledge base
    5. Generate channel-aware response
    6. Send response or escalate
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize agent with configuration
        
        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.system_prompt = SYSTEM_PROMPT
        self.channel_prompts = CHANNEL_PROMPTS
        self.escalation_rules = ESCALATION_RULES
        self.response_templates = RESPONSE_TEMPLATES
        
        # Formatters
        self.channel_formatter = ChannelFormatter()
        self.response_formatter = ResponseFormatter()
        self.ticket_formatter = TicketFormatter()
        
        logger.info("CustomerSuccessAgent initialized")
    
    async def process_message(self, message: CustomerMessage) -> AgentResponse:
        """
        Main entry point - process incoming customer message
        
        Workflow:
        1. Identify customer & get history
        2. Analyze sentiment
        3. Check escalation rules
        4. Search knowledge base
        5. Generate response
        6. Send or escalate
        
        Args:
            message: CustomerMessage object
            
        Returns:
            AgentResponse object
        """
        logger.info(f"Processing message from {message.customer_email or message.customer_phone}")
        
        try:
            # Step 1: Identify customer and get history
            customer_profile = await self._identify_customer(message)
            
            # Step 2: Analyze sentiment (from tools)
            sentiment_result = await self._analyze_sentiment(message.message)
            
            # Step 3: Check escalation rules
            escalation_check = await self._check_escalation(
                message=message.message,
                sentiment=sentiment_result,
                customer_profile=customer_profile
            )
            
            # Step 4: If escalation needed, escalate
            if escalation_check.get('requires_escalation'):
                return await self._handle_escalation(
                    message=message,
                    escalation=escalation_check,
                    customer_profile=customer_profile
                )
            
            # Step 5: Search knowledge base
            kb_results = await self._search_knowledge_base(message.message)
            
            # Step 6: Generate channel-aware response
            response = await self._generate_response(
                message=message,
                sentiment=sentiment_result,
                kb_results=kb_results,
                customer_profile=customer_profile
            )
            
            # Step 7: Send response
            sent_response = await self._send_response(
                message=message,
                response=response,
                kb_results=kb_results
            )
            
            # Build final response
            return AgentResponse(
                response_text=sent_response.response.text,
                channel=message.channel,
                ticket_id=sent_response.ticket_id,
                requires_escalation=False,
                category=response.get('category', 'how_to'),
                sentiment=sentiment_result.get('sentiment', 'neutral'),
                sentiment_score=sentiment_result.get('score', 0.0),
                kb_articles=sent_response.kb_articles_referenced,
                metadata={
                    'customer_id': customer_profile.customer_id if customer_profile else None,
                    'response_time_ms': sent_response.response.character_count,
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            raise
    
    async def _identify_customer(self, message: CustomerMessage) -> Optional[CustomerProfile]:
        """Step 1: Identify customer and retrieve history"""
        try:
            # Try to get customer by email first, then phone
            customer_id = message.customer_email or message.customer_phone
            
            if not customer_id:
                logger.warning("No customer identifier provided")
                return None
            
            # Get customer history
            history_input = GetCustomerHistoryInput(
                customer_email=message.customer_email,
                customer_phone=message.customer_phone,
                limit=10
            )
            
            history_result = await get_customer_history(history_input)
            
            if not history_result or not history_result.customer:
                return None
            
            # Build customer profile
            return CustomerProfile(
                customer_id=history_result.customer.customer_id,
                name=history_result.customer.name,
                email=history_result.customer.email,
                phone=history_result.customer.phone,
                company=history_result.customer.company,
                account_tier=history_result.customer.account_tier,
                is_vip=history_result.customer.is_vip,
                total_tickets=history_result.customer.total_tickets,
                open_tickets=history_result.customer.open_tickets,
                sentiment_trend=history_result.sentiment_trend,
                preferred_channel=history_result.customer.preferred_channel if hasattr(history_result.customer, 'preferred_channel') else message.channel,
                communication_style=history_result.customer.communication_style if hasattr(history_result.customer, 'communication_style') else 'neutral'
            )
            
        except Exception as e:
            logger.error(f"Failed to identify customer: {e}")
            return None
    
    async def _analyze_sentiment(self, message: str) -> Dict:
        """Step 2: Analyze message sentiment"""
        try:
            # Import sentiment analyzer from tools
            from .tools import SentimentAnalyzer
            
            result = SentimentAnalyzer.analyze(message)
            
            return {
                'sentiment': result['sentiment'],
                'score': result['score'],
                'urgency_detected': result.get('urgency_detected', False),
                'anger_detected': result.get('anger_detected', False),
                'recommended_tone': result.get('recommended_tone', 'professional')
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'urgency_detected': False,
                'anger_detected': False,
                'recommended_tone': 'professional'
            }
    
    async def _check_escalation(
        self,
        message: str,
        sentiment: Dict,
        customer_profile: Optional[CustomerProfile]
    ) -> Dict:
        """Step 3: Check if escalation is required"""
        try:
            # Import escalation rules from tools
            from .tools import EscalationRules
            
            result = EscalationRules.check_escalation(message)
            
            if not result or not result.get('requires_escalation'):
                # Check sentiment-based escalation
                if sentiment.get('anger_detected') and sentiment.get('score', 0) < -0.7:
                    return {
                        'requires_escalation': True,
                        'reason': 'Angry customer (sentiment < -0.7)',
                        'priority': 'P1',
                        'route_to': 'Senior Support Agent'
                    }
                
                return {'requires_escalation': False}
            
            # Check VIP escalation
            if customer_profile and customer_profile.is_vip:
                result['priority'] = 'P1'
                result['route_to'] = 'Dedicated Account Manager'
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to check escalation: {e}")
            return {'requires_escalation': False}
    
    async def _search_knowledge_base(self, query: str, limit: int = 5) -> List[Dict]:
        """Step 4: Search knowledge base for relevant articles"""
        try:
            search_input = SearchKnowledgeBaseInput(
                query=query,
                limit=limit,
                min_confidence=0.3
            )
            
            result = await search_knowledge_base(search_input)
            
            if not result or not result.results:
                return []
            
            return [
                {
                    'id': doc.id,
                    'feature': doc.feature,
                    'content': doc.content,
                    'confidence': doc.confidence
                }
                for doc in result.results
            ]
            
        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
            return []
    
    async def _generate_response(
        self,
        message: CustomerMessage,
        sentiment: Dict,
        kb_results: List[Dict],
        customer_profile: Optional[CustomerProfile]
    ) -> Dict:
        """Step 5: Generate channel-aware response"""
        try:
            # Determine category (simple keyword-based for now)
            category = self._classify_intent(message.message)
            
            # Get channel-specific formatting rules
            channel_config = self.channel_formatter.get_channel_config(message.channel)
            
            # Select tone based on sentiment
            tone = self._select_tone(sentiment)
            
            # Build response using templates
            response_text = self.response_formatter.format_response(
                channel=message.channel,
                category=category,
                message=message.message,
                customer_name=message.customer_name or customer_profile.name if customer_profile else None,
                kb_results=kb_results,
                tone=tone,
                channel_config=channel_config
            )
            
            return {
                'text': response_text,
                'category': category,
                'tone': tone,
                'channel': message.channel
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            # Fallback response
            return {
                'text': f"Thank you for contacting us. We'll get back to you shortly regarding: {message.subject or message.message[:50]}",
                'category': 'default',
                'tone': 'professional',
                'channel': message.channel
            }
    
    def _classify_intent(self, message: str) -> str:
        """Classify message intent into category"""
        message_lower = message.lower()
        
        # Priority checks (escalation keywords)
        if any(word in message_lower for word in ['refund', 'charged', 'billing', 'payment']):
            return 'billing'
        
        if any(word in message_lower for word in ['gdpr', 'hipaa', 'compliance', 'legal']):
            return 'compliance'
        
        if any(word in message_lower for word in ['cancel', 'close account', 'leaving']):
            return 'cancellation'
        
        # Technical issues
        if any(word in message_lower for word in ['bug', 'error', 'not working', 'broken', 'issue']):
            return 'technical_issue'
        
        # Feature requests
        if any(word in message_lower for word in ['feature', 'request', 'roadmap', 'suggest']):
            return 'feature_inquiry'
        
        # How-to questions
        if any(word in message_lower for word in ['how', 'help', 'guide', 'tutorial', 'steps']):
            return 'how_to'
        
        # Sales inquiries
        if any(word in message_lower for word in ['pricing', 'enterprise', 'demo', 'sales']):
            return 'sales'
        
        # Default
        return 'how_to'
    
    def _select_tone(self, sentiment: Dict) -> str:
        """Select response tone based on sentiment"""
        score = sentiment.get('score', 0)
        
        if sentiment.get('anger_detected') or score < -0.7:
            return 'empathetic'
        elif score < -0.3:
            return 'empathetic'
        elif score > 0.5:
            return 'friendly'
        else:
            return 'professional'
    
    async def _send_response(
        self,
        message: CustomerMessage,
        response: Dict,
        kb_results: List[Dict]
    ) -> Any:
        """Step 6: Send response to customer"""
        try:
            # First create ticket
            ticket_input = CreateTicketInput(
                customer_email=message.customer_email or "",
                customer_name=message.customer_name,
                channel=message.channel,
                subject=message.subject or f"Support Request - {message.message[:50]}",
                message=message.message
            )
            
            ticket_result = await create_ticket(ticket_input)
            ticket_id = ticket_result.ticket.ticket_id if ticket_result else None
            
            # Send response
            response_input = SendResponseInput(
                customer_email=message.customer_email or "",
                channel=message.channel,
                message=message.message,
                category=response.get('category', 'how_to'),
                customer_name=message.customer_name,
                ticket_id=ticket_id,
                is_followup=False
            )
            
            sent_result = await send_response(response_input)
            
            return sent_result
            
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
            raise
    
    async def _handle_escalation(
        self,
        message: CustomerMessage,
        escalation: Dict,
        customer_profile: Optional[CustomerProfile]
    ) -> AgentResponse:
        """Handle escalation to human agent"""
        try:
            # Create ticket first
            ticket_input = CreateTicketInput(
                customer_email=message.customer_email or "",
                customer_name=message.customer_name,
                channel=message.channel,
                subject=f"[ESCALATION] {message.subject or message.message[:50]}",
                message=message.message
            )
            
            ticket_result = await create_ticket(ticket_input)
            ticket_id = ticket_result.ticket.ticket_id if ticket_result else None
            
            # Escalate
            escalate_input = EscalateToHumanInput(
                ticket_id=ticket_id or "",
                reason=escalation.get('reason', 'Customer requires human assistance'),
                priority=escalation.get('priority', 'P2'),
                notes=f"Customer: {customer_profile.name if customer_profile else 'Unknown'}\nChannel: {message.channel}",
                customer_email=message.customer_email
            )
            
            escalate_result = await escalate_to_human(escalate_input)
            
            # Build escalation response for customer
            response_text = self._build_escalation_response(
                channel=message.channel,
                escalation=escalation,
                ticket_id=ticket_id
            )
            
            return AgentResponse(
                response_text=response_text,
                channel=message.channel,
                ticket_id=ticket_id,
                requires_escalation=True,
                escalation_reason=escalation.get('reason'),
                priority=escalation.get('priority', 'P2'),
                category='escalation',
                metadata={
                    'routed_to': escalate_result.escalation.routed_to if escalate_result else 'Support Team',
                    'sla': escalate_result.escalation.sla_response_time if escalate_result else '24 hours'
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to handle escalation: {e}")
            raise
    
    def _build_escalation_response(self, channel: str, escalation: Dict, ticket_id: str) -> str:
        """Build customer-facing escalation response"""
        channel_config = self.channel_formatter.get_channel_config(channel)
        
        if channel == 'whatsapp':
            return f"""Hi! I'm escalating this to our {escalation.get('route_to', 'specialist team')}. 

They'll contact you within {escalation.get('sla_hours', '24')} hours.

Ticket ID: `{ticket_id}`"""
        
        elif channel == 'email':
            return f"""Dear Valued Customer,

Thank you for contacting TechNova Support.

I've reviewed your request and I'm escalating this to our {escalation.get('route_to', 'specialist team')} to ensure you receive the best assistance.

**What happens next:**
- A specialist will review your case
- You'll receive a response within {escalation.get('sla_hours', '24')} hours
- Reference your Ticket ID: {ticket_id}

We appreciate your patience and will resolve this promptly.

Best regards,
TechNova Support Team"""
        
        else:  # web_form
            return f"""Hi,

Your request has been escalated to our {escalation.get('route_to', 'specialist team')}.

**Ticket ID:** {ticket_id}
**Expected Response:** Within {escalation.get('sla_hours', '24')} hours

We'll contact you soon.

Best,
TechNova Support"""


# ============================================================================
# Agent Factory
# ============================================================================

def create_agent(config: Optional[Dict] = None) -> CustomerSuccessAgent:
    """
    Factory function to create configured agent instance
    
    Args:
        config: Optional configuration
        
    Returns:
        CustomerSuccessAgent instance
    """
    return CustomerSuccessAgent(config=config)


# ============================================================================
# Usage Example
# ============================================================================

"""
from agent.customer_success_agent import create_agent, CustomerMessage

# Create agent
agent = create_agent()

# Create customer message
message = CustomerMessage(
    message="How do I integrate with Slack?",
    channel="email",
    customer_email="john@example.com",
    customer_name="John Doe",
    subject="Slack Integration Help"
)

# Process message
response = await agent.process_message(message)

print(f"Response: {response.response_text}")
print(f"Ticket ID: {response.ticket_id}")
print(f"Escalation: {response.requires_escalation}")
"""
