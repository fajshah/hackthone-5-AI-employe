"""
TechNova Customer Support - Workers

Background workers for message processing:
- message_processor: Kafka consumer with agent integration
"""

from .message_processor import (
    MessageProcessor,
    CustomerResolver,
    ConversationManager,
    KafkaMessage,
    ProcessingResult,
    ProcessingStatus,
    MessageSource,
    WorkerConfig,
    create_message_processor,
)

# Import Kafka client for convenience
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from kafka_client import (
        KafkaTopics,
        MessageType,
        KafkaMessage,
        KafkaConfig,
        SyncKafkaProducer,
        AsyncKafkaProducer,
        SyncKafkaConsumer,
        AsyncKafkaConsumer,
        KafkaClient,
        create_producer,
        create_consumer,
    )
except ImportError:
    pass

__version__ = "1.0.0"
__all__ = [
    # Worker classes
    'MessageProcessor',
    'CustomerResolver',
    'ConversationManager',
    'ProcessingResult',
    'ProcessingStatus',
    'MessageSource',
    'WorkerConfig',
    'create_message_processor',
    
    # Kafka client
    'KafkaTopics',
    'MessageType',
    'KafkaMessage',
    'KafkaConfig',
    'SyncKafkaProducer',
    'AsyncKafkaProducer',
    'SyncKafkaConsumer',
    'AsyncKafkaConsumer',
    'KafkaClient',
    'create_producer',
    'create_consumer',
]
