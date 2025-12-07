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
    )

    # Create session
    session = get_session()

    # Use repository
    repo = MemoryRepository(session)
    repo.save_episode(episode)
"""

from .models import (
    Base,
    EpisodeModel,
    RelationshipModel,
    InteractionModel,
    SemanticFactModel,
    EmotionalMemoryModel,
    TrustHistoryModel,
)

from .repository import (
    MemoryRepository,
    get_engine,
    get_session,
    init_db,
)

__all__ = [
    # Models
    "Base",
    "EpisodeModel",
    "RelationshipModel",
    "InteractionModel",
    "SemanticFactModel",
    "EmotionalMemoryModel",
    "TrustHistoryModel",

    # Repository
    "MemoryRepository",
    "get_engine",
    "get_session",
    "init_db",
]
