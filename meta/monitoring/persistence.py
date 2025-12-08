"""
UEM v2 - Monitoring Persistence

PostgreSQL'e monitoring verilerini kaydetme.
Dashboard farklı process'te çalıştığında verilere erişebilmesi için.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import json

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from core.memory.persistence.repository import get_session, get_engine
from core.memory.persistence.models import (
    CycleMetricModel,
    ActivityLogModel,
    RelationshipModel,
    EpisodeModel,
    TrustHistoryModel,
)
from engine.events import Event, EventType, EventBus, get_event_bus

logger = logging.getLogger(__name__)


class MonitoringPersistence:
    """
    Monitoring verilerini PostgreSQL'e kaydeden sınıf.

    Event bus'ı dinler ve cycle/phase metriklerini DB'ye yazar.

    Usage:
        persistence = MonitoringPersistence()
        persistence.start()

        # ... cycles run ...

        persistence.stop()
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        database_url: Optional[str] = None,
    ):
        self.event_bus = event_bus or get_event_bus()
        self._database_url = database_url
        self._running = False

        # Track current cycle for phase durations
        self._current_cycle_id: Optional[int] = None
        self._current_cycle_started: Optional[datetime] = None
        self._phase_durations: Dict[str, float] = {}

    def start(self) -> None:
        """Monitoring persistence'ı başlat."""
        if self._running:
            return

        self._running = True
        self.event_bus.subscribe_all(self._handle_event)
        logger.info("Monitoring persistence started")

    def stop(self) -> None:
        """Monitoring persistence'ı durdur."""
        self._running = False
        logger.info("Monitoring persistence stopped")

    def _get_session(self) -> Session:
        """Get database session."""
        if self._database_url:
            engine = get_engine(self._database_url)
            return get_session(engine)
        return get_session()

    def _handle_event(self, event: Event) -> None:
        """Handle incoming events."""
        if not self._running:
            return

        try:
            if event.event_type == EventType.CYCLE_START:
                self._on_cycle_start(event)
            elif event.event_type == EventType.CYCLE_END:
                self._on_cycle_end(event)
            elif event.event_type == EventType.MODULE_END:
                self._on_phase_end(event)

            # Log important events
            if event.event_type in {
                EventType.EMOTION_CHANGED,
                EventType.TRUST_UPDATED,
                EventType.THREAT_DETECTED,
                EventType.ACTION_EXECUTED,
                EventType.ANOMALY_DETECTED,
            }:
                self._log_activity(event)

        except Exception as e:
            logger.error(f"Error handling event {event.event_type}: {e}")

    def _on_cycle_start(self, event: Event) -> None:
        """Handle cycle start."""
        self._current_cycle_id = event.data.get("cycle_id", event.cycle_id)
        self._current_cycle_started = event.timestamp
        self._phase_durations = {}

    def _on_phase_end(self, event: Event) -> None:
        """Handle phase end - collect duration."""
        phase = event.data.get("phase", "unknown")
        duration_ms = event.data.get("duration_ms", 0)
        self._phase_durations[phase] = duration_ms

    def _on_cycle_end(self, event: Event) -> None:
        """Handle cycle end - save to DB."""
        cycle_id = event.data.get("cycle_id", event.cycle_id) or self._current_cycle_id
        duration_ms = event.data.get("duration_ms", 0)
        success = event.data.get("success", True)
        error_message = event.data.get("error")

        session = self._get_session()
        try:
            metric = CycleMetricModel(
                cycle_id=cycle_id or 0,
                started_at=self._current_cycle_started or datetime.now(),
                ended_at=event.timestamp,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                phase_durations=self._phase_durations,
            )
            session.add(metric)
            session.commit()
            logger.debug(f"Saved cycle metric: cycle_id={cycle_id}, duration={duration_ms}ms")
        except Exception as e:
            logger.error(f"Error saving cycle metric: {e}")
            session.rollback()
        finally:
            session.close()

        # Reset for next cycle
        self._current_cycle_id = None
        self._current_cycle_started = None
        self._phase_durations = {}

    def _log_activity(self, event: Event) -> None:
        """Log activity to database."""
        session = self._get_session()
        try:
            # Serialize event data
            data = {}
            for k, v in event.data.items():
                try:
                    json.dumps(v)  # Test if serializable
                    data[k] = v
                except (TypeError, ValueError):
                    data[k] = str(v)

            activity = ActivityLogModel(
                event_type=event.event_type.value,
                source=event.source,
                cycle_id=event.cycle_id,
                data=data,
                created_at=event.timestamp,
            )
            session.add(activity)
            session.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            session.rollback()
        finally:
            session.close()


