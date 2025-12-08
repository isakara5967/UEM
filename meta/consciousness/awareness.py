"""
UEM v2 - Awareness Module

Farkindalik yonetimi.
Farkli farkindalik turlerini ve seviyelerini yonetir.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .types import (
    AwarenessState,
    AwarenessType,
    ConsciousnessLevel,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class AwarenessConfig:
    """Farkindalik modulu yapilandirmasi."""
    # Esik degerleri
    conscious_threshold: float = 0.6      # Bu ustunde bilinc
    hyperconscious_threshold: float = 0.9 # Bu ustunde yukseltilmis bilinc
    preconscious_threshold: float = 0.3   # Bu ustunde onbilinc
    unconscious_threshold: float = 0.1    # Bu altinda bilindisi

    # Decay parametreleri
    awareness_decay_rate: float = 0.05    # Aktif olmayanlar zayiflar
    refresh_boost: float = 0.1            # Yenilenince artis

    # Sinirlar
    max_aware_items: int = 7              # Ayni anda farkinda olunan (7+-2)
    background_capacity: int = 20         # Arka planda tutulan

    # Ozellikler
    enable_meta_awareness: bool = True
    track_history: bool = True


# ============================================================================
# AWARENESS MANAGER
# ============================================================================

class AwarenessManager:
    """
    Farkindalik yoneticisi.

    Farkli farkindalik turlerini izler ve gunceller:
    - Sensory (duyusal)
    - Cognitive (bilissel)
    - Emotional (duygusal)
    - Social (sosyal)
    - Self (oz)
    - Meta (meta-farkindalik)
    """

    def __init__(self, config: Optional[AwarenessConfig] = None):
        """
        AwarenessManager baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or AwarenessConfig()

        # Farkindalik durumlari
        self.awareness_states: Dict[AwarenessType, AwarenessState] = {}

        # Bilinc seviyesi
        self.consciousness_level: ConsciousnessLevel = ConsciousnessLevel.CONSCIOUS

        # Gecmis (opsiyonel)
        self._history: List[Dict[str, Any]] = []

        # Istatistikler
        self._stats = {
            "awareness_updates": 0,
            "level_changes": 0,
            "peaks": 0,  # Hyperconscious anlar
            "drops": 0,  # Unconscious anlara dusus
        }

        # Varsayilanlari yukle
        self._initialize_awareness_states()

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def _initialize_awareness_states(self) -> None:
        """Varsayilan farkindalik durumlarini olustur."""
        for awareness_type in AwarenessType:
            state = AwarenessState(
                awareness_type=awareness_type,
                level=0.5,
                clarity=0.5,
                depth=0.5,
            )
            self.awareness_states[awareness_type] = state

    # ========================================================================
    # AWARENESS ACCESS
    # ========================================================================

    def get_awareness(self, awareness_type: AwarenessType) -> AwarenessState:
        """
        Farkindalik durumunu getir.

        Args:
            awareness_type: Farkindalik turu

        Returns:
            Farkindalik durumu
        """
        return self.awareness_states.get(
            awareness_type,
            AwarenessState(awareness_type=awareness_type),
        )

    def get_all_awareness(self) -> Dict[AwarenessType, AwarenessState]:
        """Tum farkindalik durumlarini getir."""
        return self.awareness_states.copy()

    def get_awareness_level(self, awareness_type: AwarenessType) -> float:
        """Belirli bir turun farkindalik seviyesini getir."""
        state = self.get_awareness(awareness_type)
        return state.level

    # ========================================================================
    # AWARENESS UPDATES
    # ========================================================================

    def update_awareness(
        self,
        awareness_type: AwarenessType,
        level: Optional[float] = None,
        clarity: Optional[float] = None,
        depth: Optional[float] = None,
        focus: Optional[str] = None,
    ) -> AwarenessState:
        """
        Farkindalik durumunu guncelle.

        Args:
            awareness_type: Farkindalik turu
            level: Yeni seviye
            clarity: Yeni berraklik
            depth: Yeni derinlik
            focus: Yeni odak

        Returns:
            Guncellenmis durum
        """
        state = self.get_awareness(awareness_type)

        if level is not None:
            state.level = max(0.0, min(1.0, level))
        if clarity is not None:
            state.clarity = max(0.0, min(1.0, clarity))
        if depth is not None:
            state.depth = max(0.0, min(1.0, depth))
        if focus is not None:
            # Onceki odagi arka plana al
            if state.current_focus and state.current_focus != focus:
                if state.current_focus not in state.background_items:
                    state.background_items.append(state.current_focus)
                    # Kapasite kontrolu
                    if len(state.background_items) > self.config.background_capacity:
                        state.background_items.pop(0)
            state.current_focus = focus

        state.last_update = datetime.now()
        self.awareness_states[awareness_type] = state
        self._stats["awareness_updates"] += 1

        # Bilinc seviyesini guncelle
        self._update_consciousness_level()

        # Gecmis kaydi
        if self.config.track_history:
            self._record_history(awareness_type, state)

        return state

    def boost_awareness(
        self,
        awareness_type: AwarenessType,
        amount: float = 0.1,
    ) -> AwarenessState:
        """
        Farkindaligi artir.

        Args:
            awareness_type: Farkindalik turu
            amount: Artis miktari

        Returns:
            Guncellenmis durum
        """
        state = self.get_awareness(awareness_type)
        return self.update_awareness(
            awareness_type,
            level=state.level + amount,
            clarity=state.clarity + amount * 0.5,
        )

    def diminish_awareness(
        self,
        awareness_type: AwarenessType,
        amount: float = 0.1,
    ) -> AwarenessState:
        """
        Farkindaligi azalt.

        Args:
            awareness_type: Farkindalik turu
            amount: Azalma miktari

        Returns:
            Guncellenmis durum
        """
        state = self.get_awareness(awareness_type)
        return self.update_awareness(
            awareness_type,
            level=state.level - amount,
            clarity=state.clarity - amount * 0.5,
        )

    def refresh_awareness(self, awareness_type: AwarenessType) -> AwarenessState:
        """
        Farkindaligi yenile (tazeleme).

        Args:
            awareness_type: Farkindalik turu

        Returns:
            Guncellenmis durum
        """
        return self.boost_awareness(awareness_type, self.config.refresh_boost)

    # ========================================================================
    # CONSCIOUSNESS LEVEL
    # ========================================================================

    def _update_consciousness_level(self) -> None:
        """Genel bilinc seviyesini guncelle."""
        old_level = self.consciousness_level
        overall = self.get_overall_awareness()

        if overall >= self.config.hyperconscious_threshold:
            self.consciousness_level = ConsciousnessLevel.HYPERCONSCIOUS
            self._stats["peaks"] += 1
        elif overall >= self.config.conscious_threshold:
            self.consciousness_level = ConsciousnessLevel.CONSCIOUS
        elif overall >= self.config.preconscious_threshold:
            self.consciousness_level = ConsciousnessLevel.PRECONSCIOUS
        elif overall >= self.config.unconscious_threshold:
            self.consciousness_level = ConsciousnessLevel.SUBCONSCIOUS
        else:
            self.consciousness_level = ConsciousnessLevel.UNCONSCIOUS
            self._stats["drops"] += 1

        if old_level != self.consciousness_level:
            self._stats["level_changes"] += 1

    def get_consciousness_level(self) -> ConsciousnessLevel:
        """Bilinc seviyesini getir."""
        return self.consciousness_level

    def get_overall_awareness(self) -> float:
        """
        Genel farkindalik seviyesini hesapla.

        Returns:
            0-1 arasi deger
        """
        if not self.awareness_states:
            return 0.5

        # Agirlikli ortalama
        weights = {
            AwarenessType.SENSORY: 1.0,
            AwarenessType.COGNITIVE: 1.2,
            AwarenessType.EMOTIONAL: 1.0,
            AwarenessType.SOCIAL: 0.8,
            AwarenessType.SELF: 1.5,
            AwarenessType.META: 1.3,
        }

        weighted_sum = 0.0
        weight_total = 0.0

        for awareness_type, state in self.awareness_states.items():
            weight = weights.get(awareness_type, 1.0)
            weighted_sum += state.quality * weight
            weight_total += weight

        return weighted_sum / weight_total if weight_total > 0 else 0.5

    # ========================================================================
    # META AWARENESS
    # ========================================================================

    def check_meta_awareness(self) -> Dict[str, Any]:
        """
        Meta-farkindalik kontrolu.

        Meta-farkindalik = Farkindaligin farkinda olmak

        Returns:
            Meta-farkindalik raporu
        """
        if not self.config.enable_meta_awareness:
            return {"enabled": False}

        meta_state = self.get_awareness(AwarenessType.META)
        self_state = self.get_awareness(AwarenessType.SELF)

        # Meta-farkindalik self-awareness'e bagimli
        meta_level = meta_state.level * self_state.level

        # Diger farkindaliklarin farkinda olma
        aware_of = []
        for awareness_type, state in self.awareness_states.items():
            if state.level >= self.config.conscious_threshold:
                aware_of.append(awareness_type.value)

        return {
            "enabled": True,
            "level": meta_level,
            "self_awareness": self_state.level,
            "meta_clarity": meta_state.clarity,
            "aware_of_types": aware_of,
            "reflection_depth": meta_state.depth,
        }

    # ========================================================================
    # AWARENESS DECAY
    # ========================================================================

    def apply_decay(self, hours_passed: float = 1.0) -> Dict[str, float]:
        """
        Zaman bazli farkindalik azalmasi.

        Args:
            hours_passed: Gecen sure (saat)

        Returns:
            Her tur icin azalma miktari
        """
        decay_amount = self.config.awareness_decay_rate * hours_passed
        changes = {}

        for awareness_type in self.awareness_states:
            state = self.awareness_states[awareness_type]
            old_level = state.level

            # Decay uygula (clarity azalir daha cok)
            state.level = max(0.0, state.level - decay_amount * 0.5)
            state.clarity = max(0.0, state.clarity - decay_amount)
            state.last_update = datetime.now()

            changes[awareness_type.value] = old_level - state.level

        self._update_consciousness_level()
        return changes

    # ========================================================================
    # AWARENESS ANALYSIS
    # ========================================================================

    def get_dominant_awareness(self) -> Optional[AwarenessType]:
        """
        Baskin farkindalik turunu getir.

        Returns:
            En yuksek farkindalik turu
        """
        if not self.awareness_states:
            return None

        return max(
            self.awareness_states.keys(),
            key=lambda t: self.awareness_states[t].quality,
        )

    def get_weak_awareness_types(
        self,
        threshold: float = 0.3,
    ) -> List[AwarenessType]:
        """
        Zayif farkindalik turlerini getir.

        Args:
            threshold: Esik deger

        Returns:
            Zayif turler listesi
        """
        return [
            awareness_type
            for awareness_type, state in self.awareness_states.items()
            if state.level < threshold
        ]

    def is_conscious(self) -> bool:
        """Agent bilinc seviyesinde mi?"""
        return self.consciousness_level in (
            ConsciousnessLevel.CONSCIOUS,
            ConsciousnessLevel.HYPERCONSCIOUS,
        )

    def is_aware_of(self, awareness_type: AwarenessType) -> bool:
        """Belirli bir turde farkinda mi?"""
        state = self.get_awareness(awareness_type)
        return state.level >= self.config.conscious_threshold

    # ========================================================================
    # HISTORY & STATS
    # ========================================================================

    def _record_history(self, awareness_type: AwarenessType, state: AwarenessState) -> None:
        """Gecmis kaydi."""
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "type": awareness_type.value,
            "level": state.level,
            "clarity": state.clarity,
            "depth": state.depth,
            "quality": state.quality,
        })

        # Gecmis siniri
        max_history = 1000
        if len(self._history) > max_history:
            self._history = self._history[-max_history:]

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Son gecmis kayitlarini getir."""
        return self._history[-limit:]

    def get_stats(self) -> Dict[str, int]:
        """Istatistikleri getir."""
        return self._stats.copy()

    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================

    def summary(self) -> Dict[str, Any]:
        """Genel ozet."""
        return {
            "consciousness_level": self.consciousness_level.value,
            "overall_awareness": self.get_overall_awareness(),
            "is_conscious": self.is_conscious(),
            "dominant_type": self.get_dominant_awareness().value if self.get_dominant_awareness() else None,
            "weak_types": [t.value for t in self.get_weak_awareness_types()],
            "meta_awareness": self.check_meta_awareness(),
            "awareness_levels": {
                t.value: s.level for t, s in self.awareness_states.items()
            },
            "stats": self._stats,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_awareness_manager(
    config: Optional[AwarenessConfig] = None,
) -> AwarenessManager:
    """AwarenessManager factory."""
    return AwarenessManager(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "AwarenessConfig",
    "AwarenessManager",
    "create_awareness_manager",
]
