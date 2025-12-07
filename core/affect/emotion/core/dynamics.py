"""
UEM v2 - Emotion Dynamics

Duyguların zamanla nasıl değiştiği:
- Decay: Doğal sönümlenme
- Trigger: Olay bazlı tetikleme
- Regulation: Bilinçli düzenleme
- Contagion: Sosyal bulaşma
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import math
import time

from .pad import PADState, pad_from_stimulus, pad_from_appraisal
from .emotions import BasicEmotion, get_emotion_pad, identify_emotion


class DecayModel(str, Enum):
    """Duygu sönümlenme modelleri."""
    LINEAR = "linear"           # Sabit hızda azalma
    EXPONENTIAL = "exponential" # Üstel azalma
    LOGARITHMIC = "logarithmic" # Başta hızlı, sonra yavaş


class RegulationStrategy(str, Enum):
    """Duygu düzenleme stratejileri (Gross, 2015)."""
    REAPPRAISAL = "reappraisal"       # Durumu yeniden değerlendir
    SUPPRESSION = "suppression"        # Duyguyu bastır
    DISTRACTION = "distraction"        # Dikkat dağıt
    ACCEPTANCE = "acceptance"          # Olduğu gibi kabul et
    RUMINATION = "rumination"          # Üzerinde düşün (olumsuz)


@dataclass
class EmotionConfig:
    """Duygu dinamiği yapılandırması."""
    
    # Decay parametreleri
    decay_model: DecayModel = DecayModel.EXPONENTIAL
    decay_rate: float = 0.05          # Sönümlenme hızı (0-1)
    baseline_return_time: float = 60.0  # Nötre dönüş süresi (saniye)
    
    # Trigger parametreleri
    trigger_threshold: float = 0.3     # Minimum tetikleme şiddeti
    blend_new_weight: float = 0.6      # Yeni duygunun karışım ağırlığı
    
    # Yoğunluk limitleri
    max_intensity: float = 1.0
    min_intensity: float = 0.0
    
    # Momentum (ani değişimlere direnç)
    momentum: float = 0.3              # 0=anında değişim, 1=hiç değişmez


@dataclass
class EmotionState:
    """
    Dinamik duygu durumu.
    
    PADState'i saran, zamansal dinamikleri yöneten sınıf.
    """
    current: PADState = field(default_factory=PADState.neutral)
    baseline: PADState = field(default_factory=PADState.neutral)
    config: EmotionConfig = field(default_factory=EmotionConfig)
    
    # Zamansal takip
    last_update: float = field(default_factory=time.time)
    last_trigger: Optional[float] = None
    
    # Geçmiş (analiz için)
    history: List[PADState] = field(default_factory=list)
    max_history: int = 100
    
    def update(self, delta_time: float = None) -> PADState:
        """
        Zamanı ilerlet, decay uygula.
        
        Args:
            delta_time: Geçen süre (saniye). None ise otomatik hesapla.
            
        Returns:
            Güncel PAD durumu
        """
        now = time.time()
        if delta_time is None:
            delta_time = now - self.last_update
        
        # Decay uygula
        if delta_time > 0:
            self.current = self._apply_decay(delta_time)
        
        self.last_update = now
        self._record_history()
        
        return self.current
    
    def _apply_decay(self, delta_time: float) -> PADState:
        """Decay modelini uygula."""
        
        # Decay faktörü hesapla
        if self.config.decay_model == DecayModel.LINEAR:
            factor = self.config.decay_rate * delta_time
        
        elif self.config.decay_model == DecayModel.EXPONENTIAL:
            # e^(-rate * time)
            factor = 1 - math.exp(-self.config.decay_rate * delta_time)
        
        elif self.config.decay_model == DecayModel.LOGARITHMIC:
            # log(1 + rate * time)
            factor = math.log(1 + self.config.decay_rate * delta_time) / 3
        
        else:
            factor = self.config.decay_rate * delta_time
        
        factor = max(0.0, min(1.0, factor))
        
        # Baseline'a doğru karıştır
        return self.current.blend(self.baseline, factor)
    
    def trigger(
        self,
        stimulus_pad: PADState,
        intensity: float = 1.0,
    ) -> PADState:
        """
        Yeni duyguyu tetikle.
        
        Args:
            stimulus_pad: Tetikleyen PAD durumu
            intensity: Tetikleme şiddeti (0-1)
            
        Returns:
            Güncel PAD durumu
        """
        if intensity < self.config.trigger_threshold:
            return self.current
        
        # Yoğunluğu ayarla
        new_pad = stimulus_pad.amplify(intensity)
        
        # Momentum uygula
        effective_weight = self.config.blend_new_weight * (1 - self.config.momentum)
        
        # Karıştır
        self.current = self.current.blend(new_pad, effective_weight)
        self.current.intensity = min(
            self.config.max_intensity,
            self.current.intensity + new_pad.intensity * 0.5
        )
        
        self.last_trigger = time.time()
        self._record_history()
        
        return self.current
    
    def trigger_emotion(
        self,
        emotion: BasicEmotion,
        intensity: float = 0.7,
    ) -> PADState:
        """
        Temel duyguyu tetikle.
        
        Args:
            emotion: Tetiklenecek temel duygu
            intensity: Şiddet (0-1)
        """
        emotion_pad = get_emotion_pad(emotion)
        emotion_pad.intensity = intensity
        return self.trigger(emotion_pad, intensity)
    
    def trigger_from_event(
        self,
        threat_level: float = 0.0,
        reward_level: float = 0.0,
        uncertainty: float = 0.5,
        control: float = 0.5,
    ) -> PADState:
        """
        Olay parametrelerinden duygu tetikle.
        
        Args:
            threat_level: Tehdit (0-1)
            reward_level: Ödül (0-1)
            uncertainty: Belirsizlik (0-1)
            control: Kontrol hissi (0-1)
        """
        stimulus_pad = pad_from_stimulus(
            threat_level=threat_level,
            reward_level=reward_level,
            uncertainty=uncertainty,
            control=control,
        )
        
        # Şiddet = en yüksek faktör
        intensity = max(threat_level, reward_level, uncertainty)
        
        return self.trigger(stimulus_pad, intensity)
    
    def regulate(
        self,
        strategy: RegulationStrategy,
        strength: float = 0.5,
    ) -> PADState:
        """
        Duygu düzenleme stratejisi uygula.
        
        Args:
            strategy: Düzenleme stratejisi
            strength: Uygulama gücü (0-1)
        """
        if strategy == RegulationStrategy.REAPPRAISAL:
            # Durumu yeniden değerlendir - pleasure'ı nötre çek
            target = PADState(
                pleasure=self.current.pleasure * 0.5,
                arousal=self.current.arousal * 0.7,
                dominance=min(1.0, self.current.dominance + 0.2),
            )
            self.current = self.current.blend(target, strength * 0.4)
        
        elif strategy == RegulationStrategy.SUPPRESSION:
            # Duyguyu bastır - yoğunluğu düşür
            self.current.intensity *= (1 - strength * 0.5)
            self.current = self.current.amplify(1 - strength * 0.3)
        
        elif strategy == RegulationStrategy.DISTRACTION:
            # Dikkat dağıt - arousal düşür
            self.current.arousal *= (1 - strength * 0.4)
        
        elif strategy == RegulationStrategy.ACCEPTANCE:
            # Kabul et - dominance artır, arousal düşür
            self.current.dominance = min(1.0, self.current.dominance + strength * 0.2)
            self.current.arousal *= (1 - strength * 0.2)
        
        elif strategy == RegulationStrategy.RUMINATION:
            # Üzerinde düşün (olumsuz) - negatif duyguları güçlendir
            if self.current.pleasure < 0:
                self.current = self.current.amplify(1 + strength * 0.3)
        
        self._record_history()
        return self.current
    
    def social_contagion(
        self,
        other_pad: PADState,
        empathy_level: float = 0.5,
    ) -> PADState:
        """
        Başkasının duygusundan etkilenme.
        
        Args:
            other_pad: Diğer kişinin duygu durumu
            empathy_level: Empati seviyesi (0-1)
            
        Returns:
            Güncel PAD durumu
        """
        # Empati seviyesine göre karıştır
        contagion_weight = empathy_level * 0.4  # Max %40 etkilenme
        
        self.current = self.current.blend(other_pad, contagion_weight)
        
        self._record_history()
        return self.current
    
    def set_baseline(self, baseline: PADState) -> None:
        """Baseline (karakteristik) duygu durumunu ayarla."""
        self.baseline = baseline
    
    def reset_to_baseline(self) -> PADState:
        """Baseline'a dön."""
        self.current = self.baseline.copy()
        self._record_history()
        return self.current
    
    def _record_history(self) -> None:
        """Geçmişe kaydet."""
        self.history.append(self.current.copy())
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_dominant_emotion(self) -> Optional[BasicEmotion]:
        """Şu anki baskın duyguyu bul."""
        return identify_emotion(self.current)
    
    def get_emotional_trajectory(self) -> Dict[str, float]:
        """Son dönemdeki duygu değişim trendini hesapla."""
        if len(self.history) < 2:
            return {"pleasure_trend": 0, "arousal_trend": 0, "dominance_trend": 0}
        
        # Son 10 kayıt
        recent = self.history[-10:]
        
        # Basit lineer trend
        p_trend = recent[-1].pleasure - recent[0].pleasure
        a_trend = recent[-1].arousal - recent[0].arousal
        d_trend = recent[-1].dominance - recent[0].dominance
        
        return {
            "pleasure_trend": p_trend / len(recent),
            "arousal_trend": a_trend / len(recent),
            "dominance_trend": d_trend / len(recent),
        }
    
    @property
    def is_positive(self) -> bool:
        """Duygu pozitif mi?"""
        return self.current.pleasure > 0.1
    
    @property
    def is_negative(self) -> bool:
        """Duygu negatif mi?"""
        return self.current.pleasure < -0.1
    
    @property
    def is_neutral(self) -> bool:
        """Duygu nötr mü?"""
        return -0.1 <= self.current.pleasure <= 0.1
    
    @property
    def is_high_arousal(self) -> bool:
        """Uyarılmışlık yüksek mi?"""
        return self.current.arousal > 0.6
    
    @property
    def is_low_arousal(self) -> bool:
        """Uyarılmışlık düşük mü?"""
        return self.current.arousal < 0.4


def create_personality_baseline(
    extraversion: float = 0.5,
    neuroticism: float = 0.5,
    agreeableness: float = 0.5,
) -> PADState:
    """
    Big Five kişilik özelliklerinden baseline PAD oluştur.
    
    Args:
        extraversion: Dışa dönüklük (0-1)
        neuroticism: Nevrotiklik (0-1)
        agreeableness: Uyumluluk (0-1)
        
    Returns:
        Kişilik bazlı baseline PAD
    """
    # Extraversion → positive pleasure, higher arousal
    # Neuroticism → negative pleasure, higher arousal
    # Agreeableness → positive pleasure, lower dominance
    
    pleasure = 0.3 * (extraversion - 0.5) - 0.4 * (neuroticism - 0.5) + 0.2 * (agreeableness - 0.5)
    arousal = 0.3 + 0.2 * extraversion + 0.2 * neuroticism
    dominance = 0.5 + 0.2 * (extraversion - 0.5) - 0.1 * (agreeableness - 0.5)
    
    return PADState(
        pleasure=pleasure,
        arousal=arousal,
        dominance=dominance,
        intensity=0.3,
        source="personality_baseline",
    )
