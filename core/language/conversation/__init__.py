"""
core/language/conversation

Conversation Context management - Multi-turn conversation tracking.

UEM v2 - Context Integration.
"""

from .types import (
    Message,
    ConversationContext,
    ContextConfig,
)
from .manager import ContextManager

__all__ = [
    "Message",
    "ConversationContext",
    "ContextConfig",
    "ContextManager",
]
