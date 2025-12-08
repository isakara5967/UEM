"""
UEM v2 - Cognition Phase Handlers

Cognitive Cycle'ın REASON ve EVALUATE fazları için handler'lar.
Yeni core/cognition modülü ile entegre.

Kullanım:
    from engine.handlers.cognition import (
        create_reason_handler,
        create_evaluate_handler,
    )

    cycle = CognitiveCycle()
    cycle.register_handler(Phase.REASON, create_reason_handler())
    cycle.register_handler(Phase.EVALUATE, create_evaluate_handler())
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from foundation.state import StateVector, SVField
from foundation.types import Context
from engine.phases import Phase, PhaseResult

# Yeni cognition modülü
from core.cognition import (
    CognitionProcessor, CognitionConfig,
    CognitionOutput,
    ReasoningResult, SituationAssessment,
    Belief, Goal, Plan,
    RiskLevel, OpportunityLevel,
    get_cognition_processor,
)


logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class CognitionHandlerConfig:
    """Cognition handler'ları yapılandırması."""

    # Akıl yürütme
    enable_reasoning: bool = True
    min_belief_confidence: float = 0.3
    max_conclusions_per_cycle: int = 10

    # Değerlendirme
    enable_evaluation: bool = True
    critical_threat_threshold: float = 0.8
    high_threat_threshold: float = 0.6

    # Planlama
    enable_planning: bool = True
    auto_create_survival_goals: bool = True
    threat_goal_threshold: float = 0.5

    # StateVector güncellemeleri
    update_state_from_assessment: bool = True

    # Processor kullanımı
    use_cognition_processor: bool = True


# ============================================================================
# REASON PHASE HANDLER
# ============================================================================

class ReasonPhaseHandler:
    """
    REASON fazı handler'ı.

    Algı ve bellek verilerinden akıl yürütme yapar:
    - Deduction: Kesin çıkarımlar
    - Induction: Pattern'lerden genelleme
    - Abduction: En iyi açıklama

    Çıktılar:
    - Yeni inançlar (beliefs)
    - Çıkarımlar (conclusions)
    - Durum hakkında yargılar
    """

    def __init__(
        self,
        config: Optional[CognitionHandlerConfig] = None,
        processor: Optional[CognitionProcessor] = None,
    ):
        self.config = config or CognitionHandlerConfig()

        # Cognition processor
        if processor:
            self.processor = processor
        elif self.config.use_cognition_processor:
            cognition_config = CognitionConfig(
                enable_reasoning=self.config.enable_reasoning,
                enable_evaluation=False,  # EVALUATE fazında yapılacak
                enable_planning=False,    # Ayrı fazda yapılacak
                auto_create_beliefs=True,
            )
            self.processor = get_cognition_processor(cognition_config)
        else:
            self.processor = None

    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """REASON fazını çalıştır."""
        output: Dict[str, Any] = {
            "reasoned": False,
            "conclusions_count": 0,
            "new_beliefs_count": 0,
            "reasoning_types": [],
            "conclusions": [],
        }

        if not self.config.enable_reasoning:
            return PhaseResult(
                phase=phase,
                success=True,
                output=output,
                skipped=True,
            )

        try:
            # Context verilerini hazırla
            reason_context = self._prepare_context(context)

            # Reasoning yap
            if self.processor:
                reason_result = self.processor.reason(state, reason_context)

                output["reasoned"] = True
                output["conclusions"] = reason_result.get("conclusions", [])
                output["conclusions_count"] = len(output["conclusions"])
                output["new_beliefs_count"] = len(reason_result.get("new_beliefs", []))
                output["reasoning_types"] = reason_result.get("reasoning_applied", [])

                # Context'e ekle (EVALUATE için)
                context.metadata["reasoning_results"] = reason_result
                context.metadata["cognitive_state"] = self.processor.cognitive_state

                # Log
                if output["conclusions_count"] > 0:
                    logger.debug(
                        f"Reasoning: {output['conclusions_count']} conclusions, "
                        f"types={output['reasoning_types']}"
                    )
            else:
                # Fallback: basit reasoning
                output = self._simple_reasoning(state, context)

        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            return PhaseResult(
                phase=phase,
                success=False,
                output=output,
                error=str(e),
            )

        return PhaseResult(
            phase=phase,
            success=True,
            output=output,
        )

    def _prepare_context(self, context: Context) -> Dict[str, Any]:
        """Context'i reasoning için hazırla."""
        return {
            "cycle_id": context.cycle_id,
            "detected_agents": context.metadata.get("detected_agents", []),
            "threat_assessment": context.metadata.get("threat_assessment"),
            "perceptual_features": context.metadata.get("perceptual_features"),
            "retrieved_memories": context.metadata.get("retrieved_memories", []),
            "stimulus": context.metadata.get("stimulus"),
        }

    def _simple_reasoning(
        self,
        state: StateVector,
        context: Context,
    ) -> Dict[str, Any]:
        """Basit reasoning (fallback)."""
        output = {
            "reasoned": True,
            "conclusions_count": 0,
            "new_beliefs_count": 0,
            "reasoning_types": ["simple"],
            "conclusions": [],
        }

        # Basit deduction: yüksek tehdit varsa tehlike var
        if state.threat > 0.6:
            output["conclusions"].append({
                "type": "deduction",
                "conclusion": "danger_present",
                "confidence": state.threat,
            })
            output["conclusions_count"] = 1

        # Basit induction: düşük kaynak, dikkatli ol
        if state.resource < 0.3:
            output["conclusions"].append({
                "type": "induction",
                "conclusion": "resource_conservation_needed",
                "confidence": 0.8,
            })
            output["conclusions_count"] += 1

        return output


