"""
core/memory/types.py

Memory modulu icin tum veri tipleri.
UEM v2 - Norobiliml bazli bellek sistemi.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import uuid


# ========================================================================
# ENUMS
# ========================================================================

class MemoryType(str, Enum):
    """Bellek turu."""
    SENSORY = "sensory"
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    EMOTIONAL = "emotional"
    RELATIONSHIP = "relationship"
    CONVERSATION = "conversation"


class EmotionalValence(str, Enum):
    """Duygusal degerlik."""
    VERY_NEGATIVE = "very_negative"  # -1.0 to -0.6
    NEGATIVE = "negative"            # -0.6 to -0.2
    NEUTRAL = "neutral"              # -0.2 to 0.2
    POSITIVE = "positive"            # 0.2 to 0.6
    VERY_POSITIVE = "very_positive"  # 0.6 to 1.0


class RelationshipType(str, Enum):
    """Iliski turu."""
    UNKNOWN = "unknown"
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    COLLEAGUE = "colleague"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    FAMILY = "family"
    RIVAL = "rival"
    ENEMY = "enemy"
    NEUTRAL = "neutral"


class InteractionType(str, Enum):
    """Etkilesim turu."""
    # Pozitif
    HELPED = "helped"
    COOPERATED = "cooperated"
    SHARED = "shared"
    PROTECTED = "protected"
    CELEBRATED = "celebrated"
    COMFORTED = "comforted"

    # Notr
    OBSERVED = "observed"
    CONVERSED = "conversed"
    TRADED = "traded"

    # Negatif
    COMPETED = "competed"
    CONFLICTED = "conflicted"
    HARMED = "harmed"
    BETRAYED = "betrayed"
    THREATENED = "threatened"
    ATTACKED = "attacked"


class EpisodeType(str, Enum):
    """Olay turu."""
    ENCOUNTER = "encounter"          # Karsilasma
    INTERACTION = "interaction"      # Etkilesim
    OBSERVATION = "observation"      # Gozlem
    CONFLICT = "conflict"            # Catisma
    COOPERATION = "cooperation"      # Isbirligi
    EMOTIONAL_EVENT = "emotional"    # Duygusal olay
    SIGNIFICANT = "significant"      # Onemli olay


# ========================================================================
# BASE MEMORY ITEM
# ========================================================================

@dataclass
class MemoryItem:
    """Tum memory ogelerinin base class'i."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.WORKING

    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    # Decay parametreleri
    strength: float = 1.0           # 0-1, zamanla azalir
    importance: float = 0.5         # 0-1, decay'i etkiler

    # Duygusal etiket
    emotional_valence: float = 0.0  # -1 to 1
    emotional_arousal: float = 0.0  # 0 to 1

    # Meta
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        """Erisim kaydi - strength artir."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        # Her erisimde strength biraz artar (max 1.0)
        self.strength = min(1.0, self.strength + 0.05)

    def decay(self, rate: float = 0.01) -> None:
        """Zaman gectikce strength azalt."""
        # Importance yuksekse decay yavas
        effective_rate = rate * (1.0 - self.importance * 0.5)
        self.strength = max(0.0, self.strength - effective_rate)

    def is_forgotten(self, threshold: float = 0.1) -> bool:
        """Unutuldu mu?"""
        return self.strength < threshold


# ========================================================================
# SENSORY MEMORY
# ========================================================================

@dataclass
class SensoryTrace(MemoryItem):
    """
    Duyusal iz - cok kisa sureli (ms-saniye).
    Raw sensory input'un gecici kaydi.
    """
    memory_type: MemoryType = MemoryType.SENSORY

    modality: str = "visual"         # visual, auditory, tactile
    raw_data: Any = None             # Ham veri
    duration_ms: float = 500.0       # Varsayilan yasam suresi

    # Attention tarafindan secildi mi?
    attended: bool = False


# ========================================================================
# WORKING MEMORY
# ========================================================================

@dataclass
class WorkingMemoryItem(MemoryItem):
    """
    Calisma bellegi ogesi - aktif islem icin (7+-2 limit).
    """
    memory_type: MemoryType = MemoryType.WORKING

    content: Any = None              # Icerik (herhangi bir tip)
    source: str = ""                 # Nereden geldi (perception, retrieval, etc.)
    priority: float = 0.5            # 0-1, yuksek = daha onemli

    # Binding - diger WM items ile baglanti
    bindings: List[str] = field(default_factory=list)  # Diger item ID'leri


# ========================================================================
# EPISODIC MEMORY
# ========================================================================

@dataclass
class Episode(MemoryItem):
    """
    Olay kaydi - ne, nerede, ne zaman, kim.
    Autobiographical memory.
    """
    memory_type: MemoryType = MemoryType.EPISODIC

    # 5W1H
    what: str = ""                   # Ne oldu?
    where: str = ""                  # Nerede?
    when: datetime = field(default_factory=datetime.now)
    who: List[str] = field(default_factory=list)  # Kim vardi? (agent_id'ler)
    why: Optional[str] = None        # Neden? (cikarsanmis)
    how: Optional[str] = None        # Nasil?

    # Olay detaylari
    episode_type: EpisodeType = EpisodeType.ENCOUNTER
    duration_seconds: float = 0.0

    # Sonuc
    outcome: str = ""                # Olayin sonucu
    outcome_valence: float = 0.0     # Sonuc iyi mi kotu mu? (-1 to 1)

    # Iliskili ajanlar ve rolleri
    agent_roles: Dict[str, str] = field(default_factory=dict)  # {agent_id: role}

    # Duygusal iz (affect modulunden)
    self_emotion_during: Optional[str] = None     # Ben ne hissettim?
    self_emotion_after: Optional[str] = None      # Sonra ne hissettim?
    other_emotions: Dict[str, str] = field(default_factory=dict)  # Digerleri

    # PAD state
    pad_state: Optional[Dict[str, float]] = None  # {pleasure, arousal, dominance}


@dataclass
class EpisodeSummary:
    """Episode ozeti - hizli erisim icin."""
    episode_id: str
    episode_type: EpisodeType
    when: datetime
    who: List[str]
    outcome_valence: float
    emotional_valence: float
    importance: float


# ========================================================================
# SEMANTIC MEMORY
# ========================================================================

@dataclass
class SemanticFact(MemoryItem):
    """
    Anlamsal bilgi - genel bilgi, kavramlar.
    Context-free facts.
    """
    memory_type: MemoryType = MemoryType.SEMANTIC

    subject: str = ""                # Ozne
    predicate: str = ""              # Yuklem (iliski)
    object: str = ""                 # Nesne

    # Ornek: ("Alice", "is_a", "friend")
    # Ornek: ("enemy", "implies", "high_threat")

    confidence: float = 1.0          # Ne kadar eminim?
    source: str = ""                 # Nereden ogrendim?

    # Iliskili kavramlar
    related_concepts: List[str] = field(default_factory=list)


@dataclass
class ConceptNode:
    """
    Kavram dugumu - semantic network icin.
    """
    concept_id: str
    name: str
    category: str = ""               # Kategori (agent, object, place, action)

    # Ozellikler
    properties: Dict[str, Any] = field(default_factory=dict)

    # Baglantilar (edges)
    relations: Dict[str, List[str]] = field(default_factory=dict)
    # Ornek: {"is_a": ["person"], "can": ["help", "harm"], "opposite": ["friend"]}

    # Prototip (kategori icin tipik degerler)
    prototype: Dict[str, float] = field(default_factory=dict)


# ========================================================================
# EMOTIONAL MEMORY
# ========================================================================

@dataclass
class EmotionalMemory(MemoryItem):
    """
    Duygusal ani - affect-tagged memory.
    Duygusal olarak yuklu anilar daha guclu hatirlanir.
    """
    memory_type: MemoryType = MemoryType.EMOTIONAL

    # Bagli episode
    episode_id: Optional[str] = None

    # Duygusal icerik
    primary_emotion: str = ""        # Ana duygu (fear, joy, sadness, etc.)
    emotion_intensity: float = 0.5   # 0-1

    # PAD
    pleasure: float = 0.0
    arousal: float = 0.5
    dominance: float = 0.5

    # Tetikleyiciler
    triggers: List[str] = field(default_factory=list)  # Bu aniyi tetikleyen seyler

    # Flashbulb memory mi? (cok canli, detayli)
    is_flashbulb: bool = False

    # Somatic marker (Damasio)
    somatic_marker: Optional[str] = None  # "gut_feeling_negative", "warm_feeling"


# ========================================================================
# RELATIONSHIP MEMORY (Trust icin kritik!)
# ========================================================================

@dataclass
class Interaction:
    """Tek bir etkilesim kaydi."""

    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    interaction_type: InteractionType = InteractionType.OBSERVED
    context: str = ""                # Baglam aciklamasi

    # Sonuc
    outcome: str = ""
    outcome_valence: float = 0.0     # -1 to 1

    # Duygusal etki
    emotional_impact: float = 0.0    # -1 to 1
    trust_impact: float = 0.0        # Trust'a etkisi

    # Iliskili episode
    episode_id: Optional[str] = None


@dataclass
class RelationshipRecord(MemoryItem):
    """
    Iliski kaydi - bir agent ile tum gecmis.
    Trust modulu icin birincil kaynak!
    """
    memory_type: MemoryType = MemoryType.RELATIONSHIP

    agent_id: str = ""               # Karsi tarafin ID'si
    agent_name: str = ""             # Isim (varsa)

    # Iliski durumu
    relationship_type: RelationshipType = RelationshipType.STRANGER
    relationship_start: datetime = field(default_factory=datetime.now)

    # Etkilesim gecmisi
    interactions: List[Interaction] = field(default_factory=list)
    total_interactions: int = 0

    # Istatistikler
    positive_interactions: int = 0
    negative_interactions: int = 0
    neutral_interactions: int = 0

    # Trust ile entegrasyon
    trust_score: float = 0.5         # 0-1, Trust modulunden senkronize
    trust_history: List[float] = field(default_factory=list)  # Trust degisim tarihcesi

    # Betrayal tracking
    betrayal_count: int = 0
    last_betrayal: Optional[datetime] = None

    # Duygusal ozet
    overall_sentiment: float = 0.0   # -1 to 1
    dominant_emotion_with: str = ""  # Bu kisiyle en cok hissettigim duygu

    # Son etkilesim
    last_interaction: Optional[datetime] = None
    last_interaction_type: Optional[InteractionType] = None

    # Notlar
    notes: List[str] = field(default_factory=list)

    def add_interaction(self, interaction: Interaction) -> None:
        """Etkilesim ekle ve istatistikleri guncelle."""
        self.interactions.append(interaction)
        self.total_interactions += 1
        self.last_interaction = interaction.timestamp
        self.last_interaction_type = interaction.interaction_type

        # Trust score güncelle (KRİTİK!)
        if interaction.trust_impact != 0:
            self.trust_score = max(0.0, min(1.0, self.trust_score + interaction.trust_impact))
            self.trust_history.append(self.trust_score)

        # Istatistik guncelle
        if interaction.outcome_valence > 0.2:
            self.positive_interactions += 1
        elif interaction.outcome_valence < -0.2:
            self.negative_interactions += 1
        else:
            self.neutral_interactions += 1

        # Betrayal tracking
        if interaction.interaction_type == InteractionType.BETRAYED:
            self.betrayal_count += 1
            self.last_betrayal = interaction.timestamp

        # Sentiment guncelle
        self._update_sentiment()

    def _update_sentiment(self) -> None:
        """Genel sentiment hesapla."""
        if self.total_interactions == 0:
            self.overall_sentiment = 0.0
            return

        # Agirlikli ortalama (son etkilesimler daha onemli)
        if self.interactions:
            recent = self.interactions[-10:]  # Son 10
            weights = [0.5 + 0.5 * (i / len(recent)) for i in range(len(recent))]
            weighted_sum = sum(
                i.outcome_valence * w for i, w in zip(recent, weights)
            )
            self.overall_sentiment = weighted_sum / sum(weights)

    def get_trust_recommendation(self) -> float:
        """Trust modulu icin onerilen baslangic trust degeri."""
        if self.total_interactions == 0:
            # Hic etkilesim yok - relationship type'a gore
            type_defaults = {
                RelationshipType.UNKNOWN: 0.5,
                RelationshipType.STRANGER: 0.5,
                RelationshipType.ACQUAINTANCE: 0.55,
                RelationshipType.COLLEAGUE: 0.6,
                RelationshipType.FRIEND: 0.7,
                RelationshipType.CLOSE_FRIEND: 0.8,
                RelationshipType.FAMILY: 0.75,
                RelationshipType.RIVAL: 0.3,
                RelationshipType.ENEMY: 0.15,
                RelationshipType.NEUTRAL: 0.5,
            }
            return type_defaults.get(self.relationship_type, 0.5)

        # Etkilesim var - gecmise gore hesapla
        base = 0.5

        # Pozitif/negatif orani
        if self.total_interactions > 0:
            ratio = (self.positive_interactions - self.negative_interactions) / self.total_interactions
            base += ratio * 0.3

        # Betrayal penalty
        if self.betrayal_count > 0:
            base -= self.betrayal_count * 0.15

        return max(0.05, min(0.95, base))


# ========================================================================
# CONSOLIDATION
# ========================================================================

@dataclass
class ConsolidationTask:
    """Bellek pekistirme gorevi."""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    source_type: MemoryType = MemoryType.WORKING
    target_type: MemoryType = MemoryType.EPISODIC

    items_to_consolidate: List[str] = field(default_factory=list)  # Memory item ID'leri

    priority: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)

    status: str = "pending"  # pending, processing, completed, failed


# ========================================================================
# QUERY & RETRIEVAL
# ========================================================================

@dataclass
class MemoryQuery:
    """Bellek sorgusu."""

    query_type: str = "similarity"   # similarity, temporal, agent, emotion

    # Filtreler
    memory_types: List[MemoryType] = field(default_factory=list)
    agent_ids: List[str] = field(default_factory=list)
    time_range: Optional[tuple] = None  # (start_datetime, end_datetime)
    emotion_filter: Optional[str] = None
    min_importance: float = 0.0
    min_strength: float = 0.1

    # Similarity search
    query_embedding: Optional[List[float]] = None
    query_text: Optional[str] = None

    # Limit
    max_results: int = 10


@dataclass
class RetrievalResult:
    """Bellek getirme sonucu."""

    items: List[MemoryItem] = field(default_factory=list)
    relevance_scores: Dict[str, float] = field(default_factory=dict)

    query_time_ms: float = 0.0
    total_matches: int = 0


# ========================================================================
# CONVERSATION MEMORY
# ========================================================================

@dataclass
class DialogueTurn:
    """
    Tek bir diyalog turu - kullanici veya ajan mesaji.
    Sohbet gecmisinin temel birimi.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""           # Ait oldugu sohbet oturumu

    role: str = "user"                  # "user" | "agent" | "system"
    content: str = ""                   # Mesaj icerigi

    timestamp: datetime = field(default_factory=datetime.now)

    # Duygusal analiz
    emotional_valence: float = 0.0      # -1 to 1
    emotional_arousal: float = 0.0      # 0 to 1
    detected_emotion: Optional[str] = None  # joy, sadness, anger, etc.

    # Intent ve topic
    intent: Optional[str] = None        # question, statement, request, etc.
    topics: List[str] = field(default_factory=list)

    # Opsiyonel embedding (semantic search icin)
    embedding: Optional[List[float]] = None

    # Meta
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation(MemoryItem):
    """
    Sohbet oturumu - DialogueTurn'lerin koleksiyonu.
    Episodik bellek ile entegre calisir.
    """
    memory_type: MemoryType = MemoryType.CONVERSATION

    # Oturum bilgileri
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None       # Kullanici ID (varsa)
    agent_id: str = ""                  # Ajan ID

    # Zaman bilgisi
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    is_active: bool = True

    # Diyalog turleri
    turns: List[DialogueTurn] = field(default_factory=list)
    turn_count: int = 0

    # Ozet bilgiler
    summary: str = ""                   # Sohbet ozeti
    main_topics: List[str] = field(default_factory=list)
    resolved_intents: List[str] = field(default_factory=list)

    # Duygusal akis
    emotional_arc: List[float] = field(default_factory=list)  # Valence degisimi
    dominant_emotion: Optional[str] = None
    average_valence: float = 0.0

    # Iliskili episode (varsa)
    episode_id: Optional[str] = None

    # Sohbet kalitesi
    coherence_score: float = 1.0        # 0-1, sohbet tutarliligi
    engagement_score: float = 0.5       # 0-1, kullanici katilimi

    def add_turn(self, turn: DialogueTurn) -> None:
        """Diyalog turu ekle."""
        turn.conversation_id = self.session_id
        self.turns.append(turn)
        self.turn_count += 1
        self.last_accessed = datetime.now()

        # Duygusal arc guncelle
        self.emotional_arc.append(turn.emotional_valence)
        self._update_emotional_stats()

        # Topic guncelle
        for topic in turn.topics:
            if topic not in self.main_topics:
                self.main_topics.append(topic)

    def _update_emotional_stats(self) -> None:
        """Duygusal istatistikleri guncelle."""
        if not self.emotional_arc:
            return

        self.average_valence = sum(self.emotional_arc) / len(self.emotional_arc)

    def get_last_n_turns(self, n: int = 5) -> List[DialogueTurn]:
        """Son n turu getir."""
        return self.turns[-n:] if self.turns else []

    def get_context_window(self, max_tokens: int = 2000) -> List[DialogueTurn]:
        """
        Token limitine uygun context penceresi getir.
        Basit karakter tahmini kullanir (4 char ~= 1 token).
        """
        result = []
        total_chars = 0
        char_limit = max_tokens * 4

        for turn in reversed(self.turns):
            turn_chars = len(turn.content)
            if total_chars + turn_chars > char_limit:
                break
            result.insert(0, turn)
            total_chars += turn_chars

        return result

    def end_conversation(self) -> None:
        """Sohbeti sonlandir."""
        self.is_active = False
        self.ended_at = datetime.now()

    def get_duration_seconds(self) -> float:
        """Sohbet suresini saniye olarak getir."""
        end = self.ended_at or datetime.now()
        return (end - self.started_at).total_seconds()

    def to_text(self) -> str:
        """Sohbeti metin olarak formatla."""
        lines = []
        for turn in self.turns:
            role_label = "User" if turn.role == "user" else "Agent"
            lines.append(f"[{role_label}]: {turn.content}")
        return "\n".join(lines)
