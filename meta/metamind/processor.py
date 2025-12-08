"""
UEM v2 - MetaMind Processor

Meta-bilissel islemci - tum alt modulleri koordine eder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .types import (
    MetaState,
    MetaStateType,
    CycleAnalysisResult,
    Insight,
    InsightType,
    Pattern,
    PatternType,
    LearningGoal,
    LearningGoalType,
    SeverityLevel,
)
from .analyzers import CycleAnalyzer, AnalyzerConfig
from .insights import InsightGenerator, InsightGeneratorConfig
from .patterns import PatternDetector, PatternDetectorConfig
from .learning import LearningManager, LearningManagerConfig, AdaptationStrategy


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class MetaMindConfig:
    """MetaMindProcessor yapilandirmasi."""
    # Alt modul konfigurasyonlari
    analyzer_config: Optional[AnalyzerConfig] = None
    insight_config: Optional[InsightGeneratorConfig] = None
    pattern_config: Optional[PatternDetectorConfig] = None
    learning_config: Optional[LearningManagerConfig] = None

    # Islem parametreleri
    auto_process: bool = True                  # Otomatik isle
    generate_insights: bool = True             # Insight uret
    detect_patterns: bool = True               # Pattern tespit et
    suggest_adaptations: bool = True           # Adaptasyon oner

    # Cycle baglantisi
    process_every_n_cycles: int = 1            # Her N cycle'da isle
    deep_analysis_every_n: int = 10            # Her N'de derin analiz

    # Raporlama
    log_insights: bool = False                 # Insight'lari logla
    emit_events: bool = True                   # Event yayinla


# ============================================================================
# METAMIND OUTPUT
# ============================================================================

@dataclass
class MetaMindOutput:
    """MetaMindProcessor ciktisi."""
    # Durum
    state: MetaStateType = MetaStateType.IDLE
    cycle_id: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    # Analiz
    analysis: Optional[CycleAnalysisResult] = None
    performance_score: float = 0.0

    # Insight'lar
    new_insights: List[Insight] = field(default_factory=list)
    active_insights_count: int = 0

    # Pattern'ler
    new_patterns: List[Pattern] = field(default_factory=list)
    active_patterns_count: int = 0

    # Ogrenme
    active_goals_count: int = 0
    goals_progress: float = 0.0
    suggested_adaptation: Optional[AdaptationStrategy] = None

    # Meta
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye donustur."""
        return {
            "state": self.state.value,
            "cycle_id": self.cycle_id,
            "performance_score": self.performance_score,
            "new_insights": len(self.new_insights),
            "active_insights": self.active_insights_count,
            "new_patterns": len(self.new_patterns),
            "active_patterns": self.active_patterns_count,
            "active_goals": self.active_goals_count,
            "goals_progress": self.goals_progress,
            "has_adaptation": self.suggested_adaptation is not None,
            "processing_time_ms": self.processing_time_ms,
        }


# ============================================================================
# METAMIND PROCESSOR
# ============================================================================

