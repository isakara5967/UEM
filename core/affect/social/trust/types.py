"""
UEM v2 - Trust Types

Güven türleri ve bileşenleri.

Trust = Geçmiş etkileşimlere dayalı güven değerlendirmesi
    ≠ Empathy (anlama)
    ≠ Sympathy (duygusal tepki)

7 Güven Türü:
1. Blind Trust - Koşulsuz güven (naif)
2. Earned Trust - Kazanılmış güven (en sağlıklı)
3. Cautious Trust - Temkinli güven
4. Neutral - Nötr (bilgi yok)
5. Distrust - Güvensizlik
6. Betrayed Trust - İhanete uğramış
7. Conditional Trust - Koşullu güven

Güven Bileşenleri:
- Competence: Yetkinlik ("İşini yapabilir mi?")
- Benevolence: İyi niyet ("Bana zarar verir mi?")
- Integrity: Dürüstlük ("Sözünde durur mu?")
- Predictability: Öngörülebilirlik ("Davranışı tutarlı mı?")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime


class TrustLevel(str, Enum):
    """Güven seviyeleri."""
    BLIND = "blind"           # 0.9-1.0: Koşulsuz güven
    HIGH = "high"             # 0.7-0.9: Yüksek güven
    MODERATE = "moderate"     # 0.5-0.7: Orta güven
    CAUTIOUS = "cautious"     # 0.3-0.5: Temkinli
    LOW = "low"               # 0.1-0.3: Düşük güven
    DISTRUST = "distrust"     # 0.0-0.1: Güvensizlik
    
    @classmethod
    def from_value(cls, value: float) -> "TrustLevel":
        """Değerden seviye belirle."""
        if value >= 0.9:
            return cls.BLIND
        elif value >= 0.7:
            return cls.HIGH
        elif value >= 0.5:
            return cls.MODERATE
        elif value >= 0.3:
            return cls.CAUTIOUS
        elif value >= 0.1:
            return cls.LOW
        else:
            return cls.DISTRUST


class TrustType(str, Enum):
    """Güven türleri - nasıl oluştuğuna göre."""
    BLIND = "blind"               # Sorgulamadan güven
    EARNED = "earned"             # Pozitif deneyimlerle kazanılmış
    CAUTIOUS = "cautious"         # Temkinli başlangıç
    NEUTRAL = "neutral"           # Bilgi yok, nötr
    CONDITIONAL = "conditional"   # Belirli koşullara bağlı
    DISTRUST = "distrust"         # Aktif güvensizlik
    BETRAYED = "betrayed"         # İhanet sonrası kırılmış


class TrustDimension(str, Enum):
    """Güven boyutları (Mayer et al., 1995)."""
    COMPETENCE = "competence"         # Yetkinlik
    BENEVOLENCE = "benevolence"       # İyi niyet
    INTEGRITY = "integrity"           # Dürüstlük
    PREDICTABILITY = "predictability" # Öngörülebilirlik


@dataclass
class TrustComponents:
    """
    Güven bileşenleri - 4 boyutlu model.
    
    Her boyut 0-1 arasında.
    """
    competence: float = 0.5      # Yetkinlik
    benevolence: float = 0.5     # İyi niyet
    integrity: float = 0.5       # Dürüstlük
    predictability: float = 0.5  # Öngörülebilirlik
    
    def __post_init__(self):
        """Değerleri normalize et."""
        self.competence = max(0.0, min(1.0, self.competence))
        self.benevolence = max(0.0, min(1.0, self.benevolence))
        self.integrity = max(0.0, min(1.0, self.integrity))
        self.predictability = max(0.0, min(1.0, self.predictability))
    
    def overall(self, weights: Optional[Dict[TrustDimension, float]] = None) -> float:
        """
        Genel güven skoru hesapla.
        
        Args:
            weights: Boyut ağırlıkları
            
        Returns:
            0-1 arası genel güven
        """
        if weights is None:
            weights = {
                TrustDimension.COMPETENCE: 0.25,
                TrustDimension.BENEVOLENCE: 0.30,
                TrustDimension.INTEGRITY: 0.30,
                TrustDimension.PREDICTABILITY: 0.15,
            }
        
        total = (
            self.competence * weights[TrustDimension.COMPETENCE] +
            self.benevolence * weights[TrustDimension.BENEVOLENCE] +
            self.integrity * weights[TrustDimension.INTEGRITY] +
            self.predictability * weights[TrustDimension.PREDICTABILITY]
        )
        
        return total
    
    def weakest_dimension(self) -> TrustDimension:
        """En zayıf boyutu bul."""
        dims = [
            (TrustDimension.COMPETENCE, self.competence),
            (TrustDimension.BENEVOLENCE, self.benevolence),
            (TrustDimension.INTEGRITY, self.integrity),
            (TrustDimension.PREDICTABILITY, self.predictability),
        ]
        return min(dims, key=lambda x: x[1])[0]
    
    def strongest_dimension(self) -> TrustDimension:
        """En güçlü boyutu bul."""
        dims = [
            (TrustDimension.COMPETENCE, self.competence),
            (TrustDimension.BENEVOLENCE, self.benevolence),
            (TrustDimension.INTEGRITY, self.integrity),
            (TrustDimension.PREDICTABILITY, self.predictability),
        ]
        return max(dims, key=lambda x: x[1])[0]
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "competence": self.competence,
            "benevolence": self.benevolence,
            "integrity": self.integrity,
            "predictability": self.predictability,
            "overall": self.overall(),
        }
    
    def copy(self) -> "TrustComponents":
        return TrustComponents(
            competence=self.competence,
            benevolence=self.benevolence,
            integrity=self.integrity,
            predictability=self.predictability,
        )
    
    @classmethod
    def default(cls) -> "TrustComponents":
        """Varsayılan (nötr) bileşenler."""
        return cls(0.5, 0.5, 0.5, 0.5)
    
    @classmethod
    def high(cls) -> "TrustComponents":
        """Yüksek güven bileşenleri."""
        return cls(0.8, 0.8, 0.8, 0.8)
    
    @classmethod
    def low(cls) -> "TrustComponents":
        """Düşük güven bileşenleri."""
        return cls(0.2, 0.2, 0.2, 0.2)


@dataclass
class TrustEvent:
    """
    Güveni etkileyen olay.
    """
    event_type: str              # "promise_kept", "betrayal", "help", etc.
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Etki
    dimension: TrustDimension = TrustDimension.INTEGRITY
    impact: float = 0.0          # -1 to +1
    
    # Bağlam
    context: str = ""
    importance: float = 0.5      # 0-1, olayın önemi
    
    def weighted_impact(self) -> float:
        """Önem ağırlıklı etki."""
        return self.impact * self.importance


# ═══════════════════════════════════════════════════════════════════════════
# OLAY TİPLERİ VE ETKİLERİ
# ═══════════════════════════════════════════════════════════════════════════

TRUST_EVENT_IMPACTS: Dict[str, Tuple[TrustDimension, float, float]] = {
    # (dimension, base_impact, importance)
    
    # Pozitif olaylar
    "promise_kept": (TrustDimension.INTEGRITY, 0.15, 0.7),
    "helped_me": (TrustDimension.BENEVOLENCE, 0.20, 0.8),
    "competent_action": (TrustDimension.COMPETENCE, 0.15, 0.6),
    "consistent_behavior": (TrustDimension.PREDICTABILITY, 0.10, 0.5),
    "honest_feedback": (TrustDimension.INTEGRITY, 0.12, 0.6),
    "defended_me": (TrustDimension.BENEVOLENCE, 0.25, 0.9),
    "shared_secret_kept": (TrustDimension.INTEGRITY, 0.20, 0.8),
    
    # Negatif olaylar
    "promise_broken": (TrustDimension.INTEGRITY, -0.25, 0.8),
    "betrayal": (TrustDimension.BENEVOLENCE, -0.50, 1.0),
    "incompetent_action": (TrustDimension.COMPETENCE, -0.15, 0.6),
    "unpredictable_behavior": (TrustDimension.PREDICTABILITY, -0.12, 0.5),
    "lied_to_me": (TrustDimension.INTEGRITY, -0.30, 0.9),
    "harmed_me": (TrustDimension.BENEVOLENCE, -0.40, 1.0),
    "shared_my_secret": (TrustDimension.INTEGRITY, -0.35, 0.9),
    "abandoned_me": (TrustDimension.BENEVOLENCE, -0.35, 0.9),
}


def create_trust_event(event_type: str, context: str = "") -> TrustEvent:
    """Olay tipinden TrustEvent oluştur."""
    if event_type in TRUST_EVENT_IMPACTS:
        dim, impact, importance = TRUST_EVENT_IMPACTS[event_type]
        return TrustEvent(
            event_type=event_type,
            dimension=dim,
            impact=impact,
            importance=importance,
            context=context,
        )
    
    # Bilinmeyen olay
    return TrustEvent(
        event_type=event_type,
        dimension=TrustDimension.INTEGRITY,
        impact=0.0,
        importance=0.3,
        context=context,
    )


# ═══════════════════════════════════════════════════════════════════════════
# GÜVEN TİPİ BELİRLEME
# ═══════════════════════════════════════════════════════════════════════════

def determine_trust_type(
    components: TrustComponents,
    history_length: int = 0,
    had_betrayal: bool = False,
) -> TrustType:
    """
    Güven bileşenlerinden güven tipini belirle.
    
    Args:
        components: Güven bileşenleri
        history_length: Etkileşim geçmişi uzunluğu
        had_betrayal: İhanet yaşandı mı
        
    Returns:
        TrustType
    """
    overall = components.overall()
    
    # İhanet varsa
    if had_betrayal:
        if overall < 0.3:
            return TrustType.BETRAYED
        else:
            return TrustType.CAUTIOUS
    
    # Geçmiş yoksa
    if history_length == 0:
        return TrustType.NEUTRAL
    
    # Geçmiş az ise
    if history_length < 3:
        if overall > 0.7:
            return TrustType.BLIND  # Çok hızlı güvenmiş
        else:
            return TrustType.CAUTIOUS
    
    # Normal değerlendirme
    if overall >= 0.8:
        return TrustType.EARNED
    elif overall >= 0.5:
        return TrustType.CONDITIONAL
    elif overall >= 0.3:
        return TrustType.CAUTIOUS
    else:
        return TrustType.DISTRUST
