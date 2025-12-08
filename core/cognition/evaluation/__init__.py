"""
UEM v2 - Evaluation Module

Durum değerlendirme ve risk/fırsat analizi.

Kullanım:
    from core.cognition.evaluation import SituationEvaluator, RiskAssessor

    evaluator = SituationEvaluator()
    assessment = evaluator.evaluate(state, context)

    assessor = RiskAssessor()
    risks = assessor.assess_risks(state, beliefs)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
import time

from foundation.state import StateVector, SVField

from ..types import (
    Belief, Goal, Intention,
    SituationAssessment,
    RiskLevel, OpportunityLevel,
    CognitiveState,
)


logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class EvaluationConfig:
    """Değerlendirme yapılandırması."""

    # Risk eşikleri
    critical_threat_threshold: float = 0.8
    high_threat_threshold: float = 0.6
    moderate_threat_threshold: float = 0.4
    low_threat_threshold: float = 0.2

    # Fırsat eşikleri
    excellent_opportunity_threshold: float = 0.8
    good_opportunity_threshold: float = 0.6
    moderate_opportunity_threshold: float = 0.4

    # Güvenlik faktörleri
    resource_safety_weight: float = 0.3
    threat_safety_weight: float = 0.4
    wellbeing_safety_weight: float = 0.3

    # Aciliyet faktörleri
    threat_urgency_multiplier: float = 2.0
    goal_deadline_weight: float = 0.5

    # Değerlendirme derinliği
    consider_future_cycles: int = 3      # Kaç cycle ileriye bak
    history_window: int = 5              # Kaç cycle geriye bak


# ============================================================================
# RISK ITEM
# ============================================================================

@dataclass
class RiskItem:
    """Tanımlanan bir risk."""
    risk_id: str
    description: str
    level: RiskLevel
    probability: float            # 0-1 olasılık
    impact: float                 # 0-1 etki
    source: str                   # Riskin kaynağı
    mitigations: List[str] = field(default_factory=list)

    @property
    def severity(self) -> float:
        """Risk şiddeti = probability * impact."""
        return self.probability * self.impact


@dataclass
class OpportunityItem:
    """Tanımlanan bir fırsat."""
    opportunity_id: str
    description: str
    level: OpportunityLevel
    probability: float            # 0-1 gerçekleşme olasılığı
    value: float                  # 0-1 potansiyel değer
    source: str                   # Fırsatın kaynağı
    required_actions: List[str] = field(default_factory=list)
    window: Optional[float] = None  # Zaman penceresi (cycle sayısı)

    @property
    def expected_value(self) -> float:
        """Beklenen değer = probability * value."""
        return self.probability * self.value


# ============================================================================
# RISK ASSESSOR
# ============================================================================

class RiskAssessor:
    """
    Risk değerlendirici.

    StateVector ve beliefs'e bakarak potansiyel riskleri tanımlar.
    """

    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config or EvaluationConfig()

    def assess_risks(
        self,
        state: StateVector,
        cognitive_state: Optional[CognitiveState] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[RiskItem]:
        """
        Riskleri değerlendir.

        Args:
            state: Mevcut StateVector
            cognitive_state: Biliş durumu (opsiyonel)
            context: Ek bağlam

        Returns:
            Tanımlanan riskler listesi
        """
        context = context or {}
        risks: List[RiskItem] = []

        # 1. Threat-based risks
        threat_risks = self._assess_threat_risks(state, context)
        risks.extend(threat_risks)

        # 2. Resource-based risks
        resource_risks = self._assess_resource_risks(state, context)
        risks.extend(resource_risks)

        # 3. Wellbeing-based risks
        wellbeing_risks = self._assess_wellbeing_risks(state, context)
        risks.extend(wellbeing_risks)

        # 4. Belief-based risks (eğer cognitive_state varsa)
        if cognitive_state:
            belief_risks = self._assess_belief_risks(cognitive_state, context)
            risks.extend(belief_risks)

        # Riskleri severity'ye göre sırala
        risks.sort(key=lambda r: r.severity, reverse=True)

        logger.debug(f"Assessed {len(risks)} risks, top: {risks[0].level if risks else 'none'}")

        return risks

    def _assess_threat_risks(
        self,
        state: StateVector,
        context: Dict[str, Any],
    ) -> List[RiskItem]:
        """Tehdit kaynaklı riskler."""
        risks = []
        threat = state.threat

        if threat >= self.config.critical_threat_threshold:
            risks.append(RiskItem(
                risk_id="threat_critical",
                description="Critical threat level detected - immediate danger",
                level=RiskLevel.CRITICAL,
                probability=0.9,
                impact=0.95,
                source="threat_level",
                mitigations=["flee", "defend", "seek_help"],
            ))
        elif threat >= self.config.high_threat_threshold:
            risks.append(RiskItem(
                risk_id="threat_high",
                description="High threat level - significant danger present",
                level=RiskLevel.HIGH,
                probability=0.7,
                impact=0.8,
                source="threat_level",
                mitigations=["increase_distance", "prepare_defense", "alert"],
            ))
        elif threat >= self.config.moderate_threat_threshold:
            risks.append(RiskItem(
                risk_id="threat_moderate",
                description="Moderate threat level - caution advised",
                level=RiskLevel.MODERATE,
                probability=0.5,
                impact=0.5,
                source="threat_level",
                mitigations=["monitor", "prepare_exit"],
            ))
        elif threat >= self.config.low_threat_threshold:
            risks.append(RiskItem(
                risk_id="threat_low",
                description="Low threat level - minor concern",
                level=RiskLevel.LOW,
                probability=0.3,
                impact=0.3,
                source="threat_level",
                mitigations=["maintain_awareness"],
            ))

        return risks

    def _assess_resource_risks(
        self,
        state: StateVector,
        context: Dict[str, Any],
    ) -> List[RiskItem]:
        """Kaynak kaynaklı riskler."""
        risks = []
        resource = state.resource

        if resource < 0.1:
            risks.append(RiskItem(
                risk_id="resource_critical",
                description="Critical resource depletion - survival at risk",
                level=RiskLevel.CRITICAL,
                probability=0.95,
                impact=0.9,
                source="resource_level",
                mitigations=["seek_resources_urgently", "conserve_energy"],
            ))
        elif resource < 0.25:
            risks.append(RiskItem(
                risk_id="resource_low",
                description="Low resource level - action capacity limited",
                level=RiskLevel.HIGH,
                probability=0.8,
                impact=0.6,
                source="resource_level",
                mitigations=["seek_resources", "reduce_activity"],
            ))
        elif resource < 0.4:
            risks.append(RiskItem(
                risk_id="resource_moderate",
                description="Moderate resource level - monitoring advised",
                level=RiskLevel.MODERATE,
                probability=0.4,
                impact=0.4,
                source="resource_level",
                mitigations=["plan_resource_acquisition"],
            ))

        return risks

    def _assess_wellbeing_risks(
        self,
        state: StateVector,
        context: Dict[str, Any],
    ) -> List[RiskItem]:
        """Wellbeing kaynaklı riskler."""
        risks = []
        wellbeing = state.wellbeing

        if wellbeing < 0.2:
            risks.append(RiskItem(
                risk_id="wellbeing_critical",
                description="Critical wellbeing level - system stability at risk",
                level=RiskLevel.HIGH,
                probability=0.7,
                impact=0.7,
                source="wellbeing_level",
                mitigations=["seek_restoration", "reduce_stressors"],
            ))
        elif wellbeing < 0.35:
            risks.append(RiskItem(
                risk_id="wellbeing_low",
                description="Low wellbeing - functioning impaired",
                level=RiskLevel.MODERATE,
                probability=0.5,
                impact=0.5,
                source="wellbeing_level",
                mitigations=["rest", "positive_activity"],
            ))

        return risks

    def _assess_belief_risks(
        self,
        cognitive_state: CognitiveState,
        context: Dict[str, Any],
    ) -> List[RiskItem]:
        """İnançlardan kaynaklanan riskler."""
        risks = []

        for belief in cognitive_state.beliefs.values():
            # Tehdit ile ilgili inançlar
            if any(word in belief.predicate.lower()
                   for word in ["hostile", "dangerous", "threat", "enemy"]):
                if belief.confidence > 0.6:
                    risks.append(RiskItem(
                        risk_id=f"belief_risk_{belief.id}",
                        description=f"Belief indicates risk: {belief.subject} - {belief.predicate}",
                        level=RiskLevel.MODERATE if belief.confidence < 0.8 else RiskLevel.HIGH,
                        probability=belief.confidence,
                        impact=0.6,
                        source=f"belief:{belief.id}",
                        mitigations=["verify_belief", "take_precaution"],
                    ))

        return risks

    def get_overall_risk_level(self, risks: List[RiskItem]) -> RiskLevel:
        """Genel risk seviyesini hesapla."""
        if not risks:
            return RiskLevel.MINIMAL

        # En yüksek risk
        max_severity = max(r.severity for r in risks)

        if max_severity >= 0.8:
            return RiskLevel.CRITICAL
        elif max_severity >= 0.6:
            return RiskLevel.HIGH
        elif max_severity >= 0.4:
            return RiskLevel.MODERATE
        elif max_severity >= 0.2:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL


# ============================================================================
# OPPORTUNITY ASSESSOR
# ============================================================================

class OpportunityAssessor:
    """
    Fırsat değerlendirici.

    StateVector ve context'e bakarak potansiyel fırsatları tanımlar.
    """

    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config or EvaluationConfig()

    def assess_opportunities(
        self,
        state: StateVector,
        cognitive_state: Optional[CognitiveState] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[OpportunityItem]:
        """
        Fırsatları değerlendir.

        Args:
            state: Mevcut StateVector
            cognitive_state: Biliş durumu
            context: Ek bağlam

        Returns:
            Tanımlanan fırsatlar listesi
        """
        context = context or {}
        opportunities: List[OpportunityItem] = []

        # 1. Güvenli ortam fırsatları
        if state.threat < 0.2:
            opportunities.append(OpportunityItem(
                opportunity_id="safe_exploration",
                description="Low threat environment - exploration possible",
                level=OpportunityLevel.GOOD,
                probability=0.8,
                value=0.5,
                source="low_threat",
                required_actions=["explore", "gather_information"],
            ))

        # 2. Yüksek kaynak fırsatları
        if state.resource > 0.7:
            opportunities.append(OpportunityItem(
                opportunity_id="resource_investment",
                description="High resources - investment opportunity",
                level=OpportunityLevel.MODERATE,
                probability=0.6,
                value=0.6,
                source="high_resource",
                required_actions=["invest", "expand"],
            ))

        # 3. İyi wellbeing fırsatları
        if state.wellbeing > 0.7:
            opportunities.append(OpportunityItem(
                opportunity_id="optimal_performance",
                description="High wellbeing - optimal performance possible",
                level=OpportunityLevel.GOOD,
                probability=0.75,
                value=0.7,
                source="high_wellbeing",
                required_actions=["tackle_challenges", "learn"],
            ))

        # 4. Context'ten fırsatlar
        detected_agents = context.get("detected_agents", [])
        for agent in detected_agents:
            disposition = agent.get("disposition", "unknown")
            if disposition in ("friendly", "neutral"):
                opportunities.append(OpportunityItem(
                    opportunity_id=f"social_{agent.get('id', 'unknown')}",
                    description=f"Social opportunity with {disposition} agent",
                    level=OpportunityLevel.MODERATE,
                    probability=0.5,
                    value=0.4,
                    source="social_context",
                    required_actions=["approach", "communicate"],
                ))

        # Sırala
        opportunities.sort(key=lambda o: o.expected_value, reverse=True)

        return opportunities

    def get_overall_opportunity_level(
        self,
        opportunities: List[OpportunityItem],
    ) -> OpportunityLevel:
        """Genel fırsat seviyesini hesapla."""
        if not opportunities:
            return OpportunityLevel.NONE

        max_value = max(o.expected_value for o in opportunities)

        if max_value >= 0.7:
            return OpportunityLevel.EXCELLENT
        elif max_value >= 0.5:
            return OpportunityLevel.GOOD
        elif max_value >= 0.3:
            return OpportunityLevel.MODERATE
        elif max_value >= 0.1:
            return OpportunityLevel.LIMITED
        return OpportunityLevel.NONE


# ============================================================================
# SITUATION EVALUATOR
# ============================================================================

class SituationEvaluator:
    """
    Ana durum değerlendirici.

    Risk, fırsat ve genel durumu entegre değerlendirir.
    """

    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config or EvaluationConfig()
        self.risk_assessor = RiskAssessor(config)
        self.opportunity_assessor = OpportunityAssessor(config)

    def evaluate(
        self,
        state: StateVector,
        cognitive_state: Optional[CognitiveState] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SituationAssessment:
        """
        Tam durum değerlendirmesi yap.

        Args:
            state: Mevcut StateVector
            cognitive_state: Biliş durumu
            context: Ek bağlam

        Returns:
            SituationAssessment - kapsamlı değerlendirme
        """
        start_time = time.time()
        context = context or {}

        # 1. Risk değerlendirmesi
        risks = self.risk_assessor.assess_risks(state, cognitive_state, context)
        risk_level = self.risk_assessor.get_overall_risk_level(risks)

        # 2. Fırsat değerlendirmesi
        opportunities = self.opportunity_assessor.assess_opportunities(
            state, cognitive_state, context
        )
        opportunity_level = self.opportunity_assessor.get_overall_opportunity_level(
            opportunities
        )

        # 3. Güvenlik seviyesi hesapla
        safety_level = self._calculate_safety(state, risks)

        # 4. Fırsat seviyesi (numeric)
        opportunity_score = self._calculate_opportunity_score(opportunities)

        # 5. Aciliyet hesapla
        urgency = self._calculate_urgency(state, risks, cognitive_state)

        # 6. Önerilen eylemler
        recommended, avoid = self._generate_recommendations(
            risks, opportunities, state
        )

        # 7. Tahminler
        predictions = self._predict_developments(state, risks, opportunities)

        # Confidence hesapla
        confidence = self._calculate_confidence(state, cognitive_state)

        assessment = SituationAssessment(
            safety_level=safety_level,
            opportunity_level=opportunity_score,
            urgency_level=urgency,
            risk_level=risk_level,
            opportunity=opportunity_level,
            identified_risks=[r.description for r in risks[:5]],
            identified_opportunities=[o.description for o in opportunities[:5]],
            recommended_actions=recommended,
            actions_to_avoid=avoid,
            predicted_developments=predictions,
            assessment_time=datetime.now(),
            confidence=confidence,
        )

        elapsed = (time.time() - start_time) * 1000
        logger.debug(
            f"Situation evaluated in {elapsed:.1f}ms: "
            f"safety={safety_level:.2f}, risk={risk_level.value}, "
            f"opportunity={opportunity_level.value}"
        )

        return assessment

    def _calculate_safety(
        self,
        state: StateVector,
        risks: List[RiskItem],
    ) -> float:
        """Güvenlik seviyesi hesapla."""
        cfg = self.config

        # Base safety from state
        resource_safety = state.resource * cfg.resource_safety_weight
        threat_safety = (1 - state.threat) * cfg.threat_safety_weight
        wellbeing_safety = state.wellbeing * cfg.wellbeing_safety_weight

        base_safety = resource_safety + threat_safety + wellbeing_safety

        # Risk penalty
        if risks:
            max_risk_severity = max(r.severity for r in risks)
            risk_penalty = max_risk_severity * 0.3
            base_safety = max(0.0, base_safety - risk_penalty)

        return min(1.0, max(0.0, base_safety))

    def _calculate_opportunity_score(
        self,
        opportunities: List[OpportunityItem],
    ) -> float:
        """Fırsat skorunu hesapla."""
        if not opportunities:
            return 0.3  # Baseline

        # En iyi fırsatın expected value'su
        best = max(o.expected_value for o in opportunities)

        # Ortalama ile kombinasyon
        avg = sum(o.expected_value for o in opportunities) / len(opportunities)

        return best * 0.7 + avg * 0.3

    def _calculate_urgency(
        self,
        state: StateVector,
        risks: List[RiskItem],
        cognitive_state: Optional[CognitiveState],
    ) -> float:
        """Aciliyet hesapla."""
        urgency = 0.0

        # Threat urgency
        urgency += state.threat * self.config.threat_urgency_multiplier

        # Critical risk urgency
        critical_risks = [r for r in risks if r.level == RiskLevel.CRITICAL]
        if critical_risks:
            urgency += 0.5

        # Low resource urgency
        if state.resource < 0.2:
            urgency += 0.3

        # Goal deadline urgency
        if cognitive_state:
            for goal in cognitive_state.get_active_goals():
                if goal.deadline:
                    # Basit: deadline yakınsa urgency artır
                    urgency += 0.2 * goal.urgency

        return min(1.0, urgency)

    def _generate_recommendations(
        self,
        risks: List[RiskItem],
        opportunities: List[OpportunityItem],
        state: StateVector,
    ) -> Tuple[List[str], List[str]]:
        """Eylem önerileri oluştur."""
        recommended = []
        avoid = []

        # Risk-based recommendations
        for risk in risks[:3]:
            recommended.extend(risk.mitigations[:2])

        # Opportunity-based recommendations
        for opp in opportunities[:3]:
            recommended.extend(opp.required_actions[:2])

        # State-based recommendations
        if state.threat > 0.7:
            recommended.append("prioritize_safety")
            avoid.append("unnecessary_risks")

        if state.resource < 0.3:
            recommended.append("conserve_resources")
            avoid.append("resource_intensive_actions")

        if state.wellbeing < 0.3:
            recommended.append("seek_restoration")
            avoid.append("high_stress_activities")

        # Deduplicate
        recommended = list(dict.fromkeys(recommended))[:5]
        avoid = list(dict.fromkeys(avoid))[:3]

        return recommended, avoid

    def _predict_developments(
        self,
        state: StateVector,
        risks: List[RiskItem],
        opportunities: List[OpportunityItem],
    ) -> List[str]:
        """Gelecek gelişmeleri tahmin et."""
        predictions = []

        # Threat trajectory
        if state.threat > 0.5:
            predictions.append("threat_may_escalate_without_action")

        # Resource trajectory
        if state.resource < 0.4:
            predictions.append("resources_may_deplete_further")

        # Risk realization
        high_prob_risks = [r for r in risks if r.probability > 0.7]
        for risk in high_prob_risks[:2]:
            predictions.append(f"high_probability: {risk.description}")

        # Opportunity windows
        for opp in opportunities[:2]:
            if opp.window:
                predictions.append(
                    f"opportunity_window: {opp.description} ({opp.window} cycles)"
                )

        return predictions[:5]

    def _calculate_confidence(
        self,
        state: StateVector,
        cognitive_state: Optional[CognitiveState],
    ) -> float:
        """Değerlendirme güvenini hesapla."""
        confidence = 0.6  # Base confidence

        # Daha fazla bilgi = daha yüksek güven
        if cognitive_state:
            belief_count = len(cognitive_state.beliefs)
            confidence += min(0.2, belief_count * 0.02)

        # Low threat = higher confidence in assessment
        confidence += (1 - state.threat) * 0.1

        return min(1.0, confidence)


# ============================================================================
# FACTORY & SINGLETON
# ============================================================================

_situation_evaluator: Optional[SituationEvaluator] = None


def get_situation_evaluator(
    config: Optional[EvaluationConfig] = None,
) -> SituationEvaluator:
    """Situation evaluator singleton'ı al veya oluştur."""
    global _situation_evaluator
    if _situation_evaluator is None:
        _situation_evaluator = SituationEvaluator(config)
    return _situation_evaluator


def create_situation_evaluator(
    config: Optional[EvaluationConfig] = None,
) -> SituationEvaluator:
    """Yeni situation evaluator oluştur."""
    return SituationEvaluator(config)
