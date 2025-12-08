"""
UEM v2 - Self Module

Benlik modulu - Agent'in kendini tanimlayan, izleyen ve yoneten modulu.

Alt moduller:
- types: Temel veri yapilari (Identity, Value, Need, PersonalGoal, SelfState)
- identity: Kimlik yonetimi (IdentityManager)
- values: Deger sistemi (ValueSystem)
- needs: Ihtiyac yonetimi (NeedManager, Maslow hiyerarsisi)
- goals: Kisisel hedefler (PersonalGoalManager)
- processor: Ana koordinator (SelfProcessor)

Kullanim:
    from core.self import (
        SelfProcessor,
        create_self_processor,
        SelfState,
        Identity,
        Value,
        Need,
        PersonalGoal,
    )

    # Processor olustur
    processor = create_self_processor()

    # Islem calistir
    output = processor.process()

    # Durum bilgisi
    print(output.self_state.summary())
"""

# Types
from .types import (
    # Enums
    IdentityAspect,
    ValueCategory,
    ValuePriority,
    NeedLevel,
    NeedStatus,
    GoalDomain,
    IntegrityStatus,
    NarrativeType,
    # Dataclasses
    Value,
    Need,
    PersonalGoal,
    IdentityTrait,
    Identity,
    NarrativeElement,
    SelfState,
)

# Identity
from .identity import (
    IdentityConfig,
    IdentityManager,
    create_identity_manager,
    create_default_identity,
)

# Goals
from .goals import (
    PersonalGoalConfig,
    PersonalGoalManager,
    create_personal_goal_manager,
)

# Needs
from .needs import (
    NeedConfig,
    NeedManager,
    create_need_manager,
    get_default_needs,
)

# Values
from .values import (
    ValueSystemConfig,
    ValueSystem,
    create_value_system,
    get_default_values,
)

# Processor
from .processor import (
    SelfProcessorConfig,
    SelfOutput,
    SelfProcessor,
    create_self_processor,
    get_self_processor,
)


__all__ = [
    # === TYPES ===
    # Enums
    "IdentityAspect",
    "ValueCategory",
    "ValuePriority",
    "NeedLevel",
    "NeedStatus",
    "GoalDomain",
    "IntegrityStatus",
    "NarrativeType",
    # Dataclasses
    "Value",
    "Need",
    "PersonalGoal",
    "IdentityTrait",
    "Identity",
    "NarrativeElement",
    "SelfState",

    # === IDENTITY ===
    "IdentityConfig",
    "IdentityManager",
    "create_identity_manager",
    "create_default_identity",

    # === GOALS ===
    "PersonalGoalConfig",
    "PersonalGoalManager",
    "create_personal_goal_manager",

    # === NEEDS ===
    "NeedConfig",
    "NeedManager",
    "create_need_manager",
    "get_default_needs",

    # === VALUES ===
    "ValueSystemConfig",
    "ValueSystem",
    "create_value_system",
    "get_default_values",

    # === PROCESSOR ===
    "SelfProcessorConfig",
    "SelfOutput",
    "SelfProcessor",
    "create_self_processor",
    "get_self_processor",
]
