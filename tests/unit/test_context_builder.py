"""
tests/unit/test_context_builder.py

ContextBuilder unit testleri.
Memory + State -> LLM Context donusumu testleri.
"""

import pytest
from dataclasses import dataclass
from typing import List, Optional

from core.language.context import (
    ContextBuilder,
    ContextConfig,
    ContextSection,
    get_context_builder,
    create_context_builder,
    reset_context_builder,
)


# ========================================================================
# MOCK CLASSES
# ========================================================================

@dataclass
class MockDialogueTurn:
    """Mock DialogueTurn for testing."""
    role: str
    content: str


@dataclass
class MockConversation:
    """Mock Conversation for testing."""
    turns: List[MockDialogueTurn]

    def get_last_n_turns(self, n: int) -> List[MockDialogueTurn]:
        return self.turns[-n:]


@dataclass
class MockEmbeddingResult:
    """Mock EmbeddingResult for testing."""
    content: str
    similarity: float
    source_type: str


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def builder():
    """Default ContextBuilder instance."""
    return ContextBuilder()


@pytest.fixture
def custom_config():
    """Custom ContextConfig."""
    return ContextConfig(
        max_tokens=2000,
        recent_turns_count=5,
        relevant_memories_count=3,
        include_self_state=True,
        include_relationship=True,
        include_system_prompt=True,
    )


@pytest.fixture
def sample_conversation():
    """Sample conversation with turns."""
    return MockConversation(turns=[
        MockDialogueTurn(role="user", content="Merhaba!"),
        MockDialogueTurn(role="agent", content="Merhaba! Size nasil yardimci olabilirim?"),
        MockDialogueTurn(role="user", content="Bugun hava nasil?"),
        MockDialogueTurn(role="agent", content="Bugun gunesli ve sicak bir hava var."),
    ])


@pytest.fixture
def sample_memories():
    """Sample memory results."""
    return [
        MockEmbeddingResult(
            content="Kullanici daha once hava durumunu sormustu",
            similarity=0.85,
            source_type="dialogue",
        ),
        MockEmbeddingResult(
            content="Kullanici sicak havadan hoslanir",
            similarity=0.72,
            source_type="fact",
        ),
    ]


@pytest.fixture
def sample_self_state():
    """Sample self state."""
    return {
        "mood": "happy",
        "energy": "high",
        "arousal": 0.6,
        "goals": ["assist user", "be helpful"],
        "focus": "conversation",
    }


@pytest.fixture
def sample_relationship():
    """Sample relationship info."""
    return {
        "name": "Ali",
        "type": "friend",
        "trust_score": 0.75,
        "total_interactions": 15,
        "sentiment": 0.6,
        "notes": ["Likes technology", "Works in IT"],
    }


# ========================================================================
# CONFIG TESTS
# ========================================================================

class TestContextConfig:
    """ContextConfig testleri."""

    def test_default_config(self):
        """Default config degerleri dogru olmali."""
        config = ContextConfig()
        assert config.max_tokens == 4000
        assert config.recent_turns_count == 10
        assert config.relevant_memories_count == 5
        assert config.include_self_state is True
        assert config.include_relationship is True
        assert config.include_system_prompt is True

    def test_custom_config(self, custom_config):
        """Custom config degerleri set edilebilmeli."""
        assert custom_config.max_tokens == 2000
        assert custom_config.recent_turns_count == 5
        assert custom_config.relevant_memories_count == 3


class TestContextSection:
    """ContextSection testleri."""

    def test_section_creation(self):
        """Section olusturulabilmeli."""
        section = ContextSection(
            name="test",
            content="Test content",
            priority=1,
            token_count=5,
        )
        assert section.name == "test"
        assert section.content == "Test content"
        assert section.priority == 1
        assert section.token_count == 5


# ========================================================================
# BUILDER INIT TESTS
# ========================================================================

class TestContextBuilderInit:
    """ContextBuilder initialization testleri."""

    def test_init_default(self):
        """Default config ile initialize edilebilmeli."""
        builder = ContextBuilder()
        assert builder.config.max_tokens == 4000

    def test_init_custom_config(self, custom_config):
        """Custom config ile initialize edilebilmeli."""
        builder = ContextBuilder(config=custom_config)
        assert builder.config.max_tokens == 2000

    def test_init_stats(self, builder):
        """Stats initialize edilmeli."""
        stats = builder.stats
        assert stats["total_builds"] == 0
        assert stats["total_sections"] == 0


