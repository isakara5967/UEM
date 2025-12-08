"""
core/memory/embeddings.py

Embedding Encoder - Semantic search icin metin vektorlestirme.
UEM v2 - Multilingual destek ile sentence-transformers entegrasyonu.

Ozellikler:
- Lazy model loading (ilk kullanima kadar yuklenmez)
- Embedding cache (ayni metin tekrar encode edilmez)
- Batch encoding (toplu islem)
- Multilingual destek (Turkce, Ingilizce, vs.)
- Cosine similarity utilities
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from collections import OrderedDict
import hashlib
import logging

import numpy as np

from .types import EmbeddingConfig, EmbeddingModel

# Lazy import for sentence-transformers
if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU cache for embeddings."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _hash_key(self, text: str) -> str:
        """Generate hash key for text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from cache."""
        key = self._hash_key(text)
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def put(self, text: str, embedding: np.ndarray) -> None:
        """Put embedding in cache."""
        key = self._hash_key(text)

        if key in self._cache:
            self._cache.move_to_end(key)
            return

        if len(self._cache) >= self.max_size:
            # Remove oldest (first item)
            self._cache.popitem(last=False)

        self._cache[key] = embedding

    def clear(self) -> int:
        """Clear cache and return count of cleared items."""
        count = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        return count

    @property
    def stats(self) -> Dict[str, Any]:
        """Cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }


