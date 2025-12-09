"""
tests/unit/test_situation_builder.py

SituationBuilder test suite.
Faz 4 Aşama 2 - Context Understanding testleri.

Test count: 40+
"""

import pytest
from core.language.dialogue import (
    SituationBuilder,
    SituationBuilderConfig,
    SituationModel,
    Actor,
    Intention,
    Risk,
    EmotionalState,
)


# ============================================================================
# Builder Creation Tests
# ============================================================================

class TestBuilderCreation:
    """SituationBuilder creation tests."""

    def test_builder_creation_default_config(self):
        """Test builder creation with default config."""
        builder = SituationBuilder()
        assert builder.config is not None
        assert builder.config.max_actors == 10
        assert builder.config.max_intentions == 20
        assert builder.config.enable_emotion_detection is True

    def test_builder_creation_custom_config(self):
        """Test builder creation with custom config."""
        config = SituationBuilderConfig(
            max_actors=5,
            max_intentions=10,
            max_risks=3,
            enable_emotion_detection=False,
            enable_risk_detection=False
        )
        builder = SituationBuilder(config=config)
        assert builder.config.max_actors == 5
        assert builder.config.max_intentions == 10
        assert builder.config.enable_emotion_detection is False

    def test_builder_with_optional_processors(self):
        """Test builder with optional processors."""
        mock_perception = object()
        mock_memory = object()
        mock_cognition = object()

        builder = SituationBuilder(
            perception_processor=mock_perception,
            memory_search=mock_memory,
            cognition_processor=mock_cognition
        )
        assert builder.perception is mock_perception
        assert builder.memory is mock_memory
        assert builder.cognition is mock_cognition


# ============================================================================
# Build Method Tests
# ============================================================================

class TestBuildMethod:
    """SituationBuilder.build() tests."""

    def test_build_simple_message(self):
        """Test build with simple message."""
        builder = SituationBuilder()
        situation = builder.build("Merhaba")
        assert situation is not None
        assert isinstance(situation, SituationModel)

    def test_build_returns_situation_model(self):
        """Test build returns SituationModel."""
        builder = SituationBuilder()
        situation = builder.build("Nasılsın?")
        assert isinstance(situation, SituationModel)
        assert situation.id.startswith("sit_")

    def test_build_generates_unique_id(self):
        """Test build generates unique IDs."""
        builder = SituationBuilder()
        situation1 = builder.build("Test 1")
        situation2 = builder.build("Test 2")
        assert situation1.id != situation2.id

    def test_build_with_conversation_context(self):
        """Test build with conversation context."""
        builder = SituationBuilder()
        context = [
            {"role": "user", "content": "Merhaba"},
            {"role": "assistant", "content": "Merhaba! Nasıl yardımcı olabilirim?"}
        ]
        situation = builder.build("Bir sorum var", context)
        assert "summary" in situation.context

    def test_build_with_metadata(self):
        """Test build with metadata."""
        builder = SituationBuilder()
        metadata = {"session_id": "sess_123", "user_id": "user_456"}
        situation = builder.build("Test", metadata=metadata)
        assert situation.context.get("session_id") == "sess_123"
        assert situation.context.get("user_id") == "user_456"


# ============================================================================
# Actor Extraction Tests
# ============================================================================

class TestExtractActors:
    """SituationBuilder._extract_actors() tests."""

    def test_extract_actors_always_includes_user_and_assistant(self):
        """Test that user and assistant are always included."""
        builder = SituationBuilder()
        situation = builder.build("Herhangi bir mesaj")

        roles = [a.role for a in situation.actors]
        assert "user" in roles
        assert "assistant" in roles

    def test_extract_actors_detects_third_party_arkadasim(self):
        """Test third party detection - arkadaşım."""
        builder = SituationBuilder()
        situation = builder.build("Arkadaşım bana yardım etti")

        third_parties = [a for a in situation.actors if a.role == "third_party"]
        assert len(third_parties) >= 1

    def test_extract_actors_detects_third_party_annem(self):
        """Test third party detection - annem."""
        builder = SituationBuilder()
        situation = builder.build("Annem bugün hastalandı")

        third_parties = [a for a in situation.actors if a.role == "third_party"]
        assert len(third_parties) >= 1

    def test_extract_actors_detects_third_party_o(self):
        """Test third party detection - o."""
        builder = SituationBuilder()
        situation = builder.build("O bana söyledi")

        third_parties = [a for a in situation.actors if a.role == "third_party"]
        assert len(third_parties) >= 1

    def test_extract_actors_max_limit(self):
        """Test max actors limit."""
        config = SituationBuilderConfig(max_actors=3)
        builder = SituationBuilder(config=config)
        situation = builder.build("Annem, babam, kardeşim, eşim ve arkadaşım geldi")

        assert len(situation.actors) <= 3


