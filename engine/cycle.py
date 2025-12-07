"""
UEM v2 - Cognitive Cycle

Ana işlem döngüsü - 10 faz sırayla çalışır.

BUG FIX: Phase results artık context.metadata'ya da ekleniyor,
böylece DECIDE handler orchestrator suggestion'a erişebiliyor.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
import time
import logging

from .events import EventType, Event, EventBus, get_event_bus
from .phases import Phase, PhaseConfig, PhaseResult, DEFAULT_PHASE_CONFIGS
from foundation.state import StateVector
from foundation.types import Context, ModuleType, Stimulus

logger = logging.getLogger(__name__)


# Phase handler tipi
PhaseHandler = Callable[[Phase, StateVector, Context], PhaseResult]


@dataclass
class CycleConfig:
    """Cycle yapılandırması."""
    phase_configs: List[PhaseConfig] = field(default_factory=lambda: DEFAULT_PHASE_CONFIGS.copy())
    max_cycle_time_ms: float = 5000.0
    stop_on_error: bool = False
    emit_events: bool = True


@dataclass
class CycleState:
    """Cycle'ın anlık durumu."""
    cycle_id: int
    current_phase: Optional[Phase] = None
    state_vector: StateVector = field(default_factory=StateVector)
    phase_results: Dict[Phase, PhaseResult] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0
    
    @property
    def is_complete(self) -> bool:
        return self.end_time is not None


class CognitiveCycle:
    """
    10-Phase Cognitive Cycle.
    
    Usage:
        cycle = CognitiveCycle()
        cycle.register_handler(Phase.SENSE, my_sense_handler)
        result = cycle.run(stimulus)
    """
    
    def __init__(
        self,
        config: Optional[CycleConfig] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.config = config or CycleConfig()
        self.event_bus = event_bus or get_event_bus()
        
        self._handlers: Dict[Phase, PhaseHandler] = {}
        self._cycle_count: int = 0
        self._current_state: Optional[CycleState] = None
        
        # Default placeholder handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Tüm fazlara placeholder handler ekle."""
        for phase in Phase.ordered():
            self._handlers[phase] = self._default_handler
    
    def _default_handler(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """Default placeholder handler - sadece geçer."""
        return PhaseResult(
            phase=phase,
            success=True,
            duration_ms=0.0,
            output={"placeholder": True},
        )
    
    def register_handler(
        self,
        phase: Phase,
        handler: PhaseHandler,
    ) -> None:
        """
        Bir faza handler kaydet.
        
        Args:
            phase: Hangi faz
            handler: (phase, state, context) -> PhaseResult
        """
        self._handlers[phase] = handler
        logger.debug(f"Handler registered for {phase.value}")
    
    def run(
        self,
        stimulus: Optional[Stimulus] = None,
        initial_state: Optional[StateVector] = None,
    ) -> CycleState:
        """
        Tek bir cognitive cycle çalıştır.
        
        Args:
            stimulus: Dış uyaran (opsiyonel)
            initial_state: Başlangıç durumu
            
        Returns:
            CycleState - tüm sonuçlarla birlikte
        """
        self._cycle_count += 1
        
        # State oluştur
        cycle_state = CycleState(
            cycle_id=self._cycle_count,
            state_vector=initial_state.copy() if initial_state else StateVector(),
            start_time=datetime.now(),
        )
        self._current_state = cycle_state
        
        # Context oluştur
        context = Context(
            cycle_id=self._cycle_count,
            metadata={"stimulus": stimulus} if stimulus else {},
        )
        
        # ═══════════════════════════════════════════════════════════════
        # BUG FIX: phase_results için container oluştur
        # DECIDE handler buradan okuyacak
        # ═══════════════════════════════════════════════════════════════
        context.metadata["phase_results"] = {}
        
        # Cycle başlangıç eventi
        if self.config.emit_events:
            self.event_bus.emit(
                EventType.CYCLE_START,
                source="engine",
                cycle_id=self._cycle_count,
            )
        
        logger.info(f"Cycle {self._cycle_count} started")
        
        # Fazları sırayla çalıştır
        for phase_config in self.config.phase_configs:
            if not phase_config.enabled:
                cycle_state.phase_results[phase_config.phase] = PhaseResult(
                    phase=phase_config.phase,
                    success=True,
                    skipped=True,
                )
                continue
            
            cycle_state.current_phase = phase_config.phase
            
            # Faz eventi
            if self.config.emit_events:
                self.event_bus.emit(
                    EventType.MODULE_START,
                    source="engine",
                    cycle_id=self._cycle_count,
                    phase=phase_config.phase.value,
                )
            
            # Handler'ı çalıştır
            result = self._run_phase(
                phase_config,
                cycle_state.state_vector,
                context,
            )
            
            # ═══════════════════════════════════════════════════════════
            # BUG FIX: Result'ı HEM cycle_state'e HEM context'e yaz
            # ═══════════════════════════════════════════════════════════
            cycle_state.phase_results[phase_config.phase] = result
            context.metadata["phase_results"][phase_config.phase] = result
            
            # Faz bitiş eventi
            if self.config.emit_events:
                self.event_bus.emit(
                    EventType.MODULE_END,
                    source="engine",
                    cycle_id=self._cycle_count,
                    phase=phase_config.phase.value,
                    success=result.success,
                    duration_ms=result.duration_ms,
                )
            
            # Hata kontrolü
            if not result.success and phase_config.required and self.config.stop_on_error:
                logger.error(f"Phase {phase_config.phase.value} failed, stopping cycle")
                break
        
        # Cycle bitir
        cycle_state.end_time = datetime.now()
        cycle_state.current_phase = None
        
        # Cycle bitiş eventi
        if self.config.emit_events:
            self.event_bus.emit(
                EventType.CYCLE_END,
                source="engine",
                cycle_id=self._cycle_count,
                duration_ms=cycle_state.duration_ms,
                success=all(r.success for r in cycle_state.phase_results.values()),
            )
        
        logger.info(
            f"Cycle {self._cycle_count} completed in {cycle_state.duration_ms:.1f}ms"
        )
        
        return cycle_state
    
    def _run_phase(
        self,
        config: PhaseConfig,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """Tek bir fazı çalıştır."""
        handler = self._handlers.get(config.phase, self._default_handler)
        
        start_time = time.perf_counter()
        
        try:
            result = handler(config.phase, state, context)
            result.duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Timeout kontrolü
            if result.duration_ms > config.timeout_ms:
                logger.warning(
                    f"Phase {config.phase.value} exceeded timeout: "
                    f"{result.duration_ms:.1f}ms > {config.timeout_ms}ms"
                )
            
            return result
            
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(f"Phase {config.phase.value} error: {e}")
            
            return PhaseResult(
                phase=config.phase,
                success=False,
                duration_ms=duration,
                error=str(e),
            )
    
    @property
    def cycle_count(self) -> int:
        """Toplam çalıştırılan cycle sayısı."""
        return self._cycle_count
    
    @property
    def current_state(self) -> Optional[CycleState]:
        """Şu anki cycle state'i."""
        return self._current_state
    
    def get_stats(self) -> Dict[str, Any]:
        """Cycle istatistikleri."""
        return {
            "total_cycles": self._cycle_count,
            "registered_handlers": len([h for h in self._handlers.values() 
                                        if h != self._default_handler]),
            "event_bus_stats": self.event_bus.stats,
        }
