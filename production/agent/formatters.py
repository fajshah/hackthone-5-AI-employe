"""
TechNova Customer Support Agent - Formatters

Channel-aware formatting utilities:
- ChannelFormatter: Channel-specific rules and constraints
- ResponseFormatter: Response text formatting
- TicketFormatter: Ticket display formatting
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


# ============================================================================
# Channel Configuration
# ============================================================================

@dataclass
class ChannelConfig:
    """Channel-specific configuration"""
    name: str
    max_length: int
    min_length: int
    max_sentences: int
    tone: str
    greeting_required: bool
    signoff_required: bool
    emoji_allowed: bool
    formatting_style: str


# ============================================================================
# Channel Formatter
# ============================================================================

class ChannelFormatter:
    """
    Format responses based on channel constraints
    
    Channel specifications from discovery doc:
    - Email: 150-300 words, formal, structured paragraphs
    - WhatsApp: 20-60 words MAX, 1-3 sentences, casual with emoji
    - Web Form: 80-150 words, semi-formal, concise
    """
    
    CHANNEL_CONFIGS = {
        'email': ChannelConfig(
            name='Email',
            max_length=300,  # words
            min_length=150,
            max_sentences=10,
            tone='professional',
            greeting_required=True,
            signoff_required=True,
            emoji_allowed=False,
            formatting_style='structured'
        ),
        'whatsapp': ChannelConfig(
            name='WhatsApp',
            max_length=60,  # words (HARD LIMIT)
            min_length=10,
            max_sentences=3,  # HARD LIMIT
            tone='casual',
            greeting_required=False,
            signoff_required=False,
            emoji_allowed=True,
            formatting_style='concise'
        ),
        'web_form': ChannelConfig(
            name='Web Form',
            max_length=150,
            min_length=80,
            max_sentences=6,
            tone='semi-formal',
            greeting_required=True,
            signoff_required=True,
            emoji_allowed=False,
            formatting_style='concise'
        )
    }
    
    def get_channel_config(self, channel: str) -> ChannelConfig:
        """Get configuration for channel"""
        return self.CHANNEL_CONFIGS.get(channel, self.CHANNEL_CONFIGS['email'])
    
    def validate_response(self, response: str, channel: str) -> Dict:
        """
        Validate response meets channel constraints
        
        Returns:
            Dict with is_valid, issues, suggestions
        """
        config = self.get_channel_config(channel)
        issues = []
        suggestions = []
        
        # Count words
        words = response.split()
        word_count = len(words)
        
        # Count sentences
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        # Check word count
        if word_count > config.max_length:
            issues.append(f"Too long: {word_count} words (max {config.max_length})")
            suggestions.append(f"Reduce by {word_count - config.max_length} words")
        
        if word_count < config.min_length and channel != 'whatsapp':
            suggestions.append(f"Consider adding more detail (currently {word_count} words)")
        
        # Check sentence count (especially for WhatsApp)
        if sentence_count > config.max_sentences:
            issues.append(f"Too many sentences: {sentence_count} (max {config.max_sentences})")
            suggestions.append("Combine or remove sentences")
        
        # Check emoji usage
        has_emoji = any(char in response for char in '😀😃😄😁😆😅😂🤣😊😇🙂🙃😉😌😍🥰😘😗😙😚😋😛😝😜🤪🤨🧐🤓😎🤩🥳😏😒😞😔😟😕🙁☹️😣😖😫😩🥺😢😭😤😠😡🤬🤯😳🥵🥶😱😨😰😥😓🤗🤔🤭🤫🤥😶😐😑😬🙄😯😦😧😮😲🥱😴🤤😪😵🤐🥴🤢🤮🤧😷🤒🤕🤑🤠😈👿👹👺🤡💩👻💀☠️👽👾🤖')
        
        if has_emoji and not config.emoji_allowed:
            issues.append("Emoji not allowed for this channel")
            suggestions.append("Remove emoji")
        
        return {
            'is_valid': len(issues) == 0,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'issues': issues,
            'suggestions': suggestions,
            'config': config
        }
    
    def truncate_for_channel(self, text: str, channel: str) -> str:
        """Truncate text to fit channel constraints"""
        config = self.get_channel_config(channel)
        
        # For WhatsApp, be extra strict
        if channel == 'whatsapp':
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()][:config.max_sentences]
            text = ' '.join(sentences)
        
        # Truncate words
        words = text.split()[:config.max_length]
        return ' '.join(words)


# ============================================================================
# Response Formatter
# ============================================================================

class ResponseFormatter:
    """
    Format responses with templates and channel awareness
    
    Templates from discovery doc §2.4
    """
    
    # Response templates by category and channel
    TEMPLATES = {
        'how_to': {
            'email': """Hi {name},

Thanks for reaching out! I'd be happy to help you with {topic}.

Here's how to do it:

{steps}

{additional_context}

If you need any further assistance, feel free to reach out.

