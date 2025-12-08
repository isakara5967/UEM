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
- Conversation memory (sohbet gecmisi)

Kullanim:
    from core.memory import get_memory_store, Episode, Interaction

    # Singleton store
    store = get_memory_store()

    # Episode kaydet
    episode = Episode(what="Met Alice", who=["alice"])
    store.store_episode(episode)

    # Iliski sorgula
    relationship = store.get_relationship("alice")

    # Conversation memory
    session_id = store.conversation.start_conversation(user_id="user1")
    store.conversation.add_turn(session_id, "user", "Hello!")
    context = store.conversation.get_context(session_id)
"""

# Types - veri yapilari
from .types import (
    # Enums
    MemoryType,
    EmotionalValence,
    RelationshipType,
    InteractionType,
    EpisodeType,
    EmbeddingModel,
    SourceType,

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

    # Conversation
    DialogueTurn,
    Conversation,

    # Consolidation
    ConsolidationTask,

    # Query
    MemoryQuery,
    RetrievalResult,

    # Embedding
    EmbeddingConfig,
    EmbeddingResult,
)

# Store - ana koordinator
from .store import (
    MemoryStore,
    MemoryConfig,
    get_memory_store,
    create_memory_store,
    reset_memory_store,
)

# Conversation memory
from .conversation import (
    ConversationMemory,
    ConversationConfig,
    get_conversation_memory,
    create_conversation_memory,
    reset_conversation_memory,
)

# Embeddings
from .embeddings import (
    EmbeddingEncoder,
    get_embedding_encoder,
    create_embedding_encoder,
    reset_embedding_encoder,
    cosine_similarity,
    batch_cosine_similarity,
    top_k_indices,
    euclidean_distance,
    normalize_vector,
)

# Semantic memory
from .semantic import (
    SemanticMemory,
    get_semantic_memory,
    create_semantic_memory,
    reset_semantic_memory,
)

__all__ = [
    # Enums
    "MemoryType",
    "EmotionalValence",
    "RelationshipType",
    "InteractionType",
    "EpisodeType",
    "EmbeddingModel",
    "SourceType",

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

    # Conversation
    "DialogueTurn",
    "Conversation",
    "ConversationMemory",
    "ConversationConfig",
    "get_conversation_memory",
    "create_conversation_memory",
    "reset_conversation_memory",

    # Consolidation
    "ConsolidationTask",

    # Query
    "MemoryQuery",
    "RetrievalResult",

    # Embeddings
    "EmbeddingConfig",
    "EmbeddingResult",
    "EmbeddingEncoder",
    "get_embedding_encoder",
    "create_embedding_encoder",
    "reset_embedding_encoder",
    "cosine_similarity",
    "batch_cosine_similarity",
    "top_k_indices",
    "euclidean_distance",
    "normalize_vector",

    # Semantic Memory
    "SemanticMemory",
    "get_semantic_memory",
    "create_semantic_memory",
    "reset_semantic_memory",

    # Store
    "MemoryStore",
    "MemoryConfig",
    "get_memory_store",
    "create_memory_store",
    "reset_memory_store",
]
