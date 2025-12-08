"""
UEM v2 - Perception Phase Handlers

Cognitive Cycle'in SENSE, ATTEND ve PERCEIVE fazlari icin handler'lar.
Yeni core/perception modulu ile entegre.

Kullanim:
    from engine.handlers.perception import (
        create_sense_handler,
        create_attend_handler,
        create_perceive_handler,
    )

    cycle = CognitiveCycle()
    cycle.register_handler(Phase.SENSE, create_sense_handler())
    cycle.register_handler(Phase.ATTEND, create_attend_handler())
    cycle.register_handler(Phase.PERCEIVE, create_perceive_handler())
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from foundation.state import StateVector, SVField
from foundation.types import Context, Entity, Stimulus
from engine.phases import Phase, PhaseResult

# Yeni perception modulu
from core.perception import (
    PerceptionProcessor, ProcessorConfig,
    PerceptualInput, PerceptualFeatures, PerceptualOutput,
    SensoryModality, SensoryData,
    AttentionFocus, ThreatLevel,
    get_perception_processor,
)

logger = logging.getLogger(__name__)


# ========================================================================
# CONFIGURATION
# ========================================================================

@dataclass
class PerceptionHandlerConfig:
    """Perception handler'lari yapilandirmasi."""

    # Tehdit algilama
    detect_threat: bool = True
    threat_keywords: List[str] = field(default_factory=lambda: [
        "angry", "hostile", "aggressive", "threatening",
        "enemy", "attack", "danger"
    ])
    threat_expressions: List[str] = field(default_factory=lambda: [
        "angry", "threatening", "hostile", "aggressive"
    ])

    # Agent algilama
    detect_agents: bool = True

    # Dikkat
    attention_to_threat: float = 0.8
    attention_to_social: float = 0.6
    attention_default: float = 0.3

    # Processor kullanimi
    use_perception_processor: bool = True


# ========================================================================
# SENSE PHASE HANDLER
# ========================================================================

class SensePhaseHandler:
    """
    SENSE fazi handler'i.

    Ham stimulus'u alir, PerceptualInput'a cevirir.
    Temel duyusal islemleri yapar.
    """

    def __init__(
        self,
        config: Optional[PerceptionHandlerConfig] = None,
        processor: Optional[PerceptionProcessor] = None,
    ):
        self.config = config or PerceptionHandlerConfig()
        self.processor = processor or get_perception_processor()

    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """SENSE fazini calistir."""
        output: Dict[str, Any] = {
            "sensed": False,
            "stimulus_type": None,
            "intensity": 0.0,
            "perceptual_input": None,
        }

        stimulus = context.metadata.get("stimulus")

        if stimulus:
            # Stimulus'u PerceptualInput'a cevir
            perceptual_input = self.processor.sense(stimulus)

            output["sensed"] = True
            output["perceptual_input"] = perceptual_input

            if isinstance(stimulus, Stimulus):
                output["stimulus_type"] = stimulus.stimulus_type
                output["intensity"] = stimulus.intensity

                # Arousal'i stimulus intensity'ye gore ayarla
                state.set(SVField.AROUSAL, stimulus.intensity)
            elif isinstance(stimulus, dict):
                output["stimulus_type"] = stimulus.get("stimulus_type", "unknown")
                output["intensity"] = stimulus.get("intensity", 0.5)
                state.set(SVField.AROUSAL, output["intensity"])

            # Context'e ekle (ATTEND ve PERCEIVE icin)
            context.metadata["perceptual_input"] = perceptual_input
            context.metadata["stimulus_content"] = getattr(stimulus, "content", stimulus)
            context.metadata["stimulus_source"] = getattr(stimulus, "source_entity", None)

            logger.debug(
                f"Sensed stimulus: type={output['stimulus_type']}, "
                f"intensity={output['intensity']}"
            )

        return PhaseResult(
            phase=phase,
            success=True,
            output=output,
        )


