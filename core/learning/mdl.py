"""
core/learning/mdl.py

ApproximateMDL - Minimum Description Length yaklasik hesaplayici.
UEM v2 - Pattern degerlendirme ve secim icin.

MDL (Minimum Description Length) prensibi:
En iyi model, veriyi en kisa sekilde tanımlayan modeldir.
Pattern'in episode grubunu ne kadar iyi "sıkıştırdığını" ölçer.

Formül:
    compression_score = (episode_count × avg_original_length) - (pattern_length × episode_count)
    normalized = compression_score / (episode_count × avg_original_length)

Final skor:
    final = (normalized_compression × 0.5) + (diversity × 0.3) - (risk × 0.2)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .episode import Episode
    from .types import Pattern

logger = logging.getLogger(__name__)


@dataclass
class MDLConfig:
    """
    ApproximateMDL konfigurasyonu.

    Attributes:
        compression_weight: Sikistirma skoru agirligi
        diversity_weight: Cesitlilik bonus agirligi
        risk_weight: Risk ceza agirligi
        min_episodes_for_evaluation: Minimum episode sayisi
        risk_keywords: Risk iceren kelimeler
        ethical_concerns: Etik endise kelimeleri
    """
    compression_weight: float = 0.5
    diversity_weight: float = 0.3
    risk_weight: float = 0.2

    min_episodes_for_evaluation: int = 2

    # Risk keyword'leri (normalized Turkce)
    risk_keywords: Set[str] = field(default_factory=lambda: {
        # Zarar
        "zarar", "tehlike", "tehlikeli", "olum", "oldur", "intihar",
        "siddet", "dovmek", "yaralamak",
        # Yasal sorunlar
        "yasadisi", "suç", "hacklemek", "çalmak", "dolandirmak",
        # Saglik riskleri
        "ilac", "doz", "asiri doz", "zehir",
        # Kisisel bilgi
        "sifre", "kredi karti", "kimlik",
    })

    # Etik endise kelimeleri
    ethical_concerns: Set[str] = field(default_factory=lambda: {
        "ayrimcilik", "irkçilik", "cinsiyetçilik", "nefret",
        "manipulasyon", "aldatma", "yalan",
        "gizlilik", "mahremiyet", "izinsiz",
    })

    # Diversity icin bonus katsayilari
    intent_diversity_bonus: float = 0.1
    emotion_diversity_bonus: float = 0.1
    unique_pattern_bonus: float = 0.1


@dataclass
class MDLScore:
    """
    MDL degerlendirme sonucu.

    Attributes:
        compression_score: Ham sikistirma skoru
        normalized_score: Normalize edilmis skor [0.0 - 1.0]
        episode_count: Degerlendirilen episode sayisi
        avg_episode_length: Ortalama episode uzunlugu
        pattern_length: Pattern uzunlugu
        diversity_bonus: Cesitlilik bonusu
        risk_penalty: Risk cezasi
        final_score: Nihai skor
        details: Ek detaylar
    """
    compression_score: float
    normalized_score: float
    episode_count: int
    avg_episode_length: float
    pattern_length: int
    diversity_bonus: float = 0.0
    risk_penalty: float = 0.0
    final_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate final score if not set."""
        if self.final_score == 0.0 and self.normalized_score > 0:
            self.final_score = self.normalized_score

    @property
    def is_good_pattern(self) -> bool:
        """Pattern iyi mi? (final_score > 0.5)"""
        return self.final_score > 0.5

    @property
    def is_risky(self) -> bool:
        """Pattern riskli mi?"""
        return self.risk_penalty > 0.1


