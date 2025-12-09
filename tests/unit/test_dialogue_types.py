"""
tests/unit/test_dialogue_types.py

DialogueAct, MessagePlan, SituationModel test suite.
Faz 4 - Thought-to-Speech Pipeline temel tipleri testleri.

Test count: 30+
"""

import pytest
from datetime import datetime, timedelta
from core.language.dialogue import (
    DialogueAct,
    ToneType,
    Actor,
    Intention,
    Risk,
    Relationship,
    TemporalContext,
    EmotionalState,
    SituationModel,
    MessagePlan,
    generate_situation_id,
    generate_message_plan_id,
)


# ============================================================================
# DialogueAct Enum Tests
# ============================================================================

class TestDialogueAct:
    """DialogueAct enum tests."""

    def test_dialogue_act_values(self):
        """Test DialogueAct has all required values."""
        expected_acts = [
            "inform", "explain", "clarify",
            "ask", "confirm",
            "empathize", "encourage", "comfort",
            "suggest", "warn", "advise",
            "refuse", "limit", "deflect",
            "acknowledge", "apologize", "thank"
        ]
        actual_acts = [act.value for act in DialogueAct]
        for expected in expected_acts:
            assert expected in actual_acts

    def test_dialogue_act_count(self):
        """Test DialogueAct has at least 15 acts."""
        assert len(DialogueAct) >= 15

    def test_dialogue_act_is_string_enum(self):
        """Test DialogueAct values are strings."""
        for act in DialogueAct:
            assert isinstance(act.value, str)

    def test_dialogue_act_inform_category(self):
        """Test informative dialogue acts."""
        informative = {DialogueAct.INFORM, DialogueAct.EXPLAIN, DialogueAct.CLARIFY}
        assert len(informative) == 3

    def test_dialogue_act_emotional_category(self):
        """Test emotional dialogue acts."""
        emotional = {DialogueAct.EMPATHIZE, DialogueAct.ENCOURAGE, DialogueAct.COMFORT}
        assert len(emotional) == 3

    def test_dialogue_act_boundary_category(self):
        """Test boundary dialogue acts."""
        boundary = {DialogueAct.REFUSE, DialogueAct.LIMIT, DialogueAct.DEFLECT}
        assert len(boundary) == 3


# ============================================================================
# ToneType Enum Tests
# ============================================================================

class TestToneType:
    """ToneType enum tests."""

    def test_tone_type_values(self):
        """Test ToneType has all required values."""
        expected_tones = [
            "formal", "casual", "empathic", "supportive",
            "neutral", "cautious", "enthusiastic", "serious"
        ]
        actual_tones = [tone.value for tone in ToneType]
        for expected in expected_tones:
            assert expected in actual_tones

    def test_tone_type_count(self):
        """Test ToneType has 8 tones."""
        assert len(ToneType) == 8


# ============================================================================
# Actor Tests
# ============================================================================

class TestActor:
    """Actor dataclass tests."""

    def test_actor_creation(self):
        """Test Actor creation with basic fields."""
        actor = Actor(id="actor_1", role="user", name="Alice")
        assert actor.id == "actor_1"
        assert actor.role == "user"
        assert actor.name == "Alice"

    def test_actor_default_values(self):
        """Test Actor default values."""
        actor = Actor(id="actor_1", role="assistant")
        assert actor.name is None
        assert actor.traits == {}
        assert actor.context == {}

    def test_actor_invalid_role(self):
        """Test Actor rejects invalid role."""
        with pytest.raises(ValueError) as exc_info:
            Actor(id="actor_1", role="invalid_role")
        assert "Invalid role" in str(exc_info.value)

    def test_actor_valid_roles(self):
        """Test Actor accepts all valid roles."""
        for role in ["user", "assistant", "system", "third_party"]:
            actor = Actor(id=f"actor_{role}", role=role)
            assert actor.role == role

    def test_actor_with_traits(self):
        """Test Actor with traits."""
        traits = {"personality": "friendly", "expertise": "tech"}
        actor = Actor(id="actor_1", role="user", traits=traits)
        assert actor.traits["personality"] == "friendly"


# ============================================================================
# Intention Tests
# ============================================================================

class TestIntention:
    """Intention dataclass tests."""

    def test_intention_creation(self):
        """Test Intention creation."""
        intention = Intention(
            id="int_1",
            actor_id="actor_1",
            goal="get_information"
        )
        assert intention.id == "int_1"
        assert intention.goal == "get_information"
        assert intention.confidence == 0.5

    def test_intention_confidence_validation(self):
        """Test Intention confidence validation."""
        with pytest.raises(ValueError):
            Intention(id="int_1", actor_id="actor_1", goal="test", confidence=1.5)

        with pytest.raises(ValueError):
            Intention(id="int_1", actor_id="actor_1", goal="test", confidence=-0.1)

    def test_intention_with_evidence(self):
        """Test Intention with evidence."""
        intention = Intention(
            id="int_1",
            actor_id="actor_1",
            goal="learn",
            evidence=["asked question", "showed curiosity"]
        )
        assert len(intention.evidence) == 2


