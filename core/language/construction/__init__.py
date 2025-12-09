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
)

__all__ = [
    # Enums
    "ConstructionLevel",
    "SlotType",
    # Dataclasses
    "Slot",
    "MorphologyRule",
    "ConstructionForm",
    "ConstructionMeaning",
    "Construction",
    # Utility functions
    "generate_construction_id",
    "generate_slot_id",
]
