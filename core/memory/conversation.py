"""
core/memory/conversation.py

Conversation Memory - Sohbet gecmisi ve diyalog yonetimi.
UEM v2 - Episodik bellek ile entegre calisir.

Ozellikler:
- Sohbet oturumu yonetimi
- Diyalog turleri (user/agent)
- Context window yonetimi
- Duygusal akis takibi
- Keyword-based arama
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import re

from .types import (
    Conversation,
    DialogueTurn,
    Episode,
    EpisodeType,
    MemoryType,
)

logger = logging.getLogger(__name__)


@dataclass
class ConversationConfig:
    """Conversation memory yapilandirmasi."""

    # Context window
    default_context_turns: int = 10       # Varsayilan son N tur
    max_context_tokens: int = 4000        # Maksimum token (tahmini)
    chars_per_token: int = 4              # Karakter/token orani

    # Oturum yonetimi
    session_timeout_minutes: float = 30.0  # Inaktivite timeout
    max_turns_per_session: int = 1000      # Maksimum tur sayisi

    # Arama
    default_search_limit: int = 20
    min_search_relevance: float = 0.1

    # Duygusal analiz
    track_emotional_arc: bool = True

    # Persistence (ileride)
    use_persistence: bool = False
    db_connection_string: str = ""


class ConversationMemory:
    """
    Conversation Memory - Sohbet gecmisi yonetimi.

    Episodic memory ile entegre calisir:
    - Sohbetler episode olarak kaydedilebilir
    - Context window LLM entegrasyonu icin

    Kullanim:
        conv_memory = ConversationMemory()
        session_id = conv_memory.start_conversation(user_id="user1")
        conv_memory.add_turn(session_id, "user", "Merhaba!")
        conv_memory.add_turn(session_id, "agent", "Merhaba! Size nasil yardimci olabilirim?")
        context = conv_memory.get_context(session_id)
        conv_memory.end_conversation(session_id)
    """

    def __init__(self, config: Optional[ConversationConfig] = None):
        self.config = config or ConversationConfig()

        # In-memory stores
        self._conversations: Dict[str, Conversation] = {}  # session_id -> Conversation
        self._active_sessions: Dict[str, str] = {}         # user_id -> active session_id

        # Arama indexi (basit keyword index)
        self._keyword_index: Dict[str, List[str]] = {}     # keyword -> [turn_id, ...]
        self._turn_to_conversation: Dict[str, str] = {}    # turn_id -> session_id

        # Stats
        self._stats = {
            "total_conversations": 0,
            "total_turns": 0,
            "active_sessions": 0,
            "searches": 0,
        }

        logger.info("ConversationMemory initialized")

    # ===================================================================
    # SESSION MANAGEMENT
    # ===================================================================

    def start_conversation(
        self,
        user_id: Optional[str] = None,
        agent_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Yeni sohbet oturumu baslat.

        Args:
            user_id: Kullanici ID (opsiyonel)
            agent_id: Ajan ID
            metadata: Ek bilgiler

        Returns:
            session_id
        """
        # Kullanicinin aktif oturumu varsa kapat
        if user_id and user_id in self._active_sessions:
            old_session = self._active_sessions[user_id]
            self.end_conversation(old_session)

        # Yeni conversation olustur
        conversation = Conversation(
            user_id=user_id,
            agent_id=agent_id,
        )

        if metadata:
            conversation.context = metadata

        # Kaydet
        self._conversations[conversation.session_id] = conversation

        if user_id:
            self._active_sessions[user_id] = conversation.session_id

        self._stats["total_conversations"] += 1
        self._stats["active_sessions"] = len(self._active_sessions)

        logger.debug(f"Conversation started: {conversation.session_id}")
        return conversation.session_id

    def end_conversation(
        self,
        session_id: str,
        summary: Optional[str] = None,
    ) -> Optional[Conversation]:
        """
        Sohbet oturumunu sonlandir.

        Args:
            session_id: Oturum ID
            summary: Opsiyonel ozet

        Returns:
            Kapatilan Conversation veya None
        """
        conversation = self._conversations.get(session_id)
        if not conversation:
            logger.warning(f"Conversation not found: {session_id}")
            return None

        # Oturumu kapat
        conversation.end_conversation()

        if summary:
            conversation.summary = summary

        # Aktif oturumlardan kaldir
        if conversation.user_id and conversation.user_id in self._active_sessions:
            if self._active_sessions[conversation.user_id] == session_id:
                del self._active_sessions[conversation.user_id]

        self._stats["active_sessions"] = len(self._active_sessions)

        logger.debug(f"Conversation ended: {session_id}")
        return conversation

    def get_active_session(self, user_id: str) -> Optional[str]:
        """Kullanicinin aktif oturum ID'sini getir."""
        return self._active_sessions.get(user_id)

    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """Conversation getir."""
        return self._conversations.get(session_id)

    # ===================================================================
    # TURN MANAGEMENT
    # ===================================================================

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        emotional_valence: float = 0.0,
        emotional_arousal: float = 0.0,
        detected_emotion: Optional[str] = None,
        intent: Optional[str] = None,
        topics: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[DialogueTurn]:
        """
        Sohbete yeni tur ekle.

        Args:
            session_id: Oturum ID
            role: "user" | "agent" | "system"
            content: Mesaj icerigi
            emotional_valence: Duygusal degerlik (-1 to 1)
            emotional_arousal: Duygusal yogunluk (0 to 1)
            detected_emotion: Tespit edilen duygu
            intent: Niyet (question, statement, request, etc.)
            topics: Konular
            metadata: Ek bilgiler

        Returns:
            Eklenen DialogueTurn veya None
        """
        conversation = self._conversations.get(session_id)
        if not conversation:
            logger.warning(f"Conversation not found: {session_id}")
            return None

        if not conversation.is_active:
            logger.warning(f"Conversation is not active: {session_id}")
            return None

        # Maksimum tur kontrolu
        if conversation.turn_count >= self.config.max_turns_per_session:
            logger.warning(f"Max turns reached for conversation: {session_id}")
            return None

        # Yeni tur olustur
        turn = DialogueTurn(
            conversation_id=session_id,
            role=role,
            content=content,
            emotional_valence=emotional_valence,
            emotional_arousal=emotional_arousal,
            detected_emotion=detected_emotion,
            intent=intent,
            topics=topics or [],
            metadata=metadata or {},
        )

        # Conversation'a ekle
        conversation.add_turn(turn)

        # Keyword index'e ekle
        self._index_turn(turn)

        self._stats["total_turns"] += 1

        logger.debug(f"Turn added to {session_id}: {role}")
        return turn

    def _index_turn(self, turn: DialogueTurn) -> None:
        """Turn'u keyword index'e ekle."""
        # Basit tokenization
        words = re.findall(r'\b\w+\b', turn.content.lower())

        for word in words:
            if len(word) >= 3:  # Kisa kelimeleri atla
                if word not in self._keyword_index:
                    self._keyword_index[word] = []
                self._keyword_index[word].append(turn.id)

        self._turn_to_conversation[turn.id] = turn.conversation_id

    # ===================================================================
    # CONTEXT RETRIEVAL
    # ===================================================================

    def get_context(
        self,
        session_id: str,
        max_turns: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> List[DialogueTurn]:
        """
        Sohbet contextini getir.

        Args:
            session_id: Oturum ID
            max_turns: Maksimum tur sayisi
            max_tokens: Maksimum token (tahmini)

        Returns:
            DialogueTurn listesi (kronolojik sira)
        """
        conversation = self._conversations.get(session_id)
        if not conversation:
            return []

        max_turns = max_turns or self.config.default_context_turns
        max_tokens = max_tokens or self.config.max_context_tokens

        # Token bazli context window
        return conversation.get_context_window(max_tokens)

    def get_full_history(self, session_id: str) -> List[DialogueTurn]:
        """Tum sohbet gecmisini getir."""
        conversation = self._conversations.get(session_id)
        if not conversation:
            return []
        return list(conversation.turns)

    def get_last_n_turns(
        self,
        session_id: str,
        n: int = 5,
    ) -> List[DialogueTurn]:
        """Son n turu getir."""
        conversation = self._conversations.get(session_id)
        if not conversation:
            return []
        return conversation.get_last_n_turns(n)

    def format_context_for_llm(
        self,
        session_id: str,
        max_tokens: Optional[int] = None,
        include_system: bool = False,
    ) -> str:
        """
        LLM icin formatlanmis context string.

        Args:
            session_id: Oturum ID
            max_tokens: Maksimum token
            include_system: System mesajlarini dahil et

        Returns:
            Formatlanmis string
        """
        turns = self.get_context(session_id, max_tokens=max_tokens)

        if not include_system:
            turns = [t for t in turns if t.role != "system"]

        lines = []
        for turn in turns:
            role_label = turn.role.capitalize()
            lines.append(f"{role_label}: {turn.content}")

        return "\n".join(lines)

    # ===================================================================
    # SEARCH
    # ===================================================================

    def search_history(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Tuple[DialogueTurn, float]]:
        """
        Sohbet gecmisinde ara.

        Args:
            query: Arama sorgusu
            session_id: Belirli oturumda ara
            user_id: Belirli kullanicinin oturumlarinda ara
            limit: Maksimum sonuc

        Returns:
            (DialogueTurn, relevance_score) tuples
        """
        self._stats["searches"] += 1

        # Query'yi tokenize et
        query_words = set(re.findall(r'\b\w+\b', query.lower()))

        # Eslesenleri bul
        turn_scores: Dict[str, float] = {}

        for word in query_words:
            if word in self._keyword_index:
                for turn_id in self._keyword_index[word]:
                    if turn_id not in turn_scores:
                        turn_scores[turn_id] = 0.0
                    turn_scores[turn_id] += 1.0

        # Normalize scores
        if query_words:
            for turn_id in turn_scores:
                turn_scores[turn_id] /= len(query_words)

        # Filtreleme
        results: List[Tuple[DialogueTurn, float]] = []

        for turn_id, score in turn_scores.items():
            if score < self.config.min_search_relevance:
                continue

            conv_id = self._turn_to_conversation.get(turn_id)
            if not conv_id:
                continue

            # Session filtresi
            if session_id and conv_id != session_id:
                continue

            # User filtresi
            if user_id:
                conv = self._conversations.get(conv_id)
                if not conv or conv.user_id != user_id:
                    continue

            # Turn'u bul
            conv = self._conversations.get(conv_id)
            if conv:
                for turn in conv.turns:
                    if turn.id == turn_id:
                        results.append((turn, score))
                        break

        # Skorla sirala
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:limit]

    def search_by_topic(
        self,
        topic: str,
        limit: int = 20,
    ) -> List[Conversation]:
        """Konuya gore sohbet ara."""
        results = []

        for conv in self._conversations.values():
            if topic.lower() in [t.lower() for t in conv.main_topics]:
                results.append(conv)

        # Son erisime gore sirala
        results.sort(key=lambda c: c.last_accessed, reverse=True)
        return results[:limit]

    def search_by_emotion(
        self,
        emotion: str,
        min_intensity: float = 0.3,
        limit: int = 20,
    ) -> List[DialogueTurn]:
        """Duyguya gore tur ara."""
        results = []

        for conv in self._conversations.values():
            for turn in conv.turns:
                if turn.detected_emotion == emotion:
                    intensity = abs(turn.emotional_valence)
                    if intensity >= min_intensity:
                        results.append(turn)

        # Yogunluga gore sirala
        results.sort(key=lambda t: abs(t.emotional_valence), reverse=True)
        return results[:limit]

    # ===================================================================
    # EPISODE INTEGRATION
    # ===================================================================

    def conversation_to_episode(
        self,
        session_id: str,
        episode_type: EpisodeType = EpisodeType.INTERACTION,
    ) -> Optional[Episode]:
        """
        Conversation'i Episode'a donustur.

        Episodic memory ile entegrasyon icin.
        """
        conversation = self._conversations.get(session_id)
        if not conversation:
            return None

        # Duygusal ozet
        avg_valence = conversation.average_valence
        dominant_emotion = conversation.dominant_emotion

        # Katilimcilar
        participants = []
        if conversation.user_id:
            participants.append(conversation.user_id)
        if conversation.agent_id:
            participants.append(conversation.agent_id)

        # Episode olustur
        episode = Episode(
            what=conversation.summary or f"Conversation with {len(conversation.turns)} turns",
            where="conversation",
            when=conversation.started_at,
            who=participants,
            episode_type=episode_type,
            duration_seconds=conversation.get_duration_seconds(),
            outcome=f"Topics: {', '.join(conversation.main_topics)}" if conversation.main_topics else "",
            outcome_valence=avg_valence,
            emotional_valence=avg_valence,
            self_emotion_during=dominant_emotion,
            importance=conversation.importance,
            tags=["conversation"] + conversation.main_topics,
            context={
                "session_id": session_id,
                "turn_count": conversation.turn_count,
                "coherence": conversation.coherence_score,
                "engagement": conversation.engagement_score,
            },
        )

        # Episode ID'yi conversation'a bagla
        conversation.episode_id = episode.id

        return episode

    # ===================================================================
    # MAINTENANCE
    # ===================================================================

    def cleanup_inactive_sessions(
        self,
        timeout_minutes: Optional[float] = None,
    ) -> int:
        """
        Inaktif oturumlari kapat.

        Returns:
            Kapatilan oturum sayisi
        """
        timeout = timeout_minutes or self.config.session_timeout_minutes
        cutoff = datetime.now() - timedelta(minutes=timeout)

        closed = 0
        sessions_to_close = []

        for session_id, conv in self._conversations.items():
            if conv.is_active and conv.last_accessed < cutoff:
                sessions_to_close.append(session_id)

        for session_id in sessions_to_close:
            self.end_conversation(session_id, summary="Session timed out")
            closed += 1

        if closed > 0:
            logger.info(f"Closed {closed} inactive sessions")

        return closed

    def get_user_conversations(
        self,
        user_id: str,
        include_inactive: bool = False,
        limit: int = 50,
    ) -> List[Conversation]:
        """Kullanicinin sohbetlerini getir."""
        results = []

        for conv in self._conversations.values():
            if conv.user_id == user_id:
                if include_inactive or conv.is_active:
                    results.append(conv)

        # Son erisime gore sirala
        results.sort(key=lambda c: c.last_accessed, reverse=True)
        return results[:limit]

    # ===================================================================
    # STATS & DEBUG
    # ===================================================================

    @property
    def stats(self) -> Dict[str, Any]:
        """Conversation memory istatistikleri."""
        return {
            **self._stats,
            "conversations_in_memory": len(self._conversations),
            "keywords_indexed": len(self._keyword_index),
            "turns_indexed": len(self._turn_to_conversation),
        }

    def debug_dump(self) -> Dict[str, Any]:
        """Debug icin tam dump."""
        return {
            "config": self.config.__dict__,
            "stats": self.stats,
            "active_sessions": dict(self._active_sessions),
            "conversations": {
                k: {
                    "user_id": v.user_id,
                    "turns": v.turn_count,
                    "active": v.is_active,
                    "topics": v.main_topics,
                    "avg_valence": v.average_valence,
                }
                for k, v in self._conversations.items()
            },
        }


# ========================================================================
# FACTORY
# ========================================================================

_conversation_memory: Optional[ConversationMemory] = None


def get_conversation_memory(
    config: Optional[ConversationConfig] = None,
) -> ConversationMemory:
    """Conversation memory singleton."""
    global _conversation_memory

    if _conversation_memory is None:
        _conversation_memory = ConversationMemory(config)

    return _conversation_memory


def reset_conversation_memory() -> None:
    """Reset conversation memory singleton (test icin)."""
    global _conversation_memory
    _conversation_memory = None


def create_conversation_memory(
    config: Optional[ConversationConfig] = None,
) -> ConversationMemory:
    """Yeni conversation memory olustur (test icin)."""
    return ConversationMemory(config)
