"""
UEM v2 - Consciousness Types

Bilinc modulunun temel veri yapilari.
Global Workspace Theory (Baars) temelli.

Bilinc = Tum modullerden gelen bilgilerin entegre edildigi "sahne"
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class ConsciousnessLevel(str, Enum):
    """Bilinc seviyeleri."""
    UNCONSCIOUS = "unconscious"       # Bilincli degil, otomatik islemler
    PRECONSCIOUS = "preconscious"     # Potansiyel olarak erisilebilir
    SUBCONSCIOUS = "subconscious"     # Bilinc esiginin altinda
    CONSCIOUS = "conscious"           # Tam farkindalik
    HYPERCONSCIOUS = "hyperconscious" # Yukseltilmis farkindalik (akis durumu)


class AwarenessType(str, Enum):
    """Farkindalik turleri."""
    SENSORY = "sensory"               # Duyusal farkindalik
    COGNITIVE = "cognitive"           # Bilissel farkindalik
    EMOTIONAL = "emotional"           # Duygusal farkindalik
    SOCIAL = "social"                 # Sosyal farkindalik
    SELF = "self"                     # Oz-farkindalik
    META = "meta"                     # Meta-farkindalik (farkindaligin farkinda)


class AttentionMode(str, Enum):
    """Dikkat modlari."""
    FOCUSED = "focused"               # Odaklanmis (dar, derin)
    DIFFUSE = "diffuse"               # Dagilmis (genis, yuzeysel)
    DIVIDED = "divided"               # Bolusmis (coklu odak)
    AUTOMATIC = "automatic"           # Otomatik (dikkat gerektirmiyor)
    SUSTAINED = "sustained"           # Surdurulen dikkat


class AttentionPriority(str, Enum):
    """Dikkat onceligi."""
    CRITICAL = "critical"             # Kritik (tehdit, acil)
    HIGH = "high"                     # Yuksek (onemli)
    NORMAL = "normal"                 # Normal
    LOW = "low"                       # Dusuk
    BACKGROUND = "background"         # Arka plan


class BroadcastType(str, Enum):
    """Yayin turu (Global Workspace)."""
    PERCEPTION = "perception"         # Algi bilgisi
    COGNITION = "cognition"           # Bilissel sonuc
    AFFECT = "affect"                 # Duygusal durum
    MEMORY = "memory"                 # Bellek bilgisi
    DECISION = "decision"             # Karar
    ACTION = "action"                 # Eylem niyeti
    ALERT = "alert"                   # Uyari/alarm


class IntegrationStatus(str, Enum):
    """Entegrasyon durumu."""
    PENDING = "pending"               # Bekliyor
    PROCESSING = "processing"         # Isleniyor
    INTEGRATED = "integrated"         # Entegre edildi
    BROADCAST = "broadcast"           # Yayinlandi
    EXPIRED = "expired"               # Suresi doldu


# ============================================================================
# ATTENTION FOCUS
# ============================================================================

@dataclass
class AttentionFocus:
    """
    Dikkat odagi.

    AttentionFocus = Bilincin su anda neye odaklandigl
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Hedef
    target_type: str = ""             # Ne turu hedef (entity, stimulus, thought)
    target_id: Optional[str] = None   # Hedef ID
    target_description: str = ""      # Hedef aciklamasi

    # Dikkat parametreleri
    mode: AttentionMode = AttentionMode.FOCUSED
    priority: AttentionPriority = AttentionPriority.NORMAL
    intensity: float = 0.5            # Dikkat yogunlugu (0-1)
    stability: float = 0.5            # Dikkat kararliligi (0-1)

    # Kaynak
    source_module: str = ""           # Hangi modulden geldi
    trigger_reason: str = ""          # Neden dikkat cekti

    # Zaman
    started_at: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0          # Ne kadar suredir odakta
    expected_duration_ms: float = 5000.0  # Beklenen sure

    # Meta
    switch_count: int = 0             # Kac kez degisti

    @property
    def is_expired(self) -> bool:
        """Dikkat suresi doldu mu?"""
        elapsed = (datetime.now() - self.started_at).total_seconds() * 1000
        return elapsed > self.expected_duration_ms

    @property
    def priority_score(self) -> float:
        """Oncelik skoru."""
        priority_weights = {
            AttentionPriority.CRITICAL: 1.0,
            AttentionPriority.HIGH: 0.8,
            AttentionPriority.NORMAL: 0.5,
            AttentionPriority.LOW: 0.3,
            AttentionPriority.BACKGROUND: 0.1,
        }
        weight = priority_weights.get(self.priority, 0.5)
        return weight * self.intensity * self.stability


# ============================================================================
# QUALIA (Oznel Deneyim)
# ============================================================================

