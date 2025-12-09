"""
core/learning/feedback.py

Feedback Collector ve Weighter - Kullanici geri bildirimi toplama ve agirliklama.
UEM v2 - Explicit ve implicit geri bildirim yonetimi.

Ozellikler:
- FeedbackCollector: Geri bildirim toplama
- FeedbackWeighter: Episode agirliklama (Alice uzlasisi)
- Explicit feedback: Kullanici direkt soyledi
- Implicit feedback: Davranistan cikarildi
- Interaction tracking
- User-based statistics
- Optional PostgreSQL persistence
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
import logging
import re

from .types import (
    Feedback,
    FeedbackType,
    generate_feedback_id,
)

if TYPE_CHECKING:
    from .persistence.feedback_repo import FeedbackRepository
    from .episode import Episode

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


# =============================================================================
# FeedbackWeighter - Episode Agirliklama (Alice Uzlasisi)
# =============================================================================

@dataclass
class FeedbackWeighterConfig:
    """
    FeedbackWeighter konfigurasyonu.

    Attributes:
        explicit_weight: Explicit feedback agirligi (kullanici direkt soyledi)
        trust_delta_weight: Trust degisimi agirligi
        implicit_weight: Implicit sinyal agirligi (davranistan cikarildi)
        positive_patterns: Pozitif feedback pattern'leri
        negative_patterns: Negatif feedback pattern'leri
        normalize_turkish: Turkce karakter normalizasyonu uygula
    """
    explicit_weight: float = 3.0
    trust_delta_weight: float = 1.0
    implicit_weight: float = 0.5

    # Pozitif feedback pattern'leri (normalized)
    positive_patterns: Set[str] = field(default_factory=lambda: {
        # Tesekkur
        "tesekkur", "tesekkurler", "sagol", "sagolun", "eyvallah",
        # Beğeni
        "harika", "mukemmel", "super", "guzel", "iyi", "hos",
        "basarili", "dogru", "evet", "tamam", "anladim",
        # Yardim
        "yardimci oldu", "yardimci oldun", "isime yaradi", "cok iyi",
        "faydali", "yararlı",
        # Emoji-like text
        "bravo", "aferin",
    })

    # Negatif feedback pattern'leri (normalized)
    negative_patterns: Set[str] = field(default_factory=lambda: {
        # Yanlis
        "yanlis", "hatali", "dogru degil", "oyle degil",
        # Kotu
        "kotu", "berbat", "sacma", "anlamsiz",
        # Yardim etmedi
        "yardimci olmadi", "yardimci olmuyor", "isime yaramadi",
        "anlamadim", "anlasilmadi",
        # Red
        "hayir", "istemiyorum", "bos ver", "birak",
        # Sikyet
        "yeterli degil", "eksik", "yetersiz",
    })

    normalize_turkish: bool = True


@dataclass
class ImplicitSignals:
    """
    Implicit (davranistan cikarilan) sinyaller.

    Attributes:
        conversation_continued: Konusma devam etti mi?
        asked_followup: Takip sorusu soruldu mu?
        repeated_question: Soru tekrarlandi mi? (negatif)
        session_ended_abruptly: Oturum aniden bitti mi? (negatif)
        topic_changed: Konu degistirildi mi?
        response_acknowledged: Cevap onaylandi mi?
    """
    conversation_continued: bool = False
    asked_followup: bool = False
    repeated_question: bool = False
    session_ended_abruptly: bool = False
    topic_changed: bool = False
    response_acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Dict'e donustur."""
        return {
            "conversation_continued": self.conversation_continued,
            "asked_followup": self.asked_followup,
            "repeated_question": self.repeated_question,
            "session_ended_abruptly": self.session_ended_abruptly,
            "topic_changed": self.topic_changed,
            "response_acknowledged": self.response_acknowledged,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImplicitSignals":
        """Dict'ten olustur."""
        return cls(
            conversation_continued=data.get("conversation_continued", False),
            asked_followup=data.get("asked_followup", False),
            repeated_question=data.get("repeated_question", False),
            session_ended_abruptly=data.get("session_ended_abruptly", False),
            topic_changed=data.get("topic_changed", False),
            response_acknowledged=data.get("response_acknowledged", False),
        )


class FeedbackWeighter:
    """
    Feedback agirliklama sistemi (Alice uzlasisi).

    Episode'lardan feedback skoru hesaplar:
    - Explicit feedback: Kullanici direkt ifade etti (agirlik: 3.0)
    - Trust delta: Guven skorundaki degisim (agirlik: 1.0)
    - Implicit signals: Davranistan cikarilan sinyaller (agirlik: 0.5)

    Kullanim:
        weighter = FeedbackWeighter()

        # Tek episode
        score = weighter.compute_feedback_score(episode)

        # Mesajdan explicit feedback cikar
        feedback = weighter.extract_explicit_feedback("Tesekkurler, cok yardimci oldun!")
        # -> 1.0 (pozitif)

        # Birden fazla episode
        avg_score = weighter.aggregate_episode_feedback(episodes)
    """

    def __init__(self, config: Optional[FeedbackWeighterConfig] = None):
        """
        FeedbackWeighter olustur.

        Args:
            config: Konfigurasyon (opsiyonel)
        """
        self.config = config or FeedbackWeighterConfig()
        self._normalize_func = self._get_normalize_func()

    def _get_normalize_func(self):
        """Normalizasyon fonksiyonunu al."""
        if self.config.normalize_turkish:
            try:
                from core.utils.text import normalize_turkish
                return normalize_turkish
            except ImportError:
                logger.warning("normalize_turkish not available, using simple lower()")
                return lambda x: x.lower() if x else ""
        return lambda x: x.lower() if x else ""

    def compute_feedback_score(self, episode: "Episode") -> float:
        """
        Episode icin feedback skoru hesapla.

        Formul:
            score = (explicit * explicit_weight +
                     trust_delta * trust_delta_weight +
                     implicit * implicit_weight) / toplam_agirlik

        Args:
            episode: Degerlendirilen episode

        Returns:
            float: Feedback skoru [-1.0, 1.0]
        """
        total_weight = 0.0
        weighted_sum = 0.0

        # 1. Explicit feedback (outcome'dan veya mesajdan)
        explicit_score = self._get_explicit_score(episode)
        if explicit_score is not None:
            weighted_sum += explicit_score * self.config.explicit_weight
            total_weight += self.config.explicit_weight

        # 2. Trust delta
        if episode.trust_delta != 0.0:
            # Trust delta'yi [-1, 1] araliginda normalize et
            normalized_trust = max(-1.0, min(1.0, episode.trust_delta))
            weighted_sum += normalized_trust * self.config.trust_delta_weight
            total_weight += self.config.trust_delta_weight

        # 3. Implicit signals
        implicit_score = self._compute_implicit_score(episode)
        if implicit_score != 0.0:
            weighted_sum += implicit_score * self.config.implicit_weight
            total_weight += self.config.implicit_weight

        # Normalize et
        if total_weight > 0:
            score = weighted_sum / total_weight
        else:
            # Hic sinyal yoksa notr
            score = 0.0

        # [-1, 1] araliginda clamp et
        return max(-1.0, min(1.0, score))

    def _get_explicit_score(self, episode: "Episode") -> Optional[float]:
        """
        Episode'dan explicit feedback skoru al.

        Args:
            episode: Episode

        Returns:
            Optional[float]: Explicit skor veya None
        """
        # Oncelikle outcome'daki explicit feedback
        if episode.outcome.explicit_feedback is not None:
            return episode.outcome.explicit_feedback

        # Mesajdan cikar (sonraki mesaj varsa)
        if episode.feedback:
            return self.extract_explicit_feedback(episode.feedback)

        # Kullanici mesajindan cikar (tesekkur vb.)
        return self.extract_explicit_feedback(episode.user_message)

    def _compute_implicit_score(self, episode: "Episode") -> float:
        """
        Implicit sinyallerden skor hesapla.

        Args:
            episode: Episode

        Returns:
            float: Implicit skor [-1.0, 1.0]
        """
        signals = self.extract_implicit_signals(episode.outcome.implicit_signals)
        return self.compute_implicit_value(signals)

    def extract_explicit_feedback(self, user_message: str) -> Optional[float]:
        """
        Kullanici mesajindan explicit feedback cikar.

        Args:
            user_message: Kullanici mesaji

        Returns:
            Optional[float]: Feedback degeri veya None
                1.0 = pozitif
                -1.0 = negatif
                None = belirsiz
        """
        if not user_message:
            return None

        normalized = self._normalize_func(user_message)

        # Pozitif pattern kontrolu
        for pattern in self.config.positive_patterns:
            if pattern in normalized:
                return 1.0

        # Negatif pattern kontrolu
        for pattern in self.config.negative_patterns:
            if pattern in normalized:
                return -1.0

        return None

    def extract_implicit_signals(
        self,
        session_context: Dict[str, Any]
    ) -> ImplicitSignals:
        """
        Session context'ten implicit sinyalleri cikar.

        Args:
            session_context: Oturum baglami

        Returns:
            ImplicitSignals: Cikarilan sinyaller
        """
        if not session_context:
            return ImplicitSignals()

        return ImplicitSignals(
            conversation_continued=session_context.get("conversation_continued", False),
            asked_followup=session_context.get("asked_followup", False),
            repeated_question=session_context.get("repeated_question", False),
            session_ended_abruptly=session_context.get("session_ended_abruptly", False),
            topic_changed=session_context.get("topic_changed", False),
            response_acknowledged=session_context.get("response_acknowledged", False),
        )

    def compute_implicit_value(self, signals: ImplicitSignals) -> float:
        """
        Implicit sinyallerden deger hesapla.

        Pozitif sinyaller:
        - conversation_continued: +0.3
        - asked_followup: +0.2
        - response_acknowledged: +0.4

        Negatif sinyaller:
        - repeated_question: -0.5
        - session_ended_abruptly: -0.4
        - topic_changed: -0.2

        Args:
            signals: Implicit sinyaller

        Returns:
            float: Hesaplanan deger [-1.0, 1.0]
        """
        score = 0.0

        # Pozitif sinyaller
        if signals.conversation_continued:
            score += 0.3
        if signals.asked_followup:
            score += 0.2
        if signals.response_acknowledged:
            score += 0.4

        # Negatif sinyaller
        if signals.repeated_question:
            score -= 0.5
        if signals.session_ended_abruptly:
            score -= 0.4
        if signals.topic_changed:
            score -= 0.2

        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, score))

    def aggregate_episode_feedback(
        self,
        episodes: List["Episode"],
        recent_weight: float = 1.5
    ) -> float:
        """
        Birden fazla episode'un feedback'ini toparla.

        Son episode'lara daha fazla agirlik verir.

        Args:
            episodes: Episode listesi
            recent_weight: Son episode agirligi carpani

        Returns:
            float: Ortalama feedback skoru [-1.0, 1.0]
        """
        if not episodes:
            return 0.0

        # Tarihe gore sirala (eskiden yeniye)
        sorted_episodes = sorted(episodes, key=lambda e: e.created_at)

        weighted_sum = 0.0
        weight_sum = 0.0

        n = len(sorted_episodes)
        for i, episode in enumerate(sorted_episodes):
            score = self.compute_feedback_score(episode)

            # Son episode'lara daha fazla agirlik
            # i=0 (en eski) -> agirlik=1.0
            # i=n-1 (en yeni) -> agirlik=recent_weight
            position_weight = 1.0 + (recent_weight - 1.0) * (i / max(1, n - 1))

            weighted_sum += score * position_weight
            weight_sum += position_weight

        if weight_sum > 0:
            return max(-1.0, min(1.0, weighted_sum / weight_sum))
        return 0.0

    def get_feedback_breakdown(self, episode: "Episode") -> Dict[str, Any]:
        """
        Episode feedback'inin detayli dokumunu getir.

        Args:
            episode: Episode

        Returns:
            Dict: Detayli feedback bilgisi
        """
        explicit_score = self._get_explicit_score(episode)
        implicit_signals = self.extract_implicit_signals(episode.outcome.implicit_signals)
        implicit_score = self.compute_implicit_value(implicit_signals)
        total_score = self.compute_feedback_score(episode)

        return {
            "total_score": total_score,
            "explicit": {
                "score": explicit_score,
                "weight": self.config.explicit_weight,
                "source": "outcome" if episode.outcome.explicit_feedback is not None else "message",
            },
            "trust_delta": {
                "value": episode.trust_delta,
                "weight": self.config.trust_delta_weight,
            },
            "implicit": {
                "score": implicit_score,
                "weight": self.config.implicit_weight,
                "signals": implicit_signals.to_dict(),
            },
        }

    def is_positive_feedback(self, episode: "Episode") -> bool:
        """Episode feedback'i pozitif mi?"""
        return self.compute_feedback_score(episode) > 0.3

    def is_negative_feedback(self, episode: "Episode") -> bool:
        """Episode feedback'i negatif mi?"""
        return self.compute_feedback_score(episode) < -0.3