# ========================================================================
# ATTEND PHASE HANDLER
# ========================================================================

class AttendPhaseHandler:
    """
    ATTEND fazi handler'i.

    Dikkat yonlendirme ve filtreleme yapar.
    """

    def __init__(
        self,
        config: Optional[PerceptionHandlerConfig] = None,
        processor: Optional[PerceptionProcessor] = None,
    ):
        self.config = config or PerceptionHandlerConfig()
        self.processor = processor or get_perception_processor()

    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """ATTEND fazini calistir."""
        output: Dict[str, Any] = {
            "attended": False,
            "attention_level": 0.0,
            "attention_target": None,
            "attention_reason": "none",
        }

        perceptual_input = context.metadata.get("perceptual_input")

        if perceptual_input:
            # Mevcut dikkat durumu
            current_attention = context.metadata.get("current_attention")

            # Attend uygula
            filtered_input, attention = self.processor.attend(
                perceptual_input,
                current_attention=current_attention,
                context={"cycle_id": context.cycle_id},
            )

            output["attended"] = True
            output["attention_level"] = attention.attention_level
            output["attention_target"] = attention.target_id
            output["attention_reason"] = attention.reason

            # Context'e ekle
            context.metadata["perceptual_input"] = filtered_input
            context.metadata["attention"] = attention
            context.metadata["current_attention"] = attention

            # StateVector'a yaz
            state.set(SVField.ATTENTION_FOCUS, attention.attention_level)

            logger.debug(
                f"Attended: level={attention.attention_level:.2f}, "
                f"target={attention.target_type}, reason={attention.reason}"
            )

        return PhaseResult(
            phase=phase,
            success=True,
            output=output,
        )


# ========================================================================
# PERCEIVE PHASE HANDLER
# ========================================================================

class PerceivePhaseHandler:
    """
    PERCEIVE fazi handler'i.

    Tam ozellik cikarma ve anlam olusturma.
    - Agent algilama
    - Threat detection
    - Feature extraction
    """

    def __init__(
        self,
        config: Optional[PerceptionHandlerConfig] = None,
        processor: Optional[PerceptionProcessor] = None,
    ):
        self.config = config or PerceptionHandlerConfig()
        self.processor = processor or get_perception_processor()

    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """PERCEIVE fazini calistir."""
        output: Dict[str, Any] = {
            "perceived": False,
            "agents_detected": [],
            "threat_level": 0.0,
            "attention_focus": None,
            "features": None,
        }

        perceptual_input = context.metadata.get("perceptual_input")
        attention = context.metadata.get("attention")

        if perceptual_input:
            # Tam perception isle
            features = self.processor.perceive(
                perceptual_input,
                attention=attention,
                context={"cycle_id": context.cycle_id},
            )

            output["perceived"] = True
            output["features"] = features

            # Agent bilgileri
            if features.agents:
                output["agents_detected"] = [
                    {
                        "id": a.agent_id,
                        "expression": a.expression.value if a.expression else "neutral",
                        "body_language": a.body_language.value if a.body_language else "neutral",
                        "disposition": a.disposition.value if a.disposition else "unknown",
                        "distance": a.distance,
                        "threat_level": a.threat_level.value if a.threat_level else "none",
                        "trust_level": a.trust_level,
                    }
                    for a in features.agents
                ]
                context.metadata["detected_agents"] = output["agents_detected"]
                context.metadata["perceived_agents"] = features.agents

            # Threat bilgisi
            output["threat_level"] = features.threat.overall_score
            context.metadata["threat_assessment"] = features.threat

            # StateVector'a yaz
            state.threat = max(state.threat, features.threat.overall_score)

            if features.threat.overall_score > 0.5:
                logger.debug(
                    f"Threat detected: level={features.threat.overall_level.value}, "
                    f"score={features.threat.overall_score:.2f}"
                )

            # Attention bilgisi
            output["attention_focus"] = features.attention.attention_level
            state.set(SVField.ATTENTION_FOCUS, features.attention.attention_level)

            # Features'i context'e ekle (diger fazlar icin)
            context.metadata["perceptual_features"] = features

            logger.debug(
                f"Perceived: agents={len(features.agents)}, "
                f"threat={features.threat.overall_level.value}"
            )

        return PhaseResult(
            phase=phase,
            success=True,
            output=output,
        )


