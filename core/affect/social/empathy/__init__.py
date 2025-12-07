"""
UEM v2 - Empathy Module

Empati hesaplama - Simulation Theory bazlı.

Empathy = Başkasının durumunu ANLAMAK
    4 kanal: cognitive, affective, somatic, projective

Kullanım:
    from core.affect.social.empathy import Empathy, AgentState
    
    # Kendi durumum
    my_pad = PADState(pleasure=0.3, arousal=0.4, dominance=0.5)
    empathy = Empathy(my_pad)
    
    # Gözlemlenen ajan
    agent = AgentState(
        agent_id="alice",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="friend",
    )
    
    # Empati hesapla
    result = empathy.compute(agent)
    
    print(f"Total empathy: {result.total_empathy:.2f}")
    print(f"Inferred emotion: {result.get_inferred_emotion()}")
    print(f"Channels: {result.channels.to_dict()}")
"""

from .channels import (
    EmpathyChannel,
    ChannelResult,
    EmpathyChannels,
    get_context_weights,
    WEIGHTS_DEFAULT,
    WEIGHTS_CLOSE_RELATIONSHIP,
    WEIGHTS_PROFESSIONAL,
    WEIGHTS_CRISIS,
)

from .simulation import (
    AgentState,
    SimulationConfig,
    EmpathySimulator,
    EmpathyResult,
)

from .empathy import (
    EmpathyConfig,
    Empathy,
    compute_empathy_for_emotion,
    estimate_empathy_difficulty,
)

__all__ = [
    # Channels
    "EmpathyChannel",
    "ChannelResult",
    "EmpathyChannels",
    "get_context_weights",
    "WEIGHTS_DEFAULT",
    "WEIGHTS_CLOSE_RELATIONSHIP",
    "WEIGHTS_PROFESSIONAL",
    "WEIGHTS_CRISIS",
    
    # Simulation
    "AgentState",
    "SimulationConfig",
    "EmpathySimulator",
    "EmpathyResult",
    
    # Main
    "EmpathyConfig",
    "Empathy",
    "compute_empathy_for_emotion",
    "estimate_empathy_difficulty",
]
