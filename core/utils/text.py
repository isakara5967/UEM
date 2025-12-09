"""
core/utils/text.py

Text utility functions for UEM.

Provides Turkish character normalization and text processing utilities
used across all language modules for consistent pattern matching.
"""

from typing import Dict

# Turkish character mapping to ASCII equivalents
TURKISH_TO_ASCII: Dict[str, str] = {
    'ü': 'u', 'Ü': 'U',
    'ö': 'o', 'Ö': 'O',
    'ş': 's', 'Ş': 'S',
    'ğ': 'g', 'Ğ': 'G',
    'ı': 'i', 'İ': 'I',
    'ç': 'c', 'Ç': 'C',
}


def normalize_turkish(text: str) -> str:
    """
    Normalize Turkish text by converting Turkish characters to ASCII and lowercasing.

    This function is essential for consistent pattern matching across all
    language modules, as it ensures that both input and patterns are
    normalized before comparison.

    Args:
        text: Input text (may contain Turkish characters)

    Returns:
        Normalized text (ASCII lowercase)

    Examples:
        >>> normalize_turkish("Merhaba Dünya")
        'merhaba dunya'
        >>> normalize_turkish("İyi günler")
        'iyi gunler'
        >>> normalize_turkish("ŞEKER")
        'seker'
        >>> normalize_turkish("çığır")
        'cigir'
    """
    if not text:
        return ""

    result = text
    for tr_char, ascii_char in TURKISH_TO_ASCII.items():
        result = result.replace(tr_char, ascii_char)

    return result.lower()


def normalize_for_matching(text: str) -> str:
    """
    Normalize text for pattern matching.

    Alias for normalize_turkish, providing a more descriptive name
    for use in pattern matching contexts.

    Args:
        text: Input text

    Returns:
        Normalized text for matching

    Examples:
        >>> normalize_for_matching("Üzgünüm")
        'uzgunum'
    """
    return normalize_turkish(text)
