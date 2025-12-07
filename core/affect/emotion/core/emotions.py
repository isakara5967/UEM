"""
UEM v2 - Basic Emotions

Temel duygu tipleri ve PAD uzayındaki konumları.
Ekman, Plutchik ve dimensional modellerin sentezi.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .pad import PADState, PADOctant, get_octant


class BasicEmotion(str, Enum):
    """
    Temel duygular (Ekman + Plutchik bazlı).
    
    8 temel duygu - evrensel ve biyolojik temelli.
    """
    # Ekman's Big 6
    JOY = "joy"
    SADNESS = "sadness"
    FEAR = "fear"
    ANGER = "anger"
    DISGUST = "disgust"
    SURPRISE = "surprise"
    
    # Plutchik additions
    TRUST = "trust"
    ANTICIPATION = "anticipation"


class SecondaryEmotion(str, Enum):
    """
    İkincil duygular - temel duyguların kombinasyonları.
    """
    # Joy combinations
    LOVE = "love"               # joy + trust
    OPTIMISM = "optimism"       # joy + anticipation
    
    # Trust combinations
    ACCEPTANCE = "acceptance"   # trust + joy
    SUBMISSION = "submission"   # trust + fear
    
    # Fear combinations
    AWE = "awe"                 # fear + surprise
    DESPAIR = "despair"        # fear + sadness
    
    # Surprise combinations
    DISAPPROVAL = "disapproval" # surprise + sadness
    
    # Sadness combinations
    REMORSE = "remorse"        # sadness + disgust
    CONTEMPT = "contempt"      # sadness + anger
    
    # Disgust combinations
    SHAME = "shame"            # disgust + fear
    
    # Anger combinations
    AGGRESSIVENESS = "aggressiveness"  # anger + anticipation
    
    # Anticipation combinations
    INTEREST = "interest"      # anticipation + trust


@dataclass
class EmotionProfile:
    """
    Bir duygunun tam profili.
    """
    name: str
    pad: PADState
    basic_emotion: Optional[BasicEmotion] = None
    secondary_emotion: Optional[SecondaryEmotion] = None
    
    # Davranışsal eğilimler
    action_tendency: str = ""  # "approach", "avoid", "attack", "freeze"
    
    # Bilişsel etkiler
    attention_bias: str = ""   # "threat", "reward", "novelty", "none"
    
    def __repr__(self) -> str:
        return f"EmotionProfile({self.name}, {self.pad})"


# ═══════════════════════════════════════════════════════════════════════════
# TEMEL DUYGULARIN PAD KOORDİNATLARI
# ═══════════════════════════════════════════════════════════════════════════
# Araştırma literatüründen derlenmiş ortalama değerler

BASIC_EMOTION_PAD: Dict[BasicEmotion, Tuple[float, float, float]] = {
    # (Pleasure, Arousal, Dominance)
    
    BasicEmotion.JOY:          (+0.76, 0.65, 0.70),  # Mutlu, enerjik, kontrol
    BasicEmotion.SADNESS:      (-0.63, 0.27, 0.25),  # Mutsuz, düşük enerji, güçsüz
    BasicEmotion.FEAR:         (-0.64, 0.82, 0.18),  # Negatif, yüksek enerji, güçsüz
    BasicEmotion.ANGER:        (-0.51, 0.79, 0.75),  # Negatif, yüksek enerji, güçlü
    BasicEmotion.DISGUST:      (-0.60, 0.45, 0.55),  # Negatif, orta enerji, kontrol
    BasicEmotion.SURPRISE:     (+0.14, 0.85, 0.35),  # Nötr, çok yüksek enerji, düşük kontrol
    BasicEmotion.TRUST:        (+0.58, 0.35, 0.45),  # Pozitif, düşük enerji, nötr
    BasicEmotion.ANTICIPATION: (+0.35, 0.70, 0.55),  # Hafif pozitif, yüksek enerji
}


SECONDARY_EMOTION_PAD: Dict[SecondaryEmotion, Tuple[float, float, float]] = {
    SecondaryEmotion.LOVE:          (+0.82, 0.55, 0.60),
    SecondaryEmotion.OPTIMISM:      (+0.65, 0.60, 0.65),
    SecondaryEmotion.ACCEPTANCE:    (+0.55, 0.30, 0.50),
    SecondaryEmotion.SUBMISSION:    (-0.10, 0.45, 0.20),
    SecondaryEmotion.AWE:           (+0.10, 0.80, 0.25),
    SecondaryEmotion.DESPAIR:       (-0.75, 0.55, 0.15),
    SecondaryEmotion.DISAPPROVAL:   (-0.35, 0.50, 0.55),
    SecondaryEmotion.REMORSE:       (-0.55, 0.40, 0.30),
    SecondaryEmotion.CONTEMPT:      (-0.45, 0.35, 0.70),
    SecondaryEmotion.SHAME:         (-0.70, 0.50, 0.15),
    SecondaryEmotion.AGGRESSIVENESS:(-0.40, 0.85, 0.80),
    SecondaryEmotion.INTEREST:      (+0.45, 0.55, 0.50),
}


# Action tendencies
EMOTION_ACTION_TENDENCIES: Dict[BasicEmotion, str] = {
    BasicEmotion.JOY: "approach",
    BasicEmotion.SADNESS: "withdraw",
    BasicEmotion.FEAR: "avoid",
    BasicEmotion.ANGER: "attack",
    BasicEmotion.DISGUST: "reject",
    BasicEmotion.SURPRISE: "orient",
    BasicEmotion.TRUST: "approach",
    BasicEmotion.ANTICIPATION: "approach",
}


# Attention biases
EMOTION_ATTENTION_BIAS: Dict[BasicEmotion, str] = {
    BasicEmotion.JOY: "reward",
    BasicEmotion.SADNESS: "loss",
    BasicEmotion.FEAR: "threat",
    BasicEmotion.ANGER: "obstacle",
    BasicEmotion.DISGUST: "contamination",
    BasicEmotion.SURPRISE: "novelty",
    BasicEmotion.TRUST: "safety",
    BasicEmotion.ANTICIPATION: "opportunity",
}


def get_emotion_pad(emotion: BasicEmotion) -> PADState:
    """Temel duygunun PAD koordinatlarını döndür."""
    pad_tuple = BASIC_EMOTION_PAD.get(emotion, (0.0, 0.5, 0.5))
    return PADState(
        pleasure=pad_tuple[0],
        arousal=pad_tuple[1],
        dominance=pad_tuple[2],
        source=emotion.value,
    )


def get_secondary_emotion_pad(emotion: SecondaryEmotion) -> PADState:
    """İkincil duygunun PAD koordinatlarını döndür."""
    pad_tuple = SECONDARY_EMOTION_PAD.get(emotion, (0.0, 0.5, 0.5))
    return PADState(
        pleasure=pad_tuple[0],
        arousal=pad_tuple[1],
        dominance=pad_tuple[2],
        source=emotion.value,
    )


def identify_emotion(pad: PADState, threshold: float = 0.5) -> Optional[BasicEmotion]:
    """
    PAD durumuna en yakın temel duyguyu bul.
    
    Args:
        pad: Mevcut PAD durumu
        threshold: Maksimum mesafe eşiği
        
    Returns:
        En yakın temel duygu veya None
    """
    min_distance = float('inf')
    closest_emotion = None
    
    for emotion, pad_tuple in BASIC_EMOTION_PAD.items():
        emotion_pad = PADState.from_tuple(pad_tuple)
        distance = pad.distance(emotion_pad)
        
        if distance < min_distance:
            min_distance = distance
            closest_emotion = emotion
    
    if min_distance <= threshold:
        return closest_emotion
    return None


def identify_all_emotions(
    pad: PADState, 
    max_results: int = 3,
    threshold: float = 0.8,
) -> List[Tuple[BasicEmotion, float]]:
    """
    PAD durumuna yakın tüm duyguları bul (sıralı).
    
    Args:
        pad: Mevcut PAD durumu
        max_results: Maksimum sonuç sayısı
        threshold: Maksimum mesafe eşiği
        
    Returns:
        [(emotion, distance), ...] listesi
    """
    distances = []
    
    for emotion, pad_tuple in BASIC_EMOTION_PAD.items():
        emotion_pad = PADState.from_tuple(pad_tuple)
        distance = pad.distance(emotion_pad)
        
        if distance <= threshold:
            distances.append((emotion, distance))
    
    # Mesafeye göre sırala
    distances.sort(key=lambda x: x[1])
    
    return distances[:max_results]


def create_emotion_profile(emotion: BasicEmotion) -> EmotionProfile:
    """Temel duygu için tam profil oluştur."""
    pad = get_emotion_pad(emotion)
    
    return EmotionProfile(
        name=emotion.value,
        pad=pad,
        basic_emotion=emotion,
        action_tendency=EMOTION_ACTION_TENDENCIES.get(emotion, "none"),
        attention_bias=EMOTION_ATTENTION_BIAS.get(emotion, "none"),
    )


def blend_emotions(
    emotion1: BasicEmotion,
    emotion2: BasicEmotion,
    weight: float = 0.5,
) -> PADState:
    """
    İki duyguyu karıştır.
    
    Args:
        emotion1: İlk duygu
        emotion2: İkinci duygu
        weight: 0=emotion1, 1=emotion2
        
    Returns:
        Karışık PAD durumu
    """
    pad1 = get_emotion_pad(emotion1)
    pad2 = get_emotion_pad(emotion2)
    
    return pad1.blend(pad2, weight)


# ═══════════════════════════════════════════════════════════════════════════
# DUYGU AİLELERİ - Octant bazlı gruplandırma
# ═══════════════════════════════════════════════════════════════════════════

OCTANT_EMOTIONS: Dict[PADOctant, List[str]] = {
    PADOctant.EXUBERANT: ["joy", "excitement", "elation", "triumph"],
    PADOctant.DEPENDENT: ["surprise", "hope", "curiosity", "amazement"],
    PADOctant.RELAXED: ["calm", "content", "satisfied", "peaceful"],
    PADOctant.DOCILE: ["serene", "tranquil", "accepting", "humble"],
    PADOctant.HOSTILE: ["anger", "rage", "contempt", "resentment"],
    PADOctant.ANXIOUS: ["fear", "anxiety", "worry", "panic"],
    PADOctant.DISDAINFUL: ["disgust", "boredom", "annoyance", "scorn"],
    PADOctant.BORED: ["sadness", "depression", "loneliness", "grief"],
}


def get_emotion_family(pad: PADState) -> List[str]:
    """PAD durumunun ait olduğu duygu ailesini döndür."""
    octant = get_octant(pad)
    return OCTANT_EMOTIONS.get(octant, [])