class EmbeddingEncoder:
    """
    Embedding Encoder - Metin vektorlestirme.

    Lazy loading ile model sadece ilk kullanımda yuklenir.
    Cache ile ayni metin tekrar encode edilmez.

    Kullanim:
        encoder = EmbeddingEncoder()

        # Tek metin
        embedding = encoder.encode("Merhaba dunya!")

        # Toplu encoding
        embeddings = encoder.encode_batch(["text1", "text2", "text3"])

        # Benzerlik
        sim = cosine_similarity(embedding1, embedding2)
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self._model: Optional['SentenceTransformer'] = None
        self._model_loaded = False

        # Cache
        if self.config.cache_enabled:
            self._cache = LRUCache(max_size=self.config.cache_max_size)
        else:
            self._cache = None

        # Stats
        self._encode_count = 0
        self._batch_count = 0

        logger.info(
            f"EmbeddingEncoder initialized "
            f"(model={self.config.model_name}, lazy={self.config.lazy_load})"
        )

        # Eager loading if not lazy
        if not self.config.lazy_load:
            self._load_model()

    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        if self._model_loaded:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.config.model_name}")
            self._model = SentenceTransformer(self.config.model_name)
            self._model_loaded = True
            logger.info("Embedding model loaded successfully")

        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    @property
    def model(self) -> 'SentenceTransformer':
        """Get the model (lazy loading)."""
        if not self._model_loaded:
            self._load_model()
        return self._model

    def encode(self, text: str) -> np.ndarray:
        """
        Encode single text to embedding vector.

        Args:
            text: Input text

        Returns:
            Embedding vector as numpy array
        """
        # Check cache
        if self._cache is not None:
            cached = self._cache.get(text)
            if cached is not None:
                return cached

        # Encode
        embedding = self.model.encode(
            text,
            normalize_embeddings=self.config.normalize_embeddings,
            convert_to_numpy=True,
        )

        self._encode_count += 1

        # Cache result
        if self._cache is not None:
            self._cache.put(text, embedding)

        return embedding

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Encode multiple texts to embedding vectors.

        Args:
            texts: List of input texts

        Returns:
            2D numpy array of embeddings (N x dimension)
        """
        if not texts:
            return np.array([])

        # Check cache for each text
        results = []
        texts_to_encode = []
        indices_to_encode = []

        for i, text in enumerate(texts):
            if self._cache is not None:
                cached = self._cache.get(text)
                if cached is not None:
                    results.append((i, cached))
                    continue

            texts_to_encode.append(text)
            indices_to_encode.append(i)

        # Encode uncached texts
        if texts_to_encode:
            embeddings = self.model.encode(
                texts_to_encode,
                batch_size=self.config.batch_size,
                normalize_embeddings=self.config.normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            self._batch_count += 1
            self._encode_count += len(texts_to_encode)

            # Cache and collect results
            for idx, (orig_idx, text) in enumerate(zip(indices_to_encode, texts_to_encode)):
                emb = embeddings[idx]
                if self._cache is not None:
                    self._cache.put(text, emb)
                results.append((orig_idx, emb))

        # Sort by original index and return
        results.sort(key=lambda x: x[0])
        return np.array([emb for _, emb in results])

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.config.dimension

    def clear_cache(self) -> int:
        """Clear embedding cache."""
        if self._cache is not None:
            return self._cache.clear()
        return 0

    @property
    def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self._cache is not None:
            return self._cache.stats
        return {"enabled": False}

    @property
    def stats(self) -> Dict[str, Any]:
        """Get encoder statistics."""
        return {
            "model_name": self.config.model_name,
            "dimension": self.config.dimension,
            "model_loaded": self._model_loaded,
            "encode_count": self._encode_count,
            "batch_count": self._batch_count,
            "cache": self.cache_stats,
        }

    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model_loaded


# ========================================================================
# SIMILARITY UTILITIES
# ========================================================================

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Cosine similarity (-1 to 1, usually 0 to 1 for normalized vectors)
    """
    # Handle 1D arrays
    a = a.flatten()
    b = b.flatten()

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def batch_cosine_similarity(
    query: np.ndarray,
    vectors: np.ndarray,
) -> np.ndarray:
    """
    Compute cosine similarity between query and multiple vectors.

    Args:
        query: Query vector (1D)
        vectors: Matrix of vectors (2D, N x dimension)

    Returns:
        Array of similarities (N,)
    """
    if vectors.size == 0:
        return np.array([])

    query = query.flatten()
    query_norm = np.linalg.norm(query)

    if query_norm == 0:
        return np.zeros(len(vectors))

    # Normalize query
    query_normalized = query / query_norm

    # Normalize vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
    vectors_normalized = vectors / norms

    # Dot product
    similarities = np.dot(vectors_normalized, query_normalized)

    return similarities


def top_k_indices(
    similarities: np.ndarray,
    k: int,
    min_threshold: float = 0.0,
) -> List[Tuple[int, float]]:
    """
    Get top-k indices with highest similarity scores.

    Args:
        similarities: Array of similarity scores
        k: Number of top results
        min_threshold: Minimum similarity threshold

    Returns:
        List of (index, score) tuples, sorted by score descending
    """
    if similarities.size == 0:
        return []

    # Apply threshold
    valid_mask = similarities >= min_threshold
    valid_indices = np.where(valid_mask)[0]
    valid_scores = similarities[valid_mask]

    if len(valid_indices) == 0:
        return []

    # Sort by score descending
    sorted_order = np.argsort(valid_scores)[::-1]

    # Take top k
    top_k = min(k, len(sorted_order))

    results = []
    for i in range(top_k):
        idx = valid_indices[sorted_order[i]]
        score = float(valid_scores[sorted_order[i]])
        results.append((int(idx), score))

    return results


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute Euclidean distance between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Euclidean distance (>= 0)
    """
    a = a.flatten()
    b = b.flatten()
    return float(np.linalg.norm(a - b))


def normalize_vector(v: np.ndarray) -> np.ndarray:
    """
    L2 normalize a vector.

    Args:
        v: Input vector

    Returns:
        Normalized vector
    """
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


# ========================================================================
# FACTORY & SINGLETON
# ========================================================================

_embedding_encoder: Optional[EmbeddingEncoder] = None


def get_embedding_encoder(
    config: Optional[EmbeddingConfig] = None,
) -> EmbeddingEncoder:
    """Get embedding encoder singleton."""
    global _embedding_encoder

    if _embedding_encoder is None:
        _embedding_encoder = EmbeddingEncoder(config)

    return _embedding_encoder


def reset_embedding_encoder() -> None:
    """Reset embedding encoder singleton (test icin)."""
    global _embedding_encoder
    _embedding_encoder = None


def create_embedding_encoder(
    config: Optional[EmbeddingConfig] = None,
) -> EmbeddingEncoder:
    """Create new embedding encoder (test icin)."""
    return EmbeddingEncoder(config)
