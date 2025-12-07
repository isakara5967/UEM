"""
UEM v2 - Affect Phase Handlers

Cognitive Cycle'ın FEEL fazı için handler'lar.
SocialAffectOrchestrator'ı StateVector ile entegre eder.

Kullanım:
    from engine.handlers.affect import create_feel_handler, AffectPhaseConfig
    
    cycle = CognitiveCycle()
    cycle.register_handler(Phase.FEEL, create_feel_handler())
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
import logging

import sys
sys.path.insert(0, '.')

from foundation.state import StateVector, SVField, StateVectorBridge, get_state_bridge
from foundation.types import Context, Entity, Stimulus
from engine.phases import Phase, PhaseResult

# Lazy imports to avoid circular dependencies
if TYPE_CHECKING:
    from core.affect.emotion.core import PADState
    from core.affect.social import SocialAffectOrchestrator, AgentState
    from core.affect.social.orchestrator import SocialAffectResult

logger = logging.getLogger(__name__)


@dataclass
class AffectPhaseConfig:
    """FEEL fazı yapılandırması."""
    
    # Orchestrator
    use_orchestrator: bool = True
    
    # StateVector entegrasyonu
    write_to_state_vector: bool = True
    read_from_state_vector: bool = True
    
    # Agent algılama
    auto_create_agent: bool = True  # Context'ten agent oluştur
    default_relationship: str = "stranger"
    
    # PAD güncelleme
    update_self_pad: bool = True
    pad_update_strength: float = 0.3
    
    # Fallback (orchestrator yoksa)
    fallback_valence_from_threat: bool = True


@dataclass
class AffectPhaseState:
    """FEEL fazı için tutulan state."""
    
    # Orchestrator instance (cycle boyunca tutulur)
    orchestrator: Optional["SocialAffectOrchestrator"] = None
    
    # Son işlenen agent
    last_agent_id: Optional[str] = None
    last_result: Optional["SocialAffectResult"] = None
    
    # İstatistikler
    process_count: int = 0
    total_time_ms: float = 0.0


class AffectPhaseHandler:
    """
    FEEL fazı handler'ı.
    
    SocialAffectOrchestrator'ı kullanarak:
    1. Context'ten agent bilgisi çıkarır
    2. Empathy/Sympathy/Trust hesaplar
    3. StateVector'ı günceller
    """
    
    def __init__(
        self,
        config: Optional[AffectPhaseConfig] = None,
        bridge: Optional[StateVectorBridge] = None,
    ):
        self.config = config or AffectPhaseConfig()
        self.bridge = bridge or get_state_bridge()
        self._state = AffectPhaseState()
        self._orchestrator_initialized = False
    
    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """
        FEEL fazını çalıştır.
        
        Args:
            phase: Phase.FEEL
            state: Mevcut StateVector
            context: Cycle context'i
            
        Returns:
            PhaseResult
        """
        import time
        start_time = time.perf_counter()
        
        output: Dict[str, Any] = {}
        
        try:
            # 1. Orchestrator'ı başlat/güncelle
            if self.config.use_orchestrator:
                self._ensure_orchestrator(state)
            
            # 2. Agent bilgisi al
            agent = self._extract_agent(context, state)
            
            if agent and self.config.use_orchestrator and self._state.orchestrator:
                # 3. Social affect işle
                result = self._process_social_affect(agent, state, context)
                output["social_affect"] = result.to_dict() if result else None
                output["suggested_action"] = result.suggested_action if result else None
                output["empathy"] = result.empathy.total_empathy if result and result.empathy else 0.0
                output["trust"] = result.trust_after if result else 0.5
                
                self._state.last_result = result
                self._state.last_agent_id = agent.agent_id
                
            else:
                # 4. Fallback: basit duygu hesaplama
                self._fallback_affect(state, context)
                output["fallback"] = True
            
            # 5. Emotional intensity hesapla
            self._update_emotional_intensity(state)
            
            output["valence"] = state.get(SVField.VALENCE)
            output["arousal"] = state.get(SVField.AROUSAL)
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._state.process_count += 1
            self._state.total_time_ms += duration_ms
            
            return PhaseResult(
                phase=phase,
                success=True,
                duration_ms=duration_ms,
                output=output,
            )
            
        except Exception as e:
            logger.error(f"FEEL phase error: {e}")
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            return PhaseResult(
                phase=phase,
                success=False,
                duration_ms=duration_ms,
                error=str(e),
            )
    
    def _ensure_orchestrator(self, state: StateVector) -> None:
        """Orchestrator'ı başlat veya güncelle."""
        from core.affect.social import SocialAffectOrchestrator
        
        if self._state.orchestrator is None:
            # İlk kez oluştur
            self._state.orchestrator = SocialAffectOrchestrator.from_state_vector(
                state, bridge=self.bridge
            )
            self._orchestrator_initialized = True
            logger.debug("Orchestrator initialized from StateVector")
        else:
            # Mevcut orchestrator'ı StateVector'a bağla
            self._state.orchestrator.bind_state_vector(state)
    
    def _extract_agent(
        self,
        context: Context,
        state: StateVector,
    ) -> Optional["AgentState"]:
        """Context'ten agent bilgisi çıkar."""
        from core.affect.social.empathy import AgentState
        from core.affect.emotion.core import PADState
        
        # Context metadata'dan agent bilgisi
        metadata = context.metadata
        
        # Doğrudan AgentState varsa kullan
        if "agent" in metadata:
            return metadata["agent"]
        
        # Entity varsa AgentState'e dönüştür
        if "entity" in metadata:
            entity = metadata["entity"]
            if isinstance(entity, Entity) and entity.entity_type == "agent":
                return AgentState(
                    agent_id=entity.id,
                    observed_pad=PADState(
                        pleasure=entity.get("valence", 0.0),
                        arousal=entity.get("arousal", 0.5),
                        dominance=entity.get("dominance", 0.5),
                    ),
                    facial_expression=entity.get("expression", "neutral"),
                    body_language=entity.get("body_language", "neutral"),
                    situation=entity.get("situation", "unknown"),
                    relationship_to_self=entity.get("relationship", self.config.default_relationship),
                )
        
        # Stimulus'tan agent bilgisi
        if "stimulus" in metadata:
            stimulus = metadata["stimulus"]
            if isinstance(stimulus, Stimulus) and stimulus.source_entity:
                entity = stimulus.source_entity
                if entity.entity_type == "agent":
                    return AgentState(
                        agent_id=entity.id,
                        observed_pad=PADState(
                            pleasure=entity.get("valence", 0.0),
                            arousal=entity.get("arousal", 0.5),
                            dominance=entity.get("dominance", 0.5),
                        ),
                        facial_expression=entity.get("expression", "neutral"),
                        situation=stimulus.content.get("situation", "unknown"),
                        relationship_to_self=entity.get("relationship", self.config.default_relationship),
                    )
        
        # Auto-create agent (varsa)
        if self.config.auto_create_agent and "detected_agents" in metadata:
            agents = metadata["detected_agents"]
            if agents:
                # İlk agent'ı al
                agent_data = agents[0]
                return AgentState(
                    agent_id=agent_data.get("id", "unknown"),
                    facial_expression=agent_data.get("expression", "neutral"),
                    situation=agent_data.get("situation", "unknown"),
                    relationship_to_self=agent_data.get("relationship", self.config.default_relationship),
                )
        
        return None
    
    def _process_social_affect(
        self,
        agent: "AgentState",
        state: StateVector,
        context: Context,
    ) -> Optional["SocialAffectResult"]:
        """Social affect işle."""
        if not self._state.orchestrator:
            return None
        
        # Relationship context (varsa)
        relationship = context.metadata.get("relationship")
        
        # İşle
        result = self._state.orchestrator.process(
            agent,
            relationship=relationship,
            empathy_context=context.metadata.get("empathy_context", "default"),
        )
        
        return result
    
    def _fallback_affect(
        self,
        state: StateVector,
        context: Context,
    ) -> None:
        """Fallback: basit duygu hesaplama (orchestrator yoksa)."""
        if not self.config.fallback_valence_from_threat:
            return
        
        # Threat'ten valence hesapla
        threat = state.threat
        current_valence = state.get(SVField.VALENCE, 0.5)
        
        # Threat yüksekse valence düşük
        threat_effect = -threat * 0.5
        new_valence = max(0.0, min(1.0, current_valence + threat_effect))
        
        state.set(SVField.VALENCE, new_valence)
        
        # Arousal threat'e göre artır
        current_arousal = state.get(SVField.AROUSAL, 0.5)
        arousal_boost = threat * 0.3
        new_arousal = max(0.0, min(1.0, current_arousal + arousal_boost))
        
        state.set(SVField.AROUSAL, new_arousal)
    
    def _update_emotional_intensity(self, state: StateVector) -> None:
        """Duygusal yoğunluğu hesapla."""
        valence = state.get(SVField.VALENCE, 0.5)
        arousal = state.get(SVField.AROUSAL, 0.5)
        
        # Intensity: valence'ın 0.5'ten uzaklığı + arousal
        valence_deviation = abs(valence - 0.5) * 2  # 0-1
        intensity = (valence_deviation + arousal) / 2
        
        state.set(SVField.EMOTIONAL_INTENSITY, intensity)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Handler istatistikleri."""
        return {
            "process_count": self._state.process_count,
            "total_time_ms": self._state.total_time_ms,
            "avg_time_ms": self._state.total_time_ms / max(1, self._state.process_count),
            "orchestrator_initialized": self._orchestrator_initialized,
            "last_agent_id": self._state.last_agent_id,
        }
    
    def get_last_result(self) -> Optional["SocialAffectResult"]:
        """Son işlenen social affect sonucu."""
        return self._state.last_result


def create_feel_handler(
    config: Optional[AffectPhaseConfig] = None,
) -> AffectPhaseHandler:
    """FEEL fazı handler'ı oluştur."""
    return AffectPhaseHandler(config)


# ═══════════════════════════════════════════════════════════════════════════
# SIMPLE HANDLERS (Fallback / Test için)
# ═══════════════════════════════════════════════════════════════════════════

def simple_feel_handler(
    phase: Phase,
    state: StateVector,
    context: Context,
) -> PhaseResult:
    """
    Basit FEEL handler - threat'ten valence hesaplar.
    Test ve fallback için kullanılabilir.
    """
    threat = state.threat
    
    # Threat → negative valence
    valence = 0.5 - (threat * 0.5)
    state.set(SVField.VALENCE, valence)
    
    # Threat → high arousal
    arousal = 0.3 + (threat * 0.5)
    state.set(SVField.AROUSAL, arousal)
    
    return PhaseResult(
        phase=phase,
        success=True,
        output={"valence": valence, "arousal": arousal, "simple": True},
    )
