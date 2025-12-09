"""
tests/unit/test_internal_approver.py

InternalApprover testleri - RiskAssessment → ApprovalResult

Test kategorileri:
1. InternalApprover oluşturma
2. Approve metodu
3. Auto approve
4. Self approve
5. Metamind evaluate
6. Human review
7. Modifications
8. Override approval
9. Approval flow
10. Entegrasyon testleri
"""

import pytest

from core.language.risk.approver import (
    InternalApprover,
    InternalApproverConfig,
    ApprovalDecision,
    ApprovalResult,
)
from core.language.risk.types import (
    RiskLevel,
    RiskCategory,
    RiskFactor,
    RiskAssessment,
    generate_risk_assessment_id,
    generate_risk_factor_id,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def default_approver():
    """Varsayılan InternalApprover."""
    return InternalApprover()


@pytest.fixture
def custom_config():
    """Özelleştirilmiş konfigürasyon."""
    return InternalApproverConfig(
        auto_approve_threshold=RiskLevel.MEDIUM,
        self_approve_threshold=RiskLevel.HIGH,
        require_human_above=RiskLevel.CRITICAL,
        enable_modifications=True
    )


@pytest.fixture
def strict_config():
    """Katı konfigürasyon."""
    return InternalApproverConfig(
        auto_approve_threshold=RiskLevel.LOW,
        self_approve_threshold=RiskLevel.LOW,
        require_human_above=RiskLevel.MEDIUM,
        enable_modifications=False
    )


@pytest.fixture
def low_risk_assessment():
    """Düşük riskli değerlendirme."""
    return RiskAssessment(
        id=generate_risk_assessment_id(),
        level=RiskLevel.LOW,
        overall_score=0.15,
        recommendation="approve",
        reasoning="Düşük risk"
    )


@pytest.fixture
def medium_risk_assessment():
    """Orta riskli değerlendirme."""
    return RiskAssessment(
        id=generate_risk_assessment_id(),
        level=RiskLevel.MEDIUM,
        overall_score=0.4,
        recommendation="review",
        reasoning="Orta risk"
    )


@pytest.fixture
def high_risk_assessment():
    """Yüksek riskli değerlendirme."""
    return RiskAssessment(
        id=generate_risk_assessment_id(),
        level=RiskLevel.HIGH,
        overall_score=0.65,
        factors=[
            RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.EMOTIONAL,
                description="Duygusal hassasiyet",
                score=0.6,
                source="situation"
            ),
            RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.FACTUAL,
                description="Doğruluk riski",
                score=0.5,
                source="plan"
            )
        ],
        recommendation="modify",
        reasoning="Yüksek risk"
    )


@pytest.fixture
def critical_risk_assessment():
    """Kritik riskli değerlendirme."""
    return RiskAssessment(
        id=generate_risk_assessment_id(),
        level=RiskLevel.CRITICAL,
        overall_score=0.9,
        factors=[
            RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.SAFETY,
                description="Güvenlik riski",
                score=0.9,
                source="situation"
            )
        ],
        recommendation="reject",
        reasoning="Kritik risk"
    )


@pytest.fixture
def assessment_with_trust_factor():
    """Güven faktörlü değerlendirme."""
    return RiskAssessment(
        id=generate_risk_assessment_id(),
        level=RiskLevel.MEDIUM,
        overall_score=0.45,
        factors=[
            RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.EMOTIONAL,
                description="Güven etkisi",
                score=0.6,
                source="situation"
            )
        ],
        recommendation="review",
        reasoning="Orta risk - güven etkisi"
    )


@pytest.fixture
def assessment_with_ethical_factor():
    """Etik faktörlü değerlendirme."""
    return RiskAssessment(
        id=generate_risk_assessment_id(),
        level=RiskLevel.MEDIUM,
        overall_score=0.5,
        factors=[
            RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.ETHICAL,
                description="Etik risk",
                score=0.7,
                source="situation"
            )
        ],
        recommendation="review",
        reasoning="Orta risk - etik faktör"
    )


