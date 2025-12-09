"""
core/language/pipeline/config.py

PipelineConfig - Thought-to-Speech Pipeline konfigurasyonu.

Tum pipeline bilesenleri icin merkezi yapilandirma.

UEM v2 - Thought-to-Speech Pipeline.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..risk.types import RiskLevel
from ..dialogue.types import ToneType


@dataclass
class SelfCritiqueConfig:
    """
    SelfCritique konfigurasyonu.

    Attributes:
        enabled: Self critique aktif mi?
        min_score_threshold: Minimum basari skoru (0.0-1.0)
        max_revision_attempts: Maksimum revizyon denemesi
        check_tone_match: Ton uyumu kontrolu
        check_content_coverage: Icerik kapsama kontrolu
        check_constraint_violations: Kisit ihlali kontrolu
        auto_revise: Otomatik revizyon aktif mi?
    """
    enabled: bool = True
    min_score_threshold: float = 0.6
    max_revision_attempts: int = 2
    check_tone_match: bool = True
    check_content_coverage: bool = True
    check_constraint_violations: bool = True
    auto_revise: bool = True


@dataclass
class PipelineConfig:
    """
    ThoughtToSpeechPipeline ana konfigurasyonu.

    Attributes:
        enable_self_critique: Self critique asamasini aktif et
        max_revision_attempts: Maksimum revizyon sayisi
        min_approval_level: Minimum onay seviyesi
        fallback_response: Fallback cevap metni
        enable_risk_assessment: Risk degerlendirmesi aktif mi?
        enable_approval_check: Onay kontrolu aktif mi?
        construction_timeout: Construction secimi timeout (ms)
        use_default_constructions: Varsayilan construction'lari kullan
        default_tone: Varsayilan ton
        max_output_length: Maksimum cikti uzunlugu (karakter)
        self_critique_config: Self critique alt konfigurasyonu
        extra: Ek yapilandirmalar
    """
    enable_self_critique: bool = True
    max_revision_attempts: int = 2
    min_approval_level: RiskLevel = RiskLevel.MEDIUM
    fallback_response: str = "Anlayamadim, tekrar eder misiniz?"
    enable_risk_assessment: bool = True
    enable_approval_check: bool = True
    construction_timeout: int = 5000
    use_default_constructions: bool = True
    default_tone: ToneType = ToneType.NEUTRAL
    max_output_length: int = 2000
    self_critique_config: SelfCritiqueConfig = field(
        default_factory=SelfCritiqueConfig
    )
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate config values."""
        if self.max_revision_attempts < 0:
            raise ValueError(
                f"max_revision_attempts must be >= 0, got {self.max_revision_attempts}"
            )

        if self.construction_timeout < 0:
            raise ValueError(
                f"construction_timeout must be >= 0, got {self.construction_timeout}"
            )

        if self.max_output_length < 1:
            raise ValueError(
                f"max_output_length must be >= 1, got {self.max_output_length}"
            )

    @classmethod
    def minimal(cls) -> "PipelineConfig":
        """Minimal konfigürasyon - performans öncelikli."""
        return cls(
            enable_self_critique=False,
            enable_risk_assessment=False,
            enable_approval_check=False,
            max_revision_attempts=0
        )

    @classmethod
    def strict(cls) -> "PipelineConfig":
        """Katı konfigürasyon - güvenlik öncelikli."""
        return cls(
            enable_self_critique=True,
            enable_risk_assessment=True,
            enable_approval_check=True,
            max_revision_attempts=3,
            min_approval_level=RiskLevel.LOW,
            self_critique_config=SelfCritiqueConfig(
                min_score_threshold=0.8,
                max_revision_attempts=3
            )
        )

    @classmethod
    def balanced(cls) -> "PipelineConfig":
        """Dengeli konfigürasyon - varsayılan."""
        return cls()

    def with_self_critique(self, enabled: bool = True) -> "PipelineConfig":
        """Self critique'i açıp kapatmak için."""
        return PipelineConfig(
            enable_self_critique=enabled,
            max_revision_attempts=self.max_revision_attempts,
            min_approval_level=self.min_approval_level,
            fallback_response=self.fallback_response,
            enable_risk_assessment=self.enable_risk_assessment,
            enable_approval_check=self.enable_approval_check,
            construction_timeout=self.construction_timeout,
            use_default_constructions=self.use_default_constructions,
            default_tone=self.default_tone,
            max_output_length=self.max_output_length,
            self_critique_config=self.self_critique_config,
            extra=self.extra.copy()
        )

    def with_risk_level(self, level: RiskLevel) -> "PipelineConfig":
        """Minimum onay seviyesini değiştirmek için."""
        return PipelineConfig(
            enable_self_critique=self.enable_self_critique,
            max_revision_attempts=self.max_revision_attempts,
            min_approval_level=level,
            fallback_response=self.fallback_response,
            enable_risk_assessment=self.enable_risk_assessment,
            enable_approval_check=self.enable_approval_check,
            construction_timeout=self.construction_timeout,
            use_default_constructions=self.use_default_constructions,
            default_tone=self.default_tone,
            max_output_length=self.max_output_length,
            self_critique_config=self.self_critique_config,
            extra=self.extra.copy()
        )