# ========================================================================
# BUILD TESTS
# ========================================================================

class TestContextBuilderBuild:
    """ContextBuilder.build() testleri."""

    def test_build_empty(self, builder):
        """Bos mesaj ile build edilebilmeli."""
        result = builder.build(user_message="")
        assert isinstance(result, str)

    def test_build_with_message_only(self, builder):
        """Sadece mesaj ile build edilebilmeli."""
        result = builder.build(user_message="Merhaba!")
        assert "Merhaba!" in result
        assert "[Current Message]" in result

    def test_build_with_conversation(self, builder, sample_conversation):
        """Conversation ile build edilebilmeli."""
        result = builder.build(
            user_message="Test",
            conversation=sample_conversation,
        )
        assert "[Conversation History]" in result
        assert "Merhaba!" in result

    def test_build_with_memories(self, builder, sample_memories):
        """Memories ile build edilebilmeli."""
        result = builder.build(
            user_message="Test",
            relevant_memories=sample_memories,
        )
        assert "[Relevant Memories]" in result
        assert "hava durumu" in result

    def test_build_with_self_state(self, builder, sample_self_state):
        """Self state ile build edilebilmeli."""
        result = builder.build(
            user_message="Test",
            self_state=sample_self_state,
        )
        assert "[Self State]" in result
        assert "happy" in result
        assert "high" in result

    def test_build_with_relationship(self, builder, sample_relationship):
        """Relationship ile build edilebilmeli."""
        result = builder.build(
            user_message="Test",
            relationship=sample_relationship,
        )
        assert "[Relationship]" in result
        assert "Ali" in result
        assert "friend" in result

    def test_build_with_personality(self, builder):
        """Personality ile build edilebilmeli."""
        result = builder.build(
            user_message="Test",
            personality="Sen yardimci bir asistansin.",
        )
        assert "[System]" in result
        assert "yardimci" in result

    def test_build_full_context(
        self,
        builder,
        sample_conversation,
        sample_memories,
        sample_self_state,
        sample_relationship,
    ):
        """Tum parametrelerle build edilebilmeli."""
        result = builder.build(
            user_message="Nasilsin?",
            conversation=sample_conversation,
            relevant_memories=sample_memories,
            self_state=sample_self_state,
            relationship=sample_relationship,
            personality="Arkadas canli bir asistan",
        )

        assert "[System]" in result
        assert "[Self State]" in result
        assert "[Relationship]" in result
        assert "[Relevant Memories]" in result
        assert "[Conversation History]" in result
        assert "[Current Message]" in result

    def test_build_updates_stats(self, builder):
        """Build stats'i guncellemeli."""
        builder.build(user_message="Test")
        assert builder.stats["total_builds"] == 1

    def test_build_disabled_self_state(self, sample_self_state):
        """include_self_state=False ise self state eklenmemeli."""
        config = ContextConfig(include_self_state=False)
        builder = ContextBuilder(config=config)

        result = builder.build(
            user_message="Test",
            self_state=sample_self_state,
        )
        assert "[Self State]" not in result

    def test_build_disabled_relationship(self, sample_relationship):
        """include_relationship=False ise relationship eklenmemeli."""
        config = ContextConfig(include_relationship=False)
        builder = ContextBuilder(config=config)

        result = builder.build(
            user_message="Test",
            relationship=sample_relationship,
        )
        assert "[Relationship]" not in result

    def test_build_disabled_system_prompt(self):
        """include_system_prompt=False ise system prompt eklenmemeli."""
        config = ContextConfig(include_system_prompt=False)
        builder = ContextBuilder(config=config)

        result = builder.build(
            user_message="Test",
            personality="Test personality",
        )
        assert "[System]" not in result


# ========================================================================
# TOKEN MANAGEMENT TESTS
# ========================================================================

class TestTokenCounting:
    """Token counting testleri."""

    def test_count_empty_text(self, builder):
        """Bos metin 0 donmeli."""
        assert builder.count_tokens("") == 0

    def test_count_simple_text(self, builder):
        """Basit metin icin token sayisi."""
        count = builder.count_tokens("Hello world")
        assert count > 0
        assert count < 10

    def test_count_turkish_text(self, builder):
        """Turkce metin icin token sayisi."""
        count = builder.count_tokens("Merhaba dunya, nasilsiniz?")
        assert count > 0

    def test_count_long_text(self, builder):
        """Uzun metin icin token sayisi."""
        text = "Bu bir test metnidir. " * 100
        count = builder.count_tokens(text)
        assert count > 100


