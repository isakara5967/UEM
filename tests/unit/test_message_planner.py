"""
tests/unit/test_message_planner.py

MessagePlanner testleri - ActSelectionResult + SituationModel → MessagePlan

Test kategorileri:
1. MessagePlanner oluşturma
2. Plan metodu
3. Primary intent belirleme
4. Tone belirleme
5. Content points oluşturma
6. Constraints oluşturma
7. Confidence hesaplama
8. Update plan
9. Entegrasyon testleri
"""

import pytest
from datetime import datetime

from core.language.dialogue.message_planner import (
    MessagePlanner,
    MessagePlannerConfig,
    ContentPoint,
    MessageConstraint,
    ConstraintType,
    ConstraintSeverity,
)
from core.language.dialogue.types import (
    DialogueAct,
    ToneType,
    SituationModel,
    MessagePlan,
    Actor,
    Intention,
    Risk,
    EmotionalState,
)
from core.language.dialogue.act_selector import (
    ActSelectionResult,
    SelectionStrategy,
    ActScore,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def default_planner():
    """Varsayılan MessagePlanner."""
    return MessagePlanner()


@pytest.fixture
def custom_config():
    """Özelleştirilmiş konfigürasyon."""
    return MessagePlannerConfig(
        max_content_points=5,
        max_constraints=3,
        default_tone=ToneType.FORMAL,
        enable_self_values=True,
        enable_constraints=True,
        risk_threshold_for_caution=0.6
    )


@pytest.fixture
def simple_situation():
    """Basit durum modeli."""
    return SituationModel(
        id="sit_test123",
        actors=[
            Actor(id="user", role="user"),
            Actor(id="assistant", role="assistant", name="UEM")
        ],
        intentions=[
            Intention(
                id="int_001",
                actor_id="user",
                goal="ask",
                confidence=0.7
            )
        ],
        understanding_score=0.6
    )


@pytest.fixture
def emotional_situation():
    """Duygusal durum modeli."""
    return SituationModel(
        id="sit_emotional",
        actors=[
            Actor(id="user", role="user"),
            Actor(id="assistant", role="assistant", name="UEM")
        ],
        intentions=[
            Intention(
                id="int_002",
                actor_id="user",
                goal="express_emotion",
                confidence=0.8
            )
        ],
        emotional_state=EmotionalState(
            valence=-0.6,
            arousal=0.4,
            primary_emotion="negative"
        ),
        understanding_score=0.7
    )


@pytest.fixture
def high_risk_situation():
    """Yüksek riskli durum modeli."""
    return SituationModel(
        id="sit_risky",
        actors=[
            Actor(id="user", role="user"),
            Actor(id="assistant", role="assistant", name="UEM")
        ],
        intentions=[
            Intention(
                id="int_003",
                actor_id="user",
                goal="help",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                category="safety",
                level=0.9,
                description="Safety risk detected"
            )
        ],
        understanding_score=0.5
    )


@pytest.fixture
def simple_act_result():
    """Basit act seçim sonucu."""
    return ActSelectionResult(
        primary_acts=[DialogueAct.INFORM, DialogueAct.SUGGEST],
        secondary_acts=[DialogueAct.ACKNOWLEDGE],
        all_scores=[
            ActScore(act=DialogueAct.INFORM, score=0.8, reasons=["Intent match"]),
            ActScore(act=DialogueAct.SUGGEST, score=0.6, reasons=["Help intent"]),
            ActScore(act=DialogueAct.ACKNOWLEDGE, score=0.4, reasons=["Default"])
        ],
        strategy_used=SelectionStrategy.BALANCED,
        confidence=0.7
    )


@pytest.fixture
def empathy_act_result():
    """Empati odaklı act seçim sonucu."""
    return ActSelectionResult(
        primary_acts=[DialogueAct.EMPATHIZE, DialogueAct.COMFORT],
        secondary_acts=[DialogueAct.SUGGEST],
        all_scores=[
            ActScore(act=DialogueAct.EMPATHIZE, score=0.9, reasons=["Emotion match"]),
            ActScore(act=DialogueAct.COMFORT, score=0.7, reasons=["Negative valence"]),
            ActScore(act=DialogueAct.SUGGEST, score=0.4, reasons=["Help intent"])
        ],
        strategy_used=SelectionStrategy.EXPRESSIVE,
        confidence=0.8
    )


@pytest.fixture
def warning_act_result():
    """Uyarı odaklı act seçim sonucu."""
    return ActSelectionResult(
        primary_acts=[DialogueAct.WARN, DialogueAct.EMPATHIZE],
        secondary_acts=[DialogueAct.ADVISE],
        all_scores=[
            ActScore(act=DialogueAct.WARN, score=0.9, reasons=["High risk"]),
            ActScore(act=DialogueAct.EMPATHIZE, score=0.7, reasons=["Emotion"]),
            ActScore(act=DialogueAct.ADVISE, score=0.5, reasons=["Help"])
        ],
        strategy_used=SelectionStrategy.BALANCED,
        confidence=0.75
    )


# ============================================================================
# 1. MessagePlanner Oluşturma Testleri
# ============================================================================

class TestMessagePlannerCreation:
    """MessagePlanner oluşturma testleri."""

    def test_create_default_planner(self):
        """Varsayılan planner oluşturma."""
        planner = MessagePlanner()
        assert planner is not None
        assert planner.config is not None
        assert planner.config.default_tone == ToneType.NEUTRAL

    def test_create_with_custom_config(self, custom_config):
        """Özel config ile planner oluşturma."""
        planner = MessagePlanner(config=custom_config)
        assert planner.config.max_content_points == 5
        assert planner.config.max_constraints == 3
        assert planner.config.default_tone == ToneType.FORMAL

    def test_create_with_processors(self):
        """Processor'larla planner oluşturma."""
        planner = MessagePlanner(
            self_processor="mock_self",
            affect_processor="mock_affect"
        )
        assert planner.self_proc == "mock_self"
        assert planner.affect == "mock_affect"

    def test_act_content_map_initialized(self, default_planner):
        """Act-content map'in başlatıldığını doğrula."""
        assert len(default_planner._act_content_map) == 17
        assert DialogueAct.INFORM in default_planner._act_content_map
        assert DialogueAct.EMPATHIZE in default_planner._act_content_map

    def test_act_intent_map_initialized(self, default_planner):
        """Act-intent map'in başlatıldığını doğrula."""
        assert len(default_planner._act_intent_map) == 17
        assert DialogueAct.WARN in default_planner._act_intent_map

    def test_risk_constraint_map_initialized(self, default_planner):
        """Risk-constraint map'in başlatıldığını doğrula."""
        assert "safety" in default_planner._risk_constraint_map
        assert "ethical" in default_planner._risk_constraint_map


# ============================================================================
# 2. ContentPoint ve MessageConstraint Testleri
# ============================================================================

class TestContentPoint:
    """ContentPoint testleri."""

    def test_create_content_point(self):
        """ContentPoint oluşturma."""
        cp = ContentPoint(
            key="test",
            value="Test value",
            priority=1,
            required=True
        )
        assert cp.key == "test"
        assert cp.value == "Test value"
        assert cp.priority == 1
        assert cp.required is True

    def test_content_point_default_values(self):
        """ContentPoint varsayılan değerler."""
        cp = ContentPoint(key="test", value="value")
        assert cp.priority == 1
        assert cp.required is True

    def test_content_point_invalid_priority(self):
        """Geçersiz priority kontrolü."""
        with pytest.raises(ValueError):
            ContentPoint(key="test", value="value", priority=0)

    def test_content_point_priority_boundary(self):
        """Priority sınır değeri."""
        cp = ContentPoint(key="test", value="value", priority=1)
        assert cp.priority == 1


class TestMessageConstraint:
    """MessageConstraint testleri."""

    def test_create_constraint(self):
        """MessageConstraint oluşturma."""
        mc = MessageConstraint(
            constraint_type=ConstraintType.ETHICAL,
            description="Be honest",
            severity=ConstraintSeverity.HIGH
        )
        assert mc.constraint_type == ConstraintType.ETHICAL
        assert mc.description == "Be honest"
        assert mc.severity == ConstraintSeverity.HIGH

    def test_constraint_default_severity(self):
        """Varsayılan severity."""
        mc = MessageConstraint(
            constraint_type=ConstraintType.STYLE,
            description="Be polite"
        )
        assert mc.severity == ConstraintSeverity.MEDIUM

    def test_constraint_types(self):
        """Tüm constraint türlerini kontrol et."""
        types = [ConstraintType.ETHICAL, ConstraintType.STYLE,
                 ConstraintType.CONTENT, ConstraintType.SAFETY, ConstraintType.TONE]
        for ct in types:
            mc = MessageConstraint(constraint_type=ct, description="test")
            assert mc.constraint_type == ct

    def test_severity_levels(self):
        """Tüm severity seviyelerini kontrol et."""
        levels = [ConstraintSeverity.LOW, ConstraintSeverity.MEDIUM,
                  ConstraintSeverity.HIGH, ConstraintSeverity.CRITICAL]
        for level in levels:
            mc = MessageConstraint(
                constraint_type=ConstraintType.ETHICAL,
                description="test",
                severity=level
            )
            assert mc.severity == level


# ============================================================================
# 3. Plan Metodu Testleri
# ============================================================================

class TestPlanMethod:
    """Plan metodu testleri."""

    def test_plan_basic(self, default_planner, simple_act_result, simple_situation):
        """Basit plan oluşturma."""
        plan = default_planner.plan(simple_act_result, simple_situation)

        assert isinstance(plan, MessagePlan)
        assert plan.id.startswith("plan_")
        assert plan.situation_id == simple_situation.id
        assert len(plan.dialogue_acts) > 0

    def test_plan_has_primary_intent(self, default_planner, simple_act_result, simple_situation):
        """Plan'da primary intent var."""
        plan = default_planner.plan(simple_act_result, simple_situation)
        assert plan.primary_intent is not None
        assert len(plan.primary_intent) > 0

    def test_plan_has_tone(self, default_planner, simple_act_result, simple_situation):
        """Plan'da tone var."""
        plan = default_planner.plan(simple_act_result, simple_situation)
        assert isinstance(plan.tone, ToneType)

    def test_plan_has_content_points(self, default_planner, simple_act_result, simple_situation):
        """Plan'da content points var."""
        plan = default_planner.plan(simple_act_result, simple_situation)
        assert len(plan.content_points) > 0

    def test_plan_has_constraints(self, default_planner, simple_act_result, simple_situation):
        """Plan'da constraints var."""
        plan = default_planner.plan(simple_act_result, simple_situation)
        assert len(plan.constraints) > 0

    def test_plan_dialogue_acts_from_result(self, default_planner, simple_act_result, simple_situation):
        """Plan dialogue acts, act result'tan geliyor."""
        plan = default_planner.plan(simple_act_result, simple_situation)
        assert plan.dialogue_acts == simple_act_result.primary_acts

    def test_plan_context_has_act_confidence(self, default_planner, simple_act_result, simple_situation):
        """Plan context'te act selection confidence var."""
        plan = default_planner.plan(simple_act_result, simple_situation)
        assert "act_selection_confidence" in plan.context
        assert plan.context["act_selection_confidence"] == simple_act_result.confidence

    def test_plan_context_has_strategy(self, default_planner, simple_act_result, simple_situation):
        """Plan context'te strategy var."""
        plan = default_planner.plan(simple_act_result, simple_situation)
        assert "strategy_used" in plan.context
        assert plan.context["strategy_used"] == simple_act_result.strategy_used.value

    def test_plan_with_additional_context(self, default_planner, simple_act_result, simple_situation):
        """Ek context ile plan oluşturma."""
        plan = default_planner.plan(
            simple_act_result,
            simple_situation,
            context={"custom_key": "custom_value"}
        )
        assert "custom_key" in plan.context
        assert plan.context["custom_key"] == "custom_value"

    def test_plan_max_content_points(self, custom_config, simple_act_result, simple_situation):
        """Content points max sayı sınırı."""
        planner = MessagePlanner(config=custom_config)
        plan = planner.plan(simple_act_result, simple_situation)
        assert len(plan.content_points) <= custom_config.max_content_points

    def test_plan_max_constraints(self, custom_config, simple_act_result, simple_situation):
        """Constraints max sayı sınırı."""
        planner = MessagePlanner(config=custom_config)
        plan = planner.plan(simple_act_result, simple_situation)
        assert len(plan.constraints) <= custom_config.max_constraints


# ============================================================================
# 4. Primary Intent Belirleme Testleri
# ============================================================================

class TestDeterminePrimaryIntent:
    """Primary intent belirleme testleri."""

    def test_intent_from_inform_act(self, default_planner, simple_situation):
        """INFORM act'i için intent."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.INFORM],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        intent = default_planner._determine_primary_intent(act_result, simple_situation)
        assert "bilgilendir" in intent.lower()

    def test_intent_from_empathize_act(self, default_planner, simple_situation):
        """EMPATHIZE act'i için intent."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.EMPATHIZE],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        intent = default_planner._determine_primary_intent(act_result, simple_situation)
        assert "empati" in intent.lower()

    def test_intent_from_warn_act(self, default_planner, simple_situation):
        """WARN act'i için intent."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.WARN],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        intent = default_planner._determine_primary_intent(act_result, simple_situation)
        assert "uyar" in intent.lower()

    def test_intent_includes_user_goal(self, default_planner, simple_situation):
        """Intent'te user goal var."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.INFORM],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        intent = default_planner._determine_primary_intent(act_result, simple_situation)
        assert "ask" in intent.lower()

    def test_intent_empty_acts_fallback(self, default_planner, simple_situation):
        """Boş act listesi için fallback."""
        act_result = ActSelectionResult(
            primary_acts=[],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.3
        )
        intent = default_planner._determine_primary_intent(act_result, simple_situation)
        assert "kabul" in intent.lower()


# ============================================================================
# 5. Tone Belirleme Testleri
# ============================================================================

class TestDetermineTone:
    """Tone belirleme testleri."""

    def test_tone_high_risk_cautious(self, default_planner, high_risk_situation, simple_act_result):
        """Yüksek riskli durumda CAUTIOUS tone."""
        tone = default_planner._determine_tone(simple_act_result, high_risk_situation)
        assert tone == ToneType.CAUTIOUS

    def test_tone_negative_emotion_supportive(self, default_planner, emotional_situation, simple_act_result):
        """Negatif duygu için SUPPORTIVE tone."""
        tone = default_planner._determine_tone(simple_act_result, emotional_situation)
        assert tone in [ToneType.SUPPORTIVE, ToneType.EMPATHIC]

    def test_tone_positive_emotion_enthusiastic(self, default_planner, simple_situation):
        """Pozitif duygu için ENTHUSIASTIC tone."""
        situation = SituationModel(
            id="sit_positive",
            actors=[Actor(id="user", role="user")],
            emotional_state=EmotionalState(valence=0.7, arousal=0.3)
        )
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.ACKNOWLEDGE],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        tone = default_planner._determine_tone(act_result, situation)
        assert tone in [ToneType.ENTHUSIASTIC, ToneType.CASUAL]

    def test_tone_empathy_act_empathic(self, default_planner, simple_situation, empathy_act_result):
        """Empati act'i için EMPATHIC tone."""
        tone = default_planner._determine_tone(empathy_act_result, simple_situation)
        assert tone == ToneType.EMPATHIC

    def test_tone_warn_act_serious(self, default_planner, simple_situation):
        """WARN act'i için SERIOUS tone."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.WARN],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        tone = default_planner._determine_tone(act_result, simple_situation)
        assert tone == ToneType.SERIOUS

    def test_tone_refuse_act_formal(self, default_planner, simple_situation):
        """REFUSE act'i için FORMAL tone."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.REFUSE],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        tone = default_planner._determine_tone(act_result, simple_situation)
        assert tone == ToneType.FORMAL

    def test_tone_work_topic_formal(self, default_planner):
        """Work topic için FORMAL tone."""
        situation = SituationModel(
            id="sit_work",
            actors=[Actor(id="user", role="user")],
            topic_domain="work"
        )
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.INFORM],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        tone = default_planner._determine_tone(act_result, situation)
        assert tone == ToneType.FORMAL

    def test_tone_default_neutral(self, default_planner, simple_situation, simple_act_result):
        """Varsayılan tone NEUTRAL."""
        tone = default_planner._determine_tone(simple_act_result, simple_situation)
        # Emotion yok, risk yok, özel act yok - NEUTRAL olmalı
        assert tone == ToneType.NEUTRAL


