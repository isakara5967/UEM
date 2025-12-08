"""
core/memory/persistence/repository.py

Repository pattern for Memory module PostgreSQL persistence.

Provides CRUD operations and queries for memory entities.
Does NOT integrate with MemoryStore yet - standalone persistence layer.
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from .models import (
    Base,
    EpisodeModel,
    RelationshipModel,
    InteractionModel,
    SemanticFactModel,
    EmotionalMemoryModel,
    TrustHistoryModel,
    EpisodeTypeEnum,
    RelationshipTypeEnum,
    InteractionTypeEnum,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════

# Default connection string (can be overridden via environment)
DEFAULT_DATABASE_URL = "postgresql://uem:uem_secret@localhost:5432/uem_v2"

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.environ.get("UEM_DATABASE_URL", DEFAULT_DATABASE_URL)


def get_engine(database_url: Optional[str] = None) -> Engine:
    """
    Get or create SQLAlchemy engine.

    Args:
        database_url: Override database URL (optional)

    Returns:
        SQLAlchemy Engine
    """
    global _engine

    if _engine is None or database_url:
        url = database_url or get_database_url()
        _engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=os.environ.get("UEM_SQL_ECHO", "").lower() == "true",
        )
        logger.info(f"Database engine created for {url.split('@')[-1]}")

    return _engine


def get_session(engine: Optional[Engine] = None) -> Session:
    """
    Get a new database session.

    Args:
        engine: SQLAlchemy engine (optional, uses global if not provided)

    Returns:
        SQLAlchemy Session
    """
    global _SessionLocal

    if _SessionLocal is None or engine:
        eng = engine or get_engine()
        _SessionLocal = sessionmaker(bind=eng, autocommit=False, autoflush=False)

    return _SessionLocal()


def init_db(engine: Optional[Engine] = None) -> None:
    """
    Initialize database tables.

    Note: Prefer using sql/memory_schema.sql for production.
    This is for testing/development convenience.
    """
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
    logger.info("Database tables initialized")


# ═══════════════════════════════════════════════════════════════════════════
# REPOSITORY
# ═══════════════════════════════════════════════════════════════════════════

class MemoryRepository:
    """
    Repository for Memory module persistence operations.

    Usage:
        session = get_session()
        repo = MemoryRepository(session)

        # Save episode
        episode = repo.save_episode(episode_model)

        # Query
        episodes = repo.find_episodes_by_participant("alice")

        # Don't forget to close session
        session.close()
    """

    def __init__(self, session: Session):
        self.session = session

    # ═══════════════════════════════════════════════════════════════════
    # EPISODES
    # ═══════════════════════════════════════════════════════════════════

    def save_episode(self, episode: EpisodeModel) -> EpisodeModel:
        """Save or update an episode."""
        self.session.add(episode)
        self.session.commit()
        self.session.refresh(episode)
        return episode

    def get_episode(self, episode_id: UUID) -> Optional[EpisodeModel]:
        """Get episode by ID."""
        return self.session.query(EpisodeModel).filter(
            EpisodeModel.id == episode_id
        ).first()

    def find_episodes_by_participant(
        self,
        agent_id: str,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[EpisodeModel]:
        """Find episodes involving a specific agent."""
        return self.session.query(EpisodeModel).filter(
            EpisodeModel.participants.contains([agent_id]),
            EpisodeModel.importance >= min_importance,
        ).order_by(
            desc(EpisodeModel.occurred_at)
        ).limit(limit).all()

    def find_recent_episodes(
        self,
        hours: int = 24,
        limit: int = 20,
    ) -> List[EpisodeModel]:
        """Find recent episodes."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.session.query(EpisodeModel).filter(
            EpisodeModel.occurred_at >= cutoff
        ).order_by(
            desc(EpisodeModel.occurred_at)
        ).limit(limit).all()

    def find_episodes_by_type(
        self,
        episode_type: EpisodeTypeEnum,
        limit: int = 10,
    ) -> List[EpisodeModel]:
        """Find episodes by type."""
        return self.session.query(EpisodeModel).filter(
            EpisodeModel.episode_type == episode_type
        ).order_by(
            desc(EpisodeModel.occurred_at)
        ).limit(limit).all()

    def find_important_episodes(
        self,
        min_importance: float = 0.7,
        limit: int = 10,
    ) -> List[EpisodeModel]:
        """Find high-importance episodes."""
        return self.session.query(EpisodeModel).filter(
            EpisodeModel.importance >= min_importance,
            EpisodeModel.strength > 0.1,
        ).order_by(
            desc(EpisodeModel.importance)
        ).limit(limit).all()

    def touch_episode(self, episode_id: UUID) -> None:
        """Mark episode as accessed (increases strength)."""
        episode = self.get_episode(episode_id)
        if episode:
            episode.last_accessed = datetime.utcnow()
            episode.access_count += 1
            episode.strength = min(1.0, episode.strength + 0.05)
            self.session.commit()

    def delete_episode(self, episode_id: UUID) -> bool:
        """Delete an episode."""
        episode = self.get_episode(episode_id)
        if episode:
            self.session.delete(episode)
            self.session.commit()
            return True
        return False

    # ═══════════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════════

    def save_relationship(self, relationship: RelationshipModel) -> RelationshipModel:
        """Save or update a relationship."""
        self.session.add(relationship)
        self.session.commit()
        self.session.refresh(relationship)
        return relationship

    def get_relationship(self, relationship_id: UUID) -> Optional[RelationshipModel]:
        """Get relationship by ID."""
        return self.session.query(RelationshipModel).filter(
            RelationshipModel.id == relationship_id
        ).first()

    def get_relationship_by_agent(self, agent_id: str) -> Optional[RelationshipModel]:
        """Get relationship by agent ID."""
        return self.session.query(RelationshipModel).filter(
            RelationshipModel.agent_id == agent_id
        ).first()

    def get_or_create_relationship(self, agent_id: str) -> RelationshipModel:
        """Get existing relationship or create new one."""
        relationship = self.get_relationship_by_agent(agent_id)
        if relationship is None:
            relationship = RelationshipModel(agent_id=agent_id)
            self.session.add(relationship)
            self.session.commit()
            self.session.refresh(relationship)
        return relationship

    def find_relationships_by_type(
        self,
        relationship_type: RelationshipTypeEnum,
        limit: int = 20,
    ) -> List[RelationshipModel]:
        """Find relationships by type."""
        return self.session.query(RelationshipModel).filter(
            RelationshipModel.relationship_type == relationship_type
        ).order_by(
            desc(RelationshipModel.last_interaction)
        ).limit(limit).all()

    def find_high_trust_relationships(
        self,
        min_trust: float = 0.7,
        limit: int = 10,
    ) -> List[RelationshipModel]:
        """Find high-trust relationships."""
        return self.session.query(RelationshipModel).filter(
            RelationshipModel.trust_score >= min_trust
        ).order_by(
            desc(RelationshipModel.trust_score)
        ).limit(limit).all()

    def find_low_trust_relationships(
        self,
        max_trust: float = 0.3,
        limit: int = 10,
    ) -> List[RelationshipModel]:
        """Find low-trust relationships."""
        return self.session.query(RelationshipModel).filter(
            RelationshipModel.trust_score <= max_trust
        ).order_by(
            RelationshipModel.trust_score
        ).limit(limit).all()

    def update_relationship_stats(
        self,
        agent_id: str,
        interaction_type: InteractionTypeEnum,
        trust_delta: float = 0.0,
    ) -> Optional[RelationshipModel]:
        """Update relationship statistics after an interaction."""
        relationship = self.get_or_create_relationship(agent_id)

        relationship.total_interactions += 1
        relationship.last_interaction = datetime.utcnow()
        relationship.last_interaction_type = interaction_type

        # Categorize interaction
        positive_types = {
            InteractionTypeEnum.helped, InteractionTypeEnum.cooperated,
            InteractionTypeEnum.shared, InteractionTypeEnum.protected,
            InteractionTypeEnum.celebrated, InteractionTypeEnum.comforted,
        }
        negative_types = {
            InteractionTypeEnum.harmed, InteractionTypeEnum.betrayed,
            InteractionTypeEnum.threatened, InteractionTypeEnum.attacked,
        }

        if interaction_type in positive_types:
            relationship.positive_interactions += 1
        elif interaction_type in negative_types:
            relationship.negative_interactions += 1
            if interaction_type == InteractionTypeEnum.betrayed:
                relationship.betrayal_count += 1
                relationship.last_betrayal = datetime.utcnow()
        else:
            relationship.neutral_interactions += 1

        # Update trust
        relationship.trust_score = max(0.0, min(1.0, relationship.trust_score + trust_delta))

        # Update sentiment
        total = relationship.total_interactions
        if total > 0:
            relationship.overall_sentiment = (
                (relationship.positive_interactions - relationship.negative_interactions) / total
            )

        self.session.commit()
        return relationship

    # ═══════════════════════════════════════════════════════════════════
    # INTERACTIONS
    # ═══════════════════════════════════════════════════════════════════

    def save_interaction(
        self,
        interaction: InteractionModel,
        update_relationship: bool = True,
    ) -> InteractionModel:
        """
        Save an interaction and optionally update relationship stats.

        Args:
            interaction: The interaction to save
            update_relationship: If True, updates relationship trust_score with trust_impact

        Returns:
            Saved interaction
        """
        self.session.add(interaction)
        self.session.commit()
        self.session.refresh(interaction)

        # Update relationship trust_score if trust_impact is set
        if update_relationship and interaction.trust_impact:
            relationship = self.session.query(RelationshipModel).filter(
                RelationshipModel.id == interaction.relationship_id
            ).first()

            if relationship:
                # Apply trust_impact to trust_score
                new_trust = relationship.trust_score + interaction.trust_impact
                relationship.trust_score = max(0.0, min(1.0, new_trust))

                # Update interaction counts
                relationship.total_interactions += 1
                relationship.last_interaction = interaction.occurred_at
                relationship.last_interaction_type = interaction.interaction_type

                # Categorize interaction
                positive_types = {
                    InteractionTypeEnum.helped, InteractionTypeEnum.cooperated,
                    InteractionTypeEnum.shared, InteractionTypeEnum.protected,
                    InteractionTypeEnum.celebrated, InteractionTypeEnum.comforted,
                }
                negative_types = {
                    InteractionTypeEnum.harmed, InteractionTypeEnum.betrayed,
                    InteractionTypeEnum.threatened, InteractionTypeEnum.attacked,
                }

                if interaction.interaction_type in positive_types:
                    relationship.positive_interactions += 1
                elif interaction.interaction_type in negative_types:
                    relationship.negative_interactions += 1
                    if interaction.interaction_type == InteractionTypeEnum.betrayed:
                        relationship.betrayal_count += 1
                        relationship.last_betrayal = interaction.occurred_at
                else:
                    relationship.neutral_interactions += 1

                # Update sentiment
                total = relationship.total_interactions
                if total > 0:
                    relationship.overall_sentiment = (
                        (relationship.positive_interactions - relationship.negative_interactions) / total
                    )

                self.session.commit()

        return interaction

    def find_interactions_for_relationship(
        self,
        relationship_id: UUID,
        limit: int = 20,
    ) -> List[InteractionModel]:
        """Find interactions for a relationship."""
        return self.session.query(InteractionModel).filter(
            InteractionModel.relationship_id == relationship_id
        ).order_by(
            desc(InteractionModel.occurred_at)
        ).limit(limit).all()

    def find_recent_interactions(
        self,
        hours: int = 24,
        limit: int = 50,
    ) -> List[InteractionModel]:
        """Find recent interactions."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.session.query(InteractionModel).filter(
            InteractionModel.occurred_at >= cutoff
        ).order_by(
            desc(InteractionModel.occurred_at)
        ).limit(limit).all()

    # ═══════════════════════════════════════════════════════════════════
    # SEMANTIC FACTS
    # ═══════════════════════════════════════════════════════════════════

    def save_fact(self, fact: SemanticFactModel) -> SemanticFactModel:
        """Save or update a semantic fact."""
        # Check for existing
        existing = self.session.query(SemanticFactModel).filter(
            SemanticFactModel.subject == fact.subject,
            SemanticFactModel.predicate == fact.predicate,
            SemanticFactModel.object == fact.object,
        ).first()

        if existing:
            existing.confidence = fact.confidence
            existing.strength = min(1.0, existing.strength + 0.1)
            existing.access_count += 1
            self.session.commit()
            return existing

        self.session.add(fact)
        self.session.commit()
        self.session.refresh(fact)
        return fact

    def find_facts_by_subject(
        self,
        subject: str,
        limit: int = 20,
    ) -> List[SemanticFactModel]:
        """Find facts about a subject."""
        return self.session.query(SemanticFactModel).filter(
            SemanticFactModel.subject == subject
        ).order_by(
            desc(SemanticFactModel.confidence)
        ).limit(limit).all()

    def find_facts_by_predicate(
        self,
        predicate: str,
        limit: int = 20,
    ) -> List[SemanticFactModel]:
        """Find facts with a predicate."""
        return self.session.query(SemanticFactModel).filter(
            SemanticFactModel.predicate == predicate
        ).limit(limit).all()

    def query_facts(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
    ) -> List[SemanticFactModel]:
        """Query facts by any combination of S-P-O."""
        query = self.session.query(SemanticFactModel)

        if subject:
            query = query.filter(SemanticFactModel.subject == subject)
        if predicate:
            query = query.filter(SemanticFactModel.predicate == predicate)
        if obj:
            query = query.filter(SemanticFactModel.object == obj)

        return query.all()

    # ═══════════════════════════════════════════════════════════════════
    # EMOTIONAL MEMORIES
    # ═══════════════════════════════════════════════════════════════════

    def save_emotional_memory(
        self,
        memory: EmotionalMemoryModel,
    ) -> EmotionalMemoryModel:
        """Save an emotional memory."""
        self.session.add(memory)
        self.session.commit()
        self.session.refresh(memory)
        return memory

    def find_emotional_memories_by_emotion(
        self,
        emotion: str,
        limit: int = 10,
    ) -> List[EmotionalMemoryModel]:
        """Find emotional memories by primary emotion."""
        return self.session.query(EmotionalMemoryModel).filter(
            EmotionalMemoryModel.primary_emotion == emotion
        ).order_by(
            desc(EmotionalMemoryModel.emotion_intensity)
        ).limit(limit).all()

    def find_flashbulb_memories(
        self,
        limit: int = 10,
    ) -> List[EmotionalMemoryModel]:
        """Find flashbulb (highly significant) memories."""
        return self.session.query(EmotionalMemoryModel).filter(
            EmotionalMemoryModel.is_flashbulb == True
        ).order_by(
            desc(EmotionalMemoryModel.importance)
        ).limit(limit).all()

    def find_intense_emotional_memories(
        self,
        min_intensity: float = 0.7,
        limit: int = 10,
    ) -> List[EmotionalMemoryModel]:
        """Find highly intense emotional memories."""
        return self.session.query(EmotionalMemoryModel).filter(
            EmotionalMemoryModel.emotion_intensity >= min_intensity
        ).order_by(
            desc(EmotionalMemoryModel.emotion_intensity)
        ).limit(limit).all()

    # ═══════════════════════════════════════════════════════════════════
    # TRUST HISTORY
    # ═══════════════════════════════════════════════════════════════════

    def save_trust_history(self, history: TrustHistoryModel) -> TrustHistoryModel:
        """Save a trust history entry."""
        self.session.add(history)
        self.session.commit()
        self.session.refresh(history)
        return history

    def record_trust_change(
        self,
        agent_id: str,
        new_trust: float,
        previous_trust: float,
        event_type: Optional[str] = None,
        event_context: Optional[str] = None,
    ) -> TrustHistoryModel:
        """Record a trust value change."""
        relationship = self.get_or_create_relationship(agent_id)

        history = TrustHistoryModel(
            relationship_id=relationship.id,
            agent_id=agent_id,
            trust_value=new_trust,
            previous_value=previous_trust,
            delta=new_trust - previous_trust,
            event_type=event_type,
            event_context=event_context,
        )

        return self.save_trust_history(history)

    def get_trust_history(
        self,
        agent_id: str,
        limit: int = 20,
    ) -> List[TrustHistoryModel]:
        """Get trust history for an agent."""
        return self.session.query(TrustHistoryModel).filter(
            TrustHistoryModel.agent_id == agent_id
        ).order_by(
            desc(TrustHistoryModel.recorded_at)
        ).limit(limit).all()

    # ═══════════════════════════════════════════════════════════════════
    # DECAY & CLEANUP
    # ═══════════════════════════════════════════════════════════════════

    def apply_decay(self, decay_rate: float = 0.01) -> Dict[str, int]:
        """
        Apply memory decay to all memory types.

        Returns count of affected rows per type.
        """
        results = {}

        # Episodes
        episode_count = self.session.query(EpisodeModel).filter(
            EpisodeModel.strength > 0
        ).update({
            EpisodeModel.strength: func.greatest(
                0,
                EpisodeModel.strength - decay_rate * (1 - EpisodeModel.importance * 0.5)
            )
        })
        results["episodes"] = episode_count

        # Relationships (slower decay)
        rel_count = self.session.query(RelationshipModel).filter(
            RelationshipModel.strength > 0
        ).update({
            RelationshipModel.strength: func.greatest(
                0,
                RelationshipModel.strength - decay_rate * 0.5 * (1 - RelationshipModel.importance * 0.5)
            )
        })
        results["relationships"] = rel_count

        # Semantic facts (slowest decay)
        sem_count = self.session.query(SemanticFactModel).filter(
            SemanticFactModel.strength > 0
        ).update({
            SemanticFactModel.strength: func.greatest(
                0,
                SemanticFactModel.strength - decay_rate * 0.2 * (1 - SemanticFactModel.importance * 0.5)
            )
        })
        results["semantic_facts"] = sem_count

        # Emotional memories
        emo_count = self.session.query(EmotionalMemoryModel).filter(
            EmotionalMemoryModel.strength > 0
        ).update({
            EmotionalMemoryModel.strength: func.greatest(
                0,
                EmotionalMemoryModel.strength - decay_rate * 0.3 * (1 - EmotionalMemoryModel.importance * 0.7)
            )
        })
        results["emotional_memories"] = emo_count

        self.session.commit()
        return results

    def cleanup_weak_memories(self, strength_threshold: float = 0.1) -> Dict[str, int]:
        """
        Remove memories below strength threshold.

        Note: Relationships are never deleted, only episodes and facts.
        """
        results = {}

        # Episodes (keep important ones)
        ep_count = self.session.query(EpisodeModel).filter(
            EpisodeModel.strength < strength_threshold,
            EpisodeModel.importance < 0.5,
        ).delete()
        results["episodes"] = ep_count

        # Semantic facts
        sem_count = self.session.query(SemanticFactModel).filter(
            SemanticFactModel.strength < strength_threshold * 0.5
        ).delete()
        results["semantic_facts"] = sem_count

        # Emotional memories (keep flashbulb)
        emo_count = self.session.query(EmotionalMemoryModel).filter(
            EmotionalMemoryModel.strength < strength_threshold * 0.3,
            EmotionalMemoryModel.is_flashbulb == False,
        ).delete()
        results["emotional_memories"] = emo_count

        self.session.commit()
        return results

    # ═══════════════════════════════════════════════════════════════════
    # STATS
    # ═══════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_episodes": self.session.query(EpisodeModel).count(),
            "total_relationships": self.session.query(RelationshipModel).count(),
            "total_interactions": self.session.query(InteractionModel).count(),
            "total_semantic_facts": self.session.query(SemanticFactModel).count(),
            "total_emotional_memories": self.session.query(EmotionalMemoryModel).count(),
            "avg_episode_strength": self.session.query(
                func.avg(EpisodeModel.strength)
            ).scalar() or 0,
            "avg_relationship_trust": self.session.query(
                func.avg(RelationshipModel.trust_score)
            ).scalar() or 0.5,
        }

    # ═══════════════════════════════════════════════════════════════════
    # CONTEXT MANAGER
    # ═══════════════════════════════════════════════════════════════════

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()
