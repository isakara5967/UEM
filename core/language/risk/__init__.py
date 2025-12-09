"""
core/language/risk/__init__.py

Risk Module - Risk değerlendirme ve onay sistemi.
UEM v2 - Thought-to-Speech Pipeline kontrol mekanizması.

Components:
- RiskLevel: Risk seviyeleri (LOW, MEDIUM, HIGH, CRITICAL)
- RiskCategory: Risk kategorileri
- RiskFactor: Bireysel risk faktörü
- RiskAssessment: Kapsamlı risk değerlendirmesi
- RiskScorer: MessagePlan + SituationModel → RiskAssessment
- InternalApprover: RiskAssessment → ApprovalResult
"""

from .types import (
    RiskLevel,
    RiskCategory,
    RiskFactor,
    RiskAssessment,
    generate_risk_assessment_id,
    generate_risk_factor_id,
)
from .scorer import RiskScorer, RiskScorerConfig
from .approver import (
    InternalApprover,
    InternalApproverConfig,
    ApprovalDecision,
    ApprovalResult,
)

__all__ = [
    # Enums
    "RiskLevel",
    "RiskCategory",
    "ApprovalDecision",
    # Dataclasses
    "RiskFactor",
    "RiskAssessment",
    "ApprovalResult",
    # Scorer
    "RiskScorer",
    "RiskScorerConfig",
    # Approver
    "InternalApprover",
    "InternalApproverConfig",
    # Utility functions
    "generate_risk_assessment_id",
    "generate_risk_factor_id",
]
