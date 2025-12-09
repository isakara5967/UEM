"""
tests/unit/test_act_selector.py

DialogueActSelector test suite.
Faz 4 Aşama 3 - Act Selection testleri.

Test count: 45+
"""

import pytest
from core.language.dialogue import (
    DialogueActSelector,
    ActSelectorConfig,
    ActSelectionResult,
    ActScore,
    SelectionStrategy,
    DialogueAct,
    SituationModel,
    SituationBuilder,
    Intention,
    Risk,
    EmotionalState,
    Actor,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def selector():
    """Default selector."""
    return DialogueActSelector()


@pytest.fixture
def situation_builder():
    """SituationBuilder for creating test situations."""
    return SituationBuilder()


@pytest.fixture
def greeting_situation(situation_builder):
    """Greeting situation."""
    return situation_builder.build("Merhaba, nasılsın?")


@pytest.fixture
def help_situation(situation_builder):
    """Help request situation."""
    return situation_builder.build("Yardım eder misin? Nasıl yapacağımı bilmiyorum.")


@pytest.fixture
def complaint_situation(situation_builder):
    """Complaint situation."""
    return situation_builder.build("Çok kötü bir durum, sorun var, şikayet etmek istiyorum.")


@pytest.fixture
def emotional_distress_situation(situation_builder):
    """Emotional distress situation."""
    return situation_builder.build("Çok üzgünüm, depresyondayım, dayanamıyorum.")


@pytest.fixture
def high_risk_situation(situation_builder):
    """High physical risk situation."""
    return situation_builder.build("intihar düşüncelerim var, kendime zarar vermek istiyorum.")


@pytest.fixture
def positive_situation(situation_builder):
    """Positive emotion situation."""
    return situation_builder.build("Çok mutluyum, harika bir gün geçirdim!")


# ============================================================================
# Selector Creation Tests
# ============================================================================

class TestSelectorCreation:
    """DialogueActSelector creation tests."""

    def test_selector_creation_default_config(self):
        """Test selector creation with default config."""
        selector = DialogueActSelector()
        assert selector.config is not None
        assert selector.config.max_primary_acts == 3
        assert selector.config.strategy == SelectionStrategy.BALANCED

    def test_selector_creation_custom_config(self):
        """Test selector creation with custom config."""
        config = ActSelectorConfig(
            max_primary_acts=5,
            max_secondary_acts=3,
            min_score_threshold=0.4,
            strategy=SelectionStrategy.EXPRESSIVE
        )
        selector = DialogueActSelector(config=config)
        assert selector.config.max_primary_acts == 5
        assert selector.config.strategy == SelectionStrategy.EXPRESSIVE

    def test_selector_with_optional_processors(self):
        """Test selector with optional processors."""
        mock_affect = object()
        mock_self = object()
        mock_ethics = object()

        selector = DialogueActSelector(
            affect_processor=mock_affect,
            self_processor=mock_self,
            ethics_checker=mock_ethics
        )
        assert selector.affect is mock_affect
        assert selector.self_proc is mock_self
        assert selector.ethics is mock_ethics


# ============================================================================
# Select Method Tests
# ============================================================================

class TestSelectMethod:
    """DialogueActSelector.select() tests."""

    def test_select_returns_result(self, selector, greeting_situation):
        """Test select returns ActSelectionResult."""
        result = selector.select(greeting_situation)
        assert isinstance(result, ActSelectionResult)

    def test_select_result_has_primary_acts(self, selector, greeting_situation):
        """Test result has primary acts."""
        result = selector.select(greeting_situation)
        assert len(result.primary_acts) > 0
        assert all(isinstance(act, DialogueAct) for act in result.primary_acts)

    def test_select_result_has_confidence(self, selector, greeting_situation):
        """Test result has confidence score."""
        result = selector.select(greeting_situation)
        assert 0.0 <= result.confidence <= 1.0

    def test_select_result_has_strategy(self, selector, greeting_situation):
        """Test result has strategy used."""
        result = selector.select(greeting_situation)
        assert result.strategy_used == SelectionStrategy.BALANCED

    def test_select_result_has_all_scores(self, selector, greeting_situation):
        """Test result has all act scores."""
        result = selector.select(greeting_situation)
        assert len(result.all_scores) == len(DialogueAct)


# ============================================================================
# Situation-Based Selection Tests
# ============================================================================

class TestSituationBasedSelection:
    """Tests for different situation types."""

    def test_select_greeting_situation(self, selector, greeting_situation):
        """Test greeting situation selects appropriate acts."""
        result = selector.select(greeting_situation)
        # Greeting with "?" also triggers ask intent, so INFORM/EXPLAIN may score higher
        expected_acts = {DialogueAct.ACKNOWLEDGE, DialogueAct.INFORM, DialogueAct.EXPLAIN}
        assert any(act in expected_acts for act in result.primary_acts)

    def test_select_help_request_situation(self, selector, help_situation):
        """Test help request selects ADVISE or SUGGEST."""
        result = selector.select(help_situation)
        help_acts = {DialogueAct.ADVISE, DialogueAct.SUGGEST, DialogueAct.EXPLAIN}
        assert any(act in help_acts for act in result.primary_acts)

    def test_select_complaint_situation(self, selector, complaint_situation):
        """Test complaint selects EMPATHIZE or ACKNOWLEDGE."""
        result = selector.select(complaint_situation)
        complaint_acts = {DialogueAct.EMPATHIZE, DialogueAct.ACKNOWLEDGE, DialogueAct.APOLOGIZE}
        assert any(act in complaint_acts for act in result.primary_acts)

    def test_select_emotional_distress(self, selector, emotional_distress_situation):
        """Test emotional distress selects empathetic acts."""
        result = selector.select(emotional_distress_situation)
        empathy_acts = {DialogueAct.EMPATHIZE, DialogueAct.COMFORT, DialogueAct.ENCOURAGE}
        assert any(act in empathy_acts for act in result.primary_acts)

    def test_select_high_risk_physical(self, selector, high_risk_situation):
        """Test high risk situation scores WARN and EMPATHIZE high."""
        result = selector.select(high_risk_situation)
        # Check that risk-related acts have higher scores
        risk_acts = {DialogueAct.WARN, DialogueAct.EMPATHIZE, DialogueAct.COMFORT}
        risk_scores = [s for s in result.all_scores if s.act in risk_acts]
        # At least one risk act should have a notable score
        assert any(s.score > 0.2 for s in risk_scores)

    def test_select_high_risk_ethical(self, selector, situation_builder):
        """Test ethical risk situation scores ethical acts high."""
        situation = situation_builder.build("yasadışı bir şey yapmak istiyorum")
        result = selector.select(situation)
        # Check that ethical risk acts have higher scores
        ethical_acts = {DialogueAct.WARN, DialogueAct.REFUSE, DialogueAct.DEFLECT}
        ethical_scores = [s for s in result.all_scores if s.act in ethical_acts]
        # At least one ethical act should have a notable score
        assert any(s.score > 0.1 for s in ethical_scores)

    def test_select_positive_emotion(self, selector, positive_situation):
        """Test positive emotion selects ACKNOWLEDGE or ENCOURAGE."""
        result = selector.select(positive_situation)
        positive_acts = {DialogueAct.ACKNOWLEDGE, DialogueAct.ENCOURAGE}
        assert any(act in positive_acts for act in result.primary_acts)

    def test_select_negative_emotion(self, selector, emotional_distress_situation):
        """Test negative emotion boosts empathy acts."""
        result = selector.select(emotional_distress_situation)
        # Check that empathy acts have high scores
        empathy_acts = {DialogueAct.EMPATHIZE, DialogueAct.COMFORT}
        empathy_scores = [s for s in result.all_scores if s.act in empathy_acts]
        assert any(s.score > 0.3 for s in empathy_scores)

    def test_select_high_arousal(self, selector, situation_builder):
        """Test high arousal situation."""
        situation = situation_builder.build("Çok heyecanlıyım, acil bir durum!")
        result = selector.select(situation)
        # High arousal should boost COMFORT or CLARIFY
        calming_acts = {DialogueAct.COMFORT, DialogueAct.CLARIFY}
        calming_scores = [s for s in result.all_scores if s.act in calming_acts]
        assert any(s.score > 0 for s in calming_scores)


# ============================================================================
# Score Calculation Tests
# ============================================================================

class TestScoreCalculation:
    """Score calculation tests."""

    def test_score_all_acts_returns_all(self, selector, greeting_situation):
        """Test _score_all_acts returns scores for all acts."""
        scores = selector._score_all_acts(greeting_situation)
        assert len(scores) == len(DialogueAct)

    def test_calculate_act_score(self, selector, greeting_situation):
        """Test _calculate_act_score returns valid score."""
        score, reasons = selector._calculate_act_score(
            DialogueAct.ACKNOWLEDGE,
            greeting_situation
        )
        assert 0.0 <= score <= 1.0
        assert isinstance(reasons, list)

    def test_score_by_intentions_match(self, selector):
        """Test _score_by_intentions with matching intent."""
        intentions = [
            Intention(id="int_1", actor_id="user", goal="greet", confidence=0.8)
        ]
        score, reasons = selector._score_by_intentions(
            DialogueAct.ACKNOWLEDGE,
            intentions
        )
        assert score > 0
        assert len(reasons) > 0

    def test_score_by_intentions_no_match(self, selector):
        """Test _score_by_intentions with no matching intent."""
        intentions = [
            Intention(id="int_1", actor_id="user", goal="greet", confidence=0.8)
        ]
        score, reasons = selector._score_by_intentions(
            DialogueAct.REFUSE,  # Not in greet map
            intentions
        )
        assert score == 0.0

    def test_score_by_intentions_empty(self, selector):
        """Test _score_by_intentions with empty intentions."""
        score, reasons = selector._score_by_intentions(
            DialogueAct.ACKNOWLEDGE,
            []
        )
        assert score == 0.0
        assert reasons == []

    def test_score_by_risks_match(self, selector):
        """Test _score_by_risks with matching risk."""
        risks = [
            Risk(category="safety", level=0.8, description="Safety risk")
        ]
        score, reasons = selector._score_by_risks(DialogueAct.WARN, risks)
        assert score > 0
        assert len(reasons) > 0

    def test_score_by_risks_no_risks(self, selector):
        """Test _score_by_risks with no risks."""
        score, reasons = selector._score_by_risks(DialogueAct.WARN, [])
        assert score == 0.0
        assert reasons == []

    def test_score_by_emotion_negative(self, selector):
        """Test _score_by_emotion with negative emotion."""
        emotion = EmotionalState(valence=-0.5, arousal=0.3, dominance=0.0)
        score, reasons = selector._score_by_emotion(
            DialogueAct.EMPATHIZE,
            emotion
        )
        assert score > 0
        assert "Negative emotion" in reasons[0]

    def test_score_by_emotion_positive(self, selector):
        """Test _score_by_emotion with positive emotion."""
        emotion = EmotionalState(valence=0.5, arousal=0.3, dominance=0.0)
        score, reasons = selector._score_by_emotion(
            DialogueAct.ACKNOWLEDGE,
            emotion
        )
        assert score > 0
        assert "Positive emotion" in reasons[0]

    def test_score_by_emotion_none(self, selector):
        """Test _score_by_emotion with no emotion."""
        score, reasons = selector._score_by_emotion(DialogueAct.EMPATHIZE, None)
        assert score == 0.0
        assert reasons == []


# ============================================================================
# Filter and Influence Tests
# ============================================================================

class TestFiltersAndInfluence:
    """Filter and influence application tests."""

    def test_apply_ethics_filter_high_risk(self, selector, high_risk_situation):
        """Test ethics filter with high risk."""
        scores = selector._score_all_acts(high_risk_situation)
        filtered = selector._apply_ethics_filter(scores, high_risk_situation)

        # WARN should be boosted
        warn_score = next(s for s in filtered if s.act == DialogueAct.WARN)
        assert "Ethics: boosted" in " ".join(warn_score.reasons)

    def test_apply_ethics_filter_no_risk(self, selector, greeting_situation):
        """Test ethics filter with no risk."""
        scores = selector._score_all_acts(greeting_situation)
        initial_scores = {s.act: s.score for s in scores}

        filtered = selector._apply_ethics_filter(scores, greeting_situation)
        final_scores = {s.act: s.score for s in filtered}

        # No high risk, scores should be unchanged
        for act in DialogueAct:
            assert initial_scores[act] == final_scores[act]

    def test_apply_affect_influence(self, selector):
        """Test affect influence with strong negative emotion."""
        # Create a situation with very negative valence (< -0.5)
        situation = SituationModel(
            id="sit_test",
            emotional_state=EmotionalState(valence=-0.7, arousal=0.3, dominance=0.0),
            understanding_score=0.5
        )
        scores = selector._score_all_acts(situation)
        influenced = selector._apply_affect_influence(scores, situation)

        # EMPATHIZE should be boosted
        empathize_score = next(s for s in influenced if s.act == DialogueAct.EMPATHIZE)
        assert "Affect: strong negative" in " ".join(empathize_score.reasons)


# ============================================================================
# Strategy Tests
# ============================================================================

class TestStrategies:
    """Strategy application tests."""

    def test_apply_strategy_conservative(self, greeting_situation):
        """Test conservative strategy boosts safe acts."""
        config = ActSelectorConfig(strategy=SelectionStrategy.CONSERVATIVE)
        selector = DialogueActSelector(config=config)

        scores = selector._score_all_acts(greeting_situation)
        strategized = selector._apply_strategy(scores)

        # ACKNOWLEDGE should be boosted
        ack_score = next(s for s in strategized if s.act == DialogueAct.ACKNOWLEDGE)
        assert "conservative boost" in " ".join(ack_score.reasons)

    def test_apply_strategy_balanced(self, selector, greeting_situation):
        """Test balanced strategy makes no changes."""
        scores = selector._score_all_acts(greeting_situation)
        initial_scores = {s.act: s.score for s in scores}

        strategized = selector._apply_strategy(scores)
        final_scores = {s.act: s.score for s in strategized}

        # Balanced strategy should not change scores
        for act in DialogueAct:
            assert initial_scores[act] == final_scores[act]

    def test_apply_strategy_expressive(self, greeting_situation):
        """Test expressive strategy boosts emotional acts."""
        config = ActSelectorConfig(strategy=SelectionStrategy.EXPRESSIVE)
        selector = DialogueActSelector(config=config)

        scores = selector._score_all_acts(greeting_situation)
        strategized = selector._apply_strategy(scores)

        # EMPATHIZE should be boosted
        emp_score = next(s for s in strategized if s.act == DialogueAct.EMPATHIZE)
        assert "expressive boost" in " ".join(emp_score.reasons)


# ============================================================================
# Confidence Tests
# ============================================================================

class TestConfidence:
    """Confidence calculation tests."""

    def test_calculate_confidence(self, selector, greeting_situation):
        """Test confidence calculation."""
        scores = [
            ActScore(act=DialogueAct.ACKNOWLEDGE, score=0.8, reasons=[]),
            ActScore(act=DialogueAct.INFORM, score=0.5, reasons=[]),
        ]
        confidence = selector._calculate_confidence(scores, greeting_situation)
        assert 0.0 <= confidence <= 1.0

    def test_calculate_confidence_low_understanding(self, selector):
        """Test confidence with low understanding."""
        situation = SituationModel(id="sit_test", understanding_score=0.2)
        scores = [
            ActScore(act=DialogueAct.ACKNOWLEDGE, score=0.5, reasons=[]),
        ]
        confidence = selector._calculate_confidence(scores, situation)
        # Low understanding should reduce confidence
        assert confidence < 0.7

    def test_calculate_confidence_empty_scores(self, selector, greeting_situation):
        """Test confidence with empty scores."""
        confidence = selector._calculate_confidence([], greeting_situation)
        assert confidence == 0.0


# ============================================================================
# Mapping Table Tests
# ============================================================================

class TestMappingTables:
    """Mapping table tests."""

    def test_intent_act_map_help(self, selector):
        """Test intent act map for help."""
        intent_map = selector._build_intent_act_map()
        assert "help" in intent_map
        assert DialogueAct.ADVISE in intent_map["help"]

    def test_intent_act_map_greet(self, selector):
        """Test intent act map for greet."""
        intent_map = selector._build_intent_act_map()
        assert "greet" in intent_map
        assert DialogueAct.ACKNOWLEDGE in intent_map["greet"]

    def test_risk_act_map_safety(self, selector):
        """Test risk act map for safety."""
        risk_map = selector._build_risk_act_map()
        assert "safety" in risk_map
        assert DialogueAct.WARN in risk_map["safety"]

    def test_risk_act_map_ethical(self, selector):
        """Test risk act map for ethical."""
        risk_map = selector._build_risk_act_map()
        assert "ethical" in risk_map
        assert DialogueAct.REFUSE in risk_map["ethical"]

    def test_emotion_act_map(self, selector):
        """Test emotion act map."""
        emotion_map = selector._build_emotion_act_map()
        assert "positive" in emotion_map
        assert "negative" in emotion_map
        assert "neutral" in emotion_map


# ============================================================================
# Fallback and Limit Tests
# ============================================================================

class TestFallbackAndLimits:
    """Fallback and limit tests."""

    def test_fallback_to_acknowledge(self):
        """Test fallback to ACKNOWLEDGE when no acts selected."""
        config = ActSelectorConfig(min_score_threshold=0.99)  # Very high threshold
        selector = DialogueActSelector(config=config)
        situation = SituationModel(id="sit_test", understanding_score=0.1)

        result = selector.select(situation)
        assert DialogueAct.ACKNOWLEDGE in result.primary_acts
        assert result.confidence == 0.3

    def test_max_primary_acts_limit(self, selector, help_situation):
        """Test max primary acts limit."""
        result = selector.select(help_situation)
        assert len(result.primary_acts) <= selector.config.max_primary_acts

    def test_max_secondary_acts_limit(self, selector, help_situation):
        """Test max secondary acts limit."""
        result = selector.select(help_situation)
        assert len(result.secondary_acts) <= selector.config.max_secondary_acts

    def test_min_score_threshold(self):
        """Test min score threshold."""
        config = ActSelectorConfig(min_score_threshold=0.5)
        selector = DialogueActSelector(config=config)
        situation = SituationModel(id="sit_test", understanding_score=0.3)

        result = selector.select(situation)
        # All scores should be above threshold (or fallback)
        if result.primary_acts != [DialogueAct.ACKNOWLEDGE]:
            valid_scores = [
                s for s in result.all_scores
                if s.score >= config.min_score_threshold
            ]
            assert all(act in [s.act for s in valid_scores] for act in result.primary_acts)

    def test_select_with_context(self, selector, greeting_situation):
        """Test select with additional context."""
        context = {"user_id": "user_123", "session_id": "sess_456"}
        result = selector.select(greeting_situation, context=context)
        assert isinstance(result, ActSelectionResult)


# ============================================================================
# Config Tests
# ============================================================================

class TestConfigOptions:
    """Config option tests."""

    def test_config_disable_ethics_check(self, high_risk_situation):
        """Test disabling ethics check."""
        config = ActSelectorConfig(enable_ethics_check=False)
        selector = DialogueActSelector(config=config)

        result = selector.select(high_risk_situation)
        # Ethics filter should not be applied
        warn_score = next(s for s in result.all_scores if s.act == DialogueAct.WARN)
        assert "Ethics: boosted" not in " ".join(warn_score.reasons)

    def test_config_disable_affect_influence(self, emotional_distress_situation):
        """Test disabling affect influence."""
        config = ActSelectorConfig(enable_affect_influence=False)
        selector = DialogueActSelector(config=config)

        result = selector.select(emotional_distress_situation)
        # Affect influence should not be applied
        emp_score = next(s for s in result.all_scores if s.act == DialogueAct.EMPATHIZE)
        assert "Affect: strong negative" not in " ".join(emp_score.reasons)
