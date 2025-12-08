"""
core/language/__init__.py

UEM v2 Language Module - LLM entegrasyonu.

Context building ve response generation.

Kullanim:
    from core.language import ContextBuilder, ContextConfig
    from core.language import MockLLMAdapter, LLMResponse

    builder = ContextBuilder()
    context = builder.build(
        user_message="Merhaba!",
        conversation=conv,
        relevant_memories=memories,
    )

    adapter = MockLLMAdapter()
    response = adapter.generate(context)
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
]
