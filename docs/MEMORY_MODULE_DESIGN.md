# UEM v2 - Memory Modülü Tasarım Dokümanı

**Tarih:** 7 Aralık 2025  
**Amaç:** core/memory modülünün tam tasarımı ve implementasyon rehberi  
**Yaklaşım:** Maksimalist - eksik bırakma, sonra baş ağrıtır

---

## 1. GENEL MİMARİ

### 1.1 Memory Türleri (Nörobilim Bazlı)

```
                    ┌─────────────────────────────────────┐
                    │           MEMORY SYSTEM             │
                    └─────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
    ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
    │   SENSORY     │      │  SHORT-TERM   │      │   LONG-TERM   │
    │   MEMORY      │      │    MEMORY     │      │    MEMORY     │
    │   (Buffer)    │      │  (Working)    │      │   (Storage)   │
    └───────────────┘      └───────────────┘      └───────────────┘
          │                       │                       │
          │                       │           ┌───────────┴───────────┐
          │                       │           │                       │
          ▼                       ▼           ▼                       ▼
    ┌───────────┐          ┌───────────┐  ┌───────────┐      ┌───────────┐
    │  Iconic   │          │ Capacity  │  │ EXPLICIT  │      │ IMPLICIT  │
    │  Echoic   │          │   7±2     │  │(Declarative)     │(Procedural)│
    │  Haptic   │          │  items    │  └───────────┘      └───────────┘
    └───────────┘          └───────────┘        │
                                                │
                                    ┌───────────┴───────────┐
                                    │                       │
                                    ▼                       ▼
                              ┌───────────┐          ┌───────────┐
                              │ EPISODIC  │          │ SEMANTIC  │
                              │ (Events)  │          │ (Facts)   │
                              └───────────┘          └───────────┘
```

### 1.2 UEM Memory Alt Modülleri

```
core/memory/
├── __init__.py              # Facade - tek giriş noktası
├── types.py                 # Tüm memory veri tipleri
├── store.py                 # Ana memory store (coordinator)
│
├── sensory/                 # Duyusal buffer (çok kısa süreli)
│   ├── __init__.py
│   └── buffer.py
│
├── working/                 # Çalışma belleği (7±2 öğe, aktif işlem)
│   ├── __init__.py
│   └── manager.py
│
├── episodic/                # Olay hafızası (ne, nerede, ne zaman)
│   ├── __init__.py
│   ├── episode.py           # Episode veri yapısı
│   └── store.py             # Episode storage
│
├── semantic/                # Kavramsal bilgi (facts, relationships)
│   ├── __init__.py
│   ├── knowledge.py         # Bilgi yapıları
│   └── store.py             # Knowledge storage
│
├── emotional/               # Duygusal anılar (affect-tagged memories)
│   ├── __init__.py
│   └── store.py
│
├── relationship/            # İlişki hafızası (YENİ - Trust için kritik)
│   ├── __init__.py
│   ├── record.py            # Relationship record
│   └── store.py
│
├── consolidation/           # Bellek pekiştirme (STM → LTM transfer)
│   ├── __init__.py
│   └── consolidator.py
│
└── persistence/             # PostgreSQL persistence layer
    ├── __init__.py
    ├── models.py            # SQLAlchemy models
    └── repository.py        # DB operations
```

---

## 2. VERİ YAPILARI (types.py)

### 2.1 Temel Tipler

