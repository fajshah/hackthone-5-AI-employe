"""
TechNova Customer Support - Message Processor Worker

Kafka-based message processor that:
1. Consumes messages from Kafka topics (email, whatsapp, web_form)
2. Resolves customer identity (email/phone lookup)
3. Manages conversations (create/update threads)
4. Calls agent.run() for processing
5. Delivers responses via appropriate channel
6. Logs all interactions

Architecture:
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Kafka     │────▶│ MessageProcessor │────▶│    Agent    │
│  (Topics)   │     │   (This Worker)  │     │  (Agent)    │
└─────────────┘     └──────────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Database   │
                    │ (PostgreSQL)│
                    └─────────────┘
"""

import os
import json
import uuid
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
from enum import Enum

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import aiokafka

from ..agent import (
    CustomerSuccessAgent,
    CustomerMessage,
    AgentResponse,
    create_agent,
)

from ..database import (
    CustomerQueries,
    ConversationQueries,
    MessageQueries,
    TicketQueries,
    init_database,
    close_database,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class WorkerConfig:
    """Worker configuration"""
    
    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "technova-message-processor")
    KAFKA_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")
    KAFKA_ENABLE_AUTO_COMMIT = os.getenv("KAFKA_ENABLE_AUTO_COMMIT", "false").lower() == "true"
    
    # Kafka topics
    TOPIC_EMAIL = os.getenv("KAFKA_TOPIC_EMAIL", "channel-email")
    TOPIC_WHATSAPP = os.getenv("KAFKA_TOPIC_WHATSAPP", "channel-whatsapp")
    TOPIC_WEB_FORM = os.getenv("KAFKA_TOPIC_WEBFORM", "channel-webform")
    TOPIC_RESPONSES = os.getenv("KAFKA_TOPIC_RESPONSES", "agent-responses")
    TOPIC_ESCALATIONS = os.getenv("KAFKA_TOPIC_ESCALATIONS", "agent-escalations")
    
    # Consumer configuration
    CONSUMER_POLL_TIMEOUT_MS = int(os.getenv("KAFKA_POLL_TIMEOUT_MS", "1000"))
    CONSUMER_MAX_POLL_RECORDS = int(os.getenv("KAFKA_MAX_POLL_RECORDS", "100"))
    
    # Processing configuration
    MAX_CONCURRENT_MESSAGES = int(os.getenv("MAX_CONCURRENT_MESSAGES", "10"))
    MESSAGE_PROCESSING_TIMEOUT_SECONDS = int(os.getenv("MESSAGE_PROCESSING_TIMEOUT", "30"))
    RETRY_ON_FAILURE = os.getenv("RETRY_ON_FAILURE", "true").lower() == "true"
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    # Session management
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    # Health check
    HEALTH_CHECK_INTERVAL_SECONDS = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))


# ============================================================================
# Data Classes
# ============================================================================

