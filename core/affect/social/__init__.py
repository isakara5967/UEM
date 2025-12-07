"""
UEM v2 - Social Affect Module

Sosyal duygulanım: Empathy, Sympathy, Trust ve Orchestrator.

Akış:
    Empathy (anlama) → Sympathy (tepki) → Trust (güncelleme)

Kullanım:
    from core.affect.social import SocialAffectOrchestrator, AgentState
    
    orchestrator = SocialAffectOrchestrator(my_pad)
    
    agent = AgentState(
        agent_id="bob",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="friend",
    )
    
    result = orchestrator.process(agent)
    
    print(result.summary())
"""

# Empathy
from .empathy import (
    Empathy,
    EmpathyConfig,
    EmpathyChannel,
    EmpathyChannels,
    ChannelResult,
    AgentState,
    EmpathyResult,
    SimulationConfig,
    EmpathySimulator,
    compute_empathy_for_emotion,
    estimate_empathy_difficulty,
    get_context_weights,
)

# Sympathy
from .sympathy import (
    Sympathy,
    SympathyModuleConfig,
    SympathyConfig,
    SympathyType,
    SympathyResponse,
    SympathyResult,
    RelationshipContext,
    SympathyCalculator,
    predict_sympathy,
    get_sympathy_spectrum,
)

# Trust
from .trust import (
    Trust,
    TrustConfig,
    TrustLevel,
    TrustType,
    TrustDimension,
    TrustComponents,
    TrustEvent,
    TrustProfile,
    TrustManager,
    quick_trust_check,
    calculate_risk_threshold,
)

# Orchestrator
from .orchestrator import (
    SocialAffectOrchestrator,
    SocialAffectResult,
    OrchestratorConfig,
    create_orchestrator,
    process_social_affect,
    SYMPATHY_TRUST_EFFECTS,
    SYMPATHY_TO_TRUST_EVENT,
)

__all__ = [
    # Empathy
    "Empathy",
    "EmpathyConfig",
    "EmpathyChannel",
    "EmpathyChannels",
    "ChannelResult",
    "AgentState",
    "EmpathyResult",
    "SimulationConfig",
    "EmpathySimulator",
    "compute_empathy_for_emotion",
    "estimate_empathy_difficulty",
    "get_context_weights",
    
    # Sympathy
    "Sympathy",
    "SympathyModuleConfig",
    "SympathyConfig",
    "SympathyType",
    "SympathyResponse",
    "SympathyResult",
    "RelationshipContext",
    "SympathyCalculator",
    "predict_sympathy",
    "get_sympathy_spectrum",
    
    # Trust
    "Trust",
    "TrustConfig",
    "TrustLevel",
    "TrustType",
    "TrustDimension",
    "TrustComponents",
    "TrustEvent",
    "TrustProfile",
    "TrustManager",
    "quick_trust_check",
    "calculate_risk_threshold",
    
    # Orchestrator
    "SocialAffectOrchestrator",
    "SocialAffectResult",
    "OrchestratorConfig",
    "create_orchestrator",
    "process_social_affect",
    "SYMPATHY_TRUST_EFFECTS",
    "SYMPATHY_TO_TRUST_EVENT",
]
