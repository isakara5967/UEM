"""
core/perception/__init__.py

UEM v2 - Perception Modulu

Algi sistemi - dis dunyadan gelen verileri isler.

Fazlar:
- SENSE: Ham duyusal girdi alma
- ATTEND: Dikkat yonlendirme ve filtreleme
- PERCEIVE: Ozellik cikarma ve anlam olusturma

Alt moduller:
- sensory/: Ham girdi isleme
- attention/: Dikkat yonlendirme
- fusion/: Multimodal birlestirme
- world_model/: Dunya durumu tahmini

Kullanim:
    from core.perception import (
        PerceptionProcessor, get_perception_processor,
        PerceptualInput, PerceptualOutput, PerceptualFeatures,
        PerceivedAgent, ThreatAssessment, ThreatLevel,
    )

    # Processor kullanimi
    processor = get_perception_processor()
    output = processor.process(perceptual_input)

    # Veya faz faz
    input_data = processor.sense(raw_stimulus)
    input_data, attention = processor.attend(input_data)
    features = processor.perceive(input_data, attention)
"""

# Types
from .types import (
    # Enums
    SensoryModality,
    PerceptualCategory,
    ThreatLevel,
    AgentDisposition,
    EmotionalExpression,
    BodyLanguage,

    # Sensory data types
    VisualFeatures,
    AuditoryFeatures,
    MotionFeatures,
    SensoryData,

    # Main types
    PerceptualInput,
    PerceivedAgent,
    ThreatAssessment,
    AttentionFocus,
    PerceptualFeatures,
    PerceptualOutput,
)

# Extractor
from .extractor import (
    FeatureExtractor,
    ExtractorConfig,
    VisualFeatureExtractor,
    AuditoryFeatureExtractor,
    MotionFeatureExtractor,
    AgentExtractor,
    ThreatExtractor,
)

# Filters
from .filters import (
    AttentionFilter,
    NoiseFilter,
    SalienceFilter,
    FilterConfig,
    PerceptionFilterPipeline,
)

# Processor
from .processor import (
    PerceptionProcessor,
    ProcessorConfig,
    get_perception_processor,
    reset_perception_processor,
)

__all__ = [
    # Enums
    "SensoryModality",
    "PerceptualCategory",
    "ThreatLevel",
    "AgentDisposition",
    "EmotionalExpression",
    "BodyLanguage",

    # Sensory types
    "VisualFeatures",
    "AuditoryFeatures",
    "MotionFeatures",
    "SensoryData",

    # Main types
    "PerceptualInput",
    "PerceivedAgent",
    "ThreatAssessment",
    "AttentionFocus",
    "PerceptualFeatures",
    "PerceptualOutput",

    # Extractor
    "FeatureExtractor",
    "ExtractorConfig",
    "VisualFeatureExtractor",
    "AuditoryFeatureExtractor",
    "MotionFeatureExtractor",
    "AgentExtractor",
    "ThreatExtractor",

    # Filters
    "AttentionFilter",
    "NoiseFilter",
    "SalienceFilter",
    "FilterConfig",
    "PerceptionFilterPipeline",

    # Processor
    "PerceptionProcessor",
    "ProcessorConfig",
    "get_perception_processor",
    "reset_perception_processor",
]
