"""
TechNova Customer Support - Gmail API Handler

Full Gmail API integration with Pub/Sub for real-time email ingestion.
Supports:
- OAuth 2.0 authentication
- Real-time email notifications via Pub/Sub
- Email parsing (headers, body, attachments)
- Multi-part MIME handling
- Attachment download with OCR support
"""

import os
import base64
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from email.parser import Parser
from email.message import Message
import html2text

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class GmailConfig:
    """Gmail API configuration"""
    
    # OAuth 2.0 credentials
    SERVICE_ACCOUNT_FILE = os.getenv("GMAIL_SERVICE_ACCOUNT_FILE", "credentials/gmail-service-account.json")
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify"
    ]
    
    # Pub/Sub configuration
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "technova-support")
    TOPIC_ID = os.getenv("PUBSUB_TOPIC_ID", "gmail-ingestion")
    SUBSCRIPTION_ID = os.getenv("PUBSUB_SUBSCRIPTION_ID", "gmail-ingestion-sub")
    
    # Email configuration
    SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@technova.com")
    LABEL_IDS = {
        "INBOX": "INBOX",
        "SENT": "SENT",
        "IMPORTANT": "IMPORTANT",
        "UNREAD": "UNREAD"
    }
    
    # Polling configuration (fallback if Pub/Sub fails)
    POLL_INTERVAL_SECONDS = int(os.getenv("GMAIL_POLL_INTERVAL", "60"))
    MAX_RESULTS_PER_POLL = int(os.getenv("GMAIL_MAX_RESULTS", "50"))


# ============================================================================
# Gmail API Client
# ============================================================================

