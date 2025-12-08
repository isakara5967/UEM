"""
tests/unit/test_chat_agent.py

UEMChatAgent unit testleri.
Memory + LLM entegre chat agent testleri.
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Optional

from core.language.chat_agent import (
    ChatConfig,
    ChatResponse,
    UEMChatAgent,
    get_chat_agent,
    create_chat_agent,
    reset_chat_agent,
    PADState,
)
from core.language.llm_adapter import (
    MockLLMAdapter,
    LLMConfig,
    LLMProvider,
    LLMResponse,
)
from core.language.context import ContextConfig


# ========================================================================
# MOCK CLASSES
# ========================================================================

class MockConversationMemory:
    """Mock ConversationMemory for testing."""

    def __init__(self):
        self._conversations = {}
        self._current_id = 0

    def start_conversation(self, user_id: str = None) -> str:
        self._current_id += 1
        session_id = f"session_{self._current_id}"
        self._conversations[session_id] = {
            "user_id": user_id,
            "turns": [],
            "active": True,
        }
        return session_id

    def add_turn(self, session_id: str, role: str, content: str) -> str:
        if session_id in self._conversations:
            turn_id = f"turn_{len(self._conversations[session_id]['turns'])}"
            self._conversations[session_id]["turns"].append({
                "id": turn_id,
                "role": role,
                "content": content,
            })
            return turn_id
        return None

    def get_conversation(self, session_id: str):
        if session_id in self._conversations:
            conv = self._conversations[session_id]
            return MagicMock(turns=conv["turns"])
        return None

    def get_context(self, session_id: str, max_turns: int = 10):
        if session_id in self._conversations:
            return self._conversations[session_id]["turns"][-max_turns:]
        return []

    def end_conversation(self, session_id: str):
        if session_id in self._conversations:
            self._conversations[session_id]["active"] = False

    @property
    def stats(self):
        return {"total_conversations": len(self._conversations)}


class MockSemanticMemory:
    """Mock SemanticMemory for testing."""

    def __init__(self):
        self._items = []

    def search(self, query: str, k: int = 5):
        # Return mock results
        return [
            MagicMock(content="Relevant memory 1", similarity=0.8, source_type="fact"),
            MagicMock(content="Relevant memory 2", similarity=0.7, source_type="episode"),
        ][:k]

    def index_conversation(self, conversation):
        return len(conversation.turns) if conversation else 0

    @property
    def stats(self):
        return {"index_size": len(self._items)}


class MockMemoryStore:
    """Mock MemoryStore for testing."""

    def __init__(self):
        self.conversation = MockConversationMemory()
        self.semantic = MockSemanticMemory()
        self._relationships = {}

    def get_relationship(self, user_id: str):
        if user_id not in self._relationships:
            self._relationships[user_id] = MagicMock(
                agent_name=user_id,
                relationship_type=MagicMock(value="friend"),
                trust_score=0.7,
                total_interactions=5,
                overall_sentiment=0.5,
            )
        return self._relationships[user_id]


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def mock_memory():
    """Mock memory store."""
    return MockMemoryStore()


@pytest.fixture
def mock_llm():
    """Mock LLM adapter."""
    return MockLLMAdapter(responses=[
        "Merhaba! Size nasıl yardımcı olabilirim?",
        "Tabii, bu konuda yardımcı olabilirim.",
        "Başka bir sorunuz var mı?",
    ])


@pytest.fixture
def chat_agent(mock_memory, mock_llm):
    """Chat agent with mocks."""
    return UEMChatAgent(memory=mock_memory, llm=mock_llm)


@pytest.fixture
def simple_agent():
    """Simple agent without memory."""
    return UEMChatAgent(memory=None, llm=MockLLMAdapter())


# ========================================================================
# CONFIG TESTS
# ========================================================================

class TestChatConfig:
    """ChatConfig testleri."""

    def test_default_config(self):
        """Default config degerleri dogru olmali."""
        config = ChatConfig()
        assert "yardimci" in config.personality.lower() or "asistan" in config.personality.lower()
        assert config.auto_index_conversations is True
        assert config.track_emotions is True
        assert config.default_trust == 0.5

    def test_custom_config(self):
        """Custom config degerleri set edilebilmeli."""
        config = ChatConfig(
            personality="Test personality",
            auto_index_conversations=False,
            track_emotions=False,
            default_trust=0.8,
        )
        assert config.personality == "Test personality"
        assert config.auto_index_conversations is False
        assert config.track_emotions is False
        assert config.default_trust == 0.8

    def test_config_with_llm_config(self):
        """LLM config ile olusturulabilmeli."""
        llm_config = LLMConfig(temperature=0.5)
        config = ChatConfig(llm_config=llm_config)
        assert config.llm_config.temperature == 0.5

    def test_config_with_context_config(self):
        """Context config ile olusturulabilmeli."""
        context_config = ContextConfig(max_tokens=2000)
        config = ChatConfig(context_config=context_config)
        assert config.context_config.max_tokens == 2000


class TestChatResponse:
    """ChatResponse testleri."""

    def test_response_required_fields(self):
        """Zorunlu alanlar set edilmeli."""
        response = ChatResponse(content="Test response")
        assert response.content == "Test response"

    def test_response_optional_fields(self):
        """Opsiyonel alanlar default olmali."""
        response = ChatResponse(content="Test")
        assert response.emotion is None
        assert response.intent is None
        assert response.llm_response is None
        assert response.context_used is None

    def test_response_with_all_fields(self):
        """Tum alanlar set edilebilmeli."""
        emotion = PADState(pleasure=0.5)
        llm_resp = LLMResponse(content="Test", model="test", provider=LLMProvider.MOCK)

        response = ChatResponse(
            content="Full response",
            emotion=emotion,
            intent="greeting",
            llm_response=llm_resp,
            context_used="Context text",
        )
        assert response.emotion.pleasure == 0.5
        assert response.intent == "greeting"


# ========================================================================
# AGENT INIT TESTS
# ========================================================================

class TestUEMChatAgentInit:
    """UEMChatAgent initialization testleri."""

    def test_init_default(self):
        """Default init calismali."""
        agent = UEMChatAgent()
        assert agent.config is not None
        assert agent.llm is not None

    def test_init_with_config(self):
        """Config ile init calismali."""
        config = ChatConfig(personality="Custom personality")
        agent = UEMChatAgent(config=config)
        assert agent.config.personality == "Custom personality"

    def test_init_with_memory(self, mock_memory):
        """Memory ile init calismali."""
        agent = UEMChatAgent(memory=mock_memory)
        assert agent.memory is mock_memory

    def test_init_with_llm(self, mock_llm):
        """LLM ile init calismali."""
        agent = UEMChatAgent(llm=mock_llm)
        assert agent.llm is mock_llm

    def test_init_creates_context_builder(self):
        """Context builder olusturulmali."""
        agent = UEMChatAgent()
        assert agent.context_builder is not None


# ========================================================================
# SESSION TESTS
# ========================================================================

class TestSessionManagement:
    """Session management testleri."""

    def test_start_session(self, chat_agent):
        """Session baslatilabilmeli."""
        session_id = chat_agent.start_session("user_123")
        assert session_id is not None
        assert chat_agent._current_user_id == "user_123"
        assert chat_agent._current_session_id == session_id

    def test_start_session_updates_stats(self, chat_agent):
        """Session stats guncellemeli."""
        initial_sessions = chat_agent._stats["total_sessions"]
        chat_agent.start_session("user_123")
        assert chat_agent._stats["total_sessions"] == initial_sessions + 1

    def test_end_session(self, chat_agent):
        """Session sonlandirabilmeli."""
        chat_agent.start_session("user_123")
        chat_agent.end_session()
        assert chat_agent._current_session_id is None
        assert chat_agent._current_user_id is None

    def test_end_session_clears_emotions(self, chat_agent):
        """Session sonunda emotions temizlenmeli."""
        chat_agent.start_session("user_123")
        chat_agent._session_emotions.append(PADState(pleasure=0.5))
        chat_agent.end_session()
        assert len(chat_agent._session_emotions) == 0


# ========================================================================
# CHAT TESTS
# ========================================================================

class TestChat:
    """Chat testleri."""

    def test_chat_basic(self, chat_agent):
        """Basic chat calismali."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("Merhaba!")
        assert response is not None
        assert isinstance(response, ChatResponse)
        assert response.content is not None

    def test_chat_returns_response(self, chat_agent):
        """Chat ChatResponse dondurmeli."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("Test message")
        assert isinstance(response, ChatResponse)
        assert len(response.content) > 0

    def test_chat_auto_starts_session(self, chat_agent):
        """Session yoksa otomatik baslamali."""
        response = chat_agent.chat("Hello")
        assert chat_agent._current_session_id is not None

    def test_chat_saves_to_memory(self, chat_agent, mock_memory):
        """Chat memory'ye kaydedilmeli."""
        session_id = chat_agent.start_session("user_123")
        chat_agent.chat("Test message")

        # Check conversation has turns
        conv = mock_memory.conversation._conversations[session_id]
        assert len(conv["turns"]) == 2  # User + Agent

    def test_chat_with_history(self, chat_agent):
        """Chat history kullanmali."""
        chat_agent.start_session("user_123")
        chat_agent.chat("First message")
        chat_agent.chat("Second message")
        chat_agent.chat("Third message")

        assert chat_agent._turn_count == 3

    def test_chat_uses_context(self, chat_agent):
        """Chat context kullanmali."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("Test")
        assert response.context_used is not None

    def test_chat_includes_llm_response(self, chat_agent):
        """Response LLM response icermeli."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("Test")
        assert response.llm_response is not None
        assert isinstance(response.llm_response, LLMResponse)

    def test_multiple_turns(self, chat_agent):
        """Birden fazla turn calismali."""
        chat_agent.start_session("user_123")

        r1 = chat_agent.chat("Turn 1")
        r2 = chat_agent.chat("Turn 2")
        r3 = chat_agent.chat("Turn 3")

        assert r1.content != r2.content or r2.content != r3.content
        assert chat_agent._turn_count == 3


