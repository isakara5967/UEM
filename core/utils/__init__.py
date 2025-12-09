"""
core/utils/__init__.py

UEM v2 Utility Functions.

Common utilities used across all modules.
"""

from .text import normalize_turkish, normalize_for_matching

__all__ = [
    "normalize_turkish",
    "normalize_for_matching",
]
