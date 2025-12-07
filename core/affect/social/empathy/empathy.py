"""
UEM v2 - Empathy Module

Empati hesaplama ana modülü.

Empathy = Başkasının durumunu ANLAMAK (bilişsel süreç)
    ≠ Sympathy (duygusal tepki)
    ≠ Compassion (yardım etme motivasyonu)

Kullanım:
    from core.affect.social.empathy import Empathy, AgentState
    
    empathy = Empathy(my_pad_state)
    
    agent = AgentState(
        agent_id="bob",
        facial_expression="sad",
        situation="loss",
    )
    
    result = empathy.compute(agent)
    print(f"Empati: {result.total_empathy:.2f}")
    print(f"Bob'un duygusu: {result.get_inferred_emotion()}")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

import sys
sys.path.insert(0, '.')
from core.affect.emotion.core import PADState, BasicEmotion

from .channels import (
    EmpathyChannel,
    ChannelResult,
    EmpathyChannels,
    get_context_weights,
)
from .simulation import (
    AgentState,
    SimulationConfig,
    EmpathySimulator,
    EmpathyResult,
)


@dataclass
class EmpathyConfig:
    """Empati modülü yapılandırması."""
    
    # Simülasyon ayarları
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    
    # Varsayılan context
    default_context: str = "default"
    
    # Cache ayarları
    cache_results: bool = True
    cache_ttl_seconds: float = 30.0
    
    # Performans
    timeout_ms: float = 100.0


class Empathy:
    """
    Empati hesaplama facade sınıfı.
    
    StateVector veya PADState ile başlatılır,
    AgentState alır, EmpathyResult döner.
    """
    
    def __init__(
        self,
        self_state: PADState,
        config: Optional[EmpathyConfig] = None,
    ):
        """
        Args:
            self_state: Kendi PAD durumum
            config: Yapılandırma
        """
        self.self_state = self_state
        self.config = config or EmpathyConfig()
        
        self._simulator = EmpathySimulator(
            self_state=self_state,
            config=self.config.simulation,
        )
        
        # Cache: (agent_id, context) -> (result, timestamp)
        self._cache: Dict[str, tuple] = {}
    
    def compute(
        self,
        agent: AgentState,
        context: Optional[str] = None,
    ) -> EmpathyResult:
        """
        Ajan için empati hesapla.
        
        Args:
            agent: Gözlemlenen ajanın durumu
            context: Bağlam ("default", "close", "professional", "crisis")
            
        Returns:
            EmpathyResult
        """
        start_time = time.perf_counter()
        
        # Cache kontrol - context dahil
        if self.config.cache_results and agent.agent_id:
            cached = self._get_cached(agent.agent_id, context)
            if cached:
                return cached
        
        # Simülasyon
        result = self._simulator.simulate(agent)
        
        # Context weights uygula
        if context:
            weights = get_context_weights(context)
            result.total_empathy = result.channels.weighted_average(weights)
        
        # Süre
        result.processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Cache kaydet - context dahil
        if self.config.cache_results and agent.agent_id:
            self._set_cached(agent.agent_id, result, context)
        
        return result
    
    def compute_batch(
        self,
        agents: List[AgentState],
        context: Optional[str] = None,
    ) -> List[EmpathyResult]:
        """
        Birden fazla ajan için empati hesapla.
        
        Args:
            agents: Ajan listesi
            context: Bağlam
            
        Returns:
            EmpathyResult listesi
        """
        return [self.compute(agent, context) for agent in agents]
    
    def quick_empathy(
        self,
        agent_id: str,
        emotion_hint: Optional[BasicEmotion] = None,
        situation: Optional[str] = None,
    ) -> float:
        """
        Hızlı empati skoru (basitleştirilmiş).
        
        Args:
            agent_id: Ajan ID
            emotion_hint: Bilinen duygu
            situation: Durum
            
        Returns:
            0-1 arası empati skoru
        """
        agent = AgentState(
            agent_id=agent_id,
            situation=situation,
        )
        
        if emotion_hint:
            from core.affect.emotion.core import get_emotion_pad
            agent.observed_pad = get_emotion_pad(emotion_hint)
        
        result = self.compute(agent)
        return result.total_empathy
    
    def update_self_state(self, new_state: PADState) -> None:
        """Kendi PAD durumunu güncelle."""
        self.self_state = new_state
        self._simulator.self_state = new_state
        self._cache.clear()  # Cache geçersiz
    
    def _get_cached(
        self,
        agent_id: str,
        context: Optional[str] = None,
    ) -> Optional[EmpathyResult]:
        """Cache'ten sonuç getir."""
        cache_key = f"{agent_id}_{context}"
        
        if cache_key not in self._cache:
            return None
        
        result, timestamp = self._cache[cache_key]
        age = time.time() - timestamp
        
        if age > self.config.cache_ttl_seconds:
            del self._cache[cache_key]
            return None
        
        return result
    
    def _set_cached(
        self,
        agent_id: str,
        result: EmpathyResult,
        context: Optional[str] = None,
    ) -> None:
        """Cache'e kaydet."""
        cache_key = f"{agent_id}_{context}"
        self._cache[cache_key] = (result, time.time())
    
    def clear_cache(self) -> None:
        """Cache temizle."""
        self._cache.clear()


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def compute_empathy_for_emotion(
    self_state: PADState,
    target_emotion: BasicEmotion,
) -> float:
    """
    Belirli bir duygu için empati hesapla.
    
    Args:
        self_state: Kendi PAD durumum
        target_emotion: Hedef duygu
        
    Returns:
        0-1 arası empati skoru
    """
    from core.affect.emotion.core import get_emotion_pad
    
    target_pad = get_emotion_pad(target_emotion)
    
    # PAD mesafesi - yakınsa empati yüksek
    distance = self_state.distance(target_pad)
    base_empathy = 1.0 - min(1.0, distance / 1.5)
    
    # Negatif duygulara empati genelde daha yüksek (salience)
    if target_pad.pleasure < 0:
        base_empathy *= 1.15
    
    return min(1.0, base_empathy)


def estimate_empathy_difficulty(agent: AgentState) -> float:
    """
    Empati kurmanın zorluğunu tahmin et.
    
    Args:
        agent: Hedef ajan
        
    Returns:
        0-1 arası zorluk (0=kolay, 1=zor)
    """
    difficulty = 0.5  # Başlangıç
    
    # Az ipucu = daha zor
    if not agent.has_emotional_cues():
        difficulty += 0.3
    
    # Yabancı = daha zor
    familiarity_map = {
        "stranger": 0.3,
        "acquaintance": 0.15,
        "colleague": 0.1,
        "friend": -0.1,
        "family": -0.2,
    }
    difficulty += familiarity_map.get(agent.relationship_to_self, 0.2)
    
    # Belirsiz durum = daha zor
    if not agent.situation:
        difficulty += 0.15
    
    return max(0.0, min(1.0, difficulty))
