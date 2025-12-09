"""
core/language/dialogue/types.py

Dialogue Types - Konuşma eylemleri ve mesaj planlama tipleri.
UEM v2 - Thought-to-Speech Pipeline veri yapıları.

Özellikler:
- DialogueAct: 17 konuşma eylemi türü
- ToneType: 8 ton türü
- SituationModel: Algı/Bellek/Bilişim çıktısı
- MessagePlan: Executive karar çıktısı
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class DialogueAct(str, Enum):
    """
    Konuşma eylemleri - Speech Act Theory'den esinlenilmiş.

    Kategoriler:
    - Bilgilendirme: INFORM, EXPLAIN, CLARIFY
    - Sorgulama: ASK, CONFIRM
    - Duygusal: EMPATHIZE, ENCOURAGE, COMFORT
    - Yönlendirme: SUGGEST, WARN, ADVISE
    - Sınır: REFUSE, LIMIT, DEFLECT
    - Meta: ACKNOWLEDGE, APOLOGIZE, THANK
    """
    # Bilgilendirme (Assertives)
    INFORM = "inform"           # Bilgi ver
    EXPLAIN = "explain"         # Açıkla, detaylandır
    CLARIFY = "clarify"         # Netleştir, anlaşılmayanı açıkla

    # Sorgulama (Directives - Question)
    ASK = "ask"                 # Soru sor
    CONFIRM = "confirm"         # Teyit iste, doğrulat

    # Duygusal (Expressives)
    EMPATHIZE = "empathize"     # Empati kur, duygularını anla
    ENCOURAGE = "encourage"     # Cesaretlendir, motive et
    COMFORT = "comfort"         # Teselli et, rahatlat

    # Yönlendirme (Directives - Suggestion)
    SUGGEST = "suggest"         # Öner, alternatif sun
    WARN = "warn"               # Uyar, tehlikeye dikkat çek
    ADVISE = "advise"           # Tavsiye ver, yönlendir

    # Sınır (Commissives - Boundary)
    REFUSE = "refuse"           # Reddet, yapamam de
    LIMIT = "limit"             # Sınırla, kapsamı daralt
    DEFLECT = "deflect"         # Yönlendir, başka yere çevir

    # Meta (Acknowledgments)
    ACKNOWLEDGE = "acknowledge" # Kabul et, anladığını göster
    APOLOGIZE = "apologize"     # Özür dile
    THANK = "thank"             # Teşekkür et
    GREET = "greet"             # Selamla, karşıla


class ToneType(str, Enum):
    """
    Ton türleri - Mesajın üslup ve atmosferi.

    Ton seçimi SituationModel ve Affect modülüne göre yapılır.
    """
    FORMAL = "formal"           # Resmi, profesyonel
    CASUAL = "casual"           # Günlük, samimi
    EMPATHIC = "empathic"       # Empatik, anlayışlı
    SUPPORTIVE = "supportive"   # Destekleyici
    NEUTRAL = "neutral"         # Nötr, tarafsız
    CAUTIOUS = "cautious"       # Dikkatli, temkinli
    ENTHUSIASTIC = "enthusiastic"  # Coşkulu, heyecanlı
    SERIOUS = "serious"         # Ciddi, ağırbaşlı


@dataclass
class Actor:
    """
    Konuşmadaki aktör - Kim konuşuyor/dinliyor?

    Attributes:
        id: Benzersiz aktör ID'si
        role: Aktörün rolü (user, assistant, system, etc.)
        name: Aktörün adı (opsiyonel)
        traits: Aktör özellikleri
        context: Ek bağlam bilgisi
    """
    id: str
    role: str                           # "user", "assistant", "system", "third_party"
    name: Optional[str] = None
    traits: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate role."""
        valid_roles = {"user", "assistant", "system", "third_party"}
        if self.role not in valid_roles:
            raise ValueError(f"Invalid role '{self.role}'. Must be one of: {valid_roles}")


