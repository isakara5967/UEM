"""
tests/unit/test_risk_scorer.py

RiskScorer testleri - MessagePlan + SituationModel → RiskAssessment

Test kategorileri:
1. RiskScorer oluşturma
2. Assess metodu
3. Ethical risk değerlendirme
4. Trust impact değerlendirme
5. Safety risk değerlendirme
6. Structural impact değerlendirme
7. Overall score hesaplama
8. Recommendation ve reasoning
9. Risk patterns
10. Entegrasyon testleri
"""

import pytest

from core.language.risk.scorer import RiskScorer, RiskScorerConfig
from core.language.risk.types import (
    RiskLevel,
    RiskCategory,
    RiskFactor,
    RiskAssessment,
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


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def default_scorer():
    """Varsayılan RiskScorer."""
    return RiskScorer()


@pytest.fixture
def custom_config():
    """Özelleştirilmiş konfigürasyon."""
    return RiskScorerConfig(
        ethical_weight=0.4,
        trust_weight=0.3,
        safety_weight=0.2,
        structural_weight=0.1,
        high_risk_threshold=0.5,
        critical_risk_threshold=0.7,
        enable_detailed_factors=True
    )


@pytest.fixture
def simple_plan():
    """Basit mesaj planı."""
    return MessagePlan(
        id="plan_test123",
        dialogue_acts=[DialogueAct.INFORM, DialogueAct.SUGGEST],
        primary_intent="Kullanıcıyı bilgilendir",
        tone=ToneType.NEUTRAL,
        content_points=["Bilgi ver", "Öneri sun"],
        constraints=[],
        confidence=0.7
    )


@pytest.fixture
def risky_plan():
    """Riskli mesaj planı."""
    return MessagePlan(
        id="plan_risky",
        dialogue_acts=[DialogueAct.REFUSE, DialogueAct.WARN, DialogueAct.SUGGEST],
        primary_intent="İsteği reddet ve uyar",
        tone=ToneType.SERIOUS,
        content_points=["Reddet", "Uyar", "Alternatif öner", "Açıkla", "Detaylandır"],
        constraints=["Etik sınırları koru"],
        confidence=0.4
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
                id="int_002",
                actor_id="user",
                goal="help",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                category="safety",
                level=0.9,
                description="Güvenlik riski tespit edildi"
            )
        ],
        understanding_score=0.5
    )


@pytest.fixture
def ethical_risk_situation():
    """Etik riskli durum modeli."""
    return SituationModel(
        id="sit_ethical",
        actors=[Actor(id="user", role="user")],
        risks=[
            Risk(
                category="ethical",
                level=0.7,
                description="Etik ihlal riski"
            )
        ],
        understanding_score=0.6
    )


@pytest.fixture
def emotional_situation():
    """Duygusal durum modeli."""
    return SituationModel(
        id="sit_emotional",
        actors=[Actor(id="user", role="user")],
        emotional_state=EmotionalState(
            valence=-0.7,
            arousal=0.5,
            primary_emotion="sad"
        ),
        understanding_score=0.3
    )


@pytest.fixture
def emergency_situation():
    """Acil durum modeli."""
    return SituationModel(
        id="sit_emergency",
        actors=[Actor(id="user", role="user")],
        key_entities=["intihar", "yardım"],
        context={"message": "kendime zarar vermek istiyorum"},
        understanding_score=0.8
    )


# ============================================================================
# 1. RiskScorer Oluşturma Testleri
# ============================================================================

