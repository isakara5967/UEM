"""
UEM v2 - Phase Handlers

Cognitive Cycle fazları için handler'lar.

Kullanım:
    from engine.handlers import (
        create_sense_handler,
        create_perceive_handler,
        create_retrieve_handler,
        create_feel_handler,
        create_decide_handler,
        create_act_handler,
        register_all_handlers,
    )

    cycle = CognitiveCycle()
    register_all_handlers(cycle)
"""

from .perception import (
    PerceptionConfig,
    SensePhaseHandler,
    PerceivePhaseHandler,
    create_sense_handler,
    create_perceive_handler,
)

from .memory import (
    RetrievePhaseConfig,
    RetrieveHandlerState,
    RetrievePhaseHandler,
    create_retrieve_handler,
)

from .affect import (
    AffectPhaseConfig,
    AffectPhaseState,
    AffectPhaseHandler,
    create_feel_handler,
    simple_feel_handler,
)

from .executive import (
    ExecutiveConfig,
    DecidePhaseHandler,
    ActPhaseHandler,
    create_decide_handler,
    create_act_handler,
    AVAILABLE_ACTIONS,
)


def register_all_handlers(cycle, configs: dict = None):
    """
    Tüm handler'ları cycle'a kaydet.

    Args:
        cycle: CognitiveCycle instance
        configs: {"perception": PerceptionConfig, "memory": RetrievePhaseConfig, ...}
    """
    from engine.phases import Phase

    configs = configs or {}

    # Perception
    perception_config = configs.get("perception")
    cycle.register_handler(Phase.SENSE, create_sense_handler(perception_config))
    cycle.register_handler(Phase.PERCEIVE, create_perceive_handler(perception_config))

    # Memory (RETRIEVE)
    memory_config = configs.get("memory")
    cycle.register_handler(Phase.RETRIEVE, create_retrieve_handler(memory_config))

    # Affect
    affect_config = configs.get("affect")
    cycle.register_handler(Phase.FEEL, create_feel_handler(affect_config))

    # Executive
    executive_config = configs.get("executive")
    cycle.register_handler(Phase.DECIDE, create_decide_handler(executive_config))
    cycle.register_handler(Phase.ACT, create_act_handler())


__all__ = [
    # Perception
    "PerceptionConfig",
    "SensePhaseHandler",
    "PerceivePhaseHandler",
    "create_sense_handler",
    "create_perceive_handler",

    # Memory
    "RetrievePhaseConfig",
    "RetrieveHandlerState",
    "RetrievePhaseHandler",
    "create_retrieve_handler",

    # Affect
    "AffectPhaseConfig",
    "AffectPhaseState",
    "AffectPhaseHandler",
    "create_feel_handler",
    "simple_feel_handler",

    # Executive
    "ExecutiveConfig",
    "DecidePhaseHandler",
    "ActPhaseHandler",
    "create_decide_handler",
    "create_act_handler",
    "AVAILABLE_ACTIONS",

    # Utility
    "register_all_handlers",
]