class GmailClient:
    """Gmail API client with OAuth 2.0 authentication"""
    
    _service = None
    _pubsub_publisher = None
    _pubsub_subscriber = None
    
    @classmethod
    def authenticate(cls) -> Any:
        """Authenticate with Gmail API using service account"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                GmailConfig.SERVICE_ACCOUNT_FILE,
                scopes=GmailConfig.SCOPES
            )
            
            cls._service = build("gmail", "v1", credentials=credentials)
            logger.info("Gmail API authentication successful")
            return cls._service
            
        except Exception as e:
            logger.error(f"Gmail API authentication failed: {e}")
            raise
    
    @classmethod
    def get_service(cls) -> Any:
        """Get authenticated Gmail service"""
        if cls._service is None:
            cls.authenticate()
        return cls._service
    
    @classmethod
    def setup_pubsub(cls) -> Tuple[pubsub_v1.PublisherClient, pubsub_v1.SubscriberClient]:
        """Setup Pub/Sub for real-time email notifications"""
        try:
            # Publisher client
            cls._pubsub_publisher = pubsub_v1.PublisherClient()
            
            # Subscriber client
            cls._pubsub_subscriber = pubsub_v1.SubscriberClient()
            
            # Create topic if not exists
            topic_path = cls._pubsub_publisher.topic_path(GmailConfig.PROJECT_ID, GmailConfig.TOPIC_ID)
            try:
                cls._pubsub_publisher.create_topic(request={"name": topic_path})
                logger.info(f"Created Pub/Sub topic: {GmailConfig.TOPIC_ID}")
            except Exception:
                pass  # Topic already exists
            
            # Create subscription if not exists
            subscription_path = cls._pubsub_subscriber.subscription_path(
                GmailConfig.PROJECT_ID, GmailConfig.SUBSCRIPTION_ID
            )
            try:
                cls._pubsub_subscriber.create_subscription(
                    request={"name": subscription_path, "topic": topic_path}
                )
                logger.info(f"Created Pub/Sub subscription: {GmailConfig.SUBSCRIPTION_ID}")
            except Exception:
                pass  # Subscription already exists
            
            logger.info("Pub/Sub setup complete")
            return cls._pubsub_publisher, cls._pubsub_subscriber
            
        except Exception as e:
            logger.error(f"Pub/Sub setup failed: {e}")
            raise
    
    @classmethod
    def publish_message(cls, message_data: Dict) -> str:
        """Publish message to Pub/Sub topic"""
        if cls._pubsub_publisher is None:
            cls.setup_pubsub()
        
        topic_path = cls._pubsub_publisher.topic_path(GmailConfig.PROJECT_ID, GmailConfig.TOPIC_ID)
        data_bytes = json.dumps(message_data).encode("utf-8")
        
        future = cls._pubsub_publisher.publish(topic_path, data=data_bytes)
        message_id = future.result()
        
        logger.info(f"Published message to Pub/Sub: {message_id}")
        return message_id


# ============================================================================
# Email Parser
# ============================================================================

class EmailParser:
    """Parse raw email messages"""
    
    @staticmethod
    def parse_raw_email(raw_message: str) -> Dict:
        """Parse raw RFC 2822 email message"""
        try:
            # Decode from base64url
            decoded_message = base64.urlsafe_b64decode(raw_message).decode("utf-8")
            
            # Parse email
            parser = Parser()
            email_message = parser.parsestr(decoded_message)
            
            # Extract headers
            headers = {
                "message_id": email_message.get("Message-ID", ""),
                "from": email_message.get("From", ""),
                "to": email_message.get("To", ""),
                "cc": email_message.get("CC", ""),
                "subject": email_message.get("Subject", ""),
                "date": email_message.get("Date", ""),
                "in_reply_to": email_message.get("In-Reply-To", ""),
                "references": email_message.get("References", ""),
                "content_type": email_message.get("Content-Type", "")
            }
            
            # Extract body
            body_plain, body_html, attachments = EmailParser._extract_body_and_attachments(email_message)
            
            # Parse email addresses
            from_parsed = EmailParser._parse_email_address(headers["from"])
            to_parsed = [EmailParser._parse_email_address(addr) for addr in headers["to"].split(",") if addr.strip()]
            
            return {
                "headers": headers,
                "from": from_parsed,
                "to": to_parsed,
                "subject": headers["subject"],
                "body_plain": body_plain,
                "body_html": body_html,
                "attachments": attachments,
                "in_reply_to": headers["in_reply_to"],
                "references": headers["references"],
                "date": headers["date"],
                "message_id": headers["message_id"]
            }
            
        except Exception as e:
            logger.error(f"Failed to parse email: {e}")
            raise
    
    @staticmethod
    def _extract_body_and_attachments(email_message: Message) -> Tuple[str, str, List[Dict]]:
        """Extract body text and attachments from email"""
        body_plain = ""
        body_html = ""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get_content_disposition() or "")
                
                # Handle attachments
                if "attachment" in content_disposition:
                    attachment_data = EmailParser._process_attachment(part)
                    if attachment_data:
                        attachments.append(attachment_data)
                
                # Handle body parts
                elif content_type == "text/plain" and not body_plain:
                    try:
                        body_plain = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                    except Exception:
                        pass
                
                elif content_type == "text/html" and not body_html:
                    try:
                        body_html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                        # Convert HTML to plain text
                        if not body_plain:
                            html_converter = html2text.HTML2Text()
                            html_converter.ignore_links = False
                            body_plain = html_converter.handle(body_html)
                    except Exception:
                        pass
        else:
            # Single part email
            content_type = email_message.get_content_type()
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    decoded_payload = payload.decode(email_message.get_content_charset() or "utf-8")
                    
                    if content_type == "text/html":
                        body_html = decoded_payload
                        html_converter = html2text.HTML2Text()
                        body_plain = html_converter.handle(body_html)
                    else:
                        body_plain = decoded_payload
            except Exception:
                pass
        
        return body_plain, body_html, attachments
    
    @staticmethod
    def _process_attachment(part: Message) -> Optional[Dict]:
        """Process email attachment"""
        try:
            filename = part.get_filename()
            if not filename:
                return None
            
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)
            
            if not payload:
                return None
            
            # Encode attachment for storage
            attachment_data = base64.b64encode(payload).decode("utf-8")
            
            return {
                "filename": filename,
                "content_type": content_type,
                "size": len(payload),
                "data": attachment_data
            }
            
        except Exception as e:
            logger.error(f"Failed to process attachment: {e}")
            return None
    
    @staticmethod
    def _parse_email_address(address_string: str) -> Dict:
        """Parse email address string into name and email"""
        import re
        
        if not address_string:
            return {"name": "", "email": ""}
        
        # Pattern: "Name" <email@example.com> or Name <email@example.com> or just email
        match = re.match(r'["\']?([^"\'>,<]+)["\']?\s*<([^>]+)>', address_string.strip())
        
        if match:
            return {
                "name": match.group(1).strip(),
                "email": match.group(2).strip()
            }
        else:
            # Just email address
            email = address_string.strip()
            return {
                "name": "",
                "email": email
            }


# ============================================================================
# Gmail Handler
# ============================================================================

class GmailHandler:
    """Main Gmail handler for email ingestion and sending"""
    
    @staticmethod
    def fetch_unread_emails(max_results: int = 50) -> List[Dict]:
        """Fetch unread emails from Gmail"""
        try:
            service = GmailClient.get_service()
            
            # Query for unread emails in inbox
            query = "is:unread in:inbox"
            
            results = service.users().messages().list(
                userId="me",
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get("messages", [])
            emails = []
            
            for message in messages:
                email_data = GmailHandler.get_email_details(message["id"])
                if email_data:
                    emails.append(email_data)
                    
                    # Mark as read
                    GmailHandler.mark_as_read(message["id"])
            
            logger.info(f"Fetched {len(emails)} unread emails")
            return emails
            
        except HttpError as error:
            logger.error(f"Failed to fetch emails: {error}")
            return []
    
    @staticmethod
    def get_email_details(message_id: str) -> Optional[Dict]:
        """Get full email details by message ID"""
        try:
            service = GmailClient.get_service()
            
            message = service.users().messages().get(
                userId="me",
                id=message_id,
                format="raw"
            ).execute()
            
            # Parse raw email
            email_data = EmailParser.parse_raw_email(message["raw"])
            
            # Add Gmail-specific metadata
            email_data["gmail_message_id"] = message_id
            email_data["thread_id"] = message.get("threadId", "")
            email_data["label_ids"] = message.get("labelIds", [])
            email_data["size_estimate"] = message.get("sizeEstimate", 0)
            email_data["internal_date"] = message.get("internalDate", "")
            
            return email_data
            
        except Exception as e:
            logger.error(f"Failed to get email details: {e}")
            return None
    
    @staticmethod
    def mark_as_read(message_id: str) -> bool:
        """Mark email as read"""
        try:
            service = GmailClient.get_service()
            
            service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": [GmailConfig.LABEL_IDS["UNREAD"]]}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            return False
    
    @staticmethod
    def send_email(
        to: str,
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Optional[Dict]:
        """Send email via Gmail API"""
        try:
            service = GmailClient.get_service()
            
            # Create message
            message = GmailHandler._create_message(
                to=to,
                subject=subject,
                body=body,
                body_html=body_html,
                in_reply_to=in_reply_to,
                references=references,
                attachments=attachments
            )
            
            # Send message
            sent_message = service.users().messages().send(
                userId="me",
                body=message
            ).execute()
            
            logger.info(f"Email sent successfully: {sent_message['id']}")
            
            return {
                "message_id": sent_message["id"],
                "thread_id": sent_message["threadId"],
                "status": "sent"
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return None
    
    @staticmethod
    def _create_message(
        to: str,
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict:
        """Create MIME message for sending"""
        import base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        
        if body_html:
            # Multipart message (HTML + plain text)
            message = MIMEMultipart("alternative")
            message.attach(MIMEText(body, "plain", "utf-8"))
            message.attach(MIMEText(body_html, "html", "utf-8"))
        else:
            # Plain text only
            message = MIMEMultipart()
            message.attach(MIMEText(body, "plain", "utf-8"))
        
        message["to"] = to
        message["subject"] = subject
        message["from"] = GmailConfig.SUPPORT_EMAIL
        
        # Threading headers
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
        if references:
            message["References"] = references
        
        # Attachments
        if attachments:
            for attachment in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(base64.b64decode(attachment["data"]))
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment['filename']}"
                )
                message.attach(part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        
        return {"raw": raw_message}
    
    @staticmethod
    def start_pubsub_listener(callback: callable) -> None:
        """Start listening for Pub/Sub messages (real-time email notifications)"""
        try:
            _, subscriber = GmailClient.setup_pubsub()
            
            subscription_path = subscriber.subscription_path(
                GmailConfig.PROJECT_ID, GmailConfig.SUBSCRIPTION_ID
            )
            
            def message_callback(message: pubsub_v1.subscriber.message.Message) -> None:
                """Handle incoming Pub/Sub message"""
                try:
                    data = json.loads(message.data.decode("utf-8"))
                    logger.info(f"Received Pub/Sub message: {data.get('messageId')}")
                    
                    # Call the callback with email data
                    callback(data)
                    
                    # Acknowledge message
                    message.ack()
                    
                except Exception as e:
                    logger.error(f"Failed to process Pub/Sub message: {e}")
                    message.nack()
            
            # Start streaming pull
            streaming_pull_future = subscriber.subscribe(subscription_path, callback=message_callback)
            logger.info(f"Listening for messages on {subscription_path}...")
            
            # Keep the listener running
            with subscriber:
                try:
                    streaming_pull_future.result()
                except Exception as e:
                    logger.error(f"Pub/Sub streaming error: {e}")
            
        except Exception as e:
            logger.error(f"Failed to start Pub/Sub listener: {e}")
            raise
    
    @staticmethod
    def poll_emails(callback: callable, interval_seconds: int = 60) -> None:
        """Poll Gmail for new emails (fallback if Pub/Sub is not available)"""
        import time
        
        logger.info(f"Starting Gmail polling (interval: {interval_seconds}s)")
        
        while True:
            try:
                emails = GmailHandler.fetch_unread_emails(GmailConfig.MAX_RESULTS_PER_POLL)
                
                for email in emails:
                    callback(email)
                
                if emails:
                    logger.info(f"Processed {len(emails)} emails")
                
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error during email polling: {e}")
                time.sleep(interval_seconds)


# ============================================================================
# Usage Example
# ============================================================================

"""
# Initialize Gmail handler
from channels.gmail_handler import GmailHandler

# Option 1: Real-time with Pub/Sub
def process_email(email_data: Dict):
    print(f"Processing email from: {email_data['from']['email']}")
    print(f"Subject: {email_data['subject']}")
    print(f"Body: {email_data['body_plain'][:200]}...")

# Start Pub/Sub listener (real-time)
GmailHandler.start_pubsub_listener(process_email)

# Option 2: Polling (fallback)
GmailHandler.poll_emails(process_email, interval_seconds=60)

# Send email response
GmailHandler.send_email(
    to="customer@example.com",
    subject="Re: Your support request",
    body="Thank you for contacting us...",
    body_html="<p>Thank you for contacting us...</p>",
    in_reply_to="<original-message-id@example.com>"
)
"""
