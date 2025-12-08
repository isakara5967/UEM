"""
core/memory/persistence/__init__.py

PostgreSQL persistence layer for Memory module.

Usage:
    from core.memory.persistence import (
        get_engine,
        get_session,
        EpisodeModel,
        RelationshipModel,
        MemoryRepository,
        ConversationRepository,
    )

    # Create session
    session = get_session()

    # Use repository
    repo = MemoryRepository(session)
    repo.save_episode(episode)

    # Conversation repository
    conv_repo = ConversationRepository(session)
    conv_repo.create_conversation(user_id="user1")
"""

from .models import (
    Base,
    EpisodeModel,
    RelationshipModel,
    InteractionModel,
    SemanticFactModel,
    EmotionalMemoryModel,
    TrustHistoryModel,
    ConversationModel,
    DialogueTurnModel,
)

from .repository import (
    MemoryRepository,
    get_engine,
    get_session,
    init_db,
)

from .conversation_repo import ConversationRepository

__all__ = [
    # Models
    "Base",
    "EpisodeModel",
    "RelationshipModel",
    "InteractionModel",
    "SemanticFactModel",
    "EmotionalMemoryModel",
    "TrustHistoryModel",
    "ConversationModel",
    "DialogueTurnModel",

    # Repository
    "MemoryRepository",
    "ConversationRepository",
    "get_engine",
    "get_session",
    "init_db",
]
