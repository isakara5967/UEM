"""
UEM v2 - StateVector Bridge

Modüller ile StateVector arasında köprü.
Affect modüllerinin sonuçlarını StateVector'a yazar,
StateVector'dan modül girdilerini okur.

Kullanım:
    from foundation.state import StateVector, StateVectorBridge
    
    bridge = StateVectorBridge()
    
    # Yazma
    bridge.write_pad(state, pad_result)
    bridge.write_empathy(state, empathy_result)
    bridge.write_sympathy(state, sympathy_result)
    bridge.write_trust(state, trust_profile)
    
    # Okuma
    self_pad = bridge.read_self_pad(state)
    social_context = bridge.read_social_context(state)
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any, TYPE_CHECKING

from .fields import SVField
from .vector import StateVector

# Type checking imports (circular import önleme)
if TYPE_CHECKING:
    from core.affect.emotion.core import PADState
    from core.affect.social.empathy import EmpathyResult
    from core.affect.social.sympathy import SympathyResult, SympathyType
    from core.affect.social.trust import TrustProfile


@dataclass
class SocialContext:
    """StateVector'dan okunan sosyal bağlam."""
    empathy_total: float = 0.0
    sympathy_level: float = 0.0
    sympathy_valence: float = 0.5  # 0=antisocial, 1=prosocial
    trust_value: float = 0.5
    relationship_quality: float = 0.5
    social_engagement: float = 0.5