@dataclass
class Intention:
    """
    Niyet temsili - Aktör ne yapmak istiyor?

    Attributes:
        id: Benzersiz niyet ID'si
        actor_id: Bu niyetin sahibi
        goal: Ana hedef
        sub_goals: Alt hedefler
        confidence: Niyet tespitine güven (0.0-1.0)
        evidence: Bu niyete kanıt olan ipuçları
    """
    id: str
    actor_id: str
    goal: str
    sub_goals: List[str] = field(default_factory=list)
    confidence: float = 0.5
    evidence: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate confidence range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class Risk:
    """
    Risk bilgisi - SituationModel'deki risk temsili.

    NOT: Bu, core/language/risk/types.py'deki RiskAssessment'tan farklıdır.
    Bu sadece SituationModel içindeki risk özetidir.

    Attributes:
        category: Risk kategorisi
        level: Risk seviyesi (0.0-1.0)
        description: Risk açıklaması
        mitigation: Risk azaltma önerisi
    """
    category: str                       # "ethical", "emotional", "factual", "safety"
    level: float                        # 0.0 (düşük) - 1.0 (yüksek)
    description: str
    mitigation: Optional[str] = None

    def __post_init__(self):
        """Validate level range."""
        if not 0.0 <= self.level <= 1.0:
            raise ValueError(f"Risk level must be between 0.0 and 1.0, got {self.level}")


@dataclass
class Relationship:
    """
    İlişki bilgisi - Aktörler arası ilişki.

    Attributes:
        actor1_id: Birinci aktör
        actor2_id: İkinci aktör
        relationship_type: İlişki türü
        strength: İlişki gücü (-1.0 ile 1.0 arası)
        context: Ek bağlam
    """
    actor1_id: str
    actor2_id: str
    relationship_type: str              # "trust", "rapport", "conflict", "neutral"
    strength: float = 0.0               # -1.0 (negatif) to 1.0 (pozitif)
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate strength range."""
        if not -1.0 <= self.strength <= 1.0:
            raise ValueError(f"Relationship strength must be between -1.0 and 1.0, got {self.strength}")


@dataclass
class TemporalContext:
    """
    Zaman bağlamı - Konuşmanın zamansal özellikleri.

    Attributes:
        conversation_start: Konuşma başlangıç zamanı
        current_time: Şu anki zaman
        turn_count: Konuşma tur sayısı
        time_since_last_turn: Son turdan bu yana geçen süre (saniye)
        session_context: Oturum bağlamı
    """
    conversation_start: datetime
    current_time: datetime = field(default_factory=datetime.now)
    turn_count: int = 0
    time_since_last_turn: Optional[float] = None  # saniye
    session_context: Dict[str, Any] = field(default_factory=dict)

    @property
    def conversation_duration(self) -> float:
        """Konuşma süresi (saniye)."""
        return (self.current_time - self.conversation_start).total_seconds()


@dataclass
class EmotionalState:
    """
    Duygusal durum - Affect modülünden gelen PAD değerleri.

    Attributes:
        valence: Olumlu-olumsuz ekseni (-1.0 ile 1.0)
        arousal: Uyarılmışlık seviyesi (-1.0 ile 1.0)
        dominance: Kontrol hissi (-1.0 ile 1.0)
        primary_emotion: Ana duygu etiketi
        secondary_emotions: İkincil duygular
        confidence: Duygu tespitine güven
    """
    valence: float = 0.0                # Pleasure: -1.0 (olumsuz) to 1.0 (olumlu)
    arousal: float = 0.0                # Arousal: -1.0 (sakin) to 1.0 (uyarılmış)
    dominance: float = 0.0              # Dominance: -1.0 (kontrolsüz) to 1.0 (kontrollü)
    primary_emotion: Optional[str] = None
    secondary_emotions: List[str] = field(default_factory=list)
    confidence: float = 0.5

    def __post_init__(self):
        """Validate PAD ranges."""
        for name, value in [("valence", self.valence),
                           ("arousal", self.arousal),
                           ("dominance", self.dominance)]:
            if not -1.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between -1.0 and 1.0, got {value}")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class SituationModel:
    """
    Durum Modeli - Perception + Memory + Cognition çıktısı.

    SituationModel, mevcut konuşma durumunun kapsamlı bir temsilidir.
    Executive modülü bu modeli kullanarak MessagePlan oluşturur.

    Attributes:
        id: Benzersiz model ID'si
        actors: Konuşmadaki aktörler
        intentions: Tespit edilen niyetler
        risks: Tespit edilen riskler
        relationships: Aktörler arası ilişkiler
        temporal_context: Zaman bağlamı
        emotional_state: Duygusal durum
        topic_domain: Konu alanı
        understanding_score: Anlama skoru (0.0-1.0)
        key_entities: Önemli varlıklar
        context: Ek bağlam
        created_at: Oluşturulma zamanı
    """
    id: str
    actors: List[Actor] = field(default_factory=list)
    intentions: List[Intention] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    temporal_context: Optional[TemporalContext] = None
    emotional_state: Optional[EmotionalState] = None
    topic_domain: str = "general"
    understanding_score: float = 0.5
    key_entities: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate understanding_score range."""
        if not 0.0 <= self.understanding_score <= 1.0:
            raise ValueError(
                f"understanding_score must be between 0.0 and 1.0, got {self.understanding_score}"
            )

    def get_primary_actor(self, role: str = "user") -> Optional[Actor]:
        """Belirtilen roldeki aktörü getir."""
        for actor in self.actors:
            if actor.role == role:
                return actor
        return None

    def get_highest_risk(self) -> Optional[Risk]:
        """En yüksek riskli öğeyi getir."""
        if not self.risks:
            return None
        return max(self.risks, key=lambda r: r.level)

    def has_high_risk(self, threshold: float = 0.7) -> bool:
        """Yüksek risk var mı?"""
        return any(r.level >= threshold for r in self.risks)