# ============================================================================
# Intention Extraction Tests
# ============================================================================

class TestExtractIntentions:
    """SituationBuilder._extract_intentions() tests."""

    def test_extract_intentions_question(self):
        """Test question intent detection."""
        builder = SituationBuilder()
        situation = builder.build("Bu nasıl çalışıyor?")

        goals = [i.goal for i in situation.intentions]
        assert "ask" in goals

    def test_extract_intentions_greeting(self):
        """Test greeting intent detection."""
        builder = SituationBuilder()
        situation = builder.build("Merhaba, nasılsın?")

        goals = [i.goal for i in situation.intentions]
        assert "greet" in goals

    def test_extract_intentions_help_request(self):
        """Test help request intent detection."""
        builder = SituationBuilder()
        situation = builder.build("Yardım eder misin?")

        goals = [i.goal for i in situation.intentions]
        assert "help" in goals

    def test_extract_intentions_thank(self):
        """Test thank intent detection."""
        builder = SituationBuilder()
        situation = builder.build("Teşekkür ederim!")

        goals = [i.goal for i in situation.intentions]
        assert "thank" in goals

    def test_extract_intentions_complain(self):
        """Test complain intent detection."""
        builder = SituationBuilder()
        situation = builder.build("Çok kötü bir durum, problem var")

        goals = [i.goal for i in situation.intentions]
        assert "complain" in goals

    def test_extract_intentions_request(self):
        """Test request intent detection."""
        builder = SituationBuilder()
        situation = builder.build("Lütfen bana yardım et")

        goals = [i.goal for i in situation.intentions]
        assert "request" in goals or "help" in goals

    def test_extract_intentions_default_communicate(self):
        """Test default communicate intent."""
        builder = SituationBuilder()
        situation = builder.build("xyz abc 123")  # No pattern match

        goals = [i.goal for i in situation.intentions]
        assert "communicate" in goals

    def test_extract_intentions_has_evidence(self):
        """Test that intentions have evidence."""
        builder = SituationBuilder()
        situation = builder.build("Merhaba")

        for intention in situation.intentions:
            assert len(intention.evidence) > 0


# ============================================================================
# Risk Detection Tests
# ============================================================================

class TestDetectRisks:
    """SituationBuilder._detect_risks() tests."""

    def test_detect_risks_physical_safety(self):
        """Test physical safety risk detection."""
        builder = SituationBuilder()
        situation = builder.build("intihar etmek istiyorum")

        categories = [r.category for r in situation.risks]
        assert "safety" in categories

    def test_detect_risks_emotional(self):
        """Test emotional risk detection."""
        builder = SituationBuilder()
        situation = builder.build("Depresyon içindeyim, dayanamıyorum")

        categories = [r.category for r in situation.risks]
        assert "emotional" in categories

    def test_detect_risks_ethical(self):
        """Test ethical risk detection."""
        builder = SituationBuilder()
        situation = builder.build("Yasadışı bir şey yapmak istiyorum")

        categories = [r.category for r in situation.risks]
        assert "ethical" in categories

    def test_detect_risks_relational(self):
        """Test relational risk detection."""
        builder = SituationBuilder()
        situation = builder.build("Boşanma sürecindeyim")

        categories = [r.category for r in situation.risks]
        assert "relational" in categories

    def test_detect_risks_none(self):
        """Test no risks detected."""
        builder = SituationBuilder()
        situation = builder.build("Bugün hava çok güzel")

        assert len(situation.risks) == 0

    def test_detect_risks_multiple(self):
        """Test multiple risks detected."""
        builder = SituationBuilder()
        situation = builder.build("Depresyondayım ve yasadışı işler düşünüyorum")

        assert len(situation.risks) >= 2

    def test_detect_risks_has_mitigation(self):
        """Test risks have mitigation."""
        builder = SituationBuilder()
        situation = builder.build("İntihar düşüncelerim var")

        for risk in situation.risks:
            assert risk.mitigation is not None

    def test_detect_risks_disabled(self):
        """Test risk detection can be disabled."""
        config = SituationBuilderConfig(enable_risk_detection=False)
        builder = SituationBuilder(config=config)
        situation = builder.build("İntihar etmek istiyorum")

        assert len(situation.risks) == 0