@dataclass
class Qualia:
    """
    Oznel deneyim temsili.

    Qualia = "Nasil hissettigi" - bilincin oznel, niteliksel yonu
    Ornek: Kirmizi rengin "kirmiziligi", acinon "aciligi"
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Deneyim
    modality: str = ""                # Hangi modalite (visual, auditory, emotional)
    quality: str = ""                 # Nitelik aciklamasi
    content: Dict[str, Any] = field(default_factory=dict)

    # Yogunluk
    intensity: float = 0.5            # Deneyim yogunlugu (0-1)
    valence: float = 0.0              # Hos/nahos (-1 to +1)
    salience: float = 0.5             # Dikkat cekicilik (0-1)

    # Iliskiler
    source_stimulus: Optional[str] = None  # Kaynak uyaran
    associated_emotion: Optional[str] = None  # Iliskili duygu

    # Zaman
    onset_time: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0

    @property
    def phenomenal_strength(self) -> float:
        """Fenomenal guc = intensity * salience."""
        return self.intensity * self.salience


# ============================================================================
# WORKSPACE CONTENT (Calisma Alani Icerigi)
# ============================================================================

@dataclass
class WorkspaceContent:
    """
    Global Workspace icerigi.

    WorkspaceContent = Bilince giren bir bilgi parcasi
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Icerik
    content_type: BroadcastType = BroadcastType.PERCEPTION
    source_module: str = ""           # Kaynak modul (perception, cognition, etc.)
    payload: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""                 # Kisa ozet

    # Oncelik ve onemi
    priority: AttentionPriority = AttentionPriority.NORMAL
    relevance: float = 0.5            # Alakalilik (0-1)
    urgency: float = 0.3              # Aciliyet (0-1)
    novelty: float = 0.5              # Yenilik (0-1)

    # Durum
    status: IntegrationStatus = IntegrationStatus.PENDING
    integration_score: float = 0.0    # Entegrasyon kalitesi

    # Zaman
    created_at: datetime = field(default_factory=datetime.now)
    integrated_at: Optional[datetime] = None
    broadcast_at: Optional[datetime] = None
    ttl_ms: float = 10000.0           # Yasam suresi (ms)

    # Iliskiler
    related_contents: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)

    @property
    def competition_score(self) -> float:
        """Yarisma skoru - workspace'e girme onceligi."""
        priority_weights = {
            AttentionPriority.CRITICAL: 2.0,
            AttentionPriority.HIGH: 1.5,
            AttentionPriority.NORMAL: 1.0,
            AttentionPriority.LOW: 0.5,
            AttentionPriority.BACKGROUND: 0.2,
        }
        weight = priority_weights.get(self.priority, 1.0)
        return (self.relevance + self.urgency + self.novelty) / 3 * weight

    @property
    def is_expired(self) -> bool:
        """Icerik suresi doldu mu?"""
        elapsed = (datetime.now() - self.created_at).total_seconds() * 1000
        return elapsed > self.ttl_ms

    def mark_integrated(self, score: float = 1.0) -> None:
        """Entegre olarak isaretle."""
        self.status = IntegrationStatus.INTEGRATED
        self.integration_score = score
        self.integrated_at = datetime.now()

    def mark_broadcast(self) -> None:
        """Yayinlandi olarak isaretle."""
        self.status = IntegrationStatus.BROADCAST
        self.broadcast_at = datetime.now()


# ============================================================================
# AWARENESS STATE
# ============================================================================

