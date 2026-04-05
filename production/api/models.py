"""
TechNova Support API - Pydantic Models

Request and response models for all endpoints
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class Priority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    URGENT = "urgent"
    ANGRY = "angry"
    FRUSTRATED = "frustrated"


# ============================================================================
# Request Models
# ============================================================================

class SupportSubmitRequest(BaseModel):
    """Support form submission request"""
    email: EmailStr = Field(..., description="Customer email address")
    name: Optional[str] = Field(None, max_length=100, description="Customer name")
    company: Optional[str] = Field(None, max_length=200, description="Company name")
    subject: str = Field(..., min_length=5, max_length=200, description="Request subject")
    message: str = Field(..., min_length=10, max_length=5000, description="Request message")
    category: Optional[str] = Field("general", description="Ticket category")
    priority: Optional[str] = Field("medium", description="Ticket priority")

    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()

    @validator('subject')
    def validate_subject(cls, v):
        return v.strip()

    @validator('message')
    def validate_message(cls, v):
        return v.strip()

class TicketCreateRequest(BaseModel):
    """Ticket creation request"""
    customer_id: str
    subject: str
    message: str
    channel: Channel = Channel.WEB_FORM
    priority: Priority = Priority.P3
    category: Optional[str] = None


class TicketUpdateRequest(BaseModel):
    """Ticket update request"""
    status: Optional[TicketStatus] = None
    priority: Optional[Priority] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None


class CustomerCreateRequest(BaseModel):
    """Customer creation request"""
    email: EmailStr
    name: str
    phone: Optional[str] = None
    company: Optional[str] = None
    account_tier: str = "basic"


class CustomerUpdateRequest(BaseModel):
    """Customer update request"""
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    account_tier: Optional[str] = None
    preferred_channel: Optional[Channel] = None


class EscalationRequest(BaseModel):
    """Escalation request"""
    reason: str
    priority: Priority = Priority.P2
    notes: Optional[str] = None
    target_team: Optional[str] = None


# ============================================================================
# Response Models
# ============================================================================

class SupportSubmitResponse(BaseModel):
    """Support submission response"""
    ticket_id: str
    status: str
    message: str
    email: str
    submitted_at: str


class TicketResponse(BaseModel):
    """Ticket response"""
    ticket_id: str
    customer_id: str
    subject: str
    status: TicketStatus
    priority: Priority
    channel: Channel
    created_at: str
    updated_at: str
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None


class CustomerResponse(BaseModel):
    """Customer response"""
    customer_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    account_tier: str
    total_tickets: int
    created_at: str


class ConversationResponse(BaseModel):
    """Conversation response"""
    conversation_id: str
    customer_id: str
    channel: Channel
    message_count: int
    started_at: str
    last_message_at: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    components: Dict[str, Any]


class MetricsResponse(BaseModel):
    """Metrics response"""
    requests_total: int
    requests_failed: int
    requests_by_endpoint: Dict[str, int]
    average_response_time_ms: float
    uptime_seconds: float
    start_time: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: bool
    status_code: int
    message: str
    path: str
    timestamp: str


class EscalationResponse(BaseModel):
    """Escalation response"""
    ticket_id: str
    escalated: bool
    reason: str
    priority: Priority
    assigned_to: str
    sla_response_time: str


# ============================================================================
# WebSocket Messages
# ============================================================================

class WSMessage(BaseModel):
    """WebSocket message"""
    type: str
    data: Dict[str, Any]
    timestamp: str


class WSTicketUpdate(WSMessage):
    """WebSocket ticket update message"""
    ticket_id: str
    status: TicketStatus
    message: str


class WSEscalationAlert(WSMessage):
    """WebSocket escalation alert message"""
    ticket_id: str
    priority: Priority
    reason: str