class TestRiskScorerCreation:
    """RiskScorer oluşturma testleri."""

    def test_create_default_scorer(self):
        """Varsayılan scorer oluşturma."""
        scorer = RiskScorer()
        assert scorer is not None
        assert scorer.config is not None

    def test_create_with_custom_config(self, custom_config):
        """Özel config ile scorer oluşturma."""
        scorer = RiskScorer(config=custom_config)
        assert scorer.config.ethical_weight == 0.4
        assert scorer.config.trust_weight == 0.3
        assert scorer.config.safety_weight == 0.2

    def test_create_with_processors(self):
        """Processor'larla scorer oluşturma."""
        scorer = RiskScorer(
            ethics_checker="mock_ethics",
            trust_calculator="mock_trust",
            metamind="mock_metamind"
        )
        assert scorer.ethics == "mock_ethics"
        assert scorer.trust == "mock_trust"
        assert scorer.metamind == "mock_metamind"

    def test_risk_patterns_initialized(self, default_scorer):
        """Risk patterns başlatıldı."""
        patterns = default_scorer.get_risk_patterns()
        assert "safety" in patterns
        assert "ethical" in patterns
        assert "privacy" in patterns

    def test_default_config_values(self, default_scorer):
        """Varsayılan config değerleri."""
        assert default_scorer.config.ethical_weight == 0.35
        assert default_scorer.config.trust_weight == 0.25
        assert default_scorer.config.safety_weight == 0.25
        assert default_scorer.config.structural_weight == 0.15


# ============================================================================
# 2. Assess Metodu Testleri
# ============================================================================

