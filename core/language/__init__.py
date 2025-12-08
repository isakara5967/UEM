"""
core/language/__init__.py

UEM v2 Language Module - LLM entegrasyonu.

Context building, LLM adapters ve chat agent.

Kullanim:
    from core.language import UEMChatAgent, ChatConfig

    agent = UEMChatAgent()
    session_id = agent.start_session("user_123")
    response = agent.chat("Merhaba!")
    print(response.content)
    agent.end_session()
"""

from .context import (
    ContextBuilder,
    ContextConfig,
    ContextSection,
    get_context_builder,
    create_context_builder,
    reset_context_builder,
)

from .llm_adapter import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    LLMAdapter,
    MockLLMAdapter,
    AnthropicAdapter,
    OpenAIAdapter,
    create_adapter,
    get_llm_adapter,
    reset_llm_adapter,
)

from .chat_agent import (
    ChatConfig,
    ChatResponse,
    UEMChatAgent,
    get_chat_agent,
    create_chat_agent,
    reset_chat_agent,
)

__all__ = [
    # Context
    "ContextBuilder",
    "ContextConfig",
    "ContextSection",
    "get_context_builder",
    "create_context_builder",
    "reset_context_builder",

    # LLM
    "LLMProvider",
    "LLMConfig",
    "LLMResponse",
    "LLMAdapter",
    "MockLLMAdapter",
    "AnthropicAdapter",
    "OpenAIAdapter",
    "create_adapter",
    "get_llm_adapter",
    "reset_llm_adapter",

    # Chat Agent
    "ChatConfig",
    "ChatResponse",
    "UEMChatAgent",
    "get_chat_agent",
    "create_chat_agent",
    "reset_chat_agent",
]