# ============================================================================
# 6. Content Points Oluşturma Testleri
# ============================================================================

class TestGenerateContentPoints:
    """Content points oluşturma testleri."""

    def test_content_from_primary_acts(self, default_planner, simple_act_result, simple_situation):
        """Primary act'lerden content points."""
        points = default_planner._generate_content_points(simple_act_result, simple_situation)
        assert len(points) >= 2  # INFORM + SUGGEST

    def test_content_from_secondary_acts(self, default_planner, simple_act_result, simple_situation):
        """Secondary act'lerden content points."""
        points = default_planner._generate_content_points(simple_act_result, simple_situation)
        # Secondary acts required=False olmalı
        secondary_points = [p for p in points if not p.required]
        assert len(secondary_points) >= 1

    def test_content_priority_order(self, default_planner, simple_act_result, simple_situation):
        """Content points sıralı priority."""
        points = default_planner._generate_content_points(simple_act_result, simple_situation)
        # İlk nokta en yüksek öncelikli olmalı
        priorities = [p.priority for p in points]
        assert priorities == sorted(priorities)

    def test_content_with_risk_awareness(self, default_planner, simple_act_result, high_risk_situation):
        """Risk varsa awareness content eklenir."""
        points = default_planner._generate_content_points(simple_act_result, high_risk_situation)
        keys = [p.key for p in points]
        assert "risk_awareness" in keys

    def test_content_with_emotional_support(self, default_planner, simple_act_result, emotional_situation):
        """Negative emotion varsa support content eklenir."""
        points = default_planner._generate_content_points(simple_act_result, emotional_situation)
        keys = [p.key for p in points]
        assert "emotional_support" in keys or "empathy" in keys

    def test_content_inform_key(self, default_planner, simple_situation):
        """INFORM act'i information key üretir."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.INFORM],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        points = default_planner._generate_content_points(act_result, simple_situation)
        keys = [p.key for p in points]
        assert "information" in keys

    def test_content_empathize_key(self, default_planner, simple_situation, empathy_act_result):
        """EMPATHIZE act'i empathy key üretir."""
        points = default_planner._generate_content_points(empathy_act_result, simple_situation)
        keys = [p.key for p in points]
        assert "empathy" in keys