```python
"""
core/memory/types.py

Memory modülü için tüm veri tipleri.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum, auto
from datetime import datetime
import uuid


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class MemoryType(str, Enum):
    """Bellek türü."""
    SENSORY = "sensory"
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    EMOTIONAL = "emotional"
    RELATIONSHIP = "relationship"


class EmotionalValence(str, Enum):
    """Duygusal değerlik."""
    VERY_NEGATIVE = "very_negative"  # -1.0 to -0.6
    NEGATIVE = "negative"            # -0.6 to -0.2
    NEUTRAL = "neutral"              # -0.2 to 0.2
    POSITIVE = "positive"            # 0.2 to 0.6
    VERY_POSITIVE = "very_positive"  # 0.6 to 1.0


class RelationshipType(str, Enum):
    """İlişki türü."""
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
    """Etkileşim türü."""
    # Pozitif
    HELPED = "helped"
    COOPERATED = "cooperated"
    SHARED = "shared"
    PROTECTED = "protected"
    CELEBRATED = "celebrated"
    COMFORTED = "comforted"
    
    # Nötr
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
    """Olay türü."""
    ENCOUNTER = "encounter"          # Karşılaşma
    INTERACTION = "interaction"      # Etkileşim
    OBSERVATION = "observation"      # Gözlem
    CONFLICT = "conflict"            # Çatışma
    COOPERATION = "cooperation"      # İşbirliği
    EMOTIONAL_EVENT = "emotional"    # Duygusal olay
    SIGNIFICANT = "significant"      # Önemli olay


# ═══════════════════════════════════════════════════════════════════════════
# BASE MEMORY ITEM
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MemoryItem:
    """Tüm memory öğelerinin base class'ı."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.WORKING
    
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    # Decay parametreleri
    strength: float = 1.0           # 0-1, zamanla azalır
    importance: float = 0.5         # 0-1, decay'i etkiler
    
    # Duygusal etiket
    emotional_valence: float = 0.0  # -1 to 1
    emotional_arousal: float = 0.0  # 0 to 1
    
    # Meta
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def touch(self) -> None:
        """Erişim kaydı - strength artır."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        # Her erişimde strength biraz artar (max 1.0)
        self.strength = min(1.0, self.strength + 0.05)
    
    def decay(self, rate: float = 0.01) -> None:
        """Zaman geçtikçe strength azalt."""
        # Importance yüksekse decay yavaş
        effective_rate = rate * (1.0 - self.importance * 0.5)
        self.strength = max(0.0, self.strength - effective_rate)
    
    def is_forgotten(self, threshold: float = 0.1) -> bool:
        """Unutuldu mu?"""
        return self.strength < threshold


# ═══════════════════════════════════════════════════════════════════════════
# SENSORY MEMORY
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SensoryTrace(MemoryItem):
    """
    Duyusal iz - çok kısa süreli (ms-saniye).
    Raw sensory input'un geçici kaydı.
    """
    memory_type: MemoryType = MemoryType.SENSORY
    
    modality: str = "visual"         # visual, auditory, tactile
    raw_data: Any = None             # Ham veri
    duration_ms: float = 500.0       # Varsayılan yaşam süresi
    
    # Attention tarafından seçildi mi?
    attended: bool = False


# ═══════════════════════════════════════════════════════════════════════════
# WORKING MEMORY
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class WorkingMemoryItem(MemoryItem):
    """
    Çalışma belleği öğesi - aktif işlem için (7±2 limit).
    """
    memory_type: MemoryType = MemoryType.WORKING
    
    content: Any = None              # İçerik (herhangi bir tip)
    source: str = ""                 # Nereden geldi (perception, retrieval, etc.)
    priority: float = 0.5            # 0-1, yüksek = daha önemli
    
    # Binding - diğer WM items ile bağlantı
    bindings: List[str] = field(default_factory=list)  # Diğer item ID'leri


# ═══════════════════════════════════════════════════════════════════════════
# EPISODIC MEMORY
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Episode(MemoryItem):
    """
    Olay kaydı - ne, nerede, ne zaman, kim.
    Autobiographical memory.
    """
    memory_type: MemoryType = MemoryType.EPISODIC
    
    # 5W1H
    what: str = ""                   # Ne oldu?
    where: str = ""                  # Nerede?
    when: datetime = field(default_factory=datetime.now)
    who: List[str] = field(default_factory=list)  # Kim vardı? (agent_id'ler)
    why: Optional[str] = None        # Neden? (çıkarsanmış)
    how: Optional[str] = None        # Nasıl?
    
    # Olay detayları
    episode_type: EpisodeType = EpisodeType.ENCOUNTER
    duration_seconds: float = 0.0
    
    # Sonuç
    outcome: str = ""                # Olayın sonucu
    outcome_valence: float = 0.0     # Sonuç iyi mi kötü mü? (-1 to 1)
    
    # İlişkili ajanlar ve rolleri
    agent_roles: Dict[str, str] = field(default_factory=dict)  # {agent_id: role}
    
    # Duygusal iz (affect modülünden)
    self_emotion_during: Optional[str] = None     # Ben ne hissettim?
    self_emotion_after: Optional[str] = None      # Sonra ne hissettim?
    other_emotions: Dict[str, str] = field(default_factory=dict)  # Diğerleri
    
    # PAD state
    pad_state: Optional[Dict[str, float]] = None  # {pleasure, arousal, dominance}


@dataclass
class EpisodeSummary:
    """Episode özeti - hızlı erişim için."""
    episode_id: str
    episode_type: EpisodeType
    when: datetime
    who: List[str]
    outcome_valence: float
    emotional_valence: float
    importance: float


# ═══════════════════════════════════════════════════════════════════════════
# SEMANTIC MEMORY
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SemanticFact(MemoryItem):
    """
    Anlamsal bilgi - genel bilgi, kavramlar.
    Context-free facts.
    """
    memory_type: MemoryType = MemoryType.SEMANTIC
    
    subject: str = ""                # Özne
    predicate: str = ""              # Yüklem (ilişki)
    object: str = ""                 # Nesne
    
    # Örnek: ("Alice", "is_a", "friend")
    # Örnek: ("enemy", "implies", "high_threat")
    
    confidence: float = 1.0          # Ne kadar eminim?
    source: str = ""                 # Nereden öğrendim?
    
    # İlişkili kavramlar
    related_concepts: List[str] = field(default_factory=list)


@dataclass
class ConceptNode:
    """
    Kavram düğümü - semantic network için.
    """
    concept_id: str
    name: str
    category: str = ""               # Kategori (agent, object, place, action)
    
    # Özellikler
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Bağlantılar (edges)
    relations: Dict[str, List[str]] = field(default_factory=dict)
    # Örnek: {"is_a": ["person"], "can": ["help", "harm"], "opposite": ["friend"]}
    
    # Prototip (kategori için tipik değerler)
    prototype: Dict[str, float] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# EMOTIONAL MEMORY
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EmotionalMemory(MemoryItem):
    """
    Duygusal anı - affect-tagged memory.
    Duygusal olarak yüklü anılar daha güçlü hatırlanır.
    """
    memory_type: MemoryType = MemoryType.EMOTIONAL
    
    # Bağlı episode
    episode_id: Optional[str] = None
    
    # Duygusal içerik
    primary_emotion: str = ""        # Ana duygu (fear, joy, sadness, etc.)
    emotion_intensity: float = 0.5   # 0-1
    
    # PAD
    pleasure: float = 0.0
    arousal: float = 0.5
    dominance: float = 0.5
    
    # Tetikleyiciler
    triggers: List[str] = field(default_factory=list)  # Bu anıyı tetikleyen şeyler
    
    # Flashbulb memory mi? (çok canlı, detaylı)
    is_flashbulb: bool = False
    
    # Somatic marker (Damasio)
    somatic_marker: Optional[str] = None  # "gut_feeling_negative", "warm_feeling"


# ═══════════════════════════════════════════════════════════════════════════
# RELATIONSHIP MEMORY (Trust için kritik!)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Interaction:
    """Tek bir etkileşim kaydı."""
    
    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    interaction_type: InteractionType = InteractionType.OBSERVED
    context: str = ""                # Bağlam açıklaması
    
    # Sonuç
    outcome: str = ""
    outcome_valence: float = 0.0     # -1 to 1
    
    # Duygusal etki
    emotional_impact: float = 0.0    # -1 to 1
    trust_impact: float = 0.0        # Trust'a etkisi
    
    # İlişkili episode
    episode_id: Optional[str] = None


@dataclass
class RelationshipRecord(MemoryItem):
    """
    İlişki kaydı - bir agent ile tüm geçmiş.
    Trust modülü için birincil kaynak!
    """
    memory_type: MemoryType = MemoryType.RELATIONSHIP
    
    agent_id: str = ""               # Karşı tarafın ID'si
    agent_name: str = ""             # İsim (varsa)
    
    # İlişki durumu
    relationship_type: RelationshipType = RelationshipType.STRANGER
    relationship_start: datetime = field(default_factory=datetime.now)
    
    # Etkileşim geçmişi
    interactions: List[Interaction] = field(default_factory=list)
    total_interactions: int = 0
    
    # İstatistikler
    positive_interactions: int = 0
    negative_interactions: int = 0
    neutral_interactions: int = 0
    
    # Trust ile entegrasyon
    trust_score: float = 0.5         # 0-1, Trust modülünden senkronize
    trust_history: List[float] = field(default_factory=list)  # Trust değişim tarihçesi
    
    # Betrayal tracking
    betrayal_count: int = 0
    last_betrayal: Optional[datetime] = None
    
    # Duygusal özet
    overall_sentiment: float = 0.0   # -1 to 1
    dominant_emotion_with: str = ""  # Bu kişiyle en çok hissettiğim duygu
    
    # Son etkileşim
    last_interaction: Optional[datetime] = None
    last_interaction_type: Optional[InteractionType] = None
    
    # Notlar
    notes: List[str] = field(default_factory=list)
    
    def add_interaction(self, interaction: Interaction) -> None:
        """Etkileşim ekle ve istatistikleri güncelle."""
        self.interactions.append(interaction)
        self.total_interactions += 1
        self.last_interaction = interaction.timestamp
        self.last_interaction_type = interaction.interaction_type
        
        # İstatistik güncelle
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
        
        # Sentiment güncelle
        self._update_sentiment()
    
    def _update_sentiment(self) -> None:
        """Genel sentiment hesapla."""
        if self.total_interactions == 0:
            self.overall_sentiment = 0.0
            return
        
        # Ağırlıklı ortalama (son etkileşimler daha önemli)
        if self.interactions:
            recent = self.interactions[-10:]  # Son 10
            weights = [0.5 + 0.5 * (i / len(recent)) for i in range(len(recent))]
            weighted_sum = sum(
                i.outcome_valence * w for i, w in zip(recent, weights)
            )
            self.overall_sentiment = weighted_sum / sum(weights)
    
    def get_trust_recommendation(self) -> float:
        """Trust modülü için önerilen başlangıç trust değeri."""
        if self.total_interactions == 0:
            # Hiç etkileşim yok - relationship type'a göre
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
        
        # Etkileşim var - geçmişe göre hesapla
        base = 0.5
        
        # Pozitif/negatif oranı
        if self.total_interactions > 0:
            ratio = (self.positive_interactions - self.negative_interactions) / self.total_interactions
            base += ratio * 0.3
        
        # Betrayal penalty
        if self.betrayal_count > 0:
            base -= self.betrayal_count * 0.15
        
        return max(0.05, min(0.95, base))


# ═══════════════════════════════════════════════════════════════════════════
# CONSOLIDATION
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ConsolidationTask:
    """Bellek pekiştirme görevi."""
    
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    source_type: MemoryType = MemoryType.WORKING
    target_type: MemoryType = MemoryType.EPISODIC
    
    items_to_consolidate: List[str] = field(default_factory=list)  # Memory item ID'leri
    
    priority: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    
    status: str = "pending"  # pending, processing, completed, failed


# ═══════════════════════════════════════════════════════════════════════════
# QUERY & RETRIEVAL
# ═══════════════════════════════════════════════════════════════════════════

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
```

---

## 3. POSTGRESQL ŞEMASI

### 3.1 Docker Kurulum

```bash
# Eski container'ı durdur ve sil
docker stop uem_postgres 2>/dev/null
docker rm uem_postgres 2>/dev/null

# Yeni container oluştur
docker run -d \
  --name uem_v2_postgres \
  -e POSTGRES_USER=uem \
  -e POSTGRES_PASSWORD=uem_secret \
  -e POSTGRES_DB=uem_v2 \
  -p 5432:5432 \
  -v uem_v2_pgdata:/var/lib/postgresql/data \
  postgres:15

# Bağlantı testi
docker exec -it uem_v2_postgres psql -U uem -d uem_v2 -c "SELECT 1;"
```

### 3.2 SQL Schema