class MetaMindProcessor:
    """
    MetaMind ana islemcisi.

    Tum meta-bilissel alt modulleri koordine eder:
    - CycleAnalyzer: "Bu cycle nasil gitti?"
    - InsightGenerator: "Ne ogrendim?"
    - PatternDetector: "Tekrarlayan kalipler var mi?"
    - LearningManager: "Nasil gelistebilirim?"
    """

    def __init__(self, config: Optional[MetaMindConfig] = None):
        """
        MetaMindProcessor baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or MetaMindConfig()

        # Alt modulleri olustur
        self.analyzer = CycleAnalyzer(self.config.analyzer_config)
        self.insights = InsightGenerator(self.config.insight_config)
        self.patterns = PatternDetector(self.config.pattern_config)
        self.learning = LearningManager(self.config.learning_config)

        # Durum
        self._state = MetaState()
        self._cycle_count = 0

        # Gecmis
        self._analysis_history: List[CycleAnalysisResult] = []

        # Event listeners
        self._listeners: List[Callable[[MetaMindOutput], None]] = []

        # Istatistikler
        self._stats = {
            "process_calls": 0,
            "insights_generated": 0,
            "patterns_detected": 0,
            "adaptations_suggested": 0,
        }

    # ========================================================================
    # MAIN PROCESSING
    # ========================================================================

    def process(
        self,
        cycle_id: int,
        duration_ms: float,
        phase_durations: Dict[str, float],
        success: bool = True,
        failed_phases: Optional[List[str]] = None,
        memory_retrievals: int = 0,
        memory_stores: int = 0,
        events_processed: int = 0,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> MetaMindOutput:
        """
        Cycle verisini isle.

        Args:
            cycle_id: Cycle ID
            duration_ms: Toplam sure (ms)
            phase_durations: Phase sureleri
            success: Basarili mi
            failed_phases: Basarisiz phase'ler
            memory_retrievals: Memory okuma sayisi
            memory_stores: Memory yazma sayisi
            events_processed: Islenen event sayisi
            additional_data: Ek veri

        Returns:
            MetaMindOutput
        """
        start_time = datetime.now()
        self._cycle_count += 1
        self._stats["process_calls"] += 1

        # Durum guncelle
        self._state.state_type = MetaStateType.ANALYZING
        self._state.timestamp = datetime.now()

        # 1. Cycle analizi
        analysis = self.analyzer.analyze_cycle(
            cycle_id=cycle_id,
            duration_ms=duration_ms,
            phase_durations=phase_durations,
            success=success,
            failed_phases=failed_phases,
            memory_retrievals=memory_retrievals,
            memory_stores=memory_stores,
            events_processed=events_processed,
        )

        # Gecmise ekle
        self._analysis_history.append(analysis)
        if len(self._analysis_history) > 500:
            self._analysis_history = self._analysis_history[-500:]

        self._state.cycles_analyzed += 1
        self._state.last_analysis_cycle = cycle_id

        # 2. Insight uretimi
        new_insights = []
        if self.config.generate_insights:
            self._state.state_type = MetaStateType.LEARNING
            new_insights = self.insights.generate_from_analysis(
                current=analysis,
                history=self._analysis_history[-50:],
            )
            self._state.active_insights_count = len(self.insights.get_active_insights())
            self._state.total_insights_generated += len(new_insights)
            self._stats["insights_generated"] += len(new_insights)

        # 3. Pattern tespiti
        new_patterns = []
        if self.config.detect_patterns:
            new_patterns = self.patterns.process_analysis(analysis)
            self._state.patterns_detected = self.patterns._patterns_detected
            self._state.active_patterns_count = len(self.patterns.get_all_patterns())
            self._stats["patterns_detected"] += len(new_patterns)

        # 4. Ogrenme ve adaptasyon
        suggested_adaptation = None
        if self.config.suggest_adaptations:
            self._state.state_type = MetaStateType.ADAPTING

            # Metrikleri izle
            self.learning.track_analysis(analysis)

            # Insight'lardan hedef uret
            if new_insights:
                self.learning.generate_goals_from_insights(new_insights)

            # Pattern'lerden hedef uret
            if new_patterns:
                self.learning.generate_goals_from_patterns(new_patterns)

            # Adaptasyon oner
            suggested_adaptation = self.learning.suggest_adaptation(
                analysis=analysis,
                insights=self.insights.get_active_insights(),
                patterns=self.patterns.get_all_patterns(),
            )
            if suggested_adaptation:
                self._stats["adaptations_suggested"] += 1

            self._state.active_goals_count = len(self.learning.get_active_goals())
            self._state.achieved_goals_count = self.learning._goals_achieved

        # 5. Sistem sagligi hesapla
        self._update_system_health(analysis)

        # Durum guncelle
        self._state.state_type = MetaStateType.MONITORING

        # Cikti olustur
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        output = MetaMindOutput(
            state=self._state.state_type,
            cycle_id=cycle_id,
            timestamp=datetime.now(),
            analysis=analysis,
            performance_score=analysis.get_performance_score(),
            new_insights=new_insights,
            active_insights_count=self._state.active_insights_count,
            new_patterns=new_patterns,
            active_patterns_count=self._state.active_patterns_count,
            active_goals_count=self._state.active_goals_count,
            goals_progress=self._calculate_goals_progress(),
            suggested_adaptation=suggested_adaptation,
            processing_time_ms=processing_time,
        )

        # Listener'lara bildir
        self._notify_listeners(output)

        return output

    def process_from_metrics(self, metrics: Any) -> MetaMindOutput:
        """
        CycleMetrics'ten isle.

        Args:
            metrics: CycleMetrics nesnesi

        Returns:
            MetaMindOutput
        """
        phase_durations = {}
        failed_phases = []

        if hasattr(metrics, "phase_metrics"):
            for name, pm in metrics.phase_metrics.items():
                phase_durations[name] = pm.duration_ms
                if not pm.success:
                    failed_phases.append(name)

        return self.process(
            cycle_id=getattr(metrics, "cycle_id", 0),
            duration_ms=getattr(metrics, "total_duration_ms", 0.0),
            phase_durations=phase_durations,
            success=getattr(metrics, "success", True),
            failed_phases=failed_phases,
            memory_retrievals=getattr(metrics, "memory_retrievals", 0),
            memory_stores=getattr(metrics, "memory_stores", 0),
            events_processed=getattr(metrics, "events_processed", 0),
        )

    # ========================================================================
    # SYSTEM HEALTH
    # ========================================================================

    def _update_system_health(self, analysis: CycleAnalysisResult) -> None:
        """Sistem sagligini guncelle."""
        factors = []

        # Basari orani
        recent = self._analysis_history[-20:]
        if recent:
            success_rate = sum(1 for a in recent if a.success) / len(recent)
            factors.append(success_rate)

        # Performans skoru
        factors.append(analysis.get_performance_score())

        # Anomali orani (ters)
        if recent:
            anomaly_rate = sum(1 for a in recent if a.is_anomaly) / len(recent)
            factors.append(1.0 - anomaly_rate)

        # Hedef ilerleme
        goals_progress = self._calculate_goals_progress()
        if goals_progress > 0:
            factors.append(goals_progress)

        # Ortalama saglik
        if factors:
            self._state.system_health = sum(factors) / len(factors)
        else:
            self._state.system_health = 1.0

    def _calculate_goals_progress(self) -> float:
        """Hedef ilerleme ortalamasi."""
        goals = self.learning.get_active_goals()
        if not goals:
            return 0.0
        return sum(g.progress for g in goals) / len(goals)

    # ========================================================================
    # LISTENERS
    # ========================================================================

    def register_listener(
        self,
        callback: Callable[[MetaMindOutput], None],
    ) -> None:
        """Listener kaydet."""
        self._listeners.append(callback)

    def unregister_listener(
        self,
        callback: Callable[[MetaMindOutput], None],
    ) -> None:
        """Listener kaldir."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self, output: MetaMindOutput) -> None:
        """Listener'lara bildir."""
        for listener in self._listeners:
            try:
                listener(output)
            except Exception:
                pass  # Listener hatalari sessizce gecilir

    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================

    def get_active_insights(
        self,
        insight_type: Optional[InsightType] = None,
        min_severity: Optional[SeverityLevel] = None,
    ) -> List[Insight]:
        """Aktif insight'lari getir."""
        return self.insights.get_active_insights(insight_type, min_severity)

    def get_active_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
    ) -> List[Pattern]:
        """Aktif pattern'leri getir."""
        if pattern_type:
            return self.patterns.get_patterns_by_type(pattern_type)
        return self.patterns.get_all_patterns()

    def get_active_goals(
        self,
        goal_type: Optional[LearningGoalType] = None,
    ) -> List[LearningGoal]:
        """Aktif hedefleri getir."""
        return self.learning.get_active_goals(goal_type)

    def get_adaptation_strategies(self) -> List[AdaptationStrategy]:
        """Adaptasyon stratejilerini getir."""
        return self.learning.get_active_strategies()

    def get_performance_trend(self) -> Dict[str, Any]:
        """Performans trendini getir."""
        return self.analyzer.get_trend()

    def get_system_health(self) -> float:
        """Sistem sagligini getir."""
        return self._state.system_health

    def get_meta_state(self) -> MetaState:
        """Meta durumu getir."""
        return self._state

    # ========================================================================
    # MANUAL OPERATIONS
    # ========================================================================

    def create_insight(
        self,
        insight_type: InsightType,
        title: str,
        description: str,
        severity: SeverityLevel = SeverityLevel.MEDIUM,
        recommended_action: Optional[str] = None,
    ) -> Insight:
        """Manuel insight olustur."""
        return self.insights.create_insight(
            insight_type=insight_type,
            title=title,
            description=description,
            severity=severity,
            recommended_action=recommended_action,
        )

    def create_goal(
        self,
        goal_type: LearningGoalType,
        name: str,
        target_metric: str,
        target_value: float,
        description: str = "",
    ) -> LearningGoal:
        """Manuel hedef olustur."""
        return self.learning.create_goal(
            goal_type=goal_type,
            name=name,
            description=description,
            target_metric=target_metric,
            target_value=target_value,
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Tum istatistikleri getir."""
        return {
            "processor": self._stats.copy(),
            "analyzer": self.analyzer.get_stats(),
            "insights": self.insights.get_stats(),
            "patterns": self.patterns.get_stats(),
            "learning": self.learning.get_stats(),
        }

    def summary(self) -> Dict[str, Any]:
        """Genel ozet."""
        return {
            "state": self._state.to_dict(),
            "cycles_analyzed": self._state.cycles_analyzed,
            "system_health": self._state.system_health,
            "analyzer": self.analyzer.summary(),
            "insights": self.insights.summary(),
            "patterns": self.patterns.summary(),
            "learning": self.learning.summary(),
        }

    def reset(self) -> None:
        """Tum durumu sifirla."""
        self.analyzer.reset()
        self._analysis_history.clear()
        self._state = MetaState()
        self._cycle_count = 0
        self._stats = {
            "process_calls": 0,
            "insights_generated": 0,
            "patterns_detected": 0,
            "adaptations_suggested": 0,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_metamind_processor(
    config: Optional[MetaMindConfig] = None,
) -> MetaMindProcessor:
    """MetaMindProcessor factory."""
    return MetaMindProcessor(config)


_default_processor: Optional[MetaMindProcessor] = None


def get_metamind_processor() -> MetaMindProcessor:
    """Default MetaMindProcessor getir."""
    global _default_processor
    if _default_processor is None:
        _default_processor = MetaMindProcessor()
    return _default_processor


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "MetaMindConfig",
    "MetaMindOutput",
    "MetaMindProcessor",
    "create_metamind_processor",
    "get_metamind_processor",
]
