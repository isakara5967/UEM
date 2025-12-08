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


__all__ = [
    # Enums
    "FeedbackType",
    "PatternType",
    # Dataclasses
    "Feedback",
    "Pattern",
    "LearningOutcome",
    # Utility functions
    "generate_feedback_id",
    "generate_pattern_id",
    # Classes
    "FeedbackCollector",
    "PatternStorage",
]