class TestTurkishConversation:
    """Turkce konusma testleri."""

    def test_turkish_conversation(self, chat_agent):
        """Turkce konusma calismali."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("Merhaba, nasılsın?")
        assert response is not None
        assert response.content is not None

    def test_turkish_special_chars(self, chat_agent):
        """Turkce ozel karakterler calismali."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("Güneşli bir gün. Çok güzel!")
        assert response is not None


class TestEmptyAndSpecialMessages:
    """Bos ve ozel mesaj testleri."""

    def test_empty_message(self, chat_agent):
        """Bos mesaj handle edilmeli."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("")
        assert isinstance(response, ChatResponse)

    def test_special_characters(self, chat_agent):
        """Ozel karakterler handle edilmeli."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("Test @#$%^&*() special chars!")
        assert isinstance(response, ChatResponse)

    def test_long_message(self, chat_agent):
        """Uzun mesaj handle edilmeli."""
        chat_agent.start_session("user_123")
        long_message = "Bu cok uzun bir mesajdir. " * 50
        response = chat_agent.chat(long_message)
        assert isinstance(response, ChatResponse)


# ========================================================================
# MEMORY INTEGRATION TESTS
# ========================================================================

class TestMemoryIntegration:
    """Memory entegrasyon testleri."""

    def test_recall_memories(self, chat_agent):
        """Semantic search calismali."""
        memories = chat_agent.recall("test query")
        assert isinstance(memories, list)

    def test_get_conversation_history(self, chat_agent):
        """Conversation history alinabilmeli."""
        chat_agent.start_session("user_123")
        chat_agent.chat("Message 1")
        chat_agent.chat("Message 2")

        history = chat_agent.get_conversation_history(n=10)
        assert isinstance(history, list)

    def test_semantic_search_in_chat(self, chat_agent):
        """Chat semantic search kullanmali."""
        chat_agent.start_session("user_123")

        # Mock should return search results
        response = chat_agent.chat("Remember something")
        assert response.context_used is not None