@pytest.fixture
def assessment_with_safety_factor():
    """Güvenlik faktörlü değerlendirme."""
    return RiskAssessment(
        id=generate_risk_assessment_id(),
        level=RiskLevel.HIGH,
        overall_score=0.7,
        factors=[
            RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.SAFETY,
                description="Güvenlik riski",
                score=0.8,
                source="situation"
            )
        ],
        recommendation="modify",
        reasoning="Yüksek risk - güvenlik faktörü"
    )


# ============================================================================
# 1. InternalApprover Oluşturma Testleri
# ============================================================================

class TestInternalApproverCreation:
    """InternalApprover oluşturma testleri."""

    def test_create_default_approver(self):
        """Varsayılan approver oluşturma."""
        approver = InternalApprover()
        assert approver is not None
        assert approver.config is not None

    def test_create_with_custom_config(self, custom_config):
        """Özel config ile approver oluşturma."""
        approver = InternalApprover(config=custom_config)
        assert approver.config.auto_approve_threshold == RiskLevel.MEDIUM
        assert approver.config.self_approve_threshold == RiskLevel.HIGH

    def test_create_with_processors(self):
        """Processor'larla approver oluşturma."""
        approver = InternalApprover(
            self_processor="mock_self",
            ethics_processor="mock_ethics",
            metamind_processor="mock_metamind"
        )
        assert approver.self_proc == "mock_self"
        assert approver.ethics == "mock_ethics"
        assert approver.metamind == "mock_metamind"

    def test_default_config_values(self, default_approver):
        """Varsayılan config değerleri."""
        assert default_approver.config.auto_approve_threshold == RiskLevel.LOW
        assert default_approver.config.self_approve_threshold == RiskLevel.MEDIUM
        assert default_approver.config.require_human_above == RiskLevel.CRITICAL
        assert default_approver.config.enable_modifications is True


# ============================================================================
# 2. Approve Metodu Testleri
# ============================================================================

class TestApproveMethod:
    """Approve metodu testleri."""

    def test_approve_returns_result(self, default_approver, low_risk_assessment):
        """Approve ApprovalResult döndürür."""
        result = default_approver.approve(low_risk_assessment)
        assert isinstance(result, ApprovalResult)

    def test_approve_has_decision(self, default_approver, low_risk_assessment):
        """Result'ta decision var."""
        result = default_approver.approve(low_risk_assessment)
        assert isinstance(result.decision, ApprovalDecision)

    def test_approve_has_approver(self, default_approver, low_risk_assessment):
        """Result'ta approver var."""
        result = default_approver.approve(low_risk_assessment)
        assert result.approver in ("auto", "self", "ethics", "metamind", "human", "system")

    def test_approve_has_reasoning(self, default_approver, low_risk_assessment):
        """Result'ta reasoning var."""
        result = default_approver.approve(low_risk_assessment)
        assert len(result.reasoning) > 0

    def test_approve_has_risk_assessment(self, default_approver, low_risk_assessment):
        """Result'ta risk_assessment var."""
        result = default_approver.approve(low_risk_assessment)
        assert result.risk_assessment == low_risk_assessment


# ============================================================================
# 3. Auto Approve Testleri
# ============================================================================

class TestAutoApprove:
    """Otomatik onay testleri."""

    def test_auto_approve_low_risk(self, default_approver, low_risk_assessment):
        """Düşük risk otomatik onay."""
        result = default_approver.approve(low_risk_assessment)
        assert result.decision == ApprovalDecision.APPROVED
        assert result.approver == "auto"

    def test_can_auto_approve_true(self, default_approver):
        """Auto approve mümkün."""
        assert default_approver._can_auto_approve(RiskLevel.LOW) is True

    def test_can_auto_approve_false(self, default_approver):
        """Auto approve mümkün değil."""
        assert default_approver._can_auto_approve(RiskLevel.MEDIUM) is False
        assert default_approver._can_auto_approve(RiskLevel.HIGH) is False
        assert default_approver._can_auto_approve(RiskLevel.CRITICAL) is False

    def test_auto_approve_with_custom_threshold(self, custom_config, medium_risk_assessment):
        """Özel eşik ile otomatik onay."""
        approver = InternalApprover(config=custom_config)
        # custom_config: auto_approve_threshold = MEDIUM
        result = approver.approve(medium_risk_assessment)
        assert result.decision == ApprovalDecision.APPROVED
        assert result.approver == "auto"


