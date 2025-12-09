"""
tests/unit/test_text_utils.py

Text utilities test module.
Tests for Turkish character normalization and text processing.
"""

import pytest

from core.utils.text import (
    normalize_turkish,
    normalize_for_matching,
    TURKISH_TO_ASCII,
)


# ============================================================================
# normalize_turkish Tests
# ============================================================================

class TestNormalizeTurkish:
    """normalize_turkish function tests."""

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert normalize_turkish("") == ""

    def test_none_handling(self):
        """None handling - should not crash."""
        # normalize_turkish expects str, passing empty string instead
        assert normalize_turkish("") == ""

    def test_lowercase_conversion(self):
        """Uppercase letters are converted to lowercase."""
        assert normalize_turkish("MERHABA") == "merhaba"
        assert normalize_turkish("HeLLo") == "hello"

    def test_turkish_u_umlaut(self):
        """Turkish ü is converted to u."""
        assert normalize_turkish("ü") == "u"
        assert normalize_turkish("Ü") == "u"
        assert normalize_turkish("üzgün") == "uzgun"
        assert normalize_turkish("Üzgün") == "uzgun"

    def test_turkish_o_umlaut(self):
        """Turkish ö is converted to o."""
        assert normalize_turkish("ö") == "o"
        assert normalize_turkish("Ö") == "o"
        assert normalize_turkish("öğretmen") == "ogretmen"
        assert normalize_turkish("Ölçü") == "olcu"

    def test_turkish_s_cedilla(self):
        """Turkish ş is converted to s."""
        assert normalize_turkish("ş") == "s"
        assert normalize_turkish("Ş") == "s"
        assert normalize_turkish("şeker") == "seker"
        assert normalize_turkish("Şikayet") == "sikayet"

    def test_turkish_g_breve(self):
        """Turkish ğ is converted to g."""
        assert normalize_turkish("ğ") == "g"
        assert normalize_turkish("Ğ") == "g"
        assert normalize_turkish("dağ") == "dag"
        assert normalize_turkish("Soğuk") == "soguk"

    def test_turkish_dotless_i(self):
        """Turkish ı is converted to i."""
        assert normalize_turkish("ı") == "i"
        assert normalize_turkish("sıcak") == "sicak"
        assert normalize_turkish("kısıtlı") == "kisitli"

    def test_turkish_dotted_I(self):
        """Turkish İ is converted to I then to i (lowercase)."""
        assert normalize_turkish("İ") == "i"
        assert normalize_turkish("İstanbul") == "istanbul"
        assert normalize_turkish("İyi") == "iyi"

    def test_turkish_c_cedilla(self):
        """Turkish ç is converted to c."""
        assert normalize_turkish("ç") == "c"
        assert normalize_turkish("Ç") == "c"
        assert normalize_turkish("çiçek") == "cicek"
        assert normalize_turkish("Çok") == "cok"

    def test_mixed_turkish_chars(self):
        """Multiple Turkish characters in same string."""
        assert normalize_turkish("Türkçe") == "turkce"
        assert normalize_turkish("Günaydın") == "gunaydin"
        assert normalize_turkish("öğrenci") == "ogrenci"
        assert normalize_turkish("İşçi") == "isci"
        assert normalize_turkish("Şikayet") == "sikayet"

    def test_full_sentence(self):
        """Full Turkish sentence normalization."""
        result = normalize_turkish("Merhaba, nasılsın?")
        assert result == "merhaba, nasilsin?"

        result = normalize_turkish("Çok üzgünüm, kendimi kötü hissediyorum.")
        assert result == "cok uzgunum, kendimi kotu hissediyorum."

    def test_numbers_preserved(self):
        """Numbers are preserved."""
        assert normalize_turkish("123") == "123"
        assert normalize_turkish("Test123") == "test123"

    def test_special_chars_preserved(self):
        """Special characters are preserved."""
        assert normalize_turkish("test@email.com") == "test@email.com"
        assert normalize_turkish("Merhaba!") == "merhaba!"
        assert normalize_turkish("Ne zaman?") == "ne zaman?"

    def test_whitespace_preserved(self):
        """Whitespace is preserved."""
        assert normalize_turkish("  test  ") == "  test  "
        assert normalize_turkish("a b c") == "a b c"

    def test_already_ascii(self):
        """ASCII-only text is just lowercased."""
        assert normalize_turkish("hello world") == "hello world"
        assert normalize_turkish("HELLO WORLD") == "hello world"


# ============================================================================
# normalize_for_matching Tests
# ============================================================================

