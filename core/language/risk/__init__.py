"""
core/language/risk/__init__.py

Risk Module - Risk değerlendirme ve onay sistemi.
UEM v2 - Thought-to-Speech Pipeline kontrol mekanizması.

Components:
- RiskLevel: Risk seviyeleri (LOW, MEDIUM, HIGH, CRITICAL)
- RiskCategory: Risk kategorileri
- RiskFactor: Bireysel risk faktörü
- RiskAssessment: Kapsamlı risk değerlendirmesi
"""

from .types import (
    RiskLevel,
    RiskCategory,
    RiskFactor,
    RiskAssessment,
    generate_risk_assessment_id,
)

__all__ = [
    # Enums
    "RiskLevel",
    "RiskCategory",
    # Dataclasses
    "RiskFactor",
    "RiskAssessment",
    # Utility functions
    "generate_risk_assessment_id",
]
