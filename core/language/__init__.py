"""
core/language/__init__.py

UEM v2 Language Module - LLM entegrasyonu.

Context building ve response generation.

Kullanim:
    from core.language import ContextBuilder, ContextConfig

    builder = ContextBuilder()
    context = builder.build(
        user_message="Merhaba!",
        conversation=conv,
        relevant_memories=memories,
    )
"""

from .context import (
    ContextBuilder,
    ContextConfig,
    ContextSection,
    get_context_builder,
    create_context_builder,
    reset_context_builder,
)

__all__ = [
    "ContextBuilder",
    "ContextConfig",
    "ContextSection",
    "get_context_builder",
    "create_context_builder",
    "reset_context_builder",
]
