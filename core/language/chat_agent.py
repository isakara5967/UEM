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


@dataclass
class ChatResponse:
    """Chat yanit yapisi."""

    content: str
    emotion: Optional[PADState] = None
    intent: Optional[str] = None
    llm_response: Optional[LLMResponse] = None
    context_used: Optional[str] = None
    turn_id: Optional[str] = None


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

        # Session state
        self._current_user_id: Optional[str] = None
        self._current_session_id: Optional[str] = None
        self._session_emotions: List[PADState] = []
        self._turn_count = 0

        # Stats
        self._stats = {
            "total_sessions": 0,
            "total_turns": 0,
            "total_recalls": 0,
        }

        logger.info(
            f"UEMChatAgent initialized (memory={self.memory is not None}, "
            f"llm={self.llm.get_provider().value})"
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
        1. Get context from conversation memory
        2. Get relevant memories from semantic search
        3. Build context
        4. Get response from LLM
        5. Save to memory
        6. Return response

        Args:
            user_message: User's message
            user_id: User ID (optional)

        Returns:
            ChatResponse with agent's reply
        """
        # Ensure session
        if self._current_session_id is None:
            user_id = user_id or "default_user"
            self.start_session(user_id)

        # 1. Build context
        context = self._build_context(user_message)

        # 2. Get LLM response
        llm_response = self.llm.generate(
            prompt=context,
            system=self.config.personality,
        )

        # 3. Extract emotion from response
        emotion = None
        if self.config.track_emotions:
            emotion = self._extract_emotion(llm_response.content)
            if emotion:
                self._session_emotions.append(emotion)

        # 4. Detect intent
        intent = self._detect_intent(user_message)

        # 5. Save to memory
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
                content=llm_response.content,
                emotional_valence=emotion.pleasure if emotion else 0.0,
            )
            turn_id = self.memory.conversation.add_turn(
                self._current_session_id,
                agent_turn.role,
                agent_turn.content,
            )

        self._turn_count += 1
        self._stats["total_turns"] += 1

        return ChatResponse(
            content=llm_response.content,
            emotion=emotion,
            intent=intent,
            llm_response=llm_response,
            context_used=context,
            turn_id=turn_id,
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

        return {
            "session_id": self._current_session_id,
            "user_id": self._current_user_id,
            "turn_count": self._turn_count,
            "emotion_samples": len(self._session_emotions),
            "average_emotion": avg_emotion,
            **self._stats,
        }

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
