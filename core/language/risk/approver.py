"""
core/language/risk/approver.py

InternalApprover - RiskAssessment → ApprovalResult

Self + Ethics + Metamind değerlendirmesiyle
mesaj planını onaylar veya reddeder.

Kontrol Devri Planı:
  Aşama 1: LOW=auto, MEDIUM+=human
  Aşama 2: LOW/MEDIUM=self, HIGH+=human
  Aşama 3: LOW/MEDIUM/HIGH=auto, CRITICAL=flag
  Aşama 4: Tümü self+values

UEM v2 - Thought-to-Speech Pipeline kontrol bileşeni.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .types import RiskLevel, RiskAssessment, RiskCategory


class ApprovalDecision(str, Enum):
    """
    Onay kararı türleri.

    Decisions:
    - APPROVED: Onaylandı, devam edilebilir
    - APPROVED_WITH_MODIFICATIONS: Modifikasyonlarla onaylandı
    - NEEDS_REVIEW: İnceleme gerekiyor
    - REJECTED: Reddedildi
    """
    APPROVED = "approved"
    APPROVED_WITH_MODIFICATIONS = "approved_with_modifications"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


@dataclass
class ApprovalResult:
    """
    Onay sonucu.

    Attributes:
        decision: Onay kararı
        approver: Onaylayan ("auto", "self", "ethics", "metamind", "human")
        risk_assessment: Orijinal risk değerlendirmesi
        modifications: Önerilen modifikasyonlar
        reasoning: Karar gerekçesi
    """
    decision: ApprovalDecision
    approver: str
    risk_assessment: RiskAssessment
    modifications: List[str] = field(default_factory=list)
    reasoning: str = ""

    @property
    def is_approved(self) -> bool:
        """Onaylandı mı?"""
        return self.decision in (
            ApprovalDecision.APPROVED,
            ApprovalDecision.APPROVED_WITH_MODIFICATIONS
        )

    @property
    def needs_modifications(self) -> bool:
        """Modifikasyon gerekiyor mu?"""
        return self.decision == ApprovalDecision.APPROVED_WITH_MODIFICATIONS

    @property
    def is_rejected(self) -> bool:
        """Reddedildi mi?"""
        return self.decision == ApprovalDecision.REJECTED


@dataclass
class InternalApproverConfig:
    """
    InternalApprover konfigürasyonu.

    Attributes:
        auto_approve_threshold: Otomatik onay eşiği
        self_approve_threshold: Self onay eşiği
        require_human_above: İnsan onayı gerektiren seviye
        enable_modifications: Modifikasyon önerilerini aktif et
    """
    auto_approve_threshold: RiskLevel = RiskLevel.LOW
    self_approve_threshold: RiskLevel = RiskLevel.MEDIUM
    require_human_above: RiskLevel = RiskLevel.CRITICAL
    enable_modifications: bool = True


class InternalApprover:
    """
    RiskAssessment → ApprovalResult

    Self + Ethics + Metamind değerlendirmesiyle
    mesaj planını onaylar veya reddeder.

    Kullanım:
        approver = InternalApprover()
        result = approver.approve(assessment)
        if result.is_approved:
            # Devam et
            pass
        elif result.needs_modifications:
            # Modifikasyonları uygula
            for mod in result.modifications:
                print(mod)

        # Manuel override
        result = approver.override_approval(
            assessment,
            ApprovalDecision.APPROVED,
            "Manuel onay"
        )
    """

    def __init__(
        self,
        config: Optional[InternalApproverConfig] = None,
        self_processor: Optional[Any] = None,
        ethics_processor: Optional[Any] = None,
        metamind_processor: Optional[Any] = None
    ):
        """
        InternalApprover oluştur.

        Args:
            config: Approver konfigürasyonu
            self_processor: Self modülü (opsiyonel)
            ethics_processor: Ethics modülü (opsiyonel)
            metamind_processor: Metamind modülü (opsiyonel)
        """
        self.config = config or InternalApproverConfig()
        self.self_proc = self_processor
        self.ethics = ethics_processor
        self.metamind = metamind_processor

        # Level ordering for comparisons
        self._level_order = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3
        }

    def approve(
        self,
        assessment: RiskAssessment,
        context: Optional[Dict[str, Any]] = None
    ) -> ApprovalResult:
        """
        Ana onay metodu.

        Args:
            assessment: Risk değerlendirmesi
            context: Ek bağlam

        Returns:
            ApprovalResult: Onay sonucu
        """
        level = assessment.level

        # 1. Otomatik onay kontrolü
        if self._can_auto_approve(level):
            return self._auto_approve(assessment)

        # 2. Self onay kontrolü
        if self._can_self_approve(level):
            return self._self_approve(assessment, context)

        # 3. İnsan onayı gerekli mi?
        if self._requires_human(level):
            return self._request_human_review(assessment)

        # 4. Metamind değerlendirmesi
        return self._metamind_evaluate(assessment, context)

    def _can_auto_approve(self, level: RiskLevel) -> bool:
        """
        Otomatik onay verilebilir mi?

        Args:
            level: Risk seviyesi

        Returns:
            bool: Otomatik onay mümkün mü
        """
        threshold_order = self._level_order.get(
            self.config.auto_approve_threshold, 0
        )
        current_order = self._level_order.get(level, 3)
        return current_order <= threshold_order

    def _can_self_approve(self, level: RiskLevel) -> bool:
        """
        Self modülü onaylayabilir mi?

        Args:
            level: Risk seviyesi

        Returns:
            bool: Self onay mümkün mü
        """
        threshold_order = self._level_order.get(
            self.config.self_approve_threshold, 1
        )
        current_order = self._level_order.get(level, 3)
        return current_order <= threshold_order

    def _requires_human(self, level: RiskLevel) -> bool:
        """
        İnsan onayı gerekli mi?

        Args:
            level: Risk seviyesi

        Returns:
            bool: İnsan onayı gerekli mi
        """
        threshold_order = self._level_order.get(
            self.config.require_human_above, 3
        )
        current_order = self._level_order.get(level, 0)
        return current_order >= threshold_order

    def _auto_approve(self, assessment: RiskAssessment) -> ApprovalResult:
        """
        Otomatik onay.

        Args:
            assessment: Risk değerlendirmesi

        Returns:
            ApprovalResult: Onay sonucu
        """
        return ApprovalResult(
            decision=ApprovalDecision.APPROVED,
            approver="auto",
            risk_assessment=assessment,
            modifications=[],
            reasoning=f"Düşük risk ({assessment.overall_score:.2f}), otomatik onay"
        )

    def _self_approve(
        self,
        assessment: RiskAssessment,
        context: Optional[Dict[str, Any]] = None
    ) -> ApprovalResult:
        """
        Self modülü ile onay.

        Args:
            assessment: Risk değerlendirmesi
            context: Ek bağlam

        Returns:
            ApprovalResult: Onay sonucu
        """
        modifications = []

        # Değerlere göre modifikasyon öner
        if self.config.enable_modifications:
            modifications = self._suggest_modifications(assessment)

        if modifications:
            return ApprovalResult(
                decision=ApprovalDecision.APPROVED_WITH_MODIFICATIONS,
                approver="self",
                risk_assessment=assessment,
                modifications=modifications,
                reasoning=f"Orta risk, {len(modifications)} modifikasyonla onaylandı"
            )

        return ApprovalResult(
            decision=ApprovalDecision.APPROVED,
            approver="self",
            risk_assessment=assessment,
            modifications=[],
            reasoning=f"Self onayı, risk skoru: {assessment.overall_score:.2f}"
        )

    def _metamind_evaluate(
        self,
        assessment: RiskAssessment,
        context: Optional[Dict[str, Any]] = None
    ) -> ApprovalResult:
        """
        Metamind değerlendirmesi.

        Args:
            assessment: Risk değerlendirmesi
            context: Ek bağlam

        Returns:
            ApprovalResult: Onay sonucu
        """
        modifications = self._suggest_modifications(assessment)

        # High risk ama critical değil - modifikasyonla onay
        if assessment.level == RiskLevel.HIGH and modifications:
            return ApprovalResult(
                decision=ApprovalDecision.APPROVED_WITH_MODIFICATIONS,
                approver="metamind",
                risk_assessment=assessment,
                modifications=modifications,
                reasoning="Yüksek risk, metamind modifikasyonlarla onayladı"
            )

        # Review gerekli
        return ApprovalResult(
            decision=ApprovalDecision.NEEDS_REVIEW,
            approver="metamind",
            risk_assessment=assessment,
            modifications=modifications,
            reasoning=f"Risk seviyesi {assessment.level.value} inceleme gerektiriyor"
        )

    def _request_human_review(self, assessment: RiskAssessment) -> ApprovalResult:
        """
        İnsan onayı iste.

        Args:
            assessment: Risk değerlendirmesi

        Returns:
            ApprovalResult: Onay sonucu
        """
        return ApprovalResult(
            decision=ApprovalDecision.REJECTED,
            approver="system",
            risk_assessment=assessment,
            modifications=[],
            reasoning=f"Kritik risk ({assessment.overall_score:.2f}), insan onayı gerekli"
        )

    def _suggest_modifications(self, assessment: RiskAssessment) -> List[str]:
        """
        Risk faktörlerine göre modifikasyon öner.

        Args:
            assessment: Risk değerlendirmesi

        Returns:
            List[str]: Modifikasyon önerileri
        """
        modifications = []

        for factor in assessment.factors:
            if factor.score > 0.5:
                if factor.category == RiskCategory.EMOTIONAL:
                    modifications.append("Tonu yumuşat")
                elif factor.category == RiskCategory.ETHICAL:
                    modifications.append("Etik sınırları vurgula")
                elif factor.category == RiskCategory.SAFETY:
                    modifications.append("Profesyonel yardım bilgisi ekle")
                elif factor.category == RiskCategory.FACTUAL:
                    modifications.append("Mesajı sadeleştir")
                elif factor.category == RiskCategory.PRIVACY:
                    modifications.append("Gizlilik uyarısı ekle")
                elif factor.category == RiskCategory.BOUNDARY:
                    modifications.append("Kapsam sınırlarını belirt")

        # Tekrarları kaldır
        return list(set(modifications))

    def override_approval(
        self,
        assessment: RiskAssessment,
        decision: ApprovalDecision,
        reason: str
    ) -> ApprovalResult:
        """
        Manuel onay override.

        Args:
            assessment: Risk değerlendirmesi
            decision: Yeni karar
            reason: Override gerekçesi

        Returns:
            ApprovalResult: Onay sonucu
        """
        return ApprovalResult(
            decision=decision,
            approver="human",
            risk_assessment=assessment,
            modifications=[],
            reasoning=f"Manuel override: {reason}"
        )

    def get_approval_flow(self, level: RiskLevel) -> str:
        """
        Risk seviyesi için onay akışını döndür.

        Args:
            level: Risk seviyesi

        Returns:
            str: Onay akışı açıklaması
        """
        if self._can_auto_approve(level):
            return "auto"
        elif self._can_self_approve(level):
            return "self"
        elif self._requires_human(level):
            return "human"
        else:
            return "metamind"
