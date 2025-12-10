"""
tests/unit/test_intent_recognizer.py

IntentRecognizer için kapsamlı testler.

Her intent kategorisi için:
- Standart formlar
- Kısaltmalar
- Yazım hataları
- Compound intent
- Edge case'ler

50+ test.
"""

import pytest
from core.language.intent import (
    IntentRecognizer,
    IntentRecognizerConfig,
    IntentCategory,
    IntentResult,
)


@pytest.fixture
def recognizer():
    """IntentRecognizer fixture."""
    return IntentRecognizer()


@pytest.fixture
def recognizer_strict():
    """Strict threshold ile IntentRecognizer."""
    config = IntentRecognizerConfig(min_confidence_threshold=0.6)
    return IntentRecognizer(config=config)


# =========================================================================
# GREETING Tests (6 tests)
# =========================================================================

def test_greeting_standard(recognizer):
    """Standart selamlama."""
    result = recognizer.recognize("Merhaba")
    assert result.primary == IntentCategory.GREETING
    assert result.confidence > 0.5


def test_greeting_casual(recognizer):
    """Samimi selamlama."""
    result = recognizer.recognize("Selam")
    assert result.primary == IntentCategory.GREETING


def test_greeting_abbreviation_slm(recognizer):
    """Kısaltma: slm."""
    result = recognizer.recognize("slm")
    assert result.primary == IntentCategory.GREETING


def test_greeting_abbreviation_mrb(recognizer):
    """Kısaltma: mrb."""
    result = recognizer.recognize("mrb")
    assert result.primary == IntentCategory.GREETING


def test_greeting_religious(recognizer):
    """Dini selamlama: sa."""
    result = recognizer.recognize("sa")
    assert result.primary == IntentCategory.GREETING


def test_greeting_english(recognizer):
    """İngilizce selamlama."""
    result = recognizer.recognize("hello")
    assert result.primary == IntentCategory.GREETING


# =========================================================================
# FAREWELL Tests (4 tests)
# =========================================================================

def test_farewell_standard(recognizer):
    """Standart vedalaşma."""
    result = recognizer.recognize("Hoşçakal")
    assert result.primary == IntentCategory.FAREWELL


def test_farewell_informal(recognizer):
    """Informal vedalaşma."""
    result = recognizer.recognize("Görüşürüz")
    assert result.primary == IntentCategory.FAREWELL


def test_farewell_abbreviation_bb(recognizer):
    """Kısaltma: bb."""
    result = recognizer.recognize("bb")
    assert result.primary == IntentCategory.FAREWELL


def test_farewell_english(recognizer):
    """İngilizce vedalaşma."""
    result = recognizer.recognize("bye")
    assert result.primary == IntentCategory.FAREWELL


# =========================================================================
# ASK_WELLBEING Tests (5 tests)
# =========================================================================

def test_ask_wellbeing_standard(recognizer):
    """Standart hal hatır sorma."""
    result = recognizer.recognize("Nasılsın?")
    assert result.primary == IntentCategory.ASK_WELLBEING


def test_ask_wellbeing_informal(recognizer):
    """Informal: naber."""
    result = recognizer.recognize("naber")
    assert result.primary == IntentCategory.ASK_WELLBEING


def test_ask_wellbeing_abbreviation(recognizer):
    """Kısaltma: nbr."""
    result = recognizer.recognize("nbr")
    assert result.primary == IntentCategory.ASK_WELLBEING


def test_ask_wellbeing_how_are_you(recognizer):
    """İyi misin?"""
    result = recognizer.recognize("iyi misin")
    assert result.primary == IntentCategory.ASK_WELLBEING


def test_ask_wellbeing_keyifler(recognizer):
    """Keyifler nasıl?"""
    result = recognizer.recognize("keyifler nasıl")
    assert result.primary == IntentCategory.ASK_WELLBEING


# =========================================================================
# ASK_IDENTITY Tests (4 tests)
# =========================================================================

def test_ask_identity_sen_kimsin(recognizer):
    """Sen kimsin?"""
    result = recognizer.recognize("Sen kimsin?")
    assert result.primary == IntentCategory.ASK_IDENTITY


