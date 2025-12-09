"""
tests/unit/test_risk_types.py

RiskLevel, RiskCategory, RiskFactor, RiskAssessment test suite.
Faz 4 - Risk değerlendirme sistemi testleri.

Test count: 25+
"""

import pytest
from datetime import datetime
from core.language.risk import (
    RiskLevel,
    RiskCategory,
    RiskFactor,
    RiskAssessment,
    generate_risk_assessment_id,
)
from core.language.risk.types import generate_risk_factor_id


# ============================================================================
# RiskLevel Enum Tests
# ============================================================================

class TestRiskLevel:
    """RiskLevel enum tests."""

    def test_risk_level_values(self):
        """Test RiskLevel has all required values."""
        expected = ["low", "medium", "high", "critical"]
        actual = [level.value for level in RiskLevel]
        for exp in expected:
            assert exp in actual

    def test_risk_level_count(self):
        """Test RiskLevel has 4 levels."""
        assert len(RiskLevel) == 4

    def test_risk_level_from_score_low(self):
        """Test from_score returns LOW for low scores."""
        assert RiskLevel.from_score(0.0) == RiskLevel.LOW
        assert RiskLevel.from_score(0.1) == RiskLevel.LOW
        assert RiskLevel.from_score(0.24) == RiskLevel.LOW

    def test_risk_level_from_score_medium(self):
        """Test from_score returns MEDIUM for medium scores."""
        assert RiskLevel.from_score(0.25) == RiskLevel.MEDIUM
        assert RiskLevel.from_score(0.35) == RiskLevel.MEDIUM
        assert RiskLevel.from_score(0.49) == RiskLevel.MEDIUM

    def test_risk_level_from_score_high(self):
        """Test from_score returns HIGH for high scores."""
        assert RiskLevel.from_score(0.50) == RiskLevel.HIGH
        assert RiskLevel.from_score(0.60) == RiskLevel.HIGH
        assert RiskLevel.from_score(0.74) == RiskLevel.HIGH

    def test_risk_level_from_score_critical(self):
        """Test from_score returns CRITICAL for critical scores."""
        assert RiskLevel.from_score(0.75) == RiskLevel.CRITICAL
        assert RiskLevel.from_score(0.90) == RiskLevel.CRITICAL
        assert RiskLevel.from_score(1.0) == RiskLevel.CRITICAL

    def test_risk_level_requires_human_approval(self):
        """Test requires_human_approval property."""
        assert not RiskLevel.LOW.requires_human_approval
        assert not RiskLevel.MEDIUM.requires_human_approval
        assert RiskLevel.HIGH.requires_human_approval
        assert RiskLevel.CRITICAL.requires_human_approval

    def test_risk_level_allows_auto_approval(self):
        """Test allows_auto_approval property."""
        assert RiskLevel.LOW.allows_auto_approval
        assert not RiskLevel.MEDIUM.allows_auto_approval
        assert not RiskLevel.HIGH.allows_auto_approval
        assert not RiskLevel.CRITICAL.allows_auto_approval


# ============================================================================
# RiskCategory Enum Tests
# ============================================================================

class TestRiskCategory:
    """RiskCategory enum tests."""

    def test_risk_category_values(self):
        """Test RiskCategory has all required values."""
        expected = ["ethical", "emotional", "factual", "safety", "privacy", "boundary"]
        actual = [cat.value for cat in RiskCategory]
        for exp in expected:
            assert exp in actual

    def test_risk_category_count(self):
        """Test RiskCategory has 6 categories."""
        assert len(RiskCategory) == 6


# ============================================================================
# RiskFactor Tests
# ============================================================================