@dataclass
class AwarenessState:
    """
    Farkindalik durumu.

    AwarenessState = Belirli bir alana ait farkindalik seviyesi
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Farkindalik
    awareness_type: AwarenessType = AwarenessType.COGNITIVE
    level: float = 0.5                # Farkindalik seviyesi (0-1)
    clarity: float = 0.5              # Berraklik (0-1)
    depth: float = 0.5                # Derinlik (0-1)

    # Icerik
    current_focus: Optional[str] = None  # Su anda ne hakkinda farkinda
    background_items: List[str] = field(default_factory=list)  # Arka planda

    # Zaman
    last_update: datetime = field(default_factory=datetime.now)

    @property
    def quality(self) -> float:
        """Farkindalik kalitesi = level * clarity * depth."""
        return self.level * self.clarity * self.depth


# ============================================================================
# GLOBAL WORKSPACE STATE
# ============================================================================

@dataclass
class GlobalWorkspaceState:
    """
    Global Workspace durumu.

    GlobalWorkspaceState = Bilincin "sahnesi" - entegre bilgi
    """
    # Workspace icerikleri
    active_contents: Dict[str, WorkspaceContent] = field(default_factory=dict)
    broadcast_queue: List[str] = field(default_factory=list)  # Yayinlanacaklar
    broadcast_history: List[str] = field(default_factory=list)  # Son yayinlar

    # Dikkat
    current_focus: Optional[AttentionFocus] = None
    attention_history: List[str] = field(default_factory=list)

    # Farkindalik durumu
    awareness_states: Dict[AwarenessType, AwarenessState] = field(default_factory=dict)

    # Bilinc seviyesi
    consciousness_level: ConsciousnessLevel = ConsciousnessLevel.CONSCIOUS
    overall_awareness: float = 0.5    # Genel farkindalik (0-1)
    coherence: float = 0.5            # Tutarlilik (0-1)

    # Entegrasyon metrikleri
    integration_count: int = 0
    broadcast_count: int = 0
    conflict_count: int = 0

    # Zaman
    last_broadcast: Optional[datetime] = None
    cycle_id: int = 0

    # ========================================================================
    # CONTENT OPERATIONS
    # ========================================================================

    def add_content(self, content: WorkspaceContent) -> None:
        """Workspace'e icerik ekle."""
        self.active_contents[content.id] = content

    def remove_content(self, content_id: str) -> Optional[WorkspaceContent]:
        """Icerigi kaldir."""
        return self.active_contents.pop(content_id, None)

    def get_content(self, content_id: str) -> Optional[WorkspaceContent]:
        """Icerigi getir."""
        return self.active_contents.get(content_id)

    def get_contents_by_type(self, content_type: BroadcastType) -> List[WorkspaceContent]:
        """Ture gore icerikleri getir."""
        return [c for c in self.active_contents.values() if c.content_type == content_type]

    def get_top_contents(self, n: int = 5) -> List[WorkspaceContent]:
        """En yuksek skorlu icerikleri getir."""
        sorted_contents = sorted(
            self.active_contents.values(),
            key=lambda c: c.competition_score,
            reverse=True,
        )
        return sorted_contents[:n]

    def cleanup_expired(self) -> int:
        """Suresi dolmus icerikleri temizle."""
        expired = [cid for cid, c in self.active_contents.items() if c.is_expired]
        for cid in expired:
            del self.active_contents[cid]
        return len(expired)

    # ========================================================================
    # AWARENESS OPERATIONS
    # ========================================================================

    def get_awareness(self, awareness_type: AwarenessType) -> Optional[AwarenessState]:
        """Farkindalik durumunu getir."""
        return self.awareness_states.get(awareness_type)

    def set_awareness(self, state: AwarenessState) -> None:
        """Farkindalik durumunu ayarla."""
        self.awareness_states[state.awareness_type] = state

    def get_overall_awareness(self) -> float:
        """Genel farkindalik seviyesini hesapla."""
        if not self.awareness_states:
            return 0.5
        total = sum(s.level for s in self.awareness_states.values())
        return total / len(self.awareness_states)

    # ========================================================================
    # SUMMARY
    # ========================================================================

    def summary(self) -> Dict[str, Any]:
        """Workspace ozeti."""
        return {
            "consciousness_level": self.consciousness_level.value,
            "overall_awareness": self.overall_awareness,
            "coherence": self.coherence,
            "active_contents": len(self.active_contents),
            "broadcast_queue": len(self.broadcast_queue),
            "current_focus": self.current_focus.target_description if self.current_focus else None,
            "awareness_types": list(self.awareness_states.keys()),
            "integration_count": self.integration_count,
            "broadcast_count": self.broadcast_count,
            "cycle_id": self.cycle_id,
        }


# ============================================================================
# CONSCIOUS EXPERIENCE
# ============================================================================

@dataclass
class ConsciousExperience:
    """
    Butunlesik bilinc deneyimi.

    ConsciousExperience = Belirli bir andaki tum bilinc durumu
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Bilinc durumu
    level: ConsciousnessLevel = ConsciousnessLevel.CONSCIOUS
    clarity: float = 0.5              # Genel berraklik
    unity: float = 0.5                # Birlestiricilik (unified experience)

    # Icerik
    phenomenal_contents: List[Qualia] = field(default_factory=list)
    cognitive_contents: List[str] = field(default_factory=list)  # Dusunceler
    emotional_tone: Dict[str, float] = field(default_factory=dict)  # Duygusal ton

    # Dikkat
    attention_focus: Optional[AttentionFocus] = None
    peripheral_awareness: List[str] = field(default_factory=list)

    # Self-awareness
    self_awareness_level: float = 0.5
    meta_awareness_level: float = 0.3  # Farkindaligin farkindasi

    # Zaman
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0

    # Meta
    cycle_id: int = 0

    @property
    def richness(self) -> float:
        """Deneyim zenginligi."""
        content_count = len(self.phenomenal_contents) + len(self.cognitive_contents)
        normalized = min(1.0, content_count / 10.0)
        return normalized * self.clarity * self.unity

    def add_qualia(self, qualia: Qualia) -> None:
        """Oznel deneyim ekle."""
        self.phenomenal_contents.append(qualia)

    def summary(self) -> Dict[str, Any]:
        """Deneyim ozeti."""
        return {
            "level": self.level.value,
            "clarity": self.clarity,
            "unity": self.unity,
            "richness": self.richness,
            "phenomenal_count": len(self.phenomenal_contents),
            "cognitive_count": len(self.cognitive_contents),
            "self_awareness": self.self_awareness_level,
            "meta_awareness": self.meta_awareness_level,
            "focus": self.attention_focus.target_description if self.attention_focus else None,
        }
