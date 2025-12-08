"""
UEM v2 - Monitoring Module Tests

Tests for metrics, reporter, and cycle integration.
"""

import pytest
from datetime import datetime, timedelta
from io import StringIO

from meta.monitoring.metrics import (
    Metric,
    MetricSummary,
    MetricsCollector,
    MetricType,
    PhaseMetrics,
    CycleMetrics,
    CycleMetricsHistory,
)
from meta.monitoring.reporter import (
    ReporterConfig,
    MonitoringReporter,
)
from meta.monitoring import (
    get_metrics_collector,
    get_reporter,
)


class TestMetricsCollector:
    """MetricsCollector tests."""

    def test_record_metric(self):
        """Test basic metric recording."""
        collector = MetricsCollector()
        metric = collector.record("test_metric", 42.5)

        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert isinstance(metric.timestamp, datetime)

    def test_record_with_tags(self):
        """Test metric with tags."""
        collector = MetricsCollector()
        metric = collector.record("phase_duration", 10.5, phase="sense")

        assert metric.tags == {"phase": "sense"}

    def test_increment(self):
        """Test counter increment."""
        collector = MetricsCollector()

        collector.increment("counter")
        collector.increment("counter")
        collector.increment("counter", 5)

        last = collector.get_last("counter")
        assert last.value == 7

    def test_get_summary(self):
        """Test metric summary calculation."""
        collector = MetricsCollector()

        for i in range(10):
            collector.record("test", float(i))

        summary = collector.get_summary("test")

        assert summary.count == 10
        assert summary.min_value == 0
        assert summary.max_value == 9
        assert summary.avg_value == 4.5
        assert summary.last_value == 9

    def test_get_history(self):
        """Test history retrieval."""
        collector = MetricsCollector()

        for i in range(20):
            collector.record("test", float(i))

        history = collector.get_history("test", limit=5)

        assert len(history) == 5
        assert history[0].value == 15  # 20 - 5 = 15

    def test_clear(self):
        """Test metric clearing."""
        collector = MetricsCollector()
        collector.record("test1", 1)
        collector.record("test2", 2)

        collector.clear("test1")
        assert "test1" not in collector.get_all_names()
        assert "test2" in collector.get_all_names()

        collector.clear()
        assert len(collector.get_all_names()) == 0


class TestCycleMetrics:
    """CycleMetrics tests."""

    def test_basic_cycle_metrics(self):
        """Test basic cycle metrics creation."""
        metrics = CycleMetrics(cycle_id=1)

        assert metrics.cycle_id == 1
        assert metrics.success is True
        assert metrics.memory_retrievals == 0

    def test_phase_recording(self):
        """Test phase start/end recording."""
        metrics = CycleMetrics(cycle_id=1)

        metrics.record_phase_start("sense")
        metrics.record_phase_end("sense", success=True, items=5)

        assert "sense" in metrics.phase_metrics
        pm = metrics.phase_metrics["sense"]
        assert pm.success is True
        assert pm.details.get("items") == 5

    def test_memory_tracking(self):
        """Test memory retrieval/store tracking."""
        metrics = CycleMetrics(cycle_id=1)

        metrics.record_memory_retrieval(3)
        metrics.record_memory_store(2)

        assert metrics.memory_retrievals == 3
        assert metrics.memory_stores == 2

    def test_trust_change_tracking(self):
        """Test trust change recording."""
        metrics = CycleMetrics(cycle_id=1)

        metrics.record_trust_change(
            entity_id="agent_1",
            old_value=0.5,
            new_value=0.7,
            reason="positive_interaction",
        )

        assert metrics.trust_updates == 1
        assert len(metrics.trust_changes) == 1

        change = metrics.trust_changes[0]
        assert change["entity_id"] == "agent_1"
        assert change["delta"] == pytest.approx(0.2)
        assert change["reason"] == "positive_interaction"

    def test_finalize(self):
        """Test cycle finalization."""
        metrics = CycleMetrics(cycle_id=1)
        metrics.record_phase_start("sense")
        metrics.record_phase_end("sense", success=True)
        metrics.record_phase_start("perceive")
        metrics.record_phase_end("perceive", success=False)

        metrics.finalize()

        assert metrics.end_time is not None
        assert metrics.total_duration_ms >= 0
        assert metrics.success is False  # One phase failed

    def test_to_dict(self):
        """Test dictionary conversion."""
        metrics = CycleMetrics(cycle_id=42)
        metrics.record_memory_retrieval(5)
        metrics.finalize()

        d = metrics.to_dict()

        assert d["cycle_id"] == 42
        assert d["memory"]["retrievals"] == 5
        assert "phases" in d

    def test_get_slowest_phase(self):
        """Test slowest phase detection."""
        metrics = CycleMetrics(cycle_id=1)

        # Manually set durations for testing
        metrics.phase_metrics["fast"] = PhaseMetrics(
            phase_name="fast", duration_ms=10.0
        )
        metrics.phase_metrics["slow"] = PhaseMetrics(
            phase_name="slow", duration_ms=100.0
        )
        metrics.phase_metrics["medium"] = PhaseMetrics(
            phase_name="medium", duration_ms=50.0
        )

        assert metrics.get_slowest_phase() == "slow"