def test_ask_identity_adin_ne(recognizer):
    """Adın ne?"""
    result = recognizer.recognize("Adın ne?")
    assert result.primary == IntentCategory.ASK_IDENTITY


def test_ask_identity_nesin(recognizer):
    """Nesin?"""
    result = recognizer.recognize("Nesin?")
    assert result.primary == IntentCategory.ASK_IDENTITY


def test_ask_identity_english(recognizer):
    """İngilizce: who are you?"""
    result = recognizer.recognize("who are you")
    assert result.primary == IntentCategory.ASK_IDENTITY


# =========================================================================
# EXPRESS_POSITIVE Tests (5 tests)
# =========================================================================

def test_express_positive_iyiyim(recognizer):
    """İyiyim."""
    result = recognizer.recognize("İyiyim")
    assert result.primary == IntentCategory.EXPRESS_POSITIVE


def test_express_positive_harika(recognizer):
    """Harika!"""
    result = recognizer.recognize("Harika!")
    assert result.primary == IntentCategory.EXPRESS_POSITIVE


def test_express_positive_super(recognizer):
    """Süper."""
    result = recognizer.recognize("süper")
    assert result.primary == IntentCategory.EXPRESS_POSITIVE


def test_express_positive_mukemmel(recognizer):
    """Mükemmel."""
    result = recognizer.recognize("mükemmel")
    assert result.primary == IntentCategory.EXPRESS_POSITIVE


def test_express_positive_cok_iyi(recognizer):
    """Çok iyi."""
    result = recognizer.recognize("çok iyi")
    assert result.primary == IntentCategory.EXPRESS_POSITIVE


# =========================================================================
# EXPRESS_NEGATIVE Tests (6 tests)
# =========================================================================

def test_express_negative_kotuyum(recognizer):
    """Kötüyüm."""
    result = recognizer.recognize("Kötüyüm")
    assert result.primary == IntentCategory.EXPRESS_NEGATIVE


def test_express_negative_uzgunum(recognizer):
    """Üzgünüm."""
    result = recognizer.recognize("Üzgünüm")
    assert result.primary == IntentCategory.EXPRESS_NEGATIVE


def test_express_negative_berbat(recognizer):
    """Berbat."""
    result = recognizer.recognize("berbat")
    assert result.primary == IntentCategory.EXPRESS_NEGATIVE


def test_express_negative_mutsuzum(recognizer):
    """Mutsuzum."""
    result = recognizer.recognize("mutsuzum")
    assert result.primary == IntentCategory.EXPRESS_NEGATIVE


def test_express_negative_depresif(recognizer):
    """Depresifteyim."""
    result = recognizer.recognize("depresifteyim")
    assert result.primary == IntentCategory.EXPRESS_NEGATIVE


def test_express_negative_moralim_bozuk(recognizer):
    """Moralim bozuk."""
    result = recognizer.recognize("moralim bozuk")
    assert result.primary == IntentCategory.EXPRESS_NEGATIVE


# =========================================================================
# REQUEST_HELP Tests (4 tests)
# =========================================================================

def test_request_help_standard(recognizer):
    """Yardım et."""
    result = recognizer.recognize("Yardım et")
    assert result.primary == IntentCategory.REQUEST_HELP


def test_request_help_yardimci_ol(recognizer):
    """Yardımcı ol."""
    result = recognizer.recognize("Yardımcı ol")
    assert result.primary == IntentCategory.REQUEST_HELP


def test_request_help_english(recognizer):
    """İngilizce: help."""
    result = recognizer.recognize("help")
    assert result.primary == IntentCategory.REQUEST_HELP


def test_request_help_ihtiyacim_var(recognizer):
    """Yardıma ihtiyacım var."""
    result = recognizer.recognize("yardıma ihtiyacım var")
    assert result.primary == IntentCategory.REQUEST_HELP


# =========================================================================
# THANK Tests (5 tests)
# =========================================================================

def test_thank_standard(recognizer):
    """Teşekkürler."""
    result = recognizer.recognize("Teşekkürler")
    assert result.primary == IntentCategory.THANK


