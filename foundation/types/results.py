"""
UEM v2 - Result Types

Modüllerden dönen sonuç veri yapıları.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from .base import ModuleType


class ResultStatus(str, Enum):
    """İşlem sonucu durumu."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ModuleResult:
    """
    Herhangi bir modülün işlem sonucu.
    
    Tüm modüller bu base class'tan türetilmiş result döner.
    """
    status: ResultStatus
    source: ModuleType
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # 0-1
    processing_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    @property
    def is_success(self) -> bool:
        return self.status == ResultStatus.SUCCESS
    
    @property
    def is_failed(self) -> bool:
        return self.status == ResultStatus.FAILED


@dataclass
class PerceptionResult(ModuleResult):
    """Perception modülü sonucu."""
    detected_entities: List[Any] = field(default_factory=list)
    attention_focus: Optional[str] = None
    salience_map: Dict[str, float] = field(default_factory=dict)


@dataclass
class CognitionResult(ModuleResult):
    """Cognition modülü sonucu."""
    conclusions: List[str] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    reasoning_chain: List[str] = field(default_factory=list)


@dataclass
class MemoryResult(ModuleResult):
    """Memory modülü sonucu."""
    retrieved_items: List[Any] = field(default_factory=list)
    relevance_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class AffectResult(ModuleResult):
    """Affect modülü sonucu."""
    primary_emotion: Optional[str] = None
    emotion_intensities: Dict[str, float] = field(default_factory=dict)
    valence: float = 0.0  # -1 to 1
    arousal: float = 0.5  # 0-1


@dataclass
class ExecutiveResult(ModuleResult):
    """Executive modülü sonucu."""
    selected_action: Optional[str] = None
    action_parameters: Dict[str, Any] = field(default_factory=dict)
    alternative_actions: List[str] = field(default_factory=list)
    goal_progress: Dict[str, float] = field(default_factory=dict)


@dataclass
class CycleResult:
    """
    Tek bir cognitive cycle'ın sonucu.
    """
    cycle_id: int
    module_results: Dict[ModuleType, ModuleResult] = field(default_factory=dict)
    total_time_ms: float = 0.0
    final_action: Optional[str] = None
    state_changes: Dict[str, float] = field(default_factory=dict)
    
    def get_result(self, module: ModuleType) -> Optional[ModuleResult]:
        return self.module_results.get(module)
