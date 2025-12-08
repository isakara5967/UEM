"""
tests/unit/test_conversation_memory.py

Conversation Memory modulu unit testleri.
DialogueTurn, Conversation ve ConversationMemory testleri.
"""

import pytest
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from core.memory import (
    create_memory_store,
    MemoryConfig,
    DialogueTurn,
    Conversation,
    ConversationMemory,
    ConversationConfig,
    create_conversation_memory,
    Episode,
    EpisodeType,
)


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def conv_memory():
    """Fresh conversation memory for each test."""
    return create_conversation_memory()


@pytest.fixture
def conv_memory_with_config():
    """Conversation memory with custom config."""
    config = ConversationConfig(
        default_context_turns=5,
        max_context_tokens=2000,
        session_timeout_minutes=10.0,
        max_turns_per_session=50,
    )
    return create_conversation_memory(config)


@pytest.fixture
def store():
    """Memory store with conversation memory."""
    return create_memory_store()


# ========================================================================
# DIALOGUE TURN TESTS
# ========================================================================

class TestDialogueTurn:
    """DialogueTurn dataclass testleri."""

    def test_create_dialogue_turn(self):
        """DialogueTurn olusturma."""
        turn = DialogueTurn(
            role="user",
            content="Hello!",
            emotional_valence=0.5,
        )
        assert turn.role == "user"
        assert turn.content == "Hello!"
        assert turn.emotional_valence == 0.5
        assert turn.id is not None

    def test_dialogue_turn_defaults(self):
        """Varsayilan degerler."""
        turn = DialogueTurn()
        assert turn.role == "user"
        assert turn.content == ""
        assert turn.emotional_valence == 0.0
        assert turn.emotional_arousal == 0.0
        assert turn.topics == []
        assert turn.metadata == {}

    def test_dialogue_turn_with_topics(self):
        """Konu etiketleri."""
        turn = DialogueTurn(
            role="agent",
            content="Let me help you with that.",
            topics=["assistance", "support"],
            intent="response",
        )
        assert "assistance" in turn.topics
        assert turn.intent == "response"

    def test_dialogue_turn_with_emotion(self):
        """Duygusal analiz alanlari."""
        turn = DialogueTurn(
            role="user",
            content="I'm so happy!",
            emotional_valence=0.9,
            emotional_arousal=0.8,
            detected_emotion="joy",
        )
        assert turn.emotional_valence == 0.9
        assert turn.detected_emotion == "joy"


# ========================================================================
# CONVERSATION TESTS
# ========================================================================

class TestConversation:
    """Conversation dataclass testleri."""

    def test_create_conversation(self):
        """Conversation olusturma."""
        conv = Conversation(
            user_id="user1",
            agent_id="agent1",
        )
        assert conv.user_id == "user1"
        assert conv.agent_id == "agent1"
        assert conv.is_active is True
        assert conv.turn_count == 0
        assert conv.session_id is not None

    def test_add_turn_to_conversation(self):
        """Conversation'a turn ekleme."""
        conv = Conversation(user_id="user1")
        turn = DialogueTurn(role="user", content="Hello!")

        conv.add_turn(turn)

        assert conv.turn_count == 1
        assert len(conv.turns) == 1
        assert conv.turns[0].conversation_id == conv.session_id

    def test_emotional_arc_tracking(self):
        """Duygusal akis takibi."""
        conv = Conversation()

        conv.add_turn(DialogueTurn(role="user", content="Hi", emotional_valence=0.5))
        conv.add_turn(DialogueTurn(role="agent", content="Hello!", emotional_valence=0.6))
        conv.add_turn(DialogueTurn(role="user", content="Great!", emotional_valence=0.8))

        assert len(conv.emotional_arc) == 3
        assert conv.average_valence == pytest.approx(0.633, abs=0.01)

    def test_topic_tracking(self):
        """Konu takibi."""
        conv = Conversation()

        conv.add_turn(DialogueTurn(role="user", content="Weather?", topics=["weather"]))
        conv.add_turn(DialogueTurn(role="agent", content="Sunny!", topics=["weather"]))
        conv.add_turn(DialogueTurn(role="user", content="Travel?", topics=["travel"]))

        assert "weather" in conv.main_topics
        assert "travel" in conv.main_topics
        assert len(conv.main_topics) == 2

    def test_get_last_n_turns(self):
        """Son n turu getir."""
        conv = Conversation()
        for i in range(10):
            conv.add_turn(DialogueTurn(role="user", content=f"Message {i}"))

        last_3 = conv.get_last_n_turns(3)
        assert len(last_3) == 3
        assert last_3[0].content == "Message 7"
        assert last_3[2].content == "Message 9"

    def test_get_context_window(self):
        """Context window token limiti."""
        conv = Conversation()
        # Her mesaj ~50 karakter = ~12 token
        for i in range(100):
            conv.add_turn(DialogueTurn(
                role="user",
                content=f"This is message number {i} with some padding text.",
            ))

        # 500 token limiti = ~2000 karakter
        context = conv.get_context_window(max_tokens=500)

        total_chars = sum(len(t.content) for t in context)
        assert total_chars <= 500 * 4  # 4 char/token

    def test_end_conversation(self):
        """Sohbeti sonlandir."""
        conv = Conversation()
        conv.add_turn(DialogueTurn(role="user", content="Bye"))

        conv.end_conversation()

        assert conv.is_active is False
        assert conv.ended_at is not None

    def test_get_duration(self):
        """Sohbet suresi hesaplama."""
        conv = Conversation()
        conv.add_turn(DialogueTurn(role="user", content="Hi"))

        duration = conv.get_duration_seconds()
        assert duration >= 0

    def test_to_text(self):
        """Metin formatina donusum."""
        conv = Conversation()
        conv.add_turn(DialogueTurn(role="user", content="Hello"))
        conv.add_turn(DialogueTurn(role="agent", content="Hi there!"))

        text = conv.to_text()
        assert "[User]: Hello" in text
        assert "[Agent]: Hi there!" in text


