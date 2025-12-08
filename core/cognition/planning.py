"""
UEM v2 - Planning Module

Eylem planlama ve hedef yönetimi.

Kullanım:
    from core.cognition.planning import ActionPlanner, GoalManager

    planner = ActionPlanner()
    plan = planner.create_plan(goal, state, context)

    goal_manager = GoalManager()
    goal_manager.add_goal(goal)
    active = goal_manager.get_prioritized_goals()
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
import logging
import time
import uuid

from foundation.state import StateVector, SVField

from .types import (
    Goal, GoalType, GoalPriority, GoalStatus,
    Plan, PlanStep,
    Intention, IntentionStrength,
    Belief,
    SituationAssessment, RiskLevel,
    CognitiveState,
)


logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PlanningConfig:
    """Planlama yapılandırması."""

    # Plan limitleri
    max_plan_steps: int = 10             # Maksimum plan adımı
    max_concurrent_goals: int = 5        # Aynı anda aktif hedef
    max_plans_per_goal: int = 3          # Hedef başına plan

    # Planlama kalitesi
    min_plan_feasibility: float = 0.3    # Minimum uygulanabilirlik
    safety_margin: float = 0.2           # Güvenlik marjı

    # Önceliklendirme
    urgency_weight: float = 0.4
    utility_weight: float = 0.3
    feasibility_weight: float = 0.3

    # Replanning
    replan_on_failure: bool = True
    max_replan_attempts: int = 2


# ============================================================================
# ACTION TEMPLATES
# ============================================================================

@dataclass
class ActionTemplate:
    """Eylem şablonu."""
    action_type: str
    name: str
    description: str

    # Gereksinimler
    preconditions: List[str] = field(default_factory=list)
    resource_cost: float = 0.1           # 0-1 kaynak maliyeti

    # Etkiler
    expected_effects: List[str] = field(default_factory=list)
    risk_level: float = 0.1              # 0-1 risk

    # Uygulanabilirlik
    applicable_goals: List[GoalType] = field(default_factory=list)
    min_resource: float = 0.1            # Minimum kaynak gereksinimi
    max_threat: float = 1.0              # Maksimum tehdit seviyesi


# Önceden tanımlı eylem şablonları
BUILTIN_ACTIONS: Dict[str, ActionTemplate] = {
    "flee": ActionTemplate(
        action_type="flee",
        name="Flee",
        description="Escape from danger",
        preconditions=["threat_detected"],
        resource_cost=0.2,
        expected_effects=["distance_increased", "threat_reduced"],
        risk_level=0.3,
        applicable_goals=[GoalType.SURVIVAL, GoalType.AVOIDANCE],
        min_resource=0.1,
    ),
    "defend": ActionTemplate(
        action_type="defend",
        name="Defend",
        description="Defend against threat",
        preconditions=["threat_detected", "resource_sufficient"],
        resource_cost=0.3,
        expected_effects=["threat_mitigated"],
        risk_level=0.5,
        applicable_goals=[GoalType.SURVIVAL],
        min_resource=0.3,
    ),
    "approach": ActionTemplate(
        action_type="approach",
        name="Approach",
        description="Move toward target",
        preconditions=["target_identified"],
        resource_cost=0.1,
        expected_effects=["distance_decreased"],
        risk_level=0.2,
        applicable_goals=[GoalType.ACHIEVEMENT, GoalType.SOCIAL, GoalType.EXPLORATION],
        min_resource=0.1,
        max_threat=0.6,
    ),
    "observe": ActionTemplate(
        action_type="observe",
        name="Observe",
        description="Gather information",
        preconditions=[],
        resource_cost=0.05,
        expected_effects=["information_gathered"],
        risk_level=0.1,
        applicable_goals=[GoalType.EXPLORATION, GoalType.MAINTENANCE],
        min_resource=0.05,
    ),
    "communicate": ActionTemplate(
        action_type="communicate",
        name="Communicate",
        description="Interact with agent",
        preconditions=["agent_present"],
        resource_cost=0.1,
        expected_effects=["social_interaction"],
        risk_level=0.2,
        applicable_goals=[GoalType.SOCIAL],
        min_resource=0.1,
        max_threat=0.5,
    ),
    "wait": ActionTemplate(
        action_type="wait",
        name="Wait",
        description="Wait and conserve",
        preconditions=[],
        resource_cost=0.02,
        expected_effects=["time_passed", "energy_conserved"],
        risk_level=0.05,
        applicable_goals=[GoalType.MAINTENANCE, GoalType.AVOIDANCE],
        min_resource=0.0,
    ),
    "seek_resource": ActionTemplate(
        action_type="seek_resource",
        name="Seek Resource",
        description="Search for resources",
        preconditions=["resource_low"],
        resource_cost=0.15,
        expected_effects=["resource_found"],
        risk_level=0.2,
        applicable_goals=[GoalType.SURVIVAL, GoalType.MAINTENANCE],
        min_resource=0.1,
        max_threat=0.4,
    ),
    "rest": ActionTemplate(
        action_type="rest",
        name="Rest",
        description="Recover energy",
        preconditions=["safe_location"],
        resource_cost=0.0,
        expected_effects=["wellbeing_increased", "energy_recovered"],
        risk_level=0.1,
        applicable_goals=[GoalType.MAINTENANCE],
        min_resource=0.0,
        max_threat=0.3,
    ),
}


# ============================================================================
# GOAL MANAGER
# ============================================================================

class GoalManager:
    """
    Hedef yöneticisi.

    Hedefleri oluşturur, önceliklendirir ve durumlarını yönetir.
    """

    def __init__(self, config: Optional[PlanningConfig] = None):
        self.config = config or PlanningConfig()
        self._goals: Dict[str, Goal] = {}
        self._goal_history: List[Tuple[str, GoalStatus, datetime]] = []

    # ========================================================================
    # GOAL CRUD
    # ========================================================================

    def add_goal(self, goal: Goal) -> str:
        """Hedef ekle."""
        if len(self.get_active_goals()) >= self.config.max_concurrent_goals:
            # En düşük öncelikli aktif hedefi askıya al
            lowest = self._get_lowest_priority_active()
            if lowest and goal.importance > lowest.importance:
                self.suspend_goal(lowest.id)
            else:
                logger.warning(f"Cannot add goal {goal.id}: max concurrent reached")
                return ""

        self._goals[goal.id] = goal
        self._goal_history.append((goal.id, goal.status, datetime.now()))
        logger.debug(f"Added goal: {goal.id} ({goal.name})")
        return goal.id

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Hedefi getir."""
        return self._goals.get(goal_id)

    def remove_goal(self, goal_id: str) -> bool:
        """Hedefi kaldır."""
        if goal_id in self._goals:
            del self._goals[goal_id]
            return True
        return False

    def update_goal_status(self, goal_id: str, status: GoalStatus) -> bool:
        """Hedef durumunu güncelle."""
        goal = self._goals.get(goal_id)
        if goal:
            goal.status = status
            self._goal_history.append((goal_id, status, datetime.now()))
            return True
        return False

    # ========================================================================
    # GOAL QUERIES
    # ========================================================================

    def get_active_goals(self) -> List[Goal]:
        """Aktif hedefleri getir."""
        return [g for g in self._goals.values() if g.status == GoalStatus.ACTIVE]

    def get_pending_goals(self) -> List[Goal]:
        """Bekleyen hedefleri getir."""
        return [g for g in self._goals.values() if g.status == GoalStatus.PENDING]

    def get_prioritized_goals(self) -> List[Goal]:
        """Önceliklendirilmiş hedef listesi."""
        active = self.get_active_goals()
        return sorted(active, key=lambda g: g.importance, reverse=True)

    def get_highest_priority_goal(self) -> Optional[Goal]:
        """En yüksek öncelikli hedefi getir."""
        prioritized = self.get_prioritized_goals()
        return prioritized[0] if prioritized else None

    def _get_lowest_priority_active(self) -> Optional[Goal]:
        """En düşük öncelikli aktif hedef."""
        active = self.get_active_goals()
        if not active:
            return None
        return min(active, key=lambda g: g.importance)

    # ========================================================================
    # GOAL LIFECYCLE
    # ========================================================================

    def activate_goal(self, goal_id: str) -> bool:
        """Hedefi aktifleştir."""
        return self.update_goal_status(goal_id, GoalStatus.ACTIVE)

    def suspend_goal(self, goal_id: str) -> bool:
        """Hedefi askıya al."""
        return self.update_goal_status(goal_id, GoalStatus.SUSPENDED)

    def complete_goal(self, goal_id: str) -> bool:
        """Hedefi tamamla."""
        goal = self._goals.get(goal_id)
        if goal:
            goal.progress = 1.0
            return self.update_goal_status(goal_id, GoalStatus.ACHIEVED)
        return False

    def fail_goal(self, goal_id: str) -> bool:
        """Hedefi başarısız yap."""
        goal = self._goals.get(goal_id)
        if goal:
            goal.attempts += 1
            return self.update_goal_status(goal_id, GoalStatus.FAILED)
        return False

    # ========================================================================
    # GOAL CREATION HELPERS
    # ========================================================================

    def create_survival_goal(
        self,
        threat_source: str,
        priority: GoalPriority = GoalPriority.CRITICAL,
    ) -> Goal:
        """Hayatta kalma hedefi oluştur."""
        goal = Goal(
            id=str(uuid.uuid4())[:8],
            name=f"survive_{threat_source}",
            description=f"Survive threat from {threat_source}",
            goal_type=GoalType.SURVIVAL,
            priority=priority,
            status=GoalStatus.ACTIVE,
            success_conditions=[f"threat_{threat_source}_eliminated"],
            utility=1.0,
            urgency=0.9,
        )
        return goal

    def create_resource_goal(
        self,
        resource_type: str = "general",
        priority: GoalPriority = GoalPriority.HIGH,
    ) -> Goal:
        """Kaynak edinme hedefi oluştur."""
        goal = Goal(
            id=str(uuid.uuid4())[:8],
            name=f"acquire_{resource_type}",
            description=f"Acquire {resource_type} resources",
            goal_type=GoalType.ACHIEVEMENT,
            priority=priority,
            status=GoalStatus.PENDING,
            success_conditions=["resource_level_sufficient"],
            utility=0.7,
            urgency=0.5,
        )
        return goal

    def create_social_goal(
        self,
        agent_id: str,
        interaction_type: str = "communicate",
    ) -> Goal:
        """Sosyal hedef oluştur."""
        goal = Goal(
            id=str(uuid.uuid4())[:8],
            name=f"{interaction_type}_with_{agent_id}",
            description=f"{interaction_type.capitalize()} with agent {agent_id}",
            goal_type=GoalType.SOCIAL,
            priority=GoalPriority.NORMAL,
            status=GoalStatus.PENDING,
            preconditions=[f"agent_{agent_id}_present"],
            success_conditions=[f"{interaction_type}_completed"],
            utility=0.5,
            urgency=0.3,
        )
        return goal