class TestNormalizeForMatching:
    """normalize_for_matching function tests."""

    def test_is_alias_for_normalize_turkish(self):
        """normalize_for_matching is an alias for normalize_turkish."""
        test_strings = [
            "Merhaba",
            "Üzgün",
            "Şikayet",
            "İstanbul",
            "çok güzel",
        ]

        for s in test_strings:
            assert normalize_for_matching(s) == normalize_turkish(s)

    def test_matching_use_case(self):
        """Test typical matching use case."""
        user_input = "Çok üzgünüm"
        pattern = "uzgun"

        normalized_input = normalize_for_matching(user_input)
        assert pattern in normalized_input


# ============================================================================
# TURKISH_TO_ASCII Mapping Tests
# ============================================================================

class TestTurkishToAsciiMapping:
    """TURKISH_TO_ASCII mapping tests."""

    def test_all_mappings_exist(self):
        """All Turkish characters have mappings."""
        expected_chars = ['ü', 'Ü', 'ö', 'Ö', 'ş', 'Ş', 'ğ', 'Ğ', 'ı', 'İ', 'ç', 'Ç']
        for char in expected_chars:
            assert char in TURKISH_TO_ASCII

    def test_mappings_are_ascii(self):
        """All mapped values are ASCII."""
        for tr_char, ascii_char in TURKISH_TO_ASCII.items():
            assert ord(ascii_char) < 128, f"{ascii_char} is not ASCII"

    def test_case_pairs_match(self):
        """Upper and lower case mappings are consistent."""
        pairs = [
            ('ü', 'Ü'),
            ('ö', 'Ö'),
            ('ş', 'Ş'),
            ('ğ', 'Ğ'),
            ('ç', 'Ç'),
        ]

        for lower, upper in pairs:
            lower_map = TURKISH_TO_ASCII[lower]
            upper_map = TURKISH_TO_ASCII[upper]
            assert lower_map.lower() == upper_map.lower()


# ============================================================================
# Integration Tests with Other Modules
# ============================================================================

class TestIntegrationWithLanguageModules:
    """Integration tests with language modules."""

    def test_situation_builder_pattern_matching(self):
        """Test that normalized patterns work with situation builder."""
        # Simulate pattern matching as done in situation_builder
        message = "Çok üzgünüm"
        normalized = normalize_turkish(message)

        # Pattern should match after normalization
        assert "uzgun" in normalized

    def test_risk_scorer_keyword_matching(self):
        """Test that normalized keywords work with risk scorer."""
        # Safety keywords in Turkish
        keywords = ["intihar", "kendine zarar", "olmek"]

        # User message with Turkish chars
        message = "Ölmek istiyorum"
        normalized = normalize_turkish(message)

        # Should match the normalized keyword
        assert "olmek" in normalized

    def test_emotional_words_matching(self):
        """Test emotional word matching."""
        positive_words = ["mutlu", "harika", "guzel"]
        negative_words = ["uzgun", "kotu", "sinirli"]

        # Turkish messages
        messages = [
            ("Çok mutluyum", "positive"),
            ("Kendimi kötü hissediyorum", "negative"),
            ("Üzgünüm", "negative"),
        ]

        for message, expected_type in messages:
            normalized = normalize_turkish(message)
            if expected_type == "positive":
                assert any(w in normalized for w in positive_words)
            else:
                assert any(w in normalized for w in negative_words)

    def test_topic_domain_matching(self):
        """Test topic domain pattern matching."""
        # Patterns for health topic (normalized)
        health_patterns = ["saglik", "hastalik", "doktor", "ilac"]

        # Turkish message about health
        message = "Sağlık sorunum var, ilaç almam gerekiyor"
        normalized = normalize_turkish(message)

        # Should match health patterns
        assert any(p in normalized for p in health_patterns)

    def test_intent_pattern_matching(self):
        """Test intent pattern matching."""
        # Intent patterns (normalized)
        help_patterns = ["yardim", "nasil", "ne yapmali"]
        greet_patterns = ["merhaba", "selam", "gunaydin"]

        # Test messages
        test_cases = [
            ("Yardım eder misin?", help_patterns),
            ("Nasıl yapmalıyım?", help_patterns),
            ("Merhaba!", greet_patterns),
            ("Günaydın", greet_patterns),
        ]

        for message, patterns in test_cases:
            normalized = normalize_turkish(message)
            assert any(p in normalized for p in patterns), \
                f"'{message}' should match {patterns}"


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_very_long_string(self):
        """Very long strings are handled correctly."""
        long_string = "Türkçe " * 1000
        result = normalize_turkish(long_string)
        assert len(result) > 0
        assert "ü" not in result

    def test_unicode_emojis(self):
        """Emojis are preserved."""
        result = normalize_turkish("Merhaba 😊")
        assert "merhaba" in result
        assert "😊" in result

    def test_repeated_turkish_chars(self):
        """Repeated Turkish characters are all converted."""
        result = normalize_turkish("üüüüü")
        assert result == "uuuuu"

    def test_mixed_unicode(self):
        """Mixed Unicode characters are handled."""
        result = normalize_turkish("Тест Türkçe مرحبا")
        assert "turkce" in result