# ============================================================================
# EVALUATE PHASE HANDLER
# ============================================================================

class EvaluatePhaseHandler:
    """
    EVALUATE fazı handler'ı.

    Mevcut durumu değerlendirir:
    - Risk analizi
    - Fırsat analizi
    - Aciliyet değerlendirmesi
    - Eylem önerileri

    Çıktılar:
    - SituationAssessment
    - Risk listesi
    - Fırsat listesi
    - Önerilen eylemler
    """

    def __init__(
        self,
        config: Optional[CognitionHandlerConfig] = None,
        processor: Optional[CognitionProcessor] = None,
    ):
        self.config = config or CognitionHandlerConfig()

        # Cognition processor
        if processor:
            self.processor = processor
        elif self.config.use_cognition_processor:
            cognition_config = CognitionConfig(
                enable_reasoning=False,   # REASON fazında yapıldı
                enable_evaluation=self.config.enable_evaluation,
                enable_planning=self.config.enable_planning,
                auto_create_survival_goals=self.config.auto_create_survival_goals,
                threat_goal_threshold=self.config.threat_goal_threshold,
            )
            self.processor = get_cognition_processor(cognition_config)
        else:
            self.processor = None

    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """EVALUATE fazını çalıştır."""
        output: Dict[str, Any] = {
            "evaluated": False,
            "safety_level": 0.5,
            "risk_level": "unknown",
            "opportunity_level": "unknown",
            "urgency": 0.0,
            "risks_count": 0,
            "opportunities_count": 0,
            "recommended_actions": [],
            "active_goal": None,
            "has_plan": False,
        }

        if not self.config.enable_evaluation:
            return PhaseResult(
                phase=phase,
                success=True,
                output=output,
                skipped=True,
            )

        try:
            # Context verilerini hazırla
            eval_context = self._prepare_context(context)

            # Evaluation yap
            if self.processor:
                eval_result = self.processor.evaluate(state, eval_context)

                assessment = eval_result.get("assessment")
                if assessment:
                    output["evaluated"] = True
                    output["safety_level"] = assessment.safety_level
                    output["risk_level"] = assessment.risk_level.value
                    output["opportunity_level"] = assessment.opportunity.value
                    output["urgency"] = assessment.urgency_level
                    output["recommended_actions"] = assessment.recommended_actions

                    # Context'e ekle (FEEL ve DECIDE için)
                    context.metadata["situation_assessment"] = assessment

                output["risks_count"] = len(eval_result.get("risks", []))
                output["opportunities_count"] = len(eval_result.get("opportunities", []))

                # Planning sonuçları (eğer enable_planning True ise)
                if self.config.enable_planning:
                    plan_result = self.processor._do_planning(
                        state, eval_context, assessment
                    )
                    if plan_result.get("active_goal"):
                        output["active_goal"] = plan_result["active_goal"].name
                    if plan_result.get("plan"):
                        output["has_plan"] = True
                        context.metadata["current_plan"] = plan_result["plan"]
                    if plan_result.get("recommended_action"):
                        if plan_result["recommended_action"] not in output["recommended_actions"]:
                            output["recommended_actions"].insert(
                                0, plan_result["recommended_action"]
                            )

                # StateVector güncellemeleri
                if self.config.update_state_from_assessment and assessment:
                    self._update_state(state, assessment)

                logger.debug(
                    f"Evaluation: safety={output['safety_level']:.2f}, "
                    f"risk={output['risk_level']}, urgency={output['urgency']:.2f}"
                )
            else:
                # Fallback: basit evaluation
                output = self._simple_evaluation(state, context)

        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return PhaseResult(
                phase=phase,
                success=False,
                output=output,
                error=str(e),
            )

        return PhaseResult(
            phase=phase,
            success=True,
            output=output,
        )

    def _prepare_context(self, context: Context) -> Dict[str, Any]:
        """Context'i evaluation için hazırla."""
        return {
            "cycle_id": context.cycle_id,
            "detected_agents": context.metadata.get("detected_agents", []),
            "threat_assessment": context.metadata.get("threat_assessment"),
            "perceptual_features": context.metadata.get("perceptual_features"),
            "reasoning_results": context.metadata.get("reasoning_results"),
            "cognitive_state": context.metadata.get("cognitive_state"),
            "retrieved_memories": context.metadata.get("retrieved_memories", []),
        }

    def _update_state(
        self,
        state: StateVector,
        assessment: SituationAssessment,
    ) -> None:
        """StateVector'u assessment'a göre güncelle."""
        # Safety'yi wellbeing'e yansıt
        safety_influence = (assessment.safety_level - 0.5) * 0.1
        new_wellbeing = state.wellbeing + safety_influence
        state.wellbeing = max(0.0, min(1.0, new_wellbeing))

        # Urgency'yi arousal'a yansıt
        state.set(SVField.AROUSAL, assessment.urgency_level)

        # Cognitive load
        state.set(SVField.COGNITIVE_LOAD, 0.5 + assessment.urgency_level * 0.3)

    def _simple_evaluation(
        self,
        state: StateVector,
        context: Context,
    ) -> Dict[str, Any]:
        """Basit evaluation (fallback)."""
        output = {
            "evaluated": True,
            "safety_level": 1.0 - state.threat,
            "risk_level": "unknown",
            "opportunity_level": "moderate",
            "urgency": state.threat,
            "risks_count": 0,
            "opportunities_count": 0,
            "recommended_actions": [],
            "active_goal": None,
            "has_plan": False,
        }

        # Risk level
        if state.threat >= 0.8:
            output["risk_level"] = "critical"
            output["recommended_actions"] = ["flee", "defend"]
        elif state.threat >= 0.6:
            output["risk_level"] = "high"
            output["recommended_actions"] = ["prepare_defense", "increase_distance"]
        elif state.threat >= 0.4:
            output["risk_level"] = "moderate"
            output["recommended_actions"] = ["monitor", "prepare_exit"]
        elif state.threat >= 0.2:
            output["risk_level"] = "low"
            output["recommended_actions"] = ["maintain_awareness"]
        else:
            output["risk_level"] = "minimal"
            output["recommended_actions"] = ["continue_activity"]

        return output


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_reason_handler(
    config: Optional[CognitionHandlerConfig] = None,
    processor: Optional[CognitionProcessor] = None,
) -> ReasonPhaseHandler:
    """REASON fazı handler'ı oluştur."""
    return ReasonPhaseHandler(config, processor)


def create_evaluate_handler(
    config: Optional[CognitionHandlerConfig] = None,
    processor: Optional[CognitionProcessor] = None,
) -> EvaluatePhaseHandler:
    """EVALUATE fazı handler'ı oluştur."""
    return EvaluatePhaseHandler(config, processor)


def create_cognition_handlers(
    config: Optional[CognitionHandlerConfig] = None,
) -> Dict[Phase, Any]:
    """
    Tüm cognition handler'larını oluştur.

    Returns:
        {Phase.REASON: handler, Phase.EVALUATE: handler}
    """
    config = config or CognitionHandlerConfig()

    # Aynı processor'ı paylaş
    processor = get_cognition_processor()

    return {
        Phase.REASON: ReasonPhaseHandler(config, processor),
        Phase.EVALUATE: EvaluatePhaseHandler(config, processor),
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "CognitionHandlerConfig",
    "ReasonPhaseHandler",
    "EvaluatePhaseHandler",
    "create_reason_handler",
    "create_evaluate_handler",
    "create_cognition_handlers",
]
