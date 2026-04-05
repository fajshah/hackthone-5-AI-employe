"""
TechNova Customer Support - Kafka Client

Complete Kafka client with:
- All topic definitions
- Producer class (sync + async)
- Consumer class (sync + async)
- Message serialization
- Error handling & retry
- Connection management
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Callable, Union, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager, asynccontextmanager

# Kafka imports
from kafka import KafkaProducer, KafkaConsumer, TopicPartition
from kafka.errors import KafkaError, KafkaTimeoutError
from kafka.structs import TopicPartition, OffsetAndMetadata

# Async Kafka
import aiokafka

logger = logging.getLogger(__name__)


# ============================================================================
# Topic Definitions
# ============================================================================

class KafkaTopics(str, Enum):
    """
    All Kafka topics for TechNova support system
    
    Topic Naming Convention:
    - channel-* : Ingestion from channels
    - agent-* : Agent output
    - system-* : System events
    - dlq-* : Dead letter queues
    """
    
    # Channel Ingestion Topics
    CHANNEL_EMAIL = "channel-email"
    CHANNEL_WHATSAPP = "channel-whatsapp"
    CHANNEL_WEB_FORM = "channel-webform"
    
    # Agent Topics
    AGENT_REQUESTS = "agent-requests"
    AGENT_RESPONSES = "agent-responses"
    AGENT_ESCALATIONS = "agent-escalations"
    
    # System Topics
    SYSTEM_EVENTS = "system-events"
    SYSTEM_LOGS = "system-logs"
    SYSTEM_METRICS = "system-metrics"
    
    # Customer Events
    CUSTOMER_CREATED = "customer-created"
    CUSTOMER_UPDATED = "customer-updated"
    CONVERSATION_STARTED = "conversation-started"
    CONVERSATION_CLOSED = "conversation-closed"
    
    # Ticket Events
    TICKET_CREATED = "ticket-created"
    TICKET_UPDATED = "ticket-updated"
    TICKET_RESOLVED = "ticket-resolved"
    TICKET_ESCALATED = "ticket-escalated"
    
    # Dead Letter Queues
    DLQ_EMAIL = "dlq-channel-email"
    DLQ_WHATSAPP = "dlq-channel-whatsapp"
    DLQ_WEBFORM = "dlq-channel-webform"
    DLQ_AGENT = "dlq-agent-requests"
    
    # Error Topics
    ERRORS_PROCESSING = "errors-processing"
    ERRORS_VALIDATION = "errors-validation"
    
    @classmethod
    def all_topics(cls) -> List[str]:
        """Get all topic names"""
        return [topic.value for topic in cls]
    
    @classmethod
    def channel_topics(cls) -> List[str]:
        """Get all channel ingestion topics"""
        return [
            cls.CHANNEL_EMAIL.value,
            cls.CHANNEL_WHATSAPP.value,
            cls.CHANNEL_WEB_FORM.value,
        ]
    
    @classmethod
    def agent_topics(cls) -> List[str]:
        """Get all agent-related topics"""
        return [
            cls.AGENT_REQUESTS.value,
            cls.AGENT_RESPONSES.value,
            cls.AGENT_ESCALATIONS.value,
        ]
    
    @classmethod
    def dlq_topics(cls) -> List[str]:
        """Get all dead letter queue topics"""
        return [
            cls.DLQ_EMAIL.value,
            cls.DLQ_WHATSAPP.value,
            cls.DLQ_WEBFORM.value,
            cls.DLQ_AGENT.value,
        ]


# ============================================================================
# Message Classes
# ============================================================================

class MessageType(str, Enum):
    """Message type definitions"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    ESCALATION = "escalation"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"