```sql
-- sql/memory_schema.sql

-- ═══════════════════════════════════════════════════════════════════════════
-- ENUMS
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TYPE memory_type AS ENUM (
    'sensory', 'working', 'episodic', 'semantic', 'emotional', 'relationship'
);

CREATE TYPE relationship_type AS ENUM (
    'unknown', 'stranger', 'acquaintance', 'colleague', 
    'friend', 'close_friend', 'family', 'rival', 'enemy', 'neutral'
);

CREATE TYPE interaction_type AS ENUM (
    'helped', 'cooperated', 'shared', 'protected', 'celebrated', 'comforted',
    'observed', 'conversed', 'traded',
    'competed', 'conflicted', 'harmed', 'betrayed', 'threatened', 'attacked'
);

CREATE TYPE episode_type AS ENUM (
    'encounter', 'interaction', 'observation', 'conflict', 
    'cooperation', 'emotional', 'significant'
);

-- ═══════════════════════════════════════════════════════════════════════════
-- EPISODES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 5W1H
    what TEXT NOT NULL,
    location TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    participants TEXT[] DEFAULT '{}',  -- agent_id array
    why TEXT,
    how TEXT,
    
    -- Olay detayları
    episode_type episode_type NOT NULL DEFAULT 'encounter',
    duration_seconds FLOAT DEFAULT 0,
    
    -- Sonuç
    outcome TEXT,
    outcome_valence FLOAT DEFAULT 0 CHECK (outcome_valence >= -1 AND outcome_valence <= 1),
    
    -- Duygusal iz
    self_emotion_during TEXT,
    self_emotion_after TEXT,
    pleasure FLOAT,
    arousal FLOAT,
    dominance FLOAT,
    
    -- Memory metadata
    strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    emotional_valence FLOAT DEFAULT 0 CHECK (emotional_valence >= -1 AND emotional_valence <= 1),
    emotional_arousal FLOAT DEFAULT 0 CHECK (emotional_arousal >= 0 AND emotional_arousal <= 1),
    
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Meta
    tags TEXT[] DEFAULT '{}',
    context JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_episodes_occurred_at ON episodes(occurred_at DESC);
CREATE INDEX idx_episodes_participants ON episodes USING GIN(participants);
CREATE INDEX idx_episodes_type ON episodes(episode_type);
CREATE INDEX idx_episodes_importance ON episodes(importance DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- RELATIONSHIPS
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    agent_id TEXT NOT NULL UNIQUE,
    agent_name TEXT,
    
    relationship_type relationship_type NOT NULL DEFAULT 'stranger',
    relationship_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- İstatistikler
    total_interactions INT DEFAULT 0,
    positive_interactions INT DEFAULT 0,
    negative_interactions INT DEFAULT 0,
    neutral_interactions INT DEFAULT 0,
    
    -- Trust
    trust_score FLOAT DEFAULT 0.5 CHECK (trust_score >= 0 AND trust_score <= 1),
    
    -- Betrayal
    betrayal_count INT DEFAULT 0,
    last_betrayal TIMESTAMP WITH TIME ZONE,
    
    -- Duygusal özet
    overall_sentiment FLOAT DEFAULT 0 CHECK (overall_sentiment >= -1 AND overall_sentiment <= 1),
    dominant_emotion TEXT,
    
    -- Son etkileşim
    last_interaction TIMESTAMP WITH TIME ZONE,
    last_interaction_type interaction_type,
    
    -- Memory metadata
    strength FLOAT DEFAULT 1.0,
    importance FLOAT DEFAULT 0.5,
    
    -- Meta
    notes TEXT[] DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_relationships_agent_id ON relationships(agent_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
CREATE INDEX idx_relationships_trust ON relationships(trust_score);

-- ═══════════════════════════════════════════════════════════════════════════
-- INTERACTIONS
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    relationship_id UUID NOT NULL REFERENCES relationships(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id) ON DELETE SET NULL,
    
    interaction_type interaction_type NOT NULL,
    context TEXT,
    
    -- Sonuç
    outcome TEXT,
    outcome_valence FLOAT DEFAULT 0 CHECK (outcome_valence >= -1 AND outcome_valence <= 1),
    
    -- Etki
    emotional_impact FLOAT DEFAULT 0,
    trust_impact FLOAT DEFAULT 0,
    
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_interactions_relationship ON interactions(relationship_id);
CREATE INDEX idx_interactions_occurred_at ON interactions(occurred_at DESC);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);

-- ═══════════════════════════════════════════════════════════════════════════
-- SEMANTIC FACTS
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE semantic_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    source TEXT,
    
    -- Memory metadata
    strength FLOAT DEFAULT 1.0,
    importance FLOAT DEFAULT 0.5,
    access_count INT DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(subject, predicate, object)
);

CREATE INDEX idx_semantic_subject ON semantic_facts(subject);
CREATE INDEX idx_semantic_predicate ON semantic_facts(predicate);
CREATE INDEX idx_semantic_object ON semantic_facts(object);

-- ═══════════════════════════════════════════════════════════════════════════
-- EMOTIONAL MEMORIES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE emotional_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    episode_id UUID REFERENCES episodes(id) ON DELETE SET NULL,
    
    primary_emotion TEXT NOT NULL,
    emotion_intensity FLOAT DEFAULT 0.5 CHECK (emotion_intensity >= 0 AND emotion_intensity <= 1),
    
    pleasure FLOAT DEFAULT 0,
    arousal FLOAT DEFAULT 0.5,
    dominance FLOAT DEFAULT 0.5,
    
    triggers TEXT[] DEFAULT '{}',
    is_flashbulb BOOLEAN DEFAULT FALSE,
    somatic_marker TEXT,
    
    -- Memory metadata
    strength FLOAT DEFAULT 1.0,
    importance FLOAT DEFAULT 0.5,
    access_count INT DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_emotional_emotion ON emotional_memories(primary_emotion);
CREATE INDEX idx_emotional_intensity ON emotional_memories(emotion_intensity DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- TRUST HISTORY (Trust modülü ile senkronizasyon)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE trust_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    relationship_id UUID NOT NULL REFERENCES relationships(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    
    trust_value FLOAT NOT NULL CHECK (trust_value >= 0 AND trust_value <= 1),
    previous_value FLOAT,
    delta FLOAT,
    
    event_type TEXT,  -- Trust modülündeki event (helped_me, betrayal, etc.)
    event_context TEXT,
    
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_trust_history_agent ON trust_history(agent_id);
CREATE INDEX idx_trust_history_recorded ON trust_history(recorded_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER episodes_updated_at
    BEFORE UPDATE ON episodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER relationships_updated_at
    BEFORE UPDATE ON relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER semantic_facts_updated_at
    BEFORE UPDATE ON semantic_facts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER emotional_memories_updated_at
    BEFORE UPDATE ON emotional_memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Decay function (cron job ile çağrılabilir)
CREATE OR REPLACE FUNCTION apply_memory_decay(decay_rate FLOAT DEFAULT 0.01)
RETURNS void AS $$
BEGIN
    -- Episodes
    UPDATE episodes
    SET strength = GREATEST(0, strength - decay_rate * (1 - importance * 0.5))
    WHERE strength > 0;
    
    -- Relationships - daha yavaş decay
    UPDATE relationships
    SET strength = GREATEST(0, strength - decay_rate * 0.5 * (1 - importance * 0.5))
    WHERE strength > 0;
    
    -- Semantic facts - en yavaş decay
    UPDATE semantic_facts
    SET strength = GREATEST(0, strength - decay_rate * 0.2 * (1 - importance * 0.5))
    WHERE strength > 0;
    
    -- Emotional memories - importance yüksekse çok yavaş
    UPDATE emotional_memories
    SET strength = GREATEST(0, strength - decay_rate * 0.3 * (1 - importance * 0.7))
    WHERE strength > 0;
END;
$$ LANGUAGE plpgsql;
```

---

## 4. ANA STORE (Coordinator)

