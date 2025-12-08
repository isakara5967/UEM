"""
UEM v2 - MetaMind Insights

Ogrenilen dersler: "Ne ogrendim?"
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta

from .types import (
    Insight,
    InsightType,
    SeverityLevel,
    AnalysisScope,
    CycleAnalysisResult,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class InsightGeneratorConfig:
    """InsightGenerator yapilandirmasi."""
    # Insight uretim esikleri
    performance_drop_threshold: float = 0.2     # %20 performans dususu
    anomaly_cluster_size: int = 3               # N anomali = cluster
    success_rate_warning: float = 0.9           # %90 alti = uyari

    # Correlation
    min_correlation: float = 0.7                # Min korelasyon

    # Insight yasam suresi
    default_ttl_hours: int = 24                 # Varsayilan yasam suresi
    critical_ttl_hours: int = 168               # Kritik insight yasam suresi

    # Sinirlar
    max_active_insights: int = 100              # Max aktif insight
    max_insights_per_type: int = 10             # Tur basina max


# ============================================================================
# INSIGHT GENERATOR
# ============================================================================

class InsightGenerator:
    """
    Insight uretici.

    Cycle analizlerinden ogrenilen dersleri cikarir.
    """

    def __init__(self, config: Optional[InsightGeneratorConfig] = None):
        """
        InsightGenerator baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or InsightGeneratorConfig()

        # Aktif insight'lar
        self._insights: Dict[str, Insight] = {}

        # Insight gecmisi (tum zamanlar)
        self._insight_history: List[Insight] = []

        # Sayaclar
        self._insights_generated = 0

        # Ozel insight uretici fonksiyonlar
        self._custom_generators: List[Callable[[CycleAnalysisResult, List[CycleAnalysisResult]], Optional[Insight]]] = []

    # ========================================================================
    # INSIGHT GENERATION
    # ========================================================================

    def generate_from_analysis(
        self,
        current: CycleAnalysisResult,
        history: Optional[List[CycleAnalysisResult]] = None,
    ) -> List[Insight]:
        """
        Analiz sonuclarindan insight uret.

        Args:
            current: Mevcut cycle analizi
            history: Gecmis analizler

        Returns:
            Uretilen insight listesi
        """
        insights = []
        history = history or []

        # 1. Anomali bazli insight
        if current.is_anomaly:
            insight = self._generate_anomaly_insight(current)
            if insight:
                insights.append(insight)

        # 2. Performans degisimi insight
        if current.vs_average and abs(current.vs_average) > self.config.performance_drop_threshold * 100:
            insight = self._generate_performance_insight(current)
            if insight:
                insights.append(insight)

        # 3. Basarisizlik insight
        if not current.success:
            insight = self._generate_failure_insight(current)
            if insight:
                insights.append(insight)

        # 4. Yavas phase insight
        for phase, duration in current.phase_durations.items():
            if phase == current.slowest_phase and duration > 100:  # 100ms+
                insight = self._generate_bottleneck_insight(current, phase, duration)
                if insight:
                    insights.append(insight)

        # 5. Trend bazli insight (gecmis gerekli)
        if len(history) >= 10:
            trend_insight = self._generate_trend_insight(history + [current])
            if trend_insight:
                insights.append(trend_insight)

        # 6. Ozel generator'lar
        for generator in self._custom_generators:
            try:
                custom_insight = generator(current, history)
                if custom_insight:
                    insights.append(custom_insight)
            except Exception:
                pass  # Ozel generator hatalari sessizce gecilir

        # Insight'lari kaydet
        for insight in insights:
            self._register_insight(insight)

        return insights

    def _generate_anomaly_insight(self, analysis: CycleAnalysisResult) -> Optional[Insight]:
        """Anomali bazli insight uret."""
        return Insight(
            insight_type=InsightType.ANOMALY,
            title=f"Anomaly detected in cycle {analysis.cycle_id}",
            description=analysis.anomaly_reason or "Unusual cycle behavior detected",
            evidence={
                "cycle_id": analysis.cycle_id,
                "duration_ms": analysis.total_duration_ms,
                "reason": analysis.anomaly_reason,
            },
            severity=SeverityLevel.MEDIUM,
            confidence=0.8,
            actionable=True,
            recommended_action="Investigate the cause of the anomaly",
            source_cycles=[analysis.cycle_id],
            scope=AnalysisScope.SINGLE_CYCLE,
        )

    def _generate_performance_insight(self, analysis: CycleAnalysisResult) -> Optional[Insight]:
        """Performans degisimi insight'i uret."""
        is_degradation = analysis.vs_average > 0

        if is_degradation:
            insight_type = InsightType.BOTTLENECK
            title = f"Performance degradation: {analysis.vs_average:.1f}% slower than average"
            severity = SeverityLevel.HIGH if analysis.vs_average > 50 else SeverityLevel.MEDIUM
            recommended_action = f"Investigate slowdown, particularly in {analysis.slowest_phase}"
        else:
            insight_type = InsightType.OPTIMIZATION
            title = f"Performance improvement: {abs(analysis.vs_average):.1f}% faster than average"
            severity = SeverityLevel.LOW
            recommended_action = "Document what made this cycle faster"

        return Insight(
            insight_type=insight_type,
            title=title,
            description=f"Cycle {analysis.cycle_id} completed in {analysis.total_duration_ms:.1f}ms",
            evidence={
                "cycle_id": analysis.cycle_id,
                "duration_ms": analysis.total_duration_ms,
                "vs_average_percent": analysis.vs_average,
                "slowest_phase": analysis.slowest_phase,
            },
            severity=severity,
            confidence=0.9,
            actionable=is_degradation,
            recommended_action=recommended_action,
            source_cycles=[analysis.cycle_id],
            scope=AnalysisScope.SINGLE_CYCLE,
        )

    def _generate_failure_insight(self, analysis: CycleAnalysisResult) -> Optional[Insight]:
        """Basarisizlik insight'i uret."""
        failed_phases_str = ", ".join(analysis.failed_phases) if analysis.failed_phases else "unknown"

        return Insight(
            insight_type=InsightType.WARNING,
            title=f"Cycle {analysis.cycle_id} failed",
            description=f"Failed phases: {failed_phases_str}",
            evidence={
                "cycle_id": analysis.cycle_id,
                "failed_phases": analysis.failed_phases,
                "duration_ms": analysis.total_duration_ms,
            },
            severity=SeverityLevel.HIGH,
            confidence=1.0,
            actionable=True,
            recommended_action=f"Fix issues in {failed_phases_str}",
            source_cycles=[analysis.cycle_id],
            scope=AnalysisScope.SINGLE_CYCLE,
        )

    def _generate_bottleneck_insight(
        self,
        analysis: CycleAnalysisResult,
        phase: str,
        duration: float,
    ) -> Optional[Insight]:
        """Darbogazinsight'i uret."""
        total = analysis.total_duration_ms
        percentage = (duration / total * 100) if total > 0 else 0

        if percentage < 40:  # %40'tan az = bottleneck degil
            return None

        return Insight(
            insight_type=InsightType.BOTTLENECK,
            title=f"Bottleneck detected: {phase}",
            description=f"{phase} phase takes {percentage:.1f}% of cycle time ({duration:.1f}ms)",
            evidence={
                "phase": phase,
                "duration_ms": duration,
                "total_duration_ms": total,
                "percentage": percentage,
            },
            severity=SeverityLevel.MEDIUM if percentage < 60 else SeverityLevel.HIGH,
            confidence=0.85,
            actionable=True,
            recommended_action=f"Optimize {phase} phase to improve overall performance",
            source_cycles=[analysis.cycle_id],
            scope=AnalysisScope.SINGLE_CYCLE,
        )

    def _generate_trend_insight(
        self,
        analyses: List[CycleAnalysisResult],
    ) -> Optional[Insight]:
        """Trend bazli insight uret."""
        if len(analyses) < 10:
            return None

        # Son 10 vs ilk 10 karsilastir
        first_10 = analyses[:10]
        last_10 = analyses[-10:]

        avg_first = sum(a.total_duration_ms for a in first_10) / len(first_10)
        avg_last = sum(a.total_duration_ms for a in last_10) / len(last_10)

        if avg_first == 0:
            return None

        change_percent = ((avg_last - avg_first) / avg_first) * 100

        # Onemli degisim yoksa insight uretme
        if abs(change_percent) < 10:
            return None

        if change_percent > 0:
            insight_type = InsightType.TREND
            title = f"Performance degradation trend: {change_percent:.1f}% slower"
            severity = SeverityLevel.HIGH if change_percent > 30 else SeverityLevel.MEDIUM
            recommended_action = "Investigate gradual slowdown cause"
        else:
            insight_type = InsightType.SUCCESS
            title = f"Performance improvement trend: {abs(change_percent):.1f}% faster"
            severity = SeverityLevel.LOW
            recommended_action = "Document optimization success"

        return Insight(
            insight_type=insight_type,
            title=title,
            description=f"Average duration changed from {avg_first:.1f}ms to {avg_last:.1f}ms",
            evidence={
                "first_avg_ms": avg_first,
                "last_avg_ms": avg_last,
                "change_percent": change_percent,
                "sample_size": len(analyses),
            },
            severity=severity,
            confidence=0.75,
            actionable=change_percent > 0,
            recommended_action=recommended_action,
            source_cycles=[a.cycle_id for a in last_10],
            scope=AnalysisScope.SHORT_TERM,
        )

    # ========================================================================
    # MANUAL INSIGHT CREATION
    # ========================================================================

    def create_insight(
        self,
        insight_type: InsightType,
        title: str,
        description: str,
        evidence: Optional[Dict[str, Any]] = None,
        severity: SeverityLevel = SeverityLevel.MEDIUM,
        confidence: float = 0.8,
        recommended_action: Optional[str] = None,
    ) -> Insight:
        """Manuel insight olustur."""
        insight = Insight(
            insight_type=insight_type,
            title=title,
            description=description,
            evidence=evidence or {},
            severity=severity,
            confidence=confidence,
            actionable=recommended_action is not None,
            recommended_action=recommended_action,
        )

        self._register_insight(insight)
        return insight

    # ========================================================================
    # INSIGHT MANAGEMENT
    # ========================================================================

    def _register_insight(self, insight: Insight) -> None:
        """Insight'i kaydet."""
        # TTL ayarla
        if not insight.expires_at:
            ttl_hours = (
                self.config.critical_ttl_hours
                if insight.severity == SeverityLevel.CRITICAL
                else self.config.default_ttl_hours
            )
            insight.expires_at = datetime.now() + timedelta(hours=ttl_hours)

        # Limit kontrolu
        type_count = sum(
            1 for i in self._insights.values()
            if i.insight_type == insight.insight_type and i.is_active
        )

        if type_count >= self.config.max_insights_per_type:
            # En eski benzer insight'i deaktive et
            oldest = min(
                (i for i in self._insights.values()
                 if i.insight_type == insight.insight_type and i.is_active),
                key=lambda x: x.timestamp,
                default=None,
            )
            if oldest:
                oldest.is_active = False

        # Kaydet
        self._insights[insight.id] = insight
        self._insight_history.append(insight)
        self._insights_generated += 1

        # Toplam limit
        if len(self._insights) > self.config.max_active_insights:
            self._cleanup_expired()

    def _cleanup_expired(self) -> None:
        """Suresi dolmus insight'lari temizle."""
        now = datetime.now()

        # Suresi dolanlari deaktive et
        for insight in self._insights.values():
            if insight.expires_at and insight.expires_at < now:
                insight.is_active = False

        # Deaktif olanlari sil (en eski %25'i)
        inactive = [i for i in self._insights.values() if not i.is_active]
        inactive.sort(key=lambda x: x.timestamp)

        for insight in inactive[:len(inactive) // 4 + 1]:
            del self._insights[insight.id]

    def get_insight(self, insight_id: str) -> Optional[Insight]:
        """Insight getir."""
        return self._insights.get(insight_id)

    def get_active_insights(
        self,
        insight_type: Optional[InsightType] = None,
        min_severity: Optional[SeverityLevel] = None,
    ) -> List[Insight]:
        """Aktif insight'lari getir."""
        insights = [i for i in self._insights.values() if i.is_active]

        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]

        if min_severity:
            severity_order = list(SeverityLevel)
            min_idx = severity_order.index(min_severity)
            insights = [
                i for i in insights
                if severity_order.index(i.severity) >= min_idx
            ]

        return sorted(insights, key=lambda x: x.get_priority(), reverse=True)

    def get_actionable_insights(self) -> List[Insight]:
        """Aksiyon alinabilir insight'lari getir."""
        return [
            i for i in self._insights.values()
            if i.is_active and i.actionable
        ]

    def dismiss_insight(self, insight_id: str) -> bool:
        """Insight'i kapat."""
        if insight_id in self._insights:
            self._insights[insight_id].is_active = False
            return True
        return False

    # ========================================================================
    # CUSTOM GENERATORS
    # ========================================================================

    def register_generator(
        self,
        generator: Callable[[CycleAnalysisResult, List[CycleAnalysisResult]], Optional[Insight]],
    ) -> None:
        """Ozel insight generator ekle."""
        self._custom_generators.append(generator)

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Istatistikleri getir."""
        active = self.get_active_insights()

        by_type = {}
        for insight in active:
            t = insight.insight_type.value
            by_type[t] = by_type.get(t, 0) + 1

        by_severity = {}
        for insight in active:
            s = insight.severity.value
            by_severity[s] = by_severity.get(s, 0) + 1

        return {
            "total_generated": self._insights_generated,
            "active_count": len(active),
            "by_type": by_type,
            "by_severity": by_severity,
            "actionable_count": len(self.get_actionable_insights()),
        }

    def summary(self) -> Dict[str, Any]:
        """Genel ozet."""
        active = self.get_active_insights()

        return {
            "active_insights": len(active),
            "total_generated": self._insights_generated,
            "critical_count": len([i for i in active if i.severity == SeverityLevel.CRITICAL]),
            "high_count": len([i for i in active if i.severity == SeverityLevel.HIGH]),
            "actionable": len(self.get_actionable_insights()),
            "top_insights": [i.to_dict() for i in active[:5]],
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_insight_generator(
    config: Optional[InsightGeneratorConfig] = None,
) -> InsightGenerator:
    """InsightGenerator factory."""
    return InsightGenerator(config)


_default_generator: Optional[InsightGenerator] = None


def get_insight_generator() -> InsightGenerator:
    """Default InsightGenerator getir."""
    global _default_generator
    if _default_generator is None:
        _default_generator = InsightGenerator()
    return _default_generator


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "InsightGeneratorConfig",
    "InsightGenerator",
    "create_insight_generator",
    "get_insight_generator",
]
