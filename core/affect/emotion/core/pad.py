"""
UEM v2 - PAD Model

Pleasure-Arousal-Dominance duygu temsil modeli.
Mehrabian & Russell (1974) bazlı.

PAD Uzayı:
    Pleasure (Valence):  -1 (mutsuz) → +1 (mutlu)
    Arousal:              0 (sakin)  →  1 (heyecanlı)
    Dominance:            0 (güçsüz) →  1 (güçlü/kontrol)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple
from enum import Enum
import math


@dataclass
class PADState:
    """
    PAD duygu durumu.
    
    Tüm duygular bu 3 boyutlu uzayda temsil edilir.
    """
    pleasure: float = 0.0   # -1 to +1 (valence)
    arousal: float = 0.5    # 0 to 1
    dominance: float = 0.5  # 0 to 1
    
    # Metadata
    intensity: float = 0.5  # Genel yoğunluk (0-1)
    timestamp: Optional[float] = None
    source: Optional[str] = None  # Ne tetikledi?
    
    def __post_init__(self):
        """Değerleri normalize et."""
        self.pleasure = max(-1.0, min(1.0, self.pleasure))
        self.arousal = max(0.0, min(1.0, self.arousal))
        self.dominance = max(0.0, min(1.0, self.dominance))
        self.intensity = max(0.0, min(1.0, self.intensity))
    
    @property
    def valence(self) -> float:
        """Pleasure için alias."""
        return self.pleasure
    
    @valence.setter
    def valence(self, value: float):
        self.pleasure = max(-1.0, min(1.0, value))
    
    def distance(self, other: "PADState") -> float:
        """
        İki PAD durumu arasındaki Euclidean mesafe.
        Duygu benzerliği ölçmek için kullanılır.
        """
        # Pleasure'ı 0-1 aralığına normalize et (karşılaştırma için)
        p1 = (self.pleasure + 1) / 2
        p2 = (other.pleasure + 1) / 2
        
        return math.sqrt(
            (p1 - p2) ** 2 +
            (self.arousal - other.arousal) ** 2 +
            (self.dominance - other.dominance) ** 2
        )
    
    def blend(self, other: "PADState", weight: float = 0.5) -> "PADState":
        """
        İki duygu durumunu karıştır.
        
        Args:
            other: Karıştırılacak diğer durum
            weight: 0=self, 1=other, 0.5=eşit
        
        Returns:
            Yeni karışık PADState
        """
        w = max(0.0, min(1.0, weight))
        return PADState(
            pleasure=self.pleasure * (1 - w) + other.pleasure * w,
            arousal=self.arousal * (1 - w) + other.arousal * w,
            dominance=self.dominance * (1 - w) + other.dominance * w,
            intensity=self.intensity * (1 - w) + other.intensity * w,
            source=f"blend({self.source},{other.source})",
        )
    
    def amplify(self, factor: float) -> "PADState":
        """
        Duyguyu güçlendir/zayıflat.
        
        Args:
            factor: >1 güçlendir, <1 zayıflat
        """
        return PADState(
            pleasure=max(-1, min(1, self.pleasure * factor)),
            arousal=max(0, min(1, self.arousal * factor)),
            dominance=self.dominance,  # Dominance genelde sabit
            intensity=max(0, min(1, self.intensity * factor)),
            source=self.source,
        )
    
    def decay(self, rate: float = 0.1) -> "PADState":
        """
        Duygunun zamanla nötr duruma dönmesi.
        
        Args:
            rate: Decay oranı (0-1)
        """
        neutral = PADState(pleasure=0.0, arousal=0.3, dominance=0.5)
        return self.blend(neutral, weight=rate)
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "pleasure": self.pleasure,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "intensity": self.intensity,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "PADState":
        return cls(
            pleasure=data.get("pleasure", 0.0),
            arousal=data.get("arousal", 0.5),
            dominance=data.get("dominance", 0.5),
            intensity=data.get("intensity", 0.5),
        )
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """(P, A, D) tuple döndür."""
        return (self.pleasure, self.arousal, self.dominance)
    
    def copy(self) -> "PADState":
        """Derin kopya oluştur."""
        return PADState(
            pleasure=self.pleasure,
            arousal=self.arousal,
            dominance=self.dominance,
            intensity=self.intensity,
            timestamp=self.timestamp,
            source=self.source,
        )
    
    @classmethod
    def from_tuple(cls, pad: Tuple[float, float, float]) -> "PADState":
        return cls(pleasure=pad[0], arousal=pad[1], dominance=pad[2])
    
    @classmethod
    def neutral(cls) -> "PADState":
        """Nötr duygu durumu."""
        return cls(pleasure=0.0, arousal=0.3, dominance=0.5, intensity=0.3)
    
    def __repr__(self) -> str:
        return f"PAD(P={self.pleasure:+.2f}, A={self.arousal:.2f}, D={self.dominance:.2f})"


class PADOctant(str, Enum):
    """
    PAD uzayının 8 oktantı - temel duygu bölgeleri.
    
    Her oktant bir duygu ailesini temsil eder.
    """
    # +P +A +D: Exuberant (Coşkulu)
    EXUBERANT = "exuberant"      # joy, excitement
    
    # +P +A -D: Dependent (Bağımlı)  
    DEPENDENT = "dependent"      # surprise, hope
    
    # +P -A +D: Relaxed (Rahat)
    RELAXED = "relaxed"          # calm, content
    
    # +P -A -D: Docile (Uysal)
    DOCILE = "docile"            # peaceful, serene
    
    # -P +A +D: Hostile (Düşmanca)
    HOSTILE = "hostile"          # anger, contempt
    
    # -P +A -D: Anxious (Kaygılı)
    ANXIOUS = "anxious"          # fear, anxiety
    
    # -P -A +D: Disdainful (Küçümseyen)
    DISDAINFUL = "disdainful"    # boredom, disgust
    
    # -P -A -D: Bored (Sıkılmış)
    BORED = "bored"              # sadness, depression


def get_octant(pad: PADState) -> PADOctant:
    """
    PAD durumunun hangi oktantta olduğunu bul.
    
    Args:
        pad: PAD durumu
        
    Returns:
        İlgili oktant
    """
    p_pos = pad.pleasure >= 0
    a_high = pad.arousal >= 0.5
    d_high = pad.dominance >= 0.5
    
    if p_pos:
        if a_high:
            return PADOctant.EXUBERANT if d_high else PADOctant.DEPENDENT
        else:
            return PADOctant.RELAXED if d_high else PADOctant.DOCILE
    else:
        if a_high:
            return PADOctant.HOSTILE if d_high else PADOctant.ANXIOUS
        else:
            return PADOctant.DISDAINFUL if d_high else PADOctant.BORED


def pad_from_appraisal(
    goal_relevance: float,      # 0-1: Bu olay benim için ne kadar önemli?
    goal_congruence: float,     # -1 to +1: Hedeflerimle uyumlu mu?
    coping_potential: float,    # 0-1: Başa çıkabilir miyim?
    novelty: float = 0.5,       # 0-1: Ne kadar beklenmedik?
) -> PADState:
    """
    Appraisal teorisinden PAD hesapla.
    
    Scherer's Component Process Model bazlı.
    Olayları değerlendirerek duygu üretir.
    
    Args:
        goal_relevance: Olayın kişisel önemi
        goal_congruence: Hedeflerle uyum (-1=engel, +1=destek)
        coping_potential: Başa çıkma kapasitesi
        novelty: Beklenmediklik derecesi
        
    Returns:
        Hesaplanan PAD durumu
    """
    # Pleasure: Hedef uyumu ve başa çıkma potansiyeli
    pleasure = goal_congruence * (0.6 + 0.4 * coping_potential)
    
    # Arousal: Önem ve yenilik
    arousal = 0.3 + (goal_relevance * 0.4) + (novelty * 0.3)
    
    # Dominance: Başa çıkma potansiyeli
    dominance = 0.2 + (coping_potential * 0.6) + (0.2 if goal_congruence > 0 else 0)
    
    # Intensity: Tüm faktörlerin kombinasyonu
    intensity = goal_relevance * (0.5 + abs(goal_congruence) * 0.5)
    
    return PADState(
        pleasure=pleasure,
        arousal=arousal,
        dominance=dominance,
        intensity=intensity,
        source="appraisal",
    )


def pad_from_stimulus(
    threat_level: float,        # 0-1: Tehdit seviyesi
    reward_level: float,        # 0-1: Ödül/fayda seviyesi
    uncertainty: float = 0.5,   # 0-1: Belirsizlik
    control: float = 0.5,       # 0-1: Kontrol hissi
) -> PADState:
    """
    Stimulus özelliklerinden PAD hesapla.
    
    Daha basit, doğrudan hesaplama.
    
    Args:
        threat_level: Algılanan tehdit
        reward_level: Algılanan ödül/fayda
        uncertainty: Durum belirsizliği
        control: Kontrol edebilme hissi
        
    Returns:
        Hesaplanan PAD durumu
    """
    # Pleasure: Ödül - Tehdit
    pleasure = reward_level - threat_level
    
    # Arousal: Tehdit ve belirsizlik artırır
    arousal = 0.2 + (threat_level * 0.4) + (uncertainty * 0.3) + (reward_level * 0.1)
    
    # Dominance: Kontrol ve düşük tehdit
    dominance = control * (1 - threat_level * 0.5)
    
    # Intensity
    intensity = max(threat_level, reward_level) * (0.5 + uncertainty * 0.5)
    
    return PADState(
        pleasure=pleasure,
        arousal=min(1.0, arousal),
        dominance=dominance,
        intensity=intensity,
        source="stimulus",
    )