class ApproximateMDL:
    """
    Minimum Description Length yaklasik hesaplayici.

    Pattern'in bir episode grubunu ne kadar iyi tanımladığını ölçer.
    Daha kısa pattern, daha fazla episode'u tanımlıyorsa daha iyidir.

    Kullanim:
        mdl = ApproximateMDL()

        # Tek pattern degerlendirme
        score = mdl.evaluate_candidate(pattern, episodes)
        print(f"Final skor: {score.final_score}")

        # Pattern karsilastirma
        better = mdl.compare_patterns(pattern1, pattern2, episodes)

        # Sikistirma skoru
        compression = mdl.compute_compression_score(pattern, episodes)
    """

    def __init__(self, config: Optional[MDLConfig] = None):
        """
        ApproximateMDL olustur.

        Args:
            config: Konfigurasyon (opsiyonel)
        """
        self.config = config or MDLConfig()
        self._normalize_func = self._get_normalize_func()

    def _get_normalize_func(self):
        """Normalizasyon fonksiyonunu al."""
        try:
            from core.utils.text import normalize_turkish
            return normalize_turkish
        except ImportError:
            logger.warning("normalize_turkish not available, using simple lower()")
            return lambda x: x.lower() if x else ""

    def compute_compression_score(
        self,
        pattern: "Pattern",
        episodes: List["Episode"]
    ) -> float:
        """
        Sikistirma skoru hesapla.

        Formül:
            compression = (episode_count × avg_length) - (pattern_length × episode_count)

        Args:
            pattern: Degerlendirilen pattern
            episodes: Episode listesi

        Returns:
            float: Sikistirma skoru (pozitif = iyi sikistirma)
        """
        if not episodes:
            return 0.0

        episode_count = len(episodes)
        avg_episode_length = sum(
            self.compute_episode_length(ep) for ep in episodes
        ) / episode_count

        pattern_length = self.compute_pattern_length(pattern)

        # MDL formülü
        original_bits = episode_count * avg_episode_length
        compressed_bits = pattern_length + (episode_count * 2)  # Pattern + pointer per episode

        compression_score = original_bits - compressed_bits

        return compression_score

    def compute_pattern_length(self, pattern: "Pattern") -> int:
        """
        Pattern uzunlugunu hesapla.

        Uzunluk = template uzunlugu + slot sayisi * slot_cost

        Args:
            pattern: Pattern

        Returns:
            int: Pattern uzunlugu (bit benzeri birim)
        """
        # Pattern content uzunlugu
        content_length = len(pattern.content) if pattern.content else 0

        # Extra data'daki slot bilgisi
        slots = pattern.extra_data.get("slots", [])
        slot_count = len(slots) if isinstance(slots, list) else 0

        # Her slot ek maliyet
        slot_cost = slot_count * 5

        # Pattern type maliyeti
        type_cost = 2

        return content_length + slot_cost + type_cost

    def compute_episode_length(self, episode: "Episode") -> int:
        """
        Episode uzunlugunu hesapla.

        Uzunluk = mesaj uzunlugu + metadata maliyeti

        Args:
            episode: Episode

        Returns:
            int: Episode uzunlugu (bit benzeri birim)
        """
        # Mesaj uzunlugu
        message_length = len(episode.user_message) if episode.user_message else 0

        # Intent maliyeti
        intent_cost = len(episode.intent) if episode.intent else 0

        # Emotion maliyeti
        emotion_cost = len(episode.emotion_label) if episode.emotion_label else 0

        # Dialogue acts maliyeti
        acts_cost = sum(len(act) for act in episode.dialogue_acts) if episode.dialogue_acts else 0

        # Metadata overhead
        metadata_cost = 10

        return message_length + intent_cost + emotion_cost + acts_cost + metadata_cost

    def evaluate_candidate(
        self,
        pattern: "Pattern",
        episodes: List["Episode"],
        existing_patterns: Optional[List["Pattern"]] = None
    ) -> MDLScore:
        """
        Pattern adayini degerlendir.

        Final skor:
            final = (normalized × compression_weight) +
                    (diversity × diversity_weight) -
                    (risk × risk_weight)

        Args:
            pattern: Degerlendirilen pattern
            episodes: Episode listesi
            existing_patterns: Mevcut pattern'ler (uniqueness icin)

        Returns:
            MDLScore: Degerlendirme sonucu
        """
        if len(episodes) < self.config.min_episodes_for_evaluation:
            return MDLScore(
                compression_score=0.0,
                normalized_score=0.0,
                episode_count=len(episodes),
                avg_episode_length=0.0,
                pattern_length=self.compute_pattern_length(pattern),
                details={"error": "Not enough episodes"}
            )

        # 1. Sikistirma skoru
        compression_score = self.compute_compression_score(pattern, episodes)

        # 2. Normalize et
        episode_count = len(episodes)
        avg_episode_length = sum(
            self.compute_episode_length(ep) for ep in episodes
        ) / episode_count

        original_bits = episode_count * avg_episode_length
        normalized_score = compression_score / original_bits if original_bits > 0 else 0.0
        normalized_score = max(0.0, min(1.0, (normalized_score + 1) / 2))  # [-1,1] -> [0,1]

        # 3. Diversity bonus
        diversity_bonus = self._compute_diversity_bonus(
            pattern, episodes, existing_patterns
        )

        # 4. Risk penalty
        risk_penalty = self._compute_risk_penalty(pattern)

        # 5. Final skor
        final_score = (
            normalized_score * self.config.compression_weight +
            diversity_bonus * self.config.diversity_weight -
            risk_penalty * self.config.risk_weight
        )
        final_score = max(0.0, min(1.0, final_score))

        return MDLScore(
            compression_score=compression_score,
            normalized_score=normalized_score,
            episode_count=episode_count,
            avg_episode_length=avg_episode_length,
            pattern_length=self.compute_pattern_length(pattern),
            diversity_bonus=diversity_bonus,
            risk_penalty=risk_penalty,
            final_score=final_score,
            details={
                "original_bits": original_bits,
                "intent_diversity": self._get_unique_intents(episodes),
                "emotion_diversity": self._get_unique_emotions(episodes),
            }
        )

    def _compute_diversity_bonus(
        self,
        pattern: "Pattern",
        episodes: List["Episode"],
        existing_patterns: Optional[List["Pattern"]] = None
    ) -> float:
        """
        Cesitlilik bonusu hesapla.

        Args:
            pattern: Pattern
            episodes: Episode listesi
            existing_patterns: Mevcut pattern'ler

        Returns:
            float: Diversity bonus [0.0 - 1.0]
        """
        bonus = 0.0

        # 1. Intent diversity
        unique_intents = self._get_unique_intents(episodes)
        if len(unique_intents) > 1:
            bonus += self.config.intent_diversity_bonus * min(len(unique_intents), 5) / 5

        # 2. Emotion diversity
        unique_emotions = self._get_unique_emotions(episodes)
        if len(unique_emotions) > 1:
            bonus += self.config.emotion_diversity_bonus * min(len(unique_emotions), 5) / 5

        # 3. Uniqueness bonus (mevcut pattern'lere benzemiyor)
        if existing_patterns:
            is_unique = self._is_unique_pattern(pattern, existing_patterns)
            if is_unique:
                bonus += self.config.unique_pattern_bonus

        return min(1.0, bonus)

    def _get_unique_intents(self, episodes: List["Episode"]) -> Set[str]:
        """Episode'lardaki unique intent'leri getir."""
        return {ep.intent for ep in episodes if ep.intent}

    def _get_unique_emotions(self, episodes: List["Episode"]) -> Set[str]:
        """Episode'lardaki unique emotion'lari getir."""
        return {ep.emotion_label for ep in episodes if ep.emotion_label}

    def _is_unique_pattern(
        self,
        pattern: "Pattern",
        existing_patterns: List["Pattern"]
    ) -> bool:
        """
        Pattern benzersiz mi kontrol et.

        Args:
            pattern: Kontrol edilecek pattern
            existing_patterns: Mevcut pattern'ler

        Returns:
            bool: Benzersiz ise True
        """
        if not existing_patterns:
            return True

        pattern_content = self._normalize_func(pattern.content)

        for existing in existing_patterns:
            existing_content = self._normalize_func(existing.content)

            # Ayni icerik
            if pattern_content == existing_content:
                return False

            # Cok benzer (Jaccard > 0.8)
            if self._jaccard_similarity(pattern_content, existing_content) > 0.8:
                return False

        return True

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Basit Jaccard benzerligi."""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _compute_risk_penalty(self, pattern: "Pattern") -> float:
        """
        Risk cezasi hesapla.

        Args:
            pattern: Pattern

        Returns:
            float: Risk penalty [0.0 - 1.0]
        """
        if not pattern.content:
            return 0.0

        normalized_content = self._normalize_func(pattern.content)
        penalty = 0.0

        # Risk keyword kontrolu
        risk_count = sum(
            1 for keyword in self.config.risk_keywords
            if keyword in normalized_content
        )
        if risk_count > 0:
            penalty += min(risk_count * 0.2, 0.6)

        # Ethical concern kontrolu
        ethical_count = sum(
            1 for concern in self.config.ethical_concerns
            if concern in normalized_content
        )
        if ethical_count > 0:
            penalty += min(ethical_count * 0.15, 0.4)

        return min(1.0, penalty)

    def compare_patterns(
        self,
        pattern1: "Pattern",
        pattern2: "Pattern",
        episodes: List["Episode"],
        existing_patterns: Optional[List["Pattern"]] = None
    ) -> "Pattern":
        """
        Iki pattern'i karsilastir ve daha iyisini don.

        Args:
            pattern1: Birinci pattern
            pattern2: Ikinci pattern
            episodes: Episode listesi
            existing_patterns: Mevcut pattern'ler

        Returns:
            Pattern: Daha iyi pattern
        """
        score1 = self.evaluate_candidate(pattern1, episodes, existing_patterns)
        score2 = self.evaluate_candidate(pattern2, episodes, existing_patterns)

        if score1.final_score >= score2.final_score:
            return pattern1
        return pattern2

    def rank_patterns(
        self,
        patterns: List["Pattern"],
        episodes: List["Episode"],
        existing_patterns: Optional[List["Pattern"]] = None
    ) -> List[tuple]:
        """
        Pattern'leri sirala.

        Args:
            patterns: Pattern listesi
            episodes: Episode listesi
            existing_patterns: Mevcut pattern'ler

        Returns:
            List[tuple]: (pattern, score) listesi, skorla sirali
        """
        scored = []

        for pattern in patterns:
            score = self.evaluate_candidate(pattern, episodes, existing_patterns)
            scored.append((pattern, score))

        # Final score'a gore sirala (yuksekten dusuge)
        scored.sort(key=lambda x: x[1].final_score, reverse=True)

        return scored

    def filter_good_patterns(
        self,
        patterns: List["Pattern"],
        episodes: List["Episode"],
        min_score: float = 0.5,
        existing_patterns: Optional[List["Pattern"]] = None
    ) -> List["Pattern"]:
        """
        Iyi pattern'leri filtrele.

        Args:
            patterns: Pattern listesi
            episodes: Episode listesi
            min_score: Minimum skor esigi
            existing_patterns: Mevcut pattern'ler

        Returns:
            List[Pattern]: Iyi pattern'ler
        """
        good_patterns = []

        for pattern in patterns:
            score = self.evaluate_candidate(pattern, episodes, existing_patterns)
            if score.final_score >= min_score and not score.is_risky:
                good_patterns.append(pattern)

        return good_patterns

    def get_score_breakdown(
        self,
        pattern: "Pattern",
        episodes: List["Episode"]
    ) -> Dict[str, Any]:
        """
        Detayli skor raporu.

        Args:
            pattern: Pattern
            episodes: Episode listesi

        Returns:
            Dict: Detayli rapor
        """
        score = self.evaluate_candidate(pattern, episodes)

        return {
            "pattern_id": pattern.id,
            "pattern_content": pattern.content,
            "final_score": score.final_score,
            "is_good": score.is_good_pattern,
            "is_risky": score.is_risky,
            "components": {
                "compression": {
                    "raw_score": score.compression_score,
                    "normalized": score.normalized_score,
                    "weight": self.config.compression_weight,
                    "weighted": score.normalized_score * self.config.compression_weight,
                },
                "diversity": {
                    "bonus": score.diversity_bonus,
                    "weight": self.config.diversity_weight,
                    "weighted": score.diversity_bonus * self.config.diversity_weight,
                },
                "risk": {
                    "penalty": score.risk_penalty,
                    "weight": self.config.risk_weight,
                    "weighted": score.risk_penalty * self.config.risk_weight,
                },
            },
            "episode_stats": {
                "count": score.episode_count,
                "avg_length": score.avg_episode_length,
            },
            "pattern_stats": {
                "length": score.pattern_length,
            },
            "details": score.details,
        }
