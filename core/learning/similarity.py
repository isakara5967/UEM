"""
core/learning/similarity.py

EpisodeSimilarity - Episode benzerlik hesaplayici.
UEM v2 - Pattern clustering ve benzer durum bulma icin.

Benzerlik metrikleri:
- Text similarity: Jaccard similarity (kelime seti bazli)
- Intent similarity: Tam eslesme veya kategorik yakinlik
- Emotion similarity: Duygu kategorileri arasi mesafe
- DialogueAct similarity: Act setleri arasi Jaccard

Ozellikler:
- LLM/embedding kullanmaz (hafif ve hizli)
- Konfigure edilebilir agirliklar
- Batch islem destegi
- Threshold bazli filtreleme
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from .episode import Episode


@dataclass
class SimilarityConfig:
    """
    EpisodeSimilarity konfigurasyonu.

    Attributes:
        text_weight: Metin benzerlik agirligi
        intent_weight: Intent benzerlik agirligi
        emotion_weight: Duygu benzerlik agirligi
        dialogue_act_weight: DialogueAct benzerlik agirligi
        similar_threshold: Benzer sayilma esigi
        cluster_threshold: Cluster dahil edilme esigi
        case_sensitive: Buyuk/kucuk harf duyarliligi
        stop_words: Filtrelenecek kelimeler
    """
    text_weight: float = 0.30
    intent_weight: float = 0.25
    emotion_weight: float = 0.20
    dialogue_act_weight: float = 0.25
    similar_threshold: float = 0.80
    cluster_threshold: float = 0.70
    case_sensitive: bool = False
    stop_words: Set[str] = field(default_factory=lambda: {
        "bir", "ve", "de", "da", "mi", "mu", "bu", "su", "o",
        "ben", "sen", "biz", "siz", "ne", "nasil", "neden",
        "the", "a", "an", "is", "are", "was", "were", "be",
        "have", "has", "do", "does", "did", "will", "would",
        "can", "could", "should", "may", "might", "must",
        "i", "you", "he", "she", "it", "we", "they",
    })

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = (
            self.text_weight +
            self.intent_weight +
            self.emotion_weight +
            self.dialogue_act_weight
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Weights must sum to 1.0, got {total:.3f}"
            )


@dataclass
class SimilarityResult:
    """
    Benzerlik hesaplama sonucu.

    Attributes:
        total_score: Toplam benzerlik skoru [0.0-1.0]
        text_score: Metin benzerlik skoru
        intent_score: Intent benzerlik skoru
        emotion_score: Duygu benzerlik skoru
        dialogue_act_score: DialogueAct benzerlik skoru
        is_similar: similar_threshold'u geciyor mu
        is_cluster_candidate: cluster_threshold'u geciyor mu
    """
    total_score: float
    text_score: float
    intent_score: float
    emotion_score: float
    dialogue_act_score: float
    is_similar: bool
    is_cluster_candidate: bool


class EpisodeSimilarity:
    """
    Episode benzerlik hesaplayici.

    Iki episode arasindaki benzerligi coklu metriklerle hesaplar.
    LLM veya embedding kullanmaz - saf algoritmik yaklasim.

    Kullanim:
        similarity = EpisodeSimilarity()
        score = similarity.compute(episode1, episode2)
        print(f"Benzerlik: {score:.2f}")

        # Batch islem
        candidates = similarity.compute_batch(episode, all_episodes)
        similar = [(e, s) for e, s in candidates if s > 0.8]
    """

    # Intent kategorileri - yakin intent'ler birbirine benzer
    INTENT_CATEGORIES: Dict[str, str] = {
        # Selamlama
        "greet": "social",
        "farewell": "social",
        "thank": "social",
        # Bilgi
        "ask": "information",
        "inform": "information",
        "explain": "information",
        "clarify": "information",
        # Yardim
        "help": "assistance",
        "request": "assistance",
        "suggest": "assistance",
        # Duygu
        "complain": "emotional",
        "express_emotion": "emotional",
        "empathize": "emotional",
        # Iletisim
        "communicate": "general",
        "acknowledge": "general",
    }

    # Duygu kategorileri ve yakınlıkları
    EMOTION_CATEGORIES: Dict[str, str] = {
        # Pozitif
        "happy": "positive",
        "joy": "positive",
        "excited": "positive",
        "grateful": "positive",
        "hopeful": "positive",
        # Negatif
        "sad": "negative",
        "angry": "negative",
        "frustrated": "negative",
        "disappointed": "negative",
        "anxious": "negative",
        "worried": "negative",
        "fearful": "negative",
        # Notr
        "neutral": "neutral",
        "calm": "neutral",
        "curious": "neutral",
    }

    # Duygu kategorileri arasi mesafe (0 = ayni, 1 = tam zit)
    EMOTION_CATEGORY_DISTANCE: Dict[Tuple[str, str], float] = {
        ("positive", "positive"): 0.0,
        ("negative", "negative"): 0.0,
        ("neutral", "neutral"): 0.0,
        ("positive", "neutral"): 0.3,
        ("neutral", "positive"): 0.3,
        ("negative", "neutral"): 0.3,
        ("neutral", "negative"): 0.3,
        ("positive", "negative"): 0.8,
        ("negative", "positive"): 0.8,
    }

    def __init__(self, config: Optional[SimilarityConfig] = None):
        """
        EpisodeSimilarity olustur.

        Args:
            config: Konfigürasyon (opsiyonel)
        """
        self.config = config or SimilarityConfig()

    def compute(self, episode1: Episode, episode2: Episode) -> float:
        """
        Iki episode arasindaki benzerligi hesapla.

        Args:
            episode1: Birinci episode
            episode2: Ikinci episode

        Returns:
            float: Benzerlik skoru [0.0-1.0]
        """
        result = self.compute_detailed(episode1, episode2)
        return result.total_score

    def compute_detailed(
        self,
        episode1: Episode,
        episode2: Episode
    ) -> SimilarityResult:
        """
        Detayli benzerlik hesapla.

        Args:
            episode1: Birinci episode
            episode2: Ikinci episode

        Returns:
            SimilarityResult: Detayli benzerlik sonucu
        """
        # Alt metrikleri hesapla
        text_score = self._text_similarity(
            episode1.user_message,
            episode2.user_message
        )
        intent_score = self._intent_similarity(
            episode1.intent,
            episode2.intent
        )
        emotion_score = self._emotion_similarity(
            episode1.emotion_label,
            episode2.emotion_label
        )
        dialogue_act_score = self._dialogue_act_similarity(
            episode1.dialogue_acts,
            episode2.dialogue_acts
        )

        # Agirlikli toplam
        total_score = (
            text_score * self.config.text_weight +
            intent_score * self.config.intent_weight +
            emotion_score * self.config.emotion_weight +
            dialogue_act_score * self.config.dialogue_act_weight
        )

        return SimilarityResult(
            total_score=total_score,
            text_score=text_score,
            intent_score=intent_score,
            emotion_score=emotion_score,
            dialogue_act_score=dialogue_act_score,
            is_similar=total_score >= self.config.similar_threshold,
            is_cluster_candidate=total_score >= self.config.cluster_threshold
        )

    def compute_batch(
        self,
        episode: Episode,
        candidates: List[Episode],
        min_threshold: Optional[float] = None
    ) -> List[Tuple[Episode, float]]:
        """
        Bir episode'u birden fazla adayla karsilastir.

        Args:
            episode: Karsilastirilacak episode
            candidates: Aday episode'lar
            min_threshold: Minimum skor esigi (opsiyonel)

        Returns:
            List[Tuple[Episode, float]]: (episode, skor) listesi, skorla sirali
        """
        threshold = min_threshold or 0.0
        results = []

        for candidate in candidates:
            # Kendisiyle karsilastirma yapma
            if candidate.id == episode.id:
                continue

            score = self.compute(episode, candidate)
            if score >= threshold:
                results.append((candidate, score))

        # Skora gore sirala (yuksekten dusuge)
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def find_similar(
        self,
        episode: Episode,
        candidates: List[Episode],
        limit: Optional[int] = None
    ) -> List[Tuple[Episode, float]]:
        """
        Benzer episode'lari bul.

        Args:
            episode: Kaynak episode
            candidates: Aday episode'lar
            limit: Maksimum sonuc sayisi

        Returns:
            List[Tuple[Episode, float]]: Benzer episode'lar
        """
        results = self.compute_batch(
            episode,
            candidates,
            min_threshold=self.config.similar_threshold
        )
        if limit:
            return results[:limit]
        return results

    def find_cluster_candidates(
        self,
        episode: Episode,
        candidates: List[Episode]
    ) -> List[Tuple[Episode, float]]:
        """
        Cluster adaylarini bul.

        Args:
            episode: Kaynak episode
            candidates: Aday episode'lar

        Returns:
            List[Tuple[Episode, float]]: Cluster adaylari
        """
        return self.compute_batch(
            episode,
            candidates,
            min_threshold=self.config.cluster_threshold
        )

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Metin benzerligi hesapla (Jaccard similarity).

        Args:
            text1: Birinci metin
            text2: Ikinci metin

        Returns:
            float: Benzerlik skoru [0.0-1.0]
        """
        if not text1 or not text2:
            return 0.0 if (text1 or text2) else 1.0

        # Kelimelere ayir
        words1 = self._tokenize(text1)
        words2 = self._tokenize(text2)

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity: |A ∩ B| / |A ∪ B|
        intersection = words1 & words2
        union = words1 | words2

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _tokenize(self, text: str) -> Set[str]:
        """
        Metni kelimelere ayir ve filtrele.

        Args:
            text: Giris metni

        Returns:
            Set[str]: Kelime seti
        """
        if not self.config.case_sensitive:
            text = text.lower()

        # Basit tokenization - alfanumerik karakterleri tut
        words = set()
        current_word = []

        for char in text:
            if char.isalnum():
                current_word.append(char)
            else:
                if current_word:
                    word = "".join(current_word)
                    if word not in self.config.stop_words:
                        words.add(word)
                    current_word = []

        # Son kelimeyi ekle
        if current_word:
            word = "".join(current_word)
            if word not in self.config.stop_words:
                words.add(word)

        return words

    def _intent_similarity(self, intent1: str, intent2: str) -> float:
        """
        Intent benzerligi hesapla.

        Args:
            intent1: Birinci intent
            intent2: Ikinci intent

        Returns:
            float: Benzerlik skoru [0.0-1.0]
        """
        if not intent1 or not intent2:
            return 0.0 if (intent1 or intent2) else 1.0

        # Tam eslesme
        if intent1 == intent2:
            return 1.0

        # Normalize et
        intent1_lower = intent1.lower()
        intent2_lower = intent2.lower()

        if intent1_lower == intent2_lower:
            return 1.0

        # Kategori bazli eslesme
        cat1 = self.INTENT_CATEGORIES.get(intent1_lower, "unknown")
        cat2 = self.INTENT_CATEGORIES.get(intent2_lower, "unknown")

        if cat1 == cat2 and cat1 != "unknown":
            return 0.7  # Ayni kategoride

        return 0.0  # Farkli kategoriler

    def _emotion_similarity(self, emotion1: str, emotion2: str) -> float:
        """
        Duygu benzerligi hesapla.

        Args:
            emotion1: Birinci duygu
            emotion2: Ikinci duygu

        Returns:
            float: Benzerlik skoru [0.0-1.0]
        """
        if not emotion1 or not emotion2:
            return 0.0 if (emotion1 or emotion2) else 1.0

        # Normalize et
        emo1_lower = emotion1.lower()
        emo2_lower = emotion2.lower()

        # Tam eslesme
        if emo1_lower == emo2_lower:
            return 1.0

        # Kategori al
        cat1 = self.EMOTION_CATEGORIES.get(emo1_lower, "neutral")
        cat2 = self.EMOTION_CATEGORIES.get(emo2_lower, "neutral")

        # Mesafe al
        distance = self.EMOTION_CATEGORY_DISTANCE.get(
            (cat1, cat2),
            0.5  # Bilinmeyen kombinasyon
        )

        # Mesafeyi benzerllige cevir
        return 1.0 - distance

    def _dialogue_act_similarity(
        self,
        acts1: List[str],
        acts2: List[str]
    ) -> float:
        """
        DialogueAct benzerligi hesapla (Jaccard similarity).

        Args:
            acts1: Birinci act listesi
            acts2: Ikinci act listesi

        Returns:
            float: Benzerlik skoru [0.0-1.0]
        """
        if not acts1 or not acts2:
            return 0.0 if (acts1 or acts2) else 1.0

        # Set'e cevir
        set1 = set(act.lower() for act in acts1)
        set2 = set(act.lower() for act in acts2)

        # Jaccard similarity
        intersection = set1 & set2
        union = set1 | set2

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def get_similarity_breakdown(
        self,
        episode1: Episode,
        episode2: Episode
    ) -> Dict[str, Any]:
        """
        Detayli benzerlik raporu.

        Args:
            episode1: Birinci episode
            episode2: Ikinci episode

        Returns:
            Dict[str, Any]: Detayli rapor
        """
        result = self.compute_detailed(episode1, episode2)

        return {
            "total_score": result.total_score,
            "is_similar": result.is_similar,
            "is_cluster_candidate": result.is_cluster_candidate,
            "components": {
                "text": {
                    "score": result.text_score,
                    "weight": self.config.text_weight,
                    "weighted": result.text_score * self.config.text_weight,
                },
                "intent": {
                    "score": result.intent_score,
                    "weight": self.config.intent_weight,
                    "weighted": result.intent_score * self.config.intent_weight,
                    "values": (episode1.intent, episode2.intent),
                },
                "emotion": {
                    "score": result.emotion_score,
                    "weight": self.config.emotion_weight,
                    "weighted": result.emotion_score * self.config.emotion_weight,
                    "values": (episode1.emotion_label, episode2.emotion_label),
                },
                "dialogue_acts": {
                    "score": result.dialogue_act_score,
                    "weight": self.config.dialogue_act_weight,
                    "weighted": result.dialogue_act_score * self.config.dialogue_act_weight,
                    "values": (episode1.dialogue_acts, episode2.dialogue_acts),
                },
            },
            "thresholds": {
                "similar_threshold": self.config.similar_threshold,
                "cluster_threshold": self.config.cluster_threshold,
            },
        }


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Jaccard similarity hesapla.

    Args:
        set1: Birinci set
        set2: Ikinci set

    Returns:
        float: Benzerlik skoru [0.0-1.0]
    """
    if not set1 or not set2:
        return 0.0 if (set1 or set2) else 1.0

    intersection = set1 & set2
    union = set1 | set2

    return len(intersection) / len(union) if union else 0.0


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Levenshtein (edit) mesafesi hesapla.

    Args:
        s1: Birinci string
        s2: Ikinci string

    Returns:
        int: Edit mesafesi
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)

    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Normalize Levenshtein benzerligi hesapla.

    Args:
        s1: Birinci string
        s2: Ikinci string

    Returns:
        float: Benzerlik skoru [0.0-1.0]
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0

    distance = levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)