class StateVectorBridge:
    """
    StateVector ile affect modülleri arasında köprü.
    
    Yazma işlemleri: Modül sonuçlarını StateVector'a yazar
    Okuma işlemleri: StateVector'dan modül girdileri oluşturur
    """
    
    def __init__(self):
        """Bridge başlat."""
        pass
    
    # ═══════════════════════════════════════════════════════════════════
    # WRITE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════
    
    def write_pad(
        self,
        state: StateVector,
        pad: "PADState",
    ) -> StateVector:
        """
        PAD durumunu StateVector'a yaz.
        
        Args:
            state: Güncellenecek StateVector
            pad: PADState sonucu
            
        Returns:
            Güncellenmiş StateVector
        """
        # PAD değerleri: pleasure -1..1, arousal/dominance 0..1
        # StateVector 0..1 aralığı kullanıyor
        
        # Valence: -1..1 → 0..1 normalize
        valence_normalized = (pad.pleasure + 1) / 2
        state.set(SVField.VALENCE, valence_normalized)
        
        # Arousal ve Dominance zaten 0..1
        state.set(SVField.AROUSAL, pad.arousal)
        state.set(SVField.DOMINANCE, pad.dominance)
        
        # Emotional intensity (PAD büyüklüğü)
        intensity = (abs(pad.pleasure) + pad.arousal) / 2
        state.set(SVField.EMOTIONAL_INTENSITY, intensity)
        
        return state
    
    def write_empathy(
        self,
        state: StateVector,
        empathy: "EmpathyResult",
    ) -> StateVector:
        """
        Empathy sonucunu StateVector'a yaz.
        
        Args:
            state: Güncellenecek StateVector
            empathy: EmpathyResult sonucu
            
        Returns:
            Güncellenmiş StateVector
        """
        # 4 kanal - ChannelResult objelerinden .value al
        if empathy.channels:
            state.set(SVField.COGNITIVE_EMPATHY, empathy.channels.cognitive.value)
            state.set(SVField.AFFECTIVE_EMPATHY, empathy.channels.affective.value)
            state.set(SVField.SOMATIC_EMPATHY, empathy.channels.somatic.value)
            state.set(SVField.PROJECTIVE_EMPATHY, empathy.channels.projective.value)
        
        # Toplam
        state.set(SVField.EMPATHY_TOTAL, empathy.total_empathy)
        
        return state
    
    def write_sympathy(
        self,
        state: StateVector,
        sympathy: "SympathyResult",
    ) -> StateVector:
        """
        Sympathy sonucunu StateVector'a yaz.
        
        Args:
            state: Güncellenecek StateVector
            sympathy: SympathyResult sonucu
            
        Returns:
            Güncellenmiş StateVector
        """
        # Sympathy level (dominant response intensity)
        level = 0.0
        if sympathy.dominant_sympathy and sympathy.responses:
            for r in sympathy.responses:
                if r.sympathy_type == sympathy.dominant_sympathy:
                    level = r.intensity
                    break
        
        state.set(SVField.SYMPATHY_LEVEL, level)
        
        # Sympathy valence (prosocial vs antisocial)
        # 1.0 = prosocial, 0.0 = antisocial, 0.5 = neutral
        valence = 0.5
        if sympathy.dominant_sympathy:
            if sympathy.is_prosocial():
                valence = 0.7 + (level * 0.3)  # 0.7 - 1.0
            elif sympathy.is_antisocial():
                valence = 0.3 - (level * 0.3)  # 0.0 - 0.3
        
        state.set(SVField.SYMPATHY_VALENCE, valence)
        
        return state
    
    def write_trust(
        self,
        state: StateVector,
        profile: "TrustProfile",
        agent_id: Optional[str] = None,
    ) -> StateVector:
        """
        Trust profilini StateVector'a yaz.
        
        Not: StateVector tek bir agent için trust tutar.
        Birden fazla agent varsa en son yazılan geçerli olur.
        Çoklu agent için state.metadata kullanılabilir.
        
        Args:
            state: Güncellenecek StateVector
            profile: TrustProfile
            agent_id: Opsiyonel agent ID (metadata için)
            
        Returns:
            Güncellenmiş StateVector
        """
        state.set(SVField.TRUST_VALUE, profile.overall_trust)
        
        # Trust boyutları
        if profile.components:
            state.set(SVField.TRUST_COMPETENCE, profile.components.competence)
            state.set(SVField.TRUST_BENEVOLENCE, profile.components.benevolence)
            state.set(SVField.TRUST_INTEGRITY, profile.components.integrity)
            state.set(SVField.TRUST_PREDICTABILITY, profile.components.predictability)
        
        return state
    
    def write_social_affect(
        self,
        state: StateVector,
        empathy: Optional["EmpathyResult"] = None,
        sympathy: Optional["SympathyResult"] = None,
        trust: Optional["TrustProfile"] = None,
        pad: Optional["PADState"] = None,
    ) -> StateVector:
        """
        Tüm social affect sonuçlarını tek seferde yaz.
        
        Args:
            state: Güncellenecek StateVector
            empathy: EmpathyResult (opsiyonel)
            sympathy: SympathyResult (opsiyonel)
            trust: TrustProfile (opsiyonel)
            pad: PADState (opsiyonel)
            
        Returns:
            Güncellenmiş StateVector
        """
        if pad:
            self.write_pad(state, pad)
        
        if empathy:
            self.write_empathy(state, empathy)
        
        if sympathy:
            self.write_sympathy(state, sympathy)
        
        if trust:
            self.write_trust(state, trust)
        
        # Relationship quality (empathy + trust ortalaması)
        if empathy and trust:
            quality = (empathy.total_empathy + trust.overall_trust) / 2
            state.set(SVField.RELATIONSHIP_QUALITY, quality)
        
        return state
    
    # ═══════════════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ═══════════════════════════════════════════════════════════════════
    
    def read_self_pad(self, state: StateVector) -> "PADState":
        """
        StateVector'dan PADState oku.
        
        Args:
            state: Okunacak StateVector
            
        Returns:
            PADState
        """
        # Lazy import (circular dependency önleme)
        from core.affect.emotion.core import PADState
        
        # Valence: 0..1 → -1..1 denormalize
        valence_norm = state.get(SVField.VALENCE, 0.5)
        pleasure = (valence_norm * 2) - 1
        
        arousal = state.get(SVField.AROUSAL, 0.5)
        dominance = state.get(SVField.DOMINANCE, 0.5)
        
        return PADState(
            pleasure=pleasure,
            arousal=arousal,
            dominance=dominance,
        )
    
    def read_social_context(self, state: StateVector) -> SocialContext:
        """
        StateVector'dan sosyal bağlam oku.
        
        Args:
            state: Okunacak StateVector
            
        Returns:
            SocialContext
        """
        return SocialContext(
            empathy_total=state.get(SVField.EMPATHY_TOTAL, 0.0),
            sympathy_level=state.get(SVField.SYMPATHY_LEVEL, 0.0),
            sympathy_valence=state.get(SVField.SYMPATHY_VALENCE, 0.5),
            trust_value=state.get(SVField.TRUST_VALUE, 0.5),
            relationship_quality=state.get(SVField.RELATIONSHIP_QUALITY, 0.5),
            social_engagement=state.get(SVField.SOCIAL_ENGAGEMENT, 0.5),
        )
    
    def read_empathy_channels(self, state: StateVector) -> Dict[str, float]:
        """
        StateVector'dan empathy kanallarını oku.
        
        Returns:
            {"cognitive": float, "affective": float, ...}
        """
        return {
            "cognitive": state.get(SVField.COGNITIVE_EMPATHY, 0.0),
            "affective": state.get(SVField.AFFECTIVE_EMPATHY, 0.0),
            "somatic": state.get(SVField.SOMATIC_EMPATHY, 0.0),
            "projective": state.get(SVField.PROJECTIVE_EMPATHY, 0.0),
            "total": state.get(SVField.EMPATHY_TOTAL, 0.0),
        }
    
    def read_trust_dimensions(self, state: StateVector) -> Dict[str, float]:
        """
        StateVector'dan trust boyutlarını oku.
        
        Returns:
            {"competence": float, "benevolence": float, ...}
        """
        return {
            "overall": state.get(SVField.TRUST_VALUE, 0.5),
            "competence": state.get(SVField.TRUST_COMPETENCE, 0.5),
            "benevolence": state.get(SVField.TRUST_BENEVOLENCE, 0.5),
            "integrity": state.get(SVField.TRUST_INTEGRITY, 0.5),
            "predictability": state.get(SVField.TRUST_PREDICTABILITY, 0.5),
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_affect_summary(self, state: StateVector) -> Dict[str, Any]:
        """
        StateVector'dan affect özeti çıkar.
        
        Returns:
            Tüm affect değerlerinin özeti
        """
        pad = self.read_self_pad(state)
        social = self.read_social_context(state)
        empathy = self.read_empathy_channels(state)
        trust = self.read_trust_dimensions(state)
        
        return {
            "pad": {
                "pleasure": pad.pleasure,
                "arousal": pad.arousal,
                "dominance": pad.dominance,
            },
            "empathy": empathy,
            "sympathy": {
                "level": social.sympathy_level,
                "valence": social.sympathy_valence,
            },
            "trust": trust,
            "social": {
                "relationship_quality": social.relationship_quality,
                "social_engagement": social.social_engagement,
            },
        }
    
    def reset_social_fields(self, state: StateVector) -> StateVector:
        """
        Sosyal alanları sıfırla (yeni agent için).
        
        Args:
            state: Güncellenecek StateVector
            
        Returns:
            Güncellenmiş StateVector
        """
        # Empathy
        state.set(SVField.COGNITIVE_EMPATHY, 0.0)
        state.set(SVField.AFFECTIVE_EMPATHY, 0.0)
        state.set(SVField.SOMATIC_EMPATHY, 0.0)
        state.set(SVField.PROJECTIVE_EMPATHY, 0.0)
        state.set(SVField.EMPATHY_TOTAL, 0.0)
        
        # Sympathy
        state.set(SVField.SYMPATHY_LEVEL, 0.0)
        state.set(SVField.SYMPATHY_VALENCE, 0.5)
        
        # Trust (neutral'a set et, 0 değil)
        state.set(SVField.TRUST_VALUE, 0.5)
        state.set(SVField.TRUST_COMPETENCE, 0.5)
        state.set(SVField.TRUST_BENEVOLENCE, 0.5)
        state.set(SVField.TRUST_INTEGRITY, 0.5)
        state.set(SVField.TRUST_PREDICTABILITY, 0.5)
        
        # Relationship
        state.set(SVField.RELATIONSHIP_QUALITY, 0.5)
        
        return state


# Singleton instance
_default_bridge: Optional[StateVectorBridge] = None


def get_state_bridge() -> StateVectorBridge:
    """Default StateVectorBridge instance'ını getir."""
    global _default_bridge
    if _default_bridge is None:
        _default_bridge = StateVectorBridge()
    return _default_bridge
