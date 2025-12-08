"""
UEM v2 - MetaMind Module

Meta-bilissel analiz modulu.
Sistem performansini analiz eder, kalipler tespit eder,
ogrenme hedefleri belirler ve adaptasyon stratejileri onerir.

Alt Moduller:
    - analyzers: Cycle performans analizi ("Bu cycle nasil gitti?")
    - insights: Ogrenilen dersler ("Ne ogrendim?")
    - patterns: Kalip tespiti ("Tekrarlayan kalipler var mi?")
    - learning: Ogrenme yonetimi ("Nasil gelistebilirim?")

Kullanim:
    from meta.metamind import MetaMindProcessor, create_metamind_processor

    processor = create_metamind_processor()

    # Her cycle sonunda isle
    output = processor.process(
        cycle_id=1,
        duration_ms=150.0,
        phase_durations={"sense": 30, "think": 80, "act": 40},
        success=True,
    )

    # Insight'lari kontrol et
    for insight in output.new_insights:
        print(f"Insight: {insight.title}")

    # Adaptasyon onerisi
    if output.suggested_adaptation:
        print(f"Adaptation: {output.suggested_adaptation.name}")
"""

# Types
from .types import (
    # Enums
    InsightType,
    PatternType,
    LearningGoalType,
    MetaStateType,
    AnalysisScope,
    SeverityLevel,
    # Dataclasses
    CycleAnalysisResult,
    Insight,
    Pattern,
    LearningGoal,
    MetaState,
)

# Analyzers
from .analyzers import (
    AnalyzerConfig,
    CycleAnalyzer,
    create_cycle_analyzer,
    get_cycle_analyzer,
)

# Insights
from .insights import (
    InsightGeneratorConfig,
    InsightGenerator,
    create_insight_generator,
    get_insight_generator,
)

# Patterns
from .patterns import (
    PatternDetectorConfig,
    PatternDetector,
    create_pattern_detector,
    get_pattern_detector,
)

# Learning
from .learning import (
    LearningManagerConfig,
    AdaptationStrategy,
    LearningManager,
    create_learning_manager,
    get_learning_manager,
)

# Processor
from .processor import (
    MetaMindConfig,
    MetaMindOutput,
    MetaMindProcessor,
    create_metamind_processor,
    get_metamind_processor,
)


__all__ = [
    # Types - Enums
    "InsightType",
    "PatternType",
    "LearningGoalType",
    "MetaStateType",
    "AnalysisScope",
    "SeverityLevel",
    # Types - Dataclasses
    "CycleAnalysisResult",
    "Insight",
    "Pattern",
    "LearningGoal",
    "MetaState",
    # Analyzers
    "AnalyzerConfig",
    "CycleAnalyzer",
    "create_cycle_analyzer",
    "get_cycle_analyzer",
    # Insights
    "InsightGeneratorConfig",
    "InsightGenerator",
    "create_insight_generator",
    "get_insight_generator",
    # Patterns
    "PatternDetectorConfig",
    "PatternDetector",
    "create_pattern_detector",
    "get_pattern_detector",
    # Learning
    "LearningManagerConfig",
    "AdaptationStrategy",
    "LearningManager",
    "create_learning_manager",
    "get_learning_manager",
    # Processor
    "MetaMindConfig",
    "MetaMindOutput",
    "MetaMindProcessor",
    "create_metamind_processor",
    "get_metamind_processor",
]
