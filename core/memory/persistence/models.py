"""
core/memory/persistence/models.py

SQLAlchemy models for Memory module PostgreSQL persistence.

Maps to sql/memory_schema.sql tables.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
import enum

from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean,
    DateTime, ForeignKey, Enum, ARRAY, JSON,
    CheckConstraint, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS (matching PostgreSQL enums)
# ═══════════════════════════════════════════════════════════════════════════

class MemoryTypeEnum(str, enum.Enum):
    # Lowercase names to match PostgreSQL enum values
    sensory = "sensory"
    working = "working"
    episodic = "episodic"
    semantic = "semantic"
    emotional = "emotional"
    relationship = "relationship"
    conversation = "conversation"


class RelationshipTypeEnum(str, enum.Enum):
    # Lowercase names to match PostgreSQL enum values
    unknown = "unknown"
    stranger = "stranger"
    acquaintance = "acquaintance"
    colleague = "colleague"
    friend = "friend"
    close_friend = "close_friend"
    family = "family"
    rival = "rival"
    enemy = "enemy"
    neutral = "neutral"


class InteractionTypeEnum(str, enum.Enum):
    # Lowercase names to match PostgreSQL enum values
    # Positive
    helped = "helped"
    cooperated = "cooperated"
    shared = "shared"
    protected = "protected"
    celebrated = "celebrated"
    comforted = "comforted"
    # Neutral
    observed = "observed"
    conversed = "conversed"
    traded = "traded"
    # Negative
    competed = "competed"
    conflicted = "conflicted"
    harmed = "harmed"
    betrayed = "betrayed"
    threatened = "threatened"
    attacked = "attacked"


class EpisodeTypeEnum(str, enum.Enum):
    # Lowercase names to match PostgreSQL enum values
    encounter = "encounter"
    interaction = "interaction"
    observation = "observation"
    conflict = "conflict"
    cooperation = "cooperation"
    emotional = "emotional"
    significant = "significant"


# ═══════════════════════════════════════════════════════════════════════════
# EPISODES
# ═══════════════════════════════════════════════════════════════════════════

class EpisodeModel(Base):
    """
    Episodic memory - olay kaydı.

    5W1H: What, Where, When, Who, Why, How
    """
    __tablename__ = "episodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 5W1H
    what = Column(Text, nullable=False)
    location = Column(Text)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    participants = Column(ARRAY(Text), default=[])
    why = Column(Text)
    how = Column(Text)

    # Episode details
    episode_type = Column(
        Enum(EpisodeTypeEnum, name="episode_type", create_type=False),
        nullable=False,
        default=EpisodeTypeEnum.encounter,
    )
    duration_seconds = Column(Float, default=0)

    # Outcome
    outcome = Column(Text)
    outcome_valence = Column(Float, default=0)

    # Emotional trace
    self_emotion_during = Column(Text)
    self_emotion_after = Column(Text)
    pleasure = Column(Float)
    arousal = Column(Float)
    dominance = Column(Float)

    # Memory metadata
    strength = Column(Float, default=1.0)
    importance = Column(Float, default=0.5)
    emotional_valence = Column(Float, default=0)
    emotional_arousal = Column(Float, default=0)

    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), default=func.now())

    # Meta
    tags = Column(ARRAY(Text), default=[])
    context = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    emotional_memories = relationship("EmotionalMemoryModel", back_populates="episode")
    interactions = relationship("InteractionModel", back_populates="episode")

    __table_args__ = (
        CheckConstraint("outcome_valence >= -1 AND outcome_valence <= 1"),
        CheckConstraint("strength >= 0 AND strength <= 1"),
        CheckConstraint("importance >= 0 AND importance <= 1"),
        CheckConstraint("emotional_valence >= -1 AND emotional_valence <= 1"),
        CheckConstraint("emotional_arousal >= 0 AND emotional_arousal <= 1"),
        Index("idx_episodes_occurred_at", occurred_at.desc()),
        Index("idx_episodes_importance", importance.desc()),
        Index("idx_episodes_strength", strength.desc()),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "what": self.what,
            "location": self.location,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "participants": self.participants or [],
            "episode_type": self.episode_type.value if self.episode_type else None,
            "outcome": self.outcome,
            "outcome_valence": self.outcome_valence,
            "self_emotion_during": self.self_emotion_during,
            "strength": self.strength,
            "importance": self.importance,
            "emotional_valence": self.emotional_valence,
            "tags": self.tags or [],
        }


# ═══════════════════════════════════════════════════════════════════════════
# RELATIONSHIPS
# ═══════════════════════════════════════════════════════════════════════════

class RelationshipModel(Base):
    """
    Relationship memory - agent ile ilişki kaydı.
    """
    __tablename__ = "relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    agent_id = Column(Text, nullable=False, unique=True)
    agent_name = Column(Text)

    relationship_type = Column(
        Enum(RelationshipTypeEnum, name="relationship_type", create_type=False),
        nullable=False,
        default=RelationshipTypeEnum.stranger,
    )
    relationship_start = Column(DateTime(timezone=True), default=func.now())

    # Statistics
    total_interactions = Column(Integer, default=0)
    positive_interactions = Column(Integer, default=0)
    negative_interactions = Column(Integer, default=0)
    neutral_interactions = Column(Integer, default=0)

    # Trust
    trust_score = Column(Float, default=0.5)

    # Betrayal
    betrayal_count = Column(Integer, default=0)
    last_betrayal = Column(DateTime(timezone=True))

    # Emotional summary
    overall_sentiment = Column(Float, default=0)
    dominant_emotion = Column(Text)

    # Last interaction
    last_interaction = Column(DateTime(timezone=True))
    last_interaction_type = Column(
        Enum(InteractionTypeEnum, name="interaction_type", create_type=False),
    )

    # Memory metadata
    strength = Column(Float, default=1.0)
    importance = Column(Float, default=0.5)

    # Meta
    notes = Column(ARRAY(Text), default=[])

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    interactions = relationship("InteractionModel", back_populates="rel")
    trust_history = relationship("TrustHistoryModel", back_populates="rel")

    __table_args__ = (
        CheckConstraint("trust_score >= 0 AND trust_score <= 1"),
        CheckConstraint("overall_sentiment >= -1 AND overall_sentiment <= 1"),
        Index("idx_relationships_agent_id", agent_id),
        Index("idx_relationships_trust", trust_score),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "relationship_type": self.relationship_type.value if self.relationship_type else None,
            "total_interactions": self.total_interactions,
            "positive_interactions": self.positive_interactions,
            "negative_interactions": self.negative_interactions,
            "trust_score": self.trust_score,
            "betrayal_count": self.betrayal_count,
            "overall_sentiment": self.overall_sentiment,
            "strength": self.strength,
            "importance": self.importance,
        }


# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIONS
# ═══════════════════════════════════════════════════════════════════════════

class InteractionModel(Base):
    """
    Single interaction record.
    """
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    relationship_id = Column(UUID(as_uuid=True), ForeignKey("relationships.id", ondelete="CASCADE"), nullable=False)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="SET NULL"))

    interaction_type = Column(
        Enum(InteractionTypeEnum, name="interaction_type", create_type=False),
        nullable=False,
    )
    context = Column(Text)

    # Outcome
    outcome = Column(Text)
    outcome_valence = Column(Float, default=0)

    # Impact
    emotional_impact = Column(Float, default=0)
    trust_impact = Column(Float, default=0)

    occurred_at = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships (note: attribute named 'rel' to avoid collision with relationship() function)
    rel = relationship("RelationshipModel", back_populates="interactions")
    episode = relationship("EpisodeModel", back_populates="interactions")

    __table_args__ = (
        CheckConstraint("outcome_valence >= -1 AND outcome_valence <= 1"),
        Index("idx_interactions_relationship", relationship_id),
        Index("idx_interactions_occurred_at", occurred_at.desc()),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "relationship_id": str(self.relationship_id) if self.relationship_id else None,
            "episode_id": str(self.episode_id) if self.episode_id else None,
            "interaction_type": self.interaction_type.value if self.interaction_type else None,
            "context": self.context,
            "outcome_valence": self.outcome_valence,
            "trust_impact": self.trust_impact,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════════
# SEMANTIC FACTS
# ═══════════════════════════════════════════════════════════════════════════

class SemanticFactModel(Base):
    """
    Semantic memory - subject-predicate-object facts.
    """
    __tablename__ = "semantic_facts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    subject = Column(Text, nullable=False)
    predicate = Column(Text, nullable=False)
    object = Column(Text, nullable=False)

    confidence = Column(Float, default=1.0)
    source = Column(Text)

    # Memory metadata
    strength = Column(Float, default=1.0)
    importance = Column(Float, default=0.5)
    access_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1"),
        UniqueConstraint("subject", "predicate", "object", name="uq_semantic_spo"),
        Index("idx_semantic_subject", subject),
        Index("idx_semantic_predicate", predicate),
        Index("idx_semantic_object", object),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "source": self.source,
            "strength": self.strength,
        }


# ═══════════════════════════════════════════════════════════════════════════
# EMOTIONAL MEMORIES
# ═══════════════════════════════════════════════════════════════════════════

class EmotionalMemoryModel(Base):
    """
    Emotional memory - affect-tagged memories.
    """
    __tablename__ = "emotional_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="SET NULL"))

    primary_emotion = Column(Text, nullable=False)
    emotion_intensity = Column(Float, default=0.5)

    pleasure = Column(Float, default=0)
    arousal = Column(Float, default=0.5)
    dominance = Column(Float, default=0.5)

    triggers = Column(ARRAY(Text), default=[])
    is_flashbulb = Column(Boolean, default=False)
    somatic_marker = Column(Text)

    # Memory metadata
    strength = Column(Float, default=1.0)
    importance = Column(Float, default=0.5)
    access_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    episode = relationship("EpisodeModel", back_populates="emotional_memories")

    __table_args__ = (
        CheckConstraint("emotion_intensity >= 0 AND emotion_intensity <= 1"),
        Index("idx_emotional_emotion", primary_emotion),
        Index("idx_emotional_intensity", emotion_intensity.desc()),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "episode_id": str(self.episode_id) if self.episode_id else None,
            "primary_emotion": self.primary_emotion,
            "emotion_intensity": self.emotion_intensity,
            "pleasure": self.pleasure,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "is_flashbulb": self.is_flashbulb,
            "triggers": self.triggers or [],
            "strength": self.strength,
        }


# ═══════════════════════════════════════════════════════════════════════════
# TRUST HISTORY
# ═══════════════════════════════════════════════════════════════════════════

class TrustHistoryModel(Base):
    """
    Trust history - trust score changes over time.
    """
    __tablename__ = "trust_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    relationship_id = Column(UUID(as_uuid=True), ForeignKey("relationships.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(Text, nullable=False)

    trust_value = Column(Float, nullable=False)
    previous_value = Column(Float)
    delta = Column(Float)

    event_type = Column(Text)
    event_context = Column(Text)

    recorded_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships (note: attribute named 'rel' to avoid collision with relationship() function)
    rel = relationship("RelationshipModel", back_populates="trust_history")

    __table_args__ = (
        CheckConstraint("trust_value >= 0 AND trust_value <= 1"),
        Index("idx_trust_history_agent", agent_id),
        Index("idx_trust_history_recorded", recorded_at.desc()),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "trust_value": self.trust_value,
            "previous_value": self.previous_value,
            "delta": self.delta,
            "event_type": self.event_type,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════════
# CYCLE METRICS
# ═══════════════════════════════════════════════════════════════════════════

class CycleMetricModel(Base):
    """
    Cycle metrics - monitoring dashboard için.
    """
    __tablename__ = "cycle_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    cycle_id = Column(Integer, nullable=False)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    ended_at = Column(DateTime(timezone=True))
    duration_ms = Column(Float)

    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Phase durations
    phase_durations = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        Index("idx_cycle_metrics_started", started_at.desc()),
        Index("idx_cycle_metrics_cycle_id", cycle_id),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "cycle_id": self.cycle_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "phase_durations": self.phase_durations or {},
        }


# ═══════════════════════════════════════════════════════════════════════════
# ACTIVITY LOG
# ═══════════════════════════════════════════════════════════════════════════

class ActivityLogModel(Base):
    """
    Activity log - dashboard için event logları.
    """
    __tablename__ = "activity_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    event_type = Column(Text, nullable=False)
    source = Column(Text)
    cycle_id = Column(Integer)

    data = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        Index("idx_activity_log_created", created_at.desc()),
        Index("idx_activity_log_event_type", event_type),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "source": self.source,
            "cycle_id": self.cycle_id,
            "data": self.data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════════
# CONVERSATIONS
# ═══════════════════════════════════════════════════════════════════════════

class ConversationModel(Base):
    """
    Conversation memory - sohbet oturumu.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Session info
    session_id = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid4)
    user_id = Column(Text)
    agent_id = Column(Text, nullable=False, default="default")

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    ended_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, nullable=False, default=True)

    # Summary
    turn_count = Column(Integer, default=0)
    summary = Column(Text)
    main_topics = Column(ARRAY(Text), default=[])
    resolved_intents = Column(ARRAY(Text), default=[])

    # Emotional arc
    emotional_arc = Column(ARRAY(Float), default=[])
    dominant_emotion = Column(Text)
    average_valence = Column(Float, default=0)

    # Related episode
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="SET NULL"))

    # Quality metrics
    coherence_score = Column(Float, default=1.0)
    engagement_score = Column(Float, default=0.5)

    # Memory metadata
    strength = Column(Float, default=1.0)
    importance = Column(Float, default=0.5)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), default=func.now())

    # Meta
    tags = Column(ARRAY(Text), default=[])
    context = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    turns = relationship("DialogueTurnModel", back_populates="conversation", cascade="all, delete-orphan")
    episode = relationship("EpisodeModel")

    __table_args__ = (
        CheckConstraint("coherence_score >= 0 AND coherence_score <= 1"),
        CheckConstraint("engagement_score >= 0 AND engagement_score <= 1"),
        CheckConstraint("strength >= 0 AND strength <= 1"),
        CheckConstraint("importance >= 0 AND importance <= 1"),
        Index("idx_conversations_session_id", session_id),
        Index("idx_conversations_user_id", user_id),
        Index("idx_conversations_started_at", started_at.desc()),
        Index("idx_conversations_is_active", is_active),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "is_active": self.is_active,
            "turn_count": self.turn_count,
            "summary": self.summary,
            "main_topics": self.main_topics or [],
            "average_valence": self.average_valence,
            "coherence_score": self.coherence_score,
            "engagement_score": self.engagement_score,
            "strength": self.strength,
            "importance": self.importance,
        }


