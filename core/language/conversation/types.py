"""
core/language/conversation/types.py

Conversation Context types - Multi-turn conversation context management.

Message, ConversationContext, ContextConfig - Basit, etkili.

UEM v2 - Context Integration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum

from ..intent.types import IntentCategory
from ..dialogue.types import DialogueAct


@dataclass
class Message:
    """
    Tek bir konuşma mesajı.

    Attributes:
        role: Mesaj gönderici rolü ("user" veya "assistant")
        content: Mesaj içeriği
        intent: Algılanan intent (opsiyonel)
        timestamp: Mesaj zamanı
        metadata: Ek bilgiler
    """
    role: str  # "user" or "assistant"
    content: str
    intent: Optional[IntentCategory] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def is_user(self) -> bool:
        """Kullanıcı mesajı mı?"""
        return self.role == "user"

    def is_assistant(self) -> bool:
        """Asistan mesajı mı?"""
        return self.role == "assistant"


@dataclass
class ConversationContext:
    """
    Multi-turn konuşma bağlamı.

    Son N mesajı tutar, konu ve duygu takibi yapar.

    Attributes:
        messages: Son N mesaj listesi
        current_topic: Mevcut konu (opsiyonel)
        last_user_intent: Son kullanıcı intent'i
        last_assistant_act: Son asistan eylemi
        session_start: Oturum başlangıç zamanı
        turn_count: Toplam tur sayısı
        user_sentiment: Kullanıcı duygu ortalaması (-1.0 to 1.0)
        metadata: Ek bağlam bilgileri
    """
    messages: List[Message] = field(default_factory=list)
    current_topic: Optional[str] = None
    last_user_intent: Optional[IntentCategory] = None
    last_assistant_act: Optional[DialogueAct] = None
    session_start: datetime = field(default_factory=datetime.now)
    turn_count: int = 0
    user_sentiment: float = 0.0  # -1.0 (very negative) to 1.0 (very positive)
    metadata: dict = field(default_factory=dict)

    def get_recent_messages(self, n: int = 3) -> List[Message]:
        """Son N mesajı döndür."""
        return self.messages[-n:] if len(self.messages) >= n else self.messages

    def get_user_messages(self) -> List[Message]:
        """Sadece kullanıcı mesajlarını döndür."""
        return [m for m in self.messages if m.is_user()]

    def get_assistant_messages(self) -> List[Message]:
        """Sadece asistan mesajlarını döndür."""
        return [m for m in self.messages if m.is_assistant()]

    def get_last_user_message(self) -> Optional[Message]:
        """Son kullanıcı mesajını döndür."""
        user_messages = self.get_user_messages()
        return user_messages[-1] if user_messages else None

    def get_last_assistant_message(self) -> Optional[Message]:
        """Son asistan mesajını döndür."""
        assistant_messages = self.get_assistant_messages()
        return assistant_messages[-1] if assistant_messages else None

    @property
    def message_count(self) -> int:
        """Toplam mesaj sayısı."""
        return len(self.messages)

    @property
    def is_empty(self) -> bool:
        """Bağlam boş mu?"""
        return len(self.messages) == 0

    @property
    def session_duration_seconds(self) -> float:
        """Oturum süresi (saniye)."""
        return (datetime.now() - self.session_start).total_seconds()


@dataclass
class ContextConfig:
    """
    ContextManager konfigürasyonu.

    Attributes:
        max_history: Maksimum mesaj geçmişi sayısı (son N mesaj tutulur)
        sentiment_decay: Duygu azalma faktörü (running average için)
        enable_topic_tracking: Konu takibi aktif mi?
        enable_sentiment_tracking: Duygu takibi aktif mi?
        topic_change_threshold: Konu değişikliği eşiği (0.0-1.0)
    """
    max_history: int = 5  # Son 5 mesaj
    sentiment_decay: float = 0.8  # Yeni mesaj %20, eski ortalama %80
    enable_topic_tracking: bool = True
    enable_sentiment_tracking: bool = True
    topic_change_threshold: float = 0.5  # >0.5 farklılık = konu değişti
