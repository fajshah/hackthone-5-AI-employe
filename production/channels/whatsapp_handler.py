"""
TechNova Customer Support - WhatsApp Handler

Full Twilio WhatsApp API integration with validation.
Supports:
- Incoming message webhook handling
- Outgoing message sending
- Media attachment handling
- Message validation and sanitization
- Session/thread management
- Rate limiting
"""

import os
import re
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps

from twilio.rest import Client
from twilio.request_validator import RequestValidator
from flask import Flask, request, jsonify, abort

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class WhatsAppConfig:
    """WhatsApp/Twilio configuration"""
    
    # Twilio credentials
    ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "+14155238886")  # Twilio sandbox
    
    # Webhook configuration
    WEBHOOK_SECRET = os.getenv("TWILIO_WEBHOOK_SECRET", "")
    WEBHOOK_URL = os.getenv("TWILIO_WEBHOOK_URL", "https://your-domain.com/api/whatsapp/webhook")
    
    # Rate limiting
    RATE_LIMIT_MESSAGES = int(os.getenv("WHATSAPP_RATE_LIMIT_MESSAGES", "10"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("WHATSAPP_RATE_LIMIT_WINDOW", "60"))
    
    # Message validation
    MAX_MESSAGE_LENGTH = int(os.getenv("WHATSAPP_MAX_MESSAGE_LENGTH", "4096"))
    ALLOWED_MEDIA_TYPES = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
        "video/mp4",
        "audio/mpeg"
    ]
    
    # Session management
    SESSION_TIMEOUT_MINUTES = int(os.getenv("WHATSAPP_SESSION_TIMEOUT", "30"))


# ============================================================================
# Twilio Client
# ============================================================================