# ═══════════════════════════════════════════════════════════════════════════
# DIALOGUE TURNS
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# LEARNING - PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

class PatternTypeEnum(str, enum.Enum):
    """Pattern type enum for database."""
    response = "response"
    behavior = "behavior"
    emotion = "emotion"
    language = "language"


class PatternModel(Base):
    """
    Learning pattern - ogrenilen davranis patterni.
    """
    __tablename__ = "patterns"

    id = Column(String, primary_key=True)

    pattern_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    # Embedding for similarity search (384 dimensions for all-MiniLM-L6-v2)
    embedding = Column(ARRAY(Float), nullable=True)

    # Statistics
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    total_reward = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Extra data
    extra_data = Column(JSONB, default={})

    __table_args__ = (
        Index("idx_patterns_type", pattern_type),
        Index("idx_patterns_created_at", created_at.desc()),
        Index("idx_patterns_success_count", success_count.desc()),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "content": self.content,
            "embedding": self.embedding,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_reward": self.total_reward,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "extra_data": self.extra_data or {},
        }


# ═══════════════════════════════════════════════════════════════════════════
# LEARNING - FEEDBACKS
# ═══════════════════════════════════════════════════════════════════════════

class FeedbackTypeEnum(str, enum.Enum):
    """Feedback type enum for database."""
    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    explicit = "explicit"
    implicit = "implicit"


