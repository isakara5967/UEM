"""
core/learning/feedback.py

Feedback Collector - Kullanici geri bildirimi toplama.
UEM v2 - Explicit ve implicit geri bildirim yonetimi.

Ozellikler:
- Explicit feedback: Kullanici direkt soyledi
- Implicit feedback: Davranistan cikarildi
- Interaction tracking
- User-based statistics
- Optional PostgreSQL persistence
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import logging

from .types import (
    Feedback,
    FeedbackType,
    generate_feedback_id,
)

if TYPE_CHECKING:
    from .persistence.feedback_repo import FeedbackRepository

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """
    Kullanici geri bildirimi toplama ve yonetim sinifi.

    Hem explicit (kullanici soyledi) hem de implicit (davranistan
    cikarildi) geri bildirimleri toplar ve istatistik saglar.

    Supports optional PostgreSQL persistence via repository.
    If repository is None, operates in memory-only mode.
    """

    def __init__(self, repository: Optional["FeedbackRepository"] = None):
        """
        Initialize feedback collector.

        Args:
            repository: Feedback repository for DB persistence (opsiyonel)
        """
        self.repository = repository
        self._feedback_history: List[Feedback] = []
        self._interaction_feedback: Dict[str, List[Feedback]] = defaultdict(list)
        self._user_feedback: Dict[str, List[Feedback]] = defaultdict(list)

        # Load from DB if repository available
        if self.repository:
            self._load_from_db()

    def _load_from_db(self) -> None:
        """Load feedbacks from database into memory."""
        if not self.repository:
            return

        try:
            feedbacks = self.repository.get_all()
            for feedback in feedbacks:
                self._feedback_history.append(feedback)
                self._interaction_feedback[feedback.interaction_id].append(feedback)
                if feedback.user_id:
                    self._user_feedback[feedback.user_id].append(feedback)
            logger.info(f"Loaded {len(feedbacks)} feedbacks from database")
        except Exception as e:
            logger.error(f"Error loading feedbacks from database: {e}")

    def _save_to_db(self, feedback: Feedback) -> None:
        """Save feedback to database."""
        if not self.repository:
            return

        try:
            self.repository.save(feedback)
        except Exception as e:
            logger.error(f"Error saving feedback to database: {e}")

    def record(
        self,
        interaction_id: str,
        feedback_type: FeedbackType,
        value: float,
        user_id: Optional[str] = None,
        context: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Feedback:
        """
        Geri bildirim kaydet.

        Args:
            interaction_id: Etkilesim ID'si
            feedback_type: Geri bildirim turu
            value: Deger (-1.0 ile 1.0 arasi)
            user_id: Kullanici ID'si (opsiyonel)
            context: Baglam bilgisi (opsiyonel)
            reason: Sebep (opsiyonel)

        Returns:
            Olusturulan Feedback nesnesi
        """
        # Clamp value to valid range
        value = max(-1.0, min(1.0, value))

        feedback = Feedback(
            id=generate_feedback_id(),
            interaction_id=interaction_id,
            feedback_type=feedback_type,
            value=value,
            timestamp=datetime.now(),
            user_id=user_id,
            context=context,
            reason=reason
        )

        self._feedback_history.append(feedback)
        self._interaction_feedback[interaction_id].append(feedback)

        if user_id:
            self._user_feedback[user_id].append(feedback)

        # Persist to database
        self._save_to_db(feedback)

        return feedback

    def record_explicit(
        self,
        interaction_id: str,
        positive: bool,
        reason: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Feedback:
        """
        Explicit (kullanici soyledi) geri bildirim kaydet.

        Args:
            interaction_id: Etkilesim ID'si
            positive: Olumlu mu?
            reason: Sebep (opsiyonel)
            user_id: Kullanici ID'si (opsiyonel)

        Returns:
            Olusturulan Feedback nesnesi
        """
        value = 1.0 if positive else -1.0

        return self.record(
            interaction_id=interaction_id,
            feedback_type=FeedbackType.EXPLICIT,
            value=value,
            user_id=user_id,
            reason=reason
        )

    def record_implicit(
        self,
        interaction_id: str,
        signals: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Feedback:
        """
        Implicit (davranistan cikarildi) geri bildirim kaydet.

        Implicit signals:
        - continued_conversation: True/False
        - response_time: "fast"/"slow"
        - sentiment_change: "positive"/"negative"/"neutral"
        - follow_up_questions: count (int)

        Args:
            interaction_id: Etkilesim ID'si
            signals: Davranis sinyalleri
            user_id: Kullanici ID'si (opsiyonel)

        Returns:
            Olusturulan Feedback nesnesi
        """
        # Calculate implicit value from signals
        value = self._calculate_implicit_value(signals)

        # Build context from signals
        context_parts = []
        for key, val in signals.items():
            context_parts.append(f"{key}={val}")
        context = ", ".join(context_parts) if context_parts else None

        return self.record(
            interaction_id=interaction_id,
            feedback_type=FeedbackType.IMPLICIT,
            value=value,
            user_id=user_id,
            context=context
        )

    def _calculate_implicit_value(self, signals: Dict[str, Any]) -> float:
        """
        Implicit sinyallerden deger hesapla.

        Args:
            signals: Davranis sinyalleri

        Returns:
            Hesaplanan deger (-1.0 ile 1.0 arasi)
        """
        value = 0.0
        weight_sum = 0.0

        # continued_conversation: +0.3 if True, -0.2 if False
        if "continued_conversation" in signals:
            weight = 0.3
            if signals["continued_conversation"]:
                value += 0.3
            else:
                value -= 0.2
            weight_sum += weight

        # response_time: +0.2 if fast, -0.1 if slow
        if "response_time" in signals:
            weight = 0.2
            if signals["response_time"] == "fast":
                value += 0.2
            elif signals["response_time"] == "slow":
                value -= 0.1
            weight_sum += weight

        # sentiment_change: +0.4 if positive, -0.4 if negative
        if "sentiment_change" in signals:
            weight = 0.4
            if signals["sentiment_change"] == "positive":
                value += 0.4
            elif signals["sentiment_change"] == "negative":
                value -= 0.4
            weight_sum += weight

        # follow_up_questions: +0.1 per question (max 0.3)
        if "follow_up_questions" in signals:
            weight = 0.3
            count = int(signals["follow_up_questions"])
            value += min(count * 0.1, 0.3)
            weight_sum += weight

        # Normalize if we have weights
        if weight_sum > 0:
            value = value / weight_sum

        # Clamp to valid range
        return max(-1.0, min(1.0, value))

    def get_feedback(self, interaction_id: str) -> List[Feedback]:
        """
        Etkilesime ait geri bildirimleri getir.

        Args:
            interaction_id: Etkilesim ID'si

        Returns:
            Geri bildirim listesi
        """
        return list(self._interaction_feedback.get(interaction_id, []))

    def get_history(self, limit: int = 100) -> List[Feedback]:
        """
        Geri bildirim gecmisini getir.

        Args:
            limit: Maksimum kayit sayisi

        Returns:
            Son N geri bildirim
        """
        return list(self._feedback_history[-limit:])

    def get_by_user(self, user_id: str) -> List[Feedback]:
        """
        Kullaniciya ait geri bildirimleri getir.

        Args:
            user_id: Kullanici ID'si

        Returns:
            Geri bildirim listesi
        """
        return list(self._user_feedback.get(user_id, []))

    def get_average_score(self, user_id: Optional[str] = None) -> float:
        """
        Ortalama geri bildirim skorunu hesapla.

        Args:
            user_id: Kullanici ID'si (opsiyonel, verilmezse tum kayitlar)

        Returns:
            Ortalama skor (-1.0 ile 1.0 arasi), kayit yoksa 0.0
        """
        if user_id:
            feedbacks = self._user_feedback.get(user_id, [])
        else:
            feedbacks = self._feedback_history

        if not feedbacks:
            return 0.0

        total = sum(f.value for f in feedbacks)
        return total / len(feedbacks)

    def get_stats(self) -> Dict[str, Any]:
        """
        Geri bildirim istatistiklerini getir.

        Returns:
            Istatistik sozlugu
        """
        total = len(self._feedback_history)

        if total == 0:
            return {
                "total_feedback": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "explicit_count": 0,
                "implicit_count": 0,
                "average_score": 0.0,
                "unique_users": 0,
                "unique_interactions": 0
            }

        positive = sum(1 for f in self._feedback_history if f.value > 0.3)
        negative = sum(1 for f in self._feedback_history if f.value < -0.3)
        neutral = total - positive - negative

        explicit = sum(1 for f in self._feedback_history if f.feedback_type == FeedbackType.EXPLICIT)
        implicit = sum(1 for f in self._feedback_history if f.feedback_type == FeedbackType.IMPLICIT)

        return {
            "total_feedback": total,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "explicit_count": explicit,
            "implicit_count": implicit,
            "average_score": self.get_average_score(),
            "unique_users": len(self._user_feedback),
            "unique_interactions": len(self._interaction_feedback)
        }

    def clear(self) -> int:
        """
        Tum geri bildirimleri temizle.

        Returns:
            Silinen kayit sayisi
        """
        count = len(self._feedback_history)
        self._feedback_history.clear()
        self._interaction_feedback.clear()
        self._user_feedback.clear()

        # Clear database
        if self.repository:
            try:
                self.repository.clear()
            except Exception as e:
                logger.error(f"Error clearing feedbacks from database: {e}")

        return count