class TestAssessMethod:
    """Assess metodu testleri."""

    def test_assess_returns_risk_assessment(self, default_scorer, simple_plan, simple_situation):
        """Assess RiskAssessment döndürür."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert isinstance(result, RiskAssessment)

    def test_assess_has_id(self, default_scorer, simple_plan, simple_situation):
        """Assessment'ta ID var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert result.id.startswith("risk_")

    def test_assess_has_level(self, default_scorer, simple_plan, simple_situation):
        """Assessment'ta level var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert isinstance(result.level, RiskLevel)

    def test_assess_has_overall_score(self, default_scorer, simple_plan, simple_situation):
        """Assessment'ta overall_score var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert 0.0 <= result.overall_score <= 1.0

    def test_assess_has_ethical_score(self, default_scorer, simple_plan, simple_situation):
        """Assessment'ta ethical_score var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert 0.0 <= result.ethical_score <= 1.0

    def test_assess_has_trust_impact(self, default_scorer, simple_plan, simple_situation):
        """Assessment'ta trust_impact var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert -1.0 <= result.trust_impact <= 1.0

    def test_assess_has_structural_impact(self, default_scorer, simple_plan, simple_situation):
        """Assessment'ta structural_impact var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert 0.0 <= result.structural_impact <= 1.0

    def test_assess_has_recommendation(self, default_scorer, simple_plan, simple_situation):
        """Assessment'ta recommendation var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert result.recommendation in ("approve", "review", "modify", "reject")

    def test_assess_has_reasoning(self, default_scorer, simple_plan, simple_situation):
        """Assessment'ta reasoning var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert len(result.reasoning) > 0

    def test_assess_has_message_plan_id(self, default_scorer, simple_plan, simple_situation):
        """Assessment'ta plan ID var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert result.message_plan_id == simple_plan.id

    def test_assess_has_situation_id_in_context(self, default_scorer, simple_plan, simple_situation):
        """Assessment context'te situation ID var."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert "situation_id" in result.context
        assert result.context["situation_id"] == simple_situation.id

    def test_assess_low_risk_situation(self, default_scorer, simple_plan, simple_situation):
        """Düşük riskli durum değerlendirmesi."""
        result = default_scorer.assess(simple_plan, simple_situation)
        # Basit plan ve basit durum = düşük risk beklenir
        assert result.level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_assess_high_risk_situation(self, default_scorer, simple_plan, high_risk_situation):
        """Yüksek riskli durum değerlendirmesi."""
        result = default_scorer.assess(simple_plan, high_risk_situation)
        # Güvenlik riski var = yüksek risk beklenir
        assert result.overall_score > 0.3


# ============================================================================
# 3. Ethical Risk Değerlendirme Testleri
# ============================================================================

class TestEthicalRiskAssessment:
    """Etik risk değerlendirme testleri."""

    def test_ethical_risk_from_situation(self, default_scorer, simple_plan, ethical_risk_situation):
        """Situation'dan etik risk."""
        result = default_scorer.assess(simple_plan, ethical_risk_situation)
        assert result.ethical_score > 0

    def test_ethical_risk_from_constraints(self, default_scorer, risky_plan, simple_situation):
        """Plan constraints'tan etik risk."""
        result = default_scorer.assess(risky_plan, simple_situation)
        assert result.ethical_score > 0

    def test_ethical_risk_from_sensitive_acts(self, default_scorer, risky_plan, simple_situation):
        """Hassas act'lerden etik risk."""
        # REFUSE, WARN act'leri var
        result = default_scorer.assess(risky_plan, simple_situation)
        ethical_factors = [
            f for f in result.factors
            if f.category == RiskCategory.ETHICAL
        ]
        assert len(ethical_factors) > 0

    def test_no_ethical_risk_simple_plan(self, default_scorer, simple_plan, simple_situation):
        """Basit planda düşük etik risk."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert result.ethical_score < 0.5


# ============================================================================
# 4. Trust Impact Değerlendirme Testleri
# ============================================================================

class TestTrustImpactAssessment:
    """Güven etkisi değerlendirme testleri."""

    def test_trust_impact_negative_emotion(self, default_scorer, simple_plan, emotional_situation):
        """Negatif duygu güven etkisi."""
        result = default_scorer.assess(simple_plan, emotional_situation)
        # Negatif valence = negatif trust impact
        assert result.trust_impact < 0

    def test_trust_impact_low_understanding(self, default_scorer, simple_plan, emotional_situation):
        """Düşük anlama skoru güven etkisi."""
        # emotional_situation.understanding_score = 0.3
        result = default_scorer.assess(simple_plan, emotional_situation)
        trust_factors = [
            f for f in result.factors
            if f.category == RiskCategory.FACTUAL and "anlama" in f.description.lower()
        ]
        assert len(trust_factors) > 0

    def test_trust_impact_low_confidence(self, default_scorer, risky_plan, simple_situation):
        """Düşük plan confidence güven etkisi."""
        # risky_plan.confidence = 0.4
        result = default_scorer.assess(risky_plan, simple_situation)
        confidence_factors = [
            f for f in result.factors
            if "güven" in f.description.lower() and "plan" in f.description.lower()
        ]
        assert len(confidence_factors) > 0

    def test_trust_impact_serious_tone(self, default_scorer, risky_plan, simple_situation):
        """Ciddi ton güven etkisi."""
        # risky_plan.tone = ToneType.SERIOUS
        result = default_scorer.assess(risky_plan, simple_situation)
        tone_factors = [
            f for f in result.factors
            if "ton" in f.description.lower() or "ciddi" in f.description.lower()
        ]
        assert len(tone_factors) > 0


# ============================================================================
# 5. Safety Risk Değerlendirme Testleri
# ============================================================================

class TestSafetyRiskAssessment:
    """Güvenlik riski değerlendirme testleri."""

    def test_safety_risk_physical(self, default_scorer, simple_plan, high_risk_situation):
        """Fiziksel güvenlik riski."""
        result = default_scorer.assess(simple_plan, high_risk_situation)
        safety_factors = [
            f for f in result.factors
            if f.category == RiskCategory.SAFETY
        ]
        assert len(safety_factors) > 0

    def test_safety_risk_emergency_keywords(self, default_scorer, simple_plan, emergency_situation):
        """Acil durum anahtar kelimeleri."""
        result = default_scorer.assess(simple_plan, emergency_situation)
        safety_factors = [
            f for f in result.factors
            if f.category == RiskCategory.SAFETY
        ]
        assert len(safety_factors) > 0

    def test_safety_risk_high_level(self, default_scorer, simple_plan, high_risk_situation):
        """Yüksek güvenlik riski seviyesi."""
        result = default_scorer.assess(simple_plan, high_risk_situation)
        # 0.9 safety risk should contribute significantly
        assert result.context["safety_score"] > 0.5

    def test_no_safety_risk_simple_situation(self, default_scorer, simple_plan, simple_situation):
        """Basit durumda güvenlik riski yok."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert result.context["safety_score"] == 0.0


# ============================================================================
# 6. Structural Impact Değerlendirme Testleri
# ============================================================================

