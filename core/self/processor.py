"""
UEM v2 - Self Processor

Benlik modulu ana islemcisi.
Identity, Values, Needs ve Personal Goals'u entegre eder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .types import (
    SelfState,
    Identity,
    Value,
    Need,
    PersonalGoal,
    NarrativeElement,
    IdentityTrait,
    IntegrityStatus,
    NeedLevel,
    GoalDomain,
    ValueCategory,
    NarrativeType,
)
from .identity import IdentityManager, IdentityConfig
from .goals import PersonalGoalManager, PersonalGoalConfig
from .needs import NeedManager, NeedConfig
from .values import ValueSystem, ValueSystemConfig


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class SelfProcessorConfig:
    """Self processor yapilandirmasi."""
    # Alt modul konfigurasyonlari
    identity_config: Optional[IdentityConfig] = None
    goal_config: Optional[PersonalGoalConfig] = None
    need_config: Optional[NeedConfig] = None
    value_config: Optional[ValueSystemConfig] = None

    # Entegrasyon parametreleri
    integrity_check_interval: int = 5  # Her N cycle'da bir
    auto_narrative_creation: bool = True
    significant_event_threshold: float = 0.7

    # Zaman parametreleri
    time_decay_hours: float = 1.0

    # Varsayilanlari yukle
    initialize_defaults: bool = True


# ============================================================================
# SELF OUTPUT
# ============================================================================

@dataclass
class SelfOutput:
    """Self processing ciktisi."""
    # Durum
    self_state: SelfState

    # Oncelikler
    most_pressing_need: Optional[str] = None
    dominant_value: Optional[str] = None
    focus_goal: Optional[str] = None

    # Tutarlilik
    integrity_status: IntegrityStatus = IntegrityStatus.ALIGNED
    integrity_score: float = 1.0
    integrity_concerns: List[str] = field(default_factory=list)

    # Oneriler
    recommended_actions: List[str] = field(default_factory=list)
    values_to_express: List[str] = field(default_factory=list)
    needs_to_satisfy: List[str] = field(default_factory=list)

    # Meta
    processing_time_ms: float = 0.0
    cycle_id: int = 0


# ============================================================================
# SELF PROCESSOR
# ============================================================================

class SelfProcessor:
    """
    Benlik islemcisi.

    Tum benlik alt modullerini koordine eder:
    - Identity (kimlik)
    - Values (degerler)
    - Needs (ihtiyaclar)
    - Personal Goals (kisisel hedefler)
    """

    def __init__(self, config: Optional[SelfProcessorConfig] = None):
        """
        SelfProcessor baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or SelfProcessorConfig()

        # Alt modulleri olustur
        self.identity_manager = IdentityManager(self.config.identity_config)
        self.goal_manager = PersonalGoalManager(self.config.goal_config)
        self.need_manager = NeedManager(self.config.need_config)
        self.value_system = ValueSystem(self.config.value_config)

        # State
        self.self_state = SelfState()
        self._cycle_count = 0

        # Varsayilanlari yukle
        if self.config.initialize_defaults:
            self._initialize_defaults()

        # Istatistikler
        self._stats = {
            "process_calls": 0,
            "integrity_checks": 0,
            "narratives_created": 0,
            "significant_events": 0,
        }

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def _initialize_defaults(self) -> None:
        """Varsayilan degerleri yukle."""
        # Identity
        self.identity_manager.initialize_identity(
            name="UEM Agent",
            description="A unified emotional machine agent with self-awareness",
            core_traits=[
                {"name": "Helpful", "description": "Strives to assist others", "strength": 0.9},
                {"name": "Curious", "description": "Eager to learn", "strength": 0.8},
                {"name": "Ethical", "description": "Acts morally", "strength": 0.95},
            ],
            roles=["Assistant", "Learner", "Companion"],
            capabilities=["Communication", "Reasoning", "Learning", "Empathy"],
            limitations=["Physical interaction", "Real-time data", "Perfect memory"],
        )

        # Values
        self.value_system.initialize_default_values()

        # Needs
        self.need_manager.initialize_default_needs()

        # State'i guncelle
        self._sync_state()

    def _sync_state(self) -> None:
        """Alt modullerdeki durumu SelfState'e senkronize et."""
        # Identity
        self.self_state.identity = self.identity_manager.get_identity()

        # Values
        self.self_state.values = self.value_system.values.copy()
        self.self_state.core_values = self.value_system.core_value_ids.copy()

        # Needs
        self.self_state.needs = self.need_manager.needs.copy()

        # Goals
        self.self_state.personal_goals = self.goal_manager.goals.copy()

        self.self_state.last_update = datetime.now()

    # ========================================================================
    # MAIN PROCESSING
    # ========================================================================

    def process(
        self,
        context: Optional[Dict[str, Any]] = None,
        time_delta_hours: float = 0.0,
    ) -> SelfOutput:
        """
        Benlik islemi calistir.

        Args:
            context: Baglam bilgisi (mevcut durum, olaylar, vb.)
            time_delta_hours: Gecen sure (zaman bazli decay icin)

        Returns:
            SelfOutput
        """
        start_time = datetime.now()
        self._cycle_count += 1
        self._stats["process_calls"] += 1

        context = context or {}

        # 1. Zaman bazli decay
        if time_delta_hours > 0:
            self._apply_time_effects(time_delta_hours)

        # 2. Ihtiyac analizi
        need_analysis = self._analyze_needs()

        # 3. Deger analizi
        value_analysis = self._analyze_values(context)

        # 4. Hedef analizi
        goal_analysis = self._analyze_goals()

        # 5. Tutarlilik kontrolu
        integrity_result = self._check_integrity()

        # 6. Onerileri olustur
        recommendations = self._generate_recommendations(
            need_analysis, value_analysis, goal_analysis, integrity_result
        )

        # 7. Onemli olay varsa narrative olustur
        if self.config.auto_narrative_creation:
            self._check_for_significant_events(context)

        # State'i senkronize et
        self._sync_state()

        # Cikti olustur
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return SelfOutput(
            self_state=self.self_state,
            most_pressing_need=need_analysis.get("most_pressing"),
            dominant_value=value_analysis.get("dominant"),
            focus_goal=goal_analysis.get("focus"),
            integrity_status=integrity_result["status"],
            integrity_score=integrity_result["score"],
            integrity_concerns=integrity_result.get("concerns", []),
            recommended_actions=recommendations.get("actions", []),
            values_to_express=recommendations.get("values", []),
            needs_to_satisfy=recommendations.get("needs", []),
            processing_time_ms=processing_time,
            cycle_id=self._cycle_count,
        )

    # ========================================================================
    # ANALYSIS METHODS
    # ========================================================================

    def _analyze_needs(self) -> Dict[str, Any]:
        """Ihtiyac analizi."""
        most_pressing = self.need_manager.get_most_pressing_need()
        critical = self.need_manager.get_critical_needs()
        dominant_drive = self.need_manager.get_dominant_drive()

        return {
            "most_pressing": most_pressing.name if most_pressing else None,
            "most_pressing_id": most_pressing.id if most_pressing else None,
            "critical_count": len(critical),
            "critical_needs": [n.name for n in critical],
            "overall_wellbeing": self.need_manager.get_overall_wellbeing(),
            "dominant_drive": dominant_drive,
            "hierarchy": self.need_manager.check_hierarchy_satisfaction(),
        }

    def _analyze_values(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deger analizi."""
        dominant = self.value_system.get_dominant_value()
        integrity = self.value_system.calculate_value_integrity()
        conflicts = self.value_system.detect_conflicts()

        return {
            "dominant": dominant.name if dominant else None,
            "dominant_id": dominant.id if dominant else None,
            "integrity": integrity,
            "conflict_count": len(conflicts),
            "conflicts": conflicts[:3],  # En fazla 3 catisma
            "sacred_values": [v.name for v in self.value_system.get_sacred_values()],
        }

    def _analyze_goals(self) -> Dict[str, Any]:
        """Hedef analizi."""
        focus = self.goal_manager.suggest_focus_goal()
        active = self.goal_manager.get_active_goals()
        stale = self.goal_manager.get_stale_goals()

        return {
            "focus": focus.name if focus else None,
            "focus_id": focus.id if focus else None,
            "active_count": len(active),
            "stale_count": len(stale),
            "stale_goals": [g.name for g in stale],
            "completion_rate": self.goal_manager.get_completion_rate(),
        }

    def _check_integrity(self) -> Dict[str, Any]:
        """Tutarlilik kontrolu."""
        self._stats["integrity_checks"] += 1

        # Kimlik tutarliligi
        identity_stability = self.identity_manager.check_identity_stability()

        # Deger tutarliligi
        value_integrity = self.value_system.calculate_value_integrity()

        # Ihtiyac-deger uyumu
        need_value_alignment = self._check_need_value_alignment()

        # Genel skor
        overall_score = (
            identity_stability["score"] * 0.4 +
            value_integrity * 0.4 +
            need_value_alignment * 0.2
        )

        # Durum belirleme
        if overall_score >= 0.8:
            status = IntegrityStatus.ALIGNED
        elif overall_score >= 0.6:
            status = IntegrityStatus.MINOR_CONFLICT
        elif overall_score >= 0.4:
            status = IntegrityStatus.MAJOR_CONFLICT
        else:
            status = IntegrityStatus.CRISIS

        # Endiseler
        concerns = []
        if identity_stability["score"] < 0.5:
            concerns.append("Identity stability is low")
        if value_integrity < 0.7:
            concerns.append("Value integrity concerns")
        if need_value_alignment < 0.5:
            concerns.append("Need-value misalignment")
        if identity_stability.get("weak_traits"):
            concerns.append(f"Weak traits: {', '.join(identity_stability['weak_traits'])}")

        # State'i guncelle
        self.self_state.integrity_status = status
        self.self_state.integrity_score = overall_score

        return {
            "status": status,
            "score": overall_score,
            "identity_score": identity_stability["score"],
            "value_score": value_integrity,
            "alignment_score": need_value_alignment,
            "concerns": concerns,
        }

    def _check_need_value_alignment(self) -> float:
        """Ihtiyac-deger uyumunu kontrol et."""
        # Basit heuristik: kritik ihtiyaclar varken yuksek seviye degerlere odaklanma
        critical_needs = self.need_manager.get_critical_needs()
        if not critical_needs:
            return 1.0

        # Kritik ihtiyaclar varsa, survival/safety degerlerine odaklanmak gerekir
        safety_values = self.value_system.get_values_by_category(ValueCategory.MORAL)
        if safety_values:
            return 0.7  # Degerler var ama ihtiyaclar kritik

        return 0.5  # Uyumsuzluk

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================

    def _generate_recommendations(
        self,
        need_analysis: Dict[str, Any],
        value_analysis: Dict[str, Any],
        goal_analysis: Dict[str, Any],
        integrity_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Oneriler olustur."""
        actions = []
        values = []
        needs = []

        # Kritik ihtiyaclar
        if need_analysis["critical_count"] > 0:
            for need in need_analysis["critical_needs"]:
                needs.append(need)
                actions.append(f"Address critical need: {need}")

        # Bayat hedefler
        if goal_analysis["stale_count"] > 0:
            actions.append(f"Review stale goals: {', '.join(goal_analysis['stale_goals'])}")

        # Deger cakismalari
        if value_analysis["conflict_count"] > 0:
            actions.append("Resolve value conflicts")

        # Tutarlilik sorunlari
        if integrity_result["score"] < 0.7:
            actions.append("Address integrity concerns")
            for concern in integrity_result["concerns"][:2]:
                actions.append(f"- {concern}")

        # Ifade edilecek degerler
        core_values = self.value_system.get_core_values()
        for value in core_values[:2]:
            if value.expression_count < 3:  # Az ifade edilmis
                values.append(value.name)

        return {
            "actions": actions,
            "values": values,
            "needs": needs,
        }

    # ========================================================================
    # TIME EFFECTS
    # ========================================================================

    def _apply_time_effects(self, hours: float) -> None:
        """Zaman etkilerini uygula."""
        # Ihtiyac decay
        self.need_manager.apply_time_decay(hours)

        # Trait decay
        self.identity_manager.apply_trait_decay(hours)

        # Goal decay
        self.goal_manager.apply_progress_decay(hours)

    # ========================================================================
    # NARRATIVE
    # ========================================================================

    def _check_for_significant_events(self, context: Dict[str, Any]) -> None:
        """Onemli olaylari kontrol et ve narrative olustur."""
        significance = context.get("event_significance", 0.0)

        if significance >= self.config.significant_event_threshold:
            self._stats["significant_events"] += 1
            # Otomatik narrative olusturma
            event = context.get("event_description", "Significant event occurred")
            self.add_narrative_element(
                title=f"Event: {event[:30]}",
                narrative_type=NarrativeType.LESSON,
                summary=event,
                meaning=context.get("event_meaning", ""),
            )

    def add_narrative_element(
        self,
        title: str,
        narrative_type: NarrativeType = NarrativeType.LESSON,
        summary: str = "",
        meaning: str = "",
        emotional_valence: float = 0.0,
        emotional_intensity: float = 0.5,
    ) -> NarrativeElement:
        """
        Hikaye ogesi ekle.

        Args:
            title: Baslik
            narrative_type: Hikaye turu
            summary: Ozet
            meaning: Anlam
            emotional_valence: Duygusal deger
            emotional_intensity: Duygusal yogunluk

        Returns:
            Olusturulan oge
        """
        element = NarrativeElement(
            title=title,
            narrative_type=narrative_type,
            summary=summary,
            meaning=meaning,
            emotional_valence=emotional_valence,
            emotional_intensity=emotional_intensity,
        )

        self.self_state.add_narrative_element(element)
        self._stats["narratives_created"] += 1

        return element

    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================

    def express_value(self, value_name: str) -> bool:
        """Degeri ifade et."""
        return self.value_system.express_value_by_name(value_name)

    def satisfy_need(self, need_name: str, amount: float = 0.3) -> bool:
        """Ihtiyaci karila."""
        return self.need_manager.satisfy_need_by_name(need_name, amount)

    def reinforce_trait(self, trait_name: str, amount: float = 0.1) -> bool:
        """Kimlik ozelligini guclendir."""
        trait = self.identity_manager.find_trait_by_name(trait_name)
        if trait:
            return self.identity_manager.reinforce_trait(trait.id, amount)
        return False

    def progress_goal(self, goal_name: str, amount: float = 0.1) -> bool:
        """Hedefte ilerleme kaydet."""
        for goal in self.goal_manager.goals.values():
            if goal.name.lower() == goal_name.lower():
                return self.goal_manager.increment_progress(goal.id, amount)
        return False

    def get_self_description(self) -> str:
        """Benlik tanimi getir."""
        return self.identity_manager.generate_self_description()

    # ========================================================================
    # STATISTICS & STATE
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Tum istatistikleri getir."""
        return {
            "processor": self._stats.copy(),
            "identity": self.identity_manager.get_stats(),
            "goals": self.goal_manager.get_stats(),
            "needs": self.need_manager.get_stats(),
            "values": self.value_system.get_stats(),
        }

    def get_self_state(self) -> SelfState:
        """Benlik durumunu getir."""
        self._sync_state()
        return self.self_state

    def summary(self) -> Dict[str, Any]:
        """Genel ozet."""
        return {
            "identity": {
                "name": self.self_state.identity.name,
                "strength": self.self_state.identity.identity_strength,
                "stability": self.self_state.identity.identity_stability,
                "roles": self.self_state.identity.roles,
            },
            "values": self.value_system.summary(),
            "needs": self.need_manager.summary(),
            "goals": self.goal_manager.summary(),
            "integrity": {
                "status": self.self_state.integrity_status.value,
                "score": self.self_state.integrity_score,
            },
            "cycle_count": self._cycle_count,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_self_processor(
    config: Optional[SelfProcessorConfig] = None,
) -> SelfProcessor:
    """SelfProcessor factory."""
    return SelfProcessor(config)


def get_self_processor() -> SelfProcessor:
    """Singleton benzeri global processor."""
    if not hasattr(get_self_processor, "_instance"):
        get_self_processor._instance = SelfProcessor()
    return get_self_processor._instance


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SelfProcessorConfig",
    "SelfOutput",
    "SelfProcessor",
    "create_self_processor",
    "get_self_processor",
]
