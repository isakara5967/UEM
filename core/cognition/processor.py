"""
UEM v2 - Cognition Processor

Ana biliş işlemcisi - tüm biliş bileşenlerini koordine eder.

Kullanım:
    from core.cognition.processor import CognitionProcessor

    processor = CognitionProcessor()

    # REASON fazı
    reason_output = processor.reason(state, context)

    # EVALUATE fazı
    eval_output = processor.evaluate(state, context)

    # Tam işleme
    result = processor.process(state, context)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
import time

from foundation.state import StateVector, SVField

from .types import (
    Belief, BeliefType,
    Goal, GoalType, GoalPriority, GoalStatus,
    Plan, Intention, IntentionStrength,
    ReasoningResult, ReasoningType,
    SituationAssessment, RiskLevel, OpportunityLevel,
    CognitiveState,
)
from .reasoning import (
    ReasoningEngine, ReasoningConfig,
    get_reasoning_engine,
)
from .evaluation import (
    SituationEvaluator, RiskAssessor, OpportunityAssessor,
    EvaluationConfig, RiskItem, OpportunityItem,
    get_situation_evaluator,
)
from .planning import (
    ActionPlanner, GoalManager,
    PlanningConfig,
    get_action_planner, get_goal_manager,
)


logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class CognitionConfig:
    """Biliş işlemci yapılandırması."""

    # Alt sistem yapılandırmaları
    reasoning: ReasoningConfig = field(default_factory=ReasoningConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    planning: PlanningConfig = field(default_factory=PlanningConfig)

    # Genel ayarlar
    enable_reasoning: bool = True
    enable_evaluation: bool = True
    enable_planning: bool = True

    # Performans
    max_processing_time_ms: float = 500.0

    # Belief oluşturma
    auto_create_beliefs: bool = True
    belief_confidence_decay: float = 0.05  # Cycle başına decay

    # Goal oluşturma
    auto_create_survival_goals: bool = True
    threat_goal_threshold: float = 0.5

    # Logging
    log_reasoning_chain: bool = True


# ============================================================================
# COGNITION OUTPUT
# ============================================================================

@dataclass
class CognitionOutput:
    """Biliş işleme çıktısı."""

    # Akıl yürütme
    reasoning_results: List[ReasoningResult] = field(default_factory=list)
    new_beliefs: List[Belief] = field(default_factory=list)

    # Değerlendirme
    assessment: Optional[SituationAssessment] = None
    risks: List[RiskItem] = field(default_factory=list)
    opportunities: List[OpportunityItem] = field(default_factory=list)

    # Planlama
    active_goal: Optional[Goal] = None
    current_plan: Optional[Plan] = None
    recommended_action: Optional[str] = None

    # Meta
    processing_time_ms: float = 0.0
    cycle_id: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Dict'e çevir."""
        return {
            "reasoning_count": len(self.reasoning_results),
            "new_beliefs_count": len(self.new_beliefs),
            "has_assessment": self.assessment is not None,
            "risk_level": self.assessment.risk_level.value if self.assessment else None,
            "risks_count": len(self.risks),
            "opportunities_count": len(self.opportunities),
            "active_goal": self.active_goal.name if self.active_goal else None,
            "has_plan": self.current_plan is not None,
            "recommended_action": self.recommended_action,
            "processing_time_ms": self.processing_time_ms,
        }


# ============================================================================
# COGNITION PROCESSOR
# ============================================================================