class MessageSource(str, Enum):
    """Message source channels"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class ProcessingStatus(str, Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class KafkaMessage:
    """Represents a message from Kafka"""
    message_id: str
    source: MessageSource
    raw_data: Dict[str, Any]
    timestamp: datetime
    topic: str
    partition: int
    offset: int
    key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_kafka_record(cls, record: aiokafka.ConsumerRecord) -> 'KafkaMessage':
        """Create KafkaMessage from aiokafka record"""
        try:
            raw_data = json.loads(record.value.decode('utf-8')) if record.value else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            raw_data = {"raw": record.value.decode('utf-8', errors='ignore') if record.value else ""}
        
        # Parse headers
        headers = {}
        if record.headers:
            for key, value in record.headers:
                try:
                    headers[key] = value.decode('utf-8') if value else ""
                except:
                    headers[key] = str(value) if value else ""
        
        # Determine source from topic
        topic = record.topic
        if 'email' in topic.lower():
            source = MessageSource.EMAIL
        elif 'whatsapp' in topic.lower():
            source = MessageSource.WHATSAPP
        elif 'webform' in topic.lower() or 'web_form' in topic.lower():
            source = MessageSource.WEB_FORM
        else:
            source = MessageSource.EMAIL  # Default
        
        return cls(
            message_id=headers.get('message_id', str(uuid.uuid4())),
            source=source,
            raw_data=raw_data,
            timestamp=datetime.fromtimestamp(record.timestamp / 1000) if record.timestamp else datetime.now(),
            topic=topic,
            partition=record.partition,
            offset=record.offset,
            key=record.key.decode('utf-8') if record.key else None,
            headers=headers
        )


@dataclass
class ProcessingResult:
    """Result of message processing"""
    message_id: str
    status: ProcessingStatus
    ticket_id: Optional[str] = None
    conversation_id: Optional[str] = None
    customer_id: Optional[str] = None
    response_text: Optional[str] = None
    requires_escalation: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0
    processing_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Customer Resolver
# ============================================================================

class CustomerResolver:
    """
    Resolve customer identity from message data
    
    Priority:
    1. Email address
    2. Phone number
    3. Customer ID (if provided)
    4. Create new customer
    """
    
    @staticmethod
    async def resolve_customer(kafka_message: KafkaMessage) -> Optional[Dict]:
        """
        Resolve customer from message data
        
        Args:
            kafka_message: Incoming Kafka message
            
        Returns:
            Customer dict or None
        """
        try:
            raw_data = kafka_message.raw_data
            
            # Extract customer info from raw data
            email = CustomerResolver._extract_email(raw_data)
            phone = CustomerResolver._extract_phone(raw_data)
            customer_id = raw_data.get('customer_id')
            name = raw_data.get('customer_name', raw_data.get('name', ''))
            company = raw_data.get('company', '')
            
            # Try to find existing customer
            customer = None
            
            if email:
                customer = CustomerQueries.get_customer_by_email(email)
            
            if not customer and phone:
                customer = CustomerQueries.get_customer(phone)
            
            if not customer and customer_id:
                customer = CustomerQueries.get_customer(customer_id)
            
            # Create new customer if not found
            if not customer:
                customer_id = customer_id or f"CUST-{uuid.uuid4().hex[:8].upper()}"
                customer = CustomerQueries.create_or_update_customer(
                    customer_id=customer_id,
                    name=name or "Unknown Customer",
                    email=email,
                    phone=phone,
                    company=company,
                    account_tier='basic',
                    is_vip=False
                )
                logger.info(f"Created new customer: {customer_id}")
            else:
                # Update existing customer with latest info
                CustomerQueries.create_or_update_customer(
                    customer_id=customer['customer_id'],
                    name=name or customer.get('name', ''),
                    email=email or customer.get('email'),
                    phone=phone or customer.get('phone'),
                    company=company or customer.get('company'),
                )
                logger.debug(f"Updated existing customer: {customer['customer_id']}")
            
            return customer
            
        except Exception as e:
            logger.error(f"Failed to resolve customer: {e}")
            return None
    
    @staticmethod
    def _extract_email(data: Dict) -> Optional[str]:
        """Extract email from raw data"""
        # Check common email fields
        for field in ['email', 'customer_email', 'from', 'sender']:
            if field in data and data[field]:
                value = data[field]
                if isinstance(value, str) and '@' in value:
                    # Handle "Name <email@example.com>" format
                    if '<' in value:
                        value = value.split('<')[-1].rstrip('>')
                    return value.lower().strip()
        
        # Check nested structures
        if 'customer' in data and isinstance(data['customer'], dict):
            return CustomerResolver._extract_email(data['customer'])
        
        if 'from' in data and isinstance(data['from'], dict):
            return data['from'].get('email')
        
        return None
    
    @staticmethod
    def _extract_phone(data: Dict) -> Optional[str]:
        """Extract phone from raw data"""
        for field in ['phone', 'customer_phone', 'from', 'sender', 'msisdn']:
            if field in data and data[field]:
                value = data[field]
                if isinstance(value, str):
                    # Clean phone number
                    cleaned = ''.join(c for c in value if c.isdigit() or c == '+')
                    if len(cleaned) >= 10:
                        return cleaned
        
        # Check nested structures
        if 'customer' in data and isinstance(data['customer'], dict):
            return CustomerResolver._extract_phone(data['customer'])
        
        if 'from' in data and isinstance(data['from'], dict):
            return data['from'].get('phone')
        
        return None


# ============================================================================
# Conversation Manager
# ============================================================================

class ConversationManager:
    """
    Manage conversation threads
    
    Handles:
    - Creating new conversations
    - Updating existing conversations
    - Session timeout handling
    - Message threading
    """
    
    # In-memory conversation cache
    _active_conversations: Dict[str, Dict] = {}
    
    @classmethod
    async def get_or_create_conversation(
        cls,
        customer: Dict,
        kafka_message: KafkaMessage
    ) -> Dict:
        """
        Get existing conversation or create new one
        
        Args:
            customer: Customer dict
            kafka_message: Incoming Kafka message
            
        Returns:
            Conversation dict
        """
        try:
            customer_id = customer['customer_id']
            
            # Check for existing active conversation
            conversation = await cls._find_active_conversation(customer_id, kafka_message)
            
            if conversation:
                logger.debug(f"Found existing conversation: {conversation['conversation_id']}")
                return conversation
            
            # Create new conversation
            conversation_id = f"CONV-{uuid.uuid4().hex[:8].upper()}"
            
            # Extract thread ID from message if available
            thread_id = kafka_message.raw_data.get('thread_id')
            thread_id = thread_id or kafka_message.raw_data.get('conversation_id')
            thread_id = thread_id or kafka_message.headers.get('thread_id')
            
            conversation = ConversationQueries.create_conversation(
                conversation_id=conversation_id,
                customer_id=customer_id,
                channel=kafka_message.source.value,
                thread_id=thread_id
            )
            
            # Cache conversation
            cls._active_conversations[conversation_id] = {
                'conversation': conversation,
                'last_activity': datetime.now(),
                'message_count': 0
            }
            
            logger.info(f"Created new conversation: {conversation_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to get/create conversation: {e}")
            # Return minimal conversation object
            return {
                'conversation_id': f"CONV-{uuid.uuid4().hex[:8].upper()}",
                'customer_id': customer['customer_id'],
                'channel': kafka_message.source.value
            }
    
    @classmethod
    async def _find_active_conversation(
        cls,
        customer_id: str,
        kafka_message: KafkaMessage
    ) -> Optional[Dict]:
        """Find active conversation for customer"""
        try:
            # Check cache first
            for conv_id, conv_data in cls._active_conversations.items():
                if conv_data['conversation']['customer_id'] == customer_id:
                    # Check if conversation is still active
                    last_activity = conv_data['last_activity']
                    if datetime.now() - last_activity < timedelta(minutes=WorkerConfig.SESSION_TIMEOUT_MINUTES):
                        # Update last activity
                        conv_data['last_activity'] = datetime.now()
                        conv_data['message_count'] += 1
                        
                        # Update in database
                        ConversationQueries.update_conversation_sentiment(
                            conv_id,
                            sentiment='neutral',
                            sentiment_score=0.0
                        )
                        
                        return conv_data['conversation']
                    else:
                        # Conversation expired, remove from cache
                        del cls._active_conversations[conv_id]
                        break
            
            # Check database for recent conversations
            conversations = ConversationQueries.get_customer_conversations(
                customer_id=customer_id,
                limit=1
            )
            
            if conversations:
                conv = conversations[0]
                # Check if conversation is recent
                last_message = conv.get('last_message_at')
                if last_message:
                    if isinstance(last_message, str):
                        last_message = datetime.fromisoformat(last_message.replace('Z', '+00:00'))
                    if datetime.now(last_message.tzinfo) - last_message < timedelta(minutes=WorkerConfig.SESSION_TIMEOUT_MINUTES):
                        # Cache it
                        cls._active_conversations[conv['conversation_id']] = {
                            'conversation': conv,
                            'last_activity': datetime.now(),
                            'message_count': 1
                        }
                        return conv
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find active conversation: {e}")
            return None
    
    @classmethod
    async def close_conversation(cls, conversation_id: str) -> bool:
        """Close conversation and remove from cache"""
        try:
            if conversation_id in cls._active_conversations:
                del cls._active_conversations[conversation_id]
            
            # Update in database
            ConversationQueries.update_conversation_sentiment(
                conversation_id,
                sentiment='neutral',
                sentiment_score=0.0
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to close conversation: {e}")
            return False
    
    @classmethod
    def cleanup_expired_conversations(cls):
        """Remove expired conversations from cache"""
        expired = []
        now = datetime.now()
        
        for conv_id, conv_data in cls._active_conversations.items():
            if now - conv_data['last_activity'] > timedelta(minutes=WorkerConfig.SESSION_TIMEOUT_MINUTES):
                expired.append(conv_id)
        
        for conv_id in expired:
            del cls._active_conversations[conv_id]
            logger.debug(f"Cleaned up expired conversation: {conv_id}")
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired conversations")


# ============================================================================
# Message Processor (Main Worker)
# ============================================================================

class MessageProcessor:
    """
    Main message processor worker
    
    Workflow:
    1. Consume messages from Kafka topics
    2. Resolve customer identity
    3. Get/create conversation
    4. Call agent.run()
    5. Store response in database
    6. Publish response to Kafka
    7. Handle escalations
    """
    
    def __init__(self, agent: Optional[CustomerSuccessAgent] = None):
        """
        Initialize message processor
        
        Args:
            agent: Optional pre-configured agent instance
        """
        self.agent = agent or create_agent()
        self.consumer: Optional[aiokafka.AIOKafkaConsumer] = None
        self.producer: Optional[aiokafka.AIOKafkaProducer] = None
        self.is_running = False
        self.stats = {
            'messages_processed': 0,
            'messages_failed': 0,
            'escalations': 0,
            'start_time': None
        }
        
        logger.info("MessageProcessor initialized")
    
    async def start(self):
        """Start the message processor"""
        logger.info("Starting MessageProcessor...")
        
        try:
            # Initialize database
            init_database()
            logger.info("Database initialized")
            
            # Create Kafka consumer
            self.consumer = aiokafka.AIOKafkaConsumer(
                WorkerConfig.TOPIC_EMAIL,
                WorkerConfig.TOPIC_WHATSAPP,
                WorkerConfig.TOPIC_WEB_FORM,
                bootstrap_servers=WorkerConfig.KAFKA_BOOTSTRAP_SERVERS,
                consumer_group=WorkerConfig.KAFKA_CONSUMER_GROUP,
                auto_offset_reset=WorkerConfig.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=WorkerConfig.KAFKA_ENABLE_AUTO_COMMIT,
                max_poll_records=WorkerConfig.CONSUMER_MAX_POLL_RECORDS,
                value_deserializer=lambda v: v,
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
            )
            
            # Create Kafka producer
            self.producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=WorkerConfig.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            
            # Start consumer and producer
            await self.consumer.start()
            await self.producer.start()
            
            logger.info(f"Kafka consumer started (topics: email, whatsapp, webform)")
            logger.info(f"Kafka producer started")
            
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            # Start processing loop
            await self._process_loop()
            
        except Exception as e:
            logger.error(f"Failed to start MessageProcessor: {e}")
            raise
    
    async def stop(self):
        """Stop the message processor"""
        logger.info("Stopping MessageProcessor...")
        
        self.is_running = False
        
        # Close Kafka connections
        if self.consumer:
            await self.consumer.stop()
            logger.debug("Kafka consumer stopped")
        
        if self.producer:
            await self.producer.stop()
            logger.debug("Kafka producer stopped")
        
        # Close database
        close_database()
        logger.debug("Database connections closed")
        
        # Log final stats
        self._log_stats()
        
        logger.info("MessageProcessor stopped")
    
    async def _process_loop(self):
        """Main processing loop"""
        logger.info("Starting message processing loop")
        
        # Start health check task
        health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Start conversation cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        try:
            while self.is_running:
                try:
                    # Poll for messages
                    messages = await self.consumer.getmany(
                        timeout_ms=WorkerConfig.CONSUMER_POLL_TIMEOUT_MS
                    )
                    
                    # Process messages
                    for topic_partition, records in messages.items():
                        for record in records:
                            if not self.is_running:
                                break
                            
                            # Process message with semaphore for concurrency control
                            await self._process_message(record)
                    
                except asyncio.TimeoutError:
                    # No messages, continue polling
                    continue
                except KafkaError as e:
                    logger.error(f"Kafka error: {e}")
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")
                    await asyncio.sleep(1)
        
        finally:
            # Cancel background tasks
            health_check_task.cancel()
            cleanup_task.cancel()
            
            try:
                await health_check_task
                await cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _process_message(self, record: aiokafka.ConsumerRecord):
        """
        Process a single Kafka message
        
        Args:
            record: Kafka consumer record
        """
        start_time = datetime.now()
        kafka_message = None
        
        try:
            # Parse Kafka message
            kafka_message = KafkaMessage.from_kafka_record(record)
            logger.debug(f"Processing message {kafka_message.message_id} from {kafka_message.topic}")
            
            # Step 1: Resolve customer
            customer = await CustomerResolver.resolve_customer(kafka_message)
            if not customer:
                logger.error(f"Failed to resolve customer for message {kafka_message.message_id}")
                await self._publish_error(kafka_message, "Failed to resolve customer")
                return
            
            logger.debug(f"Customer resolved: {customer['customer_id']}")
            
            # Step 2: Get/create conversation
            conversation = await ConversationManager.get_or_create_conversation(
                customer=customer,
                kafka_message=kafka_message
            )
            logger.debug(f"Conversation: {conversation['conversation_id']}")
            
            # Step 3: Build CustomerMessage for agent
            agent_message = self._build_agent_message(kafka_message, customer, conversation)
            
            # Step 4: Call agent.run()
            agent_response = await asyncio.wait_for(
                self.agent.process_message(agent_message),
                timeout=WorkerConfig.MESSAGE_PROCESSING_TIMEOUT_SECONDS
            )
            
            # Step 5: Store in database
            await self._store_message(
                kafka_message=kafka_message,
                customer=customer,
                conversation=conversation,
                agent_response=agent_response
            )
            
            # Step 6: Publish response
            if agent_response.requires_escalation:
                await self._publish_escalation(kafka_message, agent_response, customer)
                self.stats['escalations'] += 1
            else:
                await self._publish_response(kafka_message, agent_response, customer)
            
            # Update stats
            self.stats['messages_processed'] += 1
            
            # Log processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(
                f"Message {kafka_message.message_id} processed in {processing_time:.0f}ms "
                f"(ticket: {agent_response.ticket_id}, escalation: {agent_response.requires_escalation})"
            )
            
            # Commit offset (manual commit)
            if not WorkerConfig.KAFKA_ENABLE_AUTO_COMMIT:
                await self.consumer.commit()
            
        except asyncio.TimeoutError:
            logger.error(f"Message processing timeout for {kafka_message.message_id if kafka_message else 'unknown'}")
            await self._handle_error(kafka_message, "Processing timeout", start_time)
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            await self._handle_error(kafka_message, str(e), start_time)
    
    def _build_agent_message(
        self,
        kafka_message: KafkaMessage,
        customer: Dict,
        conversation: Dict
    ) -> CustomerMessage:
        """Build CustomerMessage for agent"""
        raw_data = kafka_message.raw_data
        
        # Extract message content based on source
        if kafka_message.source == MessageSource.EMAIL:
            message_text = raw_data.get('body', raw_data.get('body_plain', ''))
            subject = raw_data.get('subject', kafka_message.headers.get('subject', ''))
        elif kafka_message.source == MessageSource.WHATSAPP:
            message_text = raw_data.get('body', raw_data.get('message', ''))
            subject = None
        else:  # WEB_FORM
            message_text = raw_data.get('message', raw_data.get('description', ''))
            subject = raw_data.get('subject', '')
        
        return CustomerMessage(
            message=message_text,
            channel=kafka_message.source.value,
            customer_email=customer.get('email'),
            customer_phone=customer.get('phone'),
            customer_name=customer.get('name'),
            subject=subject,
            timestamp=kafka_message.timestamp,
            metadata={
                'kafka_message_id': kafka_message.message_id,
                'conversation_id': conversation['conversation_id'],
                'topic': kafka_message.topic,
                'partition': kafka_message.partition,
                'offset': kafka_message.offset,
            }
        )
    
    async def _store_message(
        self,
        kafka_message: KafkaMessage,
        customer: Dict,
        conversation: Dict,
        agent_response: AgentResponse
    ):
        """Store message in database"""
        try:
            # Store incoming customer message
            message_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
            MessageQueries.create_message(
                message_id=message_id,
                conversation_id=conversation['conversation_id'],
                customer_id=customer['customer_id'],
                role='customer',
                content=kafka_message.raw_data.get('body', kafka_message.raw_data.get('message', '')),
                channel=kafka_message.source.value,
                category=agent_response.category,
                sentiment=agent_response.sentiment,
                sentiment_score=agent_response.sentiment_score,
                priority=agent_response.priority,
                requires_escalation=agent_response.requires_escalation,
                escalation_reason=agent_response.escalation_reason
            )
            
            # Store agent response
            response_message_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
            MessageQueries.create_message(
                message_id=response_message_id,
                conversation_id=conversation['conversation_id'],
                customer_id=customer['customer_id'],
                role='agent',
                content=agent_response.response_text,
                channel=kafka_message.source.value,
                category=agent_response.category,
                kb_articles_referenced=agent_response.kb_articles,
                response_time_ms=len(agent_response.response_text)  # Approximate
            )
            
            logger.debug(f"Stored messages in database")
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            # Don't fail the entire processing for DB errors
    
    async def _publish_response(
        self,
        kafka_message: KafkaMessage,
        agent_response: AgentResponse,
        customer: Dict
    ):
        """Publish response to Kafka"""
        try:
            response_data = {
                'message_id': kafka_message.message_id,
                'ticket_id': agent_response.ticket_id,
                'conversation_id': kafka_message.headers.get('conversation_id'),
                'customer_id': customer['customer_id'],
                'channel': kafka_message.source.value,
                'response': agent_response.response_text,
                'category': agent_response.category,
                'sentiment': agent_response.sentiment,
                'timestamp': datetime.now().isoformat(),
            }
            
            # Determine response topic based on channel
            response_topic = WorkerConfig.TOPIC_RESPONSES
            
            # Publish
            await self.producer.send_and_wait(
                topic=response_topic,
                key=f"response:{kafka_message.message_id}",
                value=response_data
            )
            
            logger.debug(f"Published response to {response_topic}")
            
        except Exception as e:
            logger.error(f"Failed to publish response: {e}")
    
    async def _publish_escalation(
        self,
        kafka_message: KafkaMessage,
        agent_response: AgentResponse,
        customer: Dict
    ):
        """Publish escalation to Kafka"""
        try:
            escalation_data = {
                'message_id': kafka_message.message_id,
                'ticket_id': agent_response.ticket_id,
                'conversation_id': kafka_message.headers.get('conversation_id'),
                'customer_id': customer['customer_id'],
                'customer_name': customer.get('name'),
                'customer_email': customer.get('email'),
                'channel': kafka_message.source.value,
                'escalation_reason': agent_response.escalation_reason,
                'priority': agent_response.priority,
                'original_message': kafka_message.raw_data.get('body', kafka_message.raw_data.get('message', '')),
                'timestamp': datetime.now().isoformat(),
            }
            
            # Publish to escalation topic
            await self.producer.send_and_wait(
                topic=WorkerConfig.TOPIC_ESCALATIONS,
                key=f"escalation:{kafka_message.message_id}",
                value=escalation_data
            )
            
            logger.info(f"Published escalation to {WorkerConfig.TOPIC_ESCALATIONS}")
            
        except Exception as e:
            logger.error(f"Failed to publish escalation: {e}")
    
    async def _publish_error(self, kafka_message: KafkaMessage, error: str):
        """Publish error to Kafka"""
        try:
            error_data = {
                'message_id': kafka_message.message_id,
                'error': error,
                'timestamp': datetime.now().isoformat(),
            }
            
            await self.producer.send_and_wait(
                topic=f"{kafka_message.topic}-errors",
                key=f"error:{kafka_message.message_id}",
                value=error_data
            )
            
        except Exception as e:
            logger.error(f"Failed to publish error: {e}")
    
    async def _handle_error(
        self,
        kafka_message: Optional[KafkaMessage],
        error: str,
        start_time: datetime
    ):
        """Handle processing error"""
        self.stats['messages_failed'] += 1
        
        # Publish error
        if kafka_message:
            await self._publish_error(kafka_message, error)
        
        # Retry logic
        if WorkerConfig.RETRY_ON_FAILURE and kafka_message:
            retry_count = kafka_message.headers.get('retry_count', '0')
            retry_count = int(retry_count)
            
            if retry_count < WorkerConfig.MAX_RETRIES:
                logger.info(f"Retrying message {kafka_message.message_id} (attempt {retry_count + 1}/{WorkerConfig.MAX_RETRIES})")
                # Re-publish to same topic for retry
                await self.producer.send_and_wait(
                    topic=kafka_message.topic,
                    key=kafka_message.key,
                    value=kafka_message.raw_data,
                    headers={
                        **kafka_message.headers,
                        'retry_count': str(retry_count + 1),
                        'original_timestamp': kafka_message.timestamp.isoformat(),
                    }
                )
    
    async def _health_check_loop(self):
        """Periodic health check"""
        while self.is_running:
            try:
                await asyncio.sleep(WorkerConfig.HEALTH_CHECK_INTERVAL_SECONDS)
                self._log_stats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _cleanup_loop(self):
        """Periodic conversation cleanup"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Run every minute
                ConversationManager.cleanup_expired_conversations()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def _log_stats(self):
        """Log current statistics"""
        uptime = datetime.now() - self.stats['start_time'] if self.stats['start_time'] else timedelta(0)
        
        logger.info(
            f"Stats | Processed: {self.stats['messages_processed']} | "
            f"Failed: {self.stats['messages_failed']} | "
            f"Escalations: {self.stats['escalations']} | "
            f"Uptime: {uptime}"
        )
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        return {
            **self.stats,
            'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0,
            'is_running': self.is_running,
        }


# ============================================================================
# Factory Function
# ============================================================================

def create_message_processor(agent: Optional[CustomerSuccessAgent] = None) -> MessageProcessor:
    """
    Factory function to create message processor
    
    Args:
        agent: Optional pre-configured agent
        
    Returns:
        MessageProcessor instance
    """
    return MessageProcessor(agent=agent)


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main entry point"""
    import signal
    
    # Create processor
    processor = create_message_processor()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(processor.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    # Start processor
    try:
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Processor error: {e}")
        raise
    finally:
        await processor.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
