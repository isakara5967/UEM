"""
UEM v2 - Emotion Core Module

PAD modeli, temel duygular ve duygu dinamikleri.

Kullanım:
    from core.affect.emotion.core import (
        PADState,
        EmotionState,
        BasicEmotion,
        get_emotion_pad,
    )
    
    # Doğrudan PAD oluştur
    pad = PADState(pleasure=0.5, arousal=0.7, dominance=0.6)
    
    # Temel duygudan PAD al
    joy_pad = get_emotion_pad(BasicEmotion.JOY)
    
    # Dinamik duygu yönetimi
    emotion = EmotionState()
    emotion.trigger_emotion(BasicEmotion.FEAR, intensity=0.8)
    emotion.update(delta_time=1.0)  # 1 saniye sonra decay
"""

from .pad import (
    PADState,
    PADOctant,
    get_octant,
    pad_from_appraisal,
    pad_from_stimulus,
)

from .emotions import (
    BasicEmotion,
    SecondaryEmotion,
    EmotionProfile,
    BASIC_EMOTION_PAD,
    get_emotion_pad,
    get_secondary_emotion_pad,
    identify_emotion,
    identify_all_emotions,
    create_emotion_profile,
    blend_emotions,
    get_emotion_family,
)

from .dynamics import (
    DecayModel,
    RegulationStrategy,
    EmotionConfig,
    EmotionState,
    create_personality_baseline,
)

__all__ = [
    # PAD
    "PADState",
    "PADOctant",
    "get_octant",
    "pad_from_appraisal",
    "pad_from_stimulus",
    
    # Emotions
    "BasicEmotion",
    "SecondaryEmotion",
    "EmotionProfile",
    "BASIC_EMOTION_PAD",
    "get_emotion_pad",
    "get_secondary_emotion_pad",
    "identify_emotion",
    "identify_all_emotions",
    "create_emotion_profile",
    "blend_emotions",
    "get_emotion_family",
    
    # Dynamics
    "DecayModel",
    "RegulationStrategy",
    "EmotionConfig",
    "EmotionState",
    "create_personality_baseline",
]
