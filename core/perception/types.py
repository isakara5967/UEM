"""
core/perception/types.py

Perception modulu icin tum veri tipleri.
UEM v2 - Algi sistemi.

Icerik:
- SensoryModality: Duyusal modalite turleri
- PerceptualInput: Ham algi girdisi
- SensoryData: Modality-spesifik duyusal veri
- VisualFeatures: Gorsel ozellikler
- AuditoryFeatures: Isitsel ozellikler
- MotionFeatures: Hareket ozellikleri
- PerceivedAgent: Algilanan ajan bilgisi
- ThreatAssessment: Tehdit degerlendirmesi
- PerceptualFeatures: Cikarilmis ozellikler
- PerceptualOutput: Algi ciktisi
- AttentionFocus: Dikkat odagi
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import uuid


# ========================================================================
# ENUMS
# ========================================================================

class SensoryModality(str, Enum):
    """Duyusal modalite turleri."""
    VISUAL = "visual"           # Gorsel
    AUDITORY = "auditory"       # Isitsel
    TACTILE = "tactile"         # Dokunsal
    PROPRIOCEPTIVE = "proprioceptive"  # Vucud pozisyonu
    INTEROCEPTIVE = "interoceptive"    # Ic beden durumu
    SOCIAL = "social"           # Sosyal ipuclari


class PerceptualCategory(str, Enum):
    """Algilanan nesne kategorileri."""
    AGENT = "agent"             # Canli ajan
    OBJECT = "object"           # Nesne
    LOCATION = "location"       # Konum
    EVENT = "event"             # Olay
    ABSTRACT = "abstract"       # Soyut kavram


class ThreatLevel(str, Enum):
    """Tehdit seviyesi."""
    NONE = "none"               # Tehdit yok
    LOW = "low"                 # Dusuk tehdit
    MODERATE = "moderate"       # Orta tehdit
    HIGH = "high"               # Yuksek tehdit
    CRITICAL = "critical"       # Kritik tehdit


class AgentDisposition(str, Enum):
    """Ajan tavir/tutumu."""
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    UNFRIENDLY = "unfriendly"
    HOSTILE = "hostile"
    UNKNOWN = "unknown"


class EmotionalExpression(str, Enum):
    """Yuz ifadesi / duygusal gosterge."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    CONTEMPTUOUS = "contemptuous"
    THREATENING = "threatening"


class BodyLanguage(str, Enum):
    """Vucut dili."""
    OPEN = "open"               # Acik, davetkar
    CLOSED = "closed"           # Kapali, savunmaci
    AGGRESSIVE = "aggressive"   # Saldirgan
    SUBMISSIVE = "submissive"   # Boyun egen
    RELAXED = "relaxed"         # Rahat
    TENSE = "tense"             # Gergin
    NEUTRAL = "neutral"


# ========================================================================
# SENSORY DATA TYPES
# ========================================================================

@dataclass
class VisualFeatures:
    """Gorsel ozellikler."""

    # Temel ozellikler
    brightness: float = 0.5         # 0-1 parlaklik
    contrast: float = 0.5           # 0-1 kontrast
    color_dominant: Optional[str] = None  # Ana renk

    # Hareket
    motion_detected: bool = False
    motion_direction: Optional[str] = None  # "approaching", "retreating", "lateral"
    motion_speed: float = 0.0       # 0-1 hiz

    # Uzamsal
    distance_estimate: float = 1.0  # Metre cinsinden tahmini mesafe
    size_estimate: float = 1.0      # Goreceli boyut (1.0 = ortalama)
    position: Optional[Tuple[float, float]] = None  # (x, y) koordinat

    # Yuz/ajan ozellikleri
    face_detected: bool = False
    expression: Optional[EmotionalExpression] = None
    gaze_direction: Optional[str] = None  # "direct", "averted", "scanning"

    # Ekstra
    salient_features: List[str] = field(default_factory=list)


@dataclass
class AuditoryFeatures:
    """Isitsel ozellikler."""

    # Temel ses ozellikleri
    volume: float = 0.5             # 0-1 ses yuksekligi
    pitch: float = 0.5              # 0-1 perde (0=bas, 1=tiz)
    tempo: float = 0.5              # 0-1 hiz

    # Ses turu
    sound_type: str = "ambient"     # "speech", "music", "noise", "ambient", "alert"

    # Konusma ozellikleri (eger speech ise)
    speech_detected: bool = False
    speech_tone: Optional[str] = None  # "calm", "excited", "angry", "fearful"
    speech_content: Optional[str] = None  # Transkript

    # Mekansal
    direction: Optional[str] = None  # "front", "left", "right", "behind"
    distance_estimate: float = 1.0  # Metre cinsinden

    # Alarm/uyari sesleri
    is_alarm: bool = False
    urgency_level: float = 0.0      # 0-1


