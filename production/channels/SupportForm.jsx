/**
 * TechNova Customer Support - Support Form Component
 * 
 * Complete support request form with:
 * - Real-time validation
 * - File upload with preview
 * - Success screen with ticket ID
 * - Error handling
 * - Responsive design
 * 
 * Usage:
 * import SupportForm from './SupportForm';
 * 
 * <SupportForm 
 *   onSubmit={(ticketId) => console.log('Ticket:', ticketId)}
 *   apiEndpoint="/api/webform/submit"
 * />
 */

import React, { useState, useCallback, useEffect } from 'react';
import './SupportForm.css';

// ============================================================================
// Types
// ============================================================================

/**
 * @typedef {Object} FormData
 * @property {string} name - Customer name
 * @property {string} email - Customer email
 * @property {string} company - Company name (optional)
 * @property {string} subject - Ticket subject
 * @property {string} message - Ticket message
 * @property {File[]} attachments - File attachments
 */

/**
 * @typedef {Object} FormErrors
 * @property {string} name - Name error message
 * @property {string} email - Email error message
 * @property {string} company - Company error message
 * @property {string} subject - Subject error message
 * @property {string} message - Message error message
 * @property {string} attachments - Attachments error message
 * @property {string} general - General error message
 */

// ============================================================================
// Constants
// ============================================================================