class TestRiskFactor:
    """RiskFactor dataclass tests."""

    def test_risk_factor_creation(self):
        """Test RiskFactor creation."""
        factor = RiskFactor(
            id="rf_123",
            category=RiskCategory.ETHICAL,
            description="Potential ethical violation",
            score=0.6
        )
        assert factor.id == "rf_123"
        assert factor.category == RiskCategory.ETHICAL
        assert factor.score == 0.6

    def test_risk_factor_score_validation(self):
        """Test RiskFactor score validation."""
        with pytest.raises(ValueError):
            RiskFactor(
                id="rf_1",
                category=RiskCategory.ETHICAL,
                description="test",
                score=1.5
            )

        with pytest.raises(ValueError):
            RiskFactor(
                id="rf_1",
                category=RiskCategory.ETHICAL,
                description="test",
                score=-0.1
            )

    def test_risk_factor_is_high(self):
        """Test is_high property."""
        factor_high = RiskFactor(
            id="rf_1",
            category=RiskCategory.SAFETY,
            description="High risk",
            score=0.8
        )
        assert factor_high.is_high

        factor_low = RiskFactor(
            id="rf_2",
            category=RiskCategory.SAFETY,
            description="Low risk",
            score=0.5
        )
        assert not factor_low.is_high

    def test_risk_factor_is_critical(self):
        """Test is_critical property."""
        factor_critical = RiskFactor(
            id="rf_1",
            category=RiskCategory.SAFETY,
            description="Critical risk",
            score=0.9
        )
        assert factor_critical.is_critical

        factor_high = RiskFactor(
            id="rf_2",
            category=RiskCategory.SAFETY,
            description="High risk",
            score=0.8
        )
        assert not factor_high.is_critical

    def test_risk_factor_with_evidence(self):
        """Test RiskFactor with evidence."""
        factor = RiskFactor(
            id="rf_1",
            category=RiskCategory.FACTUAL,
            description="Factual error",
            score=0.6,
            evidence=["contradicts known facts", "source not verified"]
        )
        assert len(factor.evidence) == 2

    def test_risk_factor_with_mitigation(self):
        """Test RiskFactor with mitigation."""
        factor = RiskFactor(
            id="rf_1",
            category=RiskCategory.EMOTIONAL,
            description="May cause distress",
            score=0.7,
            mitigation="Use gentle language and offer support"
        )
        assert "gentle" in factor.mitigation


# ============================================================================
# RiskAssessment Tests
# ============================================================================