class TestTruncation:
    """Truncation testleri."""

    def test_truncate_empty_sections(self, builder):
        """Bos section listesi bos string donmeli."""
        result = builder.truncate_to_fit([], 100)
        assert result == ""

    def test_truncate_single_section(self, builder):
        """Tek section truncate edilmeli."""
        sections = [
            ContextSection(
                name="test",
                content="Short content",
                priority=1,
                token_count=5,
            )
        ]
        result = builder.truncate_to_fit(sections, 100)
        assert "Short content" in result

    def test_max_tokens_respected(self):
        """Max tokens limiti asılmamalı."""
        config = ContextConfig(max_tokens=50)
        builder = ContextBuilder(config=config)

        # Create long content
        long_text = "Bu cok uzun bir metin. " * 50

        result = builder.build(
            user_message=long_text,
            personality="System prompt burada",
        )

        # Result should be truncated
        token_count = builder.count_tokens(result)
        # Allow some tolerance due to estimation
        assert token_count < 100  # Should be much smaller than full content


class TestPriorityOrdering:
    """Priority siralama testleri."""

    def test_priority_ordering(self, builder):
        """Dusuk priority once gelmeli."""
        sections = [
            ContextSection(name="low", content="Low priority", priority=10, token_count=5),
            ContextSection(name="high", content="High priority", priority=1, token_count=5),
            ContextSection(name="medium", content="Medium priority", priority=5, token_count=5),
        ]

        result = builder.format_for_llm(sections)

        # High priority should come first
        high_idx = result.find("High priority")
        medium_idx = result.find("Medium priority")
        low_idx = result.find("Low priority")

        assert high_idx < medium_idx < low_idx


# ========================================================================
# FORMATTING TESTS
# ========================================================================

class TestFormatForLLM:
    """format_for_llm() testleri."""

    def test_format_empty(self, builder):
        """Bos liste bos string donmeli."""
        result = builder.format_for_llm([])
        assert result == ""

    def test_format_single_section(self, builder):
        """Tek section formatlanmali."""
        sections = [
            ContextSection(name="test", content="Content", priority=1, token_count=5)
        ]
        result = builder.format_for_llm(sections)
        assert result == "Content"

    def test_format_multiple_sections(self, builder):
        """Birden fazla section formatlanmali."""
        sections = [
            ContextSection(name="a", content="A content", priority=1, token_count=5),
            ContextSection(name="b", content="B content", priority=2, token_count=5),
        ]
        result = builder.format_for_llm(sections)
        assert "A content" in result
        assert "B content" in result
        assert "\n\n" in result  # Sections separated by double newline


# ========================================================================
# SECTION BUILDER TESTS
# ========================================================================

class TestSectionBuilders:
    """Section builder testleri."""

    def test_build_system_section(self, builder):
        """System section olusturulmali."""
        section = builder._build_system_section("Test personality")
        assert section.name == "system"
        assert section.priority == 1
        assert "[System]" in section.content
        assert "Test personality" in section.content

    def test_build_self_section(self, builder, sample_self_state):
        """Self section olusturulmali."""
        section = builder._build_self_section(sample_self_state)
        assert section.name == "self_state"
        assert "Mood: happy" in section.content
        assert "Energy: high" in section.content

    def test_build_relationship_section(self, builder, sample_relationship):
        """Relationship section olusturulmali."""
        section = builder._build_relationship_section(sample_relationship)
        assert section.name == "relationship"
        assert "Ali" in section.content
        assert "friend" in section.content
        assert "high" in section.content  # Trust level

    def test_build_memory_section(self, builder, sample_memories):
        """Memory section olusturulmali."""
        section = builder._build_memory_section(sample_memories)
        assert section.name == "memories"
        assert "dialogue" in section.content
        assert "0.85" in section.content

    def test_build_conversation_section(self, builder, sample_conversation):
        """Conversation section olusturulmali."""
        section = builder._build_conversation_section(sample_conversation, max_turns=10)
        assert section.name == "conversation"
        assert "User: Merhaba!" in section.content
        assert "Agent:" in section.content

    def test_build_user_message_section(self, builder):
        """User message section olusturulmali."""
        section = builder._build_user_message_section("Test message")
        assert section.name == "user_message"
        assert section.priority == 0  # Highest priority
        assert "Test message" in section.content