# ============================================================================
# Risk Tests
# ============================================================================

class TestRisk:
    """Risk dataclass tests (dialogue module)."""

    def test_risk_creation(self):
        """Test Risk creation."""
        risk = Risk(
            category="ethical",
            level=0.5,
            description="Potential ethical concern"
        )
        assert risk.category == "ethical"
        assert risk.level == 0.5

    def test_risk_level_validation(self):
        """Test Risk level validation."""
        with pytest.raises(ValueError):
            Risk(category="ethical", level=1.5, description="test")

        with pytest.raises(ValueError):
            Risk(category="ethical", level=-0.1, description="test")

    def test_risk_with_mitigation(self):
        """Test Risk with mitigation."""
        risk = Risk(
            category="emotional",
            level=0.7,
            description="High emotional risk",
            mitigation="Use empathic tone"
        )
        assert risk.mitigation == "Use empathic tone"


# ============================================================================
# Relationship Tests
# ============================================================================

class TestRelationship:
    """Relationship dataclass tests."""

    def test_relationship_creation(self):
        """Test Relationship creation."""
        rel = Relationship(
            actor1_id="user_1",
            actor2_id="assistant",
            relationship_type="trust",
            strength=0.8
        )
        assert rel.strength == 0.8

    def test_relationship_strength_validation(self):
        """Test Relationship strength validation."""
        with pytest.raises(ValueError):
            Relationship(
                actor1_id="a", actor2_id="b",
                relationship_type="trust", strength=1.5
            )

        with pytest.raises(ValueError):
            Relationship(
                actor1_id="a", actor2_id="b",
                relationship_type="trust", strength=-1.5
            )


# ============================================================================
# TemporalContext Tests
# ============================================================================

class TestTemporalContext:
    """TemporalContext dataclass tests."""

    def test_temporal_context_creation(self):
        """Test TemporalContext creation."""
        start = datetime.now() - timedelta(minutes=5)
        ctx = TemporalContext(conversation_start=start, turn_count=10)
        assert ctx.turn_count == 10

    def test_temporal_context_duration(self):
        """Test conversation_duration property."""
        start = datetime.now() - timedelta(minutes=5)
        ctx = TemporalContext(conversation_start=start)
        # Allow 1 second tolerance
        assert 299 <= ctx.conversation_duration <= 301


# ============================================================================
# EmotionalState Tests
# ============================================================================

class TestEmotionalState:
    """EmotionalState dataclass tests."""

    def test_emotional_state_creation(self):
        """Test EmotionalState creation."""
        state = EmotionalState(
            valence=0.5,
            arousal=0.3,
            dominance=-0.2,
            primary_emotion="happy"
        )
        assert state.valence == 0.5
        assert state.primary_emotion == "happy"

    def test_emotional_state_validation(self):
        """Test EmotionalState PAD validation."""
        with pytest.raises(ValueError):
            EmotionalState(valence=1.5)

        with pytest.raises(ValueError):
            EmotionalState(arousal=-1.5)

        with pytest.raises(ValueError):
            EmotionalState(dominance=2.0)

    def test_emotional_state_confidence_validation(self):
        """Test EmotionalState confidence validation."""
        with pytest.raises(ValueError):
            EmotionalState(confidence=1.5)

    def test_emotional_state_defaults(self):
        """Test EmotionalState defaults."""
        state = EmotionalState()
        assert state.valence == 0.0
        assert state.arousal == 0.0
        assert state.dominance == 0.0
        assert state.confidence == 0.5


# ============================================================================
# SituationModel Tests
# ============================================================================

class TestSituationModel:
    """SituationModel dataclass tests."""

    def test_situation_model_creation(self):
        """Test SituationModel creation."""
        model = SituationModel(
            id="sit_123",
            topic_domain="technology",
            understanding_score=0.8
        )
        assert model.id == "sit_123"
        assert model.topic_domain == "technology"
        assert model.understanding_score == 0.8

    def test_situation_model_validation(self):
        """Test SituationModel understanding_score validation."""
        with pytest.raises(ValueError):
            SituationModel(id="sit_1", understanding_score=1.5)

    def test_situation_model_get_primary_actor(self):
        """Test get_primary_actor method."""
        user = Actor(id="user_1", role="user", name="Alice")
        assistant = Actor(id="assistant_1", role="assistant")
        model = SituationModel(id="sit_1", actors=[user, assistant])

        found_user = model.get_primary_actor("user")
        assert found_user is not None
        assert found_user.name == "Alice"

        found_assistant = model.get_primary_actor("assistant")
        assert found_assistant is not None

        found_none = model.get_primary_actor("system")
        assert found_none is None

    def test_situation_model_get_highest_risk(self):
        """Test get_highest_risk method."""
        risks = [
            Risk(category="ethical", level=0.3, description="Low risk"),
            Risk(category="emotional", level=0.8, description="High risk"),
            Risk(category="safety", level=0.5, description="Medium risk"),
        ]
        model = SituationModel(id="sit_1", risks=risks)

        highest = model.get_highest_risk()
        assert highest is not None
        assert highest.level == 0.8
        assert highest.category == "emotional"

    def test_situation_model_has_high_risk(self):
        """Test has_high_risk method."""
        low_risks = [Risk(category="ethical", level=0.3, description="Low")]
        model_low = SituationModel(id="sit_1", risks=low_risks)
        assert not model_low.has_high_risk()

        high_risks = [Risk(category="ethical", level=0.9, description="High")]
        model_high = SituationModel(id="sit_2", risks=high_risks)
        assert model_high.has_high_risk()

    def test_situation_model_no_risks(self):
        """Test SituationModel with no risks."""
        model = SituationModel(id="sit_1")
        assert model.get_highest_risk() is None
        assert not model.has_high_risk()


