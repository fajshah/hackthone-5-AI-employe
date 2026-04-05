"""
TechNova Customer Success Agent

Complete agent implementation with:
- 5 tools (search, ticket, history, response, escalate)
- Channel-aware formatting
- Sentiment analysis
- Escalation rules
- PostgreSQL + pgvector integration
"""

__version__ = "1.0.0"

# Core agent
try:
    from .customer_success_agent import (
        CustomerSuccessAgent,
        CustomerMessage,
        AgentResponse,
        CustomerProfile,
        create_agent,
    )
except ImportError:
    pass

# Tools (requires openai-agents for full functionality)
try:
    from .tools import (
        # Tools
        search_knowledge_base,
        create_ticket,
        get_customer_history,
        send_response,
        escalate_to_human,
        ALL_TOOLS,
        
        # Input models
        SearchKnowledgeBaseInput,
        CreateTicketInput,
        GetCustomerHistoryInput,
        SendResponseInput,
        EscalateToHumanInput,
        
        # Output models
        SearchKnowledgeBaseOutput,
        CreateTicketOutput,
        CustomerHistoryOutput,
        SendResponseOutput,
        EscalateToHumanOutput,
        
        # Services
        SentimentAnalyzer,
        EscalationRules,
        ResponseGenerator,
        KnowledgeBaseService,
    )
except ImportError:
    # Fallback to standalone versions
    try:
        from .run_demo import (
            SentimentAnalyzer,
            EscalationRules,
            ResponseGenerator,
            Channel,
            Category,
        )
    except ImportError:
        pass

# Formatters
try:
    from .formatters import (
        ChannelFormatter,
        ResponseFormatter,
        TicketFormatter,
        ChannelConfig,
    )
except ImportError:
    pass

# Prompts
try:
    from .prompts import (
        SYSTEM_PROMPT,
        TOOL_PROMPTS,
        CHANNEL_PROMPTS,
        QUALITY_PROMPT,
    )
except ImportError:
    pass

__all__ = [
    # Core agent
    'CustomerSuccessAgent',
    'CustomerMessage',
    'AgentResponse',
    'CustomerProfile',
    'create_agent',
    
    # Tools
    'search_knowledge_base',
    'create_ticket',
    'get_customer_history',
    'send_response',
    'escalate_to_human',
    'ALL_TOOLS',
    
    # Input models
    'SearchKnowledgeBaseInput',
    'CreateTicketInput',
    'GetCustomerHistoryInput',
    'SendResponseInput',
    'EscalateToHumanInput',
    
    # Output models
    'SearchKnowledgeBaseOutput',
    'CreateTicketOutput',
    'CustomerHistoryOutput',
    'SendResponseOutput',
    'EscalateToHumanOutput',
    
    # Services
    'SentimentAnalyzer',
    'EscalationRules',
    'ResponseGenerator',
    'KnowledgeBaseService',
    
    # Formatters
    'ChannelFormatter',
    'ResponseFormatter',
    'TicketFormatter',
    'ChannelConfig',
    
    # Prompts
    'SYSTEM_PROMPT',
    'TOOL_PROMPTS',
    'CHANNEL_PROMPTS',
    'QUALITY_PROMPT',
]
