"""
UEM v2 - System Monitor

Event bus ile entegre sistem izleme.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import logging

from .metrics.collector import MetricsCollector, get_metrics_collector
from engine.events import Event, EventType, EventBus, get_event_bus

logger = logging.getLogger(__name__)


@dataclass
class MonitorConfig:
    """Monitor yapılandırması."""
    collect_cycle_metrics: bool = True
    collect_phase_metrics: bool = True
    collect_event_metrics: bool = True
    log_events: bool = False
    alert_on_slow_cycle_ms: float = 1000.0
    alert_on_slow_phase_ms: float = 500.0


class SystemMonitor:
    """
    Sistem monitörü - event bus'ı dinler, metrikleri toplar.
    
    Usage:
        monitor = SystemMonitor()
        monitor.start()
        
        # ... cycle'lar çalışır ...
        
        report = monitor.get_report()
        monitor.stop()
    """
    
    def __init__(
        self,
        config: Optional[MonitorConfig] = None,
        event_bus: Optional[EventBus] = None,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        self.config = config or MonitorConfig()
        self.event_bus = event_bus or get_event_bus()
        self.metrics = metrics_collector or get_metrics_collector()
        
        self._running = False
        self._cycle_start_times: Dict[int, datetime] = {}
        self._phase_start_times: Dict[str, datetime] = {}
        self._alert_handlers: List[Callable[[str, Dict], None]] = []
    
    def start(self) -> None:
        """Monitoring başlat."""
        if self._running:
            return
        
        self._running = True
        self.event_bus.subscribe_all(self._handle_event)
        logger.info("System monitor started")
    
    def stop(self) -> None:
        """Monitoring durdur."""
        self._running = False
        logger.info("System monitor stopped")
    
    def add_alert_handler(
        self,
        handler: Callable[[str, Dict], None],
    ) -> None:
        """Alert handler ekle."""
        self._alert_handlers.append(handler)
    
    def _handle_event(self, event: Event) -> None:
        """Event handler - tüm eventleri işle."""
        if not self._running:
            return
        
        # Event count
        if self.config.collect_event_metrics:
            self.metrics.increment("events_total", event_type=event.event_type.value)
        
        # Log
        if self.config.log_events:
            logger.debug(f"Event: {event}")
        
        # Specific handlers
        if event.event_type == EventType.CYCLE_START:
            self._on_cycle_start(event)
        elif event.event_type == EventType.CYCLE_END:
            self._on_cycle_end(event)
        elif event.event_type == EventType.MODULE_START:
            self._on_phase_start(event)
        elif event.event_type == EventType.MODULE_END:
            self._on_phase_end(event)
    
    def _on_cycle_start(self, event: Event) -> None:
        """Cycle başlangıcı."""
        cycle_id = event.data.get("cycle_id", event.cycle_id)
        if cycle_id:
            self._cycle_start_times[cycle_id] = event.timestamp
            self.metrics.increment("cycles_started")
    
    def _on_cycle_end(self, event: Event) -> None:
        """Cycle bitişi."""
        if not self.config.collect_cycle_metrics:
            return
        
        cycle_id = event.data.get("cycle_id", event.cycle_id)
        duration_ms = event.data.get("duration_ms", 0)
        success = event.data.get("success", True)
        
        # Metrics
        self.metrics.timer("cycle_duration_ms", duration_ms)
        self.metrics.increment("cycles_completed")
        
        if success:
            self.metrics.increment("cycles_success")
        else:
            self.metrics.increment("cycles_failed")
        
        # Alert check
        if duration_ms > self.config.alert_on_slow_cycle_ms:
            self._fire_alert("slow_cycle", {
                "cycle_id": cycle_id,
                "duration_ms": duration_ms,
                "threshold_ms": self.config.alert_on_slow_cycle_ms,
            })
        
        # Cleanup
        if cycle_id and cycle_id in self._cycle_start_times:
            del self._cycle_start_times[cycle_id]
    
    def _on_phase_start(self, event: Event) -> None:
        """Phase başlangıcı."""
        phase = event.data.get("phase", "unknown")
        cycle_id = event.data.get("cycle_id", event.cycle_id)
        key = f"{cycle_id}_{phase}"
        self._phase_start_times[key] = event.timestamp
    
    def _on_phase_end(self, event: Event) -> None:
        """Phase bitişi."""
        if not self.config.collect_phase_metrics:
            return
        
        phase = event.data.get("phase", "unknown")
        duration_ms = event.data.get("duration_ms", 0)
        success = event.data.get("success", True)
        
        # Metrics
        self.metrics.timer("phase_duration_ms", duration_ms, phase=phase)
        self.metrics.increment("phases_completed", phase=phase)
        
        if not success:
            self.metrics.increment("phases_failed", phase=phase)
        
        # Alert check
        if duration_ms > self.config.alert_on_slow_phase_ms:
            self._fire_alert("slow_phase", {
                "phase": phase,
                "duration_ms": duration_ms,
                "threshold_ms": self.config.alert_on_slow_phase_ms,
            })
    
    def _fire_alert(self, alert_type: str, data: Dict) -> None:
        """Alert tetikle."""
        self.metrics.increment(f"alerts_{alert_type}")
        
        logger.warning(f"Alert: {alert_type} - {data}")
        
        for handler in self._alert_handlers:
            try:
                handler(alert_type, data)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
    
    def get_report(self) -> Dict[str, Any]:
        """Monitoring raporu oluştur."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "running": self._running,
            "summaries": {},
        }
        
        # Tüm metriklerin özetini al
        for name in self.metrics.get_all_names():
            summary = self.metrics.get_summary(name)
            if summary:
                report["summaries"][name] = {
                    "count": summary.count,
                    "min": summary.min_value,
                    "max": summary.max_value,
                    "avg": summary.avg_value,
                    "last": summary.last_value,
                }
        
        report["collector_stats"] = self.metrics.stats
        
        return report


# Singleton instance
_default_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """Default system monitor'ı getir."""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = SystemMonitor()
    return _default_monitor
