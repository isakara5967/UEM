"""
UEM v2 - MetaMind Learning

Ogrenme yonetimi: "Nasil gelistebilirim?"
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import statistics

from .types import (
    LearningGoal,
    LearningGoalType,
    Insight,
    InsightType,
    Pattern,
    PatternType,
    CycleAnalysisResult,
    SeverityLevel,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class LearningManagerConfig:
    """LearningManager yapilandirmasi."""
    # Hedef olusturma
    auto_create_goals: bool = True             # Otomatik hedef olustur
    min_data_for_goal: int = 20                # Hedef icin min veri

    # Iyilestirme esikleri
    improvement_threshold: float = 0.1         # %10 iyilestirme = basari
    speed_improvement_target: float = 0.2      # %20 hiz artisi hedefi
    stability_target: float = 0.9              # %90 kararlilik hedefi

    # Hedef limitleri
    max_active_goals: int = 10                 # Max aktif hedef
    goal_timeout_hours: int = 168              # 7 gun sonra timeout

    # Adaptasyon
    adaptation_rate: float = 0.1               # Ogrenme hizi


# ============================================================================
# ADAPTATION STRATEGY
# ============================================================================

@dataclass
class AdaptationStrategy:
    """Adaptasyon stratejisi."""
    id: str = ""
    name: str = ""
    description: str = ""
    target_metric: str = ""
    current_value: float = 0.0
    target_value: float = 0.0
    tactics: List[str] = field(default_factory=list)
    confidence: float = 0.7
    priority: float = 0.5

    def __post_init__(self):
        if not self.id:
            self.id = f"strategy_{datetime.now().timestamp()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "target_metric": self.target_metric,
            "tactics": self.tactics,
            "confidence": self.confidence,
            "priority": self.priority,
        }


# ============================================================================
# LEARNING MANAGER
# ============================================================================

class LearningManager:
    """
    Ogrenme yoneticisi.

    Sistem performansini analiz ederek nasil gelistirilebilecegini belirler.
    """

    def __init__(self, config: Optional[LearningManagerConfig] = None):
        """
        LearningManager baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or LearningManagerConfig()

        # Aktif hedefler
        self._goals: Dict[str, LearningGoal] = {}

        # Tamamlanan hedefler
        self._achieved_goals: List[LearningGoal] = []

        # Adaptasyon stratejileri
        self._strategies: Dict[str, AdaptationStrategy] = {}

        # Metrik gecmisleri
        self._metric_histories: Dict[str, List[float]] = {}

        # Sayaclar
        self._goals_created = 0
        self._goals_achieved = 0

    # ========================================================================
    # GOAL MANAGEMENT
    # ========================================================================

    def create_goal(
        self,
        goal_type: LearningGoalType,
        name: str,
        description: str,
        target_metric: str,
        target_value: float,
        current_value: Optional[float] = None,
        strategy: Optional[str] = None,
        tactics: Optional[List[str]] = None,
    ) -> LearningGoal:
        """
        Ogrenme hedefi olustur.

        Args:
            goal_type: Hedef turu
            name: Hedef adi
            description: Aciklama
            target_metric: Hedef metrik
            target_value: Hedef deger
            current_value: Mevcut deger (otomatik hesaplanir)
            strategy: Strateji
            tactics: Taktikler

        Returns:
            LearningGoal
        """
        # Mevcut degeri gecmisten al
        if current_value is None:
            history = self._metric_histories.get(target_metric, [])
            current_value = statistics.mean(history[-20:]) if history else 0.0

        goal = LearningGoal(
            goal_type=goal_type,
            name=name,
            description=description,
            target_metric=target_metric,
            current_value=current_value,
            target_value=target_value,
            baseline_value=current_value,
            strategy=strategy,
            tactics=tactics or [],
        )

        self._goals[goal.id] = goal
        self._goals_created += 1

        # Limit kontrolu
        if len(self._goals) > self.config.max_active_goals:
            self._cleanup_old_goals()

        return goal

    def update_goal_progress(self, goal_id: str, new_value: float) -> Optional[LearningGoal]:
        """Hedef ilerlemesini guncelle."""
        if goal_id not in self._goals:
            return None

        goal = self._goals[goal_id]
        goal.update_progress(new_value)

        # Hedefe ulasildi mi?
        if goal.achieved:
            self._achieved_goals.append(goal)
            self._goals_achieved += 1
            del self._goals[goal_id]

        return goal

    def get_goal(self, goal_id: str) -> Optional[LearningGoal]:
        """Hedef getir."""
        return self._goals.get(goal_id)

    def get_active_goals(
        self,
        goal_type: Optional[LearningGoalType] = None,
    ) -> List[LearningGoal]:
        """Aktif hedefleri getir."""
        goals = list(self._goals.values())

        if goal_type:
            goals = [g for g in goals if g.goal_type == goal_type]

        return sorted(goals, key=lambda g: g.progress, reverse=True)

    def cancel_goal(self, goal_id: str) -> bool:
        """Hedefi iptal et."""
        if goal_id in self._goals:
            self._goals[goal_id].is_active = False
            del self._goals[goal_id]
            return True
        return False

    def _cleanup_old_goals(self) -> None:
        """Eski hedefleri temizle."""
        # En dusuk ilerlemeye sahip hedefi sil
        if self._goals:
            oldest = min(self._goals.values(), key=lambda g: (g.progress, g.created_at))
            del self._goals[oldest.id]

    # ========================================================================
    # AUTOMATIC GOAL GENERATION
    # ========================================================================

    def generate_goals_from_insights(
        self,
        insights: List[Insight],
    ) -> List[LearningGoal]:
        """
        Insight'lardan otomatik hedef uret.

        Args:
            insights: Insight listesi

        Returns:
            Olusturulan hedefler
        """
        if not self.config.auto_create_goals:
            return []

        new_goals = []

        for insight in insights:
            if not insight.actionable:
                continue

            goal = self._insight_to_goal(insight)
            if goal:
                new_goals.append(goal)

        return new_goals

    def _insight_to_goal(self, insight: Insight) -> Optional[LearningGoal]:
        """Insight'tan hedef olustur."""
        if insight.insight_type == InsightType.BOTTLENECK:
            # Hiz hedefi
            current = insight.evidence.get("duration_ms", 100)
            target = current * (1 - self.config.speed_improvement_target)

            return self.create_goal(
                goal_type=LearningGoalType.SPEED,
                name=f"Speed up: {insight.title}",
                description=insight.description,
                target_metric="duration_ms",
                target_value=target,
                current_value=current,
                strategy="Reduce processing time",
                tactics=[insight.recommended_action] if insight.recommended_action else [],
            )

        elif insight.insight_type == InsightType.WARNING:
            # Kararlilik hedefi
            return self.create_goal(
                goal_type=LearningGoalType.STABILITY,
                name=f"Stabilize: {insight.title}",
                description=insight.description,
                target_metric="success_rate",
                target_value=self.config.stability_target,
                current_value=0.8,  # Varsayilan
                strategy="Improve reliability",
                tactics=[insight.recommended_action] if insight.recommended_action else [],
            )

        elif insight.insight_type == InsightType.OPTIMIZATION:
            # Verimlilik hedefi
            return self.create_goal(
                goal_type=LearningGoalType.EFFICIENCY,
                name=f"Optimize: {insight.title}",
                description=insight.description,
                target_metric="efficiency",
                target_value=0.9,
                current_value=0.7,
                strategy="Improve efficiency",
                tactics=[insight.recommended_action] if insight.recommended_action else [],
            )

        return None

    def generate_goals_from_patterns(
        self,
        patterns: List[Pattern],
    ) -> List[LearningGoal]:
        """
        Pattern'lerden otomatik hedef uret.

        Args:
            patterns: Pattern listesi

        Returns:
            Olusturulan hedefler
        """
        if not self.config.auto_create_goals:
            return []

        new_goals = []

        for pattern in patterns:
            goal = self._pattern_to_goal(pattern)
            if goal:
                new_goals.append(goal)

        return new_goals

    def _pattern_to_goal(self, pattern: Pattern) -> Optional[LearningGoal]:
        """Pattern'den hedef olustur."""
        if pattern.pattern_type == PatternType.DEGRADATION:
            return self.create_goal(
                goal_type=LearningGoalType.SPEED,
                name=f"Reverse degradation: {pattern.name}",
                description=pattern.description,
                target_metric=pattern.affected_metric or "duration_ms",
                target_value=pattern.average_impact * 0.8 if pattern.average_impact > 0 else 100,
                strategy="Reverse performance degradation",
            )

        elif pattern.pattern_type == PatternType.OSCILLATION:
            return self.create_goal(
                goal_type=LearningGoalType.STABILITY,
                name=f"Stabilize oscillation: {pattern.name}",
                description=pattern.description,
                target_metric="stability",
                target_value=self.config.stability_target,
                current_value=1 - pattern.frequency,
                strategy="Reduce performance variance",
            )

        elif pattern.pattern_type == PatternType.RECURRING:
            if pattern.average_impact > 0:
                return self.create_goal(
                    goal_type=LearningGoalType.EFFICIENCY,
                    name=f"Break pattern: {pattern.name}",
                    description=pattern.description,
                    target_metric=pattern.affected_metric or "efficiency",
                    target_value=pattern.average_impact * 0.7,
                    strategy="Eliminate recurring issue",
                )

        return None

    # ========================================================================
    # METRIC TRACKING
    # ========================================================================

    def track_metric(self, metric_name: str, value: float) -> None:
        """Metrik izle."""
        if metric_name not in self._metric_histories:
            self._metric_histories[metric_name] = []

        self._metric_histories[metric_name].append(value)

        # Limit
        if len(self._metric_histories[metric_name]) > 1000:
            self._metric_histories[metric_name] = self._metric_histories[metric_name][-500:]

        # Ilgili hedefleri guncelle (kopya uzerinden iterasyon)
        goals_to_update = [
            (goal.id, goal.target_metric)
            for goal in list(self._goals.values())
        ]
        for goal_id, target_metric in goals_to_update:
            if target_metric == metric_name:
                self.update_goal_progress(goal_id, value)

    def track_analysis(self, analysis: CycleAnalysisResult) -> None:
        """Analiz sonucunu izle."""
        # Temel metrikler
        self.track_metric("duration_ms", analysis.total_duration_ms)
        self.track_metric("success_rate", 1.0 if analysis.success else 0.0)

        # Phase metrikleri
        for phase, duration in analysis.phase_durations.items():
            self.track_metric(f"phase_{phase}_ms", duration)

        # Performans skoru
        self.track_metric("performance_score", analysis.get_performance_score())

    # ========================================================================
    # ADAPTATION STRATEGIES
    # ========================================================================

    def suggest_adaptation(
        self,
        analysis: CycleAnalysisResult,
        insights: Optional[List[Insight]] = None,
        patterns: Optional[List[Pattern]] = None,
    ) -> Optional[AdaptationStrategy]:
        """
        Adaptasyon stratejisi oner.

        Args:
            analysis: Son analiz
            insights: Aktif insight'lar
            patterns: Tespit edilen pattern'ler

        Returns:
            Onerilen strateji
        """
        insights = insights or []
        patterns = patterns or []

        strategies = []

        # 1. Performans bazli strateji
        if analysis.total_duration_ms > 200:  # Yavas
            strategies.append(AdaptationStrategy(
                name="Speed Optimization",
                description="Reduce processing time",
                target_metric="duration_ms",
                current_value=analysis.total_duration_ms,
                target_value=analysis.total_duration_ms * 0.7,
                tactics=[
                    f"Optimize {analysis.slowest_phase} phase",
                    "Reduce unnecessary computations",
                    "Cache frequently used data",
                ],
                confidence=0.8,
                priority=0.7,
            ))

        # 2. Basarisizlik bazli strateji
        if not analysis.success:
            strategies.append(AdaptationStrategy(
                name="Reliability Improvement",
                description="Reduce failure rate",
                target_metric="success_rate",
                current_value=0.0,
                target_value=1.0,
                tactics=[
                    f"Fix issues in: {', '.join(analysis.failed_phases)}",
                    "Add error handling",
                    "Improve input validation",
                ],
                confidence=0.9,
                priority=0.9,
            ))

        # 3. Insight bazli stratejiler
        for insight in insights:
            if insight.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
                strategies.append(AdaptationStrategy(
                    name=f"Address: {insight.title[:30]}",
                    description=insight.description,
                    target_metric=insight.evidence.get("metric", "general"),
                    tactics=[insight.recommended_action] if insight.recommended_action else [],
                    confidence=insight.confidence,
                    priority=insight.get_priority(),
                ))

        # 4. Pattern bazli stratejiler
        for pattern in patterns:
            if pattern.pattern_type == PatternType.DEGRADATION:
                strategies.append(AdaptationStrategy(
                    name="Reverse Degradation",
                    description=pattern.description,
                    target_metric=pattern.affected_metric or "performance",
                    tactics=[
                        "Identify root cause",
                        "Revert recent changes if applicable",
                        "Profile and optimize",
                    ],
                    confidence=pattern.confidence,
                    priority=0.8,
                ))

        # En yuksek oncelikli stratejiyi sec
        if strategies:
            best = max(strategies, key=lambda s: s.priority * s.confidence)
            self._strategies[best.id] = best
            return best

        return None

    def get_active_strategies(self) -> List[AdaptationStrategy]:
        """Aktif stratejileri getir."""
        return sorted(
            self._strategies.values(),
            key=lambda s: s.priority,
            reverse=True,
        )

    # ========================================================================
    # LEARNING SUMMARY
    # ========================================================================

    def get_learning_summary(self) -> Dict[str, Any]:
        """Ogrenme ozeti."""
        active_goals = self.get_active_goals()

        # Ilerleme ortalamalari
        avg_progress = (
            sum(g.progress for g in active_goals) / len(active_goals)
            if active_goals else 0
        )

        # Hedef turleri dagilimi
        goal_types = {}
        for g in active_goals:
            t = g.goal_type.value
            goal_types[t] = goal_types.get(t, 0) + 1

        return {
            "active_goals": len(active_goals),
            "achieved_goals": self._goals_achieved,
            "average_progress": avg_progress,
            "goal_types": goal_types,
            "active_strategies": len(self._strategies),
            "metrics_tracked": list(self._metric_histories.keys()),
        }

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Istatistikleri getir."""
        return {
            "goals_created": self._goals_created,
            "goals_achieved": self._goals_achieved,
            "active_goals": len(self._goals),
            "achievement_rate": (
                self._goals_achieved / self._goals_created
                if self._goals_created > 0 else 0
            ),
            "strategies_generated": len(self._strategies),
        }

    def summary(self) -> Dict[str, Any]:
        """Genel ozet."""
        active_goals = self.get_active_goals()

        return {
            "active_goals": len(active_goals),
            "achieved_goals": self._goals_achieved,
            "top_goals": [g.to_dict() for g in active_goals[:5]],
            "strategies": [s.to_dict() for s in self.get_active_strategies()[:3]],
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_learning_manager(
    config: Optional[LearningManagerConfig] = None,
) -> LearningManager:
    """LearningManager factory."""
    return LearningManager(config)


_default_manager: Optional[LearningManager] = None


def get_learning_manager() -> LearningManager:
    """Default LearningManager getir."""
    global _default_manager
    if _default_manager is None:
        _default_manager = LearningManager()
    return _default_manager


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "LearningManagerConfig",
    "AdaptationStrategy",
    "LearningManager",
    "create_learning_manager",
    "get_learning_manager",
]