class TestCycleMetricsHistory:
    """CycleMetricsHistory tests."""

    def test_add_and_get_last(self):
        """Test adding and retrieving metrics."""
        history = CycleMetricsHistory()

        for i in range(5):
            m = CycleMetrics(cycle_id=i)
            m.total_duration_ms = float(i * 10)
            history.add(m)

        last = history.get_last(3)
        assert len(last) == 3
        assert last[0].cycle_id == 2

    def test_average_duration(self):
        """Test average duration calculation."""
        history = CycleMetricsHistory()

        for i in range(10):
            m = CycleMetrics(cycle_id=i)
            m.total_duration_ms = 100.0  # All same
            history.add(m)

        avg = history.get_average_duration(10)
        assert avg == 100.0

    def test_success_rate(self):
        """Test success rate calculation."""
        history = CycleMetricsHistory()

        for i in range(10):
            m = CycleMetrics(cycle_id=i)
            m.success = i < 8  # 8 success, 2 failures
            history.add(m)

        rate = history.get_success_rate(10)
        assert rate == 0.8

    def test_phase_averages(self):
        """Test phase average calculation."""
        history = CycleMetricsHistory()

        for i in range(5):
            m = CycleMetrics(cycle_id=i)
            m.phase_metrics["sense"] = PhaseMetrics(
                phase_name="sense", duration_ms=10.0
            )
            m.phase_metrics["perceive"] = PhaseMetrics(
                phase_name="perceive", duration_ms=20.0
            )
            history.add(m)

        avgs = history.get_phase_averages(5)
        assert avgs["sense"] == 10.0
        assert avgs["perceive"] == 20.0

    def test_memory_stats(self):
        """Test memory statistics."""
        history = CycleMetricsHistory()

        for i in range(5):
            m = CycleMetrics(cycle_id=i)
            m.memory_retrievals = 10
            m.memory_stores = 5
            history.add(m)

        stats = history.get_memory_stats(5)
        assert stats["avg_retrievals"] == 10.0
        assert stats["avg_stores"] == 5.0
        assert stats["total_retrievals"] == 50

    def test_trust_stats(self):
        """Test trust statistics."""
        history = CycleMetricsHistory()

        for i in range(3):
            m = CycleMetrics(cycle_id=i)
            m.trust_changes = [
                {"entity_id": "a", "delta": 0.1},
                {"entity_id": "b", "delta": -0.05},
            ]
            history.add(m)

        stats = history.get_trust_stats(3)
        assert stats["total_changes"] == 6
        assert stats["positive_changes"] == 3
        assert stats["negative_changes"] == 3

    def test_max_history_limit(self):
        """Test history size limiting."""
        history = CycleMetricsHistory(max_history=10)

        for i in range(20):
            history.add(CycleMetrics(cycle_id=i))

        assert history.count == 10
        assert history.get_last(1)[0].cycle_id == 19