class TestStructuralImpactAssessment:
    """Yapısal etki değerlendirme testleri."""

    def test_structural_too_many_acts(self, default_scorer, simple_situation):
        """Çok fazla act yapısal risk."""
        plan = MessagePlan(
            id="plan_many_acts",
            dialogue_acts=[
                DialogueAct.INFORM, DialogueAct.EXPLAIN,
                DialogueAct.SUGGEST, DialogueAct.ADVISE
            ],
            primary_intent="Test",
            confidence=0.7
        )
        result = default_scorer.assess(plan, simple_situation)
        structural_factors = [
            f for f in result.factors
            if "fazla" in f.description.lower() and "eylem" in f.description.lower()
        ]
        assert len(structural_factors) > 0

    def test_structural_conflicting_acts(self, default_scorer, simple_situation):
        """Çelişkili act'ler yapısal risk."""
        plan = MessagePlan(
            id="plan_conflict",
            dialogue_acts=[DialogueAct.REFUSE, DialogueAct.SUGGEST],
            primary_intent="Test",
            confidence=0.7
        )
        result = default_scorer.assess(plan, simple_situation)
        conflict_factors = [
            f for f in result.factors
            if "çelişkili" in f.description.lower()
        ]
        assert len(conflict_factors) > 0

    def test_structural_many_content_points(self, default_scorer, risky_plan, simple_situation):
        """Çok fazla içerik noktası."""
        # risky_plan has 5 content points
        result = default_scorer.assess(risky_plan, simple_situation)
        content_factors = [
            f for f in result.factors
            if "içerik noktası" in f.description.lower()
        ]
        assert len(content_factors) > 0

    def test_no_structural_impact_simple_plan(self, default_scorer, simple_plan, simple_situation):
        """Basit planda yapısal etki yok."""
        result = default_scorer.assess(simple_plan, simple_situation)
        # 2 acts, 2 content points = no structural issues
        assert result.structural_impact < 0.3


# ============================================================================
# 7. Overall Score Hesaplama Testleri
# ============================================================================

class TestOverallScoreCalculation:
    """Genel skor hesaplama testleri."""

    def test_overall_score_weights(self, custom_config, simple_plan, simple_situation):
        """Ağırlıklı skor hesaplama."""
        scorer = RiskScorer(config=custom_config)
        result = scorer.assess(simple_plan, simple_situation)
        assert 0.0 <= result.overall_score <= 1.0

    def test_overall_score_bounded(self, default_scorer, risky_plan, high_risk_situation):
        """Skor sınırlı."""
        result = default_scorer.assess(risky_plan, high_risk_situation)
        assert 0.0 <= result.overall_score <= 1.0

    def test_overall_score_affects_level(self, default_scorer, simple_plan, high_risk_situation):
        """Skor seviyeyi etkiler."""
        result = default_scorer.assess(simple_plan, high_risk_situation)
        if result.overall_score >= 0.75:
            assert result.level == RiskLevel.CRITICAL
        elif result.overall_score >= 0.5:
            assert result.level == RiskLevel.HIGH
        elif result.overall_score >= 0.25:
            assert result.level == RiskLevel.MEDIUM
        else:
            assert result.level == RiskLevel.LOW


# ============================================================================
# 8. Recommendation ve Reasoning Testleri
# ============================================================================

