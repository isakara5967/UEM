"""
tests/unit/test_context_manager.py

ContextManager için kapsamlı testler.

Test kategorileri:
- Message management (add, get, filter)
- Context retrieval
- Sentiment tracking
- Topic tracking
- Legacy format conversion
- Followup detection
- History limits
- API methods
- Configuration
- Edge cases

35+ test.
"""

import pytest
from datetime import datetime, timedelta

from core.language.conversation import (
    ContextManager,
    ContextConfig,
    Message,
    ConversationContext,
)
from core.language.intent.types import IntentCategory
from core.language.dialogue.types import DialogueAct


@pytest.fixture
def manager():
    """Basic ContextManager."""
    return ContextManager()


@pytest.fixture
def manager_custom():
    """ContextManager with custom config."""
    config = ContextConfig(
        max_history=3,
        sentiment_decay=0.9,
        enable_topic_tracking=True
    )
    return ContextManager(config=config)


# =========================================================================
# Message Management Tests (8 tests)
# =========================================================================

def test_add_user_message(manager):
    """Kullanıcı mesajı ekleme."""
    msg = manager.add_user_message("Merhaba", IntentCategory.GREETING)

    assert msg.role == "user"
    assert msg.content == "Merhaba"
    assert msg.intent == IntentCategory.GREETING
    assert manager.context.message_count == 1


def test_add_assistant_message(manager):
    """Asistan mesajı ekleme."""
    msg = manager.add_assistant_message("Merhaba, nasıl yardımcı olabilirim?", DialogueAct.GREET)

    assert msg.role == "assistant"
    assert msg.content == "Merhaba, nasıl yardımcı olabilirim?"
    assert msg.metadata.get("act") == DialogueAct.GREET.value
    assert manager.context.message_count == 1


def test_add_multiple_messages(manager):
    """Birden fazla mesaj ekleme."""
    manager.add_user_message("Merhaba", IntentCategory.GREETING)
    manager.add_assistant_message("Merhaba!", DialogueAct.GREET)
    manager.add_user_message("Nasılsın?", IntentCategory.ASK_WELLBEING)

    assert manager.context.message_count == 3
    assert manager.context.turn_count == 2  # 2 user messages


def test_message_without_intent(manager):
    """Intent olmadan mesaj ekleme."""
    msg = manager.add_user_message("Test mesajı")

    assert msg.intent is None
    assert msg.content == "Test mesajı"


def test_message_with_metadata(manager):
    """Metadata ile mesaj ekleme."""
    metadata = {"source": "test", "extra_info": "value"}
    msg = manager.add_user_message("Test", metadata=metadata)

    assert msg.metadata["source"] == "test"
    assert msg.metadata["extra_info"] == "value"


def test_last_user_intent_update(manager):
    """Son kullanıcı intent'i güncelleniyor mu?"""
    manager.add_user_message("Merhaba", IntentCategory.GREETING)
    assert manager.context.last_user_intent == IntentCategory.GREETING

    manager.add_user_message("Teşekkürler", IntentCategory.THANK)
    assert manager.context.last_user_intent == IntentCategory.THANK


def test_last_assistant_act_update(manager):
    """Son asistan act'i güncelleniyor mu?"""
    manager.add_assistant_message("Selam", DialogueAct.GREET)
    assert manager.context.last_assistant_act == DialogueAct.GREET

    manager.add_assistant_message("Tabii", DialogueAct.ACKNOWLEDGE)
    assert manager.context.last_assistant_act == DialogueAct.ACKNOWLEDGE


def test_turn_count_increment(manager):
    """Turn count doğru artıyor mu?"""
    assert manager.context.turn_count == 0

    manager.add_user_message("Merhaba")
    assert manager.context.turn_count == 1

    manager.add_assistant_message("Selam")
    assert manager.context.turn_count == 1  # Assistant mesajı turn count'u artırmaz

    manager.add_user_message("Nasılsın?")
    assert manager.context.turn_count == 2


# =========================================================================
# Context Retrieval Tests (7 tests)
# =========================================================================

def test_get_context(manager):
    """Context alma."""
    manager.add_user_message("Test")
    context = manager.get_context()

    assert isinstance(context, ConversationContext)
    assert context.message_count == 1


