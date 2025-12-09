"""
core/language/pipeline/__init__.py

UEM v2 Thought-to-Speech Pipeline.

Tam pipeline bilesenleri:
- ThoughtToSpeechPipeline: Ana orkestrator
- SelfCritique: Ic degerlendirme ve revizyon
- PipelineConfig: Merkezi konfigürasyon

Kullanim:
    from core.language.pipeline import ThoughtToSpeechPipeline, PipelineConfig

    # Varsayilan konfigürasyon
    pipeline = ThoughtToSpeechPipeline()
    result = pipeline.process("Merhaba, nasilsin?")

    if result.success:
        print(result.output)

    # Ozel konfigürasyon
    config = PipelineConfig.strict()
    pipeline = ThoughtToSpeechPipeline(config=config)
"""

from .config import (
    PipelineConfig,
    SelfCritiqueConfig,
)

from .self_critique import (
    SelfCritique,
    CritiqueResult,
)

from .thought_to_speech import (
    ThoughtToSpeechPipeline,
    PipelineResult,
    generate_pipeline_result_id,
)

__all__ = [
    # Config
    "PipelineConfig",
    "SelfCritiqueConfig",

    # Self Critique
    "SelfCritique",
    "CritiqueResult",

    # Pipeline
    "ThoughtToSpeechPipeline",
    "PipelineResult",
    "generate_pipeline_result_id",
]
