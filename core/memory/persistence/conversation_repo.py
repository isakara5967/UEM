"""
core/memory/persistence/conversation_repo.py

Repository for Conversation Memory PostgreSQL persistence.

Provides CRUD operations for conversations and dialogue turns.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session

from .models import ConversationModel, DialogueTurnModel

logger = logging.getLogger(__name__)


class ConversationRepository:
    """
    Repository for conversation persistence operations.

    Usage:
        from .repository import get_session
        session = get_session()
        repo = ConversationRepository(session)

        # Create conversation
        conv = repo.create_conversation(user_id="user1")

        # Add turn
        turn = repo.add_turn(conv.session_id, role="user", content="Hello!")

        # Get context
        turns = repo.get_context_window(conv.session_id)

        session.close()
    """

    def __init__(self, session: Session):
        self.session = session

    # ═══════════════════════════════════════════════════════════════════
    # CONVERSATIONS
    # ═══════════════════════════════════════════════════════════════════

    def create_conversation(
        self,
        user_id: Optional[str] = None,
        agent_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationModel:
        """Create a new conversation."""
        conversation = ConversationModel(
            user_id=user_id,
            agent_id=agent_id,
            context=metadata or {},
        )
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        logger.debug(f"Conversation created: {conversation.session_id}")
        return conversation

    def get_conversation(self, conversation_id: UUID) -> Optional[ConversationModel]:
        """Get conversation by ID."""
        return self.session.query(ConversationModel).filter(
            ConversationModel.id == conversation_id
        ).first()

    def get_conversation_by_session(self, session_id: UUID) -> Optional[ConversationModel]:
        """Get conversation by session ID."""
        return self.session.query(ConversationModel).filter(
            ConversationModel.session_id == session_id
        ).first()

    def get_active_session(self, user_id: str) -> Optional[ConversationModel]:
        """Get user's active conversation."""
        return self.session.query(ConversationModel).filter(
            ConversationModel.user_id == user_id,
            ConversationModel.is_active == True,
        ).order_by(
            desc(ConversationModel.started_at)
        ).first()

    def end_conversation(
        self,
        session_id: UUID,
        summary: Optional[str] = None,
    ) -> Optional[ConversationModel]:
        """End a conversation."""
        conversation = self.get_conversation_by_session(session_id)
        if not conversation:
            return None

        conversation.is_active = False
        conversation.ended_at = datetime.utcnow()
        if summary:
            conversation.summary = summary

        self.session.commit()
        logger.debug(f"Conversation ended: {session_id}")
        return conversation

    def touch_conversation(self, session_id: UUID) -> None:
        """Mark conversation as accessed."""
        conversation = self.get_conversation_by_session(session_id)
        if conversation:
            conversation.last_accessed = datetime.utcnow()
            conversation.access_count += 1
            conversation.strength = min(1.0, conversation.strength + 0.05)
            self.session.commit()

    def find_user_conversations(
        self,
        user_id: str,
        include_inactive: bool = False,
        limit: int = 50,
    ) -> List[ConversationModel]:
        """Find user's conversations."""
        query = self.session.query(ConversationModel).filter(
            ConversationModel.user_id == user_id
        )

        if not include_inactive:
            query = query.filter(ConversationModel.is_active == True)

        return query.order_by(
            desc(ConversationModel.last_accessed)
        ).limit(limit).all()

    def find_recent_conversations(
        self,
        hours: int = 24,
        limit: int = 50,
    ) -> List[ConversationModel]:
        """Find recent conversations."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.session.query(ConversationModel).filter(
            ConversationModel.started_at >= cutoff
        ).order_by(
            desc(ConversationModel.started_at)
        ).limit(limit).all()

    def find_conversations_by_topic(
        self,
        topic: str,
        limit: int = 20,
    ) -> List[ConversationModel]:
        """Find conversations by topic."""
        return self.session.query(ConversationModel).filter(
            ConversationModel.main_topics.contains([topic])
        ).order_by(
            desc(ConversationModel.last_accessed)
        ).limit(limit).all()

    def cleanup_inactive_sessions(
        self,
        timeout_minutes: float = 30.0,
    ) -> int:
        """Close inactive sessions and return count."""
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)

        count = self.session.query(ConversationModel).filter(
            ConversationModel.is_active == True,
            ConversationModel.last_accessed < cutoff,
        ).update({
            ConversationModel.is_active: False,
            ConversationModel.ended_at: datetime.utcnow(),
            ConversationModel.summary: "Session timed out",
        })

        self.session.commit()
        logger.info(f"Closed {count} inactive sessions")
        return count

    # ═══════════════════════════════════════════════════════════════════
    # DIALOGUE TURNS
    # ═══════════════════════════════════════════════════════════════════

    def add_turn(
        self,
        session_id: UUID,
        role: str,
        content: str,
        emotional_valence: float = 0.0,
        emotional_arousal: float = 0.0,
        detected_emotion: Optional[str] = None,
        intent: Optional[str] = None,
        topics: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[DialogueTurnModel]:
        """Add a turn to a conversation."""
        conversation = self.get_conversation_by_session(session_id)
        if not conversation:
            logger.warning(f"Conversation not found: {session_id}")
            return None

        if not conversation.is_active:
            logger.warning(f"Conversation not active: {session_id}")
            return None

        turn = DialogueTurnModel(
            conversation_id=conversation.id,
            role=role,
            content=content,
            emotional_valence=emotional_valence,
            emotional_arousal=emotional_arousal,
            detected_emotion=detected_emotion,
            intent=intent,
            topics=topics or [],
            metadata=metadata or {},
        )

        self.session.add(turn)

        # Update conversation stats
        conversation.turn_count += 1
        conversation.last_accessed = datetime.utcnow()
        conversation.emotional_arc = (conversation.emotional_arc or []) + [emotional_valence]
        conversation.average_valence = sum(conversation.emotional_arc) / len(conversation.emotional_arc)

        # Update topics
        for topic in (topics or []):
            if topic not in (conversation.main_topics or []):
                conversation.main_topics = (conversation.main_topics or []) + [topic]

        self.session.commit()
        self.session.refresh(turn)

        logger.debug(f"Turn added to {session_id}: {role}")
        return turn

    def get_turn(self, turn_id: UUID) -> Optional[DialogueTurnModel]:
        """Get turn by ID."""
        return self.session.query(DialogueTurnModel).filter(
            DialogueTurnModel.id == turn_id
        ).first()

    def get_context_window(
        self,
        session_id: UUID,
        max_turns: int = 10,
    ) -> List[DialogueTurnModel]:
        """Get context window (last N turns)."""
        conversation = self.get_conversation_by_session(session_id)
        if not conversation:
            return []

        return self.session.query(DialogueTurnModel).filter(
            DialogueTurnModel.conversation_id == conversation.id
        ).order_by(
            desc(DialogueTurnModel.timestamp)
        ).limit(max_turns).all()[::-1]  # Reverse to chronological order

    def get_full_history(self, session_id: UUID) -> List[DialogueTurnModel]:
        """Get full conversation history."""
        conversation = self.get_conversation_by_session(session_id)
        if not conversation:
            return []

        return self.session.query(DialogueTurnModel).filter(
            DialogueTurnModel.conversation_id == conversation.id
        ).order_by(
            DialogueTurnModel.timestamp
        ).all()

    # ═══════════════════════════════════════════════════════════════════
    # SEARCH
    # ═══════════════════════════════════════════════════════════════════

    def search_history(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> List[Tuple[DialogueTurnModel, float]]:
        """
        Search conversation history using full-text search.

        Returns list of (turn, relevance_score) tuples.
        """
        base_query = self.session.query(
            DialogueTurnModel,
            func.ts_rank(
                func.to_tsvector('english', DialogueTurnModel.content),
                func.plainto_tsquery('english', query)
            ).label('relevance')
        ).filter(
            func.to_tsvector('english', DialogueTurnModel.content).match(query)
        )

        if session_id:
            conversation = self.get_conversation_by_session(session_id)
            if conversation:
                base_query = base_query.filter(
                    DialogueTurnModel.conversation_id == conversation.id
                )

        if user_id:
            # Join with conversations to filter by user
            base_query = base_query.join(
                ConversationModel,
                DialogueTurnModel.conversation_id == ConversationModel.id
            ).filter(
                ConversationModel.user_id == user_id
            )

        results = base_query.order_by(
            desc('relevance')
        ).limit(limit).all()

        return [(turn, float(relevance)) for turn, relevance in results]

    def search_by_emotion(
        self,
        emotion: str,
        min_intensity: float = 0.3,
        limit: int = 20,
    ) -> List[DialogueTurnModel]:
        """Search turns by detected emotion."""
        return self.session.query(DialogueTurnModel).filter(
            DialogueTurnModel.detected_emotion == emotion,
            func.abs(DialogueTurnModel.emotional_valence) >= min_intensity,
        ).order_by(
            desc(func.abs(DialogueTurnModel.emotional_valence))
        ).limit(limit).all()

    def search_by_intent(
        self,
        intent: str,
        limit: int = 20,
    ) -> List[DialogueTurnModel]:
        """Search turns by intent."""
        return self.session.query(DialogueTurnModel).filter(
            DialogueTurnModel.intent == intent
        ).order_by(
            desc(DialogueTurnModel.timestamp)
        ).limit(limit).all()

    # ═══════════════════════════════════════════════════════════════════
    # DECAY & CLEANUP
    # ═══════════════════════════════════════════════════════════════════

    def apply_decay(self, decay_rate: float = 0.01) -> int:
        """Apply decay to inactive conversations."""
        count = self.session.query(ConversationModel).filter(
            ConversationModel.is_active == False,
            ConversationModel.strength > 0,
        ).update({
            ConversationModel.strength: func.greatest(
                0,
                ConversationModel.strength - decay_rate * (1 - ConversationModel.importance * 0.5)
            )
        })

        self.session.commit()
        return count

    def cleanup_weak_conversations(
        self,
        strength_threshold: float = 0.1,
    ) -> int:
        """Remove weak conversations."""
        count = self.session.query(ConversationModel).filter(
            ConversationModel.strength < strength_threshold,
            ConversationModel.importance < 0.5,
            ConversationModel.is_active == False,
        ).delete()

        self.session.commit()
        return count

    # ═══════════════════════════════════════════════════════════════════
    # STATS
    # ═══════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        return {
            "total_conversations": self.session.query(ConversationModel).count(),
            "active_sessions": self.session.query(ConversationModel).filter(
                ConversationModel.is_active == True
            ).count(),
            "total_turns": self.session.query(DialogueTurnModel).count(),
            "avg_turns_per_conversation": self.session.query(
                func.avg(ConversationModel.turn_count)
            ).scalar() or 0,
            "avg_conversation_strength": self.session.query(
                func.avg(ConversationModel.strength)
            ).scalar() or 0,
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