class TestMonitoringReporter:
    """MonitoringReporter tests."""

    def test_format_duration(self):
        """Test duration formatting."""
        reporter = MonitoringReporter()

        assert "μs" in reporter._format_duration(0.5)
        assert "ms" in reporter._format_duration(50)
        assert "s" in reporter._format_duration(1500)

    def test_make_bar(self):
        """Test bar chart generation."""
        config = ReporterConfig(bar_width=10, bar_char="X", bar_empty=".")
        reporter = MonitoringReporter(config=config)

        bar = reporter._make_bar(50, 100)
        assert bar == "XXXXX....."

        bar = reporter._make_bar(100, 100)
        assert bar == "XXXXXXXXXX"

        bar = reporter._make_bar(0, 100)
        assert bar == ".........."

    def test_report_cycle(self):
        """Test cycle report output."""
        output = StringIO()
        reporter = MonitoringReporter(output=output)

        metrics = CycleMetrics(cycle_id=1)
        metrics.phase_metrics["sense"] = PhaseMetrics(
            phase_name="sense", duration_ms=10.0
        )
        metrics.total_duration_ms = 50.0
        metrics.success = True

        reporter.report_cycle(metrics)

        result = output.getvalue()
        assert "CYCLE #1" in result
        assert "[OK]" in result
        assert "sense" in result

    def test_report_cycle_compact(self):
        """Test compact cycle report."""
        output = StringIO()
        reporter = MonitoringReporter(output=output)

        metrics = CycleMetrics(cycle_id=42)
        metrics.total_duration_ms = 100.0
        metrics.success = True
        metrics.memory_retrievals = 5
        metrics.memory_stores = 2

        reporter.report_cycle_compact(metrics)

        result = output.getvalue()
        assert "#42" in result
        assert "[OK]" in result
        assert "5r/2w" in result

    def test_report_summary(self):
        """Test summary report."""
        output = StringIO()
        reporter = MonitoringReporter(output=output)

        history = CycleMetricsHistory()
        for i in range(10):
            m = CycleMetrics(cycle_id=i)
            m.total_duration_ms = 50.0
            m.success = True
            history.add(m)

        reporter.report_summary(history, last_n=10)

        result = output.getvalue()
        assert "MONITORING SUMMARY" in result
        assert "Success Rate" in result
        assert "100.0%" in result

    def test_disabled_console(self):
        """Test disabled console output."""
        output = StringIO()
        config = ReporterConfig(console_enabled=False, log_enabled=False)
        reporter = MonitoringReporter(config=config, output=output)

        metrics = CycleMetrics(cycle_id=1)
        reporter.report_cycle(metrics)

        # Should be empty since both outputs disabled
        assert output.getvalue() == ""


class TestIntegration:
    """Integration tests with CognitiveCycle."""

    def test_cycle_with_monitoring(self):
        """Test CognitiveCycle with monitoring enabled."""
        from engine.cycle import CognitiveCycle, CycleConfig

        config = CycleConfig(
            enable_monitoring=True,
            report_each_cycle=False,
        )
        cycle = CognitiveCycle(config=config)

        # Run a cycle
        result = cycle.run()

        # Check metrics recorded
        assert cycle.metrics_history.count == 1

        last_metrics = cycle.metrics_history.get_last(1)[0]
        assert last_metrics.cycle_id == 1
        assert last_metrics.total_duration_ms >= 0

    def test_multiple_cycles_tracking(self):
        """Test multiple cycles metric tracking."""
        from engine.cycle import CognitiveCycle, CycleConfig

        config = CycleConfig(enable_monitoring=True)
        cycle = CognitiveCycle(config=config)

        # Run multiple cycles
        for _ in range(5):
            cycle.run()

        assert cycle.metrics_history.count == 5

        stats = cycle.get_stats()
        assert "monitoring" in stats
        assert stats["monitoring"]["history_count"] == 5

    def test_cycle_metrics_in_context(self):
        """Test that cycle_metrics is available in context."""
        from engine.cycle import CognitiveCycle, CycleConfig, PhaseHandler
        from engine.phases import Phase, PhaseResult
        from foundation.state import StateVector
        from foundation.types import Context

        config = CycleConfig(enable_monitoring=True)
        cycle = CognitiveCycle(config=config)

        metrics_found = []

        def test_handler(
            phase: Phase, state: StateVector, context: Context
        ) -> PhaseResult:
            # Check if cycle_metrics is in context
            cm = context.metadata.get("cycle_metrics")
            metrics_found.append(cm is not None)

            # Record some metrics
            if cm:
                cm.record_memory_retrieval(3)

            return PhaseResult(phase=phase, success=True)

        cycle.register_handler(Phase.SENSE, test_handler)
        cycle.run()

        assert all(metrics_found)

        last_metrics = cycle.metrics_history.get_last(1)[0]
        assert last_metrics.memory_retrievals == 3