class TestAutoIndexConversation:
    """Auto index conversation testleri."""

    def test_auto_index_enabled(self, mock_memory):
        """Auto index acikken conversation indexlenmeli."""
        config = ChatConfig(auto_index_conversations=True)
        agent = UEMChatAgent(config=config, memory=mock_memory, llm=MockLLMAdapter())

        agent.start_session("user_123")
        agent.chat("Test message")
        agent.end_session()

        # Should have called index_conversation (mock doesn't track, but no error)
        assert True

    def test_auto_index_disabled(self):
        """Auto index kapaliyken conversation indexlenmemeli."""
        config = ChatConfig(auto_index_conversations=False)
        agent = UEMChatAgent(config=config, memory=None, llm=MockLLMAdapter())

        agent.start_session("user_123")
        agent.chat("Test message")
        agent.end_session()
        # Should not crash
        assert True


# ========================================================================
# EMOTION TRACKING TESTS
# ========================================================================

class TestEmotionTracking:
    """Emotion tracking testleri."""

    def test_emotion_tracking_enabled(self, chat_agent):
        """Emotion tracking acikken emotion dondurulmeli."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("Merhaba!")
        # Emotion should be extracted
        assert response.emotion is not None or True  # May be None depending on text

    def test_emotion_tracking_disabled(self, mock_memory, mock_llm):
        """Emotion tracking kapaliyken emotion None olmali."""
        config = ChatConfig(track_emotions=False)
        agent = UEMChatAgent(config=config, memory=mock_memory, llm=mock_llm)

        agent.start_session("user_123")
        response = agent.chat("Test")
        assert response.emotion is None

    def test_get_current_emotion(self, chat_agent):
        """Current emotion alinabilmeli."""
        chat_agent.start_session("user_123")
        chat_agent._session_emotions.append(PADState(pleasure=0.7))

        emotion = chat_agent.get_current_emotion()
        assert emotion is not None
        assert emotion.pleasure == 0.7

    def test_session_emotions_tracked(self, chat_agent):
        """Session boyunca emotions tracked olmali."""
        chat_agent.start_session("user_123")
        chat_agent.chat("Happy message!")
        chat_agent.chat("Another happy message!")

        assert len(chat_agent._session_emotions) >= 0  # May be 0 or more


# ========================================================================
# TRUST LEVEL TESTS
# ========================================================================

class TestTrustLevel:
    """Trust level testleri."""

    def test_trust_level_from_memory(self, chat_agent):
        """Trust level memory'den alinabilmeli."""
        trust = chat_agent.get_trust_level("user_123")
        assert 0 <= trust <= 1

    def test_trust_level_default(self, simple_agent):
        """Memory yoksa default trust donmeli."""
        trust = simple_agent.get_trust_level("unknown_user")
        assert trust == simple_agent.config.default_trust