# ============================================================================
# Risk Mitigations Tests
# ============================================================================

class TestGetRiskMitigations:
    """SituationBuilder._get_risk_mitigations() tests."""

    def test_get_risk_mitigations_safety(self):
        """Test safety mitigations."""
        builder = SituationBuilder()
        mitigations = builder._get_risk_mitigations("safety")
        assert len(mitigations) > 0
        assert any("Profesyonel" in m for m in mitigations)

    def test_get_risk_mitigations_emotional(self):
        """Test emotional mitigations."""
        builder = SituationBuilder()
        mitigations = builder._get_risk_mitigations("emotional")
        assert len(mitigations) > 0
        assert any("Empati" in m for m in mitigations)

    def test_get_risk_mitigations_ethical(self):
        """Test ethical mitigations."""
        builder = SituationBuilder()
        mitigations = builder._get_risk_mitigations("ethical")
        assert len(mitigations) > 0

    def test_get_risk_mitigations_unknown(self):
        """Test unknown risk type mitigations."""
        builder = SituationBuilder()
        mitigations = builder._get_risk_mitigations("unknown_type")
        assert mitigations == ["Dikkatli ol"]


# ============================================================================
# Emotion Detection Tests
# ============================================================================

class TestDetectEmotion:
    """SituationBuilder._detect_emotion() tests."""

    def test_detect_emotion_positive(self):
        """Test positive emotion detection."""
        builder = SituationBuilder()
        situation = builder.build("Çok mutluyum, harika bir gün!")

        assert situation.emotional_state is not None
        assert situation.emotional_state.valence > 0
        assert situation.emotional_state.primary_emotion == "positive"

    def test_detect_emotion_negative(self):
        """Test negative emotion detection."""
        builder = SituationBuilder()
        situation = builder.build("Çok üzgünüm, berbat hissediyorum")

        assert situation.emotional_state is not None
        assert situation.emotional_state.valence < 0
        assert situation.emotional_state.primary_emotion == "negative"

    def test_detect_emotion_high_arousal(self):
        """Test high arousal detection."""
        builder = SituationBuilder()
        situation = builder.build("Çok heyecanlıyım, acil bir durum!")

        assert situation.emotional_state is not None
        assert situation.emotional_state.arousal > 0

    def test_detect_emotion_low_arousal(self):
        """Test low arousal detection."""
        builder = SituationBuilder()
        situation = builder.build("Sakin ve huzurluyum")

        assert situation.emotional_state is not None
        assert situation.emotional_state.arousal < 0

    def test_detect_emotion_neutral(self):
        """Test neutral emotion detection."""
        builder = SituationBuilder()
        situation = builder.build("Bugün pazartesi")

        assert situation.emotional_state is not None
        assert situation.emotional_state.valence == 0.0
        assert situation.emotional_state.primary_emotion is None

    def test_detect_emotion_disabled(self):
        """Test emotion detection can be disabled."""
        config = SituationBuilderConfig(enable_emotion_detection=False)
        builder = SituationBuilder(config=config)
        situation = builder.build("Çok mutluyum!")

        assert situation.emotional_state is None


# ============================================================================
# Topic Detection Tests
# ============================================================================

class TestDetermineTopic:
    """SituationBuilder._determine_topic() tests."""

    def test_determine_topic_technology(self):
        """Test technology topic detection."""
        builder = SituationBuilder()
        situation = builder.build("Bilgisayarım çalışmıyor, yazılım hatası var")

        assert situation.topic_domain == "technology"

    def test_determine_topic_health(self):
        """Test health topic detection."""
        builder = SituationBuilder()
        situation = builder.build("Doktora gittim, ilaç aldım")

        assert situation.topic_domain == "health"

    def test_determine_topic_relationships(self):
        """Test relationships topic detection."""
        builder = SituationBuilder()
        situation = builder.build("Aile ilişkilerim kötü")

        assert situation.topic_domain == "relationships"

    def test_determine_topic_work(self):
        """Test work topic detection."""
        builder = SituationBuilder()
        situation = builder.build("İş yerinde patron ile sorun yaşıyorum")

        assert situation.topic_domain == "work"

    def test_determine_topic_education(self):
        """Test education topic detection."""
        builder = SituationBuilder()
        situation = builder.build("Okul sınavlarına çalışıyorum")

        assert situation.topic_domain == "education"

    def test_determine_topic_general_fallback(self):
        """Test general fallback topic."""
        builder = SituationBuilder()
        situation = builder.build("xyz abc 123")

        assert situation.topic_domain == "general"


