"""
core/learning/adaptation.py

Behavior Adaptation - Davranis adaptasyonu.
UEM v2 - Feedback'e gore davranis degistirme.

Ozellikler:
- Pattern suggestion based on context
- Exploration vs exploitation
- Confidence-based decisions
- Adaptive behavior tracking
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .types import (
    Feedback,
    FeedbackType,
    Pattern,
    PatternType,
)

if TYPE_CHECKING:
    from .patterns import PatternStorage
    from .feedback import FeedbackCollector


@dataclass
class AdaptationConfig:
    """Adaptasyon konfigurasyonu."""
    min_samples: int = 3          # Adaptasyon icin minimum ornek
    confidence_threshold: float = 0.6
    exploration_rate: float = 0.1  # Yeni pattern deneme orani


@dataclass
class AdaptationRecord:
    """Adaptasyon kaydi."""
    timestamp: datetime
    pattern_id: str
    action: str  # "explore", "exploit", "adapt"
    context: Optional[str] = None
    result: Optional[str] = None


class BehaviorAdapter:
    """
    Davranis adaptasyonu sinifi.

    Context'e gore en iyi pattern'i onerir ve feedback'e
    gore davranisi adapte eder.
    """

    def __init__(
        self,
        pattern_storage: "PatternStorage",
        feedback_collector: "FeedbackCollector",
        config: Optional[AdaptationConfig] = None
    ):
        """
        Initialize behavior adapter.

        Args:
            pattern_storage: Pattern depolama
            feedback_collector: Feedback toplayici
            config: Adaptasyon konfigurasyonu
        """
        self.patterns = pattern_storage
        self.feedback = feedback_collector
        self.config = config or AdaptationConfig()
        self._adaptations: List[AdaptationRecord] = []
        self._exploration_count: int = 0
        self._exploitation_count: int = 0

    def suggest_pattern(
        self,
        context: str,
        pattern_type: PatternType
    ) -> Optional[Pattern]:
        """
        Context'e gore en iyi pattern'i oner.

        1. Benzer context'leri bul
        2. Basari oranina gore sirala
        3. Exploration vs exploitation dengesi

        Args:
            context: Baglam
            pattern_type: Pattern turu

        Returns:
            Onerilen pattern veya None
        """
        # Check if we should explore
        if self.should_explore():
            pattern = self._explore_pattern(pattern_type)
            if pattern:
                self._record_adaptation(pattern.id, "explore", context)
                self._exploration_count += 1
                return pattern

        # Exploit: find best matching pattern
        pattern = self._exploit_pattern(context, pattern_type)
        if pattern:
            self._record_adaptation(pattern.id, "exploit", context)
            self._exploitation_count += 1
            return pattern

        return None

    def _explore_pattern(self, pattern_type: PatternType) -> Optional[Pattern]:
        """
        Rastgele pattern sec (exploration).

        Args:
            pattern_type: Pattern turu

        Returns:
            Rastgele pattern veya None
        """
        patterns = self.patterns.get_all(pattern_type)
        if not patterns:
            return None

        # Prefer less-used patterns for exploration
        unused = [p for p in patterns if p.total_uses < self.config.min_samples]
        if unused:
            return random.choice(unused)

        return random.choice(patterns)

    def _exploit_pattern(
        self,
        context: str,
        pattern_type: PatternType
    ) -> Optional[Pattern]:
        """
        En iyi pattern'i sec (exploitation).

        Args:
            context: Baglam
            pattern_type: Pattern turu

        Returns:
            En iyi pattern veya None
        """
        # Find similar patterns
        similar = self.patterns.find_similar(context, k=10, min_similarity=0.3)

        if not similar:
            # Fallback to best patterns of this type
            best = self.patterns.get_best_patterns(pattern_type, k=1)
            return best[0] if best else None

        # Filter by pattern type and confidence
        candidates = []
        for pattern, similarity in similar:
            if pattern.pattern_type == pattern_type:
                confidence = self.get_confidence(pattern)
                if confidence >= self.config.confidence_threshold or pattern.total_uses < self.config.min_samples:
                    score = similarity * confidence
                    candidates.append((pattern, score))

        if not candidates:
            # Return most similar regardless of confidence
            for pattern, similarity in similar:
                if pattern.pattern_type == pattern_type:
                    return pattern
            return None

        # Sort by score and return best
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def should_explore(self) -> bool:
        """
        Yeni pattern mi deneyelim, bilinen mi kullanalim?

        Returns:
            True ise explore, False ise exploit
        """
        return random.random() < self.config.exploration_rate

    def adapt_from_feedback(
        self,
        interaction_id: str,
        pattern_id: str
    ) -> bool:
        """
        Feedback'e gore davranisi adapte et.

        Args:
            interaction_id: Etkilesim ID'si
            pattern_id: Pattern ID'si

        Returns:
            Adaptasyon yapildi mi?
        """
        # Get feedback for this interaction
        feedbacks = self.feedback.get_feedback(interaction_id)
        if not feedbacks:
            return False

        # Get pattern
        pattern = self.patterns.get(pattern_id)
        if pattern is None:
            return False

        # Calculate average feedback value
        avg_value = sum(f.value for f in feedbacks) / len(feedbacks)

        # Record adaptation
        result = "positive" if avg_value > 0 else "negative" if avg_value < 0 else "neutral"
        self._record_adaptation(pattern_id, "adapt", result=result)

        return True

    def get_confidence(self, pattern: Pattern) -> float:
        """
        Pattern'in guvenilirlik skoru.

        Args:
            pattern: Pattern

        Returns:
            Guvenilirlik skoru (0-1)
        """
        # Not enough samples = low confidence
        if pattern.total_uses < self.config.min_samples:
            return 0.5

        # Confidence based on success rate and sample size
        success_rate = pattern.success_rate

        # More samples = more confidence in the success rate
        sample_factor = min(pattern.total_uses / 20.0, 1.0)

        # Weighted combination
        confidence = (success_rate * 0.7) + (sample_factor * 0.3)

        return min(max(confidence, 0.0), 1.0)

    def get_adaptations(self) -> List[Dict[str, Any]]:
        """
        Yapilan adaptasyonlari listele.

        Returns:
            Adaptasyon kayitlari
        """
        return [
            {
                "timestamp": a.timestamp.isoformat(),
                "pattern_id": a.pattern_id,
                "action": a.action,
                "context": a.context,
                "result": a.result
            }
            for a in self._adaptations
        ]

    def _record_adaptation(
        self,
        pattern_id: str,
        action: str,
        context: Optional[str] = None,
        result: Optional[str] = None
    ) -> None:
        """Record an adaptation event."""
        record = AdaptationRecord(
            timestamp=datetime.now(),
            pattern_id=pattern_id,
            action=action,
            context=context,
            result=result
        )
        self._adaptations.append(record)

    def stats(self) -> Dict[str, Any]:
        """
        Adaptasyon istatistiklerini getir.

        Returns:
            Istatistik sozlugu
        """
        total = self._exploration_count + self._exploitation_count

        return {
            "total_adaptations": len(self._adaptations),
            "exploration_count": self._exploration_count,
            "exploitation_count": self._exploitation_count,
            "exploration_rate_actual": (
                self._exploration_count / total if total > 0 else 0.0
            ),
            "exploration_rate_config": self.config.exploration_rate,
            "confidence_threshold": self.config.confidence_threshold,
            "min_samples": self.config.min_samples
        }

    def clear(self) -> int:
        """
        Adaptasyon gecmisini temizle.

        Returns:
            Silinen kayit sayisi
        """
        count = len(self._adaptations)
        self._adaptations.clear()
        self._exploration_count = 0
        self._exploitation_count = 0
        return count
