"""
UEM v2 - Personal Goals Module

Kisisel hedef yonetimi.
Agent'in bireysel gelisim ve anlam hedeflerini yonetir.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .types import (
    PersonalGoal,
    GoalDomain,
    Value,
    Need,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PersonalGoalConfig:
    """Kisisel hedef modulu yapilandirmasi."""
    # Hedef limitleri
    max_active_goals: int = 5
    max_goals_per_domain: int = 3

    # Motivasyon parametreleri
    min_motivation_threshold: float = 0.2
    intrinsic_weight: float = 0.7
    extrinsic_weight: float = 0.3

    # Ilerleme parametreleri
    progress_decay_rate: float = 0.01  # Calismazsa gerileme
    milestone_bonus: float = 0.1

    # Zaman parametreleri
    stale_goal_days: float = 30.0  # Bu kadar gun ilerleme yoksa bayat


# ============================================================================
# PERSONAL GOAL MANAGER
# ============================================================================

class PersonalGoalManager:
    """
    Kisisel hedef yoneticisi.

    Agent'in bireysel hedeflerini olusturur, izler ve gunceller.
    """

    def __init__(self, config: Optional[PersonalGoalConfig] = None):
        """
        PersonalGoalManager baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or PersonalGoalConfig()
        self.goals: Dict[str, PersonalGoal] = {}

        # Istatistikler
        self._stats = {
            "goals_created": 0,
            "goals_completed": 0,
            "goals_abandoned": 0,
            "milestones_achieved": 0,
        }

    # ========================================================================
    # GOAL CREATION
    # ========================================================================

    def create_goal(
        self,
        name: str,
        description: str = "",
        domain: GoalDomain = GoalDomain.GROWTH,
        milestones: Optional[List[str]] = None,
        related_values: Optional[List[str]] = None,
        related_needs: Optional[List[str]] = None,
        intrinsic_motivation: float = 0.7,
        extrinsic_motivation: float = 0.3,
        target_date: Optional[datetime] = None,
    ) -> Optional[PersonalGoal]:
        """
        Yeni kisisel hedef olustur.

        Args:
            name: Hedef ismi
            description: Aciklama
            domain: Hedef alani
            milestones: Ara hedefler
            related_values: Iliskili degerler
            related_needs: Iliskili ihtiyaclar
            intrinsic_motivation: Icsel motivasyon
            extrinsic_motivation: Disal motivasyon
            target_date: Hedef tarihi

        Returns:
            Olusturulan hedef veya None
        """
        # Aktif hedef limiti kontrolu
        active_goals = self.get_active_goals()
        if len(active_goals) >= self.config.max_active_goals:
            return None

        # Domain limiti kontrolu
        domain_goals = [g for g in active_goals if g.domain == domain]
        if len(domain_goals) >= self.config.max_goals_per_domain:
            return None

        goal = PersonalGoal(
            name=name,
            description=description,
            domain=domain,
            milestones=milestones or [],
            related_values=related_values or [],
            related_needs=related_needs or [],
            intrinsic_motivation=intrinsic_motivation,
            extrinsic_motivation=extrinsic_motivation,
            target_date=target_date,
            commitment=0.5,
            is_active=True,
        )

        self.goals[goal.id] = goal
        self._stats["goals_created"] += 1

        return goal

    def create_goal_from_value(
        self,
        value: Value,
        goal_name: str,
        description: str = "",
    ) -> Optional[PersonalGoal]:
        """
        Degerden hedef olustur.

        Args:
            value: Kaynak deger
            goal_name: Hedef ismi
            description: Aciklama

        Returns:
            Olusturulan hedef
        """
        # Deger kategorisine gore domain belirle
        domain_map = {
            "terminal": GoalDomain.MEANING,
            "instrumental": GoalDomain.GROWTH,
            "moral": GoalDomain.CONTRIBUTION,
            "aesthetic": GoalDomain.MASTERY,
            "epistemic": GoalDomain.GROWTH,
        }
        domain = domain_map.get(value.category.value, GoalDomain.GROWTH)

        return self.create_goal(
            name=goal_name,
            description=description or f"Goal aligned with value: {value.name}",
            domain=domain,
            related_values=[value.id],
            intrinsic_motivation=value.priority_weight,
        )

    def create_goal_from_need(
        self,
        need: Need,
        goal_name: str,
        description: str = "",
    ) -> Optional[PersonalGoal]:
        """
        Ihtiyactan hedef olustur.

        Args:
            need: Kaynak ihtiyac
            goal_name: Hedef ismi
            description: Aciklama

        Returns:
            Olusturulan hedef
        """
        # Ihtiyac seviyesine gore domain belirle
        domain_map = {
            "physiological": GoalDomain.AUTONOMY,
            "safety": GoalDomain.AUTONOMY,
            "belonging": GoalDomain.RELATIONSHIP,
            "esteem": GoalDomain.MASTERY,
            "self_actualization": GoalDomain.MEANING,
        }
        domain = domain_map.get(need.level.value, GoalDomain.GROWTH)

        # Ihtiyac eksikligi yuksekse motivasyon yuksek
        motivation = 1.0 - need.satisfaction

        return self.create_goal(
            name=goal_name,
            description=description or f"Goal to satisfy need: {need.name}",
            domain=domain,
            related_needs=[need.id],
            intrinsic_motivation=motivation,
            extrinsic_motivation=need.importance,
        )

    # ========================================================================
    # GOAL RETRIEVAL
    # ========================================================================

    def get_goal(self, goal_id: str) -> Optional[PersonalGoal]:
        """Hedefi getir."""
        return self.goals.get(goal_id)

    def get_active_goals(self) -> List[PersonalGoal]:
        """Aktif hedefleri getir."""
        return [g for g in self.goals.values() if g.is_active]

    def get_goals_by_domain(self, domain: GoalDomain) -> List[PersonalGoal]:
        """Domaine gore hedefleri getir."""
        return [g for g in self.goals.values() if g.domain == domain and g.is_active]

    def get_highest_motivation_goal(self) -> Optional[PersonalGoal]:
        """En yuksek motivasyonlu hedefi getir."""
        active = self.get_active_goals()
        if not active:
            return None
        return max(active, key=lambda g: g.total_motivation)

    def get_goals_by_value(self, value_id: str) -> List[PersonalGoal]:
        """Belirli bir degerle iliskili hedefleri getir."""
        return [g for g in self.goals.values()
                if value_id in g.related_values and g.is_active]

    def get_goals_by_need(self, need_id: str) -> List[PersonalGoal]:
        """Belirli bir ihtiyacla iliskili hedefleri getir."""
        return [g for g in self.goals.values()
                if need_id in g.related_needs and g.is_active]

    def get_stale_goals(self) -> List[PersonalGoal]:
        """Bayat hedefleri getir (uzun suredir ilerleme yok)."""
        stale = []
        now = datetime.now()
        stale_threshold = self.config.stale_goal_days * 24 * 3600  # saniye

        for goal in self.get_active_goals():
            if goal.last_progress:
                elapsed = (now - goal.last_progress).total_seconds()
                if elapsed > stale_threshold:
                    stale.append(goal)
            else:
                # Hic ilerleme olmamis, olusturma tarihine bak
                elapsed = (now - goal.created_at).total_seconds()
                if elapsed > stale_threshold:
                    stale.append(goal)

        return stale

    # ========================================================================
    # GOAL PROGRESS
    # ========================================================================

    def update_progress(self, goal_id: str, new_progress: float) -> bool:
        """
        Hedef ilerlemesini guncelle.

        Args:
            goal_id: Hedef ID
            new_progress: Yeni ilerleme (0.0-1.0)

        Returns:
            Basarili mi
        """
        goal = self.get_goal(goal_id)
        if not goal or not goal.is_active:
            return False

        goal.update_progress(new_progress)

        # Tamamlandi mi?
        if goal.progress >= 1.0:
            self.complete_goal(goal_id)

        return True

    def achieve_milestone(self, goal_id: str, milestone: str) -> bool:
        """
        Milestone tamamla.

        Args:
            goal_id: Hedef ID
            milestone: Milestone ismi

        Returns:
            Basarili mi
        """
        goal = self.get_goal(goal_id)
        if not goal or not goal.is_active:
            return False

        if milestone not in goal.milestones:
            return False

        if milestone in goal.achieved_milestones:
            return True  # Zaten tamamlanmis

        goal.achieve_milestone(milestone)
        self._stats["milestones_achieved"] += 1

        # Commitment artisi
        goal.commitment = min(1.0, goal.commitment + self.config.milestone_bonus)

        return True

    def increment_progress(self, goal_id: str, amount: float = 0.1) -> bool:
        """
        Ilerlemeyi artir.

        Args:
            goal_id: Hedef ID
            amount: Artis miktari

        Returns:
            Basarili mi
        """
        goal = self.get_goal(goal_id)
        if not goal or not goal.is_active:
            return False

        new_progress = min(1.0, goal.progress + amount)
        return self.update_progress(goal_id, new_progress)

    # ========================================================================
    # GOAL LIFECYCLE
    # ========================================================================

    def complete_goal(self, goal_id: str) -> bool:
        """
        Hedefi tamamla.

        Args:
            goal_id: Hedef ID

        Returns:
            Basarili mi
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return False

        goal.is_active = False
        goal.progress = 1.0
        self._stats["goals_completed"] += 1

        return True

    def abandon_goal(self, goal_id: str) -> bool:
        """
        Hedefi terk et.

        Args:
            goal_id: Hedef ID

        Returns:
            Basarili mi
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return False

        goal.is_active = False
        self._stats["goals_abandoned"] += 1

        return True

    def reactivate_goal(self, goal_id: str) -> bool:
        """
        Hedefi yeniden aktifle.

        Args:
            goal_id: Hedef ID

        Returns:
            Basarili mi
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return False

        # Aktif hedef limiti kontrolu
        if len(self.get_active_goals()) >= self.config.max_active_goals:
            return False

        goal.is_active = True
        return True

    # ========================================================================
    # MOTIVATION MANAGEMENT
    # ========================================================================

    def update_commitment(self, goal_id: str, delta: float) -> bool:
        """
        Baglilik guncelle.

        Args:
            goal_id: Hedef ID
            delta: Degisim

        Returns:
            Basarili mi
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return False

        goal.commitment = max(0.0, min(1.0, goal.commitment + delta))

        # Cok dusuk baglilik = hedef tehlikede
        if goal.commitment < self.config.min_motivation_threshold:
            # Uyari: hedef terk edilebilir
            pass

        return True

    def boost_intrinsic_motivation(self, goal_id: str, amount: float = 0.1) -> bool:
        """Icsel motivasyonu artir."""
        goal = self.get_goal(goal_id)
        if not goal:
            return False

        goal.intrinsic_motivation = min(1.0, goal.intrinsic_motivation + amount)
        return True

    def get_motivation_report(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """
        Hedef motivasyon raporu.

        Args:
            goal_id: Hedef ID

        Returns:
            Motivasyon raporu
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return None

        return {
            "goal_name": goal.name,
            "total_motivation": goal.total_motivation,
            "intrinsic_motivation": goal.intrinsic_motivation,
            "extrinsic_motivation": goal.extrinsic_motivation,
            "commitment": goal.commitment,
            "progress": goal.progress,
            "milestone_progress": goal.milestone_progress,
            "is_stale": goal in self.get_stale_goals(),
            "at_risk": goal.commitment < self.config.min_motivation_threshold,
        }

    # ========================================================================
    # GOAL PRIORITIZATION
    # ========================================================================

    def prioritize_goals(self) -> List[PersonalGoal]:
        """
        Hedefleri onceliklendir.

        Returns:
            Oncelik sirasina gore hedefler
        """
        active = self.get_active_goals()

        def priority_score(goal: PersonalGoal) -> float:
            motivation = goal.total_motivation
            urgency = 1.0 if goal.target_date else 0.5
            progress_factor = 1.0 - goal.progress  # Yakin olana oncelik
            return motivation * urgency * (1.0 + progress_factor * 0.5)

        return sorted(active, key=priority_score, reverse=True)

    def suggest_focus_goal(self) -> Optional[PersonalGoal]:
        """
        Odaklanilmasi gereken hedefi oner.

        Returns:
            Onerilen hedef
        """
        prioritized = self.prioritize_goals()
        return prioritized[0] if prioritized else None

    # ========================================================================
    # GOAL DECAY
    # ========================================================================

    def apply_progress_decay(self, hours_passed: float = 1.0) -> List[str]:
        """
        Ilerleme gerilmesi uygula (calisilmayan hedefler geriler).

        Args:
            hours_passed: Gecen saat

        Returns:
            Etkilenen hedef isimleri
        """
        affected = []
        decay = self.config.progress_decay_rate * hours_passed

        for goal in self.get_active_goals():
            # Yuksek commitment decay'i azaltir
            effective_decay = decay * (1.0 - goal.commitment * 0.5)
            if goal.progress > 0 and effective_decay > 0:
                goal.progress = max(0.0, goal.progress - effective_decay)
                affected.append(goal.name)

        return affected

    # ========================================================================
    # STATISTICS & STATE
    # ========================================================================

    def get_stats(self) -> Dict[str, int]:
        """Istatistikleri getir."""
        return self._stats.copy()

    def get_completion_rate(self) -> float:
        """Tamamlanma oranini getir."""
        created = self._stats["goals_created"]
        if created == 0:
            return 0.0
        return self._stats["goals_completed"] / created

    def summary(self) -> Dict[str, Any]:
        """Ozet bilgi."""
        active = self.get_active_goals()
        return {
            "total_goals": len(self.goals),
            "active_goals": len(active),
            "completed_goals": self._stats["goals_completed"],
            "abandoned_goals": self._stats["goals_abandoned"],
            "milestones_achieved": self._stats["milestones_achieved"],
            "completion_rate": self.get_completion_rate(),
            "avg_progress": sum(g.progress for g in active) / len(active) if active else 0.0,
            "stale_goals": len(self.get_stale_goals()),
            "focus_goal": self.suggest_focus_goal().name if self.suggest_focus_goal() else None,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_personal_goal_manager(
    config: Optional[PersonalGoalConfig] = None,
) -> PersonalGoalManager:
    """PersonalGoalManager factory."""
    return PersonalGoalManager(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "PersonalGoalConfig",
    "PersonalGoalManager",
    "create_personal_goal_manager",
]