```python
"""
core/memory/store.py

Ana memory store - tüm alt sistemleri koordine eder.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Type
from datetime import datetime, timedelta
import logging

from .types import (
    MemoryItem, MemoryType, MemoryQuery, RetrievalResult,
    Episode, EpisodeSummary, EpisodeType,
    SemanticFact, ConceptNode,
    EmotionalMemory,
    RelationshipRecord, Interaction, InteractionType, RelationshipType,
    WorkingMemoryItem, SensoryTrace,
    ConsolidationTask,
)

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """Memory sistem yapılandırması."""
    
    # Working memory
    working_memory_capacity: int = 7      # Miller's Law (7±2)
    working_memory_duration_sec: float = 30.0
    
    # Sensory buffer
    sensory_buffer_size: int = 100
    sensory_duration_ms: float = 500.0
    
    # Decay
    enable_decay: bool = True
    decay_interval_hours: float = 24.0
    base_decay_rate: float = 0.01
    
    # Consolidation
    enable_consolidation: bool = True
    consolidation_threshold: float = 0.7   # Importance threshold
    
    # Persistence
    use_persistence: bool = True
    db_connection_string: str = "postgresql://uem:uem_secret@localhost:5432/uem_v2"
    
    # Retrieval
    default_retrieval_limit: int = 10
    min_strength_threshold: float = 0.1


class MemoryStore:
    """
    Ana memory store - facade pattern.
    
    Tüm memory alt sistemlerini koordine eder:
    - Sensory buffer
    - Working memory
    - Episodic memory
    - Semantic memory
    - Emotional memory
    - Relationship memory
    - Consolidation
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        
        # In-memory stores
        self._sensory_buffer: List[SensoryTrace] = []
        self._working_memory: List[WorkingMemoryItem] = []
        self._episodes: Dict[str, Episode] = {}
        self._semantic_facts: Dict[str, SemanticFact] = {}
        self._emotional_memories: Dict[str, EmotionalMemory] = {}
        self._relationships: Dict[str, RelationshipRecord] = {}  # key = agent_id
        
        # Concepts (semantic network)
        self._concepts: Dict[str, ConceptNode] = {}
        
        # Consolidation queue
        self._consolidation_queue: List[ConsolidationTask] = []
        
        # Stats
        self._stats = {
            "total_episodes": 0,
            "total_relationships": 0,
            "total_retrievals": 0,
            "consolidations": 0,
        }
        
        # Persistence (lazy init)
        self._repository = None
        
        logger.info("MemoryStore initialized")
    
    # ═══════════════════════════════════════════════════════════════════
    # SENSORY BUFFER
    # ═══════════════════════════════════════════════════════════════════
    
    def buffer_sensory(self, trace: SensoryTrace) -> None:
        """Duyusal izi buffer'a ekle."""
        self._sensory_buffer.append(trace)
        
        # Buffer boyut kontrolü
        if len(self._sensory_buffer) > self.config.sensory_buffer_size:
            # Eski ve unattended olanları sil
            self._sensory_buffer = [
                t for t in self._sensory_buffer
                if t.attended or (datetime.now() - t.created_at).total_seconds() * 1000 < t.duration_ms
            ][:self.config.sensory_buffer_size]
    
    def get_sensory_buffer(self) -> List[SensoryTrace]:
        """Aktif sensory buffer'ı getir."""
        now = datetime.now()
        return [
            t for t in self._sensory_buffer
            if (now - t.created_at).total_seconds() * 1000 < t.duration_ms
        ]
    
    # ═══════════════════════════════════════════════════════════════════
    # WORKING MEMORY
    # ═══════════════════════════════════════════════════════════════════
    
    def hold_in_working(self, item: WorkingMemoryItem) -> bool:
        """
        Working memory'ye öğe ekle.
        
        Returns:
            True if added, False if capacity full
        """
        # Süresi dolmuş öğeleri temizle
        self._clean_working_memory()
        
        # Kapasite kontrolü
        if len(self._working_memory) >= self.config.working_memory_capacity:
            # En düşük priority'yi çıkar
            if item.priority > min(i.priority for i in self._working_memory):
                self._working_memory.sort(key=lambda x: x.priority)
                removed = self._working_memory.pop(0)
                # Consolidation'a gönder
                self._queue_consolidation(removed)
            else:
                return False
        
        self._working_memory.append(item)
        return True
    
    def get_working_memory(self) -> List[WorkingMemoryItem]:
        """Working memory içeriğini getir."""
        self._clean_working_memory()
        return list(self._working_memory)
    
    def clear_working_memory(self) -> List[WorkingMemoryItem]:
        """Working memory'yi temizle (cycle sonu)."""
        items = list(self._working_memory)
        self._working_memory.clear()
        
        # Önemli olanları consolidation'a gönder
        for item in items:
            if item.importance > self.config.consolidation_threshold:
                self._queue_consolidation(item)
        
        return items
    
    def _clean_working_memory(self) -> None:
        """Süresi dolmuş working memory öğelerini temizle."""
        now = datetime.now()
        cutoff = timedelta(seconds=self.config.working_memory_duration_sec)
        
        self._working_memory = [
            item for item in self._working_memory
            if now - item.created_at < cutoff
        ]
    
    # ═══════════════════════════════════════════════════════════════════
    # EPISODIC MEMORY
    # ═══════════════════════════════════════════════════════════════════
    
    def store_episode(self, episode: Episode) -> str:
        """
        Episode kaydet.
        
        Returns:
            Episode ID
        """
        self._episodes[episode.id] = episode
        self._stats["total_episodes"] += 1
        
        # İlişkili agent'ların relationship'lerini güncelle
        for agent_id in episode.who:
            self._update_relationship_from_episode(agent_id, episode)
        
        # Duygusal yoğunluk yüksekse emotional memory oluştur
        if abs(episode.emotional_valence) > 0.6 or episode.emotional_arousal > 0.7:
            self._create_emotional_memory_from_episode(episode)
        
        # Persistence
        if self.config.use_persistence and self._repository:
            self._repository.save_episode(episode)
        
        logger.debug(f"Episode stored: {episode.id}")
        return episode.id
    
    def get_episode(self, episode_id: str) -> Optional[Episode]:
        """Episode getir."""
        episode = self._episodes.get(episode_id)
        if episode:
            episode.touch()
        return episode
    
    def recall_episodes(
        self,
        agent_id: Optional[str] = None,
        episode_type: Optional[EpisodeType] = None,
        time_range: Optional[tuple] = None,
        min_importance: float = 0.0,
        limit: int = 10,
    ) -> List[Episode]:
        """
        Episode'ları hatırla (recall).
        
        Args:
            agent_id: Belirli bir agent ile ilgili
            episode_type: Belirli tür
            time_range: (start, end) datetime tuple
            min_importance: Minimum önem
            limit: Maksimum sonuç
        """
        results = []
        
        for episode in self._episodes.values():
            # Filtreler
            if episode.strength < self.config.min_strength_threshold:
                continue
            if episode.importance < min_importance:
                continue
            if agent_id and agent_id not in episode.who:
                continue
            if episode_type and episode.episode_type != episode_type:
                continue
            if time_range:
                start, end = time_range
                if not (start <= episode.when <= end):
                    continue
            
            results.append(episode)
        
        # Önem ve güncelliğe göre sırala
        results.sort(key=lambda e: (e.importance * 0.4 + e.strength * 0.6), reverse=True)
        
        # Touch (erişim kaydı)
        for episode in results[:limit]:
            episode.touch()
        
        self._stats["total_retrievals"] += 1
        return results[:limit]
    
    def recall_similar_episodes(
        self,
        situation: str,
        limit: int = 5,
    ) -> List[Episode]:
        """
        Benzer durumları hatırla.
        Basit keyword matching (ileride embedding olabilir).
        """
        keywords = set(situation.lower().split())
        
        scored = []
        for episode in self._episodes.values():
            if episode.strength < self.config.min_strength_threshold:
                continue
            
            # Basit benzerlik skoru
            episode_words = set(episode.what.lower().split())
            if episode.outcome:
                episode_words.update(episode.outcome.lower().split())
            
            overlap = len(keywords & episode_words)
            if overlap > 0:
                score = overlap / len(keywords | episode_words)
                scored.append((episode, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:limit]]
    
    # ═══════════════════════════════════════════════════════════════════
    # RELATIONSHIP MEMORY (Trust entegrasyonu için kritik!)
    # ═══════════════════════════════════════════════════════════════════
    
    def get_relationship(self, agent_id: str) -> RelationshipRecord:
        """
        Agent ile ilişki kaydını getir (yoksa oluştur).
        
        Trust modülü bu metodu kullanmalı!
        """
        if agent_id not in self._relationships:
            self._relationships[agent_id] = RelationshipRecord(
                agent_id=agent_id,
                relationship_type=RelationshipType.STRANGER,
            )
            self._stats["total_relationships"] += 1
        
        return self._relationships[agent_id]
    
    def update_relationship(
        self,
        agent_id: str,
        relationship_type: Optional[RelationshipType] = None,
        agent_name: Optional[str] = None,
    ) -> RelationshipRecord:
        """İlişki kaydını güncelle."""
        record = self.get_relationship(agent_id)
        
        if relationship_type:
            record.relationship_type = relationship_type
        if agent_name:
            record.agent_name = agent_name
        
        return record
    
    def record_interaction(
        self,
        agent_id: str,
        interaction: Interaction,
    ) -> RelationshipRecord:
        """
        Agent ile etkileşim kaydet.
        
        Trust modülü her trust event'i burada da kaydetmeli!
        """
        record = self.get_relationship(agent_id)
        record.add_interaction(interaction)
        
        # Persistence
        if self.config.use_persistence and self._repository:
            self._repository.save_interaction(agent_id, interaction)
        
        return record
    
    def get_interaction_history(
        self,
        agent_id: str,
        limit: int = 20,
        interaction_type: Optional[InteractionType] = None,
    ) -> List[Interaction]:
        """Agent ile etkileşim geçmişi."""
        record = self.get_relationship(agent_id)
        
        interactions = record.interactions
        if interaction_type:
            interactions = [i for i in interactions if i.interaction_type == interaction_type]
        
        return interactions[-limit:]
    
    def is_known_agent(self, agent_id: str) -> bool:
        """Bu agent'ı tanıyor muyuz?"""
        if agent_id not in self._relationships:
            return False
        
        record = self._relationships[agent_id]
        return record.total_interactions > 0
    
    def get_all_relationships(
        self,
        relationship_type: Optional[RelationshipType] = None,
    ) -> List[RelationshipRecord]:
        """Tüm ilişkileri getir."""
        records = list(self._relationships.values())
        
        if relationship_type:
            records = [r for r in records if r.relationship_type == relationship_type]
        
        return records
    
    def _update_relationship_from_episode(
        self,
        agent_id: str,
        episode: Episode,
    ) -> None:
        """Episode'dan relationship güncelle."""
        record = self.get_relationship(agent_id)
        
        # Episode'dan interaction çıkar
        interaction = Interaction(
            interaction_type=self._infer_interaction_type(episode),
            context=episode.what,
            outcome=episode.outcome,
            outcome_valence=episode.outcome_valence,
            emotional_impact=episode.emotional_valence,
            episode_id=episode.id,
            timestamp=episode.when,
        )
        
        record.add_interaction(interaction)
    
    def _infer_interaction_type(self, episode: Episode) -> InteractionType:
        """Episode'dan interaction type çıkar."""
        # Basit keyword matching
        what_lower = episode.what.lower()
        
        if any(w in what_lower for w in ["help", "assist", "support"]):
            return InteractionType.HELPED
        elif any(w in what_lower for w in ["attack", "fight", "hit"]):
            return InteractionType.ATTACKED
        elif any(w in what_lower for w in ["betray", "deceive", "lie"]):
            return InteractionType.BETRAYED
        elif any(w in what_lower for w in ["threat", "warn"]):
            return InteractionType.THREATENED
        elif any(w in what_lower for w in ["cooperat", "together", "team"]):
            return InteractionType.COOPERATED
        elif any(w in what_lower for w in ["talk", "convers", "discuss"]):
            return InteractionType.CONVERSED
        else:
            return InteractionType.OBSERVED
    
    # ═══════════════════════════════════════════════════════════════════
    # SEMANTIC MEMORY
    # ═══════════════════════════════════════════════════════════════════
    
    def store_fact(self, fact: SemanticFact) -> str:
        """Semantic fact kaydet."""
        key = f"{fact.subject}:{fact.predicate}:{fact.object}"
        self._semantic_facts[key] = fact
        return fact.id
    
    def query_facts(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
    ) -> List[SemanticFact]:
        """Fact sorgula."""
        results = []
        
        for fact in self._semantic_facts.values():
            if subject and fact.subject != subject:
                continue
            if predicate and fact.predicate != predicate:
                continue
            if obj and fact.object != obj:
                continue
            results.append(fact)
        
        return results
    
    def get_concept(self, concept_id: str) -> Optional[ConceptNode]:
        """Kavram getir."""
        return self._concepts.get(concept_id)
    
    def add_concept(self, concept: ConceptNode) -> None:
        """Kavram ekle."""
        self._concepts[concept.concept_id] = concept
    
    # ═══════════════════════════════════════════════════════════════════
    # EMOTIONAL MEMORY
    # ═══════════════════════════════════════════════════════════════════
    
    def store_emotional_memory(self, memory: EmotionalMemory) -> str:
        """Duygusal anı kaydet."""
        self._emotional_memories[memory.id] = memory
        return memory.id
    
    def recall_by_emotion(
        self,
        emotion: str,
        min_intensity: float = 0.3,
        limit: int = 10,
    ) -> List[EmotionalMemory]:
        """Belirli duyguyla ilişkili anıları hatırla."""
        results = [
            m for m in self._emotional_memories.values()
            if m.primary_emotion == emotion and m.emotion_intensity >= min_intensity
        ]
        
        results.sort(key=lambda m: m.emotion_intensity, reverse=True)
        return results[:limit]
    
    def recall_by_trigger(self, trigger: str) -> List[EmotionalMemory]:
        """Tetikleyiciye göre anıları hatırla."""
        return [
            m for m in self._emotional_memories.values()
            if trigger in m.triggers
        ]
    
    def _create_emotional_memory_from_episode(self, episode: Episode) -> None:
        """Episode'dan emotional memory oluştur."""
        memory = EmotionalMemory(
            episode_id=episode.id,
            primary_emotion=episode.self_emotion_during or "unknown",
            emotion_intensity=abs(episode.emotional_valence),
            pleasure=episode.pad_state.get("pleasure", 0) if episode.pad_state else 0,
            arousal=episode.pad_state.get("arousal", 0.5) if episode.pad_state else 0.5,
            dominance=episode.pad_state.get("dominance", 0.5) if episode.pad_state else 0.5,
            importance=episode.importance,
            is_flashbulb=episode.emotional_arousal > 0.9,
        )
        
        self.store_emotional_memory(memory)
    
    # ═══════════════════════════════════════════════════════════════════
    # CONSOLIDATION
    # ═══════════════════════════════════════════════════════════════════
    
    def _queue_consolidation(self, item: WorkingMemoryItem) -> None:
        """Consolidation kuyruğuna ekle."""
        if not self.config.enable_consolidation:
            return
        
        task = ConsolidationTask(
            source_type=MemoryType.WORKING,
            target_type=MemoryType.EPISODIC,
            items_to_consolidate=[item.id],
            priority=item.importance,
        )
        
        self._consolidation_queue.append(task)
    
    def run_consolidation(self) -> int:
        """
        Consolidation çalıştır (background task olarak).
        
        Returns:
            İşlenen task sayısı
        """
        processed = 0
        
        while self._consolidation_queue:
            task = self._consolidation_queue.pop(0)
            
            # TODO: Gerçek consolidation logic
            # Working memory item'ı episode'a dönüştür
            
            task.status = "completed"
            processed += 1
            self._stats["consolidations"] += 1
        
        return processed
    
    # ═══════════════════════════════════════════════════════════════════
    # DECAY
    # ═══════════════════════════════════════════════════════════════════
    
    def apply_decay(self) -> Dict[str, int]:
        """
        Tüm belleklere decay uygula.
        
        Returns:
            Her memory type için decay uygulanan öğe sayısı
        """
        if not self.config.enable_decay:
            return {}
        
        rate = self.config.base_decay_rate
        counts = {}
        
        # Episodes
        for episode in self._episodes.values():
            episode.decay(rate)
        counts["episodes"] = len(self._episodes)
        
        # Relationships (daha yavaş)
        for record in self._relationships.values():
            record.decay(rate * 0.5)
        counts["relationships"] = len(self._relationships)
        
        # Semantic (en yavaş)
        for fact in self._semantic_facts.values():
            fact.decay(rate * 0.2)
        counts["semantic"] = len(self._semantic_facts)
        
        # Emotional (importance'a çok bağlı)
        for memory in self._emotional_memories.values():
            memory.decay(rate * 0.3)
        counts["emotional"] = len(self._emotional_memories)
        
        # Unutulanları temizle
        self._cleanup_forgotten()
        
        return counts
    
    def _cleanup_forgotten(self) -> None:
        """Unutulan öğeleri temizle."""
        threshold = self.config.min_strength_threshold
        
        # Episodes
        self._episodes = {
            k: v for k, v in self._episodes.items()
            if not v.is_forgotten(threshold)
        }
        
        # Semantic (daha düşük threshold)
        self._semantic_facts = {
            k: v for k, v in self._semantic_facts.items()
            if not v.is_forgotten(threshold * 0.5)
        }
        
        # Emotional (daha düşük threshold - duygusal anılar daha kalıcı)
        self._emotional_memories = {
            k: v for k, v in self._emotional_memories.items()
            if not v.is_forgotten(threshold * 0.3)
        }
        
        # Relationships never fully forgotten (just marked inactive)
    
    # ═══════════════════════════════════════════════════════════════════
    # UNIFIED RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════
    
    def retrieve(self, query: MemoryQuery) -> RetrievalResult:
        """
        Unified memory retrieval.
        
        Cognitive cycle RETRIEVE fazı bu metodu kullanmalı.
        """
        import time
        start = time.perf_counter()
        
        results = []
        scores = {}
        
        # Memory type'lara göre sorgula
        types = query.memory_types or list(MemoryType)
        
        if MemoryType.EPISODIC in types:
            episodes = self.recall_episodes(
                agent_id=query.agent_ids[0] if query.agent_ids else None,
                time_range=query.time_range,
                min_importance=query.min_importance,
                limit=query.max_results,
            )
            for ep in episodes:
                results.append(ep)
                scores[ep.id] = ep.importance * ep.strength
        
        if MemoryType.RELATIONSHIP in types and query.agent_ids:
            for agent_id in query.agent_ids:
                record = self.get_relationship(agent_id)
                if record.total_interactions > 0:
                    results.append(record)
                    scores[record.id] = record.importance
        
        if MemoryType.EMOTIONAL in types and query.emotion_filter:
            emotions = self.recall_by_emotion(
                query.emotion_filter,
                limit=query.max_results,
            )
            for em in emotions:
                results.append(em)
                scores[em.id] = em.emotion_intensity
        
        # Sort by score
        results.sort(key=lambda x: scores.get(x.id, 0), reverse=True)
        
        self._stats["total_retrievals"] += 1
        
        return RetrievalResult(
            items=results[:query.max_results],
            relevance_scores=scores,
            query_time_ms=(time.perf_counter() - start) * 1000,
            total_matches=len(results),
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # STATS & DEBUG
    # ═══════════════════════════════════════════════════════════════════
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Memory istatistikleri."""
        return {
            **self._stats,
            "sensory_buffer_size": len(self._sensory_buffer),
            "working_memory_size": len(self._working_memory),
            "episodes_count": len(self._episodes),
            "relationships_count": len(self._relationships),
            "semantic_facts_count": len(self._semantic_facts),
            "emotional_memories_count": len(self._emotional_memories),
            "concepts_count": len(self._concepts),
            "consolidation_queue_size": len(self._consolidation_queue),
        }
    
    def debug_dump(self) -> Dict[str, Any]:
        """Debug için tam dump."""
        return {
            "config": self.config.__dict__,
            "stats": self.stats,
            "working_memory": [item.__dict__ for item in self._working_memory],
            "relationships": {
                k: {
                    "type": v.relationship_type.value,
                    "interactions": v.total_interactions,
                    "trust": v.trust_score,
                    "sentiment": v.overall_sentiment,
                }
                for k, v in self._relationships.items()
            },
        }


# ═══════════════════════════════════════════════════════════════════════════
# FACTORY & SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_memory_store: Optional[MemoryStore] = None


def get_memory_store(config: Optional[MemoryConfig] = None) -> MemoryStore:
    """Memory store singleton."""
    global _memory_store
    
    if _memory_store is None:
        _memory_store = MemoryStore(config)
    
    return _memory_store


def create_memory_store(config: Optional[MemoryConfig] = None) -> MemoryStore:
    """Yeni memory store oluştur (test için)."""
    return MemoryStore(config)
```

