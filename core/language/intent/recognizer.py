"""
core/language/intent/recognizer.py

IntentRecognizer - Kullanıcı mesajından intent çıkarma.

Türkçe normalizasyon, pattern matching, compound intent detection,
confidence scoring ile maksimum seviye intent recognition.

UEM v2 - Intent Recognition sistemi.
"""

import re
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from core.utils.text import normalize_turkish
from .types import IntentCategory, IntentMatch, IntentResult
from .patterns import INTENT_PATTERNS, get_pattern_weight

logger = logging.getLogger(__name__)


@dataclass
class IntentRecognizerConfig:
    """
    IntentRecognizer konfigürasyonu.

    Attributes:
        min_confidence_threshold: Minimum güven eşiği
        compound_detection_enabled: Compound intent algılama aktif mi?
        max_intents_per_message: Mesaj başına maksimum intent sayısı
        normalize_enabled: Türkçe normalizasyon aktif mi?
    """
    min_confidence_threshold: float = 0.3
    compound_detection_enabled: bool = True
    max_intents_per_message: int = 3
    normalize_enabled: bool = True


class IntentRecognizer:
    """
    Kullanıcı mesajından intent çıkarır.

    Türkçe varyantlar, kısaltmalar, yazım hatalarını destekler.
    Compound intent detection (birden fazla intent aynı mesajda).
    Confidence scoring ile güvenilirlik.

    Kullanım:
        recognizer = IntentRecognizer()

        # Tek intent
        result = recognizer.recognize("Merhaba, nasılsın?")
        print(result.primary)  # IntentCategory.GREETING
        print(result.secondary)  # IntentCategory.ASK_WELLBEING
        print(result.is_compound)  # True

        # Tüm eşleşmeler
        matches = recognizer.get_all_matches("Selam! Yardım eder misin?")
        for match in matches:
            print(f"{match.category}: {match.confidence}")
    """

    def __init__(self, config: Optional[IntentRecognizerConfig] = None):
        """
        IntentRecognizer oluştur.

        Args:
            config: Recognizer konfigürasyonu
        """
        self.config = config or IntentRecognizerConfig()
        self._pattern_cache: Dict[IntentCategory, List[str]] = {}
        self._build_pattern_cache()

    def _build_pattern_cache(self) -> None:
        """Pattern cache'i oluştur."""
        for category, patterns in INTENT_PATTERNS.items():
            self._pattern_cache[category] = patterns
        logger.debug(f"Pattern cache built: {len(self._pattern_cache)} categories")

    def recognize(self, message: str) -> IntentResult:
        """
        Ana intent tanıma metodu.

        Args:
            message: Kullanıcı mesajı

        Returns:
            IntentResult: Tanıma sonucu
        """
        if not message or not message.strip():
            return IntentResult(
                primary=IntentCategory.UNKNOWN,
                confidence=0.0,
                matched_patterns=[],
                is_compound=False
            )

        # 1. Metni normalize et
        normalized_text = self._normalize(message) if self.config.normalize_enabled else message.lower()

        # 2. Tüm eşleşmeleri bul
        all_matches = self._match_patterns(normalized_text)

        # 3. Eşleşme yoksa UNKNOWN
        if not all_matches:
            return IntentResult(
                primary=IntentCategory.UNKNOWN,
                confidence=0.2,  # Mesaj var ama tanınmadı
                matched_patterns=[],
                is_compound=False
            )

        # 4. Confidence eşiğinin üstündekileri filtrele
        valid_matches = [
            m for m in all_matches
            if m.confidence >= self.config.min_confidence_threshold
        ]

        if not valid_matches:
            return IntentResult(
                primary=IntentCategory.UNKNOWN,
                confidence=0.2,
                matched_patterns=[],
                is_compound=False
            )

        # 5. Compound intent kontrolü
        is_compound = len(valid_matches) > 1 and self.config.compound_detection_enabled

        # 6. Primary ve secondary intent seç
        primary_match = valid_matches[0]
        secondary_match = valid_matches[1] if len(valid_matches) > 1 else None

        # 7. Matched pattern'leri topla
        matched_patterns = [m.matched_pattern for m in valid_matches[:self.config.max_intents_per_message]]

        # 8. Genel confidence hesapla
        overall_confidence = self._calculate_overall_confidence(valid_matches)

        return IntentResult(
            primary=primary_match.category,
            secondary=secondary_match.category if secondary_match else None,
            confidence=overall_confidence,
            matched_patterns=matched_patterns,
            is_compound=is_compound,
            all_matches=valid_matches[:self.config.max_intents_per_message]
        )

    def get_all_matches(self, message: str) -> List[IntentMatch]:
        """
        Mesajdaki tüm intent eşleşmelerini döndür.

        Args:
            message: Kullanıcı mesajı

        Returns:
            Tüm eşleşmeler (sıralı, confidence'a göre)
        """
        normalized_text = self._normalize(message) if self.config.normalize_enabled else message.lower()
        all_matches = self._match_patterns(normalized_text)
        return all_matches

    def _normalize(self, text: str) -> str:
        """
        Türkçe normalize + lowercase.

        Args:
            text: Normalize edilecek metin

        Returns:
            Normalize edilmiş metin
        """
        # normalize_turkish kullan (zaten lowercase yapıyor)
        normalized = normalize_turkish(text)

        # Ekstra temizlik
        # Noktalama işaretlerini kaldır (bazı durumlarda)
        # Ama "?" gibi önemli işaretleri koru
        normalized = normalized.strip()

        return normalized

    def _match_patterns(self, normalized_text: str) -> List[IntentMatch]:
        """
        Normalize edilmiş metinde pattern eşleştir.

        Args:
            normalized_text: Normalize edilmiş metin

        Returns:
            Tüm eşleşmeler (confidence'a göre sıralı)
        """
        matches: List[IntentMatch] = []

        for category, patterns in self._pattern_cache.items():
            for pattern in patterns:
                if self._pattern_matches(pattern, normalized_text):
                    # Pattern pozisyonunu bul
                    pattern_position = self._get_pattern_position(pattern, normalized_text)

                    # Confidence hesapla
                    confidence = self._calculate_confidence(
                        pattern, normalized_text, category, pattern_position
                    )

                    matches.append(IntentMatch(
                        category=category,
                        confidence=confidence,
                        matched_pattern=pattern,
                        normalized_text=normalized_text
                    ))

                    # Bir kategoriden sadece en iyi eşleşmeyi al
                    # (aynı kategoriden birden fazla pattern eşleşebilir)
                    break

        # Confidence'a göre sırala (büyükten küçüğe)
        matches.sort(key=lambda m: m.confidence, reverse=True)

        return matches

    def _pattern_matches(self, pattern: str, text: str) -> bool:
        """
        Pattern'in metinde olup olmadığını kontrol et.

        Args:
            pattern: Aranacak pattern
            text: Metin

        Returns:
            True eğer eşleşme varsa
        """
        # Basit substring matching
        # Kelime sınırları kontrol et (daha doğru eşleşme için)

        # Tek kelimelik pattern'ler için kelime sınırı kontrolü
        if " " not in pattern:
            # Kelime sınırları ile kontrol
            # "merhaba" pattern'i "merhabalar" ile eşleşmemeli
            pattern_regex = r'\b' + re.escape(pattern) + r'\b'
            return bool(re.search(pattern_regex, text))
        else:
            # Çok kelimeli pattern'ler için substring yeterli
            return pattern in text

    def _get_pattern_position(self, pattern: str, text: str) -> int:
        """
        Pattern'in metinde kaçıncı pozisyonda olduğunu döndür.

        Args:
            pattern: Aranacak pattern
            text: Metin

        Returns:
            Pattern başlangıç pozisyonu (0-indexed), bulunamazsa -1
        """
        # Kelime sınırları ile ara
        if " " not in pattern:
            pattern_regex = r'\b' + re.escape(pattern) + r'\b'
            match = re.search(pattern_regex, text)
            if match:
                return match.start()
        else:
            # Substring ara
            idx = text.find(pattern)
            if idx != -1:
                return idx
        return -1

    def _calculate_confidence(
        self,
        pattern: str,
        text: str,
        category: IntentCategory,
        pattern_position: int = -1
    ) -> float:
        """
        Eşleşme için confidence skoru hesapla.

        Faktörler:
        - Pattern spesifikliği (uzunluk)
        - Pattern ağırlığı (PATTERN_WEIGHTS'ten)
        - Mesaj uzunluğu
        - Tam eşleşme vs. kısmi eşleşme
        - Pattern pozisyonu (compound intent için)

        Args:
            pattern: Eşleşen pattern
            text: Normalize edilmiş metin
            category: Intent kategorisi
            pattern_position: Pattern'in metindeki başlangıç pozisyonu

        Returns:
            Confidence skoru (0.0-1.0)
        """
        base_confidence = 0.7

        # 1. Pattern ağırlığı
        pattern_weight = get_pattern_weight(pattern)
        confidence = base_confidence * pattern_weight

        # 2. Pattern uzunluğu bonusu (daha uzun = daha spesifik)
        pattern_length = len(pattern)
        if pattern_length > 15:
            confidence += 0.15
        elif pattern_length > 8:
            confidence += 0.10
        elif pattern_length < 4:
            confidence -= 0.10

        # 3. Tam eşleşme bonusu
        # Eğer mesaj sadece bu pattern'den oluşuyorsa
        if text.strip() == pattern.strip():
            confidence += 0.15

        # 4. Mesaj uzunluğu etkisi
        # Kısa mesajlarda eşleşme daha güvenilir
        word_count = len(text.split())
        if word_count <= 3:
            confidence += 0.05
        elif word_count > 15:
            confidence -= 0.05

        # 5. Soru işareti kontrolü (ASK kategorileri için)
        if "?" in text:
            if "ask" in category.value or "question" in category.value:
                confidence += 0.05

        # 6. Pattern pozisyonu bonusu (compound intent için)
        # Mesajda önce geçen pattern daha yüksek öncelik
        if pattern_position >= 0 and len(text) > len(pattern):
            # Pozisyon yüzdesini hesapla
            position_ratio = pattern_position / max(1, len(text) - len(pattern))
            # Önde olan pattern'e bonus (0-10% arası)
            position_bonus = (1.0 - position_ratio) * 0.10
            confidence += position_bonus

        # Sınırla
        return min(1.0, max(0.0, confidence))

    def _calculate_overall_confidence(
        self,
        matches: List[IntentMatch]
    ) -> float:
        """
        Genel güven skoru hesapla.

        Args:
            matches: Tüm eşleşmeler

        Returns:
            Genel confidence (0.0-1.0)
        """
        if not matches:
            return 0.0

        # En yüksek confidence'ı kullan
        top_confidence = matches[0].confidence

        # Birden fazla eşleşme varsa confidence düşür
        # (belirsizlik var demektir)
        if len(matches) > 2:
            top_confidence *= 0.9
        elif len(matches) > 1:
            top_confidence *= 0.95

        return min(1.0, top_confidence)

    def _handle_compound(self, text: str) -> List[IntentCategory]:
        """
        Compound intent (birden fazla intent) tespit et.

        Örnek: "Selam, nasılsın?" = GREETING + ASK_WELLBEING

        Args:
            text: Normalize edilmiş metin

        Returns:
            Tespit edilen intent'ler
        """
        # Bu metod recognize() içinde zaten yapılıyor
        # Ama ayrı bir API olarak da kullanılabilir
        result = self.recognize(text)
        return result.get_all_categories()

    def has_intent(self, message: str, category: IntentCategory) -> bool:
        """
        Mesajda belirli bir intent var mı kontrol et.

        Args:
            message: Kullanıcı mesajı
            category: Kontrol edilecek kategori

        Returns:
            True eğer intent varsa
        """
        result = self.recognize(message)
        return result.has_intent(category)

    def get_confidence_for_category(
        self,
        message: str,
        category: IntentCategory
    ) -> float:
        """
        Belirli bir kategori için confidence skoru.

        Args:
            message: Kullanıcı mesajı
            category: Intent kategorisi

        Returns:
            Confidence skoru (0.0 eğer intent yoksa)
        """
        all_matches = self.get_all_matches(message)
        for match in all_matches:
            if match.category == category:
                return match.confidence
        return 0.0

    def get_top_intents(
        self,
        message: str,
        top_k: int = 3
    ) -> List[Tuple[IntentCategory, float]]:
        """
        En yüksek skorlu K intent.

        Args:
            message: Kullanıcı mesajı
            top_k: Kaç intent döndürülsün

        Returns:
            (IntentCategory, confidence) tuple'ları
        """
        all_matches = self.get_all_matches(message)
        top_matches = all_matches[:top_k]
        return [(m.category, m.confidence) for m in top_matches]

    def batch_recognize(
        self,
        messages: List[str]
    ) -> List[IntentResult]:
        """
        Birden fazla mesaj için intent tanıma.

        Args:
            messages: Mesaj listesi

        Returns:
            Her mesaj için IntentResult
        """
        results = []
        for message in messages:
            results.append(self.recognize(message))
        return results

    def get_stats(self) -> Dict[str, int]:
        """
        İstatistikler.

        Returns:
            İstatistik sözlüğü
        """
        total_patterns = sum(len(patterns) for patterns in self._pattern_cache.values())
        return {
            "total_categories": len(self._pattern_cache),
            "total_patterns": total_patterns,
            "avg_patterns_per_category": total_patterns // len(self._pattern_cache) if self._pattern_cache else 0
        }
