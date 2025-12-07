"""
core/memory/__init__.py

UEM v2 Memory Module - Facade

Tek giris noktasi - tum memory islemleri buradan.
Norobilim bazli bellek sistemi:
- Sensory buffer (cok kisa sureli)
- Working memory (7+-2 limit)
- Episodic memory (olaylar)
- Semantic memory (bilgi, kavramlar)
- Emotional memory (duygu etiketli anilar)
- Relationship memory (iliski gecmisi)

Kullanim:
    from core.memory import get_memory_store, Episode, Interaction

    # Singleton store
    store = get_memory_store()

    # Episode kaydet
    episode = Episode(what="Met Alice", who=["alice"])
    store.store_episode(episode)

    # Iliski sorgula
    relationship = store.get_relationship("alice")
"""

# Types - veri yapilari
from .types import (
    # Enums
    MemoryType,
    EmotionalValence,
    RelationshipType,
    InteractionType,
    EpisodeType,

    # Base
    MemoryItem,

    # Sensory
    SensoryTrace,

    # Working
    WorkingMemoryItem,

    # Episodic
    Episode,
    EpisodeSummary,

    # Semantic
    SemanticFact,
    ConceptNode,

    # Emotional
    EmotionalMemory,

    # Relationship
    Interaction,
    RelationshipRecord,

    # Consolidation
    ConsolidationTask,

    # Query
    MemoryQuery,
    RetrievalResult,
)

# Store - ana koordinator
from .store import (
    MemoryStore,
    MemoryConfig,
    get_memory_store,
    create_memory_store,
    reset_memory_store,
)

__all__ = [
    # Enums
    "MemoryType",
    "EmotionalValence",
    "RelationshipType",
    "InteractionType",
    "EpisodeType",

    # Base
    "MemoryItem",

    # Sensory
    "SensoryTrace",

    # Working
    "WorkingMemoryItem",

    # Episodic
    "Episode",
    "EpisodeSummary",

    # Semantic
    "SemanticFact",
    "ConceptNode",

    # Emotional
    "EmotionalMemory",

    # Relationship
    "Interaction",
    "RelationshipRecord",

    # Consolidation
    "ConsolidationTask",

    # Query
    "MemoryQuery",
    "RetrievalResult",

    # Store
    "MemoryStore",
    "MemoryConfig",
    "get_memory_store",
    "create_memory_store",
    "reset_memory_store",
]