# ============================================================================
# MessagePlan Tests
# ============================================================================

class TestMessagePlan:
    """MessagePlan dataclass tests."""

    def test_message_plan_creation(self):
        """Test MessagePlan creation."""
        plan = MessagePlan(
            id="plan_123",
            dialogue_acts=[DialogueAct.INFORM, DialogueAct.SUGGEST],
            primary_intent="Provide information and suggestions",
            tone=ToneType.CASUAL
        )
        assert plan.id == "plan_123"
        assert len(plan.dialogue_acts) == 2
        assert plan.tone == ToneType.CASUAL

    def test_message_plan_validation_risk_level(self):
        """Test MessagePlan risk_level validation."""
        with pytest.raises(ValueError):
            MessagePlan(
                id="plan_1",
                dialogue_acts=[DialogueAct.INFORM],
                primary_intent="test",
                risk_level=1.5
            )

    def test_message_plan_validation_confidence(self):
        """Test MessagePlan confidence validation."""
        with pytest.raises(ValueError):
            MessagePlan(
                id="plan_1",
                dialogue_acts=[DialogueAct.INFORM],
                primary_intent="test",
                confidence=-0.1
            )

    def test_message_plan_empty_dialogue_acts(self):
        """Test MessagePlan rejects empty dialogue_acts."""
        with pytest.raises(ValueError):
            MessagePlan(
                id="plan_1",
                dialogue_acts=[],
                primary_intent="test"
            )

    def test_message_plan_primary_act(self):
        """Test primary_act property."""
        plan = MessagePlan(
            id="plan_1",
            dialogue_acts=[DialogueAct.WARN, DialogueAct.ADVISE],
            primary_intent="Warning"
        )
        assert plan.primary_act == DialogueAct.WARN

    def test_message_plan_has_emotional_act(self):
        """Test has_emotional_act method."""
        plan_emotional = MessagePlan(
            id="plan_1",
            dialogue_acts=[DialogueAct.EMPATHIZE, DialogueAct.COMFORT],
            primary_intent="Emotional support"
        )
        assert plan_emotional.has_emotional_act()

        plan_informative = MessagePlan(
            id="plan_2",
            dialogue_acts=[DialogueAct.INFORM, DialogueAct.EXPLAIN],
            primary_intent="Information"
        )
        assert not plan_informative.has_emotional_act()

    def test_message_plan_has_boundary_act(self):
        """Test has_boundary_act method."""
        plan_boundary = MessagePlan(
            id="plan_1",
            dialogue_acts=[DialogueAct.REFUSE],
            primary_intent="Refuse request"
        )
        assert plan_boundary.has_boundary_act()

        plan_normal = MessagePlan(
            id="plan_2",
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="Normal response"
        )
        assert not plan_normal.has_boundary_act()

    def test_message_plan_has_warning_act(self):
        """Test has_warning_act method."""
        plan_warn = MessagePlan(
            id="plan_1",
            dialogue_acts=[DialogueAct.WARN, DialogueAct.ADVISE],
            primary_intent="Warning"
        )
        assert plan_warn.has_warning_act()

    def test_message_plan_default_values(self):
        """Test MessagePlan default values."""
        plan = MessagePlan(
            id="plan_1",
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="test"
        )
        assert plan.tone == ToneType.NEUTRAL
        assert plan.risk_level == 0.0
        assert plan.confidence == 0.5
        assert plan.content_points == []
        assert plan.constraints == []


# ============================================================================
# ID Generation Tests
# ============================================================================

class TestIDGeneration:
    """ID generation function tests."""

    def test_situation_id_format(self):
        """Test situation ID format."""
        sid = generate_situation_id()
        assert sid.startswith("sit_")
        assert len(sid) == 16  # "sit_" + 12 hex chars

    def test_situation_id_uniqueness(self):
        """Test situation ID uniqueness."""
        ids = [generate_situation_id() for _ in range(100)]
        assert len(ids) == len(set(ids))

    def test_message_plan_id_format(self):
        """Test message plan ID format."""
        pid = generate_message_plan_id()
        assert pid.startswith("plan_")
        assert len(pid) == 17  # "plan_" + 12 hex chars

    def test_message_plan_id_uniqueness(self):
        """Test message plan ID uniqueness."""
        ids = [generate_message_plan_id() for _ in range(100)]
        assert len(ids) == len(set(ids))
