"""
core/language/intent/types.py

Intent tanımlama ve kategorilendirme tipleri.

UEM v2 - Intent Recognition sistemi.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class IntentCategory(str, Enum):
    """
    Kullanıcı niyeti kategorileri.

    17 temel intent kategorisi + UNKNOWN.
    Her kategori Türkçe varyantlar, kısaltmalar ve yazım hatalarını destekler.
    """
    GREETING = "greeting"                  # merhaba, selam, naber, hey, slm
    FAREWELL = "farewell"                  # hoşçakal, görüşürüz, bb, bye
    ASK_WELLBEING = "ask_wellbeing"        # nasılsın, naber, keyifler nasıl
    ASK_IDENTITY = "ask_identity"          # sen kimsin, adın ne, nesin
    EXPRESS_POSITIVE = "express_positive"  # iyiyim, harika, süper, mükemmel
    EXPRESS_NEGATIVE = "express_negative"  # kötüyüm, üzgünüm, berbat, mutsuz
    REQUEST_HELP = "request_help"          # yardım et, yardımcı ol, help
    REQUEST_INFO = "request_info"          # bilgi ver, anlat, açıkla, nedir
    THANK = "thank"                        # teşekkürler, sağol, eyvallah, tşk
    APOLOGIZE = "apologize"                # özür dilerim, pardon, kusura bakma
    AGREE = "agree"                        # evet, tamam, ok, olur, kabul
    DISAGREE = "disagree"                  # hayır, yok, olmaz, istemiyorum
    CLARIFY = "clarify"                    # anlamadım, ne demek, tekrar et
    COMPLAIN = "complain"                  # şikayet, sorun var, çalışmıyor
    META_QUESTION = "meta_question"        # neden böyle dedin, nasıl çalışıyorsun
    SMALLTALK = "smalltalk"                # hava nasıl, ne yapıyorsun
    UNKNOWN = "unknown"                    # tanınmayan


@dataclass
class IntentMatch:
    """
    Bir intent eşleşmesi.

    Attributes:
        category: Intent kategorisi
        confidence: Güven skoru (0.0-1.0)
        matched_pattern: Eşleşen pattern
        normalized_text: Normalize edilmiş metin
    """
    category: IntentCategory
    confidence: float
    matched_pattern: str
    normalized_text: str


@dataclass
class IntentResult:
    """
    Intent tanıma sonucu.

    Attributes:
        primary: Ana intent
        secondary: İkincil intent (varsa)
        confidence: Genel güven skoru (0.0-1.0)
        matched_patterns: Eşleşen tüm pattern'ler
        is_compound: Birden fazla intent var mı?
        all_matches: Tüm eşleşmeler (sıralı)
    """
    primary: IntentCategory
    secondary: Optional[IntentCategory] = None
    confidence: float = 0.0
    matched_patterns: List[str] = field(default_factory=list)
    is_compound: bool = False
    all_matches: List[IntentMatch] = field(default_factory=list)

    def has_intent(self, category: IntentCategory) -> bool:
        """
        Belirli bir intent kategorisinin bulunup bulunmadığını kontrol et.

        Args:
            category: Kontrol edilecek kategori

        Returns:
            True eğer primary veya secondary bu kategoriyse
        """
        return self.primary == category or self.secondary == category

    def get_all_categories(self) -> List[IntentCategory]:
        """
        Tüm intent kategorilerini döndür.

        Returns:
            Primary ve secondary dahil tüm kategoriler
        """
        categories = [self.primary]
        if self.secondary:
            categories.append(self.secondary)
        return categories
