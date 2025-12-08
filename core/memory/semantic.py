"""
core/memory/semantic.py

Semantic Memory - Embedding bazli semantik arama.
UEM v2 - Vector store ile benzerlik araması.

Ozellikler:
- In-memory vector index
- Embedding encoder entegrasyonu
- Episode, DialogueTurn, Conversation indexleme
- Persistence (save/load)
- Source type filtreleme
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime
import json
import logging

import numpy as np

from .types import (
    SourceType,
    EmbeddingResult,
    Episode,
    DialogueTurn,
    Conversation,
)
from .embeddings import (
    EmbeddingEncoder,
    get_embedding_encoder,
    batch_cosine_similarity,
    top_k_indices,
)

logger = logging.getLogger(__name__)


@dataclass
class IndexEntry:
    """Internal index entry."""
    id: str
    content: str
    source_type: SourceType
    source_id: Optional[str]
    timestamp: Optional[datetime]
    extra_data: Dict[str, Any]
    embedding: np.ndarray


class SemanticMemory:
    """
    Semantic Memory - Embedding bazli arama.

    In-memory vector store ile hizli benzerlik aramasi.
    Episode, DialogueTurn ve Conversation indexleme destegi.

    Kullanim:
        semantic = SemanticMemory()

        # Ekleme
        semantic.add("id1", "Merhaba dunya", SourceType.FACT)

        # Arama
        results = semantic.search("selam", k=5)

        # Episode indexleme
        semantic.index_episode(episode)

        # Kaydet/Yukle
        semantic.save("semantic_index.json")
        semantic.load("semantic_index.json")
    """

    def __init__(self, encoder: Optional[EmbeddingEncoder] = None):
        """
        Initialize SemanticMemory.

        Args:
            encoder: EmbeddingEncoder instance (uses singleton if not provided)
        """
        self._encoder = encoder
        self._index: Dict[str, IndexEntry] = {}

        # Stats
        self._stats = {
            "total_adds": 0,
            "total_searches": 0,
            "total_removes": 0,
        }

        logger.info("SemanticMemory initialized")

    @property
    def encoder(self) -> EmbeddingEncoder:
        """Get encoder (lazy initialization)."""
        if self._encoder is None:
            self._encoder = get_embedding_encoder()
        return self._encoder

    # ===================================================================
    # INDEX MANAGEMENT
    # ===================================================================

    def add(
        self,
        id: str,
        content: str,
        source_type: SourceType,
        source_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add content to semantic index.

        Args:
            id: Unique identifier
            content: Text content to index
            source_type: Source type (episode, dialogue, fact, concept)
            source_id: Optional source reference ID
            extra_data: Optional metadata
        """
        if not content or not content.strip():
            logger.warning(f"Skipping empty content for id: {id}")
            return

        embedding = self.encoder.encode(content)

        entry = IndexEntry(
            id=id,
            content=content,
            source_type=source_type,
            source_id=source_id,
            timestamp=datetime.now(),
            extra_data=extra_data or {},
            embedding=embedding,
        )

        self._index[id] = entry
        self._stats["total_adds"] += 1

        logger.debug(f"Added to index: {id} (source={source_type.value})")

    def add_batch(self, items: List[Dict[str, Any]]) -> int:
        """
        Add multiple items to index.

        Args:
            items: List of dicts with keys: id, content, source_type,
                   and optional: source_id, extra_data

        Returns:
            Number of items added
        """
        if not items:
            return 0

        # Extract texts for batch encoding
        valid_items = []
        texts = []

        for item in items:
            content = item.get("content", "")
            if content and content.strip():
                valid_items.append(item)
                texts.append(content)

        if not texts:
            return 0

        # Batch encode
        embeddings = self.encoder.encode_batch(texts)

        # Add to index
        for i, item in enumerate(valid_items):
            source_type = item.get("source_type")
            if isinstance(source_type, str):
                source_type = SourceType(source_type)

            entry = IndexEntry(
                id=item["id"],
                content=texts[i],
                source_type=source_type,
                source_id=item.get("source_id"),
                timestamp=datetime.now(),
                extra_data=item.get("extra_data", {}),
                embedding=embeddings[i],
            )

            self._index[entry.id] = entry

        self._stats["total_adds"] += len(valid_items)
        logger.debug(f"Batch added {len(valid_items)} items to index")

        return len(valid_items)

    def remove(self, id: str) -> bool:
        """
        Remove item from index.

        Args:
            id: Item ID to remove

        Returns:
            True if removed, False if not found
        """
        if id in self._index:
            del self._index[id]
            self._stats["total_removes"] += 1
            logger.debug(f"Removed from index: {id}")
            return True
        return False

    def clear(self) -> None:
        """Clear all items from index."""
        count = len(self._index)
        self._index.clear()
        logger.info(f"Cleared {count} items from index")

    def count(self) -> int:
        """Get number of items in index."""
        return len(self._index)

    def contains(self, id: str) -> bool:
        """Check if ID exists in index."""
        return id in self._index

    # ===================================================================
    # SEARCH
    # ===================================================================

    def search(
        self,
        query: str,
        k: int = 5,
        min_similarity: float = 0.3,
    ) -> List[EmbeddingResult]:
        """
        Search for similar items.

        Args:
            query: Search query text
            k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of EmbeddingResult sorted by similarity descending
        """
        if not self._index:
            return []

        if not query or not query.strip():
            return []

        # Encode query
        query_embedding = self.encoder.encode(query)

        # Get all embeddings
        entries = list(self._index.values())
        embeddings = np.array([e.embedding for e in entries])

        # Compute similarities
        similarities = batch_cosine_similarity(query_embedding, embeddings)

        # Get top-k
        top_results = top_k_indices(similarities, k, min_similarity)

        # Build results
        results = []
        for idx, score in top_results:
            entry = entries[idx]
            results.append(EmbeddingResult(
                id=entry.id,
                content=entry.content,
                similarity=score,
                source_type=entry.source_type,
                source_id=entry.source_id,
                timestamp=entry.timestamp,
                extra_data=entry.extra_data,
            ))

        self._stats["total_searches"] += 1
        return results

    def search_by_source(
        self,
        query: str,
        source_type: SourceType,
        k: int = 5,
        min_similarity: float = 0.3,
    ) -> List[EmbeddingResult]:
        """
        Search within specific source type.

        Args:
            query: Search query text
            source_type: Filter by source type
            k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of EmbeddingResult sorted by similarity descending
        """
        if not self._index:
            return []

        if not query or not query.strip():
            return []

        # Filter entries by source type
        entries = [e for e in self._index.values() if e.source_type == source_type]

        if not entries:
            return []

        # Encode query
        query_embedding = self.encoder.encode(query)

        # Get embeddings for filtered entries
        embeddings = np.array([e.embedding for e in entries])

        # Compute similarities
        similarities = batch_cosine_similarity(query_embedding, embeddings)

        # Get top-k
        top_results = top_k_indices(similarities, k, min_similarity)

        # Build results
        results = []
        for idx, score in top_results:
            entry = entries[idx]
            results.append(EmbeddingResult(
                id=entry.id,
                content=entry.content,
                similarity=score,
                source_type=entry.source_type,
                source_id=entry.source_id,
                timestamp=entry.timestamp,
                extra_data=entry.extra_data,
            ))

        self._stats["total_searches"] += 1
        return results

    def search_similar_to_id(
        self,
        id: str,
        k: int = 5,
        min_similarity: float = 0.3,
    ) -> List[EmbeddingResult]:
        """
        Find items similar to existing item.

        Args:
            id: ID of reference item
            k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of EmbeddingResult (excluding the reference item)
        """
        if id not in self._index:
            return []

        reference = self._index[id]

        # Get all other entries
        entries = [e for e in self._index.values() if e.id != id]

        if not entries:
            return []

        # Get embeddings
        embeddings = np.array([e.embedding for e in entries])

        # Compute similarities
        similarities = batch_cosine_similarity(reference.embedding, embeddings)

        # Get top-k
        top_results = top_k_indices(similarities, k, min_similarity)

        # Build results
        results = []
        for idx, score in top_results:
            entry = entries[idx]
            results.append(EmbeddingResult(
                id=entry.id,
                content=entry.content,
                similarity=score,
                source_type=entry.source_type,
                source_id=entry.source_id,
                timestamp=entry.timestamp,
                extra_data=entry.extra_data,
            ))

        self._stats["total_searches"] += 1
        return results

    # ===================================================================
    # MEMORY INTEGRATION
    # ===================================================================

    def index_episode(self, episode: Episode) -> None:
        """
        Index an Episode for semantic search.

        Args:
            episode: Episode to index
        """
        # Build content from episode fields
        content_parts = []

        if episode.what:
            content_parts.append(episode.what)
        if episode.where:
            content_parts.append(f"Location: {episode.where}")
        if episode.outcome:
            content_parts.append(f"Outcome: {episode.outcome}")
        if episode.why:
            content_parts.append(f"Reason: {episode.why}")

        content = " ".join(content_parts)

        if not content.strip():
            logger.warning(f"Empty episode content, skipping: {episode.id}")
            return

        extra_data = {
            "episode_type": episode.episode_type.value,
            "who": episode.who,
            "outcome_valence": episode.outcome_valence,
            "importance": episode.importance,
        }

        self.add(
            id=episode.id,
            content=content,
            source_type=SourceType.EPISODE,
            source_id=episode.id,
            extra_data=extra_data,
        )

    def index_dialogue_turn(
        self,
        turn: DialogueTurn,
        conversation_id: str,
    ) -> None:
        """
        Index a DialogueTurn for semantic search.

        Args:
            turn: DialogueTurn to index
            conversation_id: Parent conversation ID
        """
        if not turn.content or not turn.content.strip():
            return

        extra_data = {
            "role": turn.role,
            "conversation_id": conversation_id,
            "emotional_valence": turn.emotional_valence,
            "intent": turn.intent,
            "topics": turn.topics,
        }

        self.add(
            id=turn.id,
            content=turn.content,
            source_type=SourceType.DIALOGUE,
            source_id=conversation_id,
            extra_data=extra_data,
        )

    def index_conversation(self, conversation: Conversation) -> int:
        """
        Index all turns in a Conversation.

        Args:
            conversation: Conversation to index

        Returns:
            Number of turns indexed
        """
        count = 0
        for turn in conversation.turns:
            if turn.content and turn.content.strip():
                self.index_dialogue_turn(turn, conversation.session_id)
                count += 1

        logger.debug(f"Indexed {count} turns from conversation {conversation.session_id}")
        return count

    # ===================================================================
    # PERSISTENCE
    # ===================================================================

    def save(self, path: str) -> None:
        """
        Save index to file.

        Args:
            path: File path to save to
        """
        data = {
            "version": "1.0",
            "count": len(self._index),
            "entries": [],
        }

        for entry in self._index.values():
            data["entries"].append({
                "id": entry.id,
                "content": entry.content,
                "source_type": entry.source_type.value,
                "source_id": entry.source_id,
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "extra_data": entry.extra_data,
                "embedding": entry.embedding.tolist(),
            })

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(self._index)} entries to {path}")

    def load(self, path: str) -> None:
        """
        Load index from file.

        Args:
            path: File path to load from
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._index.clear()

        for item in data.get("entries", []):
            timestamp = None
            if item.get("timestamp"):
                timestamp = datetime.fromisoformat(item["timestamp"])

            entry = IndexEntry(
                id=item["id"],
                content=item["content"],
                source_type=SourceType(item["source_type"]),
                source_id=item.get("source_id"),
                timestamp=timestamp,
                extra_data=item.get("extra_data", {}),
                embedding=np.array(item["embedding"]),
            )

            self._index[entry.id] = entry

        logger.info(f"Loaded {len(self._index)} entries from {path}")

    # ===================================================================
    # STATS
    # ===================================================================

    @property
    def stats(self) -> Dict[str, Any]:
        """Get semantic memory statistics."""
        source_counts = {}
        for entry in self._index.values():
            key = entry.source_type.value
            source_counts[key] = source_counts.get(key, 0) + 1

        return {
            "index_size": len(self._index),
            "source_counts": source_counts,
            **self._stats,
        }


# ========================================================================
# FACTORY & SINGLETON
# ========================================================================

_semantic_memory: Optional[SemanticMemory] = None


def get_semantic_memory(
    encoder: Optional[EmbeddingEncoder] = None,
) -> SemanticMemory:
    """Get semantic memory singleton."""
    global _semantic_memory

    if _semantic_memory is None:
        _semantic_memory = SemanticMemory(encoder)

    return _semantic_memory


def reset_semantic_memory() -> None:
    """Reset semantic memory singleton (test icin)."""
    global _semantic_memory
    _semantic_memory = None


def create_semantic_memory(
    encoder: Optional[EmbeddingEncoder] = None,
) -> SemanticMemory:
    """Create new semantic memory (test icin)."""
    return SemanticMemory(encoder)
