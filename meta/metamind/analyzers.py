"""
UEM v2 - MetaMind Analyzers

Cycle performans analizi: "Bu cycle nasil gitti?"
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import statistics

from .types import (
    CycleAnalysisResult,
    AnalysisScope,
    SeverityLevel,
)

# Opsiyonel import - monitoring mevcut degilse de calisir
try:
    from meta.monitoring.metrics.cycle import CycleMetrics, CycleMetricsHistory
except ImportError:
    CycleMetrics = None
    CycleMetricsHistory = None


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class AnalyzerConfig:
    """Analyzer yapilandirmasi."""
    # Anomali tespiti
    anomaly_std_threshold: float = 2.0       # N standart sapma = anomali
    min_samples_for_anomaly: int = 5         # Min sample sayisi

    # Performans esikleri (ms)
    slow_cycle_threshold_ms: float = 500.0   # Yavas cycle
    fast_cycle_threshold_ms: float = 50.0    # Hizli cycle

    # Phase esikleri
    slow_phase_threshold_ms: float = 200.0   # Yavas phase
    phase_imbalance_threshold: float = 0.5   # Phase dengesizligi

    # Karsilastirma penceresi
    comparison_window: int = 100             # Son N cycle

    # Gecmis tutma
    max_history: int = 1000                  # Max analiz sonucu


# ============================================================================
# CYCLE ANALYZER
# ============================================================================

class CycleAnalyzer:
    """
    Cycle performans analizcisi.

    Her cycle'i analiz eder ve performans metrikleri cikarir.
    """

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        """
        CycleAnalyzer baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or AnalyzerConfig()

        # Analiz sonuclari gecmisi
        self._analysis_history: List[CycleAnalysisResult] = []

        # Istatistikler
        self._duration_history: List[float] = []
        self._phase_histories: Dict[str, List[float]] = {}

        # Sayaclar
        self._cycles_analyzed = 0
        self._anomalies_detected = 0

    # ========================================================================
    # MAIN ANALYSIS
    # ========================================================================

    def analyze_cycle(
        self,
        cycle_id: int,
        duration_ms: float,
        phase_durations: Dict[str, float],
        success: bool = True,
        failed_phases: Optional[List[str]] = None,
        memory_retrievals: int = 0,
        memory_stores: int = 0,
        events_processed: int = 0,
    ) -> CycleAnalysisResult:
        """
        Tek cycle'i analiz et.

        Args:
            cycle_id: Cycle ID
            duration_ms: Toplam sure (ms)
            phase_durations: Phase sureleri
            success: Basarili mi
            failed_phases: Basarisiz phase'ler
            memory_retrievals: Memory okuma sayisi
            memory_stores: Memory yazma sayisi
            events_processed: Islenen event sayisi

        Returns:
            CycleAnalysisResult
        """
        result = CycleAnalysisResult(
            cycle_id=cycle_id,
            total_duration_ms=duration_ms,
            phase_durations=phase_durations,
            success=success,
            failed_phases=failed_phases or [],
            memory_retrievals=memory_retrievals,
            memory_stores=memory_stores,
            events_processed=events_processed,
        )

        # Phase analizi
        if phase_durations:
            phases_sorted = sorted(phase_durations.items(), key=lambda x: x[1])
            result.fastest_phase = phases_sorted[0][0] if phases_sorted else None
            result.slowest_phase = phases_sorted[-1][0] if phases_sorted else None

        # Karsilastirma
        result.vs_average = self._compare_to_average(duration_ms)
        result.vs_previous = self._compare_to_previous(duration_ms)

        # Anomali tespiti
        is_anomaly, reason = self._detect_anomaly(duration_ms, phase_durations, success)
        result.is_anomaly = is_anomaly
        result.anomaly_reason = reason

        if is_anomaly:
            self._anomalies_detected += 1

        # Gecmise ekle
        self._update_history(result)
        self._cycles_analyzed += 1

        return result

    def analyze_from_metrics(self, metrics: Any) -> CycleAnalysisResult:
        """
        CycleMetrics'ten analiz et.

        Args:
            metrics: CycleMetrics nesnesi

        Returns:
            CycleAnalysisResult
        """
        phase_durations = {}
        failed_phases = []

        if hasattr(metrics, "phase_metrics"):
            for name, pm in metrics.phase_metrics.items():
                phase_durations[name] = pm.duration_ms
                if not pm.success:
                    failed_phases.append(name)

        return self.analyze_cycle(
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
    # COMPARISON
    # ========================================================================

    def _compare_to_average(self, duration_ms: float) -> Optional[float]:
        """Ortalamaya gore karsilastir (% fark)."""
        if len(self._duration_history) < self.config.min_samples_for_anomaly:
            return None

        avg = statistics.mean(self._duration_history[-self.config.comparison_window:])
        if avg == 0:
            return None

        return ((duration_ms - avg) / avg) * 100

    def _compare_to_previous(self, duration_ms: float) -> Optional[float]:
        """Onceki cycle'a gore karsilastir (% fark)."""
        if not self._duration_history:
            return None

        prev = self._duration_history[-1]
        if prev == 0:
            return None

        return ((duration_ms - prev) / prev) * 100

    # ========================================================================
    # ANOMALY DETECTION
    # ========================================================================

    def _detect_anomaly(
        self,
        duration_ms: float,
        phase_durations: Dict[str, float],
        success: bool,
    ) -> Tuple[bool, Optional[str]]:
        """
        Anomali tespit et.

        Returns:
            (is_anomaly, reason)
        """
        # Basarisiz cycle = anomali
        if not success:
            return True, "Cycle failed"

        # Cok yavas cycle
        if duration_ms > self.config.slow_cycle_threshold_ms:
            return True, f"Slow cycle: {duration_ms:.1f}ms > {self.config.slow_cycle_threshold_ms}ms"

        # Istatistiksel anomali
        if len(self._duration_history) >= self.config.min_samples_for_anomaly:
            recent = self._duration_history[-self.config.comparison_window:]
            mean = statistics.mean(recent)
            stdev = statistics.stdev(recent) if len(recent) > 1 else 0

            if stdev > 0:
                z_score = (duration_ms - mean) / stdev
                if abs(z_score) > self.config.anomaly_std_threshold:
                    return True, f"Statistical anomaly: z-score={z_score:.2f}"

        # Phase dengesizligi
        if phase_durations:
            durations = list(phase_durations.values())
            if durations:
                max_dur = max(durations)
                total = sum(durations)
                if total > 0 and (max_dur / total) > self.config.phase_imbalance_threshold:
                    slowest = max(phase_durations, key=phase_durations.get)
                    return True, f"Phase imbalance: {slowest} takes {(max_dur/total)*100:.1f}% of cycle"

        return False, None

    # ========================================================================
    # HISTORY MANAGEMENT
    # ========================================================================

    def _update_history(self, result: CycleAnalysisResult) -> None:
        """Gecmisi guncelle."""
        # Ana sure gecmisi
        self._duration_history.append(result.total_duration_ms)
        if len(self._duration_history) > self.config.max_history:
            self._duration_history.pop(0)

        # Phase gecmisleri
        for phase, duration in result.phase_durations.items():
            if phase not in self._phase_histories:
                self._phase_histories[phase] = []
            self._phase_histories[phase].append(duration)
            if len(self._phase_histories[phase]) > self.config.max_history:
                self._phase_histories[phase].pop(0)

        # Analiz sonucu gecmisi
        self._analysis_history.append(result)
        if len(self._analysis_history) > self.config.max_history:
            self._analysis_history.pop(0)

    # ========================================================================
    # AGGREGATE ANALYSIS
    # ========================================================================

    def get_aggregate_stats(
        self,
        scope: AnalysisScope = AnalysisScope.SHORT_TERM,
    ) -> Dict[str, Any]:
        """
        Toplu istatistikler getir.

        Args:
            scope: Analiz kapsami

        Returns:
            Istatistik dictionary
        """
        # Kapsama gore veri sec
        if scope == AnalysisScope.SINGLE_CYCLE:
            n = 1
        elif scope == AnalysisScope.SHORT_TERM:
            n = 10
        elif scope == AnalysisScope.MEDIUM_TERM:
            n = 100
        else:  # LONG_TERM
            n = len(self._duration_history)

        recent = self._duration_history[-n:] if self._duration_history else []

        if not recent:
            return {
                "scope": scope.value,
                "sample_count": 0,
                "average_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "std_deviation_ms": 0,
                "success_rate": 0,
                "anomaly_rate": 0,
            }

        # Basari orani
        recent_results = self._analysis_history[-n:] if self._analysis_history else []
        success_count = sum(1 for r in recent_results if r.success)
        anomaly_count = sum(1 for r in recent_results if r.is_anomaly)

        return {
            "scope": scope.value,
            "sample_count": len(recent),
            "average_duration_ms": statistics.mean(recent),
            "min_duration_ms": min(recent),
            "max_duration_ms": max(recent),
            "std_deviation_ms": statistics.stdev(recent) if len(recent) > 1 else 0,
            "success_rate": success_count / len(recent_results) if recent_results else 1.0,
            "anomaly_rate": anomaly_count / len(recent_results) if recent_results else 0.0,
        }

    def get_phase_stats(
        self,
        phase_name: str,
        n: int = 100,
    ) -> Dict[str, float]:
        """
        Belirli bir phase'in istatistiklerini getir.

        Args:
            phase_name: Phase adi
            n: Son N cycle

        Returns:
            Istatistik dictionary
        """
        if phase_name not in self._phase_histories:
            return {}

        recent = self._phase_histories[phase_name][-n:]
        if not recent:
            return {}

        return {
            "average_ms": statistics.mean(recent),
            "min_ms": min(recent),
            "max_ms": max(recent),
            "std_ms": statistics.stdev(recent) if len(recent) > 1 else 0,
            "sample_count": len(recent),
        }

    def get_slowest_phases(self, n: int = 5) -> List[Tuple[str, float]]:
        """En yavas phase'leri getir (ortalama)."""
        phase_avgs = []
        for phase, durations in self._phase_histories.items():
            if durations:
                avg = statistics.mean(durations[-100:])
                phase_avgs.append((phase, avg))

        return sorted(phase_avgs, key=lambda x: x[1], reverse=True)[:n]

    def get_recent_anomalies(self, n: int = 10) -> List[CycleAnalysisResult]:
        """Son N anomaliyi getir."""
        anomalies = [r for r in self._analysis_history if r.is_anomaly]
        return anomalies[-n:]

    # ========================================================================
    # TREND ANALYSIS
    # ========================================================================

    def get_trend(self, window: int = 50) -> Dict[str, Any]:
        """
        Performans trendini analiz et.

        Args:
            window: Analiz penceresi

        Returns:
            Trend analizi
        """
        if len(self._duration_history) < window:
            return {
                "trend": "insufficient_data",
                "direction": 0,
                "slope": 0,
            }

        recent = self._duration_history[-window:]
        first_half = recent[:window // 2]
        second_half = recent[window // 2:]

        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)

        # Trend yonu
        if avg_second < avg_first * 0.95:
            direction = -1  # Iyilesiyor (sure azaliyor)
            trend = "improving"
        elif avg_second > avg_first * 1.05:
            direction = 1  # Kötülesriyor
            trend = "degrading"
        else:
            direction = 0  # Kararli
            trend = "stable"

        # Egim hesapla (basit lineer)
        slope = (avg_second - avg_first) / (window // 2) if window > 0 else 0

        return {
            "trend": trend,
            "direction": direction,
            "slope": slope,
            "first_half_avg": avg_first,
            "second_half_avg": avg_second,
            "change_percent": ((avg_second - avg_first) / avg_first) * 100 if avg_first else 0,
        }

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Analyzer istatistiklerini getir."""
        return {
            "cycles_analyzed": self._cycles_analyzed,
            "anomalies_detected": self._anomalies_detected,
            "history_size": len(self._analysis_history),
            "phases_tracked": list(self._phase_histories.keys()),
        }

    def summary(self) -> Dict[str, Any]:
        """Genel ozet."""
        recent_stats = self.get_aggregate_stats(AnalysisScope.SHORT_TERM)
        trend = self.get_trend()

        return {
            "cycles_analyzed": self._cycles_analyzed,
            "recent_average_ms": recent_stats.get("average_duration_ms", 0),
            "success_rate": recent_stats.get("success_rate", 1.0),
            "anomaly_rate": recent_stats.get("anomaly_rate", 0),
            "trend": trend.get("trend", "unknown"),
            "slowest_phases": self.get_slowest_phases(3),
        }

    def reset(self) -> None:
        """Tum gecmisi temizle."""
        self._analysis_history.clear()
        self._duration_history.clear()
        self._phase_histories.clear()
        self._cycles_analyzed = 0
        self._anomalies_detected = 0


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_cycle_analyzer(
    config: Optional[AnalyzerConfig] = None,
) -> CycleAnalyzer:
    """CycleAnalyzer factory."""
    return CycleAnalyzer(config)


# Singleton
_default_analyzer: Optional[CycleAnalyzer] = None


def get_cycle_analyzer() -> CycleAnalyzer:
    """Default CycleAnalyzer getir."""
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = CycleAnalyzer()
    return _default_analyzer


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "AnalyzerConfig",
    "CycleAnalyzer",
    "create_cycle_analyzer",
    "get_cycle_analyzer",
]