class DashboardDataProvider:
    """
    Dashboard için PostgreSQL'den veri sağlayan sınıf.

    Dashboard bu sınıfı kullanarak metrikleri okur.
    """

    def __init__(self, database_url: Optional[str] = None):
        self._database_url = database_url

    def _get_session(self) -> Session:
        """Get database session."""
        if self._database_url:
            engine = get_engine(self._database_url)
            return get_session(engine)
        return get_session()

    def get_cycle_metrics(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get cycle metrics summary.

        Returns:
            {
                "total": int,
                "success_count": int,
                "failed_count": int,
                "success_rate": float,
                "avg_duration_ms": float,
            }
        """
        session = self._get_session()
        try:
            total = session.query(CycleMetricModel).count()
            success_count = session.query(CycleMetricModel).filter(
                CycleMetricModel.success == True
            ).count()
            failed_count = total - success_count

            avg_duration = session.query(
                func.avg(CycleMetricModel.duration_ms)
            ).scalar() or 0

            success_rate = (success_count / total * 100) if total > 0 else 0

            return {
                "total": total,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": success_rate,
                "avg_duration_ms": avg_duration,
            }
        finally:
            session.close()

    def get_phase_durations(self, limit: int = 100) -> Dict[str, float]:
        """
        Get average phase durations.

        Returns:
            {"1_sense": 12.5, "2_attend": 8.3, ...}
        """
        session = self._get_session()
        try:
            # Get recent cycles
            cycles = session.query(CycleMetricModel).order_by(
                desc(CycleMetricModel.started_at)
            ).limit(limit).all()

            if not cycles:
                return {}

            # Aggregate phase durations
            phase_totals: Dict[str, List[float]] = {}
            for cycle in cycles:
                if cycle.phase_durations:
                    for phase, duration in cycle.phase_durations.items():
                        if phase not in phase_totals:
                            phase_totals[phase] = []
                        phase_totals[phase].append(duration)

            # Calculate averages
            return {
                phase: sum(durations) / len(durations)
                for phase, durations in phase_totals.items()
            }
        finally:
            session.close()

    def get_memory_stats(self) -> Dict[str, int]:
        """
        Get memory statistics.

        Returns:
            {"episodes": int, "relationships": int, "retrievals": int}
        """
        session = self._get_session()
        try:
            episodes = session.query(EpisodeModel).count()
            relationships = session.query(RelationshipModel).count()

            # Retrievals from activity log
            retrievals = session.query(ActivityLogModel).filter(
                ActivityLogModel.event_type == "memory.retrieved"
            ).count()

            return {
                "episodes": episodes,
                "relationships": relationships,
                "retrievals": retrievals,
            }
        finally:
            session.close()

    def get_trust_levels(self, limit: int = 20) -> Dict[str, float]:
        """
        Get trust levels per agent.

        Returns:
            {"alice": 0.85, "bob": 0.45, ...}
        """
        session = self._get_session()
        try:
            relationships = session.query(RelationshipModel).order_by(
                desc(RelationshipModel.trust_score)
            ).limit(limit).all()

            return {
                rel.agent_id: rel.trust_score
                for rel in relationships
            }
        finally:
            session.close()

    def get_recent_activity(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent activity log.

        Returns:
            [{"event_type": str, "source": str, "created_at": str, ...}, ...]
        """
        session = self._get_session()
        try:
            activities = session.query(ActivityLogModel).order_by(
                desc(ActivityLogModel.created_at)
            ).limit(limit).all()

            return [activity.to_dict() for activity in activities]
        finally:
            session.close()

    def get_all_dashboard_data(self) -> Dict[str, Any]:
        """
        Get all dashboard data in one call.

        Returns:
            {
                "cycle_metrics": {...},
                "phase_durations": {...},
                "memory_stats": {...},
                "trust_levels": {...},
                "recent_activity": [...],
            }
        """
        return {
            "cycle_metrics": self.get_cycle_metrics(),
            "phase_durations": self.get_phase_durations(),
            "memory_stats": self.get_memory_stats(),
            "trust_levels": self.get_trust_levels(),
            "recent_activity": self.get_recent_activity(),
        }


# Singleton instances
_persistence: Optional[MonitoringPersistence] = None
_data_provider: Optional[DashboardDataProvider] = None


def get_monitoring_persistence() -> MonitoringPersistence:
    """Get singleton MonitoringPersistence instance."""
    global _persistence
    if _persistence is None:
        _persistence = MonitoringPersistence()
    return _persistence


def get_dashboard_data_provider() -> DashboardDataProvider:
    """Get singleton DashboardDataProvider instance."""
    global _data_provider
    if _data_provider is None:
        _data_provider = DashboardDataProvider()
    return _data_provider
