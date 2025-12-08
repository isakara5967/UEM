"""
UEM v2 - Monitoring Reporter

Console ve log output için rapor formatları.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TextIO
from datetime import datetime
import logging
import sys

from .metrics.cycle import CycleMetrics, CycleMetricsHistory
from .metrics.collector import MetricsCollector, get_metrics_collector

logger = logging.getLogger(__name__)


@dataclass
class ReporterConfig:
    """Reporter yapılandırması."""
    # Output hedefleri
    console_enabled: bool = True
    log_enabled: bool = True

    # Format ayarları
    show_phase_details: bool = True
    show_memory_stats: bool = True
    show_trust_stats: bool = True
    show_timestamps: bool = False

    # Threshold'lar (vurgulamak için)
    slow_cycle_ms: float = 100.0
    slow_phase_ms: float = 50.0

    # Bar chart ayarları
    bar_width: int = 30
    bar_char: str = "█"
    bar_empty: str = "░"


class MonitoringReporter:
    """
    Monitoring verilerini console/log'a yazdıran reporter.

    Kullanım:
        reporter = MonitoringReporter()
        reporter.report_cycle(cycle_metrics)
        reporter.report_summary(metrics_history)
    """

    def __init__(
        self,
        config: Optional[ReporterConfig] = None,
        output: Optional[TextIO] = None,
    ):
        self.config = config or ReporterConfig()
        self.output = output or sys.stdout

    def _write(self, text: str) -> None:
        """Output'a yaz."""
        if self.config.console_enabled:
            print(text, file=self.output)
        if self.config.log_enabled:
            logger.info(text)

    def _format_duration(self, ms: float) -> str:
        """Süreyi formatla."""
        if ms < 1:
            return f"{ms*1000:.1f}μs"
        elif ms < 1000:
            return f"{ms:.1f}ms"
        else:
            return f"{ms/1000:.2f}s"

    def _make_bar(self, value: float, max_value: float) -> str:
        """ASCII progress bar oluştur."""
        if max_value == 0:
            return self.config.bar_empty * self.config.bar_width

        ratio = min(value / max_value, 1.0)
        filled = int(ratio * self.config.bar_width)
        empty = self.config.bar_width - filled

        return self.config.bar_char * filled + self.config.bar_empty * empty

    def _status_icon(self, success: bool) -> str:
        """Başarı durumu ikonu."""
        return "[OK]" if success else "[FAIL]"

    # =========================================================================
    # Cycle Reports
    # =========================================================================

    def report_cycle(self, metrics: CycleMetrics) -> None:
        """
        Tek bir cycle'ın raporunu yazdır.

        Örnek çıktı:
            ══════════════════════════════════════════════════════════════
            CYCLE #42 [OK]  Total: 45.2ms
            ══════════════════════════════════════════════════════════════
            Phase Durations:
              SENSE    ████████░░░░░░░░░░░░░░░░░░░░░░  8.2ms
              PERCEIVE ██████████████░░░░░░░░░░░░░░░░ 15.1ms
              RETRIEVE ████░░░░░░░░░░░░░░░░░░░░░░░░░░  4.3ms
              ...
        """
        is_slow = metrics.total_duration_ms > self.config.slow_cycle_ms
        slow_marker = " [!SLOW]" if is_slow else ""

        # Header
        self._write("")
        self._write("═" * 60)
        self._write(
            f"CYCLE #{metrics.cycle_id} {self._status_icon(metrics.success)}  "
            f"Total: {self._format_duration(metrics.total_duration_ms)}{slow_marker}"
        )
        self._write("═" * 60)

        # Timestamps
        if self.config.show_timestamps:
            self._write(f"  Start: {metrics.start_time.isoformat()}")
            if metrics.end_time:
                self._write(f"  End:   {metrics.end_time.isoformat()}")

        # Phase durations
        if self.config.show_phase_details and metrics.phase_metrics:
            self._write("")
            self._write("Phase Durations:")

            max_duration = max(
                pm.duration_ms for pm in metrics.phase_metrics.values()
            ) if metrics.phase_metrics else 1

            for name, pm in metrics.phase_metrics.items():
                bar = self._make_bar(pm.duration_ms, max_duration)
                status = "" if pm.success else " [FAIL]"
                slow = " [!]" if pm.duration_ms > self.config.slow_phase_ms else ""

                self._write(
                    f"  {name:12} {bar} {self._format_duration(pm.duration_ms)}{status}{slow}"
                )

        # Memory stats
        if self.config.show_memory_stats and (metrics.memory_retrievals or metrics.memory_stores):
            self._write("")
            self._write("Memory:")
            self._write(f"  Retrievals: {metrics.memory_retrievals}")
            self._write(f"  Stores:     {metrics.memory_stores}")
            self._write(f"  Working:    {metrics.working_memory_size} items")

        # Trust stats
        if self.config.show_trust_stats and metrics.trust_changes:
            self._write("")
            self._write("Trust Changes:")
            for change in metrics.trust_changes[-5:]:  # Son 5 değişiklik
                delta = change["delta"]
                direction = "+" if delta > 0 else ""
                self._write(
                    f"  {change['entity_id']}: {direction}{delta:.3f} ({change['reason']})"
                )

        self._write("")

    def report_cycle_compact(self, metrics: CycleMetrics) -> None:
        """
        Cycle'ı tek satırda raporla.

        Örnek:
            Cycle #42 [OK] 45.2ms | Phases: 10 | Mem: 5r/2w | Trust: +2/-0
        """
        status = "OK" if metrics.success else "FAIL"
        duration = self._format_duration(metrics.total_duration_ms)
        phases = len(metrics.phase_metrics)

        mem_r = metrics.memory_retrievals
        mem_w = metrics.memory_stores

        trust_pos = sum(1 for c in metrics.trust_changes if c["delta"] > 0)
        trust_neg = sum(1 for c in metrics.trust_changes if c["delta"] < 0)

        line = (
            f"Cycle #{metrics.cycle_id} [{status}] {duration} | "
            f"Phases: {phases} | Mem: {mem_r}r/{mem_w}w | "
            f"Trust: +{trust_pos}/-{trust_neg}"
        )

        self._write(line)

    # =========================================================================
    # Summary Reports
    # =========================================================================

    def report_summary(
        self,
        history: CycleMetricsHistory,
        last_n: int = 100,
    ) -> None:
        """
        Son N cycle'ın özet raporunu yazdır.

        Örnek:
            ══════════════════════════════════════════════════════════════
            MONITORING SUMMARY (Last 100 cycles)
            ══════════════════════════════════════════════════════════════
            Success Rate:    98.0%
            Avg Duration:    42.3ms
            Total Cycles:    100

            Phase Averages:
              SENSE       5.2ms
              PERCEIVE   12.1ms
              ...
        """
        self._write("")
        self._write("═" * 60)
        self._write(f"MONITORING SUMMARY (Last {last_n} cycles)")
        self._write("═" * 60)

        # Basic stats
        success_rate = history.get_success_rate(last_n) * 100
        avg_duration = history.get_average_duration(last_n)

        self._write(f"  Success Rate:  {success_rate:.1f}%")
        self._write(f"  Avg Duration:  {self._format_duration(avg_duration)}")
        self._write(f"  Total Cycles:  {history.count}")

        # Phase averages
        phase_avgs = history.get_phase_averages(last_n)
        if phase_avgs:
            self._write("")
            self._write("Phase Averages:")
            max_avg = max(phase_avgs.values()) if phase_avgs else 1

            for name, avg in sorted(phase_avgs.items(), key=lambda x: x[1], reverse=True):
                bar = self._make_bar(avg, max_avg)
                self._write(f"  {name:12} {bar} {self._format_duration(avg)}")

        # Memory stats
        mem_stats = history.get_memory_stats(last_n)
        if mem_stats.get("total_retrievals", 0) > 0:
            self._write("")
            self._write("Memory Stats:")
            self._write(f"  Avg Retrievals/cycle:  {mem_stats['avg_retrievals']:.1f}")
            self._write(f"  Avg Stores/cycle:      {mem_stats['avg_stores']:.1f}")
            self._write(f"  Total Retrievals:      {mem_stats['total_retrievals']}")
            self._write(f"  Total Stores:          {mem_stats['total_stores']}")

        # Trust stats
        trust_stats = history.get_trust_stats(last_n)
        if trust_stats.get("total_changes", 0) > 0:
            self._write("")
            self._write("Trust Stats:")
            self._write(f"  Total Changes:   {trust_stats['total_changes']}")
            self._write(f"  Avg Delta:       {trust_stats['avg_delta']:+.3f}")
            self._write(f"  Positive:        {trust_stats['positive_changes']}")
            self._write(f"  Negative:        {trust_stats['negative_changes']}")

        self._write("")

    def report_collector_stats(
        self,
        collector: Optional[MetricsCollector] = None,
    ) -> None:
        """Collector istatistiklerini raporla."""
        collector = collector or get_metrics_collector()

        self._write("")
        self._write("─" * 40)
        self._write("METRICS COLLECTOR STATS")
        self._write("─" * 40)

        stats = collector.stats
        self._write(f"  Metric Names:   {stats['metric_names']}")
        self._write(f"  Total Records:  {stats['total_records']}")
        self._write(f"  Uptime:         {stats['uptime_seconds']:.1f}s")

        # Her metriğin son değerini göster
        self._write("")
        self._write("Recent Metrics:")
        for name in collector.get_all_names()[:10]:  # İlk 10
            summary = collector.get_summary(name)
            if summary:
                self._write(
                    f"  {name:30} last={summary.last_value:.2f} "
                    f"avg={summary.avg_value:.2f} (n={summary.count})"
                )

        self._write("")

    # =========================================================================
    # Live Reporting
    # =========================================================================

    def report_live_header(self) -> None:
        """Live monitoring header."""
        self._write("")
        self._write("┌" + "─" * 58 + "┐")
        self._write("│" + " UEM MONITORING - LIVE ".center(58) + "│")
        self._write("└" + "─" * 58 + "┘")
        self._write("")
        self._write(f"{'Cycle':<8} {'Status':<8} {'Duration':<10} {'Memory':<12} {'Trust':<10}")
        self._write("─" * 60)

    def report_live_row(self, metrics: CycleMetrics) -> None:
        """Live monitoring satırı."""
        status = "OK" if metrics.success else "FAIL"
        duration = self._format_duration(metrics.total_duration_ms)
        memory = f"{metrics.memory_retrievals}r/{metrics.memory_stores}w"
        trust_delta = sum(c["delta"] for c in metrics.trust_changes)
        trust = f"{trust_delta:+.2f}" if metrics.trust_changes else "-"

        self._write(
            f"#{metrics.cycle_id:<7} {status:<8} {duration:<10} {memory:<12} {trust:<10}"
        )


# Singleton instance
_default_reporter: Optional[MonitoringReporter] = None


def get_reporter() -> MonitoringReporter:
    """Default reporter'ı getir."""
    global _default_reporter
    if _default_reporter is None:
        _default_reporter = MonitoringReporter()
    return _default_reporter