@dataclass
class MotionFeatures:
    """Hareket ozellikleri (proprioceptive + visual motion)."""

    # Kendi hareketi
    self_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # (x, y, z)
    self_acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Gozlemlenen hareket
    observed_motion: bool = False
    motion_pattern: str = "stationary"  # "stationary", "walking", "running", "erratic"

    # Tehdit hareketi
    approach_detected: bool = False
    approach_speed: float = 0.0
    time_to_contact: Optional[float] = None  # Saniye


@dataclass
class SensoryData:
    """Birlesik duyusal veri."""

    modality: SensoryModality
    timestamp: datetime = field(default_factory=datetime.now)

    # Modalite-spesifik veriler
    visual: Optional[VisualFeatures] = None
    auditory: Optional[AuditoryFeatures] = None
    motion: Optional[MotionFeatures] = None

    # Ham veri (opsiyonel)
    raw_data: Optional[Dict[str, Any]] = None

    # Kalite ve guvenilirlik
    confidence: float = 1.0         # 0-1 guvenilirlik
    noise_level: float = 0.0        # 0-1 gurultu seviyesi


# ========================================================================
# PERCEPTUAL INPUT
# ========================================================================

@dataclass
class PerceptualInput:
    """
    Ham algi girdisi - SENSE fazina giren veri.

    Stimulus'tan daha zengin, coklu modalite destekli.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    # Duyusal veriler (birden fazla modalite olabilir)
    sensory_data: List[SensoryData] = field(default_factory=list)

    # Kaynak bilgisi
    source_type: str = "external"   # "external", "internal", "memory"
    source_id: Optional[str] = None

    # Oncelik ve aciliyet
    intensity: float = 0.5          # 0-1 yogunluk
    urgency: float = 0.0            # 0-1 aciliyet

    # Ham stimulus (uyumluluk icin)
    raw_stimulus: Optional[Dict[str, Any]] = None

    def get_modality(self, modality: SensoryModality) -> Optional[SensoryData]:
        """Belirli bir modaliteyi getir."""
        for data in self.sensory_data:
            if data.modality == modality:
                return data
        return None

    def has_modality(self, modality: SensoryModality) -> bool:
        """Modalite var mi kontrol et."""
        return self.get_modality(modality) is not None


# ========================================================================
# PERCEIVED AGENT
# ========================================================================

@dataclass
class PerceivedAgent:
    """
    Algilanan ajan - baska bir UEM veya canli varlik.

    Bu struct hem perception ciktisi hem de memory'ye kayit icin kullanilir.
    """

    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Temel ozellikler
    name: Optional[str] = None
    agent_type: str = "unknown"     # "human", "animal", "robot", "uem", "unknown"

    # Fiziksel algi
    position: Optional[Tuple[float, float]] = None
    distance: float = 1.0
    size: float = 1.0               # Goreceli boyut

    # Duygusal/sosyal ipuclari
    expression: EmotionalExpression = EmotionalExpression.NEUTRAL
    body_language: BodyLanguage = BodyLanguage.NEUTRAL
    disposition: AgentDisposition = AgentDisposition.UNKNOWN

    # PAD tahmini (ajanin durumu)
    estimated_valence: float = 0.0      # -1 to 1
    estimated_arousal: float = 0.5      # 0 to 1
    estimated_dominance: float = 0.5    # 0 to 1

    # Hareket
    is_moving: bool = False
    movement_direction: Optional[str] = None
    approaching: bool = False

    # Ses/konusma
    speaking: bool = False
    voice_tone: Optional[str] = None
    verbal_content: Optional[str] = None

    # Iliski bilgisi (memory'den gelir)
    known: bool = False
    relationship_type: Optional[str] = None
    trust_level: Optional[float] = None

    # Tehdit degerlendirmesi
    threat_level: ThreatLevel = ThreatLevel.NONE
    threat_score: float = 0.0       # 0-1

    # Guvenilirlik
    perception_confidence: float = 1.0


# ========================================================================
# THREAT ASSESSMENT
# ========================================================================

@dataclass
class ThreatAssessment:
    """
    Tehdit degerlendirmesi - perception'in kritik ciktisi.

    Fight-or-flight tepkisini tetikler.
    """

    timestamp: datetime = field(default_factory=datetime.now)

    # Genel tehdit
    overall_level: ThreatLevel = ThreatLevel.NONE
    overall_score: float = 0.0      # 0-1

    # Tehdit kaynaklari
    threat_sources: List[str] = field(default_factory=list)  # agent_id'ler
    primary_threat_id: Optional[str] = None

    # Tehdit turleri ve skorlari
    physical_threat: float = 0.0    # Fiziksel tehdit
    social_threat: float = 0.0      # Sosyal tehdit (rejection, humiliation)
    resource_threat: float = 0.0    # Kaynak tehdidi

    # Tehdit ipuclari
    indicators: List[str] = field(default_factory=list)

    # Onerilen tepki
    suggested_response: str = "observe"  # "observe", "approach", "avoid", "flee", "confront"
    urgency: float = 0.0            # 0-1 acil mudahale gereksinimi

    # Guvenilirlik
    confidence: float = 1.0

    def is_threatening(self) -> bool:
        """Tehdit var mi?"""
        return self.overall_level not in [ThreatLevel.NONE, ThreatLevel.LOW]

    def requires_immediate_action(self) -> bool:
        """Acil aksiyon gerekli mi?"""
        return self.overall_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]


# ========================================================================
# ATTENTION FOCUS
# ========================================================================

@dataclass
class AttentionFocus:
    """Dikkat odagi - neye odaklaniliyor."""

    timestamp: datetime = field(default_factory=datetime.now)

    # Odak hedefi
    target_type: str = "none"       # "agent", "object", "location", "event", "internal", "none"
    target_id: Optional[str] = None
    target_position: Optional[Tuple[float, float]] = None

    # Dikkat seviyesi
    attention_level: float = 0.5    # 0-1
    focus_duration: float = 0.0     # Saniye

    # Dikkat turu
    attention_type: str = "voluntary"  # "voluntary", "reflexive", "sustained"

    # Dikkat nedeni
    reason: str = "default"         # "threat", "novelty", "task", "social", "default"

    # Cevresel farkindalik
    peripheral_awareness: float = 0.5  # 0-1


# ========================================================================
# PERCEPTUAL FEATURES (Cikarilmis ozellikler)
# ========================================================================

@dataclass
class PerceptualFeatures:
    """
    Cikarilmis ozellikler - PERCEIVE fazinin ana ciktisi.

    Ham veriden anlam cikarilmis hali.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    # Algilanan ajanlar
    agents: List[PerceivedAgent] = field(default_factory=list)

    # Algilanan nesneler
    objects: List[Dict[str, Any]] = field(default_factory=list)

    # Sahne/ortam bilgisi
    scene_type: str = "unknown"     # "indoor", "outdoor", "social", "isolated"
    scene_familiarity: float = 0.5  # 0-1
    ambient_threat: float = 0.0     # 0-1

    # Dikkat
    attention: AttentionFocus = field(default_factory=AttentionFocus)

    # Tehdit degerlendirmesi
    threat: ThreatAssessment = field(default_factory=ThreatAssessment)

    # Onem/belirginlik
    salience_score: float = 0.5     # 0-1 ne kadar dikkat cekici
    novelty_score: float = 0.0      # 0-1 ne kadar yeni/beklenmedik

    # Belirsizlik
    ambiguity: float = 0.0          # 0-1 belirsizlik seviyesi

    # Kaynak girdiler
    source_input_ids: List[str] = field(default_factory=list)

    def get_primary_agent(self) -> Optional[PerceivedAgent]:
        """Ana/birincil algilanan ajani getir."""
        if not self.agents:
            return None
        # En yakin veya en belirgin
        return sorted(self.agents, key=lambda a: a.distance)[0]

    def get_threatening_agents(self) -> List[PerceivedAgent]:
        """Tehditkar ajanlari getir."""
        return [a for a in self.agents if a.threat_level != ThreatLevel.NONE]


# ========================================================================
# PERCEPTUAL OUTPUT
# ========================================================================

@dataclass
class PerceptualOutput:
    """
    Perception modulunun tam ciktisi.

    Bu cikti diger modullere (Memory, Affect, Cognition) iletilir.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    cycle_id: Optional[int] = None

    # Ana sonuclar
    features: PerceptualFeatures = field(default_factory=PerceptualFeatures)

    # Islem bilgisi
    processing_time_ms: float = 0.0
    input_count: int = 0

    # Durum
    success: bool = True
    error: Optional[str] = None

    # Ozetler (diger moduller icin)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Dict'e cevir."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "cycle_id": self.cycle_id,
            "agents_detected": len(self.features.agents),
            "threat_level": self.features.threat.overall_level.value,
            "attention_target": self.features.attention.target_type,
            "success": self.success,
        }
