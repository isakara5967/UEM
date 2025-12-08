"""
UEM v2 - Cycle Metrics

Cognitive cycle'a özel metrik tanımları ve tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class MetricType(str, Enum):
    """Metrik türleri."""
    DURATION = "duration"       # Süre (ms)
    COUNT = "count"             # Sayaç
    GAUGE = "gauge"             # Anlık değer
    DELTA = "delta"             # Değişim miktarı


@dataclass
class PhaseMetrics:
    """Tek bir phase'in metrikleri."""
    phase_name: str
    duration_ms: float = 0.0
    success: bool = True
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Phase-specific counters
    operations_count: int = 0
    items_processed: int = 0

    # Optional detailed metrics
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CycleMetrics:
    """
    Tek bir cycle'ın tüm metrikleri.

    Kullanım:
        metrics = CycleMetrics(cycle_id=1)
        metrics.record_phase_start("sense")
        # ... phase çalışır ...
        metrics.record_phase_end("sense", success=True)
    """
    cycle_id: int
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # Phase metrikleri
    phase_metrics: Dict[str, PhaseMetrics] = field(default_factory=dict)

    # Cycle-level metrics
    total_duration_ms: float = 0.0
    success: bool = True

    # Memory metrics
    memory_retrievals: int = 0
    memory_stores: int = 0
    working_memory_size: int = 0

    # Trust metrics
    trust_queries: int = 0
    trust_updates: int = 0
    trust_changes: List[Dict[str, Any]] = field(default_factory=list)

    # Event metrics
    events_emitted: int = 0
    events_processed: int = 0

    def record_phase_start(self, phase_name: str) -> None:
        """Phase başlangıcını kaydet."""
        self.phase_metrics[phase_name] = PhaseMetrics(
            phase_name=phase_name,
            start_time=datetime.now(),
        )

    def record_phase_end(
        self,
        phase_name: str,
        success: bool = True,
        **details: Any,
    ) -> None:
        """Phase bitişini kaydet."""
        if phase_name not in self.phase_metrics:
            self.phase_metrics[phase_name] = PhaseMetrics(phase_name=phase_name)

        pm = self.phase_metrics[phase_name]
        pm.end_time = datetime.now()
        pm.success = success
        pm.details.update(details)

        if pm.start_time:
            pm.duration_ms = (pm.end_time - pm.start_time).total_seconds() * 1000

    def record_memory_retrieval(self, count: int = 1) -> None:
        """Memory retrieval kaydet."""
        self.memory_retrievals += count

    def record_memory_store(self, count: int = 1) -> None:
        """Memory store kaydet."""
        self.memory_stores += count

    def record_trust_change(
        self,
        entity_id: str,
        old_value: float,
        new_value: float,
        reason: str = "",
    ) -> None:
        """Trust değişikliği kaydet."""
        self.trust_updates += 1
        self.trust_changes.append({
            "entity_id": entity_id,
            "old_value": old_value,
            "new_value": new_value,
            "delta": new_value - old_value,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })

    def finalize(self) -> None:
        """Cycle sonlandır ve toplam süreyi hesapla."""
        self.end_time = datetime.now()
        self.total_duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

        # Tüm phase'lerin başarı durumunu kontrol et
        self.success = all(pm.success for pm in self.phase_metrics.values())

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye dönüştür."""
        return {
            "cycle_id": self.cycle_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": self.total_duration_ms,
            "success": self.success,
            "phases": {
                name: {
                    "duration_ms": pm.duration_ms,
                    "success": pm.success,
                    "operations": pm.operations_count,
                    "items": pm.items_processed,
                }
                for name, pm in self.phase_metrics.items()
            },
            "memory": {
                "retrievals": self.memory_retrievals,
                "stores": self.memory_stores,
                "working_memory_size": self.working_memory_size,
            },
            "trust": {
                "queries": self.trust_queries,
                "updates": self.trust_updates,
                "changes": self.trust_changes,
            },
            "events": {
                "emitted": self.events_emitted,
                "processed": self.events_processed,
            },
        }

    def get_phase_summary(self) -> Dict[str, float]:
        """Phase sürelerinin özetini getir."""
        return {
            name: pm.duration_ms
            for name, pm in self.phase_metrics.items()
        }

    def get_slowest_phase(self) -> Optional[str]:
        """En yavaş phase'i bul."""
        if not self.phase_metrics:
            return None
        return max(
            self.phase_metrics.items(),
            key=lambda x: x[1].duration_ms,
        )[0]


class CycleMetricsHistory:
    """
    Cycle metrik geçmişi.

    Son N cycle'ın metriklerini tutar ve analiz sağlar.
    """

    def __init__(self, max_history: int = 1000):
        self._history: List[CycleMetrics] = []
        self._max_history = max_history

    def add(self, metrics: CycleMetrics) -> None:
        """Cycle metriği ekle."""
        self._history.append(metrics)

        # History limit
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_last(self, n: int = 10) -> List[CycleMetrics]:
        """Son N cycle'ın metriklerini getir."""
        return self._history[-n:]

    def get_average_duration(self, n: int = 100) -> float:
        """Son N cycle'ın ortalama süresini hesapla."""
        recent = self.get_last(n)
        if not recent:
            return 0.0
        return sum(m.total_duration_ms for m in recent) / len(recent)

    def get_phase_averages(self, n: int = 100) -> Dict[str, float]:
        """Son N cycle'da phase ortalamalarını hesapla."""
        recent = self.get_last(n)
        if not recent:
            return {}

        phase_totals: Dict[str, List[float]] = {}
        for cycle in recent:
            for name, pm in cycle.phase_metrics.items():
                if name not in phase_totals:
                    phase_totals[name] = []
                phase_totals[name].append(pm.duration_ms)

        return {
            name: sum(times) / len(times)
            for name, times in phase_totals.items()
        }

    def get_success_rate(self, n: int = 100) -> float:
        """Son N cycle'ın başarı oranını hesapla."""
        recent = self.get_last(n)
        if not recent:
            return 0.0
        return sum(1 for m in recent if m.success) / len(recent)

    def get_memory_stats(self, n: int = 100) -> Dict[str, float]:
        """Son N cycle'ın memory istatistiklerini getir."""
        recent = self.get_last(n)
        if not recent:
            return {"avg_retrievals": 0, "avg_stores": 0}

        return {
            "avg_retrievals": sum(m.memory_retrievals for m in recent) / len(recent),
            "avg_stores": sum(m.memory_stores for m in recent) / len(recent),
            "total_retrievals": sum(m.memory_retrievals for m in recent),
            "total_stores": sum(m.memory_stores for m in recent),
        }

    def get_trust_stats(self, n: int = 100) -> Dict[str, Any]:
        """Son N cycle'ın trust istatistiklerini getir."""
        recent = self.get_last(n)
        if not recent:
            return {"total_changes": 0, "avg_delta": 0}

        all_changes = []
        for m in recent:
            all_changes.extend(m.trust_changes)

        if not all_changes:
            return {"total_changes": 0, "avg_delta": 0}

        return {
            "total_changes": len(all_changes),
            "avg_delta": sum(c["delta"] for c in all_changes) / len(all_changes),
            "positive_changes": sum(1 for c in all_changes if c["delta"] > 0),
            "negative_changes": sum(1 for c in all_changes if c["delta"] < 0),
        }

    @property
    def count(self) -> int:
        """Toplam kayıtlı cycle sayısı."""
        return len(self._history)