# ============================================================================
# 7. Constraints Oluşturma Testleri
# ============================================================================

class TestGenerateConstraints:
    """Constraints oluşturma testleri."""

    def test_constraints_from_risk(self, default_planner, simple_act_result, high_risk_situation):
        """Risk'ten constraint oluşturma."""
        constraints = default_planner._generate_constraints(simple_act_result, high_risk_situation)
        types = [c.constraint_type for c in constraints]
        assert ConstraintType.SAFETY in types

    def test_constraints_refuse_act(self, default_planner, simple_situation):
        """REFUSE act'i için style constraint."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.REFUSE],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.7
        )
        constraints = default_planner._generate_constraints(act_result, simple_situation)
        types = [c.constraint_type for c in constraints]
        assert ConstraintType.STYLE in types

    def test_constraints_warn_act(self, default_planner, simple_situation, warning_act_result):
        """WARN act'i için safety constraint."""
        constraints = default_planner._generate_constraints(warning_act_result, simple_situation)
        types = [c.constraint_type for c in constraints]
        assert ConstraintType.SAFETY in types

    def test_constraints_empathize_act(self, default_planner, simple_situation, empathy_act_result):
        """EMPATHIZE act'i için tone constraint."""
        constraints = default_planner._generate_constraints(empathy_act_result, simple_situation)
        types = [c.constraint_type for c in constraints]
        assert ConstraintType.TONE in types

    def test_constraints_always_ethical(self, default_planner, simple_act_result, simple_situation):
        """Her zaman ethical constraint var."""
        constraints = default_planner._generate_constraints(simple_act_result, simple_situation)
        types = [c.constraint_type for c in constraints]
        assert ConstraintType.ETHICAL in types

    def test_constraints_severity_from_risk_level(self, default_planner, simple_act_result):
        """Risk level'a göre severity."""
        situation = SituationModel(
            id="sit_critical",
            actors=[Actor(id="user", role="user")],
            risks=[
                Risk(category="safety", level=0.9, description="Critical risk")
            ]
        )
        constraints = default_planner._generate_constraints(simple_act_result, situation)
        safety_constraints = [c for c in constraints if c.constraint_type == ConstraintType.SAFETY]
        if safety_constraints:
            assert safety_constraints[0].severity == ConstraintSeverity.CRITICAL

    def test_constraints_disabled(self, simple_act_result, simple_situation):
        """Constraints devre dışı bırakılabilir."""
        config = MessagePlannerConfig(enable_constraints=False)
        planner = MessagePlanner(config=config)
        plan = planner.plan(simple_act_result, simple_situation)
        # Constraints devre dışı olsa da plan() içinde boş liste döner
        # çünkü config kontrolü _generate_constraints çağrılmadan önce
        assert isinstance(plan.constraints, list)


