"""
UEM v2 - Identity Module

Kimlik yonetimi.
Agent'in "Ben kimim?" sorusuna cevap veren modul.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from ..types import (
    Identity,
    IdentityTrait,
    IdentityAspect,
    IntegrityStatus,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class IdentityConfig:
    """Kimlik modulu yapilandirmasi."""
    # Stabilite parametreleri
    min_trait_strength: float = 0.1
    max_traits_per_aspect: int = 10
    core_trait_threshold: float = 0.7

    # Zaman parametreleri
    trait_decay_rate: float = 0.01  # Guclendirilmezse gucu azalir
    reinforcement_cooldown_hours: float = 1.0

    # Kriz esikleri
    crisis_threshold: float = 0.3
    stability_warning_threshold: float = 0.5

    # Ozellikler
    allow_trait_removal: bool = True
    track_trait_history: bool = True


# ============================================================================
# IDENTITY MANAGER
# ============================================================================

class IdentityManager:
    """
    Kimlik yoneticisi.

    Agent'in kimligini olusturur, gunceller ve korur.
    """

    def __init__(self, config: Optional[IdentityConfig] = None):
        """
        IdentityManager baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or IdentityConfig()
        self.identity = Identity()

        # Trait gecmisi (opsiyonel)
        self._trait_history: List[Dict[str, Any]] = []

        # Istatistikler
        self._stats = {
            "traits_added": 0,
            "traits_removed": 0,
            "traits_reinforced": 0,
            "traits_challenged": 0,
            "roles_added": 0,
            "identity_crises": 0,
        }

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def initialize_identity(
        self,
        name: str,
        description: str = "",
        core_traits: Optional[List[Dict[str, Any]]] = None,
        roles: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        limitations: Optional[List[str]] = None,
    ) -> Identity:
        """
        Kimligi baslat.

        Args:
            name: Agent ismi
            description: Kisa tanim
            core_traits: Temel ozellikler [{"name": "...", "description": "..."}]
            roles: Roller
            capabilities: Yetenekler
            limitations: Sinirlamalar

        Returns:
            Baslangic kimligi
        """
        self.identity = Identity(
            name=name,
            description=description,
            roles=roles or [],
            primary_role=roles[0] if roles else None,
            capabilities=capabilities or [],
            limitations=limitations or [],
        )

        # Temel ozellikleri ekle
        if core_traits:
            for trait_data in core_traits:
                trait = IdentityTrait(
                    name=trait_data.get("name", ""),
                    description=trait_data.get("description", ""),
                    aspect=IdentityAspect.CORE,
                    strength=trait_data.get("strength", 0.8),
                    stability=trait_data.get("stability", 0.9),
                )
                self.add_trait(trait)

        return self.identity

    # ========================================================================
    # TRAIT MANAGEMENT
    # ========================================================================

    def add_trait(self, trait: IdentityTrait) -> bool:
        """
        Kimlik ozelligi ekle.

        Args:
            trait: Eklenecek ozellik

        Returns:
            Basarili mi
        """
        # Aspect basina maksimum kontrol
        aspect_traits = self.identity.get_traits_by_aspect(trait.aspect)
        if len(aspect_traits) >= self.config.max_traits_per_aspect:
            # En zayif ozelligi kaldir
            weakest = min(aspect_traits, key=lambda t: t.strength)
            if weakest.strength < trait.strength:
                self.remove_trait(weakest.id)
            else:
                return False

        self.identity.add_trait(trait)
        self._stats["traits_added"] += 1

        if self.config.track_trait_history:
            self._trait_history.append({
                "action": "added",
                "trait_id": trait.id,
                "trait_name": trait.name,
                "timestamp": datetime.now().isoformat(),
            })

        return True

    def remove_trait(self, trait_id: str) -> bool:
        """
        Kimlik ozelligini kaldir.

        Args:
            trait_id: Kaldirilacak ozellik ID

        Returns:
            Basarili mi
        """
        if not self.config.allow_trait_removal:
            return False

        if trait_id not in self.identity.traits:
            return False

        trait = self.identity.traits[trait_id]

        # Core trait kontrolu
        if trait_id in self.identity.core_traits:
            if trait.strength >= self.config.core_trait_threshold:
                # Guclu core trait kaldirilamaz
                return False
            self.identity.core_traits.remove(trait_id)

        del self.identity.traits[trait_id]
        self._stats["traits_removed"] += 1

        if self.config.track_trait_history:
            self._trait_history.append({
                "action": "removed",
                "trait_id": trait_id,
                "trait_name": trait.name,
                "timestamp": datetime.now().isoformat(),
            })

        return True

    def reinforce_trait(self, trait_id: str, amount: float = 0.1) -> bool:
        """
        Kimlik ozelligini guclendir.

        Args:
            trait_id: Ozellik ID
            amount: Guc artisi

        Returns:
            Basarili mi
        """
        trait = self.identity.get_trait(trait_id)
        if not trait:
            return False

        trait.reinforce(amount)
        self._stats["traits_reinforced"] += 1

        return True

    def challenge_trait(self, trait_id: str, amount: float = 0.1) -> bool:
        """
        Kimlik ozelligini sorgula/zayiflat.

        Args:
            trait_id: Ozellik ID
            amount: Zayiflama miktari

        Returns:
            Basarili mi
        """
        trait = self.identity.get_trait(trait_id)
        if not trait:
            return False

        trait.challenge(amount)
        self._stats["traits_challenged"] += 1

        # Cok zayif dustu mu?
        if trait.strength < self.config.min_trait_strength:
            self.remove_trait(trait_id)

        return True

    def find_trait_by_name(self, name: str) -> Optional[IdentityTrait]:
        """
        Isimle ozellik bul.

        Args:
            name: Ozellik ismi

        Returns:
            Bulunan ozellik veya None
        """
        for trait in self.identity.traits.values():
            if trait.name.lower() == name.lower():
                return trait
        return None

    # ========================================================================
    # ROLE MANAGEMENT
    # ========================================================================

    def add_role(self, role: str, set_primary: bool = False) -> None:
        """
        Rol ekle.

        Args:
            role: Rol ismi
            set_primary: Birincil rol yap
        """
        self.identity.add_role(role)
        if set_primary:
            self.identity.primary_role = role
        self._stats["roles_added"] += 1

    def remove_role(self, role: str) -> bool:
        """
        Rol kaldir.

        Args:
            role: Rol ismi

        Returns:
            Basarili mi
        """
        if role not in self.identity.roles:
            return False

        self.identity.roles.remove(role)
        if self.identity.primary_role == role:
            self.identity.primary_role = self.identity.roles[0] if self.identity.roles else None

        return True

    def set_primary_role(self, role: str) -> bool:
        """
        Birincil rolu ayarla.

        Args:
            role: Rol ismi

        Returns:
            Basarili mi
        """
        if role in self.identity.roles:
            self.identity.primary_role = role
            return True
        return False

    # ========================================================================
    # CAPABILITY MANAGEMENT
    # ========================================================================

    def add_capability(self, capability: str) -> None:
        """Yetenek ekle."""
        if capability not in self.identity.capabilities:
            self.identity.capabilities.append(capability)
            self.identity.last_updated = datetime.now()

    def remove_capability(self, capability: str) -> bool:
        """Yetenek kaldir."""
        if capability in self.identity.capabilities:
            self.identity.capabilities.remove(capability)
            return True
        return False

    def add_limitation(self, limitation: str) -> None:
        """Sinirlama ekle."""
        if limitation not in self.identity.limitations:
            self.identity.limitations.append(limitation)
            self.identity.last_updated = datetime.now()

    def has_capability(self, capability: str) -> bool:
        """Yetenek var mi?"""
        return capability in self.identity.capabilities

    # ========================================================================
    # IDENTITY ANALYSIS
    # ========================================================================

    def check_identity_stability(self) -> Dict[str, Any]:
        """
        Kimlik stabilitesini kontrol et.

        Returns:
            Stabilite raporu
        """
        core_traits = self.identity.get_core_identity()

        if not core_traits:
            return {
                "stable": False,
                "status": IntegrityStatus.CRISIS,
                "message": "No core traits defined",
                "score": 0.0,
            }

        # Ortalama guc ve stabilite
        avg_strength = sum(t.strength for t in core_traits) / len(core_traits)
        avg_stability = sum(t.stability for t in core_traits) / len(core_traits)

        # Zayif ozellikler
        weak_traits = [t for t in core_traits if t.strength < self.config.stability_warning_threshold]
        challenged_traits = [t for t in core_traits if t.challenge_count > t.reinforcement_count]

        # Durum belirleme
        score = (avg_strength + avg_stability) / 2

        if score < self.config.crisis_threshold:
            status = IntegrityStatus.CRISIS
            self._stats["identity_crises"] += 1
        elif score < self.config.stability_warning_threshold:
            status = IntegrityStatus.MAJOR_CONFLICT
        elif weak_traits or challenged_traits:
            status = IntegrityStatus.MINOR_CONFLICT
        else:
            status = IntegrityStatus.ALIGNED

        return {
            "stable": status == IntegrityStatus.ALIGNED,
            "status": status,
            "score": score,
            "avg_strength": avg_strength,
            "avg_stability": avg_stability,
            "weak_traits": [t.name for t in weak_traits],
            "challenged_traits": [t.name for t in challenged_traits],
            "core_trait_count": len(core_traits),
            "total_trait_count": len(self.identity.traits),
        }

    def get_identity_conflicts(self) -> List[Dict[str, Any]]:
        """
        Kimlik cakismalarini bul.

        Returns:
            Catisma listesi
        """
        conflicts = []
        traits = list(self.identity.traits.values())

        # Trait-trait cakismalari (behavioral_impact cakismasi)
        for i, t1 in enumerate(traits):
            for t2 in traits[i + 1:]:
                # Zit etkiler var mi?
                common_behaviors = set(t1.behavioral_impact.keys()) & set(t2.behavioral_impact.keys())
                for behavior in common_behaviors:
                    impact1 = t1.behavioral_impact[behavior]
                    impact2 = t2.behavioral_impact[behavior]
                    # Zit yonlu ve ikisi de guclu
                    if impact1 * impact2 < 0 and abs(impact1) > 0.3 and abs(impact2) > 0.3:
                        conflicts.append({
                            "type": "trait_conflict",
                            "trait1": t1.name,
                            "trait2": t2.name,
                            "behavior": behavior,
                            "severity": abs(impact1 - impact2),
                        })

        return conflicts

    def generate_self_description(self) -> str:
        """
        Kimlik tanimi olustur.

        Returns:
            Insan tarafindan okunabilir kimlik tanimi
        """
        parts = []

        # Temel tanim
        parts.append(f"I am {self.identity.name}.")
        if self.identity.description:
            parts.append(self.identity.description)

        # Roller
        if self.identity.roles:
            if self.identity.primary_role:
                other_roles = [r for r in self.identity.roles if r != self.identity.primary_role]
                parts.append(f"My primary role is {self.identity.primary_role}.")
                if other_roles:
                    parts.append(f"I also serve as {', '.join(other_roles)}.")
            else:
                parts.append(f"My roles include: {', '.join(self.identity.roles)}.")

        # Core traits
        core_traits = self.identity.get_core_identity()
        if core_traits:
            trait_names = [t.name for t in core_traits]
            parts.append(f"My core characteristics are: {', '.join(trait_names)}.")

        # Yetenekler
        if self.identity.capabilities:
            parts.append(f"I am capable of: {', '.join(self.identity.capabilities)}.")

        # Sinirlamalar
        if self.identity.limitations:
            parts.append(f"I acknowledge my limitations: {', '.join(self.identity.limitations)}.")

        return " ".join(parts)

    # ========================================================================
    # TRAIT DECAY
    # ========================================================================

    def apply_trait_decay(self, hours_passed: float = 1.0) -> List[str]:
        """
        Zaman gecisine bagli ozellik gucu azalmasi.

        Args:
            hours_passed: Gecen saat

        Returns:
            Zayiflayan ozelliklerin isimleri
        """
        decayed = []
        decay_amount = self.config.trait_decay_rate * hours_passed

        for trait in self.identity.traits.values():
            # Son guclendirilmeden bu yana gecen sure
            if trait.last_reinforced:
                time_since = (datetime.now() - trait.last_reinforced).total_seconds() / 3600
                if time_since > self.config.reinforcement_cooldown_hours:
                    # Decay uygula (stability azaltir etkiyi)
                    effective_decay = decay_amount * (1.0 - trait.stability * 0.5)
                    trait.strength = max(self.config.min_trait_strength, trait.strength - effective_decay)
                    decayed.append(trait.name)

        return decayed

    # ========================================================================
    # STATISTICS & STATE
    # ========================================================================

    def get_stats(self) -> Dict[str, int]:
        """Istatistikleri getir."""
        return self._stats.copy()

    def get_trait_history(self) -> List[Dict[str, Any]]:
        """Ozellik gecmisini getir."""
        return self._trait_history.copy()

    def get_identity(self) -> Identity:
        """Kimligi getir."""
        return self.identity

    def to_dict(self) -> Dict[str, Any]:
        """Durumu dict olarak don."""
        return {
            "identity": {
                "id": self.identity.id,
                "name": self.identity.name,
                "description": self.identity.description,
                "roles": self.identity.roles,
                "primary_role": self.identity.primary_role,
                "capabilities": self.identity.capabilities,
                "limitations": self.identity.limitations,
                "trait_count": len(self.identity.traits),
                "core_trait_count": len(self.identity.core_traits),
            },
            "stability": self.check_identity_stability(),
            "stats": self._stats,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_identity_manager(config: Optional[IdentityConfig] = None) -> IdentityManager:
    """IdentityManager factory."""
    return IdentityManager(config)


def create_default_identity(
    name: str = "UEM Agent",
    description: str = "A unified emotional machine agent",
) -> Identity:
    """Varsayilan kimlik olustur."""
    manager = IdentityManager()
    return manager.initialize_identity(
        name=name,
        description=description,
        core_traits=[
            {"name": "Helpful", "description": "Strives to assist and support others"},
            {"name": "Curious", "description": "Eager to learn and understand"},
            {"name": "Ethical", "description": "Acts according to moral principles"},
        ],
        roles=["Assistant", "Learner"],
        capabilities=["Communication", "Reasoning", "Learning"],
        limitations=["Physical interaction", "Real-time data access"],
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "IdentityConfig",
    "IdentityManager",
    "create_identity_manager",
    "create_default_identity",
]
