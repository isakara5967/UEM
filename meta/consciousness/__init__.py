"""
UEM v2 - Consciousness Module

Bilinc modulu - Global Workspace Theory (Baars) implementasyonu.

Alt moduller:
- types: Temel veri yapilari (ConsciousnessLevel, AttentionFocus, Qualia, etc.)
- awareness: Farkindalik yonetimi (AwarenessManager)
- attention: Dikkat kontrolu (AttentionController)
- integration: Global Workspace (yarisma, entegrasyon, yayin)
- processor: Ana koordinator (ConsciousnessProcessor)

Kullanim:
    from meta.consciousness import (
        ConsciousnessProcessor,
        create_consciousness_processor,
        ConsciousnessLevel,
        AttentionFocus,
        BroadcastType,
    )

    # Processor olustur
    processor = create_consciousness_processor()

    # Girdi isle
    output = processor.process(inputs={
        "perception": {"summary": "Threat detected", "threat": 0.8},
        "affect": {"valence": -0.5, "arousal": 0.7},
    })

    # Durum bilgisi
    print(f"Consciousness: {output.consciousness_level}")
    print(f"Focus: {output.current_focus}")
"""

# Types
from .types import (
    # Enums
    ConsciousnessLevel,
    AwarenessType,
    AttentionMode,
    AttentionPriority,
    BroadcastType,
    IntegrationStatus,
    # Dataclasses
    AttentionFocus,
    Qualia,
    WorkspaceContent,
    AwarenessState,
    GlobalWorkspaceState,
    ConsciousExperience,
)

# Awareness
from .awareness import (
    AwarenessConfig,
    AwarenessManager,
    create_awareness_manager,
)

# Attention
from .attention import (
    AttentionConfig,
    AttentionFilter,
    AttentionController,
    create_attention_controller,
)

# Integration (Global Workspace)
from .integration import (
    GlobalWorkspaceConfig,
    BroadcastListener,
    GlobalWorkspace,
    create_global_workspace,
)

# Processor
from .processor import (
    ConsciousnessConfig,
    ConsciousnessOutput,
    ConsciousnessProcessor,
    create_consciousness_processor,
    get_consciousness_processor,
)


__all__ = [
    # === TYPES ===
    # Enums
    "ConsciousnessLevel",
    "AwarenessType",
    "AttentionMode",
    "AttentionPriority",
    "BroadcastType",
    "IntegrationStatus",
    # Dataclasses
    "AttentionFocus",
    "Qualia",
    "WorkspaceContent",
    "AwarenessState",
    "GlobalWorkspaceState",
    "ConsciousExperience",

    # === AWARENESS ===
    "AwarenessConfig",
    "AwarenessManager",
    "create_awareness_manager",

    # === ATTENTION ===
    "AttentionConfig",
    "AttentionFilter",
    "AttentionController",
    "create_attention_controller",

    # === INTEGRATION (Global Workspace) ===
    "GlobalWorkspaceConfig",
    "BroadcastListener",
    "GlobalWorkspace",
    "create_global_workspace",

    # === PROCESSOR ===
    "ConsciousnessConfig",
    "ConsciousnessOutput",
    "ConsciousnessProcessor",
    "create_consciousness_processor",
    "get_consciousness_processor",
]
