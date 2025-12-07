"""
UEM v2 - Empathy Simulation

Simulation Theory bazlı empati hesaplaması.

YANLIŞ (Experience Matching):
    "Ben de böyle bir şey yaşadım mı?" → Memory ara
    
DOĞRU (Simulation Theory):
    "Onun yerinde olsam ne hissederdim?" → Simüle et

Goldman, A. I. (2006). Simulating Minds
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

# PAD modelini import et
import sys
sys.path.insert(0, '.')
from core.affect.emotion.core import (
    PADState,
    BasicEmotion,
    get_emotion_pad,
    identify_emotion,
    pad_from_stimulus,
)

from .channels import (
    EmpathyChannel,
    ChannelResult,
    EmpathyChannels,
)


@dataclass
class AgentState:
    """
    Gözlemlenen ajanın durumu.
    
    Empati hesaplaması için gereken bilgiler.
    """
    # Temel bilgiler
    agent_id: str = ""
    
    # Gözlemlenen ipuçları
    facial_expression: Optional[str] = None      # "happy", "sad", "angry"...
    body_posture: Optional[str] = None           # "tense", "relaxed", "slumped"
    vocal_tone: Optional[str] = None             # "calm", "agitated", "trembling"
    behavioral_cues: List[str] = field(default_factory=list)  # ["pacing", "crying"]
    
    # Bağlamsal bilgiler
    situation: Optional[str] = None              # "loss", "success", "conflict"
    relationship_to_self: str = "stranger"       # "stranger", "acquaintance", "friend", "family"
    
    # Doğrudan gözlemlenen veya çıkarsanan PAD
    observed_pad: Optional[PADState] = None
    
    # Geçmiş etkileşimler
    interaction_history: List[Dict] = field(default_factory=list)
    
    def has_emotional_cues(self) -> bool:
        """Duygusal ipucu var mı?"""
        return any([
            self.facial_expression,
            self.body_posture,
            self.vocal_tone,
            self.behavioral_cues,
            self.observed_pad,
        ])


@dataclass
class SimulationConfig:
    """Simülasyon yapılandırması."""
    
    # Kanal etkinliği
    enable_cognitive: bool = True
    enable_affective: bool = True
    enable_somatic: bool = True
    enable_projective: bool = True
    
    # Simülasyon parametreleri
    similarity_boost: float = 0.2     # Benzer durumda empati artışı
    familiarity_boost: float = 0.15   # Tanıdık kişiye empati artışı
    
    # Eşikler
    min_confidence: float = 0.1
    max_projection_bias: float = 0.3  # Projeksiyon bias limiti


class EmpathySimulator:
    """
    Simulation Theory bazlı empati hesaplayıcı.
    
    Usage:
        simulator = EmpathySimulator(my_pad_state)
        result = simulator.simulate(agent_state)
        print(result.channels.weighted_average())
    """
    
    def __init__(
        self,
        self_state: PADState,
        config: Optional[SimulationConfig] = None,
    ):
        """
        Args:
            self_state: Kendi PAD durumum
            config: Simülasyon yapılandırması
        """
        self.self_state = self_state
        self.config = config or SimulationConfig()
    
    def simulate(self, agent: AgentState) -> "EmpathyResult":
        """
        Ajan için empati simülasyonu yap.
        
        Args:
            agent: Gözlemlenen ajanın durumu
            
        Returns:
            EmpathyResult - tüm kanalların sonucu
        """
        channels_results = {}
        
        # 1. Cognitive Channel
        if self.config.enable_cognitive:
            channels_results[EmpathyChannel.COGNITIVE] = self._simulate_cognitive(agent)
        else:
            channels_results[EmpathyChannel.COGNITIVE] = ChannelResult(
                EmpathyChannel.COGNITIVE, 0.0, 0.0
            )
        
        # 2. Affective Channel
        if self.config.enable_affective:
            channels_results[EmpathyChannel.AFFECTIVE] = self._simulate_affective(agent)
        else:
            channels_results[EmpathyChannel.AFFECTIVE] = ChannelResult(
                EmpathyChannel.AFFECTIVE, 0.0, 0.0
            )
        
        # 3. Somatic Channel
        if self.config.enable_somatic:
            channels_results[EmpathyChannel.SOMATIC] = self._simulate_somatic(agent)
        else:
            channels_results[EmpathyChannel.SOMATIC] = ChannelResult(
                EmpathyChannel.SOMATIC, 0.0, 0.0
            )
        
        # 4. Projective Channel
        if self.config.enable_projective:
            channels_results[EmpathyChannel.PROJECTIVE] = self._simulate_projective(agent)
        else:
            channels_results[EmpathyChannel.PROJECTIVE] = ChannelResult(
                EmpathyChannel.PROJECTIVE, 0.0, 0.0
            )
        
        # Kanalları birleştir
        channels = EmpathyChannels(
            cognitive=channels_results[EmpathyChannel.COGNITIVE],
            affective=channels_results[EmpathyChannel.AFFECTIVE],
            somatic=channels_results[EmpathyChannel.SOMATIC],
            projective=channels_results[EmpathyChannel.PROJECTIVE],
        )
        
        # Ajanın PAD'ini tahmin et
        inferred_pad = self._infer_agent_pad(agent, channels)
        
        return EmpathyResult(
            agent_id=agent.agent_id,
            channels=channels,
            inferred_pad=inferred_pad,
            total_empathy=channels.weighted_average(),
        )
    
    def _simulate_cognitive(self, agent: AgentState) -> ChannelResult:
        """
        Cognitive empati: Zihinsel perspektif alma.
        
        "Bu kişi ne düşünüyor olabilir?"
        """
        cues_used = []
        value = 0.0
        confidence = 0.3  # Başlangıç güveni
        inferred = {}
        
        # Durum analizi
        if agent.situation:
            cues_used.append(f"situation:{agent.situation}")
            situation_emotions = self._situation_to_emotion(agent.situation)
            if situation_emotions:
                inferred["likely_emotion"] = situation_emotions[0]
                value += 0.4
                confidence += 0.2
        
        # Yüz ifadesi
        if agent.facial_expression:
            cues_used.append(f"face:{agent.facial_expression}")
            value += 0.3
            confidence += 0.15
            inferred["facial"] = agent.facial_expression
        
        # Ses tonu
        if agent.vocal_tone:
            cues_used.append(f"voice:{agent.vocal_tone}")
            value += 0.2
            confidence += 0.1
        
        # İlişki yakınlığı bonusu
        familiarity = self._relationship_to_familiarity(agent.relationship_to_self)
        value += familiarity * self.config.familiarity_boost
        
        return ChannelResult(
            channel=EmpathyChannel.COGNITIVE,
            value=min(1.0, value),
            confidence=min(1.0, confidence),
            inferred_state=inferred,
            cues_used=cues_used,
        )
    
    def _simulate_affective(self, agent: AgentState) -> ChannelResult:
        """
        Affective empati: Duygusal rezonans.
        
        "Bu kişinin duygusuyla rezonansa giriyorum."
        """
        cues_used = []
        value = 0.0
        confidence = 0.3
        
        # Doğrudan PAD gözlemi varsa
        if agent.observed_pad:
            cues_used.append("direct_pad_observation")
            
            # PAD uzaklığı - yakınsa rezonans yüksek
            distance = self.self_state.distance(agent.observed_pad)
            resonance = 1.0 - min(1.0, distance / 1.5)
            
            value = 0.3 + (resonance * 0.5)
            confidence = 0.7
        
        # Davranışsal ipuçları
        if agent.behavioral_cues:
            for cue in agent.behavioral_cues:
                cues_used.append(f"behavior:{cue}")
                
                # Belirli davranışlar güçlü duygusal sinyal
                if cue in ["crying", "sobbing"]:
                    value += 0.4
                    confidence += 0.2
                elif cue in ["laughing", "smiling"]:
                    value += 0.3
                    confidence += 0.15
                elif cue in ["trembling", "shaking"]:
                    value += 0.35
                    confidence += 0.15
                elif cue in ["pacing", "fidgeting"]:
                    value += 0.2
                    confidence += 0.1
        
        # Yüz ifadesi duygusal rezonans
        if agent.facial_expression:
            cues_used.append(f"face_affect:{agent.facial_expression}")
            value += 0.25
            confidence += 0.15
        
        return ChannelResult(
            channel=EmpathyChannel.AFFECTIVE,
            value=min(1.0, value),
            confidence=min(1.0, confidence),
            cues_used=cues_used,
        )
    
    def _simulate_somatic(self, agent: AgentState) -> ChannelResult:
        """
        Somatic empati: Bedensel his.
        
        "Bedenimde ne hissediyorum bu kişiyi görünce?"
        """
        cues_used = []
        value = 0.0
        confidence = 0.2  # Somatic genelde daha düşük güven
        
        # Beden dili
        if agent.body_posture:
            cues_used.append(f"posture:{agent.body_posture}")
            
            posture_map = {
                "tense": 0.4,
                "slumped": 0.35,
                "defensive": 0.45,
                "open": 0.2,
                "relaxed": 0.15,
                "rigid": 0.4,
            }
            value += posture_map.get(agent.body_posture, 0.2)
            confidence += 0.15
        
        # Yüksek arousal davranışlar
        high_arousal_cues = ["trembling", "shaking", "pacing", "hyperventilating"]
        for cue in agent.behavioral_cues:
            if cue in high_arousal_cues:
                cues_used.append(f"somatic:{cue}")
                value += 0.3
                confidence += 0.1
        
        # Ses tonundan bedensel ipucu
        if agent.vocal_tone in ["trembling", "choked", "breathless"]:
            cues_used.append(f"voice_somatic:{agent.vocal_tone}")
            value += 0.25
            confidence += 0.1
        
        return ChannelResult(
            channel=EmpathyChannel.SOMATIC,
            value=min(1.0, value),
            confidence=min(1.0, confidence),
            cues_used=cues_used,
        )
    
    def _simulate_projective(self, agent: AgentState) -> ChannelResult:
        """
        Projective empati: "Ben olsam" simülasyonu.
        
        "Bu durumda ben olsam ne hissederdim?"
        
        DİKKAT: Projection bias riski var - kendi durumumu yansıtma
        """
        cues_used = []
        value = 0.0
        confidence = 0.4
        inferred = {}
        
        if not agent.situation:
            # Durum bilgisi yoksa projeksiyon zor
            return ChannelResult(
                channel=EmpathyChannel.PROJECTIVE,
                value=0.2,
                confidence=0.2,
                cues_used=["no_situation_info"],
            )
        
        cues_used.append(f"simulating:{agent.situation}")
        
        # Duruma göre PAD simüle et
        simulated_pad = self._simulate_situation_pad(agent.situation)
        
        if simulated_pad:
            inferred["simulated_pad"] = simulated_pad.to_dict()
            
            # Simülasyon başarılı
            value = 0.5 + (simulated_pad.intensity * 0.3)
            confidence = 0.6
            
            # Projection bias kontrolü
            # Kendi durumuma çok yakınsa bias olabilir
            distance_to_self = simulated_pad.distance(self.self_state)
            if distance_to_self < 0.3:
                # Muhtemelen kendimi yansıtıyorum
                bias_penalty = (0.3 - distance_to_self) * self.config.max_projection_bias
                confidence -= bias_penalty
                cues_used.append("projection_bias_detected")
        
        # İlişki yakınlığı simülasyonu kolaylaştırır
        familiarity = self._relationship_to_familiarity(agent.relationship_to_self)
        value += familiarity * 0.15
        confidence += familiarity * 0.1
        
        return ChannelResult(
            channel=EmpathyChannel.PROJECTIVE,
            value=min(1.0, value),
            confidence=min(1.0, max(self.config.min_confidence, confidence)),
            inferred_state=inferred,
            cues_used=cues_used,
        )
    
    def _infer_agent_pad(
        self,
        agent: AgentState,
        channels: EmpathyChannels,
    ) -> PADState:
        """
        Tüm kanallardan ajanın PAD'ini çıkarsa.
        """
        # Doğrudan gözlem varsa onu kullan
        if agent.observed_pad:
            return agent.observed_pad
        
        # Durum bazlı çıkarsama
        if agent.situation:
            return self._simulate_situation_pad(agent.situation)
        
        # Yüz ifadesinden çıkarsama
        if agent.facial_expression:
            emotion = self._expression_to_emotion(agent.facial_expression)
            if emotion:
                return get_emotion_pad(emotion)
        
        # Varsayılan nötr
        return PADState.neutral()
    
    def _simulate_situation_pad(self, situation: str) -> PADState:
        """Durumdan PAD simüle et."""
        situation_pads = {
            "loss": PADState(pleasure=-0.7, arousal=0.5, dominance=0.2),
            "grief": PADState(pleasure=-0.8, arousal=0.4, dominance=0.15),
            "success": PADState(pleasure=0.8, arousal=0.7, dominance=0.8),
            "failure": PADState(pleasure=-0.6, arousal=0.5, dominance=0.25),
            "conflict": PADState(pleasure=-0.5, arousal=0.75, dominance=0.5),
            "threat": PADState(pleasure=-0.7, arousal=0.85, dominance=0.2),
            "celebration": PADState(pleasure=0.85, arousal=0.8, dominance=0.7),
            "rejection": PADState(pleasure=-0.65, arousal=0.55, dominance=0.2),
            "acceptance": PADState(pleasure=0.6, arousal=0.4, dominance=0.55),
            "uncertainty": PADState(pleasure=-0.2, arousal=0.6, dominance=0.3),
        }
        return situation_pads.get(situation, PADState.neutral())
    
    def _situation_to_emotion(self, situation: str) -> List[str]:
        """Durumdan olası duyguları çıkarsa."""
        mapping = {
            "loss": ["sadness", "grief"],
            "grief": ["sadness", "despair"],
            "success": ["joy", "pride"],
            "failure": ["sadness", "shame"],
            "conflict": ["anger", "anxiety"],
            "threat": ["fear", "anxiety"],
            "celebration": ["joy", "excitement"],
            "rejection": ["sadness", "shame"],
            "acceptance": ["joy", "relief"],
            "uncertainty": ["anxiety", "fear"],
        }
        return mapping.get(situation, [])
    
    def _expression_to_emotion(self, expression: str) -> Optional[BasicEmotion]:
        """Yüz ifadesinden duygu çıkarsa."""
        mapping = {
            "happy": BasicEmotion.JOY,
            "sad": BasicEmotion.SADNESS,
            "angry": BasicEmotion.ANGER,
            "fearful": BasicEmotion.FEAR,
            "disgusted": BasicEmotion.DISGUST,
            "surprised": BasicEmotion.SURPRISE,
        }
        return mapping.get(expression)
    
    def _relationship_to_familiarity(self, relationship: str) -> float:
        """İlişki türünden tanışıklık skoru."""
        mapping = {
            "stranger": 0.0,
            "acquaintance": 0.3,
            "colleague": 0.4,
            "friend": 0.7,
            "close_friend": 0.85,
            "family": 0.9,
            "partner": 0.95,
        }
        return mapping.get(relationship, 0.0)


@dataclass
class EmpathyResult:
    """
    Empati hesaplama sonucu.
    """
    agent_id: str
    channels: EmpathyChannels
    inferred_pad: PADState
    total_empathy: float  # 0-1
    
    # Metadata
    processing_time_ms: float = 0.0
    
    def __repr__(self) -> str:
        return (
            f"EmpathyResult(agent={self.agent_id}, "
            f"total={self.total_empathy:.2f}, "
            f"pad={self.inferred_pad})"
        )
    
    def get_dominant_channel(self) -> EmpathyChannel:
        """En güçlü empati kanalını döndür."""
        return self.channels.dominant_channel()
    
    def get_inferred_emotion(self) -> Optional[BasicEmotion]:
        """Çıkarsanan duyguyu döndür."""
        return identify_emotion(self.inferred_pad)
    
    def to_dict(self) -> Dict:
        """Dict formatında döndür."""
        return {
            "agent_id": self.agent_id,
            "total_empathy": self.total_empathy,
            "channels": self.channels.to_dict(),
            "inferred_pad": self.inferred_pad.to_dict(),
            "inferred_emotion": str(self.get_inferred_emotion()),
            "dominant_channel": self.get_dominant_channel().value,
        }
