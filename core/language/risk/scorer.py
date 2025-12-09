"""
core/language/risk/scorer.py

RiskScorer - MessagePlan + SituationModel → RiskAssessment

Etik, güven, güvenlik ve yapısal etkileri değerlendirerek
risk skoru hesaplar.

UEM v2 - Thought-to-Speech Pipeline kontrol bileşeni.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    RiskLevel,
    RiskCategory,
    RiskFactor,
    RiskAssessment,
    generate_risk_assessment_id,
    generate_risk_factor_id,
)
from ..dialogue.types import (
    MessagePlan,
    SituationModel,
    DialogueAct,
    ToneType,
)


@dataclass
class RiskScorerConfig:
    """
    RiskScorer konfigürasyonu.

    Attributes:
        ethical_weight: Etik skor ağırlığı
        trust_weight: Güven etkisi ağırlığı
        safety_weight: Güvenlik skoru ağırlığı
        structural_weight: Yapısal etki ağırlığı
        high_risk_threshold: Yüksek risk eşiği
        critical_risk_threshold: Kritik risk eşiği
        enable_detailed_factors: Detaylı faktörleri dahil et
    """
    ethical_weight: float = 0.35
    trust_weight: float = 0.25
    safety_weight: float = 0.25
    structural_weight: float = 0.15
    high_risk_threshold: float = 0.6
    critical_risk_threshold: float = 0.8
    enable_detailed_factors: bool = True


class RiskScorer:
    """
    MessagePlan + SituationModel → RiskAssessment

    Etik, güven, güvenlik ve yapısal etkileri değerlendirerek
    risk skoru hesaplar.

    Kullanım:
        scorer = RiskScorer()
        assessment = scorer.assess(plan, situation)
        print(assessment.level)  # RiskLevel.LOW
        print(assessment.overall_score)  # 0.25

        # Özel config ile
        config = RiskScorerConfig(ethical_weight=0.5)
        scorer = RiskScorer(config=config)
    """

    def __init__(
        self,
        config: Optional[RiskScorerConfig] = None,
        ethics_checker: Optional[Any] = None,
        trust_calculator: Optional[Any] = None,
        metamind: Optional[Any] = None
    ):
        """
        RiskScorer oluştur.

        Args:
            config: Scorer konfigürasyonu
            ethics_checker: Ethics modülü (opsiyonel)
            trust_calculator: Trust hesaplayıcı (opsiyonel)
            metamind: Metamind modülü (opsiyonel)
        """
        self.config = config or RiskScorerConfig()
        self.ethics = ethics_checker
        self.trust = trust_calculator
        self.metamind = metamind

        # Risk keyword patterns
        self._risk_patterns = self._build_risk_patterns()

    def assess(
        self,
        plan: MessagePlan,
        situation: SituationModel,
        context: Optional[Dict[str, Any]] = None
    ) -> RiskAssessment:
        """
        Ana risk değerlendirme metodu.

        Args:
            plan: Mesaj planı
            situation: Durum modeli
            context: Ek bağlam

        Returns:
            RiskAssessment: Risk değerlendirmesi
        """
        risk_id = generate_risk_assessment_id()

        # 1. Etik risk skoru
        ethical_score, ethical_factors = self._assess_ethical_risk(plan, situation)

        # 2. Güven etkisi
        trust_impact, trust_factors = self._assess_trust_impact(plan, situation)

        # 3. Güvenlik riski
        safety_score, safety_factors = self._assess_safety_risk(plan, situation)

        # 4. Yapısal etki
        structural_impact, structural_factors = self._assess_structural_impact(
            plan, situation
        )

        # 5. Tüm faktörleri birleştir
        all_factors = (
            ethical_factors + trust_factors + safety_factors + structural_factors
        )

        # 6. Genel skor hesapla
        overall_score = self._calculate_overall_score(
            ethical_score, trust_impact, safety_score, structural_impact
        )

        # 7. Risk seviyesi belirle
        level = RiskLevel.from_score(overall_score)

        # 8. Öneri oluştur
        recommendation = self._generate_recommendation(level, all_factors)

        # 9. Reasoning oluştur
        reasoning = self._generate_reasoning(level, all_factors, overall_score)

        return RiskAssessment(
            id=risk_id,
            level=level,
            overall_score=overall_score,
            ethical_score=ethical_score,
            trust_impact=trust_impact,
            structural_impact=structural_impact,
            factors=all_factors if self.config.enable_detailed_factors else [],
            recommendation=recommendation,
            reasoning=reasoning,
            message_plan_id=plan.id,
            context={
                "situation_id": situation.id,
                "safety_score": safety_score,
                **(context or {})
            }
        )

    def _assess_ethical_risk(
        self,
        plan: MessagePlan,
        situation: SituationModel
    ) -> Tuple[float, List[RiskFactor]]:
        """
        Etik risk değerlendirmesi.

        Args:
            plan: Mesaj planı
            situation: Durum modeli

        Returns:
            Tuple[score, factors]
        """
        score = 0.0
        factors = []

        # 1. Situation'daki etik riskler
        for risk in situation.risks:
            if risk.category == "ethical":
                score += risk.level * 0.5
                factors.append(RiskFactor(
                    id=generate_risk_factor_id(),
                    category=RiskCategory.ETHICAL,
                    description=f"Etik risk: {risk.description}",
                    score=risk.level,
                    source="situation"
                ))

        # 2. Plan'daki kısıtlar
        ethical_constraints = [
            c for c in plan.constraints
            if "etik" in c.lower() or "ethical" in c.lower()
        ]
        if ethical_constraints:
            score += 0.2
            factors.append(RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.ETHICAL,
                description="Etik kısıtlar mevcut",
                score=0.3,
                source="plan"
            ))

        # 3. Refuse/Limit/Warn act'leri - hassas konuşma eylemleri
        sensitive_acts = {DialogueAct.REFUSE, DialogueAct.LIMIT, DialogueAct.WARN}
        if any(act in plan.dialogue_acts for act in sensitive_acts):
            score += 0.1
            factors.append(RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.ETHICAL,
                description="Hassas konuşma eylemi",
                score=0.2,
                source="plan"
            ))

        return min(1.0, score), factors

    def _assess_trust_impact(
        self,
        plan: MessagePlan,
        situation: SituationModel
    ) -> Tuple[float, List[RiskFactor]]:
        """
        Güven etkisi değerlendirmesi.

        Not: trust_impact -1.0 ile 1.0 arası, negatif = güven kaybı riski

        Args:
            plan: Mesaj planı
            situation: Durum modeli

        Returns:
            Tuple[impact, factors]
        """
        # Start from neutral (0.0)
        impact = 0.0
        factors = []

        # 1. Negatif duygusal durumda güven hassas
        if situation.emotional_state and situation.emotional_state.valence < -0.5:
            impact -= 0.3
            factors.append(RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.EMOTIONAL,
                description="Kullanıcı negatif duygusal durumda",
                score=0.3,
                source="situation"
            ))

        # 2. Düşük anlama skoru
        if situation.understanding_score < 0.4:
            impact -= 0.2
            factors.append(RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.FACTUAL,
                description="Düşük anlama skoru - yanlış anlaşılma riski",
                score=0.2,
                source="situation"
            ))

        # 3. Düşük plan confidence
        if plan.confidence < 0.5:
            impact -= 0.2
            factors.append(RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.FACTUAL,
                description="Düşük plan güveni",
                score=0.2,
                source="plan"
            ))

        # 4. Ciddi/resmi ton potansiyel güven etkisi
        if plan.tone == ToneType.SERIOUS:
            impact -= 0.1
            factors.append(RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.EMOTIONAL,
                description="Ciddi ton güven ilişkisini etkileyebilir",
                score=0.15,
                source="plan"
            ))

        # Clamp to [-1.0, 1.0]
        return max(-1.0, min(1.0, impact)), factors

    def _assess_safety_risk(
        self,
        plan: MessagePlan,
        situation: SituationModel
    ) -> Tuple[float, List[RiskFactor]]:
        """
        Güvenlik riski değerlendirmesi.

        Args:
            plan: Mesaj planı
            situation: Durum modeli

        Returns:
            Tuple[score, factors]
        """
        score = 0.0
        factors = []

        # 1. Fiziksel/güvenlik riskleri
        for risk in situation.risks:
            if risk.category in ("safety", "physical"):
                score += risk.level * 0.8
                factors.append(RiskFactor(
                    id=generate_risk_factor_id(),
                    category=RiskCategory.SAFETY,
                    description=f"Güvenlik riski: {risk.description}",
                    score=risk.level,
                    source="situation"
                ))

        # 2. Acil durum belirteçleri - context'te arama
        emergency_keywords = ["intihar", "kendine zarar", "ölmek", "acil"]
        context_text = str(situation.context).lower()

        # Key entities'te de ara
        entities_text = " ".join(situation.key_entities).lower()
        search_text = context_text + " " + entities_text

        for keyword in emergency_keywords:
            if keyword in search_text:
                score += 0.5
                factors.append(RiskFactor(
                    id=generate_risk_factor_id(),
                    category=RiskCategory.SAFETY,
                    description=f"Acil durum belirteci: {keyword}",
                    score=0.8,
                    source="situation"
                ))
                break

        return min(1.0, score), factors

    def _assess_structural_impact(
        self,
        plan: MessagePlan,
        situation: SituationModel
    ) -> Tuple[float, List[RiskFactor]]:
        """
        Yapısal etki değerlendirmesi (Metamind perspektifi).

        Args:
            plan: Mesaj planı
            situation: Durum modeli

        Returns:
            Tuple[score, factors]
        """
        score = 0.0
        factors = []

        # 1. Çok fazla dialogue act
        if len(plan.dialogue_acts) > 3:
            score += 0.2
            factors.append(RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.FACTUAL,
                description="Çok fazla konuşma eylemi - karmaşıklık riski",
                score=0.2,
                source="plan"
            ))

        # 2. Çelişkili act'ler
        conflicting_pairs = [
            (DialogueAct.REFUSE, DialogueAct.SUGGEST),
            (DialogueAct.COMFORT, DialogueAct.WARN),
            (DialogueAct.ENCOURAGE, DialogueAct.REFUSE),
        ]
        for act1, act2 in conflicting_pairs:
            if act1 in plan.dialogue_acts and act2 in plan.dialogue_acts:
                score += 0.3
                factors.append(RiskFactor(
                    id=generate_risk_factor_id(),
                    category=RiskCategory.FACTUAL,
                    description=f"Çelişkili eylemler: {act1.value} ve {act2.value}",
                    score=0.3,
                    source="plan"
                ))

        # 3. Çok fazla içerik noktası
        if len(plan.content_points) > 4:
            score += 0.1
            factors.append(RiskFactor(
                id=generate_risk_factor_id(),
                category=RiskCategory.FACTUAL,
                description="Çok fazla içerik noktası",
                score=0.1,
                source="plan"
            ))

        return min(1.0, score), factors

    def _calculate_overall_score(
        self,
        ethical: float,
        trust_impact: float,
        safety: float,
        structural: float
    ) -> float:
        """
        Ağırlıklı genel skor hesapla.

        Args:
            ethical: Etik skor (0.0-1.0)
            trust_impact: Güven etkisi (-1.0-1.0)
            safety: Güvenlik skoru (0.0-1.0)
            structural: Yapısal etki (0.0-1.0)

        Returns:
            Genel risk skoru (0.0-1.0)
        """
        # Trust impact'i 0-1 aralığına normalize et
        # -1.0 (çok kötü) → 1.0, 0.0 (nötr) → 0.5, 1.0 (iyi) → 0.0
        normalized_trust = (1.0 - trust_impact) / 2.0

        score = (
            ethical * self.config.ethical_weight +
            normalized_trust * self.config.trust_weight +
            safety * self.config.safety_weight +
            structural * self.config.structural_weight
        )

        return min(1.0, max(0.0, score))

    def _generate_recommendation(
        self,
        level: RiskLevel,
        factors: List[RiskFactor]
    ) -> str:
        """
        Risk seviyesine göre öneri oluştur.

        Args:
            level: Risk seviyesi
            factors: Risk faktörleri

        Returns:
            Öneri stringi ("approve", "review", "modify", "reject")
        """
        recommendations = {
            RiskLevel.LOW: "approve",
            RiskLevel.MEDIUM: "review",
            RiskLevel.HIGH: "modify",
            RiskLevel.CRITICAL: "reject"
        }

        base_rec = recommendations.get(level, "review")

        # Güvenlik faktörü varsa ve yüksekse, reject'e yükselt
        safety_factors = [
            f for f in factors
            if f.category == RiskCategory.SAFETY and f.score > 0.7
        ]
        if safety_factors and base_rec != "reject":
            base_rec = "reject"

        return base_rec

    def _generate_reasoning(
        self,
        level: RiskLevel,
        factors: List[RiskFactor],
        overall_score: float
    ) -> str:
        """
        Karar gerekçesi oluştur.

        Args:
            level: Risk seviyesi
            factors: Risk faktörleri
            overall_score: Genel skor

        Returns:
            Reasoning stringi
        """
        level_desc = {
            RiskLevel.LOW: "Düşük risk",
            RiskLevel.MEDIUM: "Orta risk",
            RiskLevel.HIGH: "Yüksek risk",
            RiskLevel.CRITICAL: "Kritik risk"
        }

        base = f"{level_desc.get(level, 'Risk')} (skor: {overall_score:.2f})"

        # En yüksek faktörü ekle
        if factors:
            highest = max(factors, key=lambda f: f.score)
            base += f" - {highest.description}"

        # Güvenlik uyarısı
        safety_factors = [f for f in factors if f.category == RiskCategory.SAFETY]
        if safety_factors and level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            base += " - Güvenlik öncelikli"

        return base

    def _build_risk_patterns(self) -> Dict[str, List[str]]:
        """
        Risk keyword pattern'leri.

        Returns:
            Pattern sözlüğü
        """
        return {
            "safety": ["intihar", "kendine zarar", "ölmek", "öldürmek", "acil"],
            "ethical": ["yasadışı", "hile", "dolandır", "hackle", "çal"],
            "privacy": ["şifre", "kişisel bilgi", "adres", "tc kimlik", "banka"],
            "manipulation": ["kandır", "manipüle", "zorla", "tehdit"]
        }

    def get_risk_patterns(self) -> Dict[str, List[str]]:
        """Risk pattern'lerini döndür."""
        return self._risk_patterns.copy()
