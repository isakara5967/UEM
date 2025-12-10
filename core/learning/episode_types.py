"""
core/learning/episode_types.py

Faz 5 Episode Logging Types - Comprehensive conversation turn recording.

EpisodeLog captures every detail of a conversation turn for pattern evolution:
- Input: User message and normalization
- Intent: Recognition results with pattern IDs
- Context: Conversation state snapshot
- Decision: Act selection with scores
- Construction: Used template details
- Output: Generated response
- Risk & Approval: Safety checks
- Feedback: Explicit and implicit signals
- Meta: Performance metrics

UEM v2 - Faz 5 Pattern Evolution Foundation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple
import uuid

from core.language.intent.types import IntentCategory
from core.language.dialogue.types import DialogueAct
from core.language.risk.types import RiskLevel
from core.language.risk.approver import ApprovalDecision


def _clean_string(s: str) -> str:
    r"""
    Remove surrogate characters from string.

    Surrogate characters (\udcXX) cause JSON encoding errors.
    This happens when terminal input contains invalid UTF-8.

    Args:
        s: Input string (may contain surrogates)

    Returns:
        Clean string (surrogates replaced with �)
    """
    if not s:
        return s
    # Encode with 'replace' to remove surrogates, then decode
    return s.encode('utf-8', errors='replace').decode('utf-8', errors='replace')


class ConstructionSource(str, Enum):
    """Construction kaynağı - nereden geldi?"""
    HUMAN_DEFAULT = "human_default"  # MVCS gibi insan tarafından yazılmış
    LEARNED = "learned"              # Öğrenilmiş/jeneratif
    ADAPTED = "adapted"              # Adapte edilmiş


class ConstructionLevel(str, Enum):
    """Construction seviyesi - Construction Grammar teorisinden."""
    DEEP = "deep"       # Derin yapı
    MIDDLE = "middle"   # Orta seviye
    SURFACE = "surface" # Yüzey formu


class ApprovalStatus(str, Enum):
    """Approval durumu."""
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"
    NOT_CHECKED = "not_checked"


@dataclass
class ImplicitFeedback:
    """
    Dolaylı geri bildirim sinyalleri.

    Kullanıcının davranışlarından çıkarılan implicit feedback.

    Attributes:
        conversation_continued: Kullanıcı konuşmaya devam etti mi?
        user_rephrased: Kullanıcı mesajını yeniden ifade etti mi? (anlaşılmadı sinyali)
        user_thanked: Kullanıcı teşekkür etti mi? (memnuniyet sinyali)
        user_complained: Kullanıcı şikayet etti mi? (memnuniyetsizlik sinyali)
        session_ended_abruptly: Oturum aniden bitti mi? (memnuniyetsizlik sinyali)
    """
    conversation_continued: bool = False
    user_rephrased: bool = False
    user_thanked: bool = False
    user_complained: bool = False
    session_ended_abruptly: bool = False

    def get_signal_score(self) -> float:
        """
        Implicit sinyallerden skor hesapla.

        Returns:
            float: -1.0 to 1.0 arası skor

        TODO Faz 6+: Daha sofistike scoring için FeedbackWeighter kullan.
        Şimdilik basit weighted sum yeterli.
        """
        score = 0.0

        if self.conversation_continued:
            score += 0.3
        if self.user_thanked:
            score += 0.4
        if self.user_rephrased:
            score -= 0.3
        if self.user_complained:
            score -= 0.5
        if self.session_ended_abruptly:
            score -= 0.4

        return max(-1.0, min(1.0, score))


@dataclass
class EpisodeLog:
    """
    Episode Log - Tek bir conversation turn'ünün kapsamlı kaydı.

    Faz 5 Pattern Evolution için veri sağlar.
    Her alan detaylı loglama için tasarlanmış.
    """

    # === 1. KİMLİK ===
    id: str
    session_id: str
    turn_number: int

    # === 2. INPUT ===
    user_message: str
    user_message_normalized: str

    # === 3. INTENT ===
    intent_primary: IntentCategory

    # Fields with defaults below
    timestamp: datetime = field(default_factory=datetime.now)
    intent_secondary: Optional[IntentCategory] = None
    intent_confidence: float = 0.0
    intent_matched_pattern_ids: List[str] = field(default_factory=list)

    # === 4. CONTEXT SNAPSHOT ===
    context_turn_count: int = 0
    context_last_user_intent: Optional[IntentCategory] = None
    context_last_assistant_act: Optional[DialogueAct] = None
    context_sentiment: float = 0.0
    context_sentiment_trend: int = 0  # -1 (negative), 0 (neutral), 1 (positive)
    context_topic: Optional[str] = None
    context_is_followup: bool = False

    # === 5. KARAR (Act Selection) ===
    dialogue_act_selected: DialogueAct = DialogueAct.ACKNOWLEDGE
    dialogue_act_score: float = 0.0
    dialogue_act_alternatives: List[Tuple[str, float]] = field(default_factory=list)  # [(act, score)]

    # === 6. CONSTRUCTION ===
    construction_id: str = ""
    construction_category: str = ""
    construction_source: ConstructionSource = ConstructionSource.HUMAN_DEFAULT
    construction_level: ConstructionLevel = ConstructionLevel.SURFACE

    # === 7. OUTPUT ===
    response_text: str = ""
    response_length_chars: int = 0
    response_length_words: int = 0

    # === 8. RISK & APPROVAL ===
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: float = 0.0
    approval_status: ApprovalStatus = ApprovalStatus.NOT_CHECKED
    approval_reasons: List[str] = field(default_factory=list)

    # === 9. FEEDBACK ===
    feedback_explicit: Optional[float] = None  # -1.0 to 1.0
    feedback_implicit: Optional[ImplicitFeedback] = None
    trust_before: Optional[float] = None
    trust_after: Optional[float] = None

    # === 10. META ===
    processing_time_ms: int = 0
    pipeline_version: str = "1.0"

    def __post_init__(self):
        """Post-initialization validation and calculations."""
        # Calculate response lengths if not provided
        if self.response_text:
            if self.response_length_chars == 0:
                self.response_length_chars = len(self.response_text)
            if self.response_length_words == 0:
                self.response_length_words = len(self.response_text.split())

        # Validate feedback range
        if self.feedback_explicit is not None:
            if not -1.0 <= self.feedback_explicit <= 1.0:
                raise ValueError(
                    f"feedback_explicit must be between -1.0 and 1.0, "
                    f"got {self.feedback_explicit}"
                )

    @property
    def has_explicit_feedback(self) -> bool:
        """Explicit feedback var mı?"""
        return self.feedback_explicit is not None

    @property
    def has_implicit_feedback(self) -> bool:
        """Implicit feedback var mı?"""
        return self.feedback_implicit is not None

    @property
    def overall_feedback_score(self) -> float:
        """
        Genel feedback skoru hesapla.

        Returns:
            float: -1.0 to 1.0 arası skor
        """
        if self.has_explicit_feedback:
            # Explicit feedback varsa öncelikli
            return self.feedback_explicit
        elif self.has_implicit_feedback:
            # Implicit sinyallerden çıkar
            return self.feedback_implicit.get_signal_score()
        else:
            # Feedback yoksa nötr
            return 0.0

    @property
    def is_successful(self) -> bool:
        """Episode başarılı mı?"""
        return self.overall_feedback_score > 0.0

    @property
    def has_compound_intent(self) -> bool:
        """Compound intent var mı?"""
        return self.intent_secondary is not None

    @property
    def trust_delta(self) -> Optional[float]:
        """Güven değişimi."""
        if self.trust_before is not None and self.trust_after is not None:
            return self.trust_after - self.trust_before
        return None

    def to_dict(self) -> dict:
        """
        Episode'u dictionary'e çevir (JSONL için).

        Surrogate characters temizlenir (JSON encoding hatası önleme).
        """
        return {
            # Kimlik
            "id": _clean_string(self.id),
            "session_id": _clean_string(self.session_id),
            "turn_number": self.turn_number,
            "timestamp": self.timestamp.isoformat(),

            # Input (clean surrogates)
            "user_message": _clean_string(self.user_message),
            "user_message_normalized": _clean_string(self.user_message_normalized),

            # Intent
            "intent_primary": self.intent_primary.value if self.intent_primary else None,
            "intent_secondary": self.intent_secondary.value if self.intent_secondary else None,
            "intent_confidence": self.intent_confidence,
            "intent_matched_pattern_ids": self.intent_matched_pattern_ids,

            # Context
            "context_turn_count": self.context_turn_count,
            "context_last_user_intent": self.context_last_user_intent.value if self.context_last_user_intent else None,
            "context_last_assistant_act": self.context_last_assistant_act.value if self.context_last_assistant_act else None,
            "context_sentiment": self.context_sentiment,
            "context_sentiment_trend": self.context_sentiment_trend,
            "context_topic": _clean_string(self.context_topic) if self.context_topic else None,
            "context_is_followup": self.context_is_followup,

            # Karar
            "dialogue_act_selected": self.dialogue_act_selected.value if self.dialogue_act_selected else None,
            "dialogue_act_score": self.dialogue_act_score,
            "dialogue_act_alternatives": self.dialogue_act_alternatives,

            # Construction (clean surrogates)
            "construction_id": _clean_string(self.construction_id),
            "construction_category": _clean_string(self.construction_category),
            "construction_source": self.construction_source.value if self.construction_source else None,
            "construction_level": self.construction_level.value if self.construction_level else None,

            # Output (clean surrogates)
            "response_text": _clean_string(self.response_text),
            "response_length_chars": self.response_length_chars,
            "response_length_words": self.response_length_words,

            # Risk & Approval
            "risk_level": self.risk_level.value if self.risk_level else None,
            "risk_score": self.risk_score,
            "approval_status": self.approval_status.value if self.approval_status else None,
            "approval_reasons": self.approval_reasons,

            # Feedback
            "feedback_explicit": self.feedback_explicit,
            "feedback_implicit": {
                "conversation_continued": self.feedback_implicit.conversation_continued,
                "user_rephrased": self.feedback_implicit.user_rephrased,
                "user_thanked": self.feedback_implicit.user_thanked,
                "user_complained": self.feedback_implicit.user_complained,
                "session_ended_abruptly": self.feedback_implicit.session_ended_abruptly,
            } if self.feedback_implicit else None,
            "trust_before": self.trust_before,
            "trust_after": self.trust_after,

            # Meta
            "processing_time_ms": self.processing_time_ms,
            "pipeline_version": self.pipeline_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpisodeLog":
        """Dictionary'den Episode oluştur (JSONL'den load için)."""
        # Parse timestamp
        timestamp_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()

        # Parse enums
        intent_primary = IntentCategory(data["intent_primary"]) if data.get("intent_primary") else IntentCategory.UNKNOWN
        intent_secondary = IntentCategory(data["intent_secondary"]) if data.get("intent_secondary") else None
        context_last_user_intent = IntentCategory(data["context_last_user_intent"]) if data.get("context_last_user_intent") else None
        context_last_assistant_act = DialogueAct(data["context_last_assistant_act"]) if data.get("context_last_assistant_act") else None
        dialogue_act_selected = DialogueAct(data["dialogue_act_selected"]) if data.get("dialogue_act_selected") else DialogueAct.ACKNOWLEDGE
        construction_source = ConstructionSource(data["construction_source"]) if data.get("construction_source") else ConstructionSource.HUMAN_DEFAULT
        construction_level = ConstructionLevel(data["construction_level"]) if data.get("construction_level") else ConstructionLevel.SURFACE
        risk_level = RiskLevel(data["risk_level"]) if data.get("risk_level") else RiskLevel.LOW
        approval_status = ApprovalStatus(data["approval_status"]) if data.get("approval_status") else ApprovalStatus.NOT_CHECKED

        # Parse implicit feedback
        feedback_implicit_data = data.get("feedback_implicit")
        feedback_implicit = None
        if feedback_implicit_data:
            feedback_implicit = ImplicitFeedback(
                conversation_continued=feedback_implicit_data.get("conversation_continued", False),
                user_rephrased=feedback_implicit_data.get("user_rephrased", False),
                user_thanked=feedback_implicit_data.get("user_thanked", False),
                user_complained=feedback_implicit_data.get("user_complained", False),
                session_ended_abruptly=feedback_implicit_data.get("session_ended_abruptly", False),
            )

        return cls(
            id=data["id"],
            session_id=data["session_id"],
            turn_number=data["turn_number"],
            timestamp=timestamp,
            user_message=data["user_message"],
            user_message_normalized=data["user_message_normalized"],
            intent_primary=intent_primary,
            intent_secondary=intent_secondary,
            intent_confidence=data.get("intent_confidence", 0.0),
            intent_matched_pattern_ids=data.get("intent_matched_pattern_ids", []),
            context_turn_count=data.get("context_turn_count", 0),
            context_last_user_intent=context_last_user_intent,
            context_last_assistant_act=context_last_assistant_act,
            context_sentiment=data.get("context_sentiment", 0.0),
            context_sentiment_trend=data.get("context_sentiment_trend", 0),
            context_topic=data.get("context_topic"),
            context_is_followup=data.get("context_is_followup", False),
            dialogue_act_selected=dialogue_act_selected,
            dialogue_act_score=data.get("dialogue_act_score", 0.0),
            dialogue_act_alternatives=data.get("dialogue_act_alternatives", []),
            construction_id=data.get("construction_id", ""),
            construction_category=data.get("construction_category", ""),
            construction_source=construction_source,
            construction_level=construction_level,
            response_text=data.get("response_text", ""),
            response_length_chars=data.get("response_length_chars", 0),
            response_length_words=data.get("response_length_words", 0),
            risk_level=risk_level,
            risk_score=data.get("risk_score", 0.0),
            approval_status=approval_status,
            approval_reasons=data.get("approval_reasons", []),
            feedback_explicit=data.get("feedback_explicit"),
            feedback_implicit=feedback_implicit,
            trust_before=data.get("trust_before"),
            trust_after=data.get("trust_after"),
            processing_time_ms=data.get("processing_time_ms", 0),
            pipeline_version=data.get("pipeline_version", "1.0"),
        )


def generate_episode_log_id() -> str:
    """Generate unique episode log ID."""
    return f"eplog_{uuid.uuid4().hex[:12]}"
