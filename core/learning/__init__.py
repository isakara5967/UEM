"""
core/learning/__init__.py

Learning Module - Geri bildirim ve pattern ogrenme.
UEM v2 - Kullanici etkilesimlerinden ogrenme.

Components:
- FeedbackType: Geri bildirim turleri
- PatternType: Davranis pattern turleri
- Feedback: Geri bildirim kaydi
- Pattern: Ogrenilen davranis patterni
- LearningOutcome: Ogrenme sonucu
- FeedbackCollector: Geri bildirim toplama
- PatternStorage: Pattern depolama ve arama
- RewardConfig: Reward hesaplama konfigurasyonu
- RewardCalculator: Feedback'ten reward hesaplama
- Reinforcer: Pattern guclendrme
- AdaptationConfig: Adaptasyon konfigurasyonu
- BehaviorAdapter: Davranis adaptasyonu
- LearningProcessor: Ana ogrenme koordinatoru
"""

from .types import (
    FeedbackType,
    PatternType,
    Feedback,
    Pattern,
    LearningOutcome,
    generate_feedback_id,
    generate_pattern_id,
)

from .feedback import FeedbackCollector

from .patterns import PatternStorage

from .reinforcement import (
    RewardConfig,
    RewardCalculator,
    Reinforcer,
)

from .adaptation import (
    AdaptationConfig,
    AdaptationRecord,
    BehaviorAdapter,
)

from .processor import LearningProcessor


__all__ = [
    # Enums
    "FeedbackType",
    "PatternType",
    # Dataclasses
    "Feedback",
    "Pattern",
    "LearningOutcome",
    "RewardConfig",
    "AdaptationConfig",
    "AdaptationRecord",
    # Utility functions
    "generate_feedback_id",
    "generate_pattern_id",
    # Classes
    "FeedbackCollector",
    "PatternStorage",
    "RewardCalculator",
    "Reinforcer",
    "BehaviorAdapter",
    "LearningProcessor",
]
