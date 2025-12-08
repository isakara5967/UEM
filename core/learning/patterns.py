"""
core/learning/patterns.py

Pattern Storage - Davranis patternleri depolama ve arama.
UEM v2 - Embedding tabanli benzer pattern bulma.

Ozellikler:
- Pattern depolama ve indeksleme
- Embedding-based similarity search
- Success/failure tracking
- Pattern pruning
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np

from .types import (
    Pattern,
    PatternType,
    generate_pattern_id,
)

# Conditional import for EmbeddingEncoder
if TYPE_CHECKING:
    from core.memory.embeddings import EmbeddingEncoder


class PatternStorage:
    """
    Davranis patternleri depolama ve yonetim sinifi.

    Patternleri embedding'ler ile indeksler ve benzerlik
    aramasi yapilmasini saglar.
    """

    def __init__(self, encoder: Optional["EmbeddingEncoder"] = None):
        """
        Initialize pattern storage.

        Args:
            encoder: Embedding encoder (opsiyonel)
        """
        self.encoder = encoder
        self._patterns: Dict[str, Pattern] = {}
        self._embeddings: Dict[str, np.ndarray] = {}

    def store(
        self,
        content: str,
        pattern_type: PatternType,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Pattern:
        """
        Yeni pattern kaydet.

        Args:
            content: Pattern icerigi
            pattern_type: Pattern turu
            extra_data: Ek veri (opsiyonel)

        Returns:
            Olusturulan Pattern nesnesi
        """
        pattern_id = generate_pattern_id()

        # Generate embedding if encoder available
        embedding = None
        embedding_array = None
        if self.encoder is not None:
            try:
                embedding_array = self.encoder.encode(content)
                embedding = embedding_array.tolist()
            except Exception:
                pass

        pattern = Pattern(
            id=pattern_id,
            pattern_type=pattern_type,
            content=content,
            embedding=embedding,
            extra_data=extra_data or {}
        )

        self._patterns[pattern_id] = pattern

        # Store embedding for similarity search
        if embedding_array is not None:
            self._embeddings[pattern_id] = embedding_array

        return pattern

    def get(self, pattern_id: str) -> Optional[Pattern]:
        """
        Pattern ID ile getir.

        Args:
            pattern_id: Pattern ID'si

        Returns:
            Pattern nesnesi veya None
        """
        return self._patterns.get(pattern_id)

    def find_similar(
        self,
        content: str,
        k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Tuple[Pattern, float]]:
        """
        Benzer patternleri bul.

        Args:
            content: Aranacak icerik
            k: Maksimum sonuc sayisi
            min_similarity: Minimum benzerlik esigi

        Returns:
            (Pattern, similarity) tuple listesi
        """
        if self.encoder is None or len(self._embeddings) == 0:
            return []

        try:
            query_embedding = self.encoder.encode(content)
        except Exception:
            return []

        # Calculate similarities
        similarities = []
        for pattern_id, embedding in self._embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            if similarity >= min_similarity:
                pattern = self._patterns[pattern_id]
                similarities.append((pattern, float(similarity)))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:k]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def update_stats(
        self,
        pattern_id: str,
        success: bool,
        reward: float
    ) -> None:
        """
        Pattern istatistiklerini guncelle.

        Args:
            pattern_id: Pattern ID'si
            success: Basarili mi?
            reward: Odul degeri
        """
        pattern = self._patterns.get(pattern_id)
        if pattern is None:
            return

        if success:
            pattern.success_count += 1
        else:
            pattern.failure_count += 1

        pattern.total_reward += reward
        pattern.last_used = datetime.now()

    def get_best_patterns(
        self,
        pattern_type: PatternType,
        k: int = 10
    ) -> List[Pattern]:
        """
        En basarili patternleri getir.

        Args:
            pattern_type: Pattern turu
            k: Maksimum sonuc sayisi

        Returns:
            Basari oranina gore sirali pattern listesi
        """
        patterns = [
            p for p in self._patterns.values()
            if p.pattern_type == pattern_type
        ]

        # Sort by success rate then by total reward
        patterns.sort(
            key=lambda p: (p.success_rate, p.average_reward),
            reverse=True
        )

        return patterns[:k]

    def get_worst_patterns(
        self,
        pattern_type: PatternType,
        k: int = 10
    ) -> List[Pattern]:
        """
        En basarisiz patternleri getir.

        Args:
            pattern_type: Pattern turu
            k: Maksimum sonuc sayisi

        Returns:
            Basari oranina gore sirali pattern listesi (dusukten yuksege)
        """
        patterns = [
            p for p in self._patterns.values()
            if p.pattern_type == pattern_type and p.total_uses > 0
        ]

        # Sort by success rate ascending
        patterns.sort(
            key=lambda p: (p.success_rate, p.average_reward)
        )

        return patterns[:k]

    def prune_weak_patterns(
        self,
        min_uses: int = 5,
        max_failure_rate: float = 0.7
    ) -> int:
        """
        Zayif patternleri temizle.

        Args:
            min_uses: Minimum kullanim sayisi (bu kadar kullanilmis olmali)
            max_failure_rate: Maksimum basarisizlik orani

        Returns:
            Silinen pattern sayisi
        """
        to_remove = []

        for pattern_id, pattern in self._patterns.items():
            if pattern.total_uses >= min_uses:
                failure_rate = 1.0 - pattern.success_rate
                if failure_rate >= max_failure_rate:
                    to_remove.append(pattern_id)

        for pattern_id in to_remove:
            del self._patterns[pattern_id]
            if pattern_id in self._embeddings:
                del self._embeddings[pattern_id]

        return len(to_remove)

    def count(self) -> int:
        """Toplam pattern sayisi."""
        return len(self._patterns)

    def stats(self) -> Dict[str, Any]:
        """
        Pattern istatistiklerini getir.

        Returns:
            Istatistik sozlugu
        """
        if not self._patterns:
            return {
                "total_patterns": 0,
                "by_type": {},
                "with_embeddings": 0,
                "total_uses": 0,
                "average_success_rate": 0.0
            }

        by_type = {}
        for ptype in PatternType:
            count = sum(1 for p in self._patterns.values() if p.pattern_type == ptype)
            if count > 0:
                by_type[ptype.value] = count

        total_uses = sum(p.total_uses for p in self._patterns.values())
        used_patterns = [p for p in self._patterns.values() if p.total_uses > 0]

        if used_patterns:
            avg_success = sum(p.success_rate for p in used_patterns) / len(used_patterns)
        else:
            avg_success = 0.0

        return {
            "total_patterns": len(self._patterns),
            "by_type": by_type,
            "with_embeddings": len(self._embeddings),
            "total_uses": total_uses,
            "average_success_rate": avg_success
        }

    def clear(self) -> int:
        """
        Tum patternleri temizle.

        Returns:
            Silinen pattern sayisi
        """
        count = len(self._patterns)
        self._patterns.clear()
        self._embeddings.clear()
        return count

    def get_all(self, pattern_type: Optional[PatternType] = None) -> List[Pattern]:
        """
        Tum patternleri getir.

        Args:
            pattern_type: Filtrelenecek pattern turu (opsiyonel)

        Returns:
            Pattern listesi
        """
        if pattern_type is None:
            return list(self._patterns.values())

        return [
            p for p in self._patterns.values()
            if p.pattern_type == pattern_type
        ]
