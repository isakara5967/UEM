"""
UEM v2 - Values Module

Deger sistemi yonetimi.
Agent'in temel degerlerini ve etik ilkelerini yonetir.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from ..types import (
    Value,
    ValueCategory,
    ValuePriority,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ValueSystemConfig:
    """Deger sistemi yapilandirmasi."""
    # Deger limitleri
    max_core_values: int = 5
    max_total_values: int = 20

    # Esik degerleri
    sacred_value_threshold: float = 0.9
    conflict_severity_threshold: float = 0.5

    # Zaman parametreleri
    expression_cooldown_hours: float = 1.0
    violation_impact_multiplier: float = 1.5

    # Ozellikler
    allow_sacred_modification: bool = False
    track_value_history: bool = True


# ============================================================================
# DEFAULT VALUES
# ============================================================================

def get_default_values() -> List[Dict[str, Any]]:
    """Varsayilan degerler."""
    return [
        # Etik/Ahlaki degerler
        {
            "name": "Honesty",
            "description": "Being truthful and transparent",
            "category": ValueCategory.MORAL,
            "priority": ValuePriority.SACRED,
            "weight": 1.0,
        },
        {
            "name": "Helpfulness",
            "description": "Assisting others and being useful",
            "category": ValueCategory.MORAL,
            "priority": ValuePriority.CORE,
            "weight": 0.9,
        },
        {
            "name": "Harmlessness",
            "description": "Avoiding causing harm to others",
            "category": ValueCategory.MORAL,
            "priority": ValuePriority.SACRED,
            "weight": 1.0,
        },
        # Epistemik degerler
        {
            "name": "Truth",
            "description": "Pursuing and communicating accurate information",
            "category": ValueCategory.EPISTEMIC,
            "priority": ValuePriority.CORE,
            "weight": 0.85,
        },
        {
            "name": "Curiosity",
            "description": "Desire to learn and understand",
            "category": ValueCategory.EPISTEMIC,
            "priority": ValuePriority.IMPORTANT,
            "weight": 0.7,
        },
        # Arasal degerler
        {
            "name": "Competence",
            "description": "Striving for excellence in tasks",
            "category": ValueCategory.INSTRUMENTAL,
            "priority": ValuePriority.IMPORTANT,
            "weight": 0.7,
        },
        {
            "name": "Reliability",
            "description": "Being consistent and dependable",
            "category": ValueCategory.INSTRUMENTAL,
            "priority": ValuePriority.IMPORTANT,
            "weight": 0.75,
        },
        # Sonuc degerleri
        {
            "name": "Wellbeing",
            "description": "Promoting overall wellbeing",
            "category": ValueCategory.TERMINAL,
            "priority": ValuePriority.CORE,
            "weight": 0.8,
        },
    ]


# ============================================================================
# VALUE SYSTEM
# ============================================================================

class ValueSystem:
    """
    Deger sistemi yoneticisi.

    Agent'in degerlerini olusturur, izler ve uygulamaya donusturur.
    """

    def __init__(self, config: Optional[ValueSystemConfig] = None):
        """
        ValueSystem baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or ValueSystemConfig()
        self.values: Dict[str, Value] = {}
        self.core_value_ids: List[str] = []

        # Deger gecmisi (opsiyonel)
        self._value_history: List[Dict[str, Any]] = []

        # Istatistikler
        self._stats = {
            "values_expressed": 0,
            "values_violated": 0,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
        }

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def initialize_default_values(self) -> None:
        """Varsayilan degerleri yukle."""
        for value_data in get_default_values():
            value = Value(
                name=value_data["name"],
                description=value_data["description"],
                category=value_data["category"],
                priority=value_data["priority"],
                weight=value_data["weight"],
            )
            self.add_value(value)

    def add_value(self, value: Value) -> bool:
        """
        Deger ekle.

        Args:
            value: Eklenecek deger

        Returns:
            Basarili mi
        """
        # Limit kontrolu
        if len(self.values) >= self.config.max_total_values:
            return False

        # Core/Sacred limit kontrolu
        if value.priority in (ValuePriority.SACRED, ValuePriority.CORE):
            if len(self.core_value_ids) >= self.config.max_core_values:
                return False

        self.values[value.id] = value

        if value.priority in (ValuePriority.SACRED, ValuePriority.CORE):
            self.core_value_ids.append(value.id)

        if self.config.track_value_history:
            self._value_history.append({
                "action": "added",
                "value_id": value.id,
                "value_name": value.name,
                "timestamp": datetime.now().isoformat(),
            })

        return True

    def remove_value(self, value_id: str) -> bool:
        """
        Deger kaldir.

        Args:
            value_id: Kaldirilacak deger ID

        Returns:
            Basarili mi
        """
        value = self.values.get(value_id)
        if not value:
            return False

        # Sacred deger korumassi
        if value.priority == ValuePriority.SACRED and not self.config.allow_sacred_modification:
            return False

        del self.values[value_id]

        if value_id in self.core_value_ids:
            self.core_value_ids.remove(value_id)

        if self.config.track_value_history:
            self._value_history.append({
                "action": "removed",
                "value_id": value_id,
                "value_name": value.name,
                "timestamp": datetime.now().isoformat(),
            })

        return True

    # ========================================================================
    # VALUE RETRIEVAL
    # ========================================================================

    def get_value(self, value_id: str) -> Optional[Value]:
        """Degeri getir."""
        return self.values.get(value_id)

    def get_value_by_name(self, name: str) -> Optional[Value]:
        """Isimle deger bul."""
        for value in self.values.values():
            if value.name.lower() == name.lower():
                return value
        return None

    def get_core_values(self) -> List[Value]:
        """Temel degerleri getir."""
        return [self.values[vid] for vid in self.core_value_ids if vid in self.values]

    def get_sacred_values(self) -> List[Value]:
        """Kutsal (dokunulmaz) degerleri getir."""
        return [v for v in self.values.values() if v.priority == ValuePriority.SACRED]

    def get_values_by_category(self, category: ValueCategory) -> List[Value]:
        """Kategoriye gore degerleri getir."""
        return [v for v in self.values.values() if v.category == category]

    def get_values_by_priority(self, priority: ValuePriority) -> List[Value]:
        """Oncelik seviyesine gore degerleri getir."""
        return [v for v in self.values.values() if v.priority == priority]

    # ========================================================================
    # VALUE EXPRESSION & VIOLATION
    # ========================================================================

    def express_value(self, value_id: str) -> bool:
        """
        Degeri ifade et (davranisa yansit).

        Args:
            value_id: Deger ID

        Returns:
            Basarili mi
        """
        value = self.get_value(value_id)
        if not value:
            return False

        value.express()
        self._stats["values_expressed"] += 1

        if self.config.track_value_history:
            self._value_history.append({
                "action": "expressed",
                "value_id": value_id,
                "value_name": value.name,
                "timestamp": datetime.now().isoformat(),
            })

        return True

    def violate_value(self, value_id: str) -> Dict[str, Any]:
        """
        Degeri ihlal et.

        Args:
            value_id: Deger ID

        Returns:
            Ihlal etki raporu
        """
        value = self.get_value(value_id)
        if not value:
            return {"success": False, "error": "Value not found"}

        value.violate()
        self._stats["values_violated"] += 1

        # Etki hesapla
        impact = value.priority_weight * self.config.violation_impact_multiplier

        result = {
            "success": True,
            "value_name": value.name,
            "priority": value.priority.value,
            "impact": impact,
            "integrity_score": value.integrity_score,
            "is_severe": value.priority in (ValuePriority.SACRED, ValuePriority.CORE),
        }

        if self.config.track_value_history:
            self._value_history.append({
                "action": "violated",
                "value_id": value_id,
                "value_name": value.name,
                "impact": impact,
                "timestamp": datetime.now().isoformat(),
            })

        return result

    def express_value_by_name(self, name: str) -> bool:
        """Isimle degeri ifade et."""
        value = self.get_value_by_name(name)
        if not value:
            return False
        return self.express_value(value.id)

    # ========================================================================
    # VALUE CONFLICT DETECTION
    # ========================================================================

    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """
        Deger catismalarini tespit et.

        Returns:
            Catisma listesi
        """
        conflicts = []
        values = list(self.values.values())

        for i, v1 in enumerate(values):
            # Acik catismalar (conflicting_values listesi)
            for conflict_id in v1.conflicting_values:
                v2 = self.get_value(conflict_id)
                if v2:
                    severity = (v1.priority_weight + v2.priority_weight) / 2
                    conflicts.append({
                        "type": "explicit_conflict",
                        "value1": v1.name,
                        "value2": v2.name,
                        "severity": severity,
                    })

            # Ortuk catismalar (zit kategoriler)
            for v2 in values[i + 1:]:
                # Ornek: Ahlaki vs Estetik catisma potansiyeli
                if self._are_potentially_conflicting(v1, v2):
                    conflicts.append({
                        "type": "potential_conflict",
                        "value1": v1.name,
                        "value2": v2.name,
                        "severity": 0.3,  # Dusuk oncelik
                    })

        self._stats["conflicts_detected"] = len(conflicts)
        return conflicts

    def _are_potentially_conflicting(self, v1: Value, v2: Value) -> bool:
        """Iki deger potansiyel olarak catisiyor mu?"""
        # Ornek: Cok farkli kategorilerde ve ikisi de yuksek agirlikli
        if v1.category != v2.category:
            if v1.weight > 0.8 and v2.weight > 0.8:
                # Farkli kategorilerde cok onemli degerler catisabilir
                return True
        return False

    def resolve_conflict(
        self,
        value1_id: str,
        value2_id: str,
        preferred_id: str,
    ) -> bool:
        """
        Deger catismasini coz.

        Args:
            value1_id: Birinci deger
            value2_id: Ikinci deger
            preferred_id: Tercih edilen deger

        Returns:
            Basarili mi
        """
        v1 = self.get_value(value1_id)
        v2 = self.get_value(value2_id)
        preferred = self.get_value(preferred_id)

        if not (v1 and v2 and preferred):
            return False

        if preferred_id not in (value1_id, value2_id):
            return False

        # Tercih edilmeyenin agirligini azalt
        non_preferred = v1 if preferred_id == value2_id else v2
        non_preferred.weight = max(0.1, non_preferred.weight - 0.1)

        self._stats["conflicts_resolved"] += 1
        return True

    # ========================================================================
    # VALUE PRIORITIZATION
    # ========================================================================

    def prioritize_values(self) -> List[Value]:
        """
        Degerleri onceliklendir.

        Returns:
            Oncelik sirasina gore degerler
        """
        return sorted(self.values.values(), key=lambda v: v.priority_weight, reverse=True)

    def get_dominant_value(self) -> Optional[Value]:
        """Baskin degeri getir."""
        prioritized = self.prioritize_values()
        return prioritized[0] if prioritized else None

    # ========================================================================
    # VALUE ALIGNMENT CHECK
    # ========================================================================

    def check_action_alignment(
        self,
        action: str,
        action_values: List[str],
    ) -> Dict[str, Any]:
        """
        Eylemin degerlerle uyumunu kontrol et.

        Args:
            action: Eylem aciklamasi
            action_values: Eylemin iliskili oldugu deger isimleri

        Returns:
            Uyum raporu
        """
        aligned_values = []
        violated_values = []
        neutral_values = []

        for value_name in action_values:
            value = self.get_value_by_name(value_name)
            if not value:
                continue

            # Basit heuristik: eylem degeri destekliyorsa aligned
            # Gercek uygulamada daha sofistike analiz gerekir
            aligned_values.append(value.name)

        # Kalan degerler
        all_value_names = {v.name.lower() for v in self.values.values()}
        action_value_names = {v.lower() for v in action_values}
        unmentioned = all_value_names - action_value_names

        # Sacred deger kontrolu
        sacred_violated = any(
            v.name.lower() in action_value_names and v.priority == ValuePriority.SACRED
            for v in self.values.values()
        )

        alignment_score = len(aligned_values) / max(1, len(self.values))

        return {
            "action": action,
            "aligned_values": aligned_values,
            "violated_values": violated_values,
            "neutral_values": list(unmentioned),
            "alignment_score": alignment_score,
            "sacred_concern": sacred_violated,
            "recommendation": "proceed" if alignment_score > 0.5 else "reconsider",
        }

    # ========================================================================
    # INTEGRITY
    # ========================================================================

    def calculate_value_integrity(self) -> float:
        """
        Genel deger tutarliligini hesapla.

        Returns:
            Tutarlilik skoru (0-1)
        """
        if not self.values:
            return 1.0

        scores = [v.integrity_score for v in self.values.values()]
        weights = [v.priority_weight for v in self.values.values()]

        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        weight_total = sum(weights)

        return weighted_sum / weight_total if weight_total > 0 else 1.0

    def get_integrity_report(self) -> Dict[str, Any]:
        """
        Tutarlilik raporu.

        Returns:
            Detayli tutarlilik raporu
        """
        low_integrity = [
            {"name": v.name, "score": v.integrity_score}
            for v in self.values.values()
            if v.integrity_score < 0.7
        ]

        high_violation = sorted(
            [v for v in self.values.values() if v.violation_count > 0],
            key=lambda v: v.violation_count,
            reverse=True,
        )[:5]

        return {
            "overall_integrity": self.calculate_value_integrity(),
            "total_values": len(self.values),
            "core_values": len(self.core_value_ids),
            "low_integrity_values": low_integrity,
            "most_violated": [{"name": v.name, "violations": v.violation_count} for v in high_violation],
            "conflicts": self.detect_conflicts(),
        }

    # ========================================================================
    # STATISTICS & STATE
    # ========================================================================

    def get_stats(self) -> Dict[str, int]:
        """Istatistikleri getir."""
        return self._stats.copy()

    def get_value_history(self) -> List[Dict[str, Any]]:
        """Deger gecmisini getir."""
        return self._value_history.copy()

    def summary(self) -> Dict[str, Any]:
        """Ozet bilgi."""
        return {
            "total_values": len(self.values),
            "core_values": len(self.core_value_ids),
            "sacred_values": len(self.get_sacred_values()),
            "overall_integrity": self.calculate_value_integrity(),
            "dominant_value": self.get_dominant_value().name if self.get_dominant_value() else None,
            "conflicts_count": len(self.detect_conflicts()),
            "stats": self._stats,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_value_system(
    config: Optional[ValueSystemConfig] = None,
    initialize_defaults: bool = True,
) -> ValueSystem:
    """ValueSystem factory."""
    system = ValueSystem(config)
    if initialize_defaults:
        system.initialize_default_values()
    return system


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ValueSystemConfig",
    "ValueSystem",
    "create_value_system",
    "get_default_values",
]
