"""
core/language/chat_agent.py

UEM Chat Agent - Memory + LLM entegre chat agent.
UEM v2 - Tam entegre sohbet sistemi.

Ozellikler:
- Conversation memory entegrasyonu
- Semantic search ile ilgili anıları getirme
- Context building
- Emotion tracking
- Trust level integration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import re

from .context import ContextBuilder, ContextConfig
from .llm_adapter import LLMAdapter, LLMConfig, LLMResponse, MockLLMAdapter

# Memory imports - graceful
try:
    from core.memory import (
        MemoryStore,
        MemoryConfig,
        DialogueTurn,
        Conversation,
        EmbeddingResult,
        create_memory_store,
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# Affect imports - graceful
try:
    from core.affect.emotion.core.pad import PADState
    AFFECT_AVAILABLE = True
except ImportError:
    AFFECT_AVAILABLE = False
    # Fallback PADState
    @dataclass
    class PADState:
        pleasure: float = 0.0
        arousal: float = 0.5
        dominance: float = 0.5
        intensity: float = 0.5
        timestamp: Optional[float] = None
        source: Optional[str] = None

# Learning imports - graceful
try:
    from core.learning import (
        LearningProcessor,
        FeedbackType,
        LearningOutcome,
    )
    LEARNING_AVAILABLE = True
except ImportError:
    LEARNING_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ChatConfig:
    """Chat agent yapilandirmasi."""

    personality: str = "Sen yardimci ve arkadas canli bir asistansin."
    llm_config: Optional[LLMConfig] = None
    context_config: Optional[ContextConfig] = None
    auto_index_conversations: bool = True
    track_emotions: bool = True
    default_trust: float = 0.5
    enable_learning: bool = True
    use_learned_responses: bool = True


@dataclass
class ChatResponse:
    """Chat yanit yapisi."""

    content: str
    emotion: Optional[PADState] = None
    intent: Optional[str] = None
    llm_response: Optional[LLMResponse] = None
    context_used: Optional[str] = None
    turn_id: Optional[str] = None
    source: str = "llm"  # "llm" or "learned"
    interaction_id: Optional[str] = None


class UEMChatAgent:
    """
    UEM Chat Agent - Memory + LLM entegre chat.

    Tum UEM modulleri ile entegre calisir:
    - Memory: Conversation history, semantic search
    - Affect: Emotion tracking
    - Trust: User trust levels

    Kullanim:
        agent = UEMChatAgent()
        session_id = agent.start_session("user_123")
        response = agent.chat("Merhaba!")
        print(response.content)
        agent.end_session()
    """

    def __init__(
        self,
        config: Optional[ChatConfig] = None,
        memory: Optional[Any] = None,
        llm: Optional[LLMAdapter] = None,
    ):
        """
        Initialize UEM Chat Agent.

        Args:
            config: Chat yapilandirmasi
            memory: MemoryStore instance (opsiyonel)
            llm: LLMAdapter instance (default: MockLLMAdapter)
        """
        self.config = config or ChatConfig()

        # Memory store
        if memory is not None:
            self.memory = memory
        elif MEMORY_AVAILABLE:
            self.memory = create_memory_store()
        else:
            self.memory = None
            logger.warning("Memory module not available")

        # LLM adapter
        self.llm = llm or MockLLMAdapter()

        # Context builder
        self.context_builder = ContextBuilder(self.config.context_config)

        # Learning processor
        self.learning: Optional[LearningProcessor] = None
        if self.config.enable_learning and LEARNING_AVAILABLE:
            self.learning = LearningProcessor(memory=self.memory)
            logger.info("Learning processor initialized")

        # Session state
        self._current_user_id: Optional[str] = None
        self._current_session_id: Optional[str] = None
        self._session_emotions: List[PADState] = []
        self._turn_count = 0

        # Learning state
        self._last_interaction_id: Optional[str] = None
        self._last_pattern_id: Optional[str] = None

        # Stats
        self._stats = {
            "total_sessions": 0,
            "total_turns": 0,
            "total_recalls": 0,
            "learned_responses": 0,
        }

        logger.info(
            f"UEMChatAgent initialized (memory={self.memory is not None}, "
            f"llm={self.llm.get_provider().value}, "
            f"learning={self.learning is not None})"
        )

    # ===================================================================
    # SESSION MANAGEMENT
    # ===================================================================

    def start_session(self, user_id: str) -> str:
        """
        Start new chat session.

        Args:
            user_id: User identifier

        Returns:
            Session ID
        """
        self._current_user_id = user_id

        # Start conversation in memory
        if self.memory is not None and hasattr(self.memory, 'conversation'):
            self._current_session_id = self.memory.conversation.start_conversation(
                user_id=user_id
            )
        else:
            self._current_session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self._session_emotions = []
        self._turn_count = 0
        self._stats["total_sessions"] += 1

        logger.info(f"Session started: {self._current_session_id} for user {user_id}")
        return self._current_session_id

    def end_session(self, user_id: Optional[str] = None) -> None:
        """
        End current chat session.

        Args:
            user_id: User ID (optional, uses current if not provided)
        """
        user_id = user_id or self._current_user_id

        if self.memory is not None and hasattr(self.memory, 'conversation'):
            # End conversation
            if self._current_session_id:
                self.memory.conversation.end_conversation(self._current_session_id)

            # Auto-index if enabled
            if self.config.auto_index_conversations and hasattr(self.memory, 'semantic'):
                conv = self.memory.conversation.get_conversation(self._current_session_id)
                if conv:
                    self.memory.semantic.index_conversation(conv)
                    logger.debug(f"Conversation indexed: {self._current_session_id}")

        logger.info(f"Session ended: {self._current_session_id}")

        self._current_session_id = None
        self._current_user_id = None
        self._session_emotions = []

    # ===================================================================
    # CHAT
    # ===================================================================

    def chat(
        self,
        user_message: str,
        user_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Main chat method.

        Steps:
        1. Try to get learned response
        2. If no learned response, get from LLM
        3. Save to memory
        4. Learn from interaction
        5. Return response

        Args:
            user_message: User's message
            user_id: User ID (optional)

        Returns:
            ChatResponse with agent's reply
        """
        import uuid

        # Ensure session
        if self._current_session_id is None:
            user_id = user_id or "default_user"
            self.start_session(user_id)

        # Generate interaction ID
        interaction_id = f"int_{uuid.uuid4().hex[:12]}"
        self._last_interaction_id = interaction_id

        # Detect intent early
        intent = self._detect_intent(user_message)

        # 1. Try learned response first
        response_content = None
        response_source = "llm"
        llm_response = None

        if (self.learning is not None and
            self.config.use_learned_responses):
            from core.learning import PatternType
            pattern = self.learning.adapter.suggest_pattern(user_message, PatternType.RESPONSE)
            if pattern and self._should_use_suggestion(pattern):
                response_content = pattern.content
                response_source = "learned"
                self._stats["learned_responses"] += 1
                logger.debug(f"Using learned response for: {user_message[:50]}...")

        # 2. If no learned response, use LLM
        if response_content is None:
            context = self._build_context(user_message)
            llm_response = self.llm.generate(
                prompt=context,
                system=self.config.personality,
            )
            response_content = llm_response.content
            response_source = "llm"

        # 3. Extract emotion from response
        emotion = None
        if self.config.track_emotions:
            emotion = self._extract_emotion(response_content)
            if emotion:
                self._session_emotions.append(emotion)

        # 4. Save to memory
        turn_id = None
        if self.memory is not None and hasattr(self.memory, 'conversation'):
            # Save user turn
            user_turn = DialogueTurn(
                role="user",
                content=user_message,
                intent=intent,
            )
            self.memory.conversation.add_turn(
                self._current_session_id,
                user_turn.role,
                user_turn.content,
            )

            # Save agent turn
            agent_turn = DialogueTurn(
                role="agent",
                content=response_content,
                emotional_valence=emotion.pleasure if emotion else 0.0,
            )
            turn_id = self.memory.conversation.add_turn(
                self._current_session_id,
                agent_turn.role,
                agent_turn.content,
            )

        # 5. Store response as pattern for learning (if from LLM)
        self._last_pattern_id = None
        if self.learning is not None and response_source == "llm":
            from core.learning import PatternType
            pattern = self.learning.pattern_storage.store(
                content=response_content,
                pattern_type=PatternType.RESPONSE,
                extra_data={"context": user_message, "interaction_id": interaction_id}
            )
            self._last_pattern_id = pattern.id

        self._turn_count += 1
        self._stats["total_turns"] += 1

        return ChatResponse(
            content=response_content,
            emotion=emotion,
            intent=intent,
            llm_response=llm_response,
            context_used=self._build_context(user_message) if llm_response else None,
            turn_id=turn_id,
            source=response_source,
            interaction_id=interaction_id,
        )

    # ===================================================================
    # MEMORY INTEGRATION
    # ===================================================================

    def recall(self, query: str, k: int = 5) -> List[Any]:
        """
        Recall relevant memories using semantic search.

        Args:
            query: Search query
            k: Number of results

        Returns:
            List of EmbeddingResult
        """
        if self.memory is None or not hasattr(self.memory, 'semantic'):
            return []

        self._stats["total_recalls"] += 1
        return self.memory.semantic.search(query, k=k)

    def get_conversation_history(self, n: int = 10) -> List[Any]:
        """
        Get last n turns from current conversation.

        Args:
            n: Number of turns

        Returns:
            List of DialogueTurn
        """
        if self.memory is None or not hasattr(self.memory, 'conversation'):
            return []

        if self._current_session_id is None:
            return []

        return self.memory.conversation.get_context(
            self._current_session_id,
            max_turns=n,
        )

    # ===================================================================
    # LEARNING
    # ===================================================================

    def feedback(self, positive: bool, reason: Optional[str] = None) -> bool:
        """
        Provide feedback for the last interaction.

        Args:
            positive: True for positive, False for negative feedback
            reason: Optional reason for feedback

        Returns:
            True if feedback was recorded successfully
        """
        if self.learning is None:
            logger.warning("Learning not available, feedback ignored")
            return False

        if self._last_interaction_id is None:
            logger.warning("No last interaction to provide feedback for")
            return False

        # Record explicit feedback
        feedback_type = FeedbackType.POSITIVE if positive else FeedbackType.NEGATIVE
        value = 1.0 if positive else -1.0

        feedback_obj = self.learning.feedback_collector.record(
            interaction_id=self._last_interaction_id,
            feedback_type=FeedbackType.EXPLICIT,
            value=value,
            user_id=self._current_user_id,
            reason=reason
        )

        # Reinforce pattern if exists
        if self._last_pattern_id:
            self.learning.reinforcer.reinforce(self._last_pattern_id, feedback_obj)
            logger.debug(
                f"Feedback recorded: {'positive' if positive else 'negative'} "
                f"for pattern {self._last_pattern_id}"
            )

        return True

    def get_learned_count(self) -> int:
        """
        Get number of learned patterns.

        Returns:
            Number of patterns in storage
        """
        if self.learning is None:
            return 0
        return self.learning.pattern_storage.count()

    def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get learning statistics.

        Returns:
            Learning stats dict or empty dict if learning disabled
        """
        if self.learning is None:
            return {}
        return self.learning.stats()

    # ===================================================================
    # STATE
    # ===================================================================

    def get_current_emotion(self) -> Optional[PADState]:
        """
        Get current emotional state.

        Returns:
            Most recent PADState or None
        """
        if self._session_emotions:
            return self._session_emotions[-1]
        return None

    def get_trust_level(self, user_id: str) -> float:
        """
        Get trust level for user.

        Args:
            user_id: User ID

        Returns:
            Trust score (0-1)
        """
        if self.memory is None:
            return self.config.default_trust

        # Try to get from relationship memory
        if hasattr(self.memory, 'get_relationship'):
            relationship = self.memory.get_relationship(user_id)
            if relationship:
                return relationship.trust_score

        return self.config.default_trust

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get current session statistics.

        Returns:
            Dict with session stats
        """
        avg_emotion = None
        if self._session_emotions:
            avg_pleasure = sum(e.pleasure for e in self._session_emotions) / len(self._session_emotions)
            avg_arousal = sum(e.arousal for e in self._session_emotions) / len(self._session_emotions)
            avg_emotion = {
                "pleasure": avg_pleasure,
                "arousal": avg_arousal,
            }

        stats = {
            "session_id": self._current_session_id,
            "user_id": self._current_user_id,
            "turn_count": self._turn_count,
            "emotion_samples": len(self._session_emotions),
            "average_emotion": avg_emotion,
            "patterns_learned": self.get_learned_count(),
            **self._stats,
        }

        return stats

    # ===================================================================
    # INTERNAL METHODS
    # ===================================================================

    def _build_context(self, user_message: str) -> str:
        """
        Build context for LLM.

        Args:
            user_message: Current user message

        Returns:
            Formatted context string
        """
        # Get conversation history
        conversation = None
        if self.memory is not None and hasattr(self.memory, 'conversation'):
            if self._current_session_id:
                conversation = self.memory.conversation.get_conversation(
                    self._current_session_id
                )

        # Get relevant memories
        relevant_memories = None
        if self.memory is not None and hasattr(self.memory, 'semantic'):
            relevant_memories = self.memory.semantic.search(
                user_message,
                k=self.context_builder.config.relevant_memories_count,
            )

        # Get self state
        self_state = None
        if self._session_emotions:
            last_emotion = self._session_emotions[-1]
            self_state = {
                "mood": "positive" if last_emotion.pleasure > 0 else "negative" if last_emotion.pleasure < 0 else "neutral",
                "arousal": last_emotion.arousal,
            }

        # Get relationship
        relationship = None
        if self._current_user_id and self.memory is not None:
            if hasattr(self.memory, 'get_relationship'):
                rel = self.memory.get_relationship(self._current_user_id)
                if rel and rel.total_interactions > 0:
                    relationship = {
                        "name": rel.agent_name or self._current_user_id,
                        "type": rel.relationship_type.value if hasattr(rel.relationship_type, 'value') else str(rel.relationship_type),
                        "trust_score": rel.trust_score,
                        "total_interactions": rel.total_interactions,
                        "sentiment": rel.overall_sentiment,
                    }

        # Build context
        return self.context_builder.build(
            user_message=user_message,
            conversation=conversation,
            relevant_memories=relevant_memories,
            self_state=self_state,
            relationship=relationship,
            personality=self.config.personality,
        )

    def _extract_emotion(self, text: str) -> Optional[PADState]:
        """
        Extract emotion from text.

        Simple keyword-based extraction.
        For production, use a proper sentiment analysis model.

        Args:
            text: Text to analyze

        Returns:
            PADState or None
        """
        text_lower = text.lower()

        # Simple keyword matching
        positive_words = ["mutlu", "sevinc", "harika", "guzel", "tesekkur", "sevindim", "memnun", "super", "happy", "great", "wonderful", "thanks"]
        negative_words = ["uzgun", "kotu", "maalesef", "sorry", "sad", "bad", "unfortunately", "sikinti", "problem"]
        high_arousal_words = ["heyecan", "saskin", "inanil", "wow", "excited", "amazing", "incredible"]

        pleasure = 0.0
        arousal = 0.5

        for word in positive_words:
            if word in text_lower:
                pleasure += 0.3

        for word in negative_words:
            if word in text_lower:
                pleasure -= 0.3

        for word in high_arousal_words:
            if word in text_lower:
                arousal += 0.2

        # Clamp values
        pleasure = max(-1.0, min(1.0, pleasure))
        arousal = max(0.0, min(1.0, arousal))

        return PADState(
            pleasure=pleasure,
            arousal=arousal,
            dominance=0.5,
            intensity=abs(pleasure),
            source="text_analysis",
        )

    def _should_use_suggestion(self, pattern: Any) -> bool:
        """
        Pattern kullanilabilir mi kontrol et.

        Sartlar:
        - success_count >= 3 (en az 3 basarili kullanim)
        - success_rate >= 0.7 (%70 basari orani)

        Not: similarity kontrolu patterns.find_similar'da yapiliyor (>= 0.85)

        Args:
            pattern: Kontrol edilecek pattern

        Returns:
            True ise pattern kullanilabilir
        """
        if pattern is None:
            return False
        if pattern.success_count < 3:
            return False
        if pattern.success_rate < 0.7:
            return False
        return True

    def _detect_intent(self, text: str) -> str:
        """
        Detect intent from user message.

        Simple rule-based detection.
        For production, use a proper intent classifier.

        Args:
            text: User message

        Returns:
            Intent string
        """
        text_lower = text.lower().strip()

        # Question detection
        if text_lower.endswith("?") or any(q in text_lower for q in ["mi", "mı", "mu", "mü", "ne", "nasıl", "neden", "nerede", "kim", "what", "how", "why", "where", "who", "when"]):
            return "question"

        # Greeting detection
        if any(g in text_lower for g in ["merhaba", "selam", "hey", "hello", "hi", "günaydın", "iyi günler"]):
            return "greeting"

        # Farewell detection
        if any(f in text_lower for f in ["hoşçakal", "görüşürüz", "bye", "goodbye", "iyi geceler"]):
            return "farewell"

        # Thanks detection
        if any(t in text_lower for t in ["teşekkür", "sağol", "thanks", "thank you", "eyvallah"]):
            return "thanks"

        # Request detection
        if any(r in text_lower for r in ["lütfen", "please", "yap", "et", "ver", "göster", "anlat"]):
            return "request"

        return "statement"


# ========================================================================
# FACTORY & SINGLETON
# ========================================================================

_chat_agent: Optional[UEMChatAgent] = None


def get_chat_agent(
    config: Optional[ChatConfig] = None,
    memory: Optional[Any] = None,
    llm: Optional[LLMAdapter] = None,
) -> UEMChatAgent:
    """Get chat agent singleton."""
    global _chat_agent

    if _chat_agent is None:
        _chat_agent = UEMChatAgent(config, memory, llm)

    return _chat_agent


def reset_chat_agent() -> None:
    """Reset chat agent singleton (test icin)."""
    global _chat_agent
    _chat_agent = None


def create_chat_agent(
    config: Optional[ChatConfig] = None,
    memory: Optional[Any] = None,
    llm: Optional[LLMAdapter] = None,
) -> UEMChatAgent:
    """Create new chat agent (test icin)."""
    return UEMChatAgent(config, memory, llm)