# ========================================================================
# CONVERSATION MEMORY TESTS
# ========================================================================

class TestConversationMemory:
    """ConversationMemory class testleri."""

    def test_start_conversation(self, conv_memory):
        """Sohbet baslatma."""
        session_id = conv_memory.start_conversation(user_id="user1")

        assert session_id is not None
        conv = conv_memory.get_conversation(session_id)
        assert conv is not None
        assert conv.user_id == "user1"
        assert conv.is_active is True

    def test_start_conversation_closes_previous(self, conv_memory):
        """Yeni sohbet eski sohbeti kapatir."""
        session1 = conv_memory.start_conversation(user_id="user1")
        session2 = conv_memory.start_conversation(user_id="user1")

        conv1 = conv_memory.get_conversation(session1)
        conv2 = conv_memory.get_conversation(session2)

        assert conv1.is_active is False
        assert conv2.is_active is True
        assert session1 != session2

    def test_add_turn(self, conv_memory):
        """Turn ekleme."""
        session_id = conv_memory.start_conversation()

        turn = conv_memory.add_turn(
            session_id=session_id,
            role="user",
            content="Hello!",
            emotional_valence=0.5,
        )

        assert turn is not None
        assert turn.content == "Hello!"

        conv = conv_memory.get_conversation(session_id)
        assert conv.turn_count == 1

    def test_add_turn_to_inactive_fails(self, conv_memory):
        """Kapatilmis sohbete turn eklenemez."""
        session_id = conv_memory.start_conversation()
        conv_memory.end_conversation(session_id)

        turn = conv_memory.add_turn(session_id, "user", "Hello")
        assert turn is None

    def test_add_turn_with_topics(self, conv_memory):
        """Topic ile turn ekleme."""
        session_id = conv_memory.start_conversation()

        conv_memory.add_turn(
            session_id=session_id,
            role="user",
            content="Tell me about weather",
            topics=["weather", "forecast"],
        )

        conv = conv_memory.get_conversation(session_id)
        assert "weather" in conv.main_topics
        assert "forecast" in conv.main_topics

    def test_get_context(self, conv_memory):
        """Context getirme."""
        session_id = conv_memory.start_conversation()

        for i in range(5):
            conv_memory.add_turn(session_id, "user", f"Message {i}")

        context = conv_memory.get_context(session_id)
        assert len(context) == 5

    def test_get_context_with_limit(self, conv_memory):
        """Context token limiti."""
        session_id = conv_memory.start_conversation()

        for i in range(100):
            conv_memory.add_turn(session_id, "user", f"Long message content {i} " * 10)

        context = conv_memory.get_context(session_id, max_tokens=500)

        # Token limiti uygulanmis olmali
        total_chars = sum(len(t.content) for t in context)
        assert total_chars <= 500 * 4 + 100  # 4 char/token + tolerance

    def test_get_full_history(self, conv_memory):
        """Tam gecmis."""
        session_id = conv_memory.start_conversation()

        for i in range(10):
            conv_memory.add_turn(session_id, "user", f"Message {i}")

        history = conv_memory.get_full_history(session_id)
        assert len(history) == 10

    def test_get_last_n_turns(self, conv_memory):
        """Son n turn."""
        session_id = conv_memory.start_conversation()

        for i in range(10):
            conv_memory.add_turn(session_id, "user", f"Message {i}")

        last_3 = conv_memory.get_last_n_turns(session_id, 3)
        assert len(last_3) == 3

    def test_format_context_for_llm(self, conv_memory):
        """LLM icin formatlama."""
        session_id = conv_memory.start_conversation()

        conv_memory.add_turn(session_id, "user", "Hello")
        conv_memory.add_turn(session_id, "agent", "Hi there!")

        formatted = conv_memory.format_context_for_llm(session_id)

        assert "User: Hello" in formatted
        assert "Agent: Hi there!" in formatted

    def test_end_conversation(self, conv_memory):
        """Sohbeti sonlandirma."""
        session_id = conv_memory.start_conversation(user_id="user1")
        conv_memory.add_turn(session_id, "user", "Bye")

        result = conv_memory.end_conversation(session_id, summary="Test summary")

        assert result is not None
        assert result.is_active is False
        assert result.summary == "Test summary"

    def test_get_active_session(self, conv_memory):
        """Aktif oturumu getirme."""
        session_id = conv_memory.start_conversation(user_id="user1")

        active = conv_memory.get_active_session("user1")
        assert active == session_id

    def test_search_history_by_keyword(self, conv_memory):
        """Keyword ile arama."""
        session_id = conv_memory.start_conversation()

        conv_memory.add_turn(session_id, "user", "Tell me about Python programming")
        conv_memory.add_turn(session_id, "agent", "Python is a great language")
        conv_memory.add_turn(session_id, "user", "What about JavaScript?")

        results = conv_memory.search_history("Python")

        assert len(results) >= 1
        # Ilk sonuc en alakali olmali
        assert "Python" in results[0][0].content or "python" in results[0][0].content.lower()

    def test_search_by_topic(self, conv_memory):
        """Topic ile arama."""
        session1 = conv_memory.start_conversation(user_id="user1")
        conv_memory.add_turn(session1, "user", "Weather?", topics=["weather"])
        conv_memory.end_conversation(session1)

        session2 = conv_memory.start_conversation(user_id="user2")
        conv_memory.add_turn(session2, "user", "Travel?", topics=["travel"])

        results = conv_memory.search_by_topic("weather")
        assert len(results) >= 1

    def test_search_by_emotion(self, conv_memory):
        """Duygu ile arama."""
        session_id = conv_memory.start_conversation()

        conv_memory.add_turn(
            session_id, "user", "I'm so happy!",
            emotional_valence=0.9,
            detected_emotion="joy",
        )
        conv_memory.add_turn(
            session_id, "user", "This is sad",
            emotional_valence=-0.7,
            detected_emotion="sadness",
        )

        results = conv_memory.search_by_emotion("joy")
        assert len(results) >= 1
        assert results[0].detected_emotion == "joy"

    def test_conversation_to_episode(self, conv_memory):
        """Conversation'i Episode'a donusturme."""
        session_id = conv_memory.start_conversation(user_id="user1", agent_id="agent1")

        conv_memory.add_turn(session_id, "user", "Hello!")
        conv_memory.add_turn(session_id, "agent", "Hi there!")
        conv_memory.end_conversation(session_id, summary="Greeting exchange")

        episode = conv_memory.conversation_to_episode(session_id)

        assert episode is not None
        assert "user1" in episode.who
        assert episode.episode_type == EpisodeType.INTERACTION

    def test_get_user_conversations(self, conv_memory):
        """Kullanici sohbetlerini getirme."""
        # 3 sohbet olustur
        for i in range(3):
            session = conv_memory.start_conversation(user_id="user1")
            conv_memory.add_turn(session, "user", f"Message {i}")
            if i < 2:
                conv_memory.end_conversation(session)

        convs = conv_memory.get_user_conversations("user1", include_inactive=True)
        assert len(convs) == 3

        active_only = conv_memory.get_user_conversations("user1", include_inactive=False)
        assert len(active_only) == 1

    def test_stats(self, conv_memory):
        """Istatistikler."""
        session_id = conv_memory.start_conversation()
        conv_memory.add_turn(session_id, "user", "Hello")
        conv_memory.add_turn(session_id, "agent", "Hi")

        stats = conv_memory.stats
        assert stats["total_conversations"] >= 1
        assert stats["total_turns"] >= 2

    def test_max_turns_limit(self, conv_memory_with_config):
        """Maksimum turn limiti."""
        session_id = conv_memory_with_config.start_conversation()

        # Config'de max_turns_per_session=50
        for i in range(60):
            result = conv_memory_with_config.add_turn(
                session_id, "user", f"Message {i}"
            )
            if i >= 50:
                assert result is None, f"Turn {i} should fail due to limit"


