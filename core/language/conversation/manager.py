"""
core/language/conversation/manager.py

ContextManager - Multi-turn conversation context yönetimi.

Mesaj geçmişi, konu takibi, duygu takibi.

UEM v2 - Context Integration.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime

from .types import Message, ConversationContext, ContextConfig
from ..intent.types import IntentCategory
from ..dialogue.types import DialogueAct

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Multi-turn konuşma bağlamı yöneticisi.

    Mesaj geçmişini tutar, konu ve duygu takibi yapar.
    Basit, etkili - son 5 mesaj, sentiment tracking.

    Kullanım:
        manager = ContextManager()

        # Kullanıcı mesajı ekle
        manager.add_user_message("Merhaba!", IntentCategory.GREETING)

        # Asistan yanıtı ekle
        manager.add_assistant_message("Merhaba, nasıl yardımcı olabilirim?", DialogueAct.GREET)

        # Context al
        context = manager.get_context()
        print(context.last_user_intent)  # IntentCategory.GREETING
        print(context.turn_count)  # 1

        # Eski format'a çevir (pipeline uyumluluğu için)
        legacy_context = manager.to_legacy_format()
        # [{"role": "user", "content": "Merhaba!"}, ...]
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        """
        ContextManager oluştur.

        Args:
            config: Context konfigürasyonu
        """
        self.config = config or ContextConfig()
        self.context = ConversationContext()
        self._previous_sentiment = 0.0  # Track previous sentiment for trend calculation

    def add_user_message(
        self,
        content: str,
        intent: Optional[IntentCategory] = None,
        metadata: Optional[dict] = None
    ) -> Message:
        """
        Kullanıcı mesajı ekle.

        Args:
            content: Mesaj içeriği
            intent: Algılanan intent (opsiyonel)
            metadata: Ek bilgiler

        Returns:
            Eklenen mesaj
        """
        message = Message(
            role="user",
            content=content,
            intent=intent,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        self._add_message(message)

        # Intent güncelle
        if intent:
            self.context.last_user_intent = intent

        # Sentiment güncelle
        if self.config.enable_sentiment_tracking:
            self._update_sentiment(message)

        # Topic güncelle
        if self.config.enable_topic_tracking:
            self._update_topic(message)

        # Followup check - calculate before incrementing turn_count
        self.context.is_followup = self.is_followup_question()

        self.context.turn_count += 1

        logger.debug(f"Added user message: {content[:50]}... (intent: {intent})")
        return message

    def add_assistant_message(
        self,
        content: str,
        act: Optional[DialogueAct] = None,
        metadata: Optional[dict] = None
    ) -> Message:
        """
        Asistan mesajı ekle.

        Args:
            content: Mesaj içeriği
            act: Kullanılan dialogue act (opsiyonel)
            metadata: Ek bilgiler

        Returns:
            Eklenen mesaj
        """
        message = Message(
            role="assistant",
            content=content,
            intent=None,  # Asistan'ın intent'i yok
            timestamp=datetime.now(),
            metadata={**(metadata or {}), "act": act.value if act else None}
        )

        self._add_message(message)

        # Act güncelle
        if act:
            self.context.last_assistant_act = act

        logger.debug(f"Added assistant message: {content[:50]}... (act: {act})")
        return message

    def _add_message(self, message: Message) -> None:
        """
        Mesajı context'e ekle ve geçmiş limitini uygula.

        Args:
            message: Eklenecek mesaj
        """
        self.context.messages.append(message)

        # Geçmiş limiti aşıldıysa en eskiyi sil
        if len(self.context.messages) > self.config.max_history:
            removed = self.context.messages.pop(0)
            logger.debug(f"Removed oldest message from context: {removed.content[:30]}...")

    def _update_sentiment(self, message: Message) -> None:
        """
        Kullanıcı duygu ortalamasını güncelle.

        Basit sentiment tahmini: pozitif/negatif kelime sayımı.

        Args:
            message: Kullanıcı mesajı
        """
        if not message.is_user():
            return

        # Basit sentiment hesaplama
        from core.utils.text import normalize_turkish
        content_normalized = normalize_turkish(message.content)

        # Pozitif/negatif kelimeler
        positive_words = ["iyi", "harika", "mutlu", "tesekkur", "seviyorum", "super", "guzel"]
        negative_words = ["kotu", "uzgun", "sinirli", "berbat", "nefret", "mutsuz"]

        positive_count = sum(1 for word in positive_words if word in content_normalized)
        negative_count = sum(1 for word in negative_words if word in content_normalized)

        # Sentiment skoru (-1 to 1)
        if positive_count > 0 or negative_count > 0:
            message_sentiment = (positive_count - negative_count) / max(1, positive_count + negative_count)
        else:
            message_sentiment = 0.0

        # Running average güncelle (decay ile)
        # new_avg = old_avg * decay + new_value * (1 - decay)
        self.context.user_sentiment = (
            self.context.user_sentiment * self.config.sentiment_decay +
            message_sentiment * (1 - self.config.sentiment_decay)
        )

        # Sınırla
        self.context.user_sentiment = max(-1.0, min(1.0, self.context.user_sentiment))

        # Sentiment trend hesapla
        epsilon = 0.1  # Threshold for detecting change
        if self.context.user_sentiment > self._previous_sentiment + epsilon:
            self.context.sentiment_trend = 1  # Increasing
        elif self.context.user_sentiment < self._previous_sentiment - epsilon:
            self.context.sentiment_trend = -1  # Decreasing
        else:
            self.context.sentiment_trend = 0  # Stable

        logger.debug(
            f"Updated sentiment: message={message_sentiment:.2f}, "
            f"running_avg={self.context.user_sentiment:.2f}, "
            f"trend={self.context.sentiment_trend}"
        )

        # Save current sentiment for next comparison
        self._previous_sentiment = self.context.user_sentiment

    def _update_topic(self, message: Message) -> None:
        """
        Mevcut konuyu güncelle.

        Basit konu tespiti: anahtar kelimeler.

        Args:
            message: Kullanıcı mesajı
        """
        if not message.is_user():
            return

        from core.utils.text import normalize_turkish
        content_normalized = normalize_turkish(message.content)

        # Topic pattern'leri (basit)
        topic_patterns = {
            "technology": ["bilgisayar", "yazilim", "kod", "program", "internet"],
            "health": ["saglik", "hastalik", "doktor", "ilac", "agri"],
            "relationships": ["iliski", "aile", "arkadas", "sevgili"],
            "education": ["okul", "ders", "sinav", "ogren", "egitim"],
            "work": ["is", "kariyer", "maas", "patron", "calisma"],
            "emotions": ["hissediyorum", "duygu", "mutlu", "uzgun"],
        }

        detected_topic = None
        for topic, patterns in topic_patterns.items():
            if any(pattern in content_normalized for pattern in patterns):
                detected_topic = topic
                break

        # Konu değişti mi?
        if detected_topic and detected_topic != self.context.current_topic:
            old_topic = self.context.current_topic
            self.context.current_topic = detected_topic
            logger.debug(f"Topic changed: {old_topic} -> {detected_topic}")
        elif detected_topic:
            self.context.current_topic = detected_topic

    def get_context(self) -> ConversationContext:
        """
        Mevcut context'i al.

        Returns:
            ConversationContext
        """
        return self.context

    def to_legacy_format(self) -> List[Dict[str, str]]:
        """
        Eski pipeline format'ına çevir.

        Pipeline'ın beklediği format:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Returns:
            Legacy format liste
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.context.messages
        ]

    def from_legacy_format(self, legacy_context: List[Dict[str, str]]) -> None:
        """
        Eski format'tan context'i yükle.

        Args:
            legacy_context: [{"role": "user", "content": "..."}] formatında liste
        """
        for item in legacy_context:
            role = item.get("role", "user")
            content = item.get("content", "")

            if role == "user":
                self.add_user_message(content)
            elif role == "assistant":
                self.add_assistant_message(content)

        logger.debug(f"Loaded {len(legacy_context)} messages from legacy format")

    def is_followup_question(self) -> bool:
        """
        Son mesaj bir takip sorusu mu?

        Takip sorusu: Önceki konuyla ilgili, bağlamsal referans var.

        Returns:
            True eğer takip sorusu ise
        """
        if len(self.context.messages) < 2:
            return False

        last_msg = self.context.get_last_user_message()
        if not last_msg:
            return False

        from core.utils.text import normalize_turkish
        content = normalize_turkish(last_msg.content)

        # Bağlamsal referans göstergeleri
        followup_indicators = [
            "peki", "ya", "o zaman", "ee", "tamam ama",
            "bunun", "onun", "bu", "o",
            "daha", "baska", "ayrica"
        ]

        # Kısa soru (<10 kelime) + gösterge
        word_count = len(content.split())
        has_indicator = any(indicator in content for indicator in followup_indicators)

        return word_count < 10 and has_indicator

    def is_topic_change(self) -> bool:
        """
        Konu değişikliği var mı?

        Son 2 mesajın konusunu karşılaştır.

        Returns:
            True eğer konu değişmişse
        """
        if len(self.context.messages) < 2:
            return False

        # Basit: metadata'da topic change flag
        last_msg = self.context.get_last_user_message()
        if last_msg and last_msg.metadata.get("topic_change"):
            return True

        # Daha gelişmiş: konu pattern'lerini karşılaştır
        # (Şimdilik basit tutalım)
        return False

    def get_sentiment_trend(self) -> str:
        """
        Duygu eğilimini döndür.

        Returns:
            "positive", "negative", veya "neutral"
        """
        if self.context.user_sentiment > 0.3:
            return "positive"
        elif self.context.user_sentiment < -0.3:
            return "negative"
        else:
            return "neutral"

    def reset(self) -> None:
        """
        Context'i sıfırla (yeni oturum için).
        """
        self.context = ConversationContext()
        self._previous_sentiment = 0.0  # Reset sentiment tracking
        logger.info("Context reset - new session started")

    def get_recent_intents(self, n: int = 3) -> List[Optional[IntentCategory]]:
        """
        Son N kullanıcı mesajının intent'lerini döndür.

        Args:
            n: Kaç mesaj geriye gidilsin

        Returns:
            Intent listesi (en yeni → en eski)
        """
        user_messages = self.context.get_user_messages()
        recent = user_messages[-n:] if len(user_messages) >= n else user_messages
        return [msg.intent for msg in reversed(recent)]

    def get_recent_acts(self, n: int = 3) -> List[Optional[DialogueAct]]:
        """
        Son N asistan mesajının act'lerini döndür.

        Args:
            n: Kaç mesaj geriye gidilsin

        Returns:
            Act listesi (en yeni → en eski)
        """
        assistant_messages = self.context.get_assistant_messages()
        recent = assistant_messages[-n:] if len(assistant_messages) >= n else assistant_messages
        acts = []
        for msg in reversed(recent):
            act_value = msg.metadata.get("act")
            if act_value:
                try:
                    acts.append(DialogueAct(act_value))
                except ValueError:
                    acts.append(None)
            else:
                acts.append(None)
        return acts

    def get_context_summary(self) -> str:
        """
        Context'in kısa özetini döndür.

        Returns:
            Özet string
        """
        msg_count = self.context.message_count
        turn_count = self.context.turn_count
        sentiment = self.get_sentiment_trend()
        topic = self.context.current_topic or "general"

        return (
            f"Messages: {msg_count}, Turns: {turn_count}, "
            f"Sentiment: {sentiment}, Topic: {topic}"
        )