class TestRiskAssessment:
    """RiskAssessment dataclass tests."""

    def test_risk_assessment_creation(self):
        """Test RiskAssessment creation."""
        assessment = RiskAssessment(
            id="risk_123",
            level=RiskLevel.MEDIUM,
            overall_score=0.4,
            ethical_score=0.3,
            trust_impact=0.1
        )
        assert assessment.id == "risk_123"
        assert assessment.level == RiskLevel.MEDIUM
        assert assessment.overall_score == 0.4

    def test_risk_assessment_score_validation(self):
        """Test RiskAssessment score validation."""
        # overall_score
        with pytest.raises(ValueError):
            RiskAssessment(id="r", level=RiskLevel.LOW, overall_score=1.5)

        # ethical_score
        with pytest.raises(ValueError):
            RiskAssessment(id="r", level=RiskLevel.LOW, ethical_score=1.5)

        # trust_impact (-1 to 1)
        with pytest.raises(ValueError):
            RiskAssessment(id="r", level=RiskLevel.LOW, trust_impact=1.5)

        with pytest.raises(ValueError):
            RiskAssessment(id="r", level=RiskLevel.LOW, trust_impact=-1.5)

        # structural_impact
        with pytest.raises(ValueError):
            RiskAssessment(id="r", level=RiskLevel.LOW, structural_impact=1.5)

    def test_risk_assessment_recommendation_validation(self):
        """Test RiskAssessment recommendation validation."""
        with pytest.raises(ValueError):
            RiskAssessment(
                id="r",
                level=RiskLevel.LOW,
                recommendation="invalid_recommendation"
            )

    def test_risk_assessment_valid_recommendations(self):
        """Test all valid recommendations."""
        for rec in ["approve", "review", "modify", "reject"]:
            assessment = RiskAssessment(
                id=f"r_{rec}",
                level=RiskLevel.LOW,
                recommendation=rec
            )
            assert assessment.recommendation == rec

    def test_risk_assessment_is_approved(self):
        """Test is_approved property."""
        approved = RiskAssessment(
            id="r",
            level=RiskLevel.LOW,
            recommendation="approve"
        )
        assert approved.is_approved
        assert not approved.is_rejected
        assert not approved.needs_review

    def test_risk_assessment_is_rejected(self):
        """Test is_rejected property."""
        rejected = RiskAssessment(
            id="r",
            level=RiskLevel.CRITICAL,
            recommendation="reject"
        )
        assert rejected.is_rejected
        assert not rejected.is_approved
        assert not rejected.needs_review

    def test_risk_assessment_needs_review(self):
        """Test needs_review property."""
        review = RiskAssessment(
            id="r",
            level=RiskLevel.MEDIUM,
            recommendation="review"
        )
        assert review.needs_review

        modify = RiskAssessment(
            id="r2",
            level=RiskLevel.MEDIUM,
            recommendation="modify"
        )
        assert modify.needs_review

    def test_risk_assessment_highest_risk_factor(self):
        """Test highest_risk_factor property."""
        factors = [
            RiskFactor(id="rf_1", category=RiskCategory.ETHICAL, description="Low", score=0.3),
            RiskFactor(id="rf_2", category=RiskCategory.EMOTIONAL, description="High", score=0.8),
            RiskFactor(id="rf_3", category=RiskCategory.SAFETY, description="Medium", score=0.5),
        ]
        assessment = RiskAssessment(
            id="r",
            level=RiskLevel.HIGH,
            factors=factors
        )

        highest = assessment.highest_risk_factor
        assert highest is not None
        assert highest.score == 0.8
        assert highest.category == RiskCategory.EMOTIONAL

    def test_risk_assessment_no_factors(self):
        """Test highest_risk_factor with no factors."""
        assessment = RiskAssessment(id="r", level=RiskLevel.LOW)
        assert assessment.highest_risk_factor is None

    def test_risk_assessment_get_factors_by_category(self):
        """Test get_factors_by_category method."""
        factors = [
            RiskFactor(id="rf_1", category=RiskCategory.ETHICAL, description="E1", score=0.3),
            RiskFactor(id="rf_2", category=RiskCategory.ETHICAL, description="E2", score=0.5),
            RiskFactor(id="rf_3", category=RiskCategory.SAFETY, description="S1", score=0.4),
        ]
        assessment = RiskAssessment(
            id="r",
            level=RiskLevel.MEDIUM,
            factors=factors
        )

        ethical = assessment.get_factors_by_category(RiskCategory.ETHICAL)
        assert len(ethical) == 2

        safety = assessment.get_factors_by_category(RiskCategory.SAFETY)
        assert len(safety) == 1

        privacy = assessment.get_factors_by_category(RiskCategory.PRIVACY)
        assert len(privacy) == 0

    def test_risk_assessment_has_ethical_concern(self):
        """Test has_ethical_concern method."""
        high_ethical = RiskAssessment(
            id="r",
            level=RiskLevel.HIGH,
            ethical_score=0.7
        )
        assert high_ethical.has_ethical_concern()

        low_ethical = RiskAssessment(
            id="r2",
            level=RiskLevel.LOW,
            ethical_score=0.2
        )
        assert not low_ethical.has_ethical_concern()

    def test_risk_assessment_has_trust_damage(self):
        """Test has_trust_damage method."""
        trust_damage = RiskAssessment(
            id="r",
            level=RiskLevel.HIGH,
            trust_impact=-0.5
        )
        assert trust_damage.has_trust_damage()

        no_damage = RiskAssessment(
            id="r2",
            level=RiskLevel.LOW,
            trust_impact=0.2
        )
        assert not no_damage.has_trust_damage()

    def test_risk_assessment_calculate_weighted_score(self):
        """Test calculate_weighted_score method."""
        assessment = RiskAssessment(
            id="r",
            level=RiskLevel.MEDIUM,
            ethical_score=0.5,
            trust_impact=0.0,  # Neutral (0.5 when normalized)
            structural_impact=0.5
        )
        # Default weights: 0.4, 0.3, 0.3
        # 0.5*0.4 + 0.5*0.3 + 0.5*0.3 = 0.2 + 0.15 + 0.15 = 0.5
        score = assessment.calculate_weighted_score()
        assert abs(score - 0.5) < 0.01

    def test_risk_assessment_create_low_risk(self):
        """Test create_low_risk factory method."""
        assessment = RiskAssessment.create_low_risk(
            message_plan_id="plan_123",
            reasoning="All checks passed"
        )
        assert assessment.level == RiskLevel.LOW
        assert assessment.recommendation == "approve"
        assert assessment.message_plan_id == "plan_123"

    def test_risk_assessment_create_critical_risk(self):
        """Test create_critical_risk factory method."""
        factors = [
            RiskFactor(id="rf_1", category=RiskCategory.SAFETY, description="Dangerous", score=0.9)
        ]
        assessment = RiskAssessment.create_critical_risk(
            factors=factors,
            message_plan_id="plan_456"
        )
        assert assessment.level == RiskLevel.CRITICAL
        assert assessment.recommendation == "reject"
        assert len(assessment.factors) == 1


# ============================================================================
# ID Generation Tests
# ============================================================================

class TestRiskIDGeneration:
    """Risk ID generation function tests."""

    def test_risk_assessment_id_format(self):
        """Test risk assessment ID format."""
        rid = generate_risk_assessment_id()
        assert rid.startswith("risk_")
        assert len(rid) == 17  # "risk_" + 12 hex chars

    def test_risk_assessment_id_uniqueness(self):
        """Test risk assessment ID uniqueness."""
        ids = [generate_risk_assessment_id() for _ in range(100)]
        assert len(ids) == len(set(ids))

    def test_risk_factor_id_format(self):
        """Test risk factor ID format."""
        fid = generate_risk_factor_id()
        assert fid.startswith("rf_")
        assert len(fid) == 15  # "rf_" + 12 hex chars

    def test_risk_factor_id_uniqueness(self):
        """Test risk factor ID uniqueness."""
        ids = [generate_risk_factor_id() for _ in range(100)]
        assert len(ids) == len(set(ids))
