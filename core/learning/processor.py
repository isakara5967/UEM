"""
core/learning/processor.py

Learning Processor - Ana ogrenme koordinatoru.
UEM v2 - Tum ogrenme bilesenlerni bir araya getirir.

Ozellikler:
- Etkilesimden ogrenme
- Response onerisi
- Ogrenme hizi takibi
- Ilerleme olcumu
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .types import (
    Feedback,
    FeedbackType,
    LearningOutcome,
    Pattern,
    PatternType,
    generate_feedback_id,
)
from .feedback import FeedbackCollector
from .patterns import PatternStorage
from .reinforcement import Reinforcer, RewardCalculator
from .adaptation import BehaviorAdapter

# Conditional imports
if TYPE_CHECKING:
    from core.memory.store import MemoryStore
    from core.memory.embeddings import EmbeddingEncoder


class LearningProcessor:
    """
    Ana ogrenme koordinatoru.

    Tum ogrenme bilesenlerni bir araya getirir ve
    etkilesimlerden ogrenmeyi yonetir.
    """

    def __init__(
        self,
        memory: Optional["MemoryStore"] = None,
        encoder: Optional["EmbeddingEncoder"] = None
    ):
        """
        Initialize learning processor.

        Args:
            memory: Memory store (opsiyonel)
            encoder: Embedding encoder (opsiyonel)
        """
        self.memory = memory
        self.encoder = encoder

        # Try to create encoder if not provided
        if self.encoder is None:
            try:
                from core.memory.embeddings import EmbeddingEncoder
                self.encoder = EmbeddingEncoder()
            except ImportError:
                pass

        # Initialize components
        self.feedback_collector = FeedbackCollector()
        self.pattern_storage = PatternStorage(encoder=self.encoder)
        self.reinforcer = Reinforcer(
            pattern_storage=self.pattern_storage,
            reward_calculator=RewardCalculator()
        )
        self.adapter = BehaviorAdapter(
            pattern_storage=self.pattern_storage,
            feedback_collector=self.feedback_collector
        )

        # Tracking
        self._interactions: List[Dict[str, Any]] = []
        self._success_history: List[bool] = []

    def learn_from_interaction(
        self,
        interaction_id: str,
        context: str,
        response: str,
        feedback_type: FeedbackType,
        value: Optional[float] = None
    ) -> LearningOutcome:
        """
        Tek etkilesimden ogren.

        1. Response'u pattern olarak kaydet
        2. Feedback'i kaydet
        3. Reinforce et
        4. Adaptasyon guncelle

        Args:
            interaction_id: Etkilesim ID'si
            context: Baglam
            response: Cevap
            feedback_type: Geri bildirim turu
            value: Geri bildirim degeri (opsiyonel)

        Returns:
            Ogrenme sonucu
        """
        # Determine value if not provided
        if value is None:
            if feedback_type == FeedbackType.POSITIVE:
                value = 1.0
            elif feedback_type == FeedbackType.NEGATIVE:
                value = -1.0
            else:
                value = 0.0

        # 1. Store response as pattern
        pattern = self.pattern_storage.store(
            content=response,
            pattern_type=PatternType.RESPONSE,
            extra_data={"context": context, "interaction_id": interaction_id}
        )

        # 2. Record feedback
        feedback = self.feedback_collector.record(
            interaction_id=interaction_id,
            feedback_type=feedback_type,
            value=value,
            context=context
        )

        # 3. Reinforce pattern
        outcome = self.reinforcer.reinforce(pattern.id, feedback)

        # 4. Update adaptation
        self.adapter.adapt_from_feedback(interaction_id, pattern.id)

        # Track interaction
        self._interactions.append({
            "interaction_id": interaction_id,
            "pattern_id": pattern.id,
            "feedback_value": value,
            "timestamp": datetime.now()
        })

        # Track success
        self._success_history.append(value > 0)

        return outcome

    def suggest_response(self, context: str) -> Optional[str]:
        """
        Context'e gore ogrenilmis cevap oner.

        Args:
            context: Baglam

        Returns:
            Onerilen cevap veya None
        """
        pattern = self.adapter.suggest_pattern(context, PatternType.RESPONSE)
        if pattern:
            return pattern.content
        return None

    def get_learning_rate(self) -> float:
        """
        Ogrenme hizi (son N etkilesimdeki basari orani).

        Returns:
            Ogrenme hizi (0-1)
        """
        if not self._success_history:
            return 0.0

        # Use last 50 interactions
        recent = self._success_history[-50:]
        return sum(recent) / len(recent)

    def get_improvement(self, window: int = 100) -> float:
        """
        Son N etkilesimdeki basari orani degisimi.

        Args:
            window: Pencere boyutu

        Returns:
            Ilerleme orani (pozitif = iyilesme)
        """
        if len(self._success_history) < window:
            return 0.0

        # Split into two halves
        mid = len(self._success_history) - window // 2
        first_half = self._success_history[mid - window // 2:mid]
        second_half = self._success_history[mid:]

        if not first_half or not second_half:
            return 0.0

        first_rate = sum(first_half) / len(first_half)
        second_rate = sum(second_half) / len(second_half)

        return second_rate - first_rate

    def get_pattern_for_context(
        self,
        context: str,
        pattern_type: PatternType = PatternType.RESPONSE
    ) -> Optional[Pattern]:
        """
        Context'e gore pattern getir.

        Args:
            context: Baglam
            pattern_type: Pattern turu

        Returns:
            Bulunan pattern veya None
        """
        return self.adapter.suggest_pattern(context, pattern_type)

    def reinforce_from_feedback(
        self,
        pattern_id: str,
        feedback: Feedback
    ) -> LearningOutcome:
        """
        Feedback'e gore pattern'i guclendir.

        Args:
            pattern_id: Pattern ID'si
            feedback: Geri bildirim

        Returns:
            Ogrenme sonucu
        """
        return self.reinforcer.reinforce(pattern_id, feedback)

    def stats(self) -> Dict[str, Any]:
        """
        Tum ogrenme istatistiklerini getir.

        Returns:
            Istatistik sozlugu
        """
        return {
            "feedback": self.feedback_collector.get_stats(),
            "patterns": self.pattern_storage.stats(),
            "reinforcement": self.reinforcer.stats(),
            "adaptation": self.adapter.stats(),
            "learning_rate": self.get_learning_rate(),
            "improvement": self.get_improvement(),
            "total_interactions": len(self._interactions)
        }

    def clear(self) -> Dict[str, int]:
        """
        Tum ogrenme verilerini temizle.

        Returns:
            Temizlenen kayit sayilari
        """
        return {
            "feedback": self.feedback_collector.clear(),
            "patterns": self.pattern_storage.clear(),
            "reinforcement": self.reinforcer.clear_history(),
            "adaptation": self.adapter.clear(),
            "interactions": self._clear_interactions()
        }

    def _clear_interactions(self) -> int:
        """Clear interaction history."""
        count = len(self._interactions)
        self._interactions.clear()
        self._success_history.clear()
        return count
