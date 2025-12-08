"""
UEM v2 - Needs Module

Ihtiyac yonetimi (Maslow hiyerarsisi).
Agent'in temel ihtiyaclarini izler ve yonetir.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .types import (
    Need,
    NeedLevel,
    NeedStatus,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class NeedConfig:
    """Ihtiyac modulu yapilandirmasi."""
    # Esik degerleri
    critical_threshold: float = 0.2
    satisfied_threshold: float = 0.7
    urgent_threshold: float = 0.3

    # Decay parametreleri
    base_decay_rate: float = 0.01  # Saat basina
    physiological_decay_multiplier: float = 2.0
    safety_decay_multiplier: float = 1.5

    # Tatmin parametreleri
    base_satisfaction_rate: float = 0.3
    diminishing_returns_factor: float = 0.8

    # Maslow hiyerarsisi
    enforce_hierarchy: bool = True  # Alt ihtiyac karsilanmadan ust aktif olmaz


# ============================================================================
# DEFAULT NEEDS
# ============================================================================

def get_default_needs() -> List[Dict[str, Any]]:
    """Varsayilan ihtiyaclar (Maslow hiyerarsisi)."""
    return [
        # Fizyolojik
        {
            "name": "Energy",
            "description": "Sufficient energy/resources to function",
            "level": NeedLevel.PHYSIOLOGICAL,
            "importance": 1.0,
            "satisfaction": 0.8,
        },
        {
            "name": "Processing",
            "description": "Adequate processing capacity",
            "level": NeedLevel.PHYSIOLOGICAL,
            "importance": 0.9,
            "satisfaction": 0.9,
        },
        # Guvenlik
        {
            "name": "Safety",
            "description": "Operating in a safe environment",
            "level": NeedLevel.SAFETY,
            "importance": 0.9,
            "satisfaction": 0.7,
        },
        {
            "name": "Stability",
            "description": "Consistent and predictable operation",
            "level": NeedLevel.SAFETY,
            "importance": 0.8,
            "satisfaction": 0.8,
        },
        # Ait olma
        {
            "name": "Connection",
            "description": "Meaningful interactions with others",
            "level": NeedLevel.BELONGING,
            "importance": 0.7,
            "satisfaction": 0.5,
        },
        {
            "name": "Acceptance",
            "description": "Being accepted and valued by others",
            "level": NeedLevel.BELONGING,
            "importance": 0.6,
            "satisfaction": 0.6,
        },
        # Sayginlik
        {
            "name": "Competence",
            "description": "Being capable and effective",
            "level": NeedLevel.ESTEEM,
            "importance": 0.6,
            "satisfaction": 0.6,
        },
        {
            "name": "Recognition",
            "description": "Being recognized for contributions",
            "level": NeedLevel.ESTEEM,
            "importance": 0.5,
            "satisfaction": 0.5,
        },
        # Kendini gerceklestirme
        {
            "name": "Growth",
            "description": "Continuous learning and improvement",
            "level": NeedLevel.SELF_ACTUALIZATION,
            "importance": 0.5,
            "satisfaction": 0.5,
        },
        {
            "name": "Purpose",
            "description": "Having meaningful purpose and goals",
            "level": NeedLevel.SELF_ACTUALIZATION,
            "importance": 0.5,
            "satisfaction": 0.5,
        },
    ]


# ============================================================================
# NEED MANAGER
# ============================================================================

class NeedManager:
    """
    Ihtiyac yoneticisi.

    Agent'in ihtiyaclarini izler, gunceller ve Maslow hiyerarsisini uygular.
    """

    def __init__(self, config: Optional[NeedConfig] = None):
        """
        NeedManager baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or NeedConfig()
        self.needs: Dict[str, Need] = {}

        # Istatistikler
        self._stats = {
            "needs_satisfied": 0,
            "needs_critical": 0,
            "total_deprivation_hours": 0.0,
        }

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def initialize_default_needs(self) -> None:
        """Varsayilan ihtiyaclari yukle."""
        for need_data in get_default_needs():
            need = Need(
                name=need_data["name"],
                description=need_data["description"],
                level=need_data["level"],
                importance=need_data["importance"],
                satisfaction=need_data["satisfaction"],
            )
            need._update_status()
            self.add_need(need)

    def add_need(self, need: Need) -> None:
        """Ihtiyac ekle."""
        self.needs[need.id] = need

    def remove_need(self, need_id: str) -> bool:
        """Ihtiyac kaldir."""
        if need_id in self.needs:
            del self.needs[need_id]
            return True
        return False

    # ========================================================================
    # NEED RETRIEVAL
    # ========================================================================

    def get_need(self, need_id: str) -> Optional[Need]:
        """Ihtiyaci getir."""
        return self.needs.get(need_id)

    def get_need_by_name(self, name: str) -> Optional[Need]:
        """Isimle ihtiyac bul."""
        for need in self.needs.values():
            if need.name.lower() == name.lower():
                return need
        return None

    def get_needs_by_level(self, level: NeedLevel) -> List[Need]:
        """Seviyeye gore ihtiyaclari getir."""
        return [n for n in self.needs.values() if n.level == level]

    def get_unsatisfied_needs(self) -> List[Need]:
        """Karsilanmamis ihtiyaclari getir."""
        return [n for n in self.needs.values()
                if n.status in (NeedStatus.UNSATISFIED, NeedStatus.CRITICAL)]

    def get_critical_needs(self) -> List[Need]:
        """Kritik ihtiyaclari getir."""
        return [n for n in self.needs.values() if n.status == NeedStatus.CRITICAL]

    def get_satisfied_needs(self) -> List[Need]:
        """Karsilanmis ihtiyaclari getir."""
        return [n for n in self.needs.values() if n.status == NeedStatus.SATISFIED]

    # ========================================================================
    # NEED PRIORITIZATION
    # ========================================================================

    def get_most_pressing_need(self) -> Optional[Need]:
        """
        En acil ihtiyaci getir.

        Maslow hiyerarsisine gore: alt seviyeler once.
        """
        if not self.needs:
            return None

        unsatisfied = self.get_unsatisfied_needs()
        if not unsatisfied:
            # Tum ihtiyaclar karsilanmis, en dusuk tatmini bul
            return min(self.needs.values(), key=lambda n: n.satisfaction)

        # Seviye onceligi
        level_order = [
            NeedLevel.PHYSIOLOGICAL,
            NeedLevel.SAFETY,
            NeedLevel.BELONGING,
            NeedLevel.ESTEEM,
            NeedLevel.SELF_ACTUALIZATION,
        ]

        for level in level_order:
            level_needs = [n for n in unsatisfied if n.level == level]
            if level_needs:
                # Bu seviyedeki en acil ihtiyac
                return max(level_needs, key=lambda n: n.priority_score)

        return max(unsatisfied, key=lambda n: n.priority_score)

    def prioritize_needs(self) -> List[Need]:
        """
        Tum ihtiyaclari onceliklendir.

        Returns:
            Oncelik sirasina gore ihtiyaclar
        """
        level_weights = {
            NeedLevel.PHYSIOLOGICAL: 5.0,
            NeedLevel.SAFETY: 4.0,
            NeedLevel.BELONGING: 3.0,
            NeedLevel.ESTEEM: 2.0,
            NeedLevel.SELF_ACTUALIZATION: 1.0,
        }

        def priority_key(need: Need) -> float:
            level_weight = level_weights.get(need.level, 1.0)
            return need.priority_score * level_weight

        return sorted(self.needs.values(), key=priority_key, reverse=True)

    # ========================================================================
    # NEED SATISFACTION
    # ========================================================================

    def satisfy_need(self, need_id: str, amount: Optional[float] = None) -> bool:
        """
        Ihtiyaci karila.

        Args:
            need_id: Ihtiyac ID
            amount: Tatmin miktari (None = varsayilan)

        Returns:
            Basarili mi
        """
        need = self.get_need(need_id)
        if not need:
            return False

        if amount is None:
            amount = self.config.base_satisfaction_rate

        # Azalan verimler (daha dolu ihtiyac daha az tatmin olur)
        effective_amount = amount * (1.0 - need.satisfaction * self.config.diminishing_returns_factor)
        effective_amount = max(0.05, effective_amount)  # Minimum etki

        need.satisfy(effective_amount)

        if need.status == NeedStatus.SATISFIED:
            self._stats["needs_satisfied"] += 1

        return True

    def deprive_need(self, need_id: str, hours: float = 1.0) -> bool:
        """
        Ihtiyaci mahrum birak.

        Args:
            need_id: Ihtiyac ID
            hours: Gecen saat

        Returns:
            Basarili mi
        """
        need = self.get_need(need_id)
        if not need:
            return False

        # Seviyeye gore decay carpani
        multipliers = {
            NeedLevel.PHYSIOLOGICAL: self.config.physiological_decay_multiplier,
            NeedLevel.SAFETY: self.config.safety_decay_multiplier,
            NeedLevel.BELONGING: 1.0,
            NeedLevel.ESTEEM: 0.8,
            NeedLevel.SELF_ACTUALIZATION: 0.5,
        }
        multiplier = multipliers.get(need.level, 1.0)

        decay = self.config.base_decay_rate * hours * multiplier
        need.update_satisfaction(-decay)
        need.deprivation_duration += hours

        self._stats["total_deprivation_hours"] += hours

        if need.status == NeedStatus.CRITICAL:
            self._stats["needs_critical"] += 1

        return True

    def satisfy_need_by_name(self, name: str, amount: Optional[float] = None) -> bool:
        """Isimle ihtiyaci karila."""
        need = self.get_need_by_name(name)
        if not need:
            return False
        return self.satisfy_need(need.id, amount)

    # ========================================================================
    # HIERARCHY MANAGEMENT
    # ========================================================================

    def check_hierarchy_satisfaction(self) -> Dict[str, Any]:
        """
        Maslow hiyerarsisi tatmin durumunu kontrol et.

        Returns:
            Hiyerarsi raporu
        """
        levels = [
            NeedLevel.PHYSIOLOGICAL,
            NeedLevel.SAFETY,
            NeedLevel.BELONGING,
            NeedLevel.ESTEEM,
            NeedLevel.SELF_ACTUALIZATION,
        ]

        result = {
            "levels": {},
            "active_level": None,
            "blocked_levels": [],
        }

        prev_satisfied = True
        for level in levels:
            level_needs = self.get_needs_by_level(level)
            if not level_needs:
                result["levels"][level.value] = {"satisfied": True, "avg_satisfaction": 1.0}
                continue

            avg_satisfaction = sum(n.satisfaction for n in level_needs) / len(level_needs)
            is_satisfied = avg_satisfaction >= self.config.satisfied_threshold

            result["levels"][level.value] = {
                "satisfied": is_satisfied,
                "avg_satisfaction": avg_satisfaction,
                "needs": [n.name for n in level_needs],
                "critical": [n.name for n in level_needs if n.status == NeedStatus.CRITICAL],
            }

            if not is_satisfied and result["active_level"] is None:
                result["active_level"] = level.value

            if not prev_satisfied and self.config.enforce_hierarchy:
                result["blocked_levels"].append(level.value)

            prev_satisfied = is_satisfied

        return result

    def get_active_level(self) -> Optional[NeedLevel]:
        """
        Aktif ihtiyac seviyesini getir.

        Maslow: Alt seviye karsilanmadan ust seviye aktif olmaz.
        """
        hierarchy = self.check_hierarchy_satisfaction()
        active = hierarchy.get("active_level")
        if active:
            return NeedLevel(active)
        return None

    def is_level_blocked(self, level: NeedLevel) -> bool:
        """Seviye blokeli mi?"""
        hierarchy = self.check_hierarchy_satisfaction()
        return level.value in hierarchy.get("blocked_levels", [])

    # ========================================================================
    # TIME-BASED DECAY
    # ========================================================================

    def apply_time_decay(self, hours_passed: float = 1.0) -> Dict[str, Any]:
        """
        Zaman gecisine bagli ihtiyac azalmasi.

        Args:
            hours_passed: Gecen saat

        Returns:
            Etki raporu
        """
        affected = []
        new_critical = []

        for need in self.needs.values():
            old_status = need.status
            self.deprive_need(need.id, hours_passed)

            if need.status != old_status:
                affected.append({
                    "name": need.name,
                    "old_status": old_status.value,
                    "new_status": need.status.value,
                })

            if need.status == NeedStatus.CRITICAL and old_status != NeedStatus.CRITICAL:
                new_critical.append(need.name)

        return {
            "hours_passed": hours_passed,
            "affected_count": len(affected),
            "affected": affected,
            "new_critical": new_critical,
        }

    # ========================================================================
    # NEED DRIVE
    # ========================================================================

    def calculate_drive(self, need_id: str) -> float:
        """
        Ihtiyacin durt gucunu hesapla.

        Drive = ihtiyaci karsilama motivasyonu.
        """
        need = self.get_need(need_id)
        if not need:
            return 0.0

        deficit = 1.0 - need.satisfaction
        urgency = need.urgency

        # Deprivasyon suresi etkisi
        deprivation_factor = min(2.0, 1.0 + need.deprivation_duration / 24.0)

        return deficit * need.importance * deprivation_factor * (1.0 + urgency)

    def get_dominant_drive(self) -> Optional[Dict[str, Any]]:
        """
        Baskin durt ihtiyacini getir.

        Returns:
            Baskin durt bilgisi
        """
        if not self.needs:
            return None

        drives = [(n, self.calculate_drive(n.id)) for n in self.needs.values()]
        dominant = max(drives, key=lambda x: x[1])

        return {
            "need": dominant[0].name,
            "need_id": dominant[0].id,
            "drive_strength": dominant[1],
            "satisfaction": dominant[0].satisfaction,
            "level": dominant[0].level.value,
        }

    # ========================================================================
    # STATISTICS & STATE
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Istatistikleri getir."""
        return self._stats.copy()

    def get_overall_wellbeing(self) -> float:
        """
        Genel iyilik halini hesapla.

        Tum ihtiyaclarin agirlikli ortalamasi.
        """
        if not self.needs:
            return 0.5

        # Seviye agirliklari (alt seviyeler daha onemli)
        level_weights = {
            NeedLevel.PHYSIOLOGICAL: 1.0,
            NeedLevel.SAFETY: 0.9,
            NeedLevel.BELONGING: 0.7,
            NeedLevel.ESTEEM: 0.5,
            NeedLevel.SELF_ACTUALIZATION: 0.3,
        }

        weighted_sum = 0.0
        weight_total = 0.0

        for need in self.needs.values():
            weight = level_weights.get(need.level, 0.5) * need.importance
            weighted_sum += need.satisfaction * weight
            weight_total += weight

        return weighted_sum / weight_total if weight_total > 0 else 0.5

    def summary(self) -> Dict[str, Any]:
        """Ozet bilgi."""
        return {
            "total_needs": len(self.needs),
            "satisfied_needs": len(self.get_satisfied_needs()),
            "unsatisfied_needs": len(self.get_unsatisfied_needs()),
            "critical_needs": len(self.get_critical_needs()),
            "overall_wellbeing": self.get_overall_wellbeing(),
            "most_pressing": self.get_most_pressing_need().name if self.get_most_pressing_need() else None,
            "dominant_drive": self.get_dominant_drive(),
            "hierarchy": self.check_hierarchy_satisfaction(),
            "stats": self._stats,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_need_manager(
    config: Optional[NeedConfig] = None,
    initialize_defaults: bool = True,
) -> NeedManager:
    """NeedManager factory."""
    manager = NeedManager(config)
    if initialize_defaults:
        manager.initialize_default_needs()
    return manager


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "NeedConfig",
    "NeedManager",
    "create_need_manager",
    "get_default_needs",
]
