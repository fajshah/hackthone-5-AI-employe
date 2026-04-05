"""
TechNova Customer Support - Channel Handlers

Multi-channel ingestion handlers:
- Gmail (Email)
- WhatsApp (Twilio)
- Web Form (REST API)
"""

from .gmail_handler import (
    GmailHandler,
    GmailClient,
    EmailParser,
    GmailConfig,
)

from .whatsapp_handler import (
    WhatsAppHandler,
    TwilioClient,
    MessageValidator,
    RateLimiter,
    SessionManager,
    WhatsAppConfig,
    create_whatsapp_webhook_app,
)

from .web_form_handler import (
    WebFormHandler,
    FormValidator,
    WebFormRateLimiter,
    CSRFProtection,
    FileUploadHandler,
    WebFormConfig,
    create_webform_app,
)

__version__ = "1.0.0"
__all__ = [
    # Gmail
    "GmailHandler",
    "GmailClient",
    "EmailParser",
    "GmailConfig",
    
    # WhatsApp
    "WhatsAppHandler",
    "TwilioClient",
    "MessageValidator",
    "RateLimiter",
    "SessionManager",
    "WhatsAppConfig",
    "create_whatsapp_webhook_app",
    
    # Web Form
    "WebFormHandler",
    "FormValidator",
    "WebFormRateLimiter",
    "CSRFProtection",
    "FileUploadHandler",
    "WebFormConfig",
    "create_webform_app",
]