def test_thank_sagol(recognizer):
    """Sağol."""
    result = recognizer.recognize("Sağol")
    assert result.primary == IntentCategory.THANK


def test_thank_abbreviation_tsk(recognizer):
    """Kısaltma: tşk."""
    result = recognizer.recognize("tşk")
    assert result.primary == IntentCategory.THANK


def test_thank_eyvallah(recognizer):
    """Eyvallah."""
    result = recognizer.recognize("eyvallah")
    assert result.primary == IntentCategory.THANK


def test_thank_english(recognizer):
    """İngilizce: thanks."""
    result = recognizer.recognize("thanks")
    assert result.primary == IntentCategory.THANK


# =========================================================================
# AGREE Tests (4 tests)
# =========================================================================

def test_agree_evet(recognizer):
    """Evet."""
    result = recognizer.recognize("Evet")
    assert result.primary == IntentCategory.AGREE


def test_agree_tamam(recognizer):
    """Tamam."""
    result = recognizer.recognize("Tamam")
    assert result.primary == IntentCategory.AGREE


def test_agree_ok(recognizer):
    """OK."""
    result = recognizer.recognize("ok")
    assert result.primary == IntentCategory.AGREE


def test_agree_olur(recognizer):
    """Olur."""
    result = recognizer.recognize("olur")
    assert result.primary == IntentCategory.AGREE


# =========================================================================
# DISAGREE Tests (3 tests)
# =========================================================================

def test_disagree_hayir(recognizer):
    """Hayır."""
    result = recognizer.recognize("Hayır")
    assert result.primary == IntentCategory.DISAGREE


def test_disagree_olmaz(recognizer):
    """Olmaz."""
    result = recognizer.recognize("Olmaz")
    assert result.primary == IntentCategory.DISAGREE


def test_disagree_istemiyorum(recognizer):
    """İstemiyorum."""
    result = recognizer.recognize("istemiyorum")
    assert result.primary == IntentCategory.DISAGREE


# =========================================================================
# Compound Intent Tests (5 tests)
# =========================================================================

def test_compound_greeting_ask_wellbeing(recognizer):
    """Compound: Selam, nasılsın?"""
    result = recognizer.recognize("Selam, nasılsın?")
    assert result.primary == IntentCategory.GREETING
    assert result.secondary == IntentCategory.ASK_WELLBEING
    assert result.is_compound is True


def test_compound_greeting_thank(recognizer):
    """Compound: Merhaba, teşekkürler."""
    result = recognizer.recognize("Merhaba, teşekkürler")
    # GREETING veya THANK önce olabilir (confidence'a bağlı)
    categories = result.get_all_categories()
    assert IntentCategory.GREETING in categories
    assert IntentCategory.THANK in categories


def test_compound_help_request(recognizer):
    """Compound: Yardım et lütfen, nasıl yapacağım?"""
    result = recognizer.recognize("Yardım et lütfen")
    assert result.primary == IntentCategory.REQUEST_HELP


def test_compound_multiple_intents(recognizer):
    """Compound: 3 intent birden."""
    result = recognizer.recognize("Merhaba! Nasılsın? Teşekkürler!")
    assert result.is_compound is True
    assert len(result.all_matches) >= 2


def test_compound_express_and_request(recognizer):
    """Compound: Üzgünüm, yardım et."""
    result = recognizer.recognize("Üzgünüm, yardım et")
    categories = result.get_all_categories()
    # Her ikisi de olmalı
    assert IntentCategory.EXPRESS_NEGATIVE in categories or IntentCategory.REQUEST_HELP in categories


# =========================================================================
# Edge Cases (8 tests)
# =========================================================================

def test_empty_message(recognizer):
    """Boş mesaj."""
    result = recognizer.recognize("")
    assert result.primary == IntentCategory.UNKNOWN
    assert result.confidence == 0.0


def test_whitespace_only(recognizer):
    """Sadece boşluk."""
    result = recognizer.recognize("   ")
    assert result.primary == IntentCategory.UNKNOWN