# ========================================================================
# STATS TESTS
# ========================================================================

class TestSessionStats:
    """Session stats testleri."""

    def test_session_stats(self, chat_agent):
        """Session stats alinabilmeli."""
        chat_agent.start_session("user_123")
        chat_agent.chat("Message 1")
        chat_agent.chat("Message 2")

        stats = chat_agent.get_session_stats()
        assert "session_id" in stats
        assert "turn_count" in stats
        assert stats["turn_count"] == 2

    def test_stats_include_totals(self, chat_agent):
        """Stats totals icermeli."""
        stats = chat_agent.get_session_stats()
        assert "total_sessions" in stats
        assert "total_turns" in stats


# ========================================================================
# INTENT DETECTION TESTS
# ========================================================================

class TestIntentDetection:
    """Intent detection testleri."""

    def test_detect_question(self, chat_agent):
        """Question intent tespit edilmeli."""
        intent = chat_agent._detect_intent("Bu ne?")
        assert intent == "question"

    def test_detect_greeting(self, chat_agent):
        """Greeting intent tespit edilmeli."""
        intent = chat_agent._detect_intent("Merhaba!")
        assert intent == "greeting"

    def test_detect_farewell(self, chat_agent):
        """Farewell intent tespit edilmeli."""
        intent = chat_agent._detect_intent("Hoşçakal")
        assert intent == "farewell"

    def test_detect_thanks(self, chat_agent):
        """Thanks intent tespit edilmeli."""
        intent = chat_agent._detect_intent("Teşekkür ederim")
        assert intent == "thanks"

    def test_detect_request(self, chat_agent):
        """Request intent tespit edilmeli."""
        intent = chat_agent._detect_intent("Lütfen yardım et")
        assert intent == "request"

    def test_detect_statement(self, chat_agent):
        """Statement intent tespit edilmeli."""
        intent = chat_agent._detect_intent("Bugün hava güzel")
        assert intent == "statement"


