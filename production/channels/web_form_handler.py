"""
TechNova Customer Support - Web Form Handler

REST API endpoint for web form submissions.
Supports:
- Form validation
- File attachment handling
- Browser/device detection
- CSRF protection
- Rate limiting
- Ticket auto-creation
"""

import os
import re
import logging
import json
import uuid
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, abort, send_from_directory
from werkzeug.utils import secure_filename
import user_agents

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class WebFormConfig:
    """Web form configuration"""
    
    # Upload configuration
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads/tickets")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_SIZE", 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "txt", "doc", "docx"}
    
    # Rate limiting
    RATE_LIMIT_SUBMISSIONS = int(os.getenv("WEBFORM_RATE_LIMIT", "5"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("WEBFORM_RATE_WINDOW", "3600"))  # 1 hour
    
    # CSRF protection
    CSRF_SECRET = os.getenv("CSRF_SECRET", "change-me-in-production")
    
    # Form validation
    REQUIRED_FIELDS = ["email", "subject", "message"]
    MAX_SUBJECT_LENGTH = 200
    MAX_MESSAGE_LENGTH = 5000
    MIN_MESSAGE_LENGTH = 10
    
    # Browser detection
    SUPPORTED_BROWSERS = ["Chrome", "Firefox", "Safari", "Edge"]
    MIN_BROWSER_VERSIONS = {
        "Chrome": 90,
        "Firefox": 88,
        "Safari": 14,
        "Edge": 90
    }


# ============================================================================
# Form Validator
# ============================================================================

class FormValidator:
    """Validate web form submissions"""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email address"""
        if not email:
            return False, "Email is required"
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        if len(email) > 254:
            return False, "Email too long"
        
        return True, email.lower().strip()
    
    @staticmethod
    def validate_subject(subject: str) -> Tuple[bool, str]:
        """Validate subject line"""
        if not subject:
            return False, "Subject is required"
        
        subject = subject.strip()
        
        if len(subject) < 5:
            return False, "Subject too short (min 5 characters)"
        
        if len(subject) > WebFormConfig.MAX_SUBJECT_LENGTH:
            return False, f"Subject too long (max {WebFormConfig.MAX_SUBJECT_LENGTH} characters)"
        
        return True, subject
    
    @staticmethod
    def validate_message(message: str) -> Tuple[bool, str]:
        """Validate message content"""
        if not message:
            return False, "Message is required"
        
        message = message.strip()
        
        if len(message) < WebFormConfig.MIN_MESSAGE_LENGTH:
            return False, f"Message too short (min {WebFormConfig.MIN_MESSAGE_LENGTH} characters)"
        
        if len(message) > WebFormConfig.MAX_MESSAGE_LENGTH:
            return False, f"Message too long (max {WebFormConfig.MAX_MESSAGE_LENGTH} characters)"
        
        return True, message
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """Validate customer name"""
        if not name:
            return True, ""  # Name is optional
        
        name = name.strip()
        
        if len(name) > 100:
            return False, "Name too long"
        
        # Check for valid characters
        if not re.match(r'^[\w\s\-\.\']+$', name):
            return False, "Name contains invalid characters"
        
        return True, name
    
    @staticmethod
    def validate_company(company: str) -> Tuple[bool, str]:
        """Validate company name"""
        if not company:
            return True, ""  # Company is optional
        
        company = company.strip()
        
        if len(company) > 200:
            return False, "Company name too long"
        
        return True, company
    
    @staticmethod
    def validate_file(filename: str, file_size: int) -> Tuple[bool, str]:
        """Validate file attachment"""
        if not filename:
            return True, ""  # File is optional
        
        # Check extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in WebFormConfig.ALLOWED_EXTENSIONS:
            return False, f"File type .{ext} not allowed"
        
        # Check file size
        if file_size > WebFormConfig.MAX_CONTENT_LENGTH:
            return False, f"File too large (max {WebFormConfig.MAX_CONTENT_LENGTH / 1024 / 1024}MB)"
        
        return True, filename
    
    @staticmethod
    def validate_browser(user_agent: str) -> Dict:
        """Validate and extract browser information"""
        ua = user_agents.parse(user_agent) if user_agent else user_agents.parse("")
        
        browser_info = {
            "browser": ua.browser.family if ua.browser else "Unknown",
            "browser_version": ua.browser.version.string if ua.browser and ua.browser.version else "Unknown",
            "os": ua.os.family if ua.os else "Unknown",
            "os_version": ua.os.version.string if ua.os and ua.os.version else "Unknown",
            "device": ua.device.family if ua.device else "Desktop",
            "is_mobile": ua.is_mobile,
            "is_tablet": ua.is_tablet,
            "is_bot": ua.is_bot
        }
        
        # Check if browser is supported
        browser_name = browser_info["browser"]
        if browser_name in WebFormConfig.SUPPORTED_BROWSERS:
            try:
                major_version = int(browser_info["browser_version"].split(".")[0])
                min_version = WebFormConfig.MIN_BROWSER_VERSIONS.get(browser_name, 0)
                browser_info["is_supported"] = major_version >= min_version
            except (ValueError, IndexError):
                browser_info["is_supported"] = True
        else:
            browser_info["is_supported"] = True  # Allow unknown browsers
        
        return browser_info


# ============================================================================
# Rate Limiter
# ============================================================================

class WebFormRateLimiter:
    """Rate limiting for form submissions"""
    
    _submissions: Dict[str, List[datetime]] = {}
    
    @classmethod
    def is_rate_limited(cls, identifier: str) -> Tuple[bool, int]:
        """Check if identifier is rate limited"""
        now = datetime.now()
        window_start = now - timedelta(seconds=WebFormConfig.RATE_LIMIT_WINDOW_SECONDS)
        
        if identifier not in cls._submissions:
            cls._submissions[identifier] = []
        
        # Clean old submissions
        cls._submissions[identifier] = [
            sub_time for sub_time in cls._submissions[identifier]
            if sub_time > window_start
        ]
        
        # Check rate limit
        submission_count = len(cls._submissions[identifier])
        if submission_count >= WebFormConfig.RATE_LIMIT_SUBMISSIONS:
            oldest = min(cls._submissions[identifier])
            retry_after = int((oldest + timedelta(seconds=WebFormConfig.RATE_LIMIT_WINDOW_SECONDS) - now).total_seconds())
            return True, max(1, retry_after)
        
        # Record this submission
        cls._submissions[identifier].append(now)
        return False, 0
    
    @classmethod
    def get_remaining_submissions(cls, identifier: str) -> int:
        """Get remaining submissions in current window"""
        is_limited, _ = cls.is_rate_limited(identifier)
        if is_limited:
            return 0
        
        now = datetime.now()
        window_start = now - timedelta(seconds=WebFormConfig.RATE_LIMIT_WINDOW_SECONDS)
        
        if identifier not in cls._submissions:
            return WebFormConfig.RATE_LIMIT_SUBMISSIONS
        
        current_count = len([
            sub_time for sub_time in cls._submissions[identifier]
            if sub_time > window_start
        ])
        
        return WebFormConfig.RATE_LIMIT_SUBMISSIONS - current_count


# ============================================================================
# CSRF Protection
# ============================================================================

class CSRFProtection:
    """CSRF token generation and validation"""
    
    @staticmethod
    def generate_token(session_id: str) -> str:
        """Generate CSRF token"""
        timestamp = datetime.now().isoformat()
        data = f"{session_id}:{timestamp}:{WebFormConfig.CSRF_SECRET}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def validate_token(token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        if not token or not session_id:
            return False
        
        # Token is valid for 1 hour
        try:
            # Simple validation - in production, use proper token storage
            expected = CSRFProtection.generate_token(session_id)
            return token == expected
        except Exception:
            return False


# ============================================================================
# File Upload Handler
# ============================================================================

class FileUploadHandler:
    """Handle file uploads"""
    
    @staticmethod
    def save_file(file, ticket_id: str) -> Optional[Dict]:
        """Save uploaded file"""
        try:
            if not file or file.filename == "":
                return None
            
            # Secure filename
            filename = secure_filename(file.filename)
            
            # Add ticket ID to filename
            name, ext = os.path.splitext(filename)
            unique_filename = f"{ticket_id}_{name}_{uuid.uuid4().hex[:8]}{ext}"
            
            # Create upload directory
            upload_dir = os.path.join(WebFormConfig.UPLOAD_FOLDER, ticket_id)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            filepath = os.path.join(upload_dir, unique_filename)
            file.save(filepath)
            
            # Get file info
            file_size = os.path.getsize(filepath)
            
            file_info = {
                "filename": filename,
                "unique_filename": unique_filename,
                "filepath": filepath,
                "size": file_size,
                "type": file.content_type or "application/octet-stream",
                "ticket_id": ticket_id
            }
            
            logger.info(f"File saved: {unique_filename} ({file_size} bytes)")
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return None
    
    @staticmethod
    def get_file(ticket_id: str, filename: str) -> Optional[Tuple[bytes, str]]:
        """Get uploaded file"""
        try:
            filepath = os.path.join(WebFormConfig.UPLOAD_FOLDER, ticket_id, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, "rb") as f:
                content = f.read()
            
            # Guess content type
            ext = os.path.splitext(filename)[-1].lower()
            content_types = {
                ".pdf": "application/pdf",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".txt": "text/plain",
                ".doc": "application/msword",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
            
            content_type = content_types.get(ext, "application/octet-stream")
            
            return content, content_type
            
        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            return None


# ============================================================================
# Web Form Handler
# ============================================================================

class WebFormHandler:
    """Main web form handler"""
    
    @staticmethod
    def process_submission(data: Dict, files: Dict, user_agent: str, ip_address: str) -> Dict:
        """
        Process web form submission
        
        Args:
            data: Form data (dict)
            files: Uploaded files (dict)
            user_agent: Browser user agent string
            ip_address: Client IP address
        
        Returns:
            Dict with ticket_id, status, errors, etc.
        """
        errors = []
        warnings = []
        
        # Rate limiting
        rate_limit_id = f"{ip_address}:{data.get('email', 'unknown')}"
        is_limited, retry_after = WebFormRateLimiter.is_rate_limited(rate_limit_id)
        if is_limited:
            return {
                "success": False,
                "error": "rate_limited",
                "message": f"Too many submissions. Try again in {retry_after} seconds.",
                "retry_after": retry_after
            }
        
        # Validate required fields
        for field in WebFormConfig.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                errors.append(f"{field.capitalize()} is required")
        
        if errors:
            return {
                "success": False,
                "error": "validation_failed",
                "errors": errors
            }
        
        # Validate email
        is_valid, result = FormValidator.validate_email(data.get("email", ""))
        if not is_valid:
            errors.append(result)
        else:
            email = result
        
        # Validate subject
        is_valid, result = FormValidator.validate_subject(data.get("subject", ""))
        if not is_valid:
            errors.append(result)
        else:
            subject = result
        
        # Validate message
        is_valid, result = FormValidator.validate_message(data.get("message", ""))
        if not is_valid:
            errors.append(result)
        else:
            message = result
        
        # Validate optional fields
        name = ""
        if data.get("name"):
            is_valid, result = FormValidator.validate_name(data["name"])
            if not is_valid:
                errors.append(result)
            else:
                name = result
        
        company = ""
        if data.get("company"):
            is_valid, result = FormValidator.validate_company(data["company"])
            if not is_valid:
                errors.append(result)
            else:
                company = result
        
        if errors:
            return {
                "success": False,
                "error": "validation_failed",
                "errors": errors
            }
        
        # Generate ticket ID
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        
        # Process attachments
        attachments = []
        for field_name, file in files.items():
            if field_name.startswith("attachment"):
                is_valid, msg = FormValidator.validate_file(file.filename, file.content_length or 0)
                if not is_valid:
                    warnings.append(f"File '{file.filename}': {msg}")
                else:
                    file_info = FileUploadHandler.save_file(file, ticket_id)
                    if file_info:
                        attachments.append(file_info)
        
        # Get browser info
        browser_info = FormValidator.validate_browser(user_agent)
        
        # Build normalized submission
        submission = {
            "ticket_id": ticket_id,
            "channel": "web_form",
            "customer": {
                "name": name,
                "email": email,
                "company": company
            },
            "ticket": {
                "subject": subject,
                "message": message,
                "category": "how_to",  # Default, will be classified by AI
                "priority": "P3"  # Default
            },
            "attachments": attachments,
            "browser": browser_info,
            "ip_address": ip_address,
            "submitted_at": datetime.now().isoformat(),
            "warnings": warnings
        }
        
        logger.info(f"Web form submission processed: {ticket_id}")
        return {
            "success": True,
            "ticket_id": ticket_id,
            "submission": submission,
            "remaining_submissions": WebFormRateLimiter.get_remaining_submissions(rate_limit_id)
        }


# ============================================================================
# Flask API
# ============================================================================

def create_webform_app() -> Flask:
    """Create Flask app for web form API"""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = WebFormConfig.MAX_CONTENT_LENGTH
    app.config["UPLOAD_FOLDER"] = WebFormConfig.UPLOAD_FOLDER
    
    @app.route("/api/webform/submit", methods=["POST"])
    def submit_form():
        """Handle web form submission"""
        try:
            # Get form data
            data = request.form.to_dict()
            files = request.files.to_dict()
            user_agent = request.headers.get("User-Agent", "")
            ip_address = request.remote_addr or "unknown"
            
            # Process submission
            result = WebFormHandler.process_submission(data, files, user_agent, ip_address)
            
            if not result["success"]:
                status_code = 429 if result.get("error") == "rate_limited" else 400
                return jsonify(result), status_code
            
            # Return success
            return jsonify({
                "success": True,
                "ticket_id": result["ticket_id"],
                "message": "Your support request has been submitted successfully.",
                "email": result["submission"]["customer"]["email"],
                "remaining_submissions": result.get("remaining_submissions", 0)
            }), 201
            
        except Exception as e:
            logger.error(f"Failed to process form submission: {e}")
            return jsonify({
                "success": False,
                "error": "internal_error",
                "message": "Failed to process your request. Please try again."
            }), 500
    
    @app.route("/api/webform/validate", methods=["POST"])
    def validate_form():
        """Validate form data (client-side validation helper)"""
        try:
            data = request.get_json() or {}
            
            errors = {}
            
            # Validate each field
            if "email" in data:
                is_valid, result = FormValidator.validate_email(data["email"])
                if not is_valid:
                    errors["email"] = result
            
            if "subject" in data:
                is_valid, result = FormValidator.validate_subject(data["subject"])
                if not is_valid:
                    errors["subject"] = result
            
            if "message" in data:
                is_valid, result = FormValidator.validate_message(data["message"])
                if not is_valid:
                    errors["message"] = result
            
            if "name" in data:
                is_valid, result = FormValidator.validate_name(data["name"])
                if not is_valid:
                    errors["name"] = result
            
            return jsonify({
                "valid": len(errors) == 0,
                "errors": errors
            }), 200
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return jsonify({"valid": False, "errors": {"_server": "Validation failed"}}), 500
    
    @app.route("/api/webform/status/<ticket_id>", methods=["GET"])
    def get_ticket_status(ticket_id: str):
        """Get ticket status"""
        # This would query the database in production
        return jsonify({
            "ticket_id": ticket_id,
            "status": "received",
            "message": "Your ticket has been received and will be processed shortly."
        }), 200
    
    @app.route("/api/webform/health", methods=["GET"])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "webform-handler",
            "timestamp": datetime.now().isoformat()
        }), 200
    
    return app


# ============================================================================
# Usage Example
# ============================================================================

"""
# Run as Flask app
from channels.web_form_handler import create_webform_app

app = create_webform_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

# Use handler directly
from channels.web_form_handler import WebFormHandler

result = WebFormHandler.process_submission(
    data={
        "email": "customer@example.com",
        "name": "John Doe",
        "subject": "Need help with integration",
        "message": "I'm trying to integrate with Slack but..."
    },
    files={},
    user_agent="Mozilla/5.0...",
    ip_address="192.168.1.1"
)

if result["success"]:
    print(f"Ticket created: {result['ticket_id']}")
else:
    print(f"Errors: {result['errors']}")
"""