@dataclass
class MessagePlan:
    """
    Mesaj Planı - Executive karar çıktısı.

    MessagePlan, SituationModel'e dayanarak oluşturulan
    yanıt stratejisini temsil eder. Construction modülü
    bu planı kullanarak gerçek metni üretir.

    Attributes:
        id: Benzersiz plan ID'si
        dialogue_acts: Sıralı konuşma eylemleri
        primary_intent: Ana niyet açıklaması
        tone: Mesaj tonu
        content_points: İçerik noktaları (ne söylenecek)
        constraints: Kısıtlar (etik, üslup)
        risk_level: Risk seviyesi (0.0-1.0)
        confidence: Plan güveni (0.0-1.0)
        situation_id: Kaynak SituationModel ID'si
        context: Ek bağlam
        created_at: Oluşturulma zamanı
    """
    id: str
    dialogue_acts: List[DialogueAct]
    primary_intent: str
    tone: ToneType = ToneType.NEUTRAL
    content_points: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    risk_level: float = 0.0
    confidence: float = 0.5
    situation_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate ranges."""
        if not 0.0 <= self.risk_level <= 1.0:
            raise ValueError(f"risk_level must be between 0.0 and 1.0, got {self.risk_level}")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

        if not self.dialogue_acts:
            raise ValueError("dialogue_acts cannot be empty")

    @property
    def primary_act(self) -> DialogueAct:
        """Ana konuşma eylemi."""
        return self.dialogue_acts[0]

    def has_emotional_act(self) -> bool:
        """Duygusal eylem içeriyor mu?"""
        emotional_acts = {DialogueAct.EMPATHIZE, DialogueAct.ENCOURAGE, DialogueAct.COMFORT}
        return any(act in emotional_acts for act in self.dialogue_acts)

    def has_boundary_act(self) -> bool:
        """Sınır eylemi içeriyor mu?"""
        boundary_acts = {DialogueAct.REFUSE, DialogueAct.LIMIT, DialogueAct.DEFLECT}
        return any(act in boundary_acts for act in self.dialogue_acts)

    def has_warning_act(self) -> bool:
        """Uyarı eylemi içeriyor mu?"""
        return DialogueAct.WARN in self.dialogue_acts


def generate_situation_id() -> str:
    """Generate unique situation model ID."""
    return f"sit_{uuid.uuid4().hex[:12]}"


def generate_message_plan_id() -> str:
    """Generate unique message plan ID."""
    return f"plan_{uuid.uuid4().hex[:12]}"
