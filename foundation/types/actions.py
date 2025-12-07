"""
UEM v2 - Action Types

Sistemin gerçekleştirebileceği eylem tanımları.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ActionCategory(str, Enum):
    """Eylem kategorileri."""
    MOTOR = "motor"           # Fiziksel hareket
    VERBAL = "verbal"         # Konuşma/iletişim
    COGNITIVE = "cognitive"   # Düşünme/analiz
    SOCIAL = "social"         # Sosyal etkileşim
    INTERNAL = "internal"     # İç durum değişikliği
    WAIT = "wait"             # Bekleme/gözlem


class ActionStatus(str, Enum):
    """Eylem durumu."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Action:
    """
    Gerçekleştirilecek eylem.
    """
    action_id: str
    category: ActionCategory
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: float = 0.5  # 0-1
    expected_duration_ms: float = 100.0
    preconditions: List[str] = field(default_factory=list)
    
    target_entity_id: Optional[str] = None
    status: ActionStatus = ActionStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "category": self.category.value,
            "name": self.name,
            "parameters": self.parameters,
            "priority": self.priority,
            "target_entity_id": self.target_entity_id,
            "status": self.status.value,
        }


@dataclass
class ActionOutcome:
    """
    Gerçekleştirilen eylemin sonucu.
    """
    action: Action
    success: bool
    actual_duration_ms: float = 0.0
    effects: Dict[str, Any] = field(default_factory=dict)
    feedback: Optional[str] = None
    error: Optional[str] = None


# Sık kullanılan aksiyonlar için factory fonksiyonlar
def create_wait_action(duration_ms: float = 1000) -> Action:
    """Bekleme aksiyonu oluştur."""
    return Action(
        action_id="wait",
        category=ActionCategory.WAIT,
        name="wait",
        parameters={"duration_ms": duration_ms},
        expected_duration_ms=duration_ms,
    )


def create_observe_action(target_id: str) -> Action:
    """Gözlem aksiyonu oluştur."""
    return Action(
        action_id=f"observe_{target_id}",
        category=ActionCategory.COGNITIVE,
        name="observe",
        target_entity_id=target_id,
        expected_duration_ms=50.0,
    )
