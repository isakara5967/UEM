"""
UEM v2 - Empathy Channels

Empati'nin 4 kanalı:
1. Cognitive: Zihinsel anlama ("Ne düşünüyor?")
2. Affective: Duygusal rezonans ("Ne hissediyor?")
3. Somatic: Bedensel his ("Bedeni ne söylüyor?")
4. Projective: Simülasyon ("Ben olsam ne hissederdim?")

Simulation Theory bazlı - Experience Matching DEĞİL.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum


class EmpathyChannel(str, Enum):
    """Empati kanalları."""
    COGNITIVE = "cognitive"     # Zihinsel perspektif alma
    AFFECTIVE = "affective"     # Duygusal rezonans
    SOMATIC = "somatic"         # Bedensel empati
    PROJECTIVE = "projective"   # Simülasyon bazlı projeksiyon


@dataclass
class ChannelResult:
    """Tek bir kanalın sonucu."""
    channel: EmpathyChannel
    value: float              # 0-1 empati seviyesi
    confidence: float = 0.5   # 0-1 güven
    
    # Detaylar
    inferred_state: Optional[Dict] = None  # Çıkarsanan durum
    cues_used: List[str] = field(default_factory=list)  # Kullanılan ipuçları
    
    def __repr__(self) -> str:
        return f"{self.channel.value}: {self.value:.2f} (conf: {self.confidence:.2f})"


@dataclass
class EmpathyChannels:
    """
    4 kanalın birleşik sonucu.
    """
    cognitive: ChannelResult
    affective: ChannelResult
    somatic: ChannelResult
    projective: ChannelResult
    
    def __post_init__(self):
        """Varsayılan değerler."""
        if self.cognitive is None:
            self.cognitive = ChannelResult(EmpathyChannel.COGNITIVE, 0.0)
        if self.affective is None:
            self.affective = ChannelResult(EmpathyChannel.AFFECTIVE, 0.0)
        if self.somatic is None:
            self.somatic = ChannelResult(EmpathyChannel.SOMATIC, 0.0)
        if self.projective is None:
            self.projective = ChannelResult(EmpathyChannel.PROJECTIVE, 0.0)
    
    def get(self, channel: EmpathyChannel) -> ChannelResult:
        """Kanal sonucunu getir."""
        mapping = {
            EmpathyChannel.COGNITIVE: self.cognitive,
            EmpathyChannel.AFFECTIVE: self.affective,
            EmpathyChannel.SOMATIC: self.somatic,
            EmpathyChannel.PROJECTIVE: self.projective,
        }
        return mapping[channel]
    
    def weighted_average(
        self,
        weights: Optional[Dict[EmpathyChannel, float]] = None,
    ) -> float:
        """
        Ağırlıklı ortalama empati skoru.
        
        Args:
            weights: Kanal ağırlıkları. None ise eşit ağırlık.
            
        Returns:
            0-1 arası toplam empati skoru
        """
        if weights is None:
            weights = {
                EmpathyChannel.COGNITIVE: 0.30,
                EmpathyChannel.AFFECTIVE: 0.35,
                EmpathyChannel.SOMATIC: 0.15,
                EmpathyChannel.PROJECTIVE: 0.20,
            }
        
        total = 0.0
        weight_sum = 0.0
        
        for channel, weight in weights.items():
            result = self.get(channel)
            # Confidence ile ağırlığı modüle et
            effective_weight = weight * result.confidence
            total += result.value * effective_weight
            weight_sum += effective_weight
        
        if weight_sum == 0:
            return 0.0
        
        return total / weight_sum
    
    def to_dict(self) -> Dict[str, float]:
        """Dict formatında döndür."""
        return {
            "cognitive": self.cognitive.value,
            "affective": self.affective.value,
            "somatic": self.somatic.value,
            "projective": self.projective.value,
            "total": self.weighted_average(),
        }
    
    def dominant_channel(self) -> EmpathyChannel:
        """En güçlü kanalı bul."""
        channels = [
            (EmpathyChannel.COGNITIVE, self.cognitive.value),
            (EmpathyChannel.AFFECTIVE, self.affective.value),
            (EmpathyChannel.SOMATIC, self.somatic.value),
            (EmpathyChannel.PROJECTIVE, self.projective.value),
        ]
        return max(channels, key=lambda x: x[1])[0]


# ═══════════════════════════════════════════════════════════════════════════
# CHANNEL WEIGHTS - Bağlama göre farklı ağırlıklar
# ═══════════════════════════════════════════════════════════════════════════

WEIGHTS_DEFAULT = {
    EmpathyChannel.COGNITIVE: 0.30,
    EmpathyChannel.AFFECTIVE: 0.35,
    EmpathyChannel.SOMATIC: 0.15,
    EmpathyChannel.PROJECTIVE: 0.20,
}

WEIGHTS_CLOSE_RELATIONSHIP = {
    # Yakın ilişkilerde affective ve projective daha önemli
    EmpathyChannel.COGNITIVE: 0.20,
    EmpathyChannel.AFFECTIVE: 0.40,
    EmpathyChannel.SOMATIC: 0.15,
    EmpathyChannel.PROJECTIVE: 0.25,
}

WEIGHTS_PROFESSIONAL = {
    # Profesyonel bağlamda cognitive ağırlıklı
    EmpathyChannel.COGNITIVE: 0.45,
    EmpathyChannel.AFFECTIVE: 0.25,
    EmpathyChannel.SOMATIC: 0.10,
    EmpathyChannel.PROJECTIVE: 0.20,
}

WEIGHTS_CRISIS = {
    # Kriz durumunda somatic ve affective öne çıkar
    EmpathyChannel.COGNITIVE: 0.15,
    EmpathyChannel.AFFECTIVE: 0.40,
    EmpathyChannel.SOMATIC: 0.30,
    EmpathyChannel.PROJECTIVE: 0.15,
}


def get_context_weights(context: str) -> Dict[EmpathyChannel, float]:
    """Bağlama uygun ağırlıkları getir."""
    mapping = {
        "default": WEIGHTS_DEFAULT,
        "close": WEIGHTS_CLOSE_RELATIONSHIP,
        "professional": WEIGHTS_PROFESSIONAL,
        "crisis": WEIGHTS_CRISIS,
    }
    return mapping.get(context, WEIGHTS_DEFAULT)