# ============================================================================
# 4. Self Approve Testleri
# ============================================================================

class TestSelfApprove:
    """Self onay testleri."""

    def test_self_approve_medium_risk(self, default_approver, medium_risk_assessment):
        """Orta risk self onay."""
        result = default_approver.approve(medium_risk_assessment)
        assert result.approver == "self"

    def test_can_self_approve_true(self, default_approver):
        """Self approve mümkün."""
        assert default_approver._can_self_approve(RiskLevel.LOW) is True
        assert default_approver._can_self_approve(RiskLevel.MEDIUM) is True

    def test_can_self_approve_false(self, default_approver):
        """Self approve mümkün değil."""
        assert default_approver._can_self_approve(RiskLevel.HIGH) is False
        assert default_approver._can_self_approve(RiskLevel.CRITICAL) is False

    def test_self_approve_with_modifications(self, default_approver, assessment_with_trust_factor):
        """Self onay modifikasyonlarla."""
        result = default_approver.approve(assessment_with_trust_factor)
        if result.approver == "self" and len(result.modifications) > 0:
            assert result.decision == ApprovalDecision.APPROVED_WITH_MODIFICATIONS


# ============================================================================
# 5. Metamind Evaluate Testleri
# ============================================================================

class TestMetamindEvaluate:
    """Metamind değerlendirme testleri."""

    def test_metamind_evaluate_high_risk(self, default_approver, high_risk_assessment):
        """Yüksek risk metamind değerlendirmesi."""
        result = default_approver.approve(high_risk_assessment)
        # HIGH risk goes to metamind
        assert result.approver == "metamind"

    def test_metamind_with_modifications(self, default_approver, high_risk_assessment):
        """Metamind modifikasyonlarla."""
        result = default_approver.approve(high_risk_assessment)
        if result.approver == "metamind":
            assert result.decision in (
                ApprovalDecision.APPROVED_WITH_MODIFICATIONS,
                ApprovalDecision.NEEDS_REVIEW
            )

    def test_metamind_needs_review(self, default_approver, high_risk_assessment):
        """Metamind inceleme gerektirir."""
        # Remove all factors to prevent modifications
        high_risk_assessment.factors = []
        result = default_approver.approve(high_risk_assessment)
        if result.approver == "metamind":
            assert result.decision == ApprovalDecision.NEEDS_REVIEW


# ============================================================================
# 6. Human Review Testleri
# ============================================================================

class TestHumanReview:
    """İnsan onayı testleri."""

    def test_reject_critical_risk(self, default_approver, critical_risk_assessment):
        """Kritik risk reddi."""
        result = default_approver.approve(critical_risk_assessment)
        assert result.decision == ApprovalDecision.REJECTED
        assert result.approver == "system"

    def test_requires_human_critical(self, default_approver):
        """Kritik risk insan gerektirir."""
        assert default_approver._requires_human(RiskLevel.CRITICAL) is True

    def test_requires_human_not_critical(self, default_approver):
        """Kritik olmayan insan gerektirmez."""
        assert default_approver._requires_human(RiskLevel.LOW) is False
        assert default_approver._requires_human(RiskLevel.MEDIUM) is False
        assert default_approver._requires_human(RiskLevel.HIGH) is False

    def test_strict_config_requires_human(self, strict_config, medium_risk_assessment):
        """Katı config insan gerektirir."""
        approver = InternalApprover(config=strict_config)
        # strict_config: require_human_above = MEDIUM
        result = approver.approve(medium_risk_assessment)
        assert result.decision == ApprovalDecision.REJECTED


