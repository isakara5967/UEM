"""
core/memory/store.py

Ana memory store - tum alt sistemleri koordine eder.
UEM v2 - Facade pattern ile unified memory interface.

PostgreSQL persistence integration:
- DB varsa hem in-memory hem DB'ye yazar
- DB yoksa graceful fallback ile sadece in-memory calısır
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime, timedelta
from uuid import UUID
import logging

from .types import (
    MemoryItem, MemoryType, MemoryQuery, RetrievalResult,
    Episode, EpisodeSummary, EpisodeType,
    SemanticFact, ConceptNode,
    EmotionalMemory,
    RelationshipRecord, Interaction, InteractionType, RelationshipType,
    WorkingMemoryItem, SensoryTrace,
    ConsolidationTask,
    Conversation, DialogueTurn,
)
from .conversation import ConversationMemory, ConversationConfig

# PostgreSQL persistence - graceful import
try:
    from .persistence.repository import MemoryRepository, get_session, get_engine
    from .persistence.models import (
        EpisodeModel, RelationshipModel, InteractionModel,
        EpisodeTypeEnum, RelationshipTypeEnum, InteractionTypeEnum,
    )
    PERSISTENCE_AVAILABLE = True
except ImportError:
    PERSISTENCE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """Memory sistem yapilandirmasi."""

    # Working memory
    working_memory_capacity: int = 7      # Miller's Law (7+-2)
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

    # Persistence (disabled by default - in-memory only)
    use_persistence: bool = False
    db_connection_string: str = ""

    # Retrieval
    default_retrieval_limit: int = 10
    min_strength_threshold: float = 0.1

    # Conversation memory
    conversation_context_turns: int = 10
    conversation_max_tokens: int = 4000
    conversation_session_timeout_min: float = 30.0


class MemoryStore:
    """
    Ana memory store - facade pattern.

    Tum memory alt sistemlerini koordine eder:
    - Sensory buffer
    - Working memory
    - Episodic memory
    - Semantic memory
    - Emotional memory
    - Relationship memory
    - Conversation memory
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

        # Conversation memory subsystem
        conv_config = ConversationConfig(
            default_context_turns=self.config.conversation_context_turns,
            max_context_tokens=self.config.conversation_max_tokens,
            session_timeout_minutes=self.config.conversation_session_timeout_min,
        )
        self.conversation = ConversationMemory(conv_config)

        # Stats
        self._stats = {
            "total_episodes": 0,
            "total_relationships": 0,
            "total_retrievals": 0,
            "consolidations": 0,
            "db_writes": 0,
            "db_errors": 0,
        }

        # PostgreSQL persistence - graceful init
        self._repository: Optional['MemoryRepository'] = None
        self._db_session = None
        self._db_available = False
        self._init_repository()

        logger.info(
            f"MemoryStore initialized (persistence: {self._db_available})"
        )

    # ===================================================================
    # POSTGRESQL PERSISTENCE
    # ===================================================================

    def _init_repository(self) -> None:
        """
        Initialize PostgreSQL repository with graceful fallback.

        DB yoksa veya baglanti basarisizsa:
        - Hata vermez, sadece log'lar
        - In-memory devam eder
        """
        if not self.config.use_persistence:
            logger.debug("Persistence disabled in config")
            return

        if not PERSISTENCE_AVAILABLE:
            logger.warning(
                "PostgreSQL persistence not available (sqlalchemy/psycopg2 not installed). "
                "Continuing with in-memory only."
            )
            return

        try:
            # Get connection string from config or default
            db_url = self.config.db_connection_string or None

            # Try to create engine and session
            engine = get_engine(db_url)
            self._db_session = get_session(engine)
            self._repository = MemoryRepository(self._db_session)
            self._db_available = True

            logger.info("PostgreSQL persistence initialized successfully")

        except Exception as e:
            logger.warning(
                f"PostgreSQL connection failed: {e}. "
                "Continuing with in-memory only."
            )
            self._repository = None
            self._db_session = None
            self._db_available = False

    def _persist_episode(self, episode: Episode) -> bool:
        """
        Episode'u PostgreSQL'e kaydet.

        Returns:
            True if saved, False if failed or DB not available
        """
        if not self._db_available or not self._repository:
            return False

        try:
            # Convert domain type to SQLAlchemy model
            model = EpisodeModel(
                id=UUID(episode.id),
                what=episode.what,
                location=episode.where,
                occurred_at=episode.when,
                participants=episode.who,
                why=episode.why,
                how=episode.how,
                episode_type=EpisodeTypeEnum(episode.episode_type.value),
                duration_seconds=episode.duration_seconds,
                outcome=episode.outcome,
                outcome_valence=episode.outcome_valence,
                self_emotion_during=episode.self_emotion_during,
                self_emotion_after=episode.self_emotion_after,
                pleasure=episode.pad_state.get("pleasure") if episode.pad_state else None,
                arousal=episode.pad_state.get("arousal") if episode.pad_state else None,
                dominance=episode.pad_state.get("dominance") if episode.pad_state else None,
                strength=episode.strength,
                importance=episode.importance,
                emotional_valence=episode.emotional_valence,
                emotional_arousal=episode.emotional_arousal,
                tags=episode.tags,
                context=episode.context,
            )

            self._repository.save_episode(model)
            self._stats["db_writes"] += 1
            logger.debug(f"Episode persisted to DB: {episode.id}")
            return True

        except Exception as e:
            self._stats["db_errors"] += 1
            logger.warning(f"Failed to persist episode {episode.id}: {e}")
            return False

    def _persist_relationship(self, record: RelationshipRecord) -> bool:
        """
        Relationship'i PostgreSQL'e kaydet veya guncelle.

        Returns:
            True if saved, False if failed or DB not available
        """
        if not self._db_available or not self._repository:
            return False

        try:
            # Get or create in DB
            db_rel = self._repository.get_or_create_relationship(record.agent_id)

            # Update fields
            db_rel.agent_name = record.agent_name or db_rel.agent_name
            db_rel.relationship_type = RelationshipTypeEnum(record.relationship_type.value)
            db_rel.total_interactions = record.total_interactions
            db_rel.positive_interactions = record.positive_interactions
            db_rel.negative_interactions = record.negative_interactions
            db_rel.neutral_interactions = record.neutral_interactions
            db_rel.trust_score = record.trust_score
            db_rel.betrayal_count = record.betrayal_count
            db_rel.last_betrayal = record.last_betrayal
            db_rel.overall_sentiment = record.overall_sentiment
            db_rel.last_interaction = record.last_interaction
            if record.last_interaction_type:
                db_rel.last_interaction_type = InteractionTypeEnum(record.last_interaction_type.value)
            db_rel.strength = record.strength
            db_rel.importance = record.importance
            db_rel.notes = record.notes

            self._repository.session.commit()
            self._stats["db_writes"] += 1
            logger.debug(f"Relationship persisted to DB: {record.agent_id}")
            return True

        except Exception as e:
            self._stats["db_errors"] += 1
            logger.warning(f"Failed to persist relationship {record.agent_id}: {e}")
            try:
                self._repository.session.rollback()
            except Exception:
                pass
            return False

    def _persist_interaction(
        self,
        agent_id: str,
        interaction: Interaction,
    ) -> bool:
        """
        Interaction'ı PostgreSQL'e kaydet.

        Returns:
            True if saved, False if failed or DB not available
        """
        if not self._db_available or not self._repository:
            return False

        try:
            # Get relationship from DB
            db_rel = self._repository.get_or_create_relationship(agent_id)

            # Create interaction model
            model = InteractionModel(
                relationship_id=db_rel.id,
                episode_id=UUID(interaction.episode_id) if interaction.episode_id else None,
                interaction_type=InteractionTypeEnum(interaction.interaction_type.value),
                context=interaction.context,
                outcome=interaction.outcome,
                outcome_valence=interaction.outcome_valence,
                emotional_impact=interaction.emotional_impact,
                trust_impact=interaction.trust_impact,
                occurred_at=interaction.timestamp,
            )

            self._repository.save_interaction(model, update_relationship=False)

            # Update relationship stats (trust_score, counts, etc.)
            self._repository.update_relationship_stats(
                agent_id=agent_id,
                interaction_type=InteractionTypeEnum(interaction.interaction_type.value),
                trust_delta=interaction.trust_impact,
            )

            self._stats["db_writes"] += 1
            logger.debug(f"Interaction persisted to DB for agent: {agent_id}")
            return True

        except Exception as e:
            self._stats["db_errors"] += 1
            logger.warning(f"Failed to persist interaction for {agent_id}: {e}")
            try:
                self._repository.session.rollback()
            except Exception:
                pass
            return False

    def _load_relationship_from_db(self, agent_id: str) -> Optional[RelationshipRecord]:
        """
        DB'den relationship yükle.

        Returns:
            RelationshipRecord if found, None otherwise
        """
        if not self._db_available or not self._repository:
            return None

        try:
            db_rel = self._repository.get_relationship_by_agent(agent_id)
            if not db_rel:
                return None

            # Convert to domain type
            record = RelationshipRecord(
                id=str(db_rel.id),
                agent_id=db_rel.agent_id,
                agent_name=db_rel.agent_name or "",
                relationship_type=RelationshipType(db_rel.relationship_type.value),
                relationship_start=db_rel.relationship_start or datetime.now(),
                total_interactions=db_rel.total_interactions or 0,
                positive_interactions=db_rel.positive_interactions or 0,
                negative_interactions=db_rel.negative_interactions or 0,
                neutral_interactions=db_rel.neutral_interactions or 0,
                trust_score=db_rel.trust_score or 0.5,
                betrayal_count=db_rel.betrayal_count or 0,
                last_betrayal=db_rel.last_betrayal,
                overall_sentiment=db_rel.overall_sentiment or 0.0,
                last_interaction=db_rel.last_interaction,
                last_interaction_type=InteractionType(db_rel.last_interaction_type.value) if db_rel.last_interaction_type else None,
                strength=db_rel.strength or 1.0,
                importance=db_rel.importance or 0.5,
                notes=db_rel.notes or [],
            )

            logger.debug(f"Relationship loaded from DB: {agent_id}")
            return record

        except Exception as e:
            logger.warning(f"Failed to load relationship {agent_id} from DB: {e}")
            return None

    def close(self) -> None:
        """Close database session if open."""
        if self._db_session:
            try:
                self._db_session.close()
                logger.debug("Database session closed")
            except Exception as e:
                logger.warning(f"Error closing database session: {e}")
            finally:
                self._db_session = None
                self._repository = None
                self._db_available = False

    # ===================================================================
    # SENSORY BUFFER
    # ===================================================================

    def buffer_sensory(self, trace: SensoryTrace) -> None:
        """Duyusal izi buffer'a ekle."""
        self._sensory_buffer.append(trace)

        # Buffer boyut kontrolu
        if len(self._sensory_buffer) > self.config.sensory_buffer_size:
            # Eski ve unattended olanlari sil
            self._sensory_buffer = [
                t for t in self._sensory_buffer
                if t.attended or (datetime.now() - t.created_at).total_seconds() * 1000 < t.duration_ms
            ][:self.config.sensory_buffer_size]

    def get_sensory_buffer(self) -> List[SensoryTrace]:
        """Aktif sensory buffer'i getir."""
        now = datetime.now()
        return [
            t for t in self._sensory_buffer
            if (now - t.created_at).total_seconds() * 1000 < t.duration_ms
        ]

    # ===================================================================
    # WORKING MEMORY
    # ===================================================================

    def hold_in_working(self, item: WorkingMemoryItem) -> bool:
        """
        Working memory'ye oge ekle.

        Returns:
            True if added, False if capacity full
        """
        # Suresi dolmus ogeleri temizle
        self._clean_working_memory()

        # Kapasite kontrolu
        if len(self._working_memory) >= self.config.working_memory_capacity:
            # En dusuk priority'yi cikar
            if item.priority > min(i.priority for i in self._working_memory):
                self._working_memory.sort(key=lambda x: x.priority)
                removed = self._working_memory.pop(0)
                # Consolidation'a gonder
                self._queue_consolidation(removed)
            else:
                return False

        self._working_memory.append(item)
        return True

    def get_working_memory(self) -> List[WorkingMemoryItem]:
        """Working memory icerigini getir."""
        self._clean_working_memory()
        return list(self._working_memory)

    def clear_working_memory(self) -> List[WorkingMemoryItem]:
        """Working memory'yi temizle (cycle sonu)."""
        items = list(self._working_memory)
        self._working_memory.clear()

        # Onemli olanlari consolidation'a gonder
        for item in items:
            if item.importance > self.config.consolidation_threshold:
                self._queue_consolidation(item)

        return items

    def _clean_working_memory(self) -> None:
        """Suresi dolmus working memory ogelerini temizle."""
        now = datetime.now()
        cutoff = timedelta(seconds=self.config.working_memory_duration_sec)

        self._working_memory = [
            item for item in self._working_memory
            if now - item.created_at < cutoff
        ]

    # ===================================================================
    # EPISODIC MEMORY
    # ===================================================================

    def store_episode(self, episode: Episode) -> str:
        """
        Episode kaydet.

        Hem in-memory hem PostgreSQL'e kaydeder (DB varsa).

        Returns:
            Episode ID
        """
        # 1. In-memory kayıt (her zaman)
        self._episodes[episode.id] = episode
        self._stats["total_episodes"] += 1

        # 2. PostgreSQL kayıt (varsa)
        self._persist_episode(episode)

        # 3. Iliskili agent'larin relationship'lerini guncelle
        for agent_id in episode.who:
            self._update_relationship_from_episode(agent_id, episode)

        # 4. Duygusal yogunluk yuksekse emotional memory olustur
        if abs(episode.emotional_valence) > 0.6 or episode.emotional_arousal > 0.7:
            self._create_emotional_memory_from_episode(episode)

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
        Episode'lari hatirla (recall).

        Args:
            agent_id: Belirli bir agent ile ilgili
            episode_type: Belirli tur
            time_range: (start, end) datetime tuple
            min_importance: Minimum onem
            limit: Maksimum sonuc
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

        # Onem ve guncellige gore sirala
        results.sort(key=lambda e: (e.importance * 0.4 + e.strength * 0.6), reverse=True)

        # Touch (erisim kaydi)
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
        Benzer durumlari hatirla.
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

    # ===================================================================
    # RELATIONSHIP MEMORY (Trust entegrasyonu icin kritik!)
    # ===================================================================

    def get_relationship(self, agent_id: str) -> RelationshipRecord:
        """
        Agent ile iliski kaydini getir (yoksa olustur).

        Trust modulu bu metodu kullanmali!

        Sıralama:
        1. In-memory'de varsa döndür
        2. DB'de varsa yükle ve in-memory'ye de koy
        3. Hiçbir yerde yoksa yeni oluştur
        """
        # 1. In-memory'de var mı?
        if agent_id in self._relationships:
            return self._relationships[agent_id]

        # 2. DB'den yüklemeyi dene
        db_record = self._load_relationship_from_db(agent_id)
        if db_record:
            self._relationships[agent_id] = db_record
            return db_record

        # 3. Yeni oluştur
        new_record = RelationshipRecord(
            agent_id=agent_id,
            relationship_type=RelationshipType.STRANGER,
        )
        self._relationships[agent_id] = new_record
        self._stats["total_relationships"] += 1

        # DB'ye de kaydet
        self._persist_relationship(new_record)

        return new_record

    def update_relationship(
        self,
        agent_id: str,
        relationship_type: Optional[RelationshipType] = None,
        agent_name: Optional[str] = None,
    ) -> RelationshipRecord:
        """Iliski kaydini guncelle."""
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
        Agent ile etkilesim kaydet.

        Trust modulu her trust event'i burada da kaydetmeli!

        Hem in-memory hem PostgreSQL'e kaydeder (DB varsa).
        """
        # 1. In-memory kayıt
        record = self.get_relationship(agent_id)
        record.add_interaction(interaction)

        # 2. PostgreSQL kayıt (varsa)
        self._persist_interaction(agent_id, interaction)

        # 3. Relationship'in güncel halini de DB'ye kaydet
        self._persist_relationship(record)

        return record

    def get_interaction_history(
        self,
        agent_id: str,
        limit: int = 20,
        interaction_type: Optional[InteractionType] = None,
    ) -> List[Interaction]:
        """Agent ile etkilesim gecmisi."""
        record = self.get_relationship(agent_id)

        interactions = record.interactions
        if interaction_type:
            interactions = [i for i in interactions if i.interaction_type == interaction_type]

        return interactions[-limit:]

    def is_known_agent(self, agent_id: str) -> bool:
        """Bu agent'i taniyor muyuz?"""
        if agent_id not in self._relationships:
            return False

        record = self._relationships[agent_id]
        return record.total_interactions > 0

    def get_all_relationships(
        self,
        relationship_type: Optional[RelationshipType] = None,
    ) -> List[RelationshipRecord]:
        """Tum iliskileri getir."""
        records = list(self._relationships.values())

        if relationship_type:
            records = [r for r in records if r.relationship_type == relationship_type]

        return records

    def _update_relationship_from_episode(
        self,
        agent_id: str,
        episode: Episode,
    ) -> None:
        """Episode'dan relationship guncelle."""
        record = self.get_relationship(agent_id)

        # Episode'dan interaction cikar
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
        """Episode'dan interaction type cikar."""
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

    # ===================================================================
    # SEMANTIC MEMORY
    # ===================================================================

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

    # ===================================================================
    # EMOTIONAL MEMORY
    # ===================================================================

    def store_emotional_memory(self, memory: EmotionalMemory) -> str:
        """Duygusal ani kaydet."""
        self._emotional_memories[memory.id] = memory
        return memory.id

    def recall_by_emotion(
        self,
        emotion: str,
        min_intensity: float = 0.3,
        limit: int = 10,
    ) -> List[EmotionalMemory]:
        """Belirli duyguyla iliskili anilari hatirla."""
        results = [
            m for m in self._emotional_memories.values()
            if m.primary_emotion == emotion and m.emotion_intensity >= min_intensity
        ]

        results.sort(key=lambda m: m.emotion_intensity, reverse=True)
        return results[:limit]

    def recall_by_trigger(self, trigger: str) -> List[EmotionalMemory]:
        """Tetikleyiciye gore anilari hatirla."""
        return [
            m for m in self._emotional_memories.values()
            if trigger in m.triggers
        ]

    def _create_emotional_memory_from_episode(self, episode: Episode) -> None:
        """Episode'dan emotional memory olustur."""
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

    # ===================================================================
    # CONSOLIDATION
    # ===================================================================

    def _queue_consolidation(self, item: WorkingMemoryItem) -> None:
        """Consolidation kuyruguna ekle."""
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
        Consolidation calistir (background task olarak).

        Returns:
            Islenen task sayisi
        """
        processed = 0

        while self._consolidation_queue:
            task = self._consolidation_queue.pop(0)

            # TODO: Gercek consolidation logic
            # Working memory item'i episode'a donustur

            task.status = "completed"
            processed += 1
            self._stats["consolidations"] += 1

        return processed

    # ===================================================================
    # DECAY
    # ===================================================================

    def apply_decay(self) -> Dict[str, int]:
        """
        Tum belleklere decay uygula.

        Returns:
            Her memory type icin decay uygulanan oge sayisi
        """
        if not self.config.enable_decay:
            return {}

        rate = self.config.base_decay_rate
        counts = {}

        # Episodes
        for episode in self._episodes.values():
            episode.decay(rate)
        counts["episodes"] = len(self._episodes)

        # Relationships (daha yavas)
        for record in self._relationships.values():
            record.decay(rate * 0.5)
        counts["relationships"] = len(self._relationships)

        # Semantic (en yavas)
        for fact in self._semantic_facts.values():
            fact.decay(rate * 0.2)
        counts["semantic"] = len(self._semantic_facts)

        # Emotional (importance'a cok bagli)
        for memory in self._emotional_memories.values():
            memory.decay(rate * 0.3)
        counts["emotional"] = len(self._emotional_memories)

        # Unutulanlari temizle
        self._cleanup_forgotten()

        return counts

    def _cleanup_forgotten(self) -> None:
        """Unutulan ogeleri temizle."""
        threshold = self.config.min_strength_threshold

        # Episodes
        self._episodes = {
            k: v for k, v in self._episodes.items()
            if not v.is_forgotten(threshold)
        }

        # Semantic (daha dusuk threshold)
        self._semantic_facts = {
            k: v for k, v in self._semantic_facts.items()
            if not v.is_forgotten(threshold * 0.5)
        }

        # Emotional (daha dusuk threshold - duygusal anilar daha kalici)
        self._emotional_memories = {
            k: v for k, v in self._emotional_memories.items()
            if not v.is_forgotten(threshold * 0.3)
        }

        # Relationships never fully forgotten (just marked inactive)

    # ===================================================================
    # UNIFIED RETRIEVAL
    # ===================================================================

    def retrieve(self, query: MemoryQuery) -> RetrievalResult:
        """
        Unified memory retrieval.

        Cognitive cycle RETRIEVE fazi bu metodu kullanmali.
        """
        import time
        start = time.perf_counter()

        results = []
        scores = {}

        # Memory type'lara gore sorgula
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

    # ===================================================================
    # STATS & DEBUG
    # ===================================================================

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
            **{f"conversation_{k}": v for k, v in self.conversation.stats.items()},
        }

    def debug_dump(self) -> Dict[str, Any]:
        """Debug icin tam dump."""
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


# ========================================================================
# FACTORY & SINGLETON
# ========================================================================

_memory_store: Optional[MemoryStore] = None


def get_memory_store(config: Optional[MemoryConfig] = None) -> MemoryStore:
    """Memory store singleton."""
    global _memory_store

    if _memory_store is None:
        _memory_store = MemoryStore(config)

    return _memory_store


def reset_memory_store() -> None:
    """Reset memory store singleton (test icin)."""
    global _memory_store
    _memory_store = None


def create_memory_store(config: Optional[MemoryConfig] = None) -> MemoryStore:
    """Yeni memory store olustur (test icin)."""
    return MemoryStore(config)