class FeedbackModel(Base):
    """
    Learning feedback - geri bildirim kaydi.
    """
    __tablename__ = "feedbacks"

    id = Column(String, primary_key=True)

    interaction_id = Column(String, nullable=False)
    feedback_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)

    timestamp = Column(DateTime(timezone=True), default=func.now())

    user_id = Column(String, nullable=True)
    context = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("value >= -1 AND value <= 1"),
        Index("idx_feedbacks_interaction", interaction_id),
        Index("idx_feedbacks_user", user_id),
        Index("idx_feedbacks_timestamp", timestamp.desc()),
        Index("idx_feedbacks_type", feedback_type),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "interaction_id": self.interaction_id,
            "feedback_type": self.feedback_type,
            "value": self.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "context": self.context,
            "reason": self.reason,
        }


class DialogueTurnModel(Base):
    """
    Dialogue turn - tek bir mesaj.
    """
    __tablename__ = "dialogue_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Message info
    role = Column(Text, nullable=False)  # user, agent, system
    content = Column(Text, nullable=False)

    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Emotional analysis
    emotional_valence = Column(Float, default=0)
    emotional_arousal = Column(Float, default=0)
    detected_emotion = Column(Text)

    # Intent and topics
    intent = Column(Text)
    topics = Column(ARRAY(Text), default=[])

    # Embedding (for semantic search)
    embedding = Column(ARRAY(Float))

    # Meta
    extra_data = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    conversation = relationship("ConversationModel", back_populates="turns")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'agent', 'system')"),
        CheckConstraint("emotional_valence >= -1 AND emotional_valence <= 1"),
        CheckConstraint("emotional_arousal >= 0 AND emotional_arousal <= 1"),
        Index("idx_dialogue_turns_conversation", conversation_id),
        Index("idx_dialogue_turns_timestamp", timestamp.desc()),
        Index("idx_dialogue_turns_role", role),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "emotional_valence": self.emotional_valence,
            "emotional_arousal": self.emotional_arousal,
            "detected_emotion": self.detected_emotion,
            "intent": self.intent,
            "topics": self.topics or [],
        }