# ============================================================================
# 7. Modifications Testleri
# ============================================================================

class TestModifications:
    """Modifikasyon testleri."""

    def test_suggest_modifications_emotional(self, default_approver, assessment_with_trust_factor):
        """Duygusal faktör modifikasyonu."""
        mods = default_approver._suggest_modifications(assessment_with_trust_factor)
        assert "Tonu yumuşat" in mods

    def test_suggest_modifications_ethical(self, default_approver, assessment_with_ethical_factor):
        """Etik faktör modifikasyonu."""
        mods = default_approver._suggest_modifications(assessment_with_ethical_factor)
        assert "Etik sınırları vurgula" in mods

    def test_suggest_modifications_safety(self, default_approver, assessment_with_safety_factor):
        """Güvenlik faktör modifikasyonu."""
        mods = default_approver._suggest_modifications(assessment_with_safety_factor)
        assert "Profesyonel yardım bilgisi ekle" in mods

    def test_modifications_no_duplicates(self, default_approver):
        """Tekrarsız modifikasyonlar."""
        assessment = RiskAssessment(
            id=generate_risk_assessment_id(),
            level=RiskLevel.HIGH,
            overall_score=0.7,
            factors=[
                RiskFactor(
                    id=generate_risk_factor_id(),
                    category=RiskCategory.EMOTIONAL,
                    description="Faktör 1",
                    score=0.6
                ),
                RiskFactor(
                    id=generate_risk_factor_id(),
                    category=RiskCategory.EMOTIONAL,
                    description="Faktör 2",
                    score=0.7
                )
            ]
        )
        mods = default_approver._suggest_modifications(assessment)
        # Should have only one "Tonu yumuşat"
        assert mods.count("Tonu yumuşat") == 1

    def test_modifications_disabled(self, strict_config, assessment_with_trust_factor):
        """Modifikasyonlar devre dışı."""
        approver = InternalApprover(config=strict_config)
        # strict_config: enable_modifications = False
        # Since this will trigger human review due to require_human_above=MEDIUM
        result = approver.approve(assessment_with_trust_factor)
        # Even if modifications are disabled, the result should still work
        assert isinstance(result, ApprovalResult)


# ============================================================================
# 8. Override Approval Testleri
# ============================================================================

class TestOverrideApproval:
    """Override onay testleri."""

    def test_override_approval(self, default_approver, critical_risk_assessment):
        """Manuel override."""
        result = default_approver.override_approval(
            critical_risk_assessment,
            ApprovalDecision.APPROVED,
            "Yönetici onayı"
        )
        assert result.decision == ApprovalDecision.APPROVED
        assert result.approver == "human"

    def test_override_approval_approved(self, default_approver, high_risk_assessment):
        """Override ile onay."""
        result = default_approver.override_approval(
            high_risk_assessment,
            ApprovalDecision.APPROVED,
            "Test onayı"
        )
        assert result.is_approved is True

    def test_override_approval_rejected(self, default_approver, low_risk_assessment):
        """Override ile red."""
        result = default_approver.override_approval(
            low_risk_assessment,
            ApprovalDecision.REJECTED,
            "Test reddi"
        )
        assert result.is_rejected is True

    def test_override_reasoning(self, default_approver, medium_risk_assessment):
        """Override gerekçesi."""
        reason = "Özel durum değerlendirmesi"
        result = default_approver.override_approval(
            medium_risk_assessment,
            ApprovalDecision.APPROVED,
            reason
        )
        assert reason in result.reasoning


# ============================================================================
# 9. Approval Flow Testleri
# ============================================================================