Best regards,
TechNova Support Team""",
            
            'whatsapp': """Hey! 👋 {action_text}

Need more help?""",
            
            'web_form': """Hi {name},

Thanks for your question about {topic}.

{steps}

Let us know if you need further assistance.

Best,
TechNova Support"""
        },
        
        'technical_issue': {
            'email': """Hi {name},

Thank you for reporting this issue. I understand how frustrating this must be.

Let me help you troubleshoot this:

{steps}

{troubleshooting_tips}

If the issue persists, please let me know and I'll escalate this.

Best regards,
TechNova Support Team""",
            
            'whatsapp': """Hi! Sorry you're facing this issue 😕

{action_text}

Let me know if it works!""",
            
            'web_form': """Hi {name},

Thanks for reporting this technical issue.

Please try: {steps}

If problem continues, reply with browser version and screenshot.

Best,
TechNova Support"""
        },
        
        'billing': {
            'email': """Hi {name},

I completely understand your frustration with this billing issue, and I sincerely apologize for the inconvenience.

I've reviewed your account and here's what I'm doing:

**Immediate Action:**
- {action_items}

**Timeline:**
- {timeline}

**Reference:** {reference}

I'll personally monitor this to ensure it's resolved promptly.

Best regards,
TechNova Support Team""",
            
            'whatsapp': """Hi! I understand this is concerning 😟

{action_text}

