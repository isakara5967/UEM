"""
UEM v2 - Sympathy Module

Sempati hesaplama - Empati sonrası duygusal tepki.

Sympathy = KENDİ duygusal tepkim (empatiyle anladıktan sonra)

8 Sempati Türü:
- Prososyal: compassion, empathic_joy, gratitude, empathic_sadness, empathic_anger
- Antisosyal: pity, schadenfreude, envy

Kullanım:
    from core.affect.social.sympathy import Sympathy, RelationshipContext
    from core.affect.social.empathy import Empathy, AgentState
    
    # Önce empati
    empathy = Empathy(my_pad)
    empathy_result = empathy.compute(agent)
    
    # Sonra sempati
    sympathy = Sympathy(my_pad)
    result = sympathy.compute(
        empathy_result,
        relationship=RelationshipContext.friend()
    )
    
    print(f"Sempati: {result.dominant_sympathy}")
    print(f"Eylem: {result.get_action_tendency()}")
    print(f"Prososyal mi: {result.is_prosocial()}")
"""

from .types import (
    SympathyType,
    SympathyResponse,
    SympathyTrigger,
    SYMPATHY_PAD_EFFECTS,
    SYMPATHY_ACTION_TENDENCIES,
    SYMPATHY_TRIGGERS,
    get_sympathy_pad,
    get_action_tendency,
    get_trigger,
)

from .calculator import (
    RelationshipContext,
    SympathyConfig,
    SympathyCalculator,
    SympathyResult,
)

from .sympathy import (
    SympathyModuleConfig,
    Sympathy,
    predict_sympathy,
    get_sympathy_spectrum,
)

__all__ = [
    # Types
    "SympathyType",
    "SympathyResponse",
    "SympathyTrigger",
    "SYMPATHY_PAD_EFFECTS",
    "SYMPATHY_ACTION_TENDENCIES",
    "SYMPATHY_TRIGGERS",
    "get_sympathy_pad",
    "get_action_tendency",
    "get_trigger",
    
    # Calculator
    "RelationshipContext",
    "SympathyConfig",
    "SympathyCalculator",
    "SympathyResult",
    
    # Main
    "SympathyModuleConfig",
    "Sympathy",
    "predict_sympathy",
    "get_sympathy_spectrum",
]
