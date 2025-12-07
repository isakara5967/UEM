"""
UEM v2 - Sympathy Module

Sempati hesaplama ana modülü.

Sympathy = Empati sonrası KENDİ duygusal tepkim
    ≠ Empathy (anlama)
    ≠ Compassion (yardım motivasyonu - sympathy'nin bir türü)

Kullanım:
    from core.affect.social.sympathy import Sympathy
    from core.affect.social.empathy import Empathy, AgentState
    
    # Önce empati hesapla
    empathy = Empathy(my_pad)
    empathy_result = empathy.compute(agent)
    
    # Sonra sempati hesapla
    sympathy = Sympathy(my_pad)
    sympathy_result = sympathy.compute(empathy_result)
    
    print(f"Sempati: {sympathy_result.dominant_sympathy}")
    print(f"Eylem eğilimi: {sympathy_result.get_action_tendency()}")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

import sys
sys.path.insert(0, '.')
from core.affect.emotion.core import PADState
from core.affect.social.empathy import EmpathyResult, AgentState, Empathy

from .types import (
    SympathyType,
    SympathyResponse,
    get_sympathy_pad,
    get_action_tendency,
)
from .calculator import (
    SympathyCalculator,
    SympathyResult,
    SympathyConfig,
    RelationshipContext,
)


@dataclass
class SympathyModuleConfig:
    """Sempati modülü yapılandırması."""
    
    # Calculator config
    calculator: SympathyConfig = field(default_factory=SympathyConfig)
    
    # Modül ayarları
    auto_update_self_pad: bool = True  # Sempati sonucu kendi PAD'i günceller mi
    pad_update_strength: float = 0.3   # Güncelleme gücü
    
    # Cache
    cache_results: bool = False
    cache_ttl_seconds: float = 10.0


class Sympathy:
    """
    Sempati hesaplama facade sınıfı.
    
    EmpathyResult alır, SympathyResult döner.
    """
    
    def __init__(
        self,
        self_state: PADState,
        config: Optional[SympathyModuleConfig] = None,
    ):
        """
        Args:
            self_state: Kendi PAD durumum
            config: Yapılandırma
        """
        self.self_state = self_state
        self.config = config or SympathyModuleConfig()
        
        self._calculator = SympathyCalculator(
            self_state=self_state,
            config=self.config.calculator,
        )
    
    def compute(
        self,
        empathy_result: EmpathyResult,
        relationship: Optional[RelationshipContext] = None,
    ) -> SympathyResult:
        """
        Empati sonucundan sempati hesapla.
        
        Args:
            empathy_result: Empati hesaplama sonucu
            relationship: İlişki bağlamı (opsiyonel)
            
        Returns:
            SympathyResult
        """
        # İlişki bağlamı yoksa empati'den çıkarsanabilir
        if relationship is None:
            relationship = self._infer_relationship(empathy_result)
        
        # Hesapla
        result = self._calculator.calculate(empathy_result, relationship)
        
        # Kendi PAD'i güncelle (opsiyonel)
        if self.config.auto_update_self_pad and result.has_sympathy():
            self._update_self_pad(result.combined_pad_effect)
        
        return result
    
    def compute_from_agent(
        self,
        agent: AgentState,
        empathy_module: Optional[Empathy] = None,
        relationship: Optional[RelationshipContext] = None,
    ) -> SympathyResult:
        """
        AgentState'den direkt sempati hesapla (empatiyi otomatik yap).
        
        Args:
            agent: Hedef ajan
            empathy_module: Empati modülü (yoksa oluşturulur)
            relationship: İlişki bağlamı
            
        Returns:
            SympathyResult
        """
        # Empati modülü yoksa oluştur
        if empathy_module is None:
            empathy_module = Empathy(self.self_state)
        
        # Empati hesapla
        empathy_result = empathy_module.compute(agent)
        
        # İlişki bağlamı
        if relationship is None:
            relationship = RelationshipContext.from_relationship_type(
                agent.relationship_to_self
            )
        
        # Sempati hesapla
        return self.compute(empathy_result, relationship)
    
    def quick_sympathy(
        self,
        target_emotion: str,
        relationship_type: str = "stranger",
    ) -> Optional[SympathyType]:
        """
        Hızlı sempati tahmini.
        
        Args:
            target_emotion: Hedefin duygusu ("happy", "sad", "angry", "fearful")
            relationship_type: İlişki türü
            
        Returns:
            Beklenen sempati türü veya None
        """
        # Basitleştirilmiş mantık
        relationship = RelationshipContext.from_relationship_type(relationship_type)
        
        # Hedef mutsuzsa
        if target_emotion in ["sad", "fearful", "angry"]:
            if relationship.valence > 0:
                return SympathyType.COMPASSION
            elif relationship.valence < -0.3:
                return SympathyType.SCHADENFREUDE
            else:
                return SympathyType.EMPATHIC_SADNESS
        
        # Hedef mutluysa
        elif target_emotion in ["happy", "excited"]:
            if relationship.valence > 0:
                return SympathyType.EMPATHIC_JOY
            elif relationship.valence < -0.3:
                return SympathyType.ENVY
        
        return None
    
    def _infer_relationship(
        self,
        empathy_result: EmpathyResult,
    ) -> RelationshipContext:
        """Empati sonucundan ilişki çıkarsa."""
        # Empati yüksekse muhtemelen yakın ilişki
        empathy_level = empathy_result.total_empathy
        
        if empathy_level > 0.7:
            return RelationshipContext(valence=0.5, positive_history=0.6)
        elif empathy_level > 0.4:
            return RelationshipContext(valence=0.2, positive_history=0.4)
        else:
            return RelationshipContext.stranger()
    
    def _update_self_pad(self, sympathy_pad: PADState) -> None:
        """Sempati sonucu kendi PAD'i güncelle."""
        strength = self.config.pad_update_strength
        
        self.self_state = PADState(
            pleasure=self.self_state.pleasure + (sympathy_pad.pleasure - self.self_state.pleasure) * strength,
            arousal=self.self_state.arousal + (sympathy_pad.arousal - self.self_state.arousal) * strength,
            dominance=self.self_state.dominance + (sympathy_pad.dominance - self.self_state.dominance) * strength,
        )
        
        self._calculator.self_state = self.self_state
    
    def update_self_state(self, new_state: PADState) -> None:
        """Kendi PAD durumunu güncelle."""
        self.self_state = new_state
        self._calculator.self_state = new_state
    
    def get_self_state(self) -> PADState:
        """Mevcut PAD durumunu döndür."""
        return self.self_state


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def predict_sympathy(
    target_valence: float,
    relationship_valence: float,
) -> SympathyType:
    """
    Basit sempati tahmini.
    
    Args:
        target_valence: Hedefin valence'ı (-1 to 1)
        relationship_valence: İlişki değeri (-1 to 1)
        
    Returns:
        Beklenen sempati türü
    """
    # Hedef mutsuz
    if target_valence < -0.2:
        if relationship_valence > 0.2:
            return SympathyType.COMPASSION
        elif relationship_valence < -0.2:
            return SympathyType.SCHADENFREUDE
        else:
            return SympathyType.PITY
    
    # Hedef mutlu
    elif target_valence > 0.2:
        if relationship_valence > 0.2:
            return SympathyType.EMPATHIC_JOY
        elif relationship_valence < -0.2:
            return SympathyType.ENVY
        else:
            return SympathyType.EMPATHIC_JOY
    
    # Nötr
    return SympathyType.COMPASSION


def get_sympathy_spectrum(
    empathy_result: EmpathyResult,
) -> Dict[SympathyType, float]:
    """
    Olası tüm sempatilerin spektrumunu döndür.
    
    Args:
        empathy_result: Empati sonucu
        
    Returns:
        {SympathyType: probability} dict
    """
    target_pad = empathy_result.inferred_pad
    empathy_level = empathy_result.total_empathy
    
    spectrum = {}
    
    for sympathy_type in SympathyType:
        base_pad = get_sympathy_pad(sympathy_type)
        
        # PAD benzerliği
        distance = target_pad.distance(base_pad)
        similarity = 1.0 - min(1.0, distance / 1.5)
        
        # Empati modülasyonu
        probability = similarity * empathy_level
        
        spectrum[sympathy_type] = max(0.0, min(1.0, probability))
    
    return spectrum