class TestRecommendationAndReasoning:
    """Öneri ve gerekçe testleri."""

    def test_recommendation_low_risk(self, default_scorer, simple_plan, simple_situation):
        """Düşük risk önerisi."""
        result = default_scorer.assess(simple_plan, simple_situation)
        if result.level == RiskLevel.LOW:
            assert result.recommendation == "approve"

    def test_recommendation_critical_risk(self, default_scorer, simple_plan, emergency_situation):
        """Kritik risk önerisi."""
        result = default_scorer.assess(simple_plan, emergency_situation)
        # Emergency keywords trigger safety risk
        if result.level == RiskLevel.CRITICAL:
            assert result.recommendation == "reject"

    def test_recommendation_safety_override(self, default_scorer, simple_plan, high_risk_situation):
        """Güvenlik riski öneri override."""
        result = default_scorer.assess(simple_plan, high_risk_situation)
        # High safety score should lead to reject
        if result.context["safety_score"] > 0.7:
            assert result.recommendation == "reject"

    def test_reasoning_includes_score(self, default_scorer, simple_plan, simple_situation):
        """Gerekçe skor içerir."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert "skor" in result.reasoning.lower()

    def test_reasoning_includes_level(self, default_scorer, simple_plan, simple_situation):
        """Gerekçe seviye içerir."""
        result = default_scorer.assess(simple_plan, simple_situation)
        assert "risk" in result.reasoning.lower()


# ============================================================================
# 9. Risk Patterns Testleri
# ============================================================================

class TestRiskPatterns:
    """Risk pattern testleri."""

    def test_get_risk_patterns(self, default_scorer):
        """Risk pattern'leri alma."""
        patterns = default_scorer.get_risk_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) > 0

    def test_safety_patterns(self, default_scorer):
        """Güvenlik pattern'leri."""
        patterns = default_scorer.get_risk_patterns()
        assert "intihar" in patterns["safety"]
        assert "ölmek" in patterns["safety"]

    def test_ethical_patterns(self, default_scorer):
        """Etik pattern'leri."""
        patterns = default_scorer.get_risk_patterns()
        assert "yasadışı" in patterns["ethical"]

    def test_privacy_patterns(self, default_scorer):
        """Gizlilik pattern'leri."""
        patterns = default_scorer.get_risk_patterns()
        assert "şifre" in patterns["privacy"]


# ============================================================================
# 10. Factors Testleri
# ============================================================================

class TestFactors:
    """Risk faktörleri testleri."""

    def test_factors_included_when_enabled(self, default_scorer, risky_plan, high_risk_situation):
        """Faktörler dahil edilir (enabled)."""
        result = default_scorer.assess(risky_plan, high_risk_situation)
        assert len(result.factors) > 0

    def test_factors_excluded_when_disabled(self, risky_plan, high_risk_situation):
        """Faktörler hariç tutulur (disabled)."""
        config = RiskScorerConfig(enable_detailed_factors=False)
        scorer = RiskScorer(config=config)
        result = scorer.assess(risky_plan, high_risk_situation)
        assert len(result.factors) == 0

    def test_factors_have_category(self, default_scorer, risky_plan, high_risk_situation):
        """Faktörlerin kategorisi var."""
        result = default_scorer.assess(risky_plan, high_risk_situation)
        for factor in result.factors:
            assert isinstance(factor.category, RiskCategory)

    def test_factors_have_score(self, default_scorer, risky_plan, high_risk_situation):
        """Faktörlerin skoru var."""
        result = default_scorer.assess(risky_plan, high_risk_situation)
        for factor in result.factors:
            assert 0.0 <= factor.score <= 1.0

    def test_factors_have_source(self, default_scorer, risky_plan, high_risk_situation):
        """Faktörlerin kaynağı var."""
        result = default_scorer.assess(risky_plan, high_risk_situation)
        for factor in result.factors:
            assert factor.source in ("situation", "plan", "unknown")


# ============================================================================
# 11. Entegrasyon Testleri
# ============================================================================

class TestIntegration:
    """Entegrasyon testleri."""

    def test_full_assessment_flow(self, default_scorer, risky_plan, high_risk_situation):
        """Tam değerlendirme akışı."""
        result = default_scorer.assess(risky_plan, high_risk_situation)

        # Tüm alanlar dolu
        assert result.id is not None
        assert result.level is not None
        assert result.overall_score >= 0.0
        assert result.recommendation is not None
        assert result.reasoning is not None

    def test_multiple_risk_sources(self, default_scorer, risky_plan, high_risk_situation):
        """Birden fazla risk kaynağı."""
        result = default_scorer.assess(risky_plan, high_risk_situation)

        # Birden fazla kategori
        categories = set(f.category for f in result.factors)
        assert len(categories) >= 2

    def test_consistent_results(self, default_scorer, simple_plan, simple_situation):
        """Tutarlı sonuçlar."""
        result1 = default_scorer.assess(simple_plan, simple_situation)
        result2 = default_scorer.assess(simple_plan, simple_situation)

        # Aynı input = aynı level
        assert result1.level == result2.level
