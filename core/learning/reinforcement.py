"""
core/learning/reinforcement.py

Reinforcement Learning - Reward hesaplama ve pattern guclendrme.
UEM v2 - Feedback-based reinforcement learning.

Ozellikler:
- Reward calculation from feedback
- Time-based decay
- Pattern reinforcement
- Generalization to similar patterns
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .types import (
    Feedback,
    FeedbackType,
    LearningOutcome,
    Pattern,
)

if TYPE_CHECKING:
    from .patterns import PatternStorage


@dataclass
class RewardConfig:
    """Reward hesaplama konfigurasyonu."""
    positive_base: float = 1.0
    negative_base: float = -1.0
    neutral_base: float = 0.0
    decay_rate: float = 0.95      # Eski feedback'ler daha az etkili
    recency_weight: float = 0.3   # Son feedback'lere agirlik


class RewardCalculator:
    """
    Feedback'ten reward hesaplayan sinif.

    Feedback degerini reward'a donusturur ve zamana gore
    decay uygular.
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        """
        Initialize reward calculator.

        Args:
            config: Reward konfigurasyonu
        """
        self.config = config or RewardConfig()

    def calculate(self, feedback: Feedback) -> float:
        """
        Tek feedback'ten reward hesapla.

        Args:
            feedback: Geri bildirim

        Returns:
            Hesaplanan reward degeri
        """
        # Base reward from feedback value
        if feedback.value > 0.3:
            base = self.config.positive_base
        elif feedback.value < -0.3:
            base = self.config.negative_base
        else:
            base = self.config.neutral_base

        # Scale by actual feedback value
        reward = base * abs(feedback.value)

        # Apply recency weight if feedback is recent (within last hour)
        age_hours = self._get_age_hours(feedback.timestamp)
        if age_hours < 1.0:
            reward *= (1.0 + self.config.recency_weight)

        return reward

    def calculate_cumulative(self, feedbacks: List[Feedback]) -> float:
        """
        Birden fazla feedback'ten toplam reward hesapla.

        Args:
            feedbacks: Geri bildirim listesi

        Returns:
            Toplam reward (decay uygulanmis)
        """
        if not feedbacks:
            return 0.0

        # Sort by timestamp (oldest first)
        sorted_feedbacks = sorted(feedbacks, key=lambda f: f.timestamp)

        total_reward = 0.0
        for i, feedback in enumerate(sorted_feedbacks):
            reward = self.calculate(feedback)
            age_hours = self._get_age_hours(feedback.timestamp)
            decayed = self.apply_decay(reward, age_hours)
            total_reward += decayed

        return total_reward

    def apply_decay(self, reward: float, age_hours: float) -> float:
        """
        Zamana gore decay uygula.

        Args:
            reward: Orijinal reward
            age_hours: Feedback yasi (saat)

        Returns:
            Decay uygulanmis reward
        """
        if age_hours <= 0:
            return reward

        # Exponential decay based on age
        decay_factor = self.config.decay_rate ** (age_hours / 24.0)
        return reward * decay_factor

    def _get_age_hours(self, timestamp: datetime) -> float:
        """Calculate age in hours from timestamp."""
        now = datetime.now()
        delta = now - timestamp
        return delta.total_seconds() / 3600.0


class Reinforcer:
    """
    Pattern reinforcement sinifi.

    Feedback'e gore pattern'leri guclendirir veya zayiflatir.
    Benzer pattern'lere de etki edebilir (generalization).
    """

    def __init__(
        self,
        pattern_storage: "PatternStorage",
        reward_calculator: Optional[RewardCalculator] = None
    ):
        """
        Initialize reinforcer.

        Args:
            pattern_storage: Pattern depolama
            reward_calculator: Reward hesaplayici
        """
        self.patterns = pattern_storage
        self.calculator = reward_calculator or RewardCalculator()
        self._history: List[LearningOutcome] = []
        self._total_reward: float = 0.0

    def reinforce(self, pattern_id: str, feedback: Feedback) -> LearningOutcome:
        """
        Pattern'i feedback'e gore guclendir/zayiflat.

        Args:
            pattern_id: Pattern ID'si
            feedback: Geri bildirim

        Returns:
            Ogrenme sonucu
        """
        pattern = self.patterns.get(pattern_id)
        pattern_updated = False

        if pattern is not None:
            reward = self.calculator.calculate(feedback)
            success = feedback.value > 0

            self.patterns.update_stats(pattern_id, success, reward)
            self._total_reward += reward
            pattern_updated = True
        else:
            reward = 0.0

        outcome = LearningOutcome(
            pattern_id=pattern_id,
            feedback=feedback,
            reward=reward,
            pattern_updated=pattern_updated
        )

        self._history.append(outcome)
        return outcome

    def reinforce_similar(
        self,
        content: str,
        feedback: Feedback,
        spread: float = 0.5
    ) -> List[LearningOutcome]:
        """
        Benzer pattern'leri de guclendir (generalization).

        Args:
            content: Icerik
            feedback: Geri bildirim
            spread: Benzer pattern'lere uygulanacak etki orani (0-1)

        Returns:
            Ogrenme sonuclari listesi
        """
        outcomes = []

        # Find similar patterns
        similar = self.patterns.find_similar(content, k=5, min_similarity=0.5)

        for pattern, similarity in similar:
            # Scale reward by similarity and spread factor
            scaled_feedback = Feedback(
                id=feedback.id,
                interaction_id=feedback.interaction_id,
                feedback_type=feedback.feedback_type,
                value=feedback.value * similarity * spread,
                timestamp=feedback.timestamp,
                user_id=feedback.user_id,
                context=feedback.context,
                reason=feedback.reason
            )

            outcome = self.reinforce(pattern.id, scaled_feedback)
            outcomes.append(outcome)

        return outcomes

    def get_history(self, limit: int = 100) -> List[LearningOutcome]:
        """
        Reinforcement gecmisini getir.

        Args:
            limit: Maksimum kayit sayisi

        Returns:
            Son N ogrenme sonucu
        """
        return list(self._history[-limit:])

    def get_total_reward(self) -> float:
        """
        Toplam reward degerini getir.

        Returns:
            Toplam reward
        """
        return self._total_reward

    def stats(self) -> Dict[str, Any]:
        """
        Reinforcement istatistiklerini getir.

        Returns:
            Istatistik sozlugu
        """
        if not self._history:
            return {
                "total_reinforcements": 0,
                "total_reward": 0.0,
                "positive_reinforcements": 0,
                "negative_reinforcements": 0,
                "average_reward": 0.0,
                "patterns_updated": 0
            }

        positive = sum(1 for o in self._history if o.reward > 0)
        negative = sum(1 for o in self._history if o.reward < 0)
        patterns_updated = sum(1 for o in self._history if o.pattern_updated)
        avg_reward = self._total_reward / len(self._history)

        return {
            "total_reinforcements": len(self._history),
            "total_reward": self._total_reward,
            "positive_reinforcements": positive,
            "negative_reinforcements": negative,
            "average_reward": avg_reward,
            "patterns_updated": patterns_updated
        }

    def clear_history(self) -> int:
        """
        Gecmisi temizle.

        Returns:
            Silinen kayit sayisi
        """
        count = len(self._history)
        self._history.clear()
        self._total_reward = 0.0
        return count