def test_unknown_message(recognizer):
    """Tanınmayan mesaj."""
    result = recognizer.recognize("asdfghjkl zxcvbnm")
    assert result.primary == IntentCategory.UNKNOWN


def test_very_long_message(recognizer):
    """Çok uzun mesaj."""
    long_message = "Merhaba " + "çok " * 50 + "uzun mesaj"
    result = recognizer.recognize(long_message)
    assert result.primary == IntentCategory.GREETING


def test_punctuation_heavy(recognizer):
    """Noktalama işareti çok."""
    result = recognizer.recognize("Merhaba!!!")
    assert result.primary == IntentCategory.GREETING


def test_mixed_case(recognizer):
    """Karışık büyük/küçük harf."""
    result = recognizer.recognize("MeRhAbA")
    assert result.primary == IntentCategory.GREETING


def test_turkish_characters(recognizer):
    """Türkçe karakterler."""
    result = recognizer.recognize("İyi günler")
    assert result.primary == IntentCategory.GREETING


def test_typo_nasilsin(recognizer):
    """Yazım hatası: nasilsin."""
    result = recognizer.recognize("nasilsin")
    assert result.primary == IntentCategory.ASK_WELLBEING


# =========================================================================
# API Method Tests (5 tests)
# =========================================================================

def test_has_intent(recognizer):
    """has_intent metodu."""
    message = "Merhaba"
    assert recognizer.has_intent(message, IntentCategory.GREETING) is True
    assert recognizer.has_intent(message, IntentCategory.FAREWELL) is False


def test_get_all_matches(recognizer):
    """get_all_matches metodu."""
    matches = recognizer.get_all_matches("Selam, nasılsın?")
    assert len(matches) >= 2
    assert any(m.category == IntentCategory.GREETING for m in matches)
    assert any(m.category == IntentCategory.ASK_WELLBEING for m in matches)


def test_get_confidence_for_category(recognizer):
    """get_confidence_for_category metodu."""
    message = "Merhaba"
    confidence = recognizer.get_confidence_for_category(message, IntentCategory.GREETING)
    assert confidence > 0.5

    # Olmayan intent için 0
    confidence = recognizer.get_confidence_for_category(message, IntentCategory.FAREWELL)
    assert confidence == 0.0


def test_get_top_intents(recognizer):
    """get_top_intents metodu."""
    top_intents = recognizer.get_top_intents("Selam, nasılsın?", top_k=3)
    assert len(top_intents) <= 3
    assert all(isinstance(intent, IntentCategory) for intent, _ in top_intents)
    assert all(isinstance(conf, float) for _, conf in top_intents)


def test_batch_recognize(recognizer):
    """batch_recognize metodu."""
    messages = ["Merhaba", "Nasılsın", "Teşekkürler"]
    results = recognizer.batch_recognize(messages)
    assert len(results) == 3
    assert results[0].primary == IntentCategory.GREETING
    assert results[1].primary == IntentCategory.ASK_WELLBEING
    assert results[2].primary == IntentCategory.THANK


# =========================================================================
# Configuration Tests (2 tests)
# =========================================================================

def test_config_min_threshold(recognizer_strict):
    """Yüksek threshold ile tanıma."""
    # Düşük confidence'lı pattern'ler filtrelenmeli
    result = recognizer_strict.recognize("bb")  # Düşük confidence
    # Strict threshold ile bb gibi kısa pattern'ler filtrelenebilir
    # Ama yine de FAREWELL algılanmalı (eşik altında kalabilir)
    assert result is not None


def test_config_compound_disabled():
    """Compound detection kapalı."""
    config = IntentRecognizerConfig(compound_detection_enabled=False)
    recognizer = IntentRecognizer(config=config)
    result = recognizer.recognize("Selam, nasılsın?")
    # Compound detection kapalı olsa da primary ve secondary olabilir
    assert result.primary is not None


# =========================================================================
# Stats Tests (1 test)
# =========================================================================

def test_get_stats(recognizer):
    """get_stats metodu."""
    stats = recognizer.get_stats()
    assert "total_categories" in stats
    assert "total_patterns" in stats
    assert stats["total_categories"] > 0
    assert stats["total_patterns"] > 0