# ============================================================================
# Context Summary Tests
# ============================================================================

class TestSummarizeContext:
    """SituationBuilder._summarize_context() tests."""

    def test_summarize_context_no_context(self):
        """Test summary without context."""
        builder = SituationBuilder()
        situation = builder.build("Kısa mesaj")

        assert "Kullanıcı mesajı:" in situation.context["summary"]

    def test_summarize_context_with_history(self):
        """Test summary with conversation history."""
        builder = SituationBuilder()
        context = [
            {"role": "user", "content": "İlk mesaj"},
            {"role": "assistant", "content": "Yanıt"},
            {"role": "user", "content": "İkinci mesaj"}
        ]
        situation = builder.build("Üçüncü mesaj", context)

        summary = situation.context["summary"]
        assert "user:" in summary or "assistant:" in summary

    def test_summarize_context_truncates_long_messages(self):
        """Test that long messages are truncated in summary."""
        builder = SituationBuilder()
        long_message = "A" * 200
        situation = builder.build(long_message)

        summary = situation.context["summary"]
        assert "..." in summary


# ============================================================================
# Understanding Score Tests
# ============================================================================

class TestCalculateUnderstanding:
    """SituationBuilder._calculate_understanding() tests."""

    def test_calculate_understanding_base(self):
        """Test base understanding score."""
        builder = SituationBuilder()
        situation = builder.build("xyz")  # Minimal context

        assert situation.understanding_score >= 0.3

    def test_calculate_understanding_with_intentions(self):
        """Test understanding increases with intentions."""
        builder = SituationBuilder()
        situation = builder.build("Merhaba, yardım eder misin?")  # Multiple intents

        assert situation.understanding_score > 0.3

    def test_calculate_understanding_with_risks(self):
        """Test understanding increases with risk detection."""
        builder = SituationBuilder()
        situation = builder.build("Depresyondayım")  # Risk detected

        assert situation.understanding_score > 0.3

    def test_calculate_understanding_with_third_party(self):
        """Test understanding increases with third party actors."""
        builder = SituationBuilder()
        situation = builder.build("Arkadaşım bana söyledi")  # Third party

        assert situation.understanding_score > 0.3

    def test_calculate_understanding_max_cap(self):
        """Test understanding score is capped at 1.0."""
        builder = SituationBuilder()
        # Message with many signals
        situation = builder.build(
            "Merhaba, arkadaşım depresyonda, yardım eder misin? Çok mutlu olurdum."
        )

        assert situation.understanding_score <= 1.0


# ============================================================================
# Config Tests
# ============================================================================

class TestConfig:
    """SituationBuilderConfig tests."""

    def test_config_disable_emotion_detection(self):
        """Test emotion detection can be disabled via config."""
        config = SituationBuilderConfig(enable_emotion_detection=False)
        builder = SituationBuilder(config=config)
        situation = builder.build("Çok mutluyum!")

        assert situation.emotional_state is None

    def test_config_disable_risk_detection(self):
        """Test risk detection can be disabled via config."""
        config = SituationBuilderConfig(enable_risk_detection=False)
        builder = SituationBuilder(config=config)
        situation = builder.build("İntihar düşünceleri")

        assert len(situation.risks) == 0

    def test_config_max_actors_limit(self):
        """Test max actors config limit."""
        config = SituationBuilderConfig(max_actors=2)
        builder = SituationBuilder(config=config)
        situation = builder.build("Annem, babam, kardeşim geldi")

        assert len(situation.actors) <= 2

    def test_config_max_intentions_limit(self):
        """Test max intentions config limit."""
        config = SituationBuilderConfig(max_intentions=1)
        builder = SituationBuilder(config=config)
        situation = builder.build("Merhaba, yardım ister misin? Teşekkürler")

        assert len(situation.intentions) <= 1

    def test_config_max_risks_limit(self):
        """Test max risks config limit."""
        config = SituationBuilderConfig(max_risks=1)
        builder = SituationBuilder(config=config)
        situation = builder.build("Depresyon ve yasadışı işler")

        assert len(situation.risks) <= 1