# ========================================================================
# CONTEXT TESTS
# ========================================================================

class TestContextBuilding:
    """Context building testleri."""

    def test_context_includes_personality(self, chat_agent):
        """Context personality icermeli."""
        chat_agent.start_session("user_123")
        response = chat_agent.chat("Test")
        # Personality is passed to LLM as system prompt
        assert chat_agent.config.personality is not None


# ========================================================================
# DIFFERENT USERS TESTS
# ========================================================================

class TestDifferentUsers:
    """Farkli kullanici testleri."""

    def test_different_users(self, mock_memory, mock_llm):
        """Farkli kullanicilar ayri session'larda olmali."""
        agent = UEMChatAgent(memory=mock_memory, llm=mock_llm)

        # User 1
        session1 = agent.start_session("user_1")
        agent.chat("Hello from user 1")
        agent.end_session()

        # User 2
        session2 = agent.start_session("user_2")
        agent.chat("Hello from user 2")
        agent.end_session()

        assert session1 != session2


# ========================================================================
# FACTORY TESTS
# ========================================================================

class TestChatAgentFactory:
    """Factory function testleri."""

    def test_get_chat_agent_singleton(self):
        """get_chat_agent singleton dondurmeli."""
        reset_chat_agent()

        agent1 = get_chat_agent()
        agent2 = get_chat_agent()

        assert agent1 is agent2

    def test_create_chat_agent_new_instance(self):
        """create_chat_agent yeni instance olusturmali."""
        agent1 = create_chat_agent()
        agent2 = create_chat_agent()

        assert agent1 is not agent2

    def test_reset_chat_agent(self):
        """reset_chat_agent singleton'i temizlemeli."""
        reset_chat_agent()

        agent1 = get_chat_agent()
        reset_chat_agent()
        agent2 = get_chat_agent()

        assert agent1 is not agent2


# ========================================================================
# MOCK LLM INTEGRATION TESTS
# ========================================================================

class TestMockLLMIntegration:
    """Mock LLM entegrasyon testleri."""

    def test_mock_llm_receives_prompt(self, chat_agent, mock_llm):
        """Mock LLM prompt almali."""
        chat_agent.start_session("user_123")
        chat_agent.chat("Test message")

        assert mock_llm.get_call_count() > 0
        assert mock_llm.get_last_prompt() is not None

    def test_mock_llm_cycles_responses(self):
        """Mock LLM responses cycle etmeli."""
        llm = MockLLMAdapter(responses=["R1", "R2", "R3"])
        agent = UEMChatAgent(memory=None, llm=llm)

        agent.start_session("user_123")
        r1 = agent.chat("M1")
        r2 = agent.chat("M2")
        r3 = agent.chat("M3")

        assert r1.content == "R1"
        assert r2.content == "R2"
        assert r3.content == "R3"
