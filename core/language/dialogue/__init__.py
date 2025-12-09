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

__all__ = [
    # Enums
    "DialogueAct",
    "ToneType",
    # Dataclasses
    "Actor",
    "Intention",
    "Risk",
    "Relationship",
    "TemporalContext",
    "EmotionalState",
    "SituationModel",
    "MessagePlan",
    # Utility functions
    "generate_situation_id",
    "generate_message_plan_id",
]