# ========================================================================
# LEGACY UYUMLULUK (Eski API destegi)
# ========================================================================

class LegacyPerceivePhaseHandler:
    """
    Eski PERCEIVE handler (geri uyumluluk icin).

    Yeni perception modulu kullanmadan basit perception yapar.
    """

    def __init__(self, config: Optional[PerceptionHandlerConfig] = None):
        self.config = config or PerceptionHandlerConfig()

    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """PERCEIVE fazini calistir (legacy)."""
        output: Dict[str, Any] = {
            "perceived": False,
            "agents_detected": [],
            "threat_level": 0.0,
            "attention_focus": None,
        }

        stimulus = context.metadata.get("stimulus")
        source_entity = context.metadata.get("stimulus_source")

        # 1. Agent algilama
        if self.config.detect_agents and source_entity:
            agent_info = self._extract_agent_info(source_entity, stimulus)
            if agent_info:
                output["agents_detected"].append(agent_info)
                context.metadata["detected_agents"] = output["agents_detected"]
                output["perceived"] = True

        # 2. Threat detection
        if self.config.detect_threat:
            threat_level = self._detect_threat(
                stimulus, source_entity, output["agents_detected"]
            )
            output["threat_level"] = threat_level
            state.threat = max(state.threat, threat_level)

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
        """Entity'den agent bilgisi cikar."""
        if entity.entity_type != "agent":
            return None

        info = {
            "id": entity.id,
            "expression": entity.get("expression", "neutral"),
            "body_language": entity.get("body_language", "neutral"),
            "relationship": entity.get("relationship", "stranger"),
            "valence": entity.get("valence", 0.0),
            "arousal": entity.get("arousal", 0.5),
            "dominance": entity.get("dominance", 0.5),
        }

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

        if entity:
            if entity.get("hostile", False):
                threat = max(threat, 0.8)
            if entity.get("threatening", False):
                threat = max(threat, 0.7)

        for agent in agents:
            expr = agent.get("expression", "").lower()
            if expr in self.config.threat_expressions:
                threat = max(threat, 0.6)

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
        if threat_level > 0.5:
            return self.config.attention_to_threat

        if has_agent:
            return self.config.attention_to_social

        if stimulus:
            return 0.4 + (stimulus.intensity * 0.3)

        return self.config.attention_default


# ========================================================================
# FACTORY FONKSIYONLAR
# ========================================================================

def create_sense_handler(
    config: Optional[PerceptionHandlerConfig] = None,
    processor: Optional[PerceptionProcessor] = None,
) -> SensePhaseHandler:
    """SENSE fazi handler'i olustur."""
    return SensePhaseHandler(config, processor)


def create_attend_handler(
    config: Optional[PerceptionHandlerConfig] = None,
    processor: Optional[PerceptionProcessor] = None,
) -> AttendPhaseHandler:
    """ATTEND fazi handler'i olustur."""
    return AttendPhaseHandler(config, processor)


def create_perceive_handler(
    config: Optional[PerceptionHandlerConfig] = None,
    processor: Optional[PerceptionProcessor] = None,
) -> PerceivePhaseHandler:
    """PERCEIVE fazi handler'i olustur."""
    return PerceivePhaseHandler(config, processor)


def create_legacy_perceive_handler(
    config: Optional[PerceptionHandlerConfig] = None,
) -> LegacyPerceivePhaseHandler:
    """Legacy PERCEIVE handler olustur (geri uyumluluk)."""
    return LegacyPerceivePhaseHandler(config)


# Eski API uyumlulugu icin alias
PerceptionConfig = PerceptionHandlerConfig