# ========================================================================
# TURKISH CONTENT TESTS
# ========================================================================

class TestTurkishContent:
    """Turkce icerik testleri."""

    def test_turkish_message(self, builder):
        """Turkce mesaj islenmeli."""
        result = builder.build(user_message="Merhaba, bugun hava cok guzel!")
        assert "Merhaba" in result
        assert "guzel" in result

    def test_turkish_conversation(self, builder):
        """Turkce konusma islenmeli."""
        conv = MockConversation(turns=[
            MockDialogueTurn(role="user", content="Turkiye'nin baskenti neresi?"),
            MockDialogueTurn(role="agent", content="Turkiye'nin baskenti Ankara'dir."),
        ])
        result = builder.build(
            user_message="Tesekkurler!",
            conversation=conv,
        )
        assert "Ankara" in result
        assert "Tesekkurler" in result

    def test_turkish_special_chars(self, builder):
        """Turkce ozel karakterler islenmeli."""
        result = builder.build(
            user_message="Gunesli ve sicak bir gun.",
            self_state={"mood": "mutlu"},
        )
        assert "mutlu" in result


# ========================================================================
# LONG CONVERSATION TESTS
# ========================================================================

class TestLongConversation:
    """Uzun konusma testleri."""

    def test_long_conversation_truncation(self):
        """Uzun konusma truncate edilmeli."""
        config = ContextConfig(recent_turns_count=3)
        builder = ContextBuilder(config=config)

        # Create long conversation
        turns = [
            MockDialogueTurn(role="user", content=f"Message {i}")
            for i in range(10)
        ]
        conv = MockConversation(turns=turns)

        result = builder.build(
            user_message="Latest message",
            conversation=conv,
        )

        # Should only include last 3 turns
        assert "Message 7" in result
        assert "Message 8" in result
        assert "Message 9" in result
        assert "Message 0" not in result
        assert "Message 5" not in result


# ========================================================================
# FACTORY TESTS
# ========================================================================

class TestContextBuilderFactory:
    """Factory function testleri."""

    def test_get_context_builder_singleton(self):
        """get_context_builder singleton dondurmeli."""
        reset_context_builder()

        builder1 = get_context_builder()
        builder2 = get_context_builder()

        assert builder1 is builder2

    def test_create_context_builder_new_instance(self):
        """create_context_builder yeni instance olusturmali."""
        builder1 = create_context_builder()
        builder2 = create_context_builder()

        assert builder1 is not builder2

    def test_reset_context_builder(self):
        """reset_context_builder singleton'i temizlemeli."""
        reset_context_builder()

        builder1 = get_context_builder()
        reset_context_builder()
        builder2 = get_context_builder()

        assert builder1 is not builder2


# ========================================================================
# EDGE CASE TESTS
# ========================================================================

class TestEdgeCases:
    """Edge case testleri."""

    def test_none_values_handled(self, builder):
        """None degerler handle edilmeli."""
        result = builder.build(
            user_message="Test",
            conversation=None,
            relevant_memories=None,
            self_state=None,
            relationship=None,
            personality=None,
        )
        assert "[Current Message]" in result

    def test_empty_conversation(self, builder):
        """Bos conversation handle edilmeli."""
        conv = MockConversation(turns=[])
        result = builder.build(
            user_message="Test",
            conversation=conv,
        )
        assert isinstance(result, str)

    def test_empty_memories_list(self, builder):
        """Bos memories listesi handle edilmeli."""
        result = builder.build(
            user_message="Test",
            relevant_memories=[],
        )
        # Should not crash
        assert "[Current Message]" in result

    def test_dict_memories(self, builder):
        """Dict formatinda memories handle edilmeli."""
        memories = [
            {"content": "Test memory", "similarity": 0.8, "source_type": "fact"},
        ]
        result = builder.build(
            user_message="Test",
            relevant_memories=memories,
        )
        assert "Test memory" in result

    def test_list_conversation(self, builder):
        """List formatinda conversation handle edilmeli."""
        conv = [
            {"role": "user", "content": "Hello"},
            {"role": "agent", "content": "Hi there"},
        ]
        result = builder.build(
            user_message="Test",
            conversation=conv,
        )
        assert "Hello" in result