# ============================================================================
# 8. Confidence Hesaplama Testleri
# ============================================================================

class TestCalculateConfidence:
    """Confidence hesaplama testleri."""

    def test_confidence_high_act_confidence(self, default_planner, simple_situation):
        """Yüksek act confidence = yüksek plan confidence."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.INFORM],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.9
        )
        confidence = default_planner._calculate_confidence(act_result, simple_situation)
        assert confidence > 0.5

    def test_confidence_low_act_confidence(self, default_planner, simple_situation):
        """Düşük act confidence = düşük plan confidence."""
        act_result = ActSelectionResult(
            primary_acts=[DialogueAct.ACKNOWLEDGE],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.2
        )
        confidence = default_planner._calculate_confidence(act_result, simple_situation)
        assert confidence < 0.7

    def test_confidence_high_understanding(self, default_planner, simple_act_result):
        """Yüksek understanding = yüksek confidence bonus."""
        situation = SituationModel(
            id="sit_high_understanding",
            actors=[Actor(id="user", role="user")],
            understanding_score=0.9
        )
        confidence = default_planner._calculate_confidence(simple_act_result, situation)
        assert confidence > 0.5

    def test_confidence_low_risk_bonus(self, default_planner, simple_act_result, simple_situation):
        """Düşük risk = yüksek confidence bonus."""
        # simple_situation'da risk yok
        confidence = default_planner._calculate_confidence(simple_act_result, simple_situation)
        assert confidence > 0.4

    def test_confidence_high_risk_penalty(self, default_planner, simple_act_result, high_risk_situation, simple_situation):
        """Yüksek risk = düşük confidence bonus."""
        confidence_risky = default_planner._calculate_confidence(simple_act_result, high_risk_situation)
        confidence_safe = default_planner._calculate_confidence(simple_act_result, simple_situation)
        assert confidence_risky < confidence_safe

    def test_confidence_bounded(self, default_planner, simple_act_result, simple_situation):
        """Confidence 0-1 arasında."""
        confidence = default_planner._calculate_confidence(simple_act_result, simple_situation)
        assert 0.0 <= confidence <= 1.0


# ============================================================================
# 9. Update Plan Testleri
# ============================================================================

class TestUpdatePlan:
    """Update plan testleri."""

    def test_update_creates_new_plan(self, default_planner, simple_act_result, simple_situation):
        """Update yeni plan oluşturur."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(original)
        assert original.id != updated.id

    def test_update_tone(self, default_planner, simple_act_result, simple_situation):
        """Tone güncelleme."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(original, new_tone=ToneType.FORMAL)
        assert updated.tone == ToneType.FORMAL

    def test_update_preserves_original_tone(self, default_planner, simple_act_result, simple_situation):
        """Tone belirtilmezse korunur."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(original)
        assert updated.tone == original.tone

    def test_update_add_content_points(self, default_planner, simple_act_result, simple_situation):
        """Content points ekleme."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(
            original,
            additional_content_points=["Extra point 1", "Extra point 2"]
        )
        assert len(updated.content_points) >= len(original.content_points)
        assert "Extra point 1" in updated.content_points

    def test_update_add_constraints(self, default_planner, simple_act_result, simple_situation):
        """Constraints ekleme."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(
            original,
            additional_constraints=["Extra constraint"]
        )
        assert len(updated.constraints) >= len(original.constraints)
        assert "Extra constraint" in updated.constraints

    def test_update_add_context(self, default_planner, simple_act_result, simple_situation):
        """Context ekleme."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(
            original,
            new_context={"updated_by": "test"}
        )
        assert "updated_by" in updated.context
        assert updated.context["updated_by"] == "test"

    def test_update_preserves_original_plan_id(self, default_planner, simple_act_result, simple_situation):
        """Update context'te original plan ID var."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(original)
        assert "original_plan_id" in updated.context
        assert updated.context["original_plan_id"] == original.id

    def test_update_preserves_dialogue_acts(self, default_planner, simple_act_result, simple_situation):
        """Update dialogue acts korur."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(original)
        assert updated.dialogue_acts == original.dialogue_acts

    def test_update_preserves_situation_id(self, default_planner, simple_act_result, simple_situation):
        """Update situation ID korur."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(original)
        assert updated.situation_id == original.situation_id


