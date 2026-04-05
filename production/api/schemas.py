"""
TechNova Support API - Schemas

Additional schema definitions
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional


class WebhookValidationResult(BaseModel):
    """Webhook validation result"""
    is_valid: bool
    source: str
    message_id: Optional[str] = None
    error: Optional[str] = None


class KafkaPublishResult(BaseModel):
    """Kafka publish result"""
    success: bool
    topic: str
    message_id: str
    partition: Optional[int] = None
    offset: Optional[int] = None
    error: Optional[str] = None