---

## 5. TRUST ENTEGRASYONU

### 5.1 Trust Modülü Değişiklikleri

```python
"""
core/affect/social/trust/manager.py - Memory entegrasyonu

Trust modülünün memory'den relationship history okuması ve
her event'i memory'ye kaydetmesi gerekiyor.
"""

from core.memory import get_memory_store, Interaction, InteractionType


class TrustManager:
    def __init__(self, config=None):
        # ... mevcut kod ...
        self._memory = get_memory_store()
    
    def get_profile(self, agent_id: str) -> TrustProfile:
        """
        Ajan için güven profili getir.
        
        Memory'den relationship history'yi de al!
        """
        if agent_id not in self._profiles:
            # Yeni profil oluştur
            profile = TrustProfile(agent_id=agent_id)
            
            # Memory'den başlangıç trust al
            relationship = self._memory.get_relationship(agent_id)
            initial_trust = relationship.get_trust_recommendation()
            
            # Profile uygula
            profile.components = TrustComponents(
                competence=initial_trust,
                benevolence=initial_trust,
                integrity=initial_trust,
                predictability=initial_trust,
            )
            
            self._profiles[agent_id] = profile
        
        return self._profiles[agent_id]
    
    def record_event(
        self,
        agent_id: str,
        event_type: str,
        context: str = "",
    ) -> TrustProfile:
        """
        Güven olayı kaydet.
        
        Memory'ye de kaydet!
        """
        profile = self.get_profile(agent_id)
        
        # ... mevcut trust hesaplama ...
        
        # Memory'ye interaction kaydet
        interaction = Interaction(
            interaction_type=self._map_trust_event_to_interaction(event_type),
            context=context,
            outcome_valence=event.impact,
            trust_impact=event.weighted_impact(),
        )
        
        self._memory.record_interaction(agent_id, interaction)
        
        # Trust history'yi memory'ye senkronize et
        relationship = self._memory.get_relationship(agent_id)
        relationship.trust_score = profile.overall_trust
        relationship.trust_history.append(profile.overall_trust)
        
        return profile
    
    def _map_trust_event_to_interaction(self, event_type: str) -> InteractionType:
        """Trust event → Interaction type mapping."""
        mapping = {
            "helped_me": InteractionType.HELPED,
            "promise_kept": InteractionType.COOPERATED,
            "honest_feedback": InteractionType.CONVERSED,
            "competent_action": InteractionType.COOPERATED,
            "consistent_behavior": InteractionType.OBSERVED,
            "defended_me": InteractionType.PROTECTED,
            "shared_joy": InteractionType.CELEBRATED,
            "comforted_me": InteractionType.COMFORTED,
            
            "lied_to_me": InteractionType.BETRAYED,
            "betrayal": InteractionType.BETRAYED,
            "harmed_me": InteractionType.HARMED,
            "unpredictable_behavior": InteractionType.CONFLICTED,
            "incompetent_action": InteractionType.CONFLICTED,
        }
        return mapping.get(event_type, InteractionType.OBSERVED)
```

