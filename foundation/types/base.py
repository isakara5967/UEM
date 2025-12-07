"""
UEM v2 - Base Types

Tüm modüllerin kullandığı temel veri yapıları.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from enum import Enum
from datetime import datetime


class Priority(str, Enum):
    """İşlem önceliği."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class ModuleType(str, Enum):
    """Modül tipleri."""
    PERCEPTION = "perception"
    COGNITION = "cognition"
    MEMORY = "memory"
    AFFECT = "affect"
    SELF = "self"
    EXECUTIVE = "executive"
    CONSCIOUSNESS = "consciousness"
    METAMIND = "metamind"
    MONITORING = "monitoring"


@dataclass
class Context:
    """
    İşlem context'i - her modüle iletilen bağlam bilgisi.
    """
    cycle_id: int
    timestamp: datetime = field(default_factory=datetime.now)
    source_module: Optional[ModuleType] = None
    priority: Priority = Priority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def with_source(self, source: ModuleType) -> "Context":
        """Yeni source ile kopyala."""
        return Context(
            cycle_id=self.cycle_id,
            timestamp=self.timestamp,
            source_module=source,
            priority=self.priority,
            metadata=self.metadata.copy(),
        )


@dataclass
class Entity:
    """
    Algılanan varlık (agent, object, location).
    """
    id: str
    entity_type: str  # "agent", "object", "location"
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.attributes.get(key, default)


@dataclass
class Stimulus:
    """
    Dış dünyadan gelen uyaran.
    """
    stimulus_type: str  # "visual", "auditory", "social", "internal"
    content: Dict[str, Any] = field(default_factory=dict)
    intensity: float = 0.5  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)
    source_entity: Optional[Entity] = None
