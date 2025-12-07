"""
UEM v2 - Sympathy Types

Sempati türleri ve duygusal tepkiler.

Sympathy = Empati sonrası KENDİ duygusal tepkim
    ≠ Empathy (anlama)
    ≠ Compassion (yardım motivasyonu - sympathy'nin alt türü)

8 Temel Sempati Türü:
1. Compassion - Acı çekene yardım etme isteği
2. Pity - Üzüntü + üstünlük hissi  
3. Empathic Joy - Başkasının sevincinden sevinme
4. Gratitude - Minnet
5. Schadenfreude - Başkasının talihsizliğinden zevk (negatif)
6. Envy - Kıskançlık (negatif)
7. Empathic Anger - Başkası adına öfke
8. Empathic Sadness - Başkası adına üzüntü
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

import sys
sys.path.insert(0, '.')
from core.affect.emotion.core import PADState, BasicEmotion


class SympathyType(str, Enum):
    """Sempati türleri."""
    
    # Pozitif / Prososyal
    COMPASSION = "compassion"           # Acı çekene yardım isteği
    EMPATHIC_JOY = "empathic_joy"       # Başkasının sevincinden sevinme
    GRATITUDE = "gratitude"             # Minnet
    EMPATHIC_SADNESS = "empathic_sadness"  # Başkası adına üzüntü
    EMPATHIC_ANGER = "empathic_anger"   # Başkası adına öfke (haksızlığa)
    
    # Negatif / Antisosyal
    PITY = "pity"                       # Üzüntü + üstünlük
    SCHADENFREUDE = "schadenfreude"     # Başkasının talihsizliğinden zevk
    ENVY = "envy"                       # Kıskançlık
    
    @classmethod
    def prosocial(cls) -> List["SympathyType"]:
        """Prososyal (olumlu) sempati türleri."""
        return [
            cls.COMPASSION,
            cls.EMPATHIC_JOY,
            cls.GRATITUDE,
            cls.EMPATHIC_SADNESS,
            cls.EMPATHIC_ANGER,
        ]
    
    @classmethod
    def antisocial(cls) -> List["SympathyType"]:
        """Antisosyal (olumsuz) sempati türleri."""
        return [cls.PITY, cls.SCHADENFREUDE, cls.ENVY]


@dataclass
class SympathyResponse:
    """
    Tek bir sempati tepkisi.
    """
    sympathy_type: SympathyType
    intensity: float              # 0-1
    pad_effect: PADState         # Bu sempati bende yarattığı PAD değişimi
    
    # Davranışsal eğilim
    action_tendency: str = ""     # "help", "avoid", "celebrate", "withdraw"
    
    # Metadata
    triggered_by: Optional[str] = None  # Hangi empati sonucundan
    
    def __repr__(self) -> str:
        return f"{self.sympathy_type.value}: {self.intensity:.2f}"
    
    @property
    def is_prosocial(self) -> bool:
        return self.sympathy_type in SympathyType.prosocial()
    
    @property
    def is_antisocial(self) -> bool:
        return self.sympathy_type in SympathyType.antisocial()


# ═══════════════════════════════════════════════════════════════════════════
# SEMPATI TÜRÜ → PAD ETKİSİ HARİTASI
# ═══════════════════════════════════════════════════════════════════════════

SYMPATHY_PAD_EFFECTS: Dict[SympathyType, PADState] = {
    # Compassion: Hafif üzüntü + kontrol (yardım edebilirim)
    SympathyType.COMPASSION: PADState(
        pleasure=-0.2,
        arousal=0.5,
        dominance=0.6,
    ),
    
    # Empathic Joy: Sevinç + düşük arousal
    SympathyType.EMPATHIC_JOY: PADState(
        pleasure=0.7,
        arousal=0.6,
        dominance=0.5,
    ),
    
    # Gratitude: Pozitif + düşük dominance (borçluluk)
    SympathyType.GRATITUDE: PADState(
        pleasure=0.6,
        arousal=0.4,
        dominance=0.35,
    ),
    
    # Empathic Sadness: Üzüntü
    SympathyType.EMPATHIC_SADNESS: PADState(
        pleasure=-0.5,
        arousal=0.35,
        dominance=0.3,
    ),
    
    # Empathic Anger: Öfke (haksızlığa karşı)
    SympathyType.EMPATHIC_ANGER: PADState(
        pleasure=-0.4,
        arousal=0.75,
        dominance=0.7,
    ),
    
    # Pity: Üzüntü + yüksek dominance (üstünlük)
    SympathyType.PITY: PADState(
        pleasure=-0.3,
        arousal=0.3,
        dominance=0.7,
    ),
    
    # Schadenfreude: Zevk + düşük dominance (gizli)
    SympathyType.SCHADENFREUDE: PADState(
        pleasure=0.4,
        arousal=0.5,
        dominance=0.4,
    ),
    
    # Envy: Negatif + yüksek arousal
    SympathyType.ENVY: PADState(
        pleasure=-0.5,
        arousal=0.65,
        dominance=0.3,
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# SEMPATI TÜRÜ → DAVRANIŞ EĞİLİMİ
# ═══════════════════════════════════════════════════════════════════════════

SYMPATHY_ACTION_TENDENCIES: Dict[SympathyType, str] = {
    SympathyType.COMPASSION: "help",
    SympathyType.EMPATHIC_JOY: "celebrate",
    SympathyType.GRATITUDE: "reciprocate",
    SympathyType.EMPATHIC_SADNESS: "comfort",
    SympathyType.EMPATHIC_ANGER: "defend",
    SympathyType.PITY: "help_condescending",
    SympathyType.SCHADENFREUDE: "observe",
    SympathyType.ENVY: "compete",
}


def get_sympathy_pad(sympathy_type: SympathyType) -> PADState:
    """Sempati türünün PAD etkisini getir."""
    return SYMPATHY_PAD_EFFECTS.get(sympathy_type, PADState.neutral())


def get_action_tendency(sympathy_type: SympathyType) -> str:
    """Sempati türünün davranış eğilimini getir."""
    return SYMPATHY_ACTION_TENDENCIES.get(sympathy_type, "observe")


# ═══════════════════════════════════════════════════════════════════════════
# TRİGGER KOŞULLARI
# Her sempati türü hangi koşullarda tetiklenir?
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SympathyTrigger:
    """Sempati tetikleme koşulu."""
    sympathy_type: SympathyType
    
    # Hedefin durumu
    target_valence_range: Tuple[float, float] = (-1.0, 1.0)
    target_arousal_range: Tuple[float, float] = (0.0, 1.0)
    
    # İlişki gereksinimleri
    requires_positive_relationship: bool = False
    requires_negative_relationship: bool = False
    
    # Bağlam
    requires_injustice: bool = False  # Haksızlık algısı
    requires_deservedness: bool = False  # Hak etme algısı
    
    def matches(
        self,
        target_pad: PADState,
        relationship_valence: float,  # -1 to 1
        perceived_injustice: float = 0.0,
        perceived_deservedness: float = 0.5,
    ) -> float:
        """
        Koşulların ne kadar uyduğunu hesapla.
        
        Returns:
            0-1 arası uyum skoru
        """
        score = 0.0
        checks = 0
        
        # Valence kontrolü
        if self.target_valence_range[0] <= target_pad.pleasure <= self.target_valence_range[1]:
            score += 1.0
        checks += 1
        
        # Arousal kontrolü
        if self.target_arousal_range[0] <= target_pad.arousal <= self.target_arousal_range[1]:
            score += 1.0
        checks += 1
        
        # İlişki kontrolü
        if self.requires_positive_relationship:
            if relationship_valence > 0:
                score += 1.0
            checks += 1
        elif self.requires_negative_relationship:
            if relationship_valence < 0:
                score += 1.0
            checks += 1
        
        # Haksızlık kontrolü
        if self.requires_injustice:
            score += perceived_injustice
            checks += 1
        
        # Hak etme kontrolü
        if self.requires_deservedness:
            score += perceived_deservedness
            checks += 1
        
        return score / checks if checks > 0 else 0.0


# Tetikleme kuralları
SYMPATHY_TRIGGERS: Dict[SympathyType, SympathyTrigger] = {
    SympathyType.COMPASSION: SympathyTrigger(
        sympathy_type=SympathyType.COMPASSION,
        target_valence_range=(-1.0, -0.2),  # Hedef mutsuz
        requires_positive_relationship=True,
    ),
    
    SympathyType.EMPATHIC_JOY: SympathyTrigger(
        sympathy_type=SympathyType.EMPATHIC_JOY,
        target_valence_range=(0.2, 1.0),  # Hedef mutlu
        requires_positive_relationship=True,
    ),
    
    SympathyType.GRATITUDE: SympathyTrigger(
        sympathy_type=SympathyType.GRATITUDE,
        target_valence_range=(0.0, 1.0),  # Hedef bana yardım etti
        requires_positive_relationship=True,
    ),
    
    SympathyType.EMPATHIC_SADNESS: SympathyTrigger(
        sympathy_type=SympathyType.EMPATHIC_SADNESS,
        target_valence_range=(-1.0, -0.3),  # Hedef çok üzgün
        target_arousal_range=(0.0, 0.5),  # Düşük arousal
    ),
    
    SympathyType.EMPATHIC_ANGER: SympathyTrigger(
        sympathy_type=SympathyType.EMPATHIC_ANGER,
        target_valence_range=(-1.0, -0.2),  # Hedef mutsuz
        requires_injustice=True,  # Haksızlık var
    ),
    
    SympathyType.PITY: SympathyTrigger(
        sympathy_type=SympathyType.PITY,
        target_valence_range=(-1.0, -0.2),
        requires_deservedness=True,  # "Kendi suçu"
    ),
    
    SympathyType.SCHADENFREUDE: SympathyTrigger(
        sympathy_type=SympathyType.SCHADENFREUDE,
        target_valence_range=(-1.0, -0.2),  # Hedef mutsuz
        requires_negative_relationship=True,  # Düşman/rakip
        requires_deservedness=True,  # Hak etti
    ),
    
    SympathyType.ENVY: SympathyTrigger(
        sympathy_type=SympathyType.ENVY,
        target_valence_range=(0.3, 1.0),  # Hedef çok mutlu/başarılı
        target_arousal_range=(0.5, 1.0),
    ),
}


def get_trigger(sympathy_type: SympathyType) -> SympathyTrigger:
    """Sempati türünün tetikleme koşulunu getir."""
    return SYMPATHY_TRIGGERS.get(
        sympathy_type, 
        SympathyTrigger(sympathy_type=sympathy_type)
    )