### 5.2 Orchestrator Değişiklikleri

```python
"""
core/affect/social/orchestrator.py - Memory entegrasyonu
"""

from core.memory import get_memory_store, Episode, EpisodeType


class SocialAffectOrchestrator:
    def __init__(self, ...):
        # ... mevcut kod ...
        self._memory = get_memory_store()
    
    def process(self, agent: AgentState, ...) -> SocialAffectResult:
        # ... mevcut kod ...
        
        # İşlem sonunda episode kaydet
        self._store_interaction_episode(agent, result)
        
        return result
    
    def _store_interaction_episode(
        self,
        agent: AgentState,
        result: SocialAffectResult,
    ) -> None:
        """Etkileşimi episode olarak kaydet."""
        episode = Episode(
            what=f"Interaction with {agent.agent_id}",
            who=[agent.agent_id],
            episode_type=EpisodeType.INTERACTION,
            
            outcome=result.suggested_action,
            outcome_valence=0.0,  # Action'a göre hesaplanabilir
            
            self_emotion_during=result.empathy.get_inferred_emotion().value if result.empathy else None,
            emotional_valence=result.sympathy.total_intensity if result.sympathy else 0,
            
            importance=result.empathy.total_empathy if result.empathy else 0.5,
        )
        
        self._memory.store_episode(episode)
    
    def _infer_relationship(self, agent: AgentState) -> RelationshipContext:
        """
        Memory'den relationship context al.
        """
        # Memory'den relationship record al
        relationship = self._memory.get_relationship(agent.agent_id)
        
        # RelationshipContext'e dönüştür
        rel_type = relationship.relationship_type.value
        
        if rel_type == "friend" or rel_type == "close_friend":
            return RelationshipContext.friend()
        elif rel_type == "family":
            return RelationshipContext(valence=0.8, positive_history=0.9)
        elif rel_type == "colleague":
            return RelationshipContext(valence=0.3, positive_history=0.5)
        elif rel_type == "rival":
            return RelationshipContext.rival()
        elif rel_type == "enemy":
            return RelationshipContext(valence=-0.7, negative_history=0.8)
        else:
            # Memory'deki sentiment'a göre
            if relationship.total_interactions > 0:
                valence = relationship.overall_sentiment
                pos_ratio = relationship.positive_interactions / relationship.total_interactions
                return RelationshipContext(
                    valence=valence,
                    positive_history=pos_ratio,
                    negative_history=1 - pos_ratio,
                )
            return RelationshipContext.stranger()
```

---

## 6. COGNITIVE CYCLE ENTEGRASYONU

### 6.1 RETRIEVE Fazı