def test_get_recent_messages(manager):
    """Son N mesaj alma."""
    manager.add_user_message("Mesaj 1")
    manager.add_user_message("Mesaj 2")
    manager.add_user_message("Mesaj 3")
    manager.add_user_message("Mesaj 4")

    recent = manager.context.get_recent_messages(2)
    assert len(recent) == 2
    assert recent[0].content == "Mesaj 3"
    assert recent[1].content == "Mesaj 4"


def test_get_user_messages(manager):
    """Sadece kullanıcı mesajları alma."""
    manager.add_user_message("User 1")
    manager.add_assistant_message("Assistant 1")
    manager.add_user_message("User 2")

    user_msgs = manager.context.get_user_messages()
    assert len(user_msgs) == 2
    assert all(msg.is_user() for msg in user_msgs)


def test_get_assistant_messages(manager):
    """Sadece asistan mesajları alma."""
    manager.add_user_message("User 1")
    manager.add_assistant_message("Assistant 1")
    manager.add_assistant_message("Assistant 2")

    assistant_msgs = manager.context.get_assistant_messages()
    assert len(assistant_msgs) == 2
    assert all(msg.is_assistant() for msg in assistant_msgs)


def test_get_last_user_message(manager):
    """Son kullanıcı mesajı alma."""
    manager.add_user_message("First")
    manager.add_assistant_message("Response")
    manager.add_user_message("Second")

    last = manager.context.get_last_user_message()
    assert last is not None
    assert last.content == "Second"


def test_get_last_assistant_message(manager):
    """Son asistan mesajı alma."""
    manager.add_assistant_message("First")
    manager.add_user_message("User msg")
    manager.add_assistant_message("Second")

    last = manager.context.get_last_assistant_message()
    assert last is not None
    assert last.content == "Second"


def test_empty_context(manager):
    """Boş context kontrolü."""
    assert manager.context.is_empty is True
    assert manager.context.message_count == 0

    manager.add_user_message("Test")
    assert manager.context.is_empty is False


# =========================================================================
# Sentiment Tracking Tests (5 tests)
# =========================================================================

def test_sentiment_positive(manager):
    """Pozitif duygu tespiti."""
    manager.add_user_message("Harika, çok mutluyum!")

    # Pozitif olmalı
    assert manager.context.user_sentiment > 0.0


def test_sentiment_negative(manager):
    """Negatif duygu tespiti."""
    manager.add_user_message("Berbat, çok üzgünüm")

    # Negatif olmalı
    assert manager.context.user_sentiment < 0.0


def test_sentiment_neutral(manager):
    """Nötr duygu."""
    manager.add_user_message("Toplantı saat 3'te")

    # Nötr olmalı (0'a yakın)
    assert abs(manager.context.user_sentiment) < 0.3


def test_sentiment_running_average(manager):
    """Duygu running average."""
    # İlk mesaj pozitif
    manager.add_user_message("Harika!")
    first_sentiment = manager.context.user_sentiment

    # İkinci mesaj negatif
    manager.add_user_message("Berbat")
    second_sentiment = manager.context.user_sentiment

    # İkinci sentiment negatif ama ilkinden etkilenmeli (decay)
    assert second_sentiment < first_sentiment
    assert second_sentiment < 0.0  # Negatif olmalı


def test_get_sentiment_trend(manager):
    """Sentiment trend alma."""
    # İlk mesaj decay nedeniyle düşük kalır, birkaç pozitif mesaj ekle
    manager.add_user_message("Çok mutluyum, harika!")
    manager.add_user_message("Süper, çok iyi!")
    assert manager.get_sentiment_trend() == "positive"

    manager.reset()
    # Negatif trend için birkaç mesaj
    manager.add_user_message("Berbat, çok kötü")
    manager.add_user_message("Üzgünüm, mutsuzum")
    assert manager.get_sentiment_trend() == "negative"

    manager.reset()
    manager.add_user_message("Toplantı yarın")
    assert manager.get_sentiment_trend() == "neutral"


# =========================================================================
# Topic Tracking Tests (4 tests)
# =========================================================================

