"""
UEM v2 - Event Bus

Modüller arası iletişim sistemi (Pub/Sub pattern).
Spagetti import yerine temiz, gevşek bağlı iletişim.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Sistem event tipleri."""
    
    # Lifecycle events
    CYCLE_START = "cycle.start"
    CYCLE_END = "cycle.end"
    MODULE_START = "module.start"
    MODULE_END = "module.end"
    
    # Perception events
    STIMULUS_RECEIVED = "perception.stimulus_received"
    ENTITY_DETECTED = "perception.entity_detected"
    THREAT_DETECTED = "perception.threat_detected"
    ATTENTION_SHIFT = "perception.attention_shift"
    
    # Cognition events
    REASONING_COMPLETE = "cognition.reasoning_complete"
    HYPOTHESIS_GENERATED = "cognition.hypothesis_generated"
    EVALUATION_COMPLETE = "cognition.evaluation_complete"
    
    # Memory events
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    MEMORY_CONSOLIDATED = "memory.consolidated"
    
    # Affect events
    EMOTION_CHANGED = "affect.emotion_changed"
    EMPATHY_COMPUTED = "affect.empathy_computed"
    TRUST_UPDATED = "affect.trust_updated"
    
    # Self events
    VALUE_CONFLICT = "self.value_conflict"
    INTEGRITY_CHECK = "self.integrity_check"
    
    # Executive events
    ACTION_SELECTED = "executive.action_selected"
    ACTION_EXECUTED = "executive.action_executed"
    GOAL_UPDATED = "executive.goal_updated"
    
    # Meta events
    ANOMALY_DETECTED = "meta.anomaly_detected"
    INSIGHT_GENERATED = "meta.insight_generated"


@dataclass
class Event:
    """
    Sistem event'i.
    """
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    cycle_id: Optional[int] = None
    priority: int = 0  # Higher = more important
    
    def __repr__(self) -> str:
        return f"Event({self.event_type.value}, source={self.source})"


# Event handler tipi
EventHandler = Callable[[Event], None]


class EventBus:
    """
    Merkezi event bus - Pub/Sub pattern.
    
    Usage:
        bus = EventBus()
        
        # Subscribe
        bus.subscribe(EventType.THREAT_DETECTED, my_handler)
        
        # Publish
        bus.publish(Event(EventType.THREAT_DETECTED, data={"level": 0.8}))
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[Event] = []
        self._max_history: int = 1000
        self._paused: bool = False
        self._event_count: int = 0
    
    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """
        Belirli bir event tipine abone ol.
        
        Args:
            event_type: Dinlenecek event tipi
            handler: Event geldiğinde çağrılacak fonksiyon
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"Handler subscribed to {event_type.value}")
    
    def subscribe_all(self, handler: EventHandler) -> None:
        """
        Tüm eventlere abone ol (monitoring için).
        """
        if handler not in self._global_handlers:
            self._global_handlers.append(handler)
            logger.debug("Global handler subscribed")
    
    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """Aboneliği iptal et."""
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
    
    def publish(self, event: Event) -> int:
        """
        Event yayınla.
        
        Args:
            event: Yayınlanacak event
            
        Returns:
            Event'i işleyen handler sayısı
        """
        if self._paused:
            logger.debug(f"Event bus paused, skipping: {event.event_type.value}")
            return 0
        
        self._event_count += 1
        handlers_called = 0
        
        # Global handlers
        for handler in self._global_handlers:
            try:
                handler(event)
                handlers_called += 1
            except Exception as e:
                logger.error(f"Global handler error: {e}")
        
        # Type-specific handlers
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                try:
                    handler(event)
                    handlers_called += 1
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type.value}: {e}")
        
        # History
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        logger.debug(f"Published {event.event_type.value}, {handlers_called} handlers called")
        return handlers_called
    
    def emit(
        self,
        event_type: EventType,
        source: str,
        cycle_id: Optional[int] = None,
        **data: Any,
    ) -> int:
        """
        Kısa yol: Event oluştur ve yayınla.
        
        Usage:
            bus.emit(EventType.THREAT_DETECTED, "perception", level=0.8)
        """
        event = Event(
            event_type=event_type,
            source=source,
            data=data,
            cycle_id=cycle_id,
        )
        return self.publish(event)
    
    def pause(self) -> None:
        """Event işlemeyi duraklat."""
        self._paused = True
    
    def resume(self) -> None:
        """Event işlemeye devam et."""
        self._paused = False
    
    def clear_history(self) -> None:
        """Event geçmişini temizle."""
        self._event_history.clear()
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Event geçmişini getir."""
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Event bus istatistikleri."""
        return {
            "total_events": self._event_count,
            "history_size": len(self._event_history),
            "subscriber_count": sum(len(h) for h in self._handlers.values()),
            "global_handlers": len(self._global_handlers),
            "paused": self._paused,
        }


# Singleton event bus instance
_default_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Default event bus instance'ını getir."""
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


def reset_event_bus() -> None:
    """Event bus'ı sıfırla (test için)."""
    global _default_bus
    _default_bus = None