```python
"""
engine/handlers/memory.py

RETRIEVE fazı handler'ı.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from foundation.state import StateVector, SVField
from engine.phases.definitions import Phase, PhaseResult
from engine.handlers.base import PhaseHandler, Context

from core.memory import (
    get_memory_store,
    MemoryStore,
    MemoryQuery,
    MemoryType,
    RetrievalResult,
    Episode,
    RelationshipRecord,
)


@dataclass
class RetrievePhaseConfig:
    """RETRIEVE fazı yapılandırması."""
    
    # Hangi memory türlerini sorgula
    query_episodic: bool = True
    query_relationships: bool = True
    query_semantic: bool = True
    query_emotional: bool = True
    
    # Retrieval parametreleri
    max_results: int = 10
    min_importance: float = 0.1
    recency_weight: float = 0.3     # Güncel anılar daha önemli
    relevance_weight: float = 0.7    # Alakalı anılar daha önemli
    
    # Working memory
    load_to_working_memory: bool = True
    working_memory_limit: int = 5


@dataclass
class RetrieveHandlerState:
    """Handler durumu."""
    last_retrieval: Optional[RetrievalResult] = None
    retrieve_count: int = 0
    total_time_ms: float = 0.0


class RetrievePhaseHandler(PhaseHandler):
    """
    RETRIEVE fazı - bellek getirme.
    
    Context'teki bilgilere göre ilgili anıları, ilişkileri,
    ve bilgileri memory'den getirir.
    """
    
    phase = Phase.RETRIEVE
    
    def __init__(self, config: Optional[RetrievePhaseConfig] = None):
        self.config = config or RetrievePhaseConfig()
        self._memory = get_memory_store()
        self._state = RetrieveHandlerState()
    
    def handle(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """RETRIEVE fazını işle."""
        import time
        start = time.perf_counter()
        
        try:
            # Context'ten agent bilgisi al
            agents = context.metadata.get("perceived_agents", [])
            current_situation = context.metadata.get("situation", "")
            
            retrieved_items = []
            
            # 1. Algılanan agent'lar için relationship bilgisi getir
            if self.config.query_relationships and agents:
                for agent in agents:
                    agent_id = agent.get("agent_id") or agent.agent_id
                    relationship = self._memory.get_relationship(agent_id)
                    
                    retrieved_items.append({
                        "type": "relationship",
                        "agent_id": agent_id,
                        "relationship_type": relationship.relationship_type.value,
                        "trust_score": relationship.trust_score,
                        "total_interactions": relationship.total_interactions,
                        "sentiment": relationship.overall_sentiment,
                        "is_known": relationship.total_interactions > 0,
                    })
                    
                    # Trust modülüne başlangıç bilgisi ver
                    context.metadata[f"memory_trust_{agent_id}"] = relationship.get_trust_recommendation()
            
            # 2. Benzer durumları getir
            if self.config.query_episodic and current_situation:
                similar_episodes = self._memory.recall_similar_episodes(
                    current_situation,
                    limit=3,
                )
                
                for episode in similar_episodes:
                    retrieved_items.append({
                        "type": "episode",
                        "episode_id": episode.id,
                        "what": episode.what,
                        "outcome": episode.outcome,
                        "outcome_valence": episode.outcome_valence,
                        "who": episode.who,
                    })
            
            # 3. Agent'larla geçmiş olayları getir
            if self.config.query_episodic and agents:
                for agent in agents:
                    agent_id = agent.get("agent_id") or agent.agent_id
                    past_episodes = self._memory.recall_episodes(
                        agent_id=agent_id,
                        limit=3,
                    )
                    
                    for episode in past_episodes:
                        retrieved_items.append({
                            "type": "past_episode",
                            "agent_id": agent_id,
                            "episode_id": episode.id,
                            "what": episode.what,
                            "outcome_valence": episode.outcome_valence,
                        })
            
            # Context'e ekle
            context.metadata["retrieved_memories"] = retrieved_items
            context.metadata["memory_retrieval_count"] = len(retrieved_items)
            
            # Working memory'ye yükle
            if self.config.load_to_working_memory:
                self._load_to_working_memory(retrieved_items)
            
            # StateVector'a yaz
            state.set(SVField.MEMORY_LOAD, min(1.0, len(retrieved_items) / 10))
            
            duration = (time.perf_counter() - start) * 1000
            self._state.retrieve_count += 1
            self._state.total_time_ms += duration
            
            return PhaseResult(
                phase=phase,
                success=True,
                duration_ms=duration,
                output={
                    "retrieved_count": len(retrieved_items),
                    "types": list(set(item["type"] for item in retrieved_items)),
                },
            )
            
        except Exception as e:
            return PhaseResult(
                phase=phase,
                success=False,
                duration_ms=(time.perf_counter() - start) * 1000,
                error=str(e),
            )
    
    def _load_to_working_memory(self, items: List[Dict]) -> None:
        """Retrieved items'ı working memory'ye yükle."""
        from core.memory.types import WorkingMemoryItem
        
        # En önemli N tanesini al
        sorted_items = sorted(
            items,
            key=lambda x: x.get("trust_score", 0) + abs(x.get("outcome_valence", 0)),
            reverse=True,
        )[:self.config.working_memory_limit]
        
        for item in sorted_items:
            wm_item = WorkingMemoryItem(
                content=item,
                source="retrieval",
                priority=0.6,
                importance=0.5,
            )
            self._memory.hold_in_working(wm_item)


def create_retrieve_handler(
    config: Optional[RetrievePhaseConfig] = None,
) -> RetrievePhaseHandler:
    """RETRIEVE handler oluştur."""
    return RetrievePhaseHandler(config)
```

### 6.2 StateVector Yeni Alanlar

```python
"""
foundation/state/fields.py - Memory alanları
"""

class SVField(str, Enum):
    # ... mevcut alanlar ...
    
    # Memory fields
    MEMORY_LOAD = "memory_load"              # 0-1: Ne kadar bellek yüklü?
    MEMORY_RELEVANCE = "memory_relevance"    # 0-1: Getirilen bilgi ne kadar alakalı?
    KNOWN_AGENT = "known_agent"              # bool: Agent tanınıyor mu?
    RELATIONSHIP_QUALITY = "relationship_quality"  # 0-1: İlişki kalitesi
```

---

## 7. TEST SENARYOLARI