class CognitionProcessor:
    """
    Ana biliş işlemcisi.

    Reasoning, Evaluation ve Planning bileşenlerini koordine eder.
    REASON ve EVALUATE fazlarını işler.
    """

    def __init__(self, config: Optional[CognitionConfig] = None):
        self.config = config or CognitionConfig()

        # Alt sistemler
        self._reasoning_engine = get_reasoning_engine(self.config.reasoning)
        self._evaluator = get_situation_evaluator(self.config.evaluation)
        self._planner = get_action_planner(self.config.planning)
        self._goal_manager = get_goal_manager(self.config.planning)

        # Biliş durumu
        self._cognitive_state = CognitiveState()

        # Metriks
        self._total_cycles = 0
        self._total_reasoning_time_ms = 0.0
        self._total_eval_time_ms = 0.0

    # ========================================================================
    # MAIN PROCESSING
    # ========================================================================

    def process(
        self,
        state: StateVector,
        context: Optional[Dict[str, Any]] = None,
    ) -> CognitionOutput:
        """
        Tam biliş işleme - REASON + EVALUATE.

        Args:
            state: Mevcut StateVector
            context: İşlem context'i

        Returns:
            CognitionOutput - biliş çıktısı
        """
        start_time = time.time()
        context = context or {}
        cycle_id = context.get("cycle_id", self._total_cycles)

        output = CognitionOutput(cycle_id=cycle_id)

        try:
            # 1. REASON fazı
            if self.config.enable_reasoning:
                reason_result = self._do_reasoning(state, context)
                output.reasoning_results = reason_result.get("conclusions", [])
                output.new_beliefs = reason_result.get("new_beliefs", [])

            # 2. EVALUATE fazı
            if self.config.enable_evaluation:
                eval_result = self._do_evaluation(state, context)
                output.assessment = eval_result.get("assessment")
                output.risks = eval_result.get("risks", [])
                output.opportunities = eval_result.get("opportunities", [])

            # 3. PLAN (opsiyonel)
            if self.config.enable_planning:
                plan_result = self._do_planning(state, context, output.assessment)
                output.active_goal = plan_result.get("active_goal")
                output.current_plan = plan_result.get("plan")
                output.recommended_action = plan_result.get("recommended_action")

        except Exception as e:
            logger.error(f"Cognition processing error: {e}")

        # Süre
        output.processing_time_ms = (time.time() - start_time) * 1000
        self._total_cycles += 1

        logger.debug(
            f"Cognition processed: cycle={cycle_id}, "
            f"time={output.processing_time_ms:.1f}ms, "
            f"conclusions={len(output.reasoning_results)}"
        )

        return output

    # ========================================================================
    # REASON PHASE
    # ========================================================================

    def reason(
        self,
        state: StateVector,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        REASON fazı - Akıl yürütme.

        Context'ten gelen algı verilerini analiz eder,
        çıkarımlar yapar, yeni inançlar oluşturur.

        Args:
            state: Mevcut StateVector
            context: İşlem context'i

        Returns:
            Dict with reasoning outputs
        """
        return self._do_reasoning(state, context or {})

    def _do_reasoning(
        self,
        state: StateVector,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """İç reasoning implementasyonu."""
        start_time = time.time()
        result: Dict[str, Any] = {
            "conclusions": [],
            "new_beliefs": [],
            "reasoning_applied": [],
        }

        # 1. Context'ten bilgi çıkar ve beliefs oluştur
        if self.config.auto_create_beliefs:
            new_beliefs = self._extract_beliefs_from_context(state, context)
            for belief in new_beliefs:
                self._cognitive_state.add_belief(belief)
            result["new_beliefs"] = new_beliefs

        # 2. Mevcut beliefs'e decay uygula
        self._apply_belief_decay()

        # 3. Reasoning engine'i çalıştır
        conclusions = self._reasoning_engine.reason(
            self._cognitive_state,
            context,
        )
        result["conclusions"] = conclusions

        # 4. Conclusion'lardan yeni beliefs oluştur
        for conclusion in conclusions:
            if conclusion.confidence > 0.5:
                belief = Belief(
                    subject="inference",
                    predicate=conclusion.conclusion,
                    belief_type=BeliefType.INFERRED,
                    confidence=conclusion.confidence,
                    source=f"reasoning:{conclusion.reasoning_type.value}",
                    cycle_created=context.get("cycle_id", 0),
                )
                self._cognitive_state.add_belief(belief)

        # Reasoning türlerini kaydet
        result["reasoning_applied"] = list(set(
            c.reasoning_type.value for c in conclusions
        ))

        # Süre
        elapsed = (time.time() - start_time) * 1000
        self._total_reasoning_time_ms += elapsed

        if self.config.log_reasoning_chain and conclusions:
            logger.debug(
                f"Reasoning: {len(conclusions)} conclusions, "
                f"types={result['reasoning_applied']}"
            )

        return result

    def _extract_beliefs_from_context(
        self,
        state: StateVector,
        context: Dict[str, Any],
    ) -> List[Belief]:
        """Context'ten beliefs çıkar."""
        beliefs = []
        cycle_id = context.get("cycle_id", 0)

        # Algılanan ajanlardan
        detected_agents = context.get("detected_agents", [])
        for agent in detected_agents:
            agent_id = agent.get("id", "unknown")
            disposition = agent.get("disposition", "unknown")
            threat_level = agent.get("threat_level", "none")

            # Agent belief
            belief = Belief(
                subject=f"agent_{agent_id}",
                predicate=f"disposition:{disposition}, threat:{threat_level}",
                belief_type=BeliefType.FACTUAL,
                confidence=0.8,
                source="perception",
                cycle_created=cycle_id,
                content=agent,
            )
            beliefs.append(belief)

            # Hostile agent belief
            if disposition in ("hostile", "enemy") or threat_level in ("high", "critical"):
                hostile_belief = Belief(
                    subject=f"agent_{agent_id}",
                    predicate="is_hostile",
                    belief_type=BeliefType.INFERRED,
                    confidence=0.85,
                    source="perception",
                    cycle_created=cycle_id,
                )
                beliefs.append(hostile_belief)

        # Threat assessment'tan
        threat_assessment = context.get("threat_assessment")
        if threat_assessment:
            threat_score = getattr(threat_assessment, "overall_score", 0.0)
            if threat_score > 0.3:
                belief = Belief(
                    subject="environment",
                    predicate=f"threat_level:{threat_score:.2f}",
                    belief_type=BeliefType.FACTUAL,
                    confidence=0.9,
                    source="perception",
                    cycle_created=cycle_id,
                )
                beliefs.append(belief)

        # State'ten
        if state.threat > 0.5:
            belief = Belief(
                subject="situation",
                predicate="threat_detected",
                belief_type=BeliefType.FACTUAL,
                confidence=state.threat,
                source="state",
                cycle_created=cycle_id,
            )
            beliefs.append(belief)

        if state.resource < 0.3:
            belief = Belief(
                subject="self",
                predicate="resource_low",
                belief_type=BeliefType.FACTUAL,
                confidence=0.9,
                source="state",
                cycle_created=cycle_id,
            )
            beliefs.append(belief)

        return beliefs

    def _apply_belief_decay(self) -> None:
        """İnançlara zaman decay'i uygula."""
        decay = self.config.belief_confidence_decay

        for belief in list(self._cognitive_state.beliefs.values()):
            # Factual beliefs daha yavaş decay
            if belief.belief_type == BeliefType.FACTUAL:
                belief.update_confidence(-decay * 0.5)
            else:
                belief.update_confidence(-decay)

        # Çok zayıf inançları temizle
        self._cognitive_state.remove_weak_beliefs(0.1)

    # ========================================================================
    # EVALUATE PHASE
    # ========================================================================

    def evaluate(
        self,
        state: StateVector,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        EVALUATE fazı - Durum değerlendirmesi.

        Risk ve fırsat analizi yapar.

        Args:
            state: Mevcut StateVector
            context: İşlem context'i

        Returns:
            Dict with evaluation outputs
        """
        return self._do_evaluation(state, context or {})

    def _do_evaluation(
        self,
        state: StateVector,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """İç evaluation implementasyonu."""
        start_time = time.time()

        # Durumu değerlendir
        assessment = self._evaluator.evaluate(
            state,
            self._cognitive_state,
            context,
        )

        # Cognitive state'e kaydet
        self._cognitive_state.current_assessment = assessment

        # Risk assessor'dan detaylı riskler
        risks = self._evaluator.risk_assessor.assess_risks(
            state, self._cognitive_state, context
        )

        # Opportunity assessor'dan fırsatlar
        opportunities = self._evaluator.opportunity_assessor.assess_opportunities(
            state, self._cognitive_state, context
        )

        # Süre
        elapsed = (time.time() - start_time) * 1000
        self._total_eval_time_ms += elapsed

        logger.debug(
            f"Evaluation: safety={assessment.safety_level:.2f}, "
            f"risk={assessment.risk_level.value}, "
            f"risks={len(risks)}, opportunities={len(opportunities)}"
        )

        return {
            "assessment": assessment,
            "risks": risks,
            "opportunities": opportunities,
            "urgency": assessment.urgency_level,
            "recommended_actions": assessment.recommended_actions,
        }

    # ========================================================================
    # PLANNING
    # ========================================================================

    def _do_planning(
        self,
        state: StateVector,
        context: Dict[str, Any],
        assessment: Optional[SituationAssessment],
    ) -> Dict[str, Any]:
        """Planlama işlemi."""
        result: Dict[str, Any] = {
            "active_goal": None,
            "plan": None,
            "recommended_action": None,
        }

        # 1. Otomatik survival goal oluştur
        if self.config.auto_create_survival_goals:
            if state.threat >= self.config.threat_goal_threshold:
                existing_survival = any(
                    g.goal_type == GoalType.SURVIVAL and g.status == GoalStatus.ACTIVE
                    for g in self._goal_manager._goals.values()
                )
                if not existing_survival:
                    survival_goal = self._goal_manager.create_survival_goal(
                        threat_source="detected_threat",
                        priority=GoalPriority.CRITICAL,
                    )
                    self._goal_manager.add_goal(survival_goal)
                    self._cognitive_state.add_goal(survival_goal)

        # 2. En yüksek öncelikli hedefi al
        active_goal = self._goal_manager.get_highest_priority_goal()

        if active_goal:
            result["active_goal"] = active_goal
            self._cognitive_state.active_goal = active_goal.id

            # 3. Plan oluştur
            plan = self._planner.create_plan(
                active_goal,
                state,
                context,
                assessment,
            )

            if plan:
                result["plan"] = plan
                self._cognitive_state.add_plan(plan)
                self._cognitive_state.activate_plan(plan.id)

                # 4. Önerilen eylem
                next_step = plan.next_step
                if next_step:
                    result["recommended_action"] = next_step.action

        # Assessment'tan önerilen eylem (eğer plan yoksa)
        if not result["recommended_action"] and assessment:
            if assessment.recommended_actions:
                result["recommended_action"] = assessment.recommended_actions[0]

        return result

    # ========================================================================
    # STATE ACCESS
    # ========================================================================

    @property
    def cognitive_state(self) -> CognitiveState:
        """Biliş durumuna erişim."""
        return self._cognitive_state

    def get_beliefs(self) -> Dict[str, Belief]:
        """Tüm inançları getir."""
        return self._cognitive_state.beliefs

    def get_goals(self) -> Dict[str, Goal]:
        """Tüm hedefleri getir."""
        return self._cognitive_state.goals

    def get_active_plan(self) -> Optional[Plan]:
        """Aktif planı getir."""
        return self._cognitive_state.get_active_plan()

    # ========================================================================
    # EXTERNAL INPUT
    # ========================================================================

    def add_belief(self, belief: Belief) -> None:
        """Dışarıdan inanç ekle."""
        self._cognitive_state.add_belief(belief)

    def add_goal(self, goal: Goal) -> str:
        """Dışarıdan hedef ekle."""
        goal_id = self._goal_manager.add_goal(goal)
        if goal_id:
            self._cognitive_state.add_goal(goal)
        return goal_id

    def complete_current_goal(self) -> bool:
        """Mevcut hedefi tamamla."""
        if self._cognitive_state.active_goal:
            return self._goal_manager.complete_goal(
                self._cognitive_state.active_goal
            )
        return False

    # ========================================================================
    # METRICS
    # ========================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """İşlemci metriklerini getir."""
        return {
            "total_cycles": self._total_cycles,
            "total_reasoning_time_ms": self._total_reasoning_time_ms,
            "total_eval_time_ms": self._total_eval_time_ms,
            "avg_reasoning_time_ms": (
                self._total_reasoning_time_ms / max(self._total_cycles, 1)
            ),
            "avg_eval_time_ms": (
                self._total_eval_time_ms / max(self._total_cycles, 1)
            ),
            "beliefs_count": len(self._cognitive_state.beliefs),
            "goals_count": len(self._cognitive_state.goals),
            "active_goals": len(self._goal_manager.get_active_goals()),
            "plans_count": len(self._cognitive_state.plans),
        }

    def reset(self) -> None:
        """İşlemciyi sıfırla."""
        self._cognitive_state = CognitiveState()
        self._total_cycles = 0
        self._total_reasoning_time_ms = 0.0
        self._total_eval_time_ms = 0.0
        logger.info("Cognition processor reset")


# ============================================================================
# FACTORY & SINGLETON
# ============================================================================

_cognition_processor: Optional[CognitionProcessor] = None


def get_cognition_processor(
    config: Optional[CognitionConfig] = None,
) -> CognitionProcessor:
    """Cognition processor singleton'ı al veya oluştur."""
    global _cognition_processor
    if _cognition_processor is None:
        _cognition_processor = CognitionProcessor(config)
    return _cognition_processor


def create_cognition_processor(
    config: Optional[CognitionConfig] = None,
) -> CognitionProcessor:
    """Yeni cognition processor oluştur."""
    return CognitionProcessor(config)