@dataclass
class KafkaMessage:
    """
    Standardized Kafka message structure
    
    All messages follow this envelope format
    """
    message_id: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: str
    source: str
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        message_type: MessageType,
        payload: Dict[str, Any],
        source: str = "system",
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> 'KafkaMessage':
        """Create a new Kafka message"""
        headers = {
            "message_type": message_type.value,
            "source": source,
            "created_at": datetime.now().isoformat(),
        }
        
        if additional_headers:
            headers.update(additional_headers)
        
        return cls(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now().isoformat(),
            source=source,
            correlation_id=correlation_id or str(uuid.uuid4()),
            reply_to=reply_to,
            headers=headers,
            metadata={}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'KafkaMessage':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KafkaMessage':
        """Create from dictionary"""
        return cls(**data)


# ============================================================================
# Configuration
# ============================================================================

class KafkaConfig:
    """Kafka configuration"""
    
    # Connection
    BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    SSL_CAFILE = os.getenv("KAFKA_SSL_CAFILE")
    SSL_CERTFILE = os.getenv("KAFKA_SSL_CERTFILE")
    SSL_KEYFILE = os.getenv("KAFKA_SSL_KEYFILE")
    
    # Producer
    PRODUCER_ACKS = os.getenv("KAFKA_PRODUCER_ACKS", "all")
    PRODUCER_RETRIES = int(os.getenv("KAFKA_PRODUCER_RETRIES", "3"))
    PRODUCER_BATCH_SIZE = int(os.getenv("KAFKA_PRODUCER_BATCH_SIZE", "16384"))
    PRODUCER_LINGER_MS = int(os.getenv("KAFKA_PRODUCER_LINGER_MS", "1"))
    PRODUCER_COMPRESSION = os.getenv("KAFKA_PRODUCER_COMPRESSION", "gzip")
    
    # Consumer
    CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "technova-group")
    CONSUMER_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")
    CONSUMER_ENABLE_AUTO_COMMIT = os.getenv("KAFKA_ENABLE_AUTO_COMMIT", "false").lower() == "true"
    CONSUMER_MAX_POLL_RECORDS = int(os.getenv("KAFKA_MAX_POLL_RECORDS", "500"))
    CONSUMER_SESSION_TIMEOUT_MS = int(os.getenv("KAFKA_SESSION_TIMEOUT_MS", "30000"))
    
    # Topics
    DEFAULT_REPLICATION_FACTOR = int(os.getenv("KAFKA_REPLICATION_FACTOR", "1"))
    DEFAULT_NUM_PARTITIONS = int(os.getenv("KAFKA_NUM_PARTITIONS", "3"))
    
    # Retry
    RETRY_BACKOFF_MS = int(os.getenv("KAFKA_RETRY_BACKOFF_MS", "100"))
    RETRY_MAX_MS = int(os.getenv("KAFKA_RETRY_MAX_MS", "10000"))


# ============================================================================
# Synchronous Producer
# ============================================================================