```python
"""
tests/unit/test_memory.py

Memory modülü testleri.
"""

import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from core.memory import (
    MemoryStore, MemoryConfig, get_memory_store,
    Episode, EpisodeType,
    RelationshipRecord, RelationshipType,
    Interaction, InteractionType,
    SemanticFact,
    EmotionalMemory,
    WorkingMemoryItem,
    MemoryQuery, MemoryType,
)


def test_working_memory_capacity():
    """Working memory 7±2 limiti."""
    print("\n=== TEST: Working Memory Capacity ===")
    
    config = MemoryConfig(working_memory_capacity=7)
    store = MemoryStore(config)
    
    # 10 öğe eklemeye çalış
    for i in range(10):
        item = WorkingMemoryItem(
            content=f"item_{i}",
            priority=i / 10,  # 0.0 - 0.9
        )
        store.hold_in_working(item)
    
    wm = store.get_working_memory()
    print(f"  Added 10 items, WM size: {len(wm)}")
    
    assert len(wm) <= 7, f"WM should be ≤7, got {len(wm)}"
    
    # En yüksek priority olanlar kalmalı
    priorities = [item.priority for item in wm]
    print(f"  Remaining priorities: {priorities}")
    assert min(priorities) >= 0.3, "Low priority items should be removed"
    
    print("✅ Working Memory Capacity PASSED")


def test_relationship_memory():
    """Relationship memory ve trust entegrasyonu."""
    print("\n=== TEST: Relationship Memory ===")
    
    store = MemoryStore()
    
    # Yeni agent
    alice = store.get_relationship("alice")
    print(f"  New agent 'alice': type={alice.relationship_type.value}")
    assert alice.relationship_type == RelationshipType.STRANGER
    assert alice.total_interactions == 0
    
    # Etkileşim ekle
    interaction1 = Interaction(
        interaction_type=InteractionType.HELPED,
        outcome_valence=0.8,
        trust_impact=0.1,
    )
    store.record_interaction("alice", interaction1)
    
    interaction2 = Interaction(
        interaction_type=InteractionType.COOPERATED,
        outcome_valence=0.6,
        trust_impact=0.05,
    )
    store.record_interaction("alice", interaction2)
    
    alice = store.get_relationship("alice")
    print(f"  After 2 positive interactions:")
    print(f"    total_interactions: {alice.total_interactions}")
    print(f"    positive: {alice.positive_interactions}")
    print(f"    sentiment: {alice.overall_sentiment:.2f}")
    print(f"    trust_recommendation: {alice.get_trust_recommendation():.2f}")
    
    assert alice.total_interactions == 2
    assert alice.positive_interactions == 2
    assert alice.overall_sentiment > 0.5
    assert alice.get_trust_recommendation() > 0.5
    
    # Betrayal
    betrayal = Interaction(
        interaction_type=InteractionType.BETRAYED,
        outcome_valence=-0.9,
        trust_impact=-0.3,
    )
    store.record_interaction("alice", betrayal)
    
    alice = store.get_relationship("alice")
    print(f"  After betrayal:")
    print(f"    betrayal_count: {alice.betrayal_count}")
    print(f"    trust_recommendation: {alice.get_trust_recommendation():.2f}")
    
    assert alice.betrayal_count == 1
    assert alice.get_trust_recommendation() < 0.5
    
    print("✅ Relationship Memory PASSED")


def test_episode_storage_and_recall():
    """Episode kaydetme ve hatırlama."""
    print("\n=== TEST: Episode Storage & Recall ===")
    
    store = MemoryStore()
    
    # Episode oluştur
    episode1 = Episode(
        what="Alice helped me when I was in trouble",
        where="forest",
        who=["alice"],
        episode_type=EpisodeType.COOPERATION,
        outcome="Successfully escaped danger",
        outcome_valence=0.8,
        self_emotion_during="gratitude",
        emotional_valence=0.7,
        importance=0.8,
    )
    
    episode2 = Episode(
        what="Encountered enemy in the market",
        where="market",
        who=["enemy_1"],
        episode_type=EpisodeType.CONFLICT,
        outcome="Fled successfully",
        outcome_valence=0.3,
        self_emotion_during="fear",
        emotional_valence=-0.5,
        importance=0.7,
    )
    
    store.store_episode(episode1)
    store.store_episode(episode2)
    
    print(f"  Stored 2 episodes")
    
    # Alice ile ilgili hatırla
    alice_episodes = store.recall_episodes(agent_id="alice")
    print(f"  Recall for 'alice': {len(alice_episodes)} episodes")
    assert len(alice_episodes) == 1
    assert alice_episodes[0].who == ["alice"]
    
    # Conflict türü hatırla
    conflicts = store.recall_episodes(episode_type=EpisodeType.CONFLICT)
    print(f"  Recall CONFLICT type: {len(conflicts)} episodes")
    assert len(conflicts) == 1
    
    # Benzer durum hatırla
    similar = store.recall_similar_episodes("trouble danger")
    print(f"  Similar to 'trouble danger': {len(similar)} episodes")
    assert len(similar) >= 1
    
    print("✅ Episode Storage & Recall PASSED")


def test_memory_decay():
    """Bellek zamanla zayıflama."""
    print("\n=== TEST: Memory Decay ===")
    
    config = MemoryConfig(enable_decay=True, base_decay_rate=0.1)
    store = MemoryStore(config)
    
    # Episode ekle
    episode = Episode(
        what="Test event",
        importance=0.5,
        strength=1.0,
    )
    store.store_episode(episode)
    
    initial_strength = episode.strength
    print(f"  Initial strength: {initial_strength:.2f}")
    
    # Decay uygula (birkaç kez)
    for i in range(5):
        store.apply_decay()
    
    final_strength = episode.strength
    print(f"  After 5 decay cycles: {final_strength:.2f}")
    
    assert final_strength < initial_strength, "Strength should decrease"
    
    print("✅ Memory Decay PASSED")


def test_emotional_memory():
    """Duygusal anılar."""
    print("\n=== TEST: Emotional Memory ===")
    
    store = MemoryStore()
    
    # Duygusal anı oluştur
    memory = EmotionalMemory(
        primary_emotion="fear",
        emotion_intensity=0.9,
        pleasure=-0.8,
        arousal=0.9,
        triggers=["enemy", "loud_noise"],
        is_flashbulb=True,
    )
    
    store.store_emotional_memory(memory)
    
    # Duyguya göre hatırla
    fear_memories = store.recall_by_emotion("fear", min_intensity=0.5)
    print(f"  Fear memories (intensity>0.5): {len(fear_memories)}")
    assert len(fear_memories) == 1
    
    # Trigger'a göre hatırla
    triggered = store.recall_by_trigger("enemy")
    print(f"  Triggered by 'enemy': {len(triggered)}")
    assert len(triggered) == 1
    
    print("✅ Emotional Memory PASSED")


def test_unified_retrieval():
    """Unified memory retrieval."""
    print("\n=== TEST: Unified Retrieval ===")
    
    store = MemoryStore()
    
    # Veri hazırla
    store.store_episode(Episode(
        what="Met Bob at the park",
        who=["bob"],
        importance=0.7,
    ))
    
    store.record_interaction("bob", Interaction(
        interaction_type=InteractionType.CONVERSED,
        outcome_valence=0.5,
    ))
    
    # Unified query
    query = MemoryQuery(
        memory_types=[MemoryType.EPISODIC, MemoryType.RELATIONSHIP],
        agent_ids=["bob"],
        max_results=10,
    )
    
    result = store.retrieve(query)
    
    print(f"  Query for 'bob':")
    print(f"    Total matches: {result.total_matches}")
    print(f"    Items returned: {len(result.items)}")
    print(f"    Query time: {result.query_time_ms:.2f}ms")
    
    assert result.total_matches >= 2  # Episode + Relationship
    
    print("✅ Unified Retrieval PASSED")


def test_is_known_agent():
    """Agent tanıma."""
    print("\n=== TEST: Is Known Agent ===")
    
    store = MemoryStore()
    
    # Bilinmeyen agent
    assert not store.is_known_agent("stranger_1")
    print("  stranger_1: unknown ✓")
    
    # Etkileşim sonrası
    store.record_interaction("stranger_1", Interaction(
        interaction_type=InteractionType.OBSERVED,
    ))
    
    assert store.is_known_agent("stranger_1")
    print("  stranger_1 after interaction: known ✓")
    
    print("✅ Is Known Agent PASSED")


def main():
    print("=" * 60)
    print("UEM v2 - Memory Module Test Suite")
    print("=" * 60)
    
    test_working_memory_capacity()
    test_relationship_memory()
    test_episode_storage_and_recall()
    test_memory_decay()
    test_emotional_memory()
    test_unified_retrieval()
    test_is_known_agent()
    
    print("\n" + "=" * 60)
    print("🎉 ALL MEMORY TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

---

## 8. UYGULAMA SIRASI

### Adım 1: Veri Tipleri (types.py)
```bash
# Dosya oluştur
touch core/memory/types.py
# İçeriği yaz (Section 2'deki kod)
```

### Adım 2: Ana Store (store.py)
```bash
# Dosya oluştur
touch core/memory/store.py
# İçeriği yaz (Section 4'teki kod)
```

### Adım 3: PostgreSQL Setup
```bash
# Docker container
docker run -d --name uem_v2_postgres ...

# Schema uygula
docker exec -i uem_v2_postgres psql -U uem -d uem_v2 < sql/memory_schema.sql
```

### Adım 4: Test
```bash
python tests/unit/test_memory.py
```

### Adım 5: Trust Entegrasyonu
```bash
# Trust manager'ı güncelle
# Orchestrator'ı güncelle
```

### Adım 6: Cycle Entegrasyonu
```bash
# RETRIEVE handler oluştur
# Cycle'a handler'ı ekle
```

### Adım 7: Demo Güncelle
```bash
python demo.py
```

---

## 9. ÖNEMLİ NOTLAR

### 9.1 Memory → Trust Akışı

```
1. Agent algılandığında (PERCEIVE):
   → Memory'den relationship al
   → Trust modülüne başlangıç değeri ver

2. Trust event olduğunda (FEEL):
   → Trust hesapla
   → Memory'ye interaction kaydet
   → Memory'deki trust_score'u güncelle

3. Sonraki karşılaşmada:
   → Memory'den geçmiş al
   → Trust bu geçmişe göre başlasın
```

### 9.2 Episode → Emotional Memory

```
Episode emotional_valence > 0.6 veya arousal > 0.7 ise:
  → Otomatik EmotionalMemory oluştur
  → is_flashbulb = arousal > 0.9
```

### 9.3 Decay Stratejisi

| Memory Type | Decay Rate | Neden |
|-------------|------------|-------|
| Episodic | 1.0x | Normal unutma |
| Relationship | 0.5x | İlişkiler kalıcı |
| Semantic | 0.2x | Bilgi çok kalıcı |
| Emotional | 0.3x (importance bağlı) | Duygusal anılar kalıcı |

---

## 10. GELECEKTEKİ GELİŞTİRMELER

- [ ] Embedding-based similarity search
- [ ] Memory consolidation (sleep cycle simülasyonu)
- [ ] Associative retrieval (spreading activation)
- [ ] Memory reconstruction (gist-based)
- [ ] Source monitoring (nereden biliyorum?)
- [ ] Prospective memory (gelecek planları)
- [ ] Schema/Script memory

---

*Bu doküman sonraki oturumda memory modülü implementasyonu için rehber olarak kullanılacak.*