class TwilioClient:
    """Twilio API client"""
    
    _client = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get authenticated Twilio client"""
        if cls._client is None:
            if not WhatsAppConfig.ACCOUNT_SID or not WhatsAppConfig.AUTH_TOKEN:
                raise ValueError("Twilio credentials not configured")
            
            cls._client = Client(WhatsAppConfig.ACCOUNT_SID, WhatsAppConfig.AUTH_TOKEN)
            logger.info("Twilio client initialized")
        
        return cls._client
    
    @classmethod
    def validate_request(cls, url: str, params: Dict, signature: str) -> bool:
        """Validate Twilio webhook request signature"""
        if not WhatsAppConfig.WEBHOOK_SECRET:
            logger.warning("Webhook secret not configured, skipping validation")
            return True
        
        validator = RequestValidator(WhatsAppConfig.WEBHOOK_SECRET)
        is_valid = validator.validate(url, params, signature)
        
        if not is_valid:
            logger.warning("Invalid Twilio webhook signature")
        
        return is_valid


# ============================================================================
# Message Validator
# ============================================================================

class MessageValidator:
    """Validate and sanitize WhatsApp messages"""
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, str]:
        """Validate WhatsApp phone number format"""
        if not phone:
            return False, "Phone number is required"
        
        # Remove whitespace and special characters
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
        
        # Must start with + followed by digits
        if not re.match(r'^\+\d{10,15}$', cleaned):
            return False, "Invalid phone number format. Use +[country code][number]"
        
        return True, cleaned
    
    @staticmethod
    def validate_message_content(content: str) -> Tuple[bool, str]:
        """Validate message content"""
        if not content:
            return False, "Message content is required"
        
        if len(content) > WhatsAppConfig.MAX_MESSAGE_LENGTH:
            return False, f"Message too long (max {WhatsAppConfig.MAX_MESSAGE_LENGTH} characters)"
        
        # Check for spam patterns
        spam_patterns = [
            r'http[s]?://\S+',  # URLs
            r'\b\d{10,}\b',  # Long numbers
            r'(.)\1{4,}',  # Repeated characters
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Potential spam detected: {content[:50]}")
        
        return True, content.strip()
    
    @staticmethod
    def validate_media(media_type: str, file_size: int) -> Tuple[bool, str]:
        """Validate media attachment"""
        if media_type not in WhatsAppConfig.ALLOWED_MEDIA_TYPES:
            return False, f"Media type {media_type} not allowed"
        
        max_file_size = 16 * 1024 * 1024  # 16MB (WhatsApp limit)
        if file_size > max_file_size:
            return False, f"File too large (max {max_file_size / 1024 / 1024}MB)"
        
        return True, "OK"
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()


# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """Rate limiting for WhatsApp messages"""
    
    _message_counts: Dict[str, List[datetime]] = {}
    
    @classmethod
    def is_rate_limited(cls, phone_number: str) -> Tuple[bool, int]:
        """Check if phone number is rate limited"""
        now = datetime.now()
        window_start = now - timedelta(seconds=WhatsAppConfig.RATE_LIMIT_WINDOW_SECONDS)
        
        # Get message history for this number
        if phone_number not in cls._message_counts:
            cls._message_counts[phone_number] = []
        
        # Clean old messages
        cls._message_counts[phone_number] = [
            msg_time for msg_time in cls._message_counts[phone_number]
            if msg_time > window_start
        ]
        
        # Check rate limit
        message_count = len(cls._message_counts[phone_number])
        if message_count >= WhatsAppConfig.RATE_LIMIT_MESSAGES:
            # Calculate retry after
            oldest_message = min(cls._message_counts[phone_number])
            retry_after = int((oldest_message + timedelta(seconds=WhatsAppConfig.RATE_LIMIT_WINDOW_SECONDS) - now).total_seconds())
            return True, max(1, retry_after)
        
        # Record this message
        cls._message_counts[phone_number].append(now)
        return False, 0
    
    @classmethod
    def get_remaining_messages(cls, phone_number: str) -> int:
        """Get remaining messages in current window"""
        is_limited, _ = cls.is_rate_limited(phone_number)
        if is_limited:
            return 0
        
        now = datetime.now()
        window_start = now - timedelta(seconds=WhatsAppConfig.RATE_LIMIT_WINDOW_SECONDS)
        
        if phone_number not in cls._message_counts:
            return WhatsAppConfig.RATE_LIMIT_MESSAGES
        
        current_count = len([
            msg_time for msg_time in cls._message_counts[phone_number]
            if msg_time > window_start
        ])
        
        return WhatsAppConfig.RATE_LIMIT_MESSAGES - current_count


# ============================================================================
# Session Manager
# ============================================================================

class SessionManager:
    """Manage WhatsApp conversation sessions"""
    
    _sessions: Dict[str, Dict] = {}
    
    @classmethod
    def get_or_create_session(cls, phone_number: str) -> Dict:
        """Get or create session for phone number"""
        now = datetime.now()
        
        if phone_number in cls._sessions:
            session = cls._sessions[phone_number]
            
            # Check if session expired
            last_activity = session.get("last_activity")
            if last_activity:
                last_activity_dt = datetime.fromisoformat(last_activity)
                if now - last_activity_dt > timedelta(minutes=WhatsAppConfig.SESSION_TIMEOUT_MINUTES):
                    # Session expired, create new one
                    logger.info(f"Session expired for {phone_number}, creating new session")
                    del cls._sessions[phone_number]
                else:
                    return session
        
        # Create new session
        session = {
            "phone_number": phone_number,
            "session_id": cls._generate_session_id(phone_number),
            "created_at": now.isoformat(),
            "last_activity": now.isoformat(),
            "message_count": 0,
            "context": {}
        }
        
        cls._sessions[phone_number] = session
        logger.info(f"Created new session for {phone_number}: {session['session_id']}")
        
        return session
    
    @classmethod
    def update_session(cls, phone_number: str, context: Optional[Dict] = None) -> Dict:
        """Update session with new activity"""
        session = cls.get_or_create_session(phone_number)
        session["last_activity"] = datetime.now().isoformat()
        session["message_count"] += 1
        
        if context:
            session["context"].update(context)
        
        return session
    
    @classmethod
    def end_session(cls, phone_number: str) -> bool:
        """End session for phone number"""
        if phone_number in cls._sessions:
            del cls._sessions[phone_number]
            logger.info(f"Ended session for {phone_number}")
            return True
        return False
    
    @staticmethod
    def _generate_session_id(phone_number: str) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().isoformat()
        data = f"{phone_number}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# ============================================================================
# WhatsApp Handler
# ============================================================================

class WhatsAppHandler:
    """Main WhatsApp message handler"""
    
    @staticmethod
    def receive_message(data: Dict) -> Optional[Dict]:
        """
        Receive and process incoming WhatsApp message
        
        Expected Twilio webhook payload:
        {
            "MessageSid": "MMxxxx",
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "Hello",
            "MediaUrl0": "https://...",  # Optional
            "MediaContentType0": "image/jpeg"  # Optional
        }
        """
        try:
            # Extract phone number
            from_number = data.get("From", "")
            if not from_number.startswith("whatsapp:"):
                logger.error(f"Invalid WhatsApp number format: {from_number}")
                return None
            
            phone_number = from_number.replace("whatsapp:", "")
            
            # Validate phone number
            is_valid, result = MessageValidator.validate_phone_number(phone_number)
            if not is_valid:
                logger.error(f"Invalid phone number: {result}")
                return None
            
            # Extract message body
            body = data.get("Body", "")
            is_valid, body = MessageValidator.validate_message_content(body)
            if not is_valid:
                logger.error(f"Invalid message content: {body}")
                return None
            
            # Sanitize input
            body = MessageValidator.sanitize_input(body)
            
            # Check rate limit
            is_limited, retry_after = RateLimiter.is_rate_limited(phone_number)
            if is_limited:
                logger.warning(f"Rate limited: {phone_number}, retry after {retry_after}s")
                return {
                    "error": "rate_limited",
                    "retry_after": retry_after,
                    "remaining": 0
                }
            
            # Get or create session
            session = SessionManager.update_session(phone_number)
            
            # Extract media if present
            media = []
            media_index = 0
            while f"MediaUrl{media_index}" in data:
                media_url = data.get(f"MediaUrl{media_index}")
                media_type = data.get(f"MediaContentType{media_index}", "unknown")
                
                # Validate media
                is_valid, msg = MessageValidator.validate_media(media_type, 0)
                if is_valid:
                    media.append({
                        "url": media_url,
                        "type": media_type,
                        "index": media_index
                    })
                
                media_index += 1
            
            # Build normalized message
            message = {
                "message_id": data.get("MessageSid"),
                "channel": "whatsapp",
                "from": {
                    "phone": phone_number,
                    "raw": from_number
                },
                "to": data.get("To", "").replace("whatsapp:", ""),
                "body": body,
                "media": media,
                "timestamp": data.get("Timestamp", datetime.now().isoformat()),
                "session_id": session["session_id"],
                "conversation_id": session["session_id"],  # Use session as conversation
                "metadata": {
                    "twilio_message_sid": data.get("MessageSid"),
                    "num_media": len(media),
                    "rate_limit_remaining": RateLimiter.get_remaining_messages(phone_number)
                }
            }
            
            logger.info(f"Received WhatsApp message from {phone_number}: {body[:50]}...")
            return message
            
        except Exception as e:
            logger.error(f"Failed to process WhatsApp message: {e}")
            return None
    
    @staticmethod
    def send_message(
        to: str,
        body: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Send WhatsApp message via Twilio
        
        Args:
            to: Recipient phone number (with country code, e.g., +1234567890)
            body: Message text
            media_url: Optional media URL to attach
            media_type: Optional media type (image/jpeg, etc.)
            in_reply_to: Optional message SID to reply to
        
        Returns:
            Dict with message_id, status, etc. or None if failed
        """
        try:
            client = TwilioClient.get_client()
            
            # Validate recipient
            is_valid, result = MessageValidator.validate_phone_number(to)
            if not is_valid:
                logger.error(f"Invalid recipient number: {result}")
                return None
            
            phone_number = result
            
            # Validate message content
            is_valid, body = MessageValidator.validate_message_content(body)
            if not is_valid:
                logger.error(f"Invalid message content: {body}")
                return None
            
            # Build message parameters
            message_params = {
                "body": body,
                "from_": f"whatsapp:{WhatsAppConfig.WHATSAPP_NUMBER}",
                "to": f"whatsapp:{phone_number}"
            }
            
            # Add media if provided
            if media_url:
                message_params["media_url"] = media_url
            
            # Send message
            message = client.messages.create(**message_params)
            
            logger.info(f"WhatsApp message sent to {phone_number}: {message.sid}")
            
            # Update session
            SessionManager.update_session(phone_number, {"last_message_sid": message.sid})
            
            return {
                "message_id": message.sid,
                "status": message.status,
                "to": phone_number,
                "body": body,
                "timestamp": message.date_created.isoformat() if message.date_created else datetime.now().isoformat(),
                "error_code": message.error_code,
                "error_message": message.error_message
            }
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return None
    
    @staticmethod
    def send_template_message(
        to: str,
        template_name: str,
        template_params: List[str],
        language: str = "en"
    ) -> Optional[Dict]:
        """
        Send WhatsApp template message (for business-initiated conversations)
        
        Args:
            to: Recipient phone number
            template_name: Name of approved WhatsApp template
            template_params: List of template parameters
            language: Template language code
        
        Returns:
            Dict with message details or None if failed
        """
        try:
            client = TwilioClient.get_client()
            
            # Validate recipient
            is_valid, result = MessageValidator.validate_phone_number(to)
            if not is_valid:
                return None
            
            phone_number = result
            
            # Send template message
            message = client.messages.create(
                content_sid=template_name,  # Template SID
                content_variables=json.dumps(template_params),
                from_=f"whatsapp:{WhatsAppConfig.WHATSAPP_NUMBER}",
                to=f"whatsapp:{phone_number}"
            )
            
            logger.info(f"WhatsApp template message sent: {message.sid}")
            
            return {
                "message_id": message.sid,
                "status": message.status,
                "template": template_name
            }
            
        except Exception as e:
            logger.error(f"Failed to send template message: {e}")
            return None
    
    @staticmethod
    def get_message_status(message_sid: str) -> Optional[Dict]:
        """Get message delivery status"""
        try:
            client = TwilioClient.get_client()
            message = client.messages(message_sid).fetch()
            
            return {
                "message_id": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "date_created": message.date_created.isoformat() if message.date_created else None,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "date_updated": message.date_updated.isoformat() if message.date_updated else None,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
            
        except Exception as e:
            logger.error(f"Failed to get message status: {e}")
            return None


# ============================================================================
# Flask Webhook Handler
# ============================================================================

def create_whatsapp_webhook_app() -> Flask:
    """Create Flask app for WhatsApp webhook"""
    app = Flask(__name__)
    
    @app.route("/api/whatsapp/webhook", methods=["POST"])
    def whatsapp_webhook():
        """Handle incoming WhatsApp messages from Twilio"""
        
        # Validate Twilio signature
        signature = request.headers.get("X-Twilio-Signature", "")
        is_valid = TwilioClient.validate_request(
            url=request.url,
            params=dict(request.form),
            signature=signature
        )
        
        if not is_valid:
            logger.warning("Invalid webhook signature")
            abort(403)
        
        # Process message
        message_data = WhatsAppHandler.receive_message(dict(request.form))
        
        if message_data is None:
            return jsonify({"error": "Failed to process message"}), 400
        
        if message_data.get("error") == "rate_limited":
            return jsonify({
                "error": "Rate limit exceeded",
                "retry_after": message_data["retry_after"]
            }), 429
        
        # Return success (Twilio expects 200 OK)
        return jsonify({
            "status": "received",
            "message_id": message_data["message_id"],
            "session_id": message_data["session_id"]
        }), 200
    
    @app.route("/api/whatsapp/health", methods=["GET"])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "whatsapp-handler",
            "timestamp": datetime.now().isoformat()
        }), 200
    
    return app


# ============================================================================
# Usage Example
# ============================================================================

"""
# Option 1: Run as Flask webhook app
from channels.whatsapp_handler import create_whatsapp_webhook_app

app = create_whatsapp_webhook_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

# Option 2: Use handler directly
from channels.whatsapp_handler import WhatsAppHandler

# Send message
result = WhatsAppHandler.send_message(
    to="+1234567890",
    body="Hello from TechNova Support!",
    media_url="https://example.com/image.jpg",
    media_type="image/jpeg"
)

print(f"Message sent: {result}")

# Get message status
status = WhatsAppHandler.get_message_status(result["message_id"])
print(f"Message status: {status['status']}")

# Receive message (from webhook)
message = WhatsAppHandler.receive_message(request.form)
if message:
    print(f"Received: {message['body']}")
"""
