"""
core/learning/episode.py

Episode - Etkilesim kaydi ve sonucu.
UEM v2 - Ogrenme sistemi icin episode veri yapilari.

Episode, bir kullanici etkilesiminin tam kaydini tutar:
- Kullanici mesaji
- Algilanan durum (situation)
- Secilen dialogue act'ler
- Kullanilan construction'lar
- Sonuc ve geri bildirim

Bu kayitlar:
- Pattern ogrenme icin kullanilir
- Benzer durumlari bulmak icin karsilastirilir
- Basarili stratejileri genellestirmek icin analiz edilir
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class EpisodeOutcome:
    """
    Episode sonucu - Etkilesimin nasil sonuclandigini kaydeder.

    Attributes:
        success: Etkilesim basarili mi?
        explicit_feedback: Kullanicinin direkt verdigi geri bildirim [-1.0, 1.0]
        implicit_signals: Dolayli sinyaller (ornek: conversation_continued, topic_changed)
        trust_delta: Guven skorundaki degisim
    """
    success: bool
    explicit_feedback: Optional[float] = None  # -1.0 to 1.0
    implicit_signals: Dict[str, Any] = field(default_factory=dict)
    trust_delta: float = 0.0

    def __post_init__(self):
        """Validate feedback range."""
        if self.explicit_feedback is not None:
            if not -1.0 <= self.explicit_feedback <= 1.0:
                raise ValueError(
                    f"explicit_feedback must be between -1.0 and 1.0, "
                    f"got {self.explicit_feedback}"
                )

    @property
    def overall_score(self) -> float:
        """
        Genel basari skoru hesapla.

        Returns:
            float: -1.0 ile 1.0 arasi skor
        """
        # Explicit feedback varsa agirlikli kullan
        if self.explicit_feedback is not None:
            base_score = self.explicit_feedback
        else:
            # Implicit sinyallerden cikar
            base_score = 0.5 if self.success else -0.3

        # Trust delta'yi da dahil et
        return max(-1.0, min(1.0, base_score + (self.trust_delta * 0.3)))

    @property
    def has_positive_outcome(self) -> bool:
        """Sonuc pozitif mi?"""
        return self.overall_score > 0.0


@dataclass
class Episode:
    """
    Episode - Tek bir etkilesimin tam kaydi.

    Attributes:
        id: Benzersiz episode ID
        user_message: Kullanici mesaji
        situation_summary: SituationModel ozeti
        dialogue_acts: Secilen dialogue act'ler
        intent: Algilanan kullanici niyeti
        emotion_label: Algilanan duygu etiketi
        constructions_used: Kullanilan construction ID'leri
        outcome: Etkilesim sonucu
        trust_delta: Guven degisimi
        feedback: Opsiyonel metin geri bildirimi
        created_at: Olusturma zamani
        session_id: Ait oldugu oturum
        context: Ek baglamsal bilgi
    """
    id: str
    user_message: str
    situation_summary: Dict[str, Any]
    dialogue_acts: List[str]  # DialogueAct.value listesi
    intent: str
    emotion_label: str
    constructions_used: List[str]
    outcome: EpisodeOutcome
    trust_delta: float = 0.0
    feedback: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Auto-generate ID if not provided."""
        if not self.id:
            self.id = generate_episode_id()

    @property
    def success(self) -> bool:
        """Episode basarili mi?"""
        return self.outcome.success

    @property
    def word_count(self) -> int:
        """Mesajdaki kelime sayisi."""
        return len(self.user_message.split())

    @property
    def has_emotion(self) -> bool:
        """Duygu algilandi mi?"""
        return bool(self.emotion_label and self.emotion_label != "neutral")

    @property
    def dialogue_act_count(self) -> int:
        """Dialogue act sayisi."""
        return len(self.dialogue_acts)

    @property
    def construction_count(self) -> int:
        """Kullanilan construction sayisi."""
        return len(self.constructions_used)

    def to_dict(self) -> Dict[str, Any]:
        """
        Episode'u dictionary'e donustur.

        Returns:
            Dict[str, Any]: Episode verisi
        """
        return {
            "id": self.id,
            "user_message": self.user_message,
            "situation_summary": self.situation_summary,
            "dialogue_acts": self.dialogue_acts,
            "intent": self.intent,
            "emotion_label": self.emotion_label,
            "constructions_used": self.constructions_used,
            "outcome": {
                "success": self.outcome.success,
                "explicit_feedback": self.outcome.explicit_feedback,
                "implicit_signals": self.outcome.implicit_signals,
                "trust_delta": self.outcome.trust_delta,
            },
            "trust_delta": self.trust_delta,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat(),
            "session_id": self.session_id,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Episode":
        """
        Dictionary'den Episode olustur.

        Args:
            data: Episode verisi

        Returns:
            Episode: Yeni episode
        """
        outcome_data = data.get("outcome", {})
        outcome = EpisodeOutcome(
            success=outcome_data.get("success", False),
            explicit_feedback=outcome_data.get("explicit_feedback"),
            implicit_signals=outcome_data.get("implicit_signals", {}),
            trust_delta=outcome_data.get("trust_delta", 0.0),
        )

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            id=data.get("id", ""),
            user_message=data.get("user_message", ""),
            situation_summary=data.get("situation_summary", {}),
            dialogue_acts=data.get("dialogue_acts", []),
            intent=data.get("intent", ""),
            emotion_label=data.get("emotion_label", ""),
            constructions_used=data.get("constructions_used", []),
            outcome=outcome,
            trust_delta=data.get("trust_delta", 0.0),
            feedback=data.get("feedback"),
            created_at=created_at,
            session_id=data.get("session_id"),
            context=data.get("context", {}),
        )


@dataclass
class EpisodeCollection:
    """
    Episode kolleksiyonu - Birden fazla episode'u gruplar.

    Attributes:
        episodes: Episode listesi
        session_id: Oturum ID'si (opsiyonel)
        metadata: Ek meta veri
    """
    episodes: List[Episode] = field(default_factory=list)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add(self, episode: Episode) -> None:
        """Episode ekle."""
        self.episodes.append(episode)

    def get_successful(self) -> List[Episode]:
        """Basarili episode'lari getir."""
        return [e for e in self.episodes if e.success]

    def get_by_intent(self, intent: str) -> List[Episode]:
        """Intent'e gore filtrele."""
        return [e for e in self.episodes if e.intent == intent]

    def get_by_emotion(self, emotion: str) -> List[Episode]:
        """Duyguya gore filtrele."""
        return [e for e in self.episodes if e.emotion_label == emotion]

    def get_recent(self, count: int = 10) -> List[Episode]:
        """Son N episode'u getir."""
        sorted_episodes = sorted(
            self.episodes,
            key=lambda e: e.created_at,
            reverse=True
        )
        return sorted_episodes[:count]

    @property
    def success_rate(self) -> float:
        """Basari orani."""
        if not self.episodes:
            return 0.0
        successful = sum(1 for e in self.episodes if e.success)
        return successful / len(self.episodes)

    @property
    def average_trust_delta(self) -> float:
        """Ortalama guven degisimi."""
        if not self.episodes:
            return 0.0
        return sum(e.trust_delta for e in self.episodes) / len(self.episodes)

    def __len__(self) -> int:
        return len(self.episodes)

    def __iter__(self):
        return iter(self.episodes)


def generate_episode_id() -> str:
    """Generate unique episode ID."""
    return f"ep_{uuid.uuid4().hex[:12]}"