def test_topic_detection_technology(manager):
    """Teknoloji konusu tespiti."""
    manager.add_user_message("Bilgisayarım çalışmıyor")
    assert manager.context.current_topic == "technology"


def test_topic_detection_health(manager):
    """Sağlık konusu tespiti."""
    manager.add_user_message("Başım ağrıyor, doktora gitmeli miyim?")
    assert manager.context.current_topic == "health"


def test_topic_change(manager):
    """Konu değişikliği."""
    manager.add_user_message("Bilgisayar problemi var")
    assert manager.context.current_topic == "technology"

    manager.add_user_message("Okul sınavım var")
    assert manager.context.current_topic == "education"


def test_topic_disabled(manager):
    """Topic tracking kapalı."""
    config = ContextConfig(enable_topic_tracking=False)
    manager_no_topic = ContextManager(config=config)

    manager_no_topic.add_user_message("Bilgisayar")
    # Topic tracking kapalı olsa da mesaj eklenebilmeli
    assert manager_no_topic.context.message_count == 1


# =========================================================================
# Legacy Format Tests (4 tests)
# =========================================================================

def test_to_legacy_format(manager):
    """Legacy format'a çevirme."""
    manager.add_user_message("Merhaba")
    manager.add_assistant_message("Selam")

    legacy = manager.to_legacy_format()

    assert len(legacy) == 2
    assert legacy[0] == {"role": "user", "content": "Merhaba"}
    assert legacy[1] == {"role": "assistant", "content": "Selam"}


def test_from_legacy_format(manager):
    """Legacy format'tan yükleme."""
    legacy = [
        {"role": "user", "content": "Merhaba"},
        {"role": "assistant", "content": "Selam"},
        {"role": "user", "content": "Nasılsın?"}
    ]

    manager.from_legacy_format(legacy)

    assert manager.context.message_count == 3
    assert manager.context.turn_count == 2  # 2 user messages


def test_legacy_roundtrip(manager):
    """Legacy format çift yönlü dönüşüm."""
    manager.add_user_message("Test 1")
    manager.add_assistant_message("Response 1")

    legacy = manager.to_legacy_format()

    manager2 = ContextManager()
    manager2.from_legacy_format(legacy)

    assert manager2.context.message_count == 2
    legacy2 = manager2.to_legacy_format()
    assert legacy == legacy2


def test_empty_legacy_format(manager):
    """Boş legacy format."""
    legacy = manager.to_legacy_format()
    assert legacy == []


# =========================================================================
# Followup Detection Tests (3 tests)
# =========================================================================

def test_followup_detection_positive(manager):
    """Followup sorusu tespiti - pozitif."""
    manager.add_user_message("Bilgisayar nasıl çalışır?")
    manager.add_assistant_message("İşlemci komutları yürütür...")
    manager.add_user_message("Peki işlemci nedir?")

    assert manager.is_followup_question() is True


def test_followup_detection_negative(manager):
    """Followup sorusu tespiti - negatif."""
    manager.add_user_message("Hava nasıl?")

    # İlk mesaj, followup olamaz
    assert manager.is_followup_question() is False


def test_followup_long_message(manager):
    """Uzun mesaj followup olamaz."""
    manager.add_user_message("İlk mesaj")
    manager.add_assistant_message("Yanıt")
    manager.add_user_message("Peki bu çok uzun bir mesaj on kelimeden fazla kesinlikle")

    # Çok uzun olduğu için followup sayılmamalı
    assert manager.is_followup_question() is False


# =========================================================================
# History Limits Tests (3 tests)
# =========================================================================

def test_max_history_limit(manager_custom):
    """Max history limiti (3 mesaj)."""
    manager_custom.add_user_message("Mesaj 1")
    manager_custom.add_user_message("Mesaj 2")
    manager_custom.add_user_message("Mesaj 3")
    manager_custom.add_user_message("Mesaj 4")

    # Max 3 mesaj tutulmalı
    assert manager_custom.context.message_count == 3

    # En eski (Mesaj 1) silinmeli
    contents = [msg.content for msg in manager_custom.context.messages]
    assert "Mesaj 1" not in contents
    assert "Mesaj 4" in contents


