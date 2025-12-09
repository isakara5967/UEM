"""
core/language/construction/__init__.py

Construction Grammar Module - 3 katmanlı dil yapısı.
UEM v2 - Thought-to-Speech Pipeline dil üretim bileşeni.

Components:
- ConstructionLevel: Katman seviyeleri (DEEP, MIDDLE, SURFACE)
- SlotType: Slot türleri
- Slot: Template slot tanımı
- ConstructionForm: Yapının yüzey formu
- ConstructionMeaning: Yapının anlamı
- Construction: 3 katmanlı dil yapısı
- ConstructionGrammar: 3 katmanlı Construction yönetimi
- ConstructionSelector: MessagePlan → Construction seçimi
- ConstructionRealizer: Construction → Cümle üretimi
- MVCSLoader: Minimum Viable Construction Set yükleyici
- MVCSCategory: MVCS kategorileri

3 Katman:
- DEEP: Konuşma eylemleri, argüman yapıları, semantik roller
- MIDDLE: Cümle iskeletleri, bağlaç yapıları, slot tanımları
- SURFACE: Türkçe morfoloji, ünlü/ünsüz uyumu, ek sıraları
"""

from .types import (
    ConstructionLevel,
    SlotType,
    Slot,
    MorphologyRule,
    ConstructionForm,
    ConstructionMeaning,
    Construction,
    generate_construction_id,
    generate_slot_id,
    generate_morphology_rule_id,
)

from .grammar import (
    ConstructionGrammar,
    ConstructionGrammarConfig,
)

from .selector import (
    ConstructionSelector,
    ConstructionSelectorConfig,
    ConstructionScore,
    SelectionResult,
)

from .realizer import (
    ConstructionRealizer,
    ConstructionRealizerConfig,
    RealizationResult,
)

from .mvcs import (
    MVCSLoader,
    MVCSCategory,
    MVCSConfig,
)

__all__ = [
    # Enums
    "ConstructionLevel",
    "SlotType",
    # Dataclasses - Types
    "Slot",
    "MorphologyRule",
    "ConstructionForm",
    "ConstructionMeaning",
    "Construction",
    # Dataclasses - Results
    "ConstructionScore",
    "SelectionResult",
    "RealizationResult",
    # Grammar
    "ConstructionGrammar",
    "ConstructionGrammarConfig",
    # Selector
    "ConstructionSelector",
    "ConstructionSelectorConfig",
    # Realizer
    "ConstructionRealizer",
    "ConstructionRealizerConfig",
    # Utility functions
    "generate_construction_id",
    "generate_slot_id",
    "generate_morphology_rule_id",
    # MVCS
    "MVCSLoader",
    "MVCSCategory",
    "MVCSConfig",
]