# ========================================================================
# MEMORY STORE INTEGRATION TESTS
# ========================================================================

class TestMemoryStoreConversation:
    """MemoryStore conversation entegrasyonu."""

    def test_store_has_conversation_memory(self, store):
        """Store'da conversation memory var."""
        assert hasattr(store, 'conversation')
        assert isinstance(store.conversation, ConversationMemory)

    def test_conversation_through_store(self, store):
        """Store uzerinden conversation kullanimi."""
        session_id = store.conversation.start_conversation(user_id="test_user")
        store.conversation.add_turn(session_id, "user", "Hello via store!")

        context = store.conversation.get_context(session_id)
        assert len(context) == 1

    def test_store_stats_include_conversation(self, store):
        """Store stats conversation iceriyor."""
        session_id = store.conversation.start_conversation()
        store.conversation.add_turn(session_id, "user", "Test")

        stats = store.stats
        assert "conversation_total_conversations" in stats
        assert "conversation_total_turns" in stats


# ========================================================================
# EDGE CASES
# ========================================================================

class TestConversationEdgeCases:
    """Edge case testleri."""

    def test_empty_content(self, conv_memory):
        """Bos icerik."""
        session_id = conv_memory.start_conversation()
        turn = conv_memory.add_turn(session_id, "user", "")
        assert turn is not None
        assert turn.content == ""

    def test_very_long_content(self, conv_memory):
        """Cok uzun icerik."""
        session_id = conv_memory.start_conversation()
        long_content = "x" * 10000
        turn = conv_memory.add_turn(session_id, "user", long_content)
        assert turn is not None
        assert len(turn.content) == 10000

    def test_special_characters(self, conv_memory):
        """Ozel karakterler."""
        session_id = conv_memory.start_conversation()
        content = "Hello! 👋 @user #topic $100 <html> 'quotes' \"double\""
        turn = conv_memory.add_turn(session_id, "user", content)
        assert turn.content == content

    def test_nonexistent_session(self, conv_memory):
        """Olmayan oturum."""
        context = conv_memory.get_context("nonexistent-session-id")
        assert context == []

        turn = conv_memory.add_turn("nonexistent", "user", "Hello")
        assert turn is None

    def test_search_empty_query(self, conv_memory):
        """Bos arama sorgusu."""
        results = conv_memory.search_history("")
        assert results == []

    def test_concurrent_users(self, conv_memory):
        """Ayni anda birden fazla kullanici."""
        session1 = conv_memory.start_conversation(user_id="user1")
        session2 = conv_memory.start_conversation(user_id="user2")
        session3 = conv_memory.start_conversation(user_id="user3")

        conv_memory.add_turn(session1, "user", "User 1 message")
        conv_memory.add_turn(session2, "user", "User 2 message")
        conv_memory.add_turn(session3, "user", "User 3 message")

        assert conv_memory.get_active_session("user1") == session1
        assert conv_memory.get_active_session("user2") == session2
        assert conv_memory.get_active_session("user3") == session3

    def test_unicode_content(self, conv_memory):
        """Unicode karakterler."""
        session_id = conv_memory.start_conversation()
        content = "Merhaba! 你好! مرحبا! Привет! 🎉"
        turn = conv_memory.add_turn(session_id, "user", content)
        assert turn.content == content
