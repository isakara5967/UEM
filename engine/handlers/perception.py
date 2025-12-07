"""
UEM v2 - Perception Phase Handlers

Cognitive Cycle'ın SENSE ve PERCEIVE fazları için handler'lar.
Stimulus'tan agent/entity algılar, StateVector'a yazar.

Kullanım:
    from engine.handlers.perception import create_sense_handler, create_perceive_handler
    
    cycle = CognitiveCycle()
    cycle.register_handler(Phase.SENSE, create_sense_handler())
    cycle.register_handler(Phase.PERCEIVE, create_perceive_handler())
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

import sys
sys.path.insert(0, '.')

from foundation.state import StateVector, SVField
from foundation.types import Context, Entity, Stimulus
from engine.phases import Phase, PhaseResult

logger = logging.getLogger(__name__)


@dataclass
class PerceptionConfig:
    """Perception fazları yapılandırması."""
    
    # Threat detection
    detect_threat: bool = True
    threat_keywords: List[str] = field(default_factory=lambda: [
        "angry", "hostile", "aggressive", "threatening", "enemy", "attack"
    ])
    threat_expressions: List[str] = field(default_factory=lambda: [
        "angry", "threatening", "hostile", "aggressive"
    ])
    
    # Agent detection
    detect_agents: bool = True
    
    # Attention
    attention_to_threat: float = 0.8  # Threat varsa dikkat
    attention_to_social: float = 0.6  # Sosyal stimulus'a dikkat
    attention_default: float = 0.3


class SensePhaseHandler:
    """
    SENSE fazı handler'ı.
    
    Ham stimulus'u alır, temel özellikleri çıkarır.
    """
    
    def __init__(self, config: Optional[PerceptionConfig] = None):
        self.config = config or PerceptionConfig()
    
    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """SENSE fazını çalıştır."""
        output: Dict[str, Any] = {
            "sensed": False,
            "stimulus_type": None,
            "intensity": 0.0,
        }
        
        stimulus = context.metadata.get("stimulus")
        
        if stimulus and isinstance(stimulus, Stimulus):
            output["sensed"] = True
            output["stimulus_type"] = stimulus.stimulus_type
            output["intensity"] = stimulus.intensity
            
            # Arousal'ı stimulus intensity'ye göre ayarla
            state.set(SVField.AROUSAL, stimulus.intensity)
            
            # Stimulus content'i context'e ekle (PERCEIVE için)
            context.metadata["stimulus_content"] = stimulus.content
            context.metadata["stimulus_source"] = stimulus.source_entity
            
            logger.debug(f"Sensed stimulus: {stimulus.stimulus_type}, intensity={stimulus.intensity}")
        
        return PhaseResult(
            phase=phase,
            success=True,
            output=output,
        )


class PerceivePhaseHandler:
    """
    PERCEIVE fazı handler'ı.
    
    Stimulus'tan anlam çıkarır:
    - Agent algılama
    - Threat detection
    - Entity özellikleri
    """
    
    def __init__(self, config: Optional[PerceptionConfig] = None):
        self.config = config or PerceptionConfig()
    
    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """PERCEIVE fazını çalıştır."""
        output: Dict[str, Any] = {
            "perceived": False,
            "agents_detected": [],
            "threat_level": 0.0,
            "attention_focus": None,
        }
        
        stimulus = context.metadata.get("stimulus")
        source_entity = context.metadata.get("stimulus_source")
        
        # 1. Agent algılama
        if self.config.detect_agents and source_entity:
            agent_info = self._extract_agent_info(source_entity, stimulus)
            if agent_info:
                output["agents_detected"].append(agent_info)
                context.metadata["detected_agents"] = output["agents_detected"]
                output["perceived"] = True
                
                logger.debug(f"Detected agent: {agent_info['id']}")
        
        # 2. Threat detection
        if self.config.detect_threat:
            threat_level = self._detect_threat(stimulus, source_entity, output["agents_detected"])
            output["threat_level"] = threat_level
            
            # StateVector'a yaz
            state.threat = max(state.threat, threat_level)  # En yüksek threat
            
            if threat_level > 0.5:
                logger.debug(f"Threat detected: {threat_level}")
        
        # 3. Attention focus
        attention = self._calculate_attention(
            output["threat_level"],
            len(output["agents_detected"]) > 0,
            stimulus,
        )
        output["attention_focus"] = attention
        state.set(SVField.ATTENTION_FOCUS, attention)
        
        return PhaseResult(
            phase=phase,
            success=True,
            output=output,
        )
    
    def _extract_agent_info(
        self,
        entity: Entity,
        stimulus: Optional[Stimulus],
    ) -> Optional[Dict[str, Any]]:
        """Entity'den agent bilgisi çıkar."""
        if entity.entity_type != "agent":
            return None
        
        # Temel bilgiler
        info = {
            "id": entity.id,
            "expression": entity.get("expression", "neutral"),
            "body_language": entity.get("body_language", "neutral"),
            "relationship": entity.get("relationship", "stranger"),
            "valence": entity.get("valence", 0.0),
            "arousal": entity.get("arousal", 0.5),
            "dominance": entity.get("dominance", 0.5),
        }
        
        # Stimulus'tan ek bilgi
        if stimulus:
            info["situation"] = stimulus.content.get("situation", "unknown")
            info["verbal"] = stimulus.content.get("verbal", None)
        
        return info
    
    def _detect_threat(
        self,
        stimulus: Optional[Stimulus],
        entity: Optional[Entity],
        agents: List[Dict],
    ) -> float:
        """Threat seviyesi hesapla."""
        threat = 0.0
        
        # Entity attributes'tan
        if entity:
            if entity.get("hostile", False):
                threat = max(threat, 0.8)
            if entity.get("threatening", False):
                threat = max(threat, 0.7)
        
        # Agent expressions'dan
        for agent in agents:
            expr = agent.get("expression", "").lower()
            if expr in self.config.threat_expressions:
                threat = max(threat, 0.6)
        
        # Stimulus content'ten
        if stimulus and stimulus.content:
            content_str = str(stimulus.content).lower()
            for keyword in self.config.threat_keywords:
                if keyword in content_str:
                    threat = max(threat, 0.5)
                    break
        
        return threat
    
    def _calculate_attention(
        self,
        threat_level: float,
        has_agent: bool,
        stimulus: Optional[Stimulus],
    ) -> float:
        """Dikkat seviyesi hesapla."""
        # Threat en yüksek öncelik
        if threat_level > 0.5:
            return self.config.attention_to_threat
        
        # Sosyal stimulus
        if has_agent:
            return self.config.attention_to_social
        
        # Stimulus varsa orta dikkat
        if stimulus:
            return 0.4 + (stimulus.intensity * 0.3)
        
        return self.config.attention_default


def create_sense_handler(
    config: Optional[PerceptionConfig] = None,
) -> SensePhaseHandler:
    """SENSE fazı handler'ı oluştur."""
    return SensePhaseHandler(config)


def create_perceive_handler(
    config: Optional[PerceptionConfig] = None,
) -> PerceivePhaseHandler:
    """PERCEIVE fazı handler'ı oluştur."""
    return PerceivePhaseHandler(config)