class TestApprovalFlow:
    """Onay akışı testleri."""

    def test_approval_flow_low(self, default_approver):
        """Düşük risk akışı."""
        flow = default_approver.get_approval_flow(RiskLevel.LOW)
        assert flow == "auto"

    def test_approval_flow_medium(self, default_approver):
        """Orta risk akışı."""
        flow = default_approver.get_approval_flow(RiskLevel.MEDIUM)
        assert flow == "self"

    def test_approval_flow_high(self, default_approver):
        """Yüksek risk akışı."""
        flow = default_approver.get_approval_flow(RiskLevel.HIGH)
        assert flow == "metamind"

    def test_approval_flow_critical(self, default_approver):
        """Kritik risk akışı."""
        flow = default_approver.get_approval_flow(RiskLevel.CRITICAL)
        assert flow == "human"


# ============================================================================
# 10. ApprovalDecision Enum Testleri
# ============================================================================

class TestApprovalDecisionEnum:
    """ApprovalDecision enum testleri."""

    def test_approval_decision_values(self):
        """Enum değerleri."""
        assert ApprovalDecision.APPROVED.value == "approved"
        assert ApprovalDecision.APPROVED_WITH_MODIFICATIONS.value == "approved_with_modifications"
        assert ApprovalDecision.NEEDS_REVIEW.value == "needs_review"
        assert ApprovalDecision.REJECTED.value == "rejected"

    def test_approval_result_is_approved(self, low_risk_assessment):
        """is_approved property."""
        result = ApprovalResult(
            decision=ApprovalDecision.APPROVED,
            approver="auto",
            risk_assessment=low_risk_assessment
        )
        assert result.is_approved is True

    def test_approval_result_needs_modifications(self, medium_risk_assessment):
        """needs_modifications property."""
        result = ApprovalResult(
            decision=ApprovalDecision.APPROVED_WITH_MODIFICATIONS,
            approver="self",
            risk_assessment=medium_risk_assessment,
            modifications=["Test mod"]
        )
        assert result.needs_modifications is True

    def test_approval_result_is_rejected(self, critical_risk_assessment):
        """is_rejected property."""
        result = ApprovalResult(
            decision=ApprovalDecision.REJECTED,
            approver="system",
            risk_assessment=critical_risk_assessment
        )
        assert result.is_rejected is True


# ============================================================================
# 11. Entegrasyon Testleri
# ============================================================================

class TestIntegration:
    """Entegrasyon testleri."""

    def test_full_approval_flow_low(self, default_approver, low_risk_assessment):
        """Tam onay akışı - düşük risk."""
        result = default_approver.approve(low_risk_assessment)
        assert result.is_approved is True
        assert result.approver == "auto"
        assert len(result.modifications) == 0

    def test_full_approval_flow_medium(self, default_approver, assessment_with_trust_factor):
        """Tam onay akışı - orta risk."""
        result = default_approver.approve(assessment_with_trust_factor)
        assert result.approver == "self"
        # May have modifications due to trust factor

    def test_full_approval_flow_high(self, default_approver, high_risk_assessment):
        """Tam onay akışı - yüksek risk."""
        result = default_approver.approve(high_risk_assessment)
        assert result.approver == "metamind"

    def test_full_approval_flow_critical(self, default_approver, critical_risk_assessment):
        """Tam onay akışı - kritik risk."""
        result = default_approver.approve(critical_risk_assessment)
        assert result.is_rejected is True
        assert result.approver == "system"

    def test_config_affects_flow(self, custom_config):
        """Config akışı etkiler."""
        approver = InternalApprover(config=custom_config)

        # With custom config, MEDIUM is auto-approved
        medium_assessment = RiskAssessment(
            id=generate_risk_assessment_id(),
            level=RiskLevel.MEDIUM,
            overall_score=0.4
        )
        result = approver.approve(medium_assessment)
        assert result.approver == "auto"

        # HIGH is self-approved
        high_assessment = RiskAssessment(
            id=generate_risk_assessment_id(),
            level=RiskLevel.HIGH,
            overall_score=0.6
        )
        result = approver.approve(high_assessment)
        assert result.approver == "self"