I'm on this!""",
            
            'web_form': """Hi {name},

Thanks for contacting us about this billing matter.

{action_items}

Timeline: {timeline}

Best,
TechNova Support"""
        },
        
        'default': {
            'email': """Hi {name},

Thank you for contacting TechNova Support.

I've received your message about: {topic}

I'm looking into this and will get back to you shortly.

Best regards,
TechNova Support Team""",
            
            'whatsapp': """Hi! 👋 Got your message. Checking this for you now - one sec!""",
            
            'web_form': """Hi {name},

Thanks for contacting TechNova Support.

We've received your request about: {topic}

Our team will respond within 4 hours.

Best,
TechNova Support"""
        }
    }
    
    def format_response(
        self,
        channel: str,
        category: str,
        message: str,
        customer_name: Optional[str] = None,
        kb_results: Optional[List[Dict]] = None,
        tone: str = 'professional',
        channel_config: Optional[ChannelConfig] = None
    ) -> str:
        """
        Format response using templates
        
        Args:
            channel: Communication channel
            category: Message category
            message: Original customer message
            customer_name: Customer name
            kb_results: Knowledge base results
            tone: Response tone
            channel_config: Channel configuration
            
        Returns:
            Formatted response text
        """
        if channel_config is None:
            channel_config = ChannelFormatter().get_channel_config(channel)
        
        # Get template
        template_dict = self.TEMPLATES.get(category, self.TEMPLATES['default'])
        template = template_dict.get(channel, template_dict.get('email', ''))
        
        if not template:
            template = self.TEMPLATES['default']['email']
        
        # Prepare variables
        name = customer_name.split()[0] if customer_name else "there"
        topic = self._extract_topic(message)
        
        # Get steps from KB
        if kb_results and len(kb_results) > 0:
            steps = self._format_steps(kb_results, channel)
            action_text = self._generate_action_text(category, channel, kb_results)
            additional_context = self._generate_additional_context(kb_results, channel)
            troubleshooting_tips = self._generate_troubleshooting_tips(kb_results, channel)
            action_items = "Reviewing your account"
            timeline = "24-48 hours"
            reference = ""
        else:
            steps = self._get_generic_steps(category, channel)
            action_text = self._get_generic_action_text(category, channel)
            additional_context = ""
            troubleshooting_tips = ""
            action_items = "Looking into this"
            timeline = "24 hours"
            reference = ""
        
        # Fill template
        response = template.format(
            name=name,
            topic=topic,
            steps=steps,
            action_text=action_text,
            additional_context=additional_context,
            troubleshooting_tips=troubleshooting_tips,
            action_items=action_items,
            timeline=timeline,
            reference=reference
        )
        
        # Validate and adjust for channel
        validation = ChannelFormatter().validate_response(response, channel)
        
        if not validation['is_valid']:
            # Truncate if needed
            response = ChannelFormatter().truncate_for_channel(response, channel)
        
        return response
    
    def _extract_topic(self, message: str) -> str:
        """Extract main topic from message"""
        cleaned = message.strip()
        
        # Remove common starters
        starters = ['how do i', 'how to', 'how can i', 'what is', 'where do i', 'i need', 'i want']
        for starter in starters:
            if cleaned.lower().startswith(starter):
                cleaned = cleaned[len(starter):].strip()
                break
        
        # Remove punctuation
        cleaned = cleaned.rstrip('?.!')
        
        # Truncate if too long
        if len(cleaned) > 60:
            cleaned = cleaned[:57] + "..."
        
        return cleaned if cleaned else "your request"
    
    def _format_steps(self, kb_results: List[Dict], channel: str) -> str:
        """Format KB results into steps"""
        if not kb_results:
            return self._get_generic_steps('how_to', channel)
        
        doc = kb_results[0]
        content = doc.get('content', '')
        
        # Extract numbered steps
        numbered = re.findall(r'\d+\.\s*([^\n]+)', content)
        if numbered:
            if channel == 'whatsapp':
                # WhatsApp: max 2 steps
                steps = numbered[:2]
                return '\n'.join([f"{i+1}. {s[:60]}" for i, s in enumerate(steps)])
            else:
                steps = numbered[:5]
                return '\n'.join([f"{i+1}. {s}" for i, s in enumerate(steps)])
        
        # Extract bullet points
        bullets = re.findall(r'[-•*]\s*([^\n]+)', content)
        if bullets:
            if channel == 'whatsapp':
                steps = bullets[:2]
                return '\n'.join([f"• {s[:60]}" for s in steps])
            else:
                return '\n'.join([f"• {s}" for s in bullets[:5]])
        
        # Fallback
        return self._get_generic_steps('how_to', channel)
    
    def _get_generic_steps(self, category: str, channel: str) -> str:
        """Get generic steps for category"""
        if channel == 'whatsapp':
            return "1. Log in to your dashboard\n2. Check Settings\n3. Follow the prompts"
        else:
            return """1. Log in to your TechNova account
2. Navigate to the relevant section
3. Follow the on-screen instructions
4. Contact us if you need further assistance"""
    
    def _generate_action_text(self, category: str, channel: str, kb_results: List[Dict]) -> str:
        """Generate concise action text for WhatsApp"""
        if channel != 'whatsapp':
            return ""
        
        if kb_results:
            doc = kb_results[0]
            content = doc.get('content', '')
            
            # Extract first step
            numbered = re.findall(r'\d+\.\s*([^\n]+)', content)
            if numbered:
                return f"Try: {numbered[0][:60]}"
            
            bullets = re.findall(r'[-•*]\s*([^\n]+)', content)
            if bullets:
                return f"• {bullets[0][:60]}"
        
        return self._get_generic_action_text(category, channel)
    
    def _get_generic_action_text(self, category: str, channel: str) -> str:
        """Get generic action text"""
        if channel == 'whatsapp':
            generics = {
                'how_to': "1. Open your project\n2. Click the + button\n3. Follow prompts",
                'technical_issue': "1. Refresh (Ctrl+Shift+R)\n2. Clear cache\n3. Try incognito",
                'billing': "Checking your account now... one sec!",
            }
            return generics.get(category, "Let me help you with that!")
        return ""
    
    def _generate_additional_context(self, kb_results: List[Dict], channel: str) -> str:
        """Generate additional context from KB"""
        if not kb_results or channel == 'whatsapp':
            return ""
        
        doc = kb_results[0]
        content = doc.get('content', '')
        
        # Extract tips or notes section
        tips_match = re.search(r'(?:Tips|Note|Important|Remember)[:\s]+([^\n]+(?:\n[^\n]+)*)', content, re.IGNORECASE)
        if tips_match:
            return f"\n**Pro Tip:** {tips_match.group(1).strip()}"
        
        return ""
    
    def _generate_troubleshooting_tips(self, kb_results: List[Dict], channel: str) -> str:
        """Generate troubleshooting tips"""
        if not kb_results or channel == 'whatsapp':
            return ""
        
        return """
**Additional troubleshooting:**
- Clear your browser cache
- Try incognito/private mode
- Test in a different browser
- Check for browser updates"""


# ============================================================================
# Ticket Formatter
# ============================================================================

class TicketFormatter:
    """Format ticket information for display"""
    
    @staticmethod
    def format_ticket_summary(ticket: Dict) -> str:
        """Format ticket as readable summary"""
        return f"""
Ticket: {ticket.get('ticket_id', 'N/A')}
Subject: {ticket.get('subject', 'N/A')}
Status: {ticket.get('status', 'N/A')}
Priority: {ticket.get('priority', 'P3')}
Created: {ticket.get('created_at', 'N/A')}
""".strip()
    
    @staticmethod
    def format_escalation_summary(escalation: Dict) -> str:
        """Format escalation for handoff"""
        return f"""
ESCALATION SUMMARY
==================
Ticket: {escalation.get('ticket_id', 'N/A')}
Reason: {escalation.get('reason', 'N/A')}
Priority: {escalation.get('priority', 'P2')}
Routed To: {escalation.get('routed_to', 'N/A')}
SLA: {escalation.get('sla_response_time', 'N/A')}

Handoff Notes:
{escalation.get('handoff_summary', 'N/A')}
""".strip()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    'ChannelFormatter',
    'ResponseFormatter',
    'TicketFormatter',
    'ChannelConfig',
]