def test_default_max_history(manager):
    """Varsayılan max history (5)."""
    for i in range(7):
        manager.add_user_message(f"Mesaj {i}")

    assert manager.context.message_count == 5


def test_history_overflow_maintains_order(manager_custom):
    """Geçmiş taştığında sıra korunuyor mu?"""
    manager_custom.add_user_message("A")
    manager_custom.add_user_message("B")
    manager_custom.add_user_message("C")
    manager_custom.add_user_message("D")  # A silinmeli

    contents = [msg.content for msg in manager_custom.context.messages]
    assert contents == ["B", "C", "D"]


# =========================================================================
# API Method Tests (6 tests)
# =========================================================================

def test_get_recent_intents(manager):
    """Son N intent alma."""
    manager.add_user_message("Merhaba", IntentCategory.GREETING)
    manager.add_user_message("Teşekkürler", IntentCategory.THANK)
    manager.add_user_message("Hoşçakal", IntentCategory.FAREWELL)

    recent = manager.get_recent_intents(2)

    assert len(recent) == 2
    assert recent[0] == IntentCategory.FAREWELL  # En yeni
    assert recent[1] == IntentCategory.THANK


def test_get_recent_acts(manager):
    """Son N act alma."""
    manager.add_assistant_message("Selam", DialogueAct.GREET)
    manager.add_assistant_message("Tamam", DialogueAct.ACKNOWLEDGE)

    recent = manager.get_recent_acts(2)

    assert len(recent) == 2
    assert recent[0] == DialogueAct.ACKNOWLEDGE  # En yeni
    assert recent[1] == DialogueAct.GREET


def test_get_context_summary(manager):
    """Context özeti alma."""
    manager.add_user_message("Bilgisayar çalışmıyor")
    manager.add_assistant_message("Anlıyorum")

    summary = manager.get_context_summary()

    assert "Messages:" in summary
    assert "Turns:" in summary
    assert "Sentiment:" in summary
    assert "Topic:" in summary


def test_reset_context(manager):
    """Context sıfırlama."""
    manager.add_user_message("Test 1")
    manager.add_user_message("Test 2")

    assert manager.context.message_count == 2

    manager.reset()

    assert manager.context.message_count == 0
    assert manager.context.turn_count == 0
    assert manager.context.is_empty is True


def test_session_duration(manager):
    """Session süresi."""
    duration = manager.context.session_duration_seconds

    # Yeni session, 0'a yakın olmalı
    assert duration >= 0.0
    assert duration < 1.0  # 1 saniyeden az


def test_get_recent_intents_fewer_than_requested(manager):
    """İstenendan az mesaj varsa."""
    manager.add_user_message("Merhaba", IntentCategory.GREETING)

    recent = manager.get_recent_intents(5)  # 5 isteniyor ama sadece 1 var

    assert len(recent) == 1
    assert recent[0] == IntentCategory.GREETING


# =========================================================================
# Configuration Tests (2 tests)
# =========================================================================

def test_custom_config(manager_custom):
    """Custom config kullanımı."""
    assert manager_custom.config.max_history == 3
    assert manager_custom.config.sentiment_decay == 0.9


def test_sentiment_disabled():
    """Sentiment tracking kapalı."""
    config = ContextConfig(enable_sentiment_tracking=False)
    manager_no_sentiment = ContextManager(config=config)

    manager_no_sentiment.add_user_message("Harika!")

    # Sentiment tracking kapalı, 0 olmalı
    assert manager_no_sentiment.context.user_sentiment == 0.0


# =========================================================================
# Edge Cases (3 tests)
# =========================================================================

def test_empty_message(manager):
    """Boş mesaj."""
    msg = manager.add_user_message("")

    assert msg.content == ""
    assert manager.context.message_count == 1


def test_very_long_message(manager):
    """Çok uzun mesaj."""
    long_text = "test " * 1000
    msg = manager.add_user_message(long_text)

    assert msg.content == long_text
    assert manager.context.message_count == 1


def test_special_characters(manager):
    """Özel karakterler."""
    special_text = "Merhaba! Nasılsın? #test @user €100"
    msg = manager.add_user_message(special_text)

    assert msg.content == special_text