class SyncKafkaProducer:
    """
    Synchronous Kafka producer
    
    Use for:
    - Simple fire-and-forget messages
    - Scripts and batch jobs
    - When async is not needed
    """
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """
        Initialize producer
        
        Args:
            config: Optional KafkaConfig instance
        """
        self.config = config or KafkaConfig()
        self._producer: Optional[KafkaProducer] = None
        
        logger.info("SyncKafkaProducer initialized")
    
    def _get_producer(self) -> KafkaProducer:
        """Get or create producer instance"""
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.config.BOOTSTRAP_SERVERS,
                acks=self.config.PRODUCER_ACKS,
                retries=self.config.PRODUCER_RETRIES,
                batch_size=self.config.PRODUCER_BATCH_SIZE,
                linger_ms=self.config.PRODUCER_LINGER_MS,
                compression_type=self.config.PRODUCER_COMPRESSION,
                retry_backoff_ms=self.config.RETRY_BACKOFF_MS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            logger.info("Kafka producer created")
        
        return self._producer
    
    def send(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[List[tuple]] = None
    ) -> Dict[str, Any]:
        """
        Send message to Kafka topic
        
        Args:
            topic: Topic name
            value: Message value (dict)
            key: Optional message key
            headers: Optional headers
            
        Returns:
            Dict with message_id, topic, partition, offset
        """
        try:
            producer = self._get_producer()
            
            future = producer.send(
                topic=topic,
                value=value,
                key=key,
                headers=headers
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            result = {
                "message_id": key or str(uuid.uuid4()),
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset,
                "timestamp": record_metadata.timestamp
            }
            
            logger.debug(f"Message sent to {topic}[{record_metadata.partition}]@{record_metadata.offset}")
            return result
            
        except KafkaTimeoutError as e:
            logger.error(f"Kafka send timeout: {e}")
            raise
        except KafkaError as e:
            logger.error(f"Kafka send error: {e}")
            raise
    
    def send_message(self, topic: str, message: KafkaMessage) -> Dict[str, Any]:
        """
        Send KafkaMessage to topic
        
        Args:
            topic: Topic name
            message: KafkaMessage instance
            
        Returns:
            Send result dict
        """
        # Convert headers to Kafka format
        headers = [
            (key, value.encode('utf-8'))
            for key, value in message.headers.items()
        ]
        
        return self.send(
            topic=topic,
            value=message.to_dict(),
            key=message.message_id,
            headers=headers
        )
    
    def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email message to channel-email topic"""
        message = KafkaMessage.create(
            message_type=MessageType.EMAIL,
            payload=email_data,
            source="gmail-handler"
        )
        return self.send_message(KafkaTopics.CHANNEL_EMAIL.value, message)
    
    def send_whatsapp(self, whatsapp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send WhatsApp message to channel-whatsapp topic"""
        message = KafkaMessage.create(
            message_type=MessageType.WHATSAPP,
            payload=whatsapp_data,
            source="whatsapp-handler"
        )
        return self.send_message(KafkaTopics.CHANNEL_WHATSAPP.value, message)
    
    def send_web_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send web form submission to channel-webform topic"""
        message = KafkaMessage.create(
            message_type=MessageType.WEB_FORM,
            payload=form_data,
            source="webform-handler"
        )
        return self.send_message(KafkaTopics.CHANNEL_WEB_FORM.value, message)
    
    def send_agent_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send agent request to agent-requests topic"""
        message = KafkaMessage.create(
            message_type=MessageType.AGENT_REQUEST,
            payload=request_data,
            source="message-processor",
            reply_to=KafkaTopics.AGENT_RESPONSES.value
        )
        return self.send_message(KafkaTopics.AGENT_REQUESTS.value, message)
    
    def send_escalation(self, escalation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send escalation to agent-escalations topic"""
        message = KafkaMessage.create(
            message_type=MessageType.ESCALATION,
            payload=escalation_data,
            source="agent"
        )
        return self.send_message(KafkaTopics.AGENT_ESCALATIONS.value, message)
    
    def send_error(self, error_data: Dict[str, Any], error_type: str = "processing") -> Dict[str, Any]:
        """Send error to appropriate error topic"""
        topic = (
            KafkaTopics.ERRORS_PROCESSING.value if error_type == "processing"
            else KafkaTopics.ERRORS_VALIDATION.value
        )
        
        message = KafkaMessage.create(
            message_type=MessageType.ERROR,
            payload=error_data,
            source="error-handler"
        )
        return self.send_message(topic, message)
    
    def send_to_dlq(
        self,
        original_topic: str,
        message_data: Dict[str, Any],
        error: str
    ) -> Dict[str, Any]:
        """Send message to dead letter queue"""
        dlq_topic = f"dlq-{original_topic}"
        
        payload = {
            "original_topic": original_topic,
            "original_message": message_data,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        message = KafkaMessage.create(
            message_type=MessageType.ERROR,
            payload=payload,
            source="dlq-handler"
        )
        return self.send_message(dlq_topic, message)
    
    def flush(self):
        """Flush any pending messages"""
        if self._producer:
            self._producer.flush()
            logger.debug("Producer flushed")
    
    def close(self):
        """Close producer"""
        if self._producer:
            self._producer.close()
            self._producer = None
            logger.info("Producer closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================================================
# Asynchronous Producer
# ============================================================================

class AsyncKafkaProducer:
    """
    Asynchronous Kafka producer (aiokafka)
    
    Use for:
    - High-throughput applications
    - Async/await code
    - Real-time processing
    """
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """Initialize async producer"""
        self.config = config or KafkaConfig()
        self._producer: Optional[aiokafka.AIOKafkaProducer] = None
        
        logger.info("AsyncKafkaProducer initialized")
    
    async def start(self):
        """Start the producer"""
        if self._producer is None:
            self._producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=self.config.BOOTSTRAP_SERVERS,
                acks=self.config.PRODUCER_ACKS,
                compression_type=self.config.PRODUCER_COMPRESSION,
                retry_backoff_ms=self.config.RETRY_BACKOFF_MS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            await self._producer.start()
            logger.info("Async Kafka producer started")
    
    async def stop(self):
        """Stop the producer"""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Async Kafka producer stopped")
    
    async def send(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[List[tuple]] = None
    ) -> Dict[str, Any]:
        """Send message asynchronously"""
        if self._producer is None:
            await self.start()
        
        try:
            future = await self._producer.send(
                topic=topic,
                value=value,
                key=key,
                headers=headers
            )
            
            # Wait for send to complete
            record_metadata = await future
            
            return {
                "message_id": key or str(uuid.uuid4()),
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset,
                "timestamp": record_metadata.timestamp
            }
            
        except Exception as e:
            logger.error(f"Async send error: {e}")
            raise
    
    async def send_message(self, topic: str, message: KafkaMessage) -> Dict[str, Any]:
        """Send KafkaMessage asynchronously"""
        headers = [
            (key, value.encode('utf-8'))
            for key, value in message.headers.items()
        ]
        
        return await self.send(
            topic=topic,
            value=message.to_dict(),
            key=message.message_id,
            headers=headers
        )
    
    async def send_and_wait(self, topic: str, value: Dict, key: Optional[str] = None):
        """Send and wait for confirmation"""
        if self._producer is None:
            await self.start()
        
        await self._producer.send_and_wait(topic, value, key=key)
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactions"""
        if self._producer is None:
            await self.start()
        
        await self._producer.begin_transaction()
        try:
            yield self
            await self._producer.commit_transaction()
        except Exception:
            await self._producer.abort_transaction()
            raise
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


# ============================================================================
# Synchronous Consumer
# ============================================================================

class SyncKafkaConsumer:
    """
    Synchronous Kafka consumer
    
    Use for:
    - Simple polling consumers
    - Scripts and batch jobs
    - When async is not needed
    """
    
    def __init__(
        self,
        topics: Union[str, List[str]],
        group_id: Optional[str] = None,
        config: Optional[KafkaConfig] = None
    ):
        """
        Initialize consumer
        
        Args:
            topics: Topic name or list of topics
            group_id: Consumer group ID
            config: Optional KafkaConfig
        """
        self.topics = [topics] if isinstance(topics, str) else topics
        self.group_id = group_id or KafkaConfig.CONSUMER_GROUP
        self.config = config or KafkaConfig()
        self._consumer: Optional[KafkaConsumer] = None
        
        logger.info(f"SyncKafkaConsumer initialized for topics: {self.topics}")
    
    def _get_consumer(self) -> KafkaConsumer:
        """Get or create consumer instance"""
        if self._consumer is None:
            self._consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.config.BOOTSTRAP_SERVERS,
                group_id=self.group_id,
                auto_offset_reset=self.config.CONSUMER_AUTO_OFFSET_RESET,
                enable_auto_commit=self.config.CONSUMER_ENABLE_AUTO_COMMIT,
                max_poll_records=self.config.CONSUMER_MAX_POLL_RECORDS,
                session_timeout_ms=self.config.CONSUMER_SESSION_TIMEOUT_MS,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')) if v else None,
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
            )
            logger.info(f"Kafka consumer created for {self.topics}")
        
        return self._consumer
    
    def poll(self, timeout_ms: int = 1000) -> List[Dict[str, Any]]:
        """
        Poll for messages
        
        Args:
            timeout_ms: Poll timeout in milliseconds
            
        Returns:
            List of message dicts
        """
        consumer = self._get_consumer()
        messages = []
        
        try:
            for message in consumer:
                messages.append({
                    "topic": message.topic,
                    "partition": message.partition,
                    "offset": message.offset,
                    "key": message.key,
                    "value": message.value,
                    "headers": message.headers,
                    "timestamp": message.timestamp
                })
                
                # Only poll once unless timeout is 0
                if timeout_ms > 0:
                    break
                    
        except StopIteration:
            pass
        
        return messages
    
    def consume(
        self,
        callback: Callable[[Dict[str, Any]], None],
        max_messages: Optional[int] = None
    ):
        """
        Consume messages with callback
        
        Args:
            callback: Function to call for each message
            max_messages: Optional max messages to consume
        """
        consumer = self._get_consumer()
        count = 0
        
        try:
            for message in consumer:
                msg_dict = {
                    "topic": message.topic,
                    "partition": message.partition,
                    "offset": message.offset,
                    "key": message.key,
                    "value": message.value,
                    "headers": message.headers,
                    "timestamp": message.timestamp
                }
                
                callback(msg_dict)
                count += 1
                
                if max_messages and count >= max_messages:
                    break
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise
    
    def seek_to_beginning(self, partitions: Optional[List[TopicPartition]] = None):
        """Seek to beginning of partitions"""
        consumer = self._get_consumer()
        if partitions:
            consumer.seek_to_beginning(*partitions)
        else:
            consumer.seek_to_beginning()
    
    def seek_to_end(self, partitions: Optional[List[TopicPartition]] = None):
        """Seek to end of partitions"""
        consumer = self._get_consumer()
        if partitions:
            consumer.seek_to_end(*partitions)
        else:
            consumer.seek_to_end()
    
    def commit(self, offsets: Optional[Dict[TopicPartition, OffsetAndMetadata]] = None):
        """Commit offsets"""
        consumer = self._get_consumer()
        consumer.commit(offsets)
    
    def close(self):
        """Close consumer"""
        if self._consumer:
            self._consumer.close()
            self._consumer = None
            logger.info("Consumer closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================================================
# Asynchronous Consumer
# ============================================================================

class AsyncKafkaConsumer:
    """
    Asynchronous Kafka consumer (aiokafka)
    
    Use for:
    - High-throughput consumers
    - Async/await code
    - Real-time processing
    """
    
    def __init__(
        self,
        topics: Union[str, List[str]],
        group_id: Optional[str] = None,
        config: Optional[KafkaConfig] = None
    ):
        """Initialize async consumer"""
        self.topics = [topics] if isinstance(topics, str) else topics
        self.group_id = group_id or KafkaConfig.CONSUMER_GROUP
        self.config = config or KafkaConfig()
        self._consumer: Optional[aiokafka.AIOKafkaConsumer] = None
        
        logger.info(f"AsyncKafkaConsumer initialized for topics: {self.topics}")
    
    async def start(self):
        """Start the consumer"""
        if self._consumer is None:
            self._consumer = aiokafka.AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.config.BOOTSTRAP_SERVERS,
                group_id=self.group_id,
                auto_offset_reset=self.config.CONSUMER_AUTO_OFFSET_RESET,
                enable_auto_commit=self.config.CONSUMER_ENABLE_AUTO_COMMIT,
                max_poll_records=self.config.CONSUMER_MAX_POLL_RECORDS,
                session_timeout_ms=self.config.CONSUMER_SESSION_TIMEOUT_MS,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')) if v else None,
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
            )
            await self._consumer.start()
            logger.info(f"Async Kafka consumer started for {self.topics}")
    
    async def stop(self):
        """Stop the consumer"""
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
            logger.info("Async Kafka consumer stopped")
    
    async def getone(self, timeout_ms: int = 1000) -> Optional[Dict[str, Any]]:
        """Get single message"""
        if self._consumer is None:
            await self.start()
        
        try:
            record = await self._consumer.getone(timeout_ms=timeout_ms)
            
            if record:
                return {
                    "topic": record.topic,
                    "partition": record.partition,
                    "offset": record.offset,
                    "key": record.key,
                    "value": record.value,
                    "headers": record.headers,
                    "timestamp": record.timestamp
                }
            
            return None
            
        except asyncio.TimeoutError:
            return None
    
    async def getmany(
        self,
        timeout_ms: int = 1000,
        max_records: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get multiple messages"""
        if self._consumer is None:
            await self.start()
        
        try:
            records = await self._consumer.getmany(
                timeout_ms=timeout_ms,
                max_records=max_records or self.config.CONSUMER_MAX_POLL_RECORDS
            )
            
            result = {}
            for tp, msgs in records.items():
                result[f"{tp.topic}-{tp.partition}"] = [
                    {
                        "topic": msg.topic,
                        "partition": msg.partition,
                        "offset": msg.offset,
                        "key": msg.key,
                        "value": msg.value,
                        "headers": msg.headers,
                        "timestamp": msg.timestamp
                    }
                    for msg in msgs
                ]
            
            return result
            
        except asyncio.TimeoutError:
            return {}
    
    async def consume(
        self,
        callback: Callable[[Dict[str, Any]], None]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Consume messages with callback (async generator)
        
        Usage:
            async for message in consumer.consume(callback):
                process(message)
        """
        if self._consumer is None:
            await self.start()
        
        async for record in self._consumer:
            msg_dict = {
                "topic": record.topic,
                "partition": record.partition,
                "offset": record.offset,
                "key": record.key,
                "value": record.value,
                "headers": record.headers,
                "timestamp": record.timestamp
            }
            
            try:
                await callback(msg_dict) if asyncio.iscoroutinefunction(callback) else callback(msg_dict)
                yield msg_dict
            except Exception as e:
                logger.error(f"Callback error: {e}")
                # Continue processing
    
    async def commit(self, offsets: Optional[Dict] = None):
        """Commit offsets"""
        if self._consumer:
            await self._consumer.commit(offsets)
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


# ============================================================================
# Kafka Client Factory
# ============================================================================

class KafkaClient:
    """
    Kafka client factory and utilities
    
    Provides easy access to producers and consumers
    """
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """Initialize Kafka client"""
        self.config = config or KafkaConfig()
        self._sync_producer: Optional[SyncKafkaProducer] = None
        self._async_producer: Optional[AsyncKafkaProducer] = None
        
        logger.info("KafkaClient initialized")
    
    def get_sync_producer(self) -> SyncKafkaProducer:
        """Get synchronous producer"""
        if self._sync_producer is None:
            self._sync_producer = SyncKafkaProducer(self.config)
        return self._sync_producer
    
    def get_async_producer(self) -> AsyncKafkaProducer:
        """Get asynchronous producer"""
        if self._async_producer is None:
            self._async_producer = AsyncKafkaProducer(self.config)
        return self._async_producer
    
    def get_sync_consumer(
        self,
        topics: Union[str, List[str]],
        group_id: Optional[str] = None
    ) -> SyncKafkaConsumer:
        """Get synchronous consumer"""
        return SyncKafkaConsumer(topics, group_id, self.config)
    
    def get_async_consumer(
        self,
        topics: Union[str, List[str]],
        group_id: Optional[str] = None
    ) -> AsyncKafkaConsumer:
        """Get asynchronous consumer"""
        return AsyncKafkaConsumer(topics, group_id, self.config)
    
    @staticmethod
    def create_topics(
        topics: List[str],
        bootstrap_servers: Union[str, List[str]] = "localhost:9092",
        replication_factor: int = 1,
        num_partitions: int = 3
    ):
        """
        Create topics if they don't exist
        
        Note: Requires kafka-admin or manual creation
        """
        logger.info(f"Creating topics: {topics}")
        # Topic creation would use kafka.admin.KafkaAdminClient
        # This is a placeholder for topic creation logic
        for topic in topics:
            logger.info(f"Topic would be created: {topic}")
    
    @staticmethod
    def list_topics(bootstrap_servers: Union[str, List[str]] = "localhost:9092") -> List[str]:
        """List all available topics"""
        # This would use KafkaAdminClient to list topics
        # Placeholder implementation
        return KafkaTopics.all_topics()
    
    def close(self):
        """Close all connections"""
        if self._sync_producer:
            self._sync_producer.close()
        if self._async_producer:
            asyncio.create_task(self._async_producer.stop())
        logger.info("KafkaClient closed")


# ============================================================================
# Convenience Functions
# ============================================================================

def create_producer(async_mode: bool = False) -> Union[SyncKafkaProducer, AsyncKafkaProducer]:
    """Create a producer (sync or async)"""
    if async_mode:
        return AsyncKafkaProducer()
    return SyncKafkaProducer()


def create_consumer(
    topics: Union[str, List[str]],
    group_id: Optional[str] = None,
    async_mode: bool = False
) -> Union[SyncKafkaConsumer, AsyncKafkaConsumer]:
    """Create a consumer (sync or async)"""
    if async_mode:
        return AsyncKafkaConsumer(topics, group_id)
    return SyncKafkaConsumer(topics, group_id)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Classes
    'KafkaTopics',
    'MessageType',
    'KafkaMessage',
    'KafkaConfig',
    'SyncKafkaProducer',
    'AsyncKafkaProducer',
    'SyncKafkaConsumer',
    'AsyncKafkaConsumer',
    'KafkaClient',
    
    # Functions
    'create_producer',
    'create_consumer',
]