const VALIDATION_RULES = {
  EMAIL: {
    REQUIRED: 'Email is required',
    INVALID: 'Please enter a valid email address',
    PATTERN: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  },
  SUBJECT: {
    REQUIRED: 'Subject is required',
    MIN_LENGTH: 5,
    MAX_LENGTH: 200,
    TOO_SHORT: 'Subject must be at least 5 characters',
    TOO_LONG: 'Subject must be less than 200 characters'
  },
  MESSAGE: {
    REQUIRED: 'Message is required',
    MIN_LENGTH: 10,
    MAX_LENGTH: 5000,
    TOO_SHORT: 'Message must be at least 10 characters',
    TOO_LONG: 'Message must be less than 5000 characters'
  },
  NAME: {
    MAX_LENGTH: 100,
    TOO_LONG: 'Name must be less than 100 characters',
    INVALID_CHARS: 'Name contains invalid characters'
  },
  COMPANY: {
    MAX_LENGTH: 200,
    TOO_LONG: 'Company name must be less than 200 characters'
  },
  ATTACHMENTS: {
    MAX_FILES: 5,
    MAX_SIZE: 16 * 1024 * 1024, // 16MB
    MAX_SIZE_MESSAGE: 'File size must be less than 16MB',
    TOO_MANY_FILES: 'Maximum 5 files allowed',
    INVALID_TYPE: 'File type not allowed. Allowed: PDF, PNG, JPG, GIF, TXT, DOC, DOCX',
    ALLOWED_TYPES: ['application/pdf', 'image/png', 'image/jpeg', 'image/gif', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
  }
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Validate email address
 * @param {string} email
 * @returns {string|null} Error message or null if valid
 */
const validateEmail = (email) => {
  if (!email || email.trim() === '') {
    return VALIDATION_RULES.EMAIL.REQUIRED;
  }
  
  const trimmedEmail = email.trim();
  if (!VALIDATION_RULES.EMAIL.PATTERN.test(trimmedEmail)) {
    return VALIDATION_RULES.EMAIL.INVALID;
  }
  
  if (trimmedEmail.length > 254) {
    return VALIDATION_RULES.EMAIL.INVALID;
  }
  
  return null;
};

/**
 * Validate subject
 * @param {string} subject
 * @returns {string|null} Error message or null if valid
 */
const validateSubject = (subject) => {
  if (!subject || subject.trim() === '') {
    return VALIDATION_RULES.SUBJECT.REQUIRED;
  }
  
  const trimmedSubject = subject.trim();
  if (trimmedSubject.length < VALIDATION_RULES.SUBJECT.MIN_LENGTH) {
    return VALIDATION_RULES.SUBJECT.TOO_SHORT;
  }
  
  if (trimmedSubject.length > VALIDATION_RULES.SUBJECT.MAX_LENGTH) {
    return VALIDATION_RULES.SUBJECT.TOO_LONG;
  }
  
  return null;
};

/**
 * Validate message
 * @param {string} message
 * @returns {string|null} Error message or null if valid
 */
const validateMessage = (message) => {
  if (!message || message.trim() === '') {
    return VALIDATION_RULES.MESSAGE.REQUIRED;
  }
  
  const trimmedMessage = message.trim();
  if (trimmedMessage.length < VALIDATION_RULES.MESSAGE.MIN_LENGTH) {
    return VALIDATION_RULES.MESSAGE.TOO_SHORT;
  }
  
  if (trimmedMessage.length > VALIDATION_RULES.MESSAGE.MAX_LENGTH) {
    return VALIDATION_RULES.MESSAGE.TOO_LONG;
  }
  
  return null;
};

/**
 * Validate name
 * @param {string} name
 * @returns {string|null} Error message or null if valid
 */
const validateName = (name) => {
  if (!name || name.trim() === '') {
    return null; // Name is optional
  }
  
  const trimmedName = name.trim();
  if (trimmedName.length > VALIDATION_RULES.NAME.MAX_LENGTH) {
    return VALIDATION_RULES.NAME.TOO_LONG;
  }
  
  // Check for valid characters (letters, numbers, spaces, hyphens, periods, apostrophes)
  if (!/^[\w\s\-\.\']+$/.test(trimmedName)) {
    return VALIDATION_RULES.NAME.INVALID_CHARS;
  }
  
  return null;
};

/**
 * Validate company
 * @param {string} company
 * @returns {string|null} Error message or null if valid
 */
const validateCompany = (company) => {
  if (!company || company.trim() === '') {
    return null; // Company is optional
  }
  
  if (company.trim().length > VALIDATION_RULES.COMPANY.MAX_LENGTH) {
    return VALIDATION_RULES.COMPANY.TOO_LONG;
  }
  
  return null;
};

/**
 * Validate attachments
 * @param {File[]} attachments
 * @returns {string|null} Error message or null if valid
 */
const validateAttachments = (attachments) => {
  if (!attachments || attachments.length === 0) {
    return null; // Attachments are optional
  }
  
  if (attachments.length > VALIDATION_RULES.ATTACHMENTS.MAX_FILES) {
    return VALIDATION_RULES.ATTACHMENTS.TOO_MANY_FILES;
  }
  
  for (const file of attachments) {
    if (file.size > VALIDATION_RULES.ATTACHMENTS.MAX_SIZE) {
      return VALIDATION_RULES.ATTACHMENTS.MAX_SIZE_MESSAGE;
    }
    
    if (!VALIDATION_RULES.ATTACHMENTS.ALLOWED_TYPES.includes(file.type)) {
      return VALIDATION_RULES.ATTACHMENTS.INVALID_TYPE;
    }
  }
  
  return null;
};

// ============================================================================
// Components
// ============================================================================

/**
 * Success Screen Component
 * Displays after successful form submission
 */
const SuccessScreen = ({ ticketId, email, onNewTicket }) => {
  return (
    <div className="support-form-success">
      <div className="success-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
      </div>
      
      <h2 className="success-title">Request Submitted Successfully!</h2>
      
      <div className="success-details">
        <p className="success-message">
          Thank you for contacting TechNova Support. We've received your request and will respond shortly.
        </p>
        
        <div className="ticket-info">
          <div className="ticket-info-item">
            <span className="ticket-info-label">Ticket ID:</span>
            <span className="ticket-info-value">{ticketId}</span>
          </div>
          
          <div className="ticket-info-item">
            <span className="ticket-info-label">Confirmation sent to:</span>
            <span className="ticket-info-value">{email}</span>
          </div>
        </div>
        
        <div className="success-tips">
          <h3>What happens next?</h3>
          <ul>
            <li>You'll receive a confirmation email shortly</li>
            <li>Our support team will review your request</li>
            <li>Expect a response within 24 hours</li>
            <li>Reference your Ticket ID for follow-ups</li>
          </ul>
        </div>
      </div>
      
      <button 
        className="btn-new-ticket"
        onClick={onNewTicket}
      >
        Submit Another Request
      </button>
    </div>
  );
};

/**
 * File Upload Component
 * Handles file attachment with preview
 */
const FileUpload = ({ attachments, onAttachmentsChange, error }) => {
  const fileInputRef = React.useRef(null);
  
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    onAttachmentsChange([...attachments, ...files]);
  };
  
  const handleRemoveFile = (index) => {
    const newAttachments = attachments.filter((_, i) => i !== index);
    onAttachmentsChange(newAttachments);
  };
  
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };
  
  const getFileIcon = (type) => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('image')) return '🖼️';
    if (type.includes('word')) return '📝';
    if (type.includes('text')) return '📃';
    return '📎';
  };
  
  return (
    <div className="file-upload-container">
      <label className="file-upload-label">
        Attachments (Optional)
      </label>
      
      <div 
        className={`file-upload-area ${error ? 'error' : ''}`}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.gif,.txt,.doc,.docx"
          onChange={handleFileSelect}
          className="file-input-hidden"
        />
        
        <div className="file-upload-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <p>Click to upload or drag and drop</p>
          <span className="file-upload-hint">
            PDF, PNG, JPG, GIF, TXT, DOC, DOCX (Max 16MB each, 5 files)
          </span>
        </div>
      </div>
      
      {error && <div className="field-error">{error}</div>}
      
      {attachments.length > 0 && (
        <div className="file-list">
          {attachments.map((file, index) => (
            <div key={index} className="file-item">
              <span className="file-icon">{getFileIcon(file.type)}</span>
              <div className="file-info">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{formatFileSize(file.size)}</span>
              </div>
              <button
                type="button"
                className="file-remove-btn"
                onClick={() => handleRemoveFile(index)}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Main Support Form Component
 */
const SupportForm = ({ 
  onSubmit, 
  apiEndpoint = '/api/webform/submit',
  className = ''
}) => {
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    subject: '',
    message: ''
  });
  
  const [attachments, setAttachments] = useState([]);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [ticketId, setTicketId] = useState('');
  const [submittedEmail, setSubmittedEmail] = useState('');
  const [generalError, setGeneralError] = useState('');
  
  // Character counts
  const subjectCount = formData.subject.length;
  const messageCount = formData.message.length;
  
  // Handle field change
  const handleFieldChange = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  }, [errors]);
  
  // Handle field blur
  const handleFieldBlur = useCallback((field) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    
    // Validate field
    let error = null;
    switch (field) {
      case 'email':
        error = validateEmail(formData.email);
        break;
      case 'subject':
        error = validateSubject(formData.subject);
        break;
      case 'message':
        error = validateMessage(formData.message);
        break;
      case 'name':
        error = validateName(formData.name);
        break;
      case 'company':
        error = validateCompany(formData.company);
        break;
      default:
        break;
    }
    
    if (error) {
      setErrors(prev => ({ ...prev, [field]: error }));
    }
  }, [formData]);
  
  // Handle attachments change
  const handleAttachmentsChange = useCallback((newAttachments) => {
    setAttachments(newAttachments);
    const error = validateAttachments(newAttachments);
    setErrors(prev => ({ ...prev, attachments: error }));
  }, []);
  
  // Validate all fields
  const validateForm = useCallback(() => {
    const newErrors = {};
    
    const emailError = validateEmail(formData.email);
    if (emailError) newErrors.email = emailError;
    
    const subjectError = validateSubject(formData.subject);
    if (subjectError) newErrors.subject = subjectError;
    
    const messageError = validateMessage(formData.message);
    if (messageError) newErrors.message = messageError;
    
    const nameError = validateName(formData.name);
    if (nameError) newErrors.name = nameError;
    
    const companyError = validateCompany(formData.company);
    if (companyError) newErrors.company = companyError;
    
    const attachmentsError = validateAttachments(attachments);
    if (attachmentsError) newErrors.attachments = attachmentsError;
    
    setErrors(newErrors);
    setTouched({
      name: true,
      email: true,
      company: true,
      subject: true,
      message: true,
      attachments: true
    });
    
    return Object.keys(newErrors).length === 0;
  }, [formData, attachments]);
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setGeneralError('');
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Create FormData for file upload
      const submitData = new FormData();
      submitData.append('name', formData.name);
      submitData.append('email', formData.email);
      submitData.append('company', formData.company);
      submitData.append('subject', formData.subject);
      submitData.append('message', formData.message);
      
      // Add attachments
      attachments.forEach((file, index) => {
        submitData.append(`attachment${index}`, file);
      });
      
      // Submit to API
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        body: submitData
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'Failed to submit form');
      }
      
      // Success
      setSubmitSuccess(true);
      setTicketId(result.ticket_id);
      setSubmittedEmail(result.email);
      
      // Call parent callback
      if (onSubmit) {
        onSubmit(result.ticket_id);
      }
      
    } catch (error) {
      console.error('Form submission error:', error);
      setGeneralError(error.message || 'Failed to submit form. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handle new ticket (reset form)
  const handleNewTicket = useCallback(() => {
    setFormData({
      name: '',
      email: '',
      company: '',
      subject: '',
      message: ''
    });
    setAttachments([]);
    setErrors({});
    setTouched({});
    setSubmitSuccess(false);
    setTicketId('');
    setSubmittedEmail('');
    setGeneralError('');
  }, []);
  
  // Render success screen
  if (submitSuccess) {
    return (
      <SuccessScreen 
        ticketId={ticketId}
        email={submittedEmail}
        onNewTicket={handleNewTicket}
      />
    );
  }
  
  // Render form
  return (
    <div className={`support-form-container ${className}`}>
      <div className="support-form-header">
        <h1 className="support-form-title">Contact Support</h1>
        <p className="support-form-subtitle">
          Fill out the form below and we'll get back to you within 24 hours.
        </p>
      </div>
      
      {generalError && (
        <div className="form-error-banner">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{generalError}</span>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="support-form" noValidate>
        {/* Name Field */}
        <div className="form-group">
          <label htmlFor="name" className="form-label">
            Name <span className="optional-label">(Optional)</span>
          </label>
          <input
            type="text"
            id="name"
            className={`form-input ${touched.name && errors.name ? 'error' : ''}`}
            value={formData.name}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            onBlur={() => handleFieldBlur('name')}
            placeholder="John Doe"
            maxLength={100}
          />
          {touched.name && errors.name && (
            <div className="field-error">{errors.name}</div>
          )}
        </div>
        
        {/* Email Field */}
        <div className="form-group">
          <label htmlFor="email" className="form-label">
            Email <span className="required-label">*</span>
          </label>
          <input
            type="email"
            id="email"
            className={`form-input ${touched.email && errors.email ? 'error' : ''}`}
            value={formData.email}
            onChange={(e) => handleFieldChange('email', e.target.value)}
            onBlur={() => handleFieldBlur('email')}
            placeholder="john@example.com"
            required
          />
          {touched.email && errors.email && (
            <div className="field-error">{errors.email}</div>
          )}
        </div>
        
        {/* Company Field */}
        <div className="form-group">
          <label htmlFor="company" className="form-label">
            Company <span className="optional-label">(Optional)</span>
          </label>
          <input
            type="text"
            id="company"
            className={`form-input ${touched.company && errors.company ? 'error' : ''}`}
            value={formData.company}
            onChange={(e) => handleFieldChange('company', e.target.value)}
            onBlur={() => handleFieldBlur('company')}
            placeholder="Acme Corporation"
            maxLength={200}
          />
          {touched.company && errors.company && (
            <div className="field-error">{errors.company}</div>
          )}
        </div>
        
        {/* Subject Field */}
        <div className="form-group">
          <label htmlFor="subject" className="form-label">
            Subject <span className="required-label">*</span>
          </label>
          <input
            type="text"
            id="subject"
            className={`form-input ${touched.subject && errors.subject ? 'error' : ''}`}
            value={formData.subject}
            onChange={(e) => handleFieldChange('subject', e.target.value)}
            onBlur={() => handleFieldBlur('subject')}
            placeholder="Brief description of your issue"
            required
            maxLength={200}
          />
          <div className="char-counter">
            <span className={`char-count ${subjectCount > VALIDATION_RULES.SUBJECT.MAX_LENGTH ? 'error' : ''}`}>
              {subjectCount}/{VALIDATION_RULES.SUBJECT.MAX_LENGTH}
            </span>
          </div>
          {touched.subject && errors.subject && (
            <div className="field-error">{errors.subject}</div>
          )}
        </div>
        
        {/* Message Field */}
        <div className="form-group">
          <label htmlFor="message" className="form-label">
            Message <span className="required-label">*</span>
          </label>
          <textarea
            id="message"
            className={`form-textarea ${touched.message && errors.message ? 'error' : ''}`}
            value={formData.message}
            onChange={(e) => handleFieldChange('message', e.target.value)}
            onBlur={() => handleFieldBlur('message')}
            placeholder="Describe your issue in detail..."
            rows={6}
            required
            maxLength={VALIDATION_RULES.MESSAGE.MAX_LENGTH}
          />
          <div className="char-counter">
            <span className={`char-count ${messageCount > VALIDATION_RULES.MESSAGE.MAX_LENGTH ? 'error' : ''}`}>
              {messageCount}/{VALIDATION_RULES.MESSAGE.MAX_LENGTH}
            </span>
          </div>
          {touched.message && errors.message && (
            <div className="field-error">{errors.message}</div>
          )}
        </div>
        
        {/* File Upload */}
        <FileUpload 
          attachments={attachments}
          onAttachmentsChange={handleAttachmentsChange}
          error={touched.attachments && errors.attachments}
        />
        
        {/* Submit Button */}
        <button 
          type="submit" 
          className="btn-submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <span className="spinner"></span>
              Submitting...
            </>
          ) : (
            <>
              Submit Request
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default SupportForm;
