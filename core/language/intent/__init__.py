"""
core/language/intent

Intent Recognition modülü.

UEM v2 - Intent sistemi.
"""

from .types import (
    IntentCategory,
    IntentMatch,
    IntentResult,
)

from .recognizer import (
    IntentRecognizer,
    IntentRecognizerConfig,
)

from .patterns import (
    INTENT_PATTERNS,
    PATTERN_WEIGHTS,
    get_pattern_weight,
    get_all_patterns,
    get_pattern_count,
    get_patterns_for_category,
)

__all__ = [
    # Types
    "IntentCategory",
    "IntentMatch",
    "IntentResult",
    # Recognizer
    "IntentRecognizer",
    "IntentRecognizerConfig",
    # Patterns
    "INTENT_PATTERNS",
    "PATTERN_WEIGHTS",
    "get_pattern_weight",
    "get_all_patterns",
    "get_pattern_count",
    "get_patterns_for_category",
]
