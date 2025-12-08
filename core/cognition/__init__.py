"""
UEM v2 - Cognition Module

Bilis modulu - akil yurutme, degerlendirme ve planlama.

LOB 2: COGNITION
- reasoning/   : Mantik, cikarim
- evaluation/  : Degerlendirme
- creativity/  : Yaraticilik, hipotez
- simulation/  : Ic simulasyon

Kullanim:
    from core.cognition import (
        CognitionProcessor, CognitionConfig, CognitionOutput,
        get_cognition_processor,
    )

    processor = get_cognition_processor()
    output = processor.process(state, context)

    # Sadece REASON fazi
    reason_output = processor.reason(state, context)

    # Sadece EVALUATE fazi
    eval_output = processor.evaluate(state, context)
"""

# ============================================================================
# TYPES
# ============================================================================

from .types import (
    # Enums
    BeliefType,
    BeliefStrength,
    GoalType,
    GoalPriority,
    GoalStatus,
    IntentionStrength,
    ReasoningType,
    RiskLevel,
    OpportunityLevel,

    # Data classes
    Belief,
    Goal,
    Intention,
    Plan,
    PlanStep,
    ReasoningResult,
    SituationAssessment,
    CognitiveState,
)

# ============================================================================
# REASONING
# ============================================================================

from .reasoning import (
    ReasoningEngine,
    ReasoningConfig,
    InferenceRule,
    get_reasoning_engine,
    create_reasoning_engine,
)

# ============================================================================
# EVALUATION
# ============================================================================

from .evaluation import (
    SituationEvaluator,
    RiskAssessor,
    OpportunityAssessor,
    EvaluationConfig,
    RiskItem,
    OpportunityItem,
    get_situation_evaluator,
    create_situation_evaluator,
)

# ============================================================================
# PLANNING
# ============================================================================

from .planning import (
    ActionPlanner,
    GoalManager,
    PlanningConfig,
    ActionTemplate,
    get_action_planner,
    get_goal_manager,
    create_action_planner,
    create_goal_manager,
)

# ============================================================================
# PROCESSOR (Main Coordinator)
# ============================================================================

from .processor import (
    CognitionProcessor,
    CognitionConfig,
    CognitionOutput,
    get_cognition_processor,
    create_cognition_processor,
)

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Types - Enums
    "BeliefType",
    "BeliefStrength",
    "GoalType",
    "GoalPriority",
    "GoalStatus",
    "IntentionStrength",
    "ReasoningType",
    "RiskLevel",
    "OpportunityLevel",

    # Types - Data classes
    "Belief",
    "Goal",
    "Intention",
    "Plan",
    "PlanStep",
    "ReasoningResult",
    "SituationAssessment",
    "CognitiveState",

    # Reasoning
    "ReasoningEngine",
    "ReasoningConfig",
    "InferenceRule",
    "get_reasoning_engine",
    "create_reasoning_engine",

    # Evaluation
    "SituationEvaluator",
    "RiskAssessor",
    "OpportunityAssessor",
    "EvaluationConfig",
    "RiskItem",
    "OpportunityItem",
    "get_situation_evaluator",
    "create_situation_evaluator",

    # Planning
    "ActionPlanner",
    "GoalManager",
    "PlanningConfig",
    "ActionTemplate",
    "get_action_planner",
    "get_goal_manager",
    "create_action_planner",
    "create_goal_manager",

    # Processor
    "CognitionProcessor",
    "CognitionConfig",
    "CognitionOutput",
    "get_cognition_processor",
    "create_cognition_processor",
]
