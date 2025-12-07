"""
UEM v2 - Metrics Collector

Sistem metriklerini toplama ve izleme.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import statistics


@dataclass
class Metric:
    """Tek bir metrik ölçümü."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Metric({self.name}={self.value:.3f})"


@dataclass
class MetricSummary:
    """Metrik özeti (aggregation)."""
    name: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    sum_value: float
    last_value: float
    stddev: Optional[float] = None


class MetricsCollector:
    """
    Sistem metriklerini toplayan collector.
    
    Usage:
        collector = MetricsCollector()
        collector.record("cycle_duration_ms", 45.2)
        collector.record("phase_duration_ms", 12.1, phase="sense")
        
        summary = collector.get_summary("cycle_duration_ms")
    """
    
    def __init__(self, max_history_per_metric: int = 10000):
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._max_history = max_history_per_metric
        self._start_time = datetime.now()
    
    def record(
        self,
        name: str,
        value: float,
        **tags: str,
    ) -> Metric:
        """
        Metrik kaydet.
        
        Args:
            name: Metrik adı (örn: "cycle_duration_ms")
            value: Değer
            **tags: Etiketler (örn: phase="sense")
            
        Returns:
            Oluşturulan Metric
        """
        metric = Metric(name=name, value=value, tags=tags)
        self._metrics[name].append(metric)
        
        # History limit
        if len(self._metrics[name]) > self._max_history:
            self._metrics[name] = self._metrics[name][-self._max_history:]
        
        return metric
    
    def increment(
        self,
        name: str,
        amount: float = 1.0,
        **tags: str,
    ) -> Metric:
        """Counter artır."""
        # Son değeri al ve artır
        last = self.get_last(name)
        new_value = (last.value if last else 0) + amount
        return self.record(name, new_value, **tags)
    
    def gauge(
        self,
        name: str,
        value: float,
        **tags: str,
    ) -> Metric:
        """Gauge (anlık değer) kaydet."""
        return self.record(name, value, **tags)
    
    def timer(
        self,
        name: str,
        duration_ms: float,
        **tags: str,
    ) -> Metric:
        """Süre kaydet."""
        return self.record(name, duration_ms, **tags)
    
    def get_last(self, name: str) -> Optional[Metric]:
        """Son kaydedilen metriği getir."""
        if name in self._metrics and self._metrics[name]:
            return self._metrics[name][-1]
        return None
    
    def get_history(
        self,
        name: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Metric]:
        """Metrik geçmişini getir."""
        metrics = self._metrics.get(name, [])
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics[-limit:]
    
    def get_summary(
        self,
        name: str,
        since: Optional[datetime] = None,
    ) -> Optional[MetricSummary]:
        """Metrik özetini hesapla."""
        metrics = self.get_history(name, limit=self._max_history, since=since)
        
        if not metrics:
            return None
        
        values = [m.value for m in metrics]
        
        return MetricSummary(
            name=name,
            count=len(values),
            min_value=min(values),
            max_value=max(values),
            avg_value=statistics.mean(values),
            sum_value=sum(values),
            last_value=values[-1],
            stddev=statistics.stdev(values) if len(values) > 1 else None,
        )
    
    def get_all_names(self) -> List[str]:
        """Tüm metrik adlarını listele."""
        return list(self._metrics.keys())
    
    def clear(self, name: Optional[str] = None) -> None:
        """Metrikleri temizle."""
        if name:
            self._metrics.pop(name, None)
        else:
            self._metrics.clear()
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Collector istatistikleri."""
        total_metrics = sum(len(v) for v in self._metrics.values())
        return {
            "metric_names": len(self._metrics),
            "total_records": total_metrics,
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
        }


# Singleton instance
_default_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Default metrics collector'ı getir."""
    global _default_collector
    if _default_collector is None:
        _default_collector = MetricsCollector()
    return _default_collector
