"""
core/language/dialogue/__init__.py

Dialogue Module - Konuşma eylemleri ve mesaj planlama.
UEM v2 - Thought-to-Speech Pipeline bileşeni.

Components:
- DialogueAct: Konuşma eylemleri (inform, ask, warn, etc.)
- ToneType: Ton türleri (formal, casual, empathic)
- Actor: Konuşmadaki aktörler
- Intention: Niyet temsili
- Risk: Risk bilgisi
- EmotionalState: Duygusal durum
- SituationModel: Algı/Bellek/Bilişim çıktısı
- MessagePlan: Executive karar çıktısı
- SituationBuilder: Perception + Memory + Cognition → SituationModel
- DialogueActSelector: SituationModel → DialogueAct seçimi
- MessagePlanner: ActSelectionResult + SituationModel → MessagePlan
"""

from .types import (
    DialogueAct,
    ToneType,
    Actor,
    Intention,
    Risk,
    Relationship,
    TemporalContext,
    EmotionalState,
    SituationModel,
    MessagePlan,
    generate_situation_id,
    generate_message_plan_id,
)

from .situation_builder import (
    SituationBuilder,
    SituationBuilderConfig,
)

from .act_selector import (
    DialogueActSelector,
    ActSelectorConfig,
    ActSelectionResult,
    ActScore,
    SelectionStrategy,
)

from .message_planner import (
    MessagePlanner,
    MessagePlannerConfig,
    ContentPoint,
    MessageConstraint,
    ConstraintType,
    ConstraintSeverity,
)

__all__ = [
    # Enums
    "DialogueAct",
    "ToneType",
    "SelectionStrategy",
    "ConstraintType",
    "ConstraintSeverity",
    # Dataclasses
    "Actor",
    "Intention",
    "Risk",
    "Relationship",
    "TemporalContext",
    "EmotionalState",
    "SituationModel",
    "MessagePlan",
    "ActScore",
    "ActSelectionResult",
    "ContentPoint",
    "MessageConstraint",
    # Builder
    "SituationBuilder",
    "SituationBuilderConfig",
    # Selector
    "DialogueActSelector",
    "ActSelectorConfig",
    # Planner
    "MessagePlanner",
    "MessagePlannerConfig",
    # Utility functions
    "generate_situation_id",
    "generate_message_plan_id",
]