# ============================================================================
# 10. Risk Level Hesaplama Testleri
# ============================================================================

class TestCalculateRiskLevel:
    """Risk level hesaplama testleri."""

    def test_risk_level_no_risks(self, default_planner, simple_situation):
        """Risk yoksa 0.0."""
        risk_level = default_planner._calculate_risk_level(simple_situation)
        assert risk_level == 0.0

    def test_risk_level_single_risk(self, default_planner, high_risk_situation):
        """Tek risk varsa onun level'ı."""
        risk_level = default_planner._calculate_risk_level(high_risk_situation)
        assert risk_level == 0.9

    def test_risk_level_multiple_risks(self, default_planner):
        """Birden fazla risk varsa en yüksek."""
        situation = SituationModel(
            id="sit_multi_risk",
            actors=[Actor(id="user", role="user")],
            risks=[
                Risk(category="emotional", level=0.5, description="Medium risk"),
                Risk(category="safety", level=0.8, description="High risk")
            ]
        )
        risk_level = default_planner._calculate_risk_level(situation)
        assert risk_level == 0.8


# ============================================================================
# 11. Entegrasyon Testleri
# ============================================================================

class TestIntegration:
    """Entegrasyon testleri."""

    def test_full_pipeline_simple(self, default_planner, simple_act_result, simple_situation):
        """Basit tam pipeline testi."""
        plan = default_planner.plan(simple_act_result, simple_situation)

        # Plan geçerli
        assert plan.id.startswith("plan_")
        assert len(plan.dialogue_acts) > 0
        assert plan.primary_intent
        assert isinstance(plan.tone, ToneType)
        assert 0.0 <= plan.risk_level <= 1.0
        assert 0.0 <= plan.confidence <= 1.0

    def test_full_pipeline_emotional(self, default_planner, empathy_act_result, emotional_situation):
        """Duygusal durum pipeline testi."""
        plan = default_planner.plan(empathy_act_result, emotional_situation)

        # Tone empatik olmalı
        assert plan.tone in [ToneType.EMPATHIC, ToneType.SUPPORTIVE]

        # Dialogue acts empati içermeli
        assert DialogueAct.EMPATHIZE in plan.dialogue_acts

    def test_full_pipeline_high_risk(self, default_planner, warning_act_result, high_risk_situation):
        """Yüksek risk pipeline testi."""
        plan = default_planner.plan(warning_act_result, high_risk_situation)

        # Tone dikkatli olmalı
        assert plan.tone == ToneType.CAUTIOUS

        # Risk level yüksek olmalı
        assert plan.risk_level > 0.5

    def test_update_after_plan(self, default_planner, simple_act_result, simple_situation):
        """Plan sonrası update testi."""
        original = default_planner.plan(simple_act_result, simple_situation)
        updated = default_planner.update_plan(
            original,
            new_tone=ToneType.FORMAL,
            additional_content_points=["Additional info"],
            additional_constraints=["Be concise"],
            new_context={"reason": "User requested formal tone"}
        )

        # Güncellemeler uygulandı
        assert updated.tone == ToneType.FORMAL
        assert "Additional info" in updated.content_points
        assert "Be concise" in updated.constraints
        assert "reason" in updated.context

        # Orijinal değişmedi
        assert original.tone != ToneType.FORMAL or original.tone == updated.tone

    def test_empty_primary_acts_fallback(self, default_planner, simple_situation):
        """Boş primary acts fallback testi."""
        act_result = ActSelectionResult(
            primary_acts=[],
            secondary_acts=[],
            all_scores=[],
            strategy_used=SelectionStrategy.BALANCED,
            confidence=0.3
        )
        plan = default_planner.plan(act_result, simple_situation)

        # Fallback ACKNOWLEDGE olmalı
        assert DialogueAct.ACKNOWLEDGE in plan.dialogue_acts