# ============================================================================
# ACTION PLANNER
# ============================================================================

class ActionPlanner:
    """
    Eylem planlayıcı.

    Hedeflere ulaşmak için plan oluşturur.
    """

    def __init__(self, config: Optional[PlanningConfig] = None):
        self.config = config or PlanningConfig()
        self.action_templates = dict(BUILTIN_ACTIONS)
        self._plan_cache: Dict[str, Plan] = {}

    # ========================================================================
    # PLAN CREATION
    # ========================================================================

    def create_plan(
        self,
        goal: Goal,
        state: StateVector,
        context: Optional[Dict[str, Any]] = None,
        assessment: Optional[SituationAssessment] = None,
    ) -> Optional[Plan]:
        """
        Hedef için plan oluştur.

        Args:
            goal: Hedef
            state: Mevcut durum
            context: Ek bağlam
            assessment: Durum değerlendirmesi

        Returns:
            Plan veya None
        """
        context = context or {}
        start_time = time.time()

        logger.debug(f"Creating plan for goal: {goal.name}")

        # 1. Uygulanabilir eylemleri bul
        applicable_actions = self._get_applicable_actions(goal, state)

        if not applicable_actions:
            logger.debug(f"No applicable actions for goal {goal.name}")
            return None

        # 2. Plan oluştur
        plan = Plan(
            id=str(uuid.uuid4())[:8],
            goal_id=goal.id,
            name=f"plan_for_{goal.name}",
            status="draft",
        )

        # 3. Adımları ekle (basit sıralı planlama)
        steps = self._generate_steps(goal, applicable_actions, state, assessment)

        for step_data in steps:
            plan.add_step(
                action=step_data["action"],
                target=step_data.get("target"),
                parameters=step_data.get("parameters", {}),
                preconditions=step_data.get("preconditions", []),
                expected_effects=step_data.get("expected_effects", []),
            )

        # 4. Plan kalitesini hesapla
        plan.feasibility = self._calculate_feasibility(plan, state, assessment)
        plan.expected_success = self._calculate_success_probability(plan, state)
        plan.estimated_cost = self._calculate_cost(plan)

        # 5. Kontrol
        if plan.feasibility < self.config.min_plan_feasibility:
            logger.debug(
                f"Plan feasibility too low: {plan.feasibility:.2f} < "
                f"{self.config.min_plan_feasibility}"
            )
            return None

        plan.status = "ready"

        elapsed = (time.time() - start_time) * 1000
        logger.debug(
            f"Plan created: {len(plan.steps)} steps, "
            f"feasibility={plan.feasibility:.2f}, time={elapsed:.1f}ms"
        )

        return plan

    def _get_applicable_actions(
        self,
        goal: Goal,
        state: StateVector,
    ) -> List[ActionTemplate]:
        """Hedef ve duruma uygun eylemleri bul."""
        applicable = []

        for action in self.action_templates.values():
            # Hedef türü kontrolü
            if goal.goal_type not in action.applicable_goals:
                continue

            # Kaynak kontrolü
            if state.resource < action.min_resource:
                continue

            # Tehdit kontrolü
            if state.threat > action.max_threat:
                continue

            applicable.append(action)

        return applicable

    def _generate_steps(
        self,
        goal: Goal,
        actions: List[ActionTemplate],
        state: StateVector,
        assessment: Optional[SituationAssessment],
    ) -> List[Dict[str, Any]]:
        """Plan adımlarını oluştur."""
        steps = []

        # Hedef türüne göre strateji
        if goal.goal_type == GoalType.SURVIVAL:
            steps = self._plan_survival(goal, actions, state)
        elif goal.goal_type == GoalType.AVOIDANCE:
            steps = self._plan_avoidance(goal, actions, state)
        elif goal.goal_type == GoalType.ACHIEVEMENT:
            steps = self._plan_achievement(goal, actions, state)
        elif goal.goal_type == GoalType.SOCIAL:
            steps = self._plan_social(goal, actions, state)
        elif goal.goal_type == GoalType.EXPLORATION:
            steps = self._plan_exploration(goal, actions, state)
        else:
            # Generic planlama
            steps = self._plan_generic(goal, actions, state)

        # Limit
        return steps[:self.config.max_plan_steps]

    def _plan_survival(
        self,
        goal: Goal,
        actions: List[ActionTemplate],
        state: StateVector,
    ) -> List[Dict[str, Any]]:
        """Hayatta kalma planı."""
        steps = []

        # Yüksek tehdit varsa önce kaç
        if state.threat > 0.6:
            flee = next((a for a in actions if a.action_type == "flee"), None)
            if flee:
                steps.append({
                    "action": "flee",
                    "expected_effects": flee.expected_effects,
                })

        # Tehdit orta ise savun
        if state.threat > 0.3:
            defend = next((a for a in actions if a.action_type == "defend"), None)
            if defend and state.resource >= defend.min_resource:
                steps.append({
                    "action": "defend",
                    "expected_effects": defend.expected_effects,
                })

        # Gözlem yap
        observe = next((a for a in actions if a.action_type == "observe"), None)
        if observe:
            steps.append({
                "action": "observe",
                "expected_effects": observe.expected_effects,
            })

        return steps

    def _plan_avoidance(
        self,
        goal: Goal,
        actions: List[ActionTemplate],
        state: StateVector,
    ) -> List[Dict[str, Any]]:
        """Kaçınma planı."""
        steps = []

        flee = next((a for a in actions if a.action_type == "flee"), None)
        if flee:
            steps.append({"action": "flee", "expected_effects": flee.expected_effects})

        wait = next((a for a in actions if a.action_type == "wait"), None)
        if wait:
            steps.append({"action": "wait", "expected_effects": wait.expected_effects})

        return steps

    def _plan_achievement(
        self,
        goal: Goal,
        actions: List[ActionTemplate],
        state: StateVector,
    ) -> List[Dict[str, Any]]:
        """Başarı planı."""
        steps = []

        # Gözlem
        observe = next((a for a in actions if a.action_type == "observe"), None)
        if observe:
            steps.append({"action": "observe", "expected_effects": observe.expected_effects})

        # Yaklaş
        approach = next((a for a in actions if a.action_type == "approach"), None)
        if approach:
            steps.append({"action": "approach", "expected_effects": approach.expected_effects})

        # Kaynak ara
        if state.resource < 0.5:
            seek = next((a for a in actions if a.action_type == "seek_resource"), None)
            if seek:
                steps.append({"action": "seek_resource", "expected_effects": seek.expected_effects})

        return steps

    def _plan_social(
        self,
        goal: Goal,
        actions: List[ActionTemplate],
        state: StateVector,
    ) -> List[Dict[str, Any]]:
        """Sosyal plan."""
        steps = []

        # Yaklaş
        approach = next((a for a in actions if a.action_type == "approach"), None)
        if approach:
            steps.append({"action": "approach", "expected_effects": approach.expected_effects})

        # İletişim kur
        communicate = next((a for a in actions if a.action_type == "communicate"), None)
        if communicate:
            steps.append({"action": "communicate", "expected_effects": communicate.expected_effects})

        return steps

    def _plan_exploration(
        self,
        goal: Goal,
        actions: List[ActionTemplate],
        state: StateVector,
    ) -> List[Dict[str, Any]]:
        """Keşif planı."""
        steps = []

        observe = next((a for a in actions if a.action_type == "observe"), None)
        if observe:
            steps.append({"action": "observe", "expected_effects": observe.expected_effects})

        approach = next((a for a in actions if a.action_type == "approach"), None)
        if approach and state.threat < 0.4:
            steps.append({"action": "approach", "expected_effects": approach.expected_effects})

        return steps

    def _plan_generic(
        self,
        goal: Goal,
        actions: List[ActionTemplate],
        state: StateVector,
    ) -> List[Dict[str, Any]]:
        """Genel plan."""
        steps = []

        # En düşük riskli eylemler
        sorted_actions = sorted(actions, key=lambda a: a.risk_level)

        for action in sorted_actions[:3]:
            steps.append({
                "action": action.action_type,
                "expected_effects": action.expected_effects,
            })

        return steps

    # ========================================================================
    # PLAN QUALITY
    # ========================================================================

    def _calculate_feasibility(
        self,
        plan: Plan,
        state: StateVector,
        assessment: Optional[SituationAssessment],
    ) -> float:
        """Plan uygulanabilirliğini hesapla."""
        if not plan.steps:
            return 0.0

        feasibility = 1.0

        # Her adımın maliyetini kontrol et
        cumulative_cost = 0.0
        for step in plan.steps:
            template = self.action_templates.get(step.action)
            if template:
                cumulative_cost += template.resource_cost
                # Risk faktörü
                feasibility *= (1 - template.risk_level * 0.2)

        # Kaynak yeterliliği
        if cumulative_cost > state.resource:
            feasibility *= (state.resource / cumulative_cost)

        # Tehdit faktörü
        if state.threat > 0.5:
            feasibility *= (1 - state.threat * 0.3)

        # Durum değerlendirmesi
        if assessment and assessment.risk_level == RiskLevel.CRITICAL:
            feasibility *= 0.5

        return max(0.0, min(1.0, feasibility))

    def _calculate_success_probability(
        self,
        plan: Plan,
        state: StateVector,
    ) -> float:
        """Başarı olasılığını hesapla."""
        if not plan.steps:
            return 0.0

        prob = 1.0

        for step in plan.steps:
            template = self.action_templates.get(step.action)
            if template:
                # Her eylem başarısız olabilir
                step_prob = 0.8 - (template.risk_level * 0.3)
                prob *= step_prob

        # Kaynak bonusu
        if state.resource > 0.7:
            prob *= 1.1

        # Wellbeing bonusu
        if state.wellbeing > 0.6:
            prob *= 1.05

        return max(0.0, min(1.0, prob))

    def _calculate_cost(self, plan: Plan) -> float:
        """Plan maliyetini hesapla."""
        cost = 0.0

        for step in plan.steps:
            template = self.action_templates.get(step.action)
            if template:
                cost += template.resource_cost

        return min(1.0, cost)

    # ========================================================================
    # ACTION MANAGEMENT
    # ========================================================================

    def add_action_template(self, template: ActionTemplate) -> None:
        """Eylem şablonu ekle."""
        self.action_templates[template.action_type] = template

    def get_available_actions(self, state: StateVector) -> List[str]:
        """Mevcut durumda uygulanabilir eylemleri getir."""
        available = []
        for action in self.action_templates.values():
            if (state.resource >= action.min_resource and
                state.threat <= action.max_threat):
                available.append(action.action_type)
        return available


# ============================================================================
# FACTORY & SINGLETON
# ============================================================================

_goal_manager: Optional[GoalManager] = None
_action_planner: Optional[ActionPlanner] = None


def get_goal_manager(config: Optional[PlanningConfig] = None) -> GoalManager:
    """Goal manager singleton'ı al veya oluştur."""
    global _goal_manager
    if _goal_manager is None:
        _goal_manager = GoalManager(config)
    return _goal_manager


def get_action_planner(config: Optional[PlanningConfig] = None) -> ActionPlanner:
    """Action planner singleton'ı al veya oluştur."""
    global _action_planner
    if _action_planner is None:
        _action_planner = ActionPlanner(config)
    return _action_planner


def create_goal_manager(config: Optional[PlanningConfig] = None) -> GoalManager:
    """Yeni goal manager oluştur."""
    return GoalManager(config)


def create_action_planner(config: Optional[PlanningConfig] = None) -> ActionPlanner:
    """Yeni action planner oluştur."""
    return ActionPlanner(config)
