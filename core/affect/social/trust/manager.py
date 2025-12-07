"""
UEM v2 - Trust Manager

Güven yönetimi, güncelleme ve decay mekanizmaları.

Güven dinamikleri:
- Güven YAVAŞ kazanılır, HIZLI kaybedilir
- Zaman geçtikçe nötre doğru decay
- Negatif olaylar pozitiflerden daha etkili (negativity bias)

Memory Entegrasyonu:
- Relationship history Memory'den okunur
- Her trust event Memory'ye kaydedilir
- Trust score Memory ile senkronize edilir
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math

from .types import (
    TrustLevel,
    TrustType,
    TrustDimension,
    TrustComponents,
    TrustEvent,
    create_trust_event,
    determine_trust_type,
    TRUST_EVENT_IMPACTS,
)

# Memory entegrasyonu
from core.memory import get_memory_store, Interaction, InteractionType


# Trust event -> InteractionType mapping
TRUST_EVENT_TO_INTERACTION: Dict[str, InteractionType] = {
    # Pozitif eventler
    "helped_me": InteractionType.HELPED,
    "promise_kept": InteractionType.COOPERATED,
    "honest_feedback": InteractionType.CONVERSED,
    "competent_action": InteractionType.COOPERATED,
    "consistent_behavior": InteractionType.OBSERVED,
    "defended_me": InteractionType.PROTECTED,
    "shared_joy": InteractionType.CELEBRATED,
    "comforted_me": InteractionType.COMFORTED,
    "grateful_interaction": InteractionType.COOPERATED,

    # Negatif eventler
    "lied_to_me": InteractionType.BETRAYED,
    "betrayal": InteractionType.BETRAYED,
    "harmed_me": InteractionType.HARMED,
    "unpredictable_behavior": InteractionType.CONFLICTED,
    "incompetent_action": InteractionType.CONFLICTED,
}


@dataclass
class TrustProfile:
    """
    Bir ajan için güven profili.
    """
    agent_id: str
    components: TrustComponents = field(default_factory=TrustComponents.default)
    trust_type: TrustType = TrustType.NEUTRAL
    
    # Geçmiş
    history: List[TrustEvent] = field(default_factory=list)
    first_interaction: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    
    # İstatistikler
    positive_events: int = 0
    negative_events: int = 0
    betrayal_count: int = 0
    
    def __post_init__(self):
        """İlk değerleri ayarla."""
        if self.first_interaction is None:
            self.first_interaction = datetime.now()
        self.last_interaction = datetime.now()
    
    @property
    def overall_trust(self) -> float:
        """Genel güven skoru."""
        return self.components.overall()
    
    @property
    def trust_level(self) -> TrustLevel:
        """Güven seviyesi."""
        return TrustLevel.from_value(self.overall_trust)
    
    @property
    def interaction_count(self) -> int:
        """Toplam etkileşim sayısı."""
        return len(self.history)
    
    @property
    def trust_ratio(self) -> float:
        """Pozitif/negatif olay oranı."""
        total = self.positive_events + self.negative_events
        if total == 0:
            return 0.5
        return self.positive_events / total
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "overall_trust": self.overall_trust,
            "trust_level": self.trust_level.value,
            "trust_type": self.trust_type.value,
            "components": self.components.to_dict(),
            "interaction_count": self.interaction_count,
            "positive_events": self.positive_events,
            "negative_events": self.negative_events,
            "betrayal_count": self.betrayal_count,
        }


@dataclass
class TrustConfig:
    """Güven yönetimi yapılandırması."""
    
    # Öğrenme oranları
    positive_learning_rate: float = 0.1    # Pozitif olay etkisi
    negative_learning_rate: float = 0.2    # Negatif olay etkisi (daha yüksek!)
    
    # Decay
    decay_enabled: bool = True
    decay_rate: float = 0.01               # Günlük decay (nötre doğru)
    decay_target: float = 0.5              # Decay hedefi (nötr)
    
    # Sınırlar
    min_trust: float = 0.0
    max_trust: float = 1.0
    
    # Tarihçe
    max_history_size: int = 100
    history_weight_decay: float = 0.95     # Eski olaylar daha az etkili
    
    # Özel durumlar
    betrayal_multiplier: float = 2.0       # İhanet çarpanı
    first_impression_boost: float = 1.5    # İlk izlenim etkisi


class TrustManager:
    """
    Güven yöneticisi.

    Birden fazla ajan için güven profillerini yönetir.
    Memory modülü ile entegre çalışır.
    """

    def __init__(self, config: Optional[TrustConfig] = None):
        self.config = config or TrustConfig()
        self._profiles: Dict[str, TrustProfile] = {}
        self._memory = get_memory_store()
    
    def get_profile(self, agent_id: str) -> TrustProfile:
        """
        Ajan için güven profili getir (yoksa oluştur).

        Memory'den relationship history'yi alır ve başlangıç trust değerini
        buna göre belirler.
        """
        if agent_id not in self._profiles:
            # Yeni profil oluştur
            profile = TrustProfile(agent_id=agent_id)

            # Memory'den relationship al ve başlangıç trust değerini hesapla
            relationship = self._memory.get_relationship(agent_id)
            initial_trust = relationship.get_trust_recommendation()

            # Profile uygula - tüm bileşenlere aynı başlangıç değeri
            profile.components = TrustComponents(
                competence=initial_trust,
                benevolence=initial_trust,
                integrity=initial_trust,
                predictability=initial_trust,
            )

            self._profiles[agent_id] = profile

        return self._profiles[agent_id]
    
    def get_trust(self, agent_id: str) -> float:
        """Ajan için güven skoru getir."""
        return self.get_profile(agent_id).overall_trust
    
    def get_trust_level(self, agent_id: str) -> TrustLevel:
        """Ajan için güven seviyesi getir."""
        return self.get_profile(agent_id).trust_level
    
    def record_event(
        self,
        agent_id: str,
        event_type: str,
        context: str = "",
    ) -> TrustProfile:
        """
        Güven olayı kaydet ve profili güncelle.

        Memory'ye de interaction olarak kaydeder.

        Args:
            agent_id: Ajan ID
            event_type: Olay tipi (örn: "promise_kept", "betrayal")
            context: Bağlam

        Returns:
            Güncellenmiş TrustProfile
        """
        profile = self.get_profile(agent_id)

        # Olay oluştur
        event = create_trust_event(event_type, context)

        # Güncelle
        self._apply_event(profile, event)

        # Tarihçeye ekle
        profile.history.append(event)
        if len(profile.history) > self.config.max_history_size:
            profile.history = profile.history[-self.config.max_history_size:]

        # İstatistikleri güncelle
        if event.impact > 0:
            profile.positive_events += 1
        elif event.impact < 0:
            profile.negative_events += 1
            if event_type in ["betrayal", "harmed_me"]:
                profile.betrayal_count += 1

        # Son etkileşim zamanını güncelle
        profile.last_interaction = datetime.now()

        # Güven tipini yeniden belirle
        profile.trust_type = determine_trust_type(
            profile.components,
            len(profile.history),
            profile.betrayal_count > 0,
        )

        # Memory'ye interaction kaydet
        interaction = Interaction(
            interaction_type=self._map_trust_event_to_interaction(event_type),
            context=context,
            outcome_valence=event.impact,
            trust_impact=event.weighted_impact(),
        )
        self._memory.record_interaction(agent_id, interaction)

        # Memory'deki trust bilgisini senkronize et
        relationship = self._memory.get_relationship(agent_id)
        relationship.trust_score = profile.overall_trust
        relationship.trust_history.append(profile.overall_trust)

        return profile

    def _map_trust_event_to_interaction(self, event_type: str) -> InteractionType:
        """Trust event tipini InteractionType'a dönüştür."""
        return TRUST_EVENT_TO_INTERACTION.get(event_type, InteractionType.OBSERVED)
    
    def _apply_event(self, profile: TrustProfile, event: TrustEvent) -> None:
        """Olayı profile uygula."""
        
        # Öğrenme oranı
        if event.impact > 0:
            learning_rate = self.config.positive_learning_rate
        else:
            learning_rate = self.config.negative_learning_rate
        
        # İlk izlenim bonusu
        if len(profile.history) < 3:
            learning_rate *= self.config.first_impression_boost
        
        # İhanet çarpanı
        if event.event_type in ["betrayal", "harmed_me"]:
            learning_rate *= self.config.betrayal_multiplier
        
        # Ağırlıklı etki
        delta = event.weighted_impact() * learning_rate
        
        # İlgili boyutu güncelle
        current = getattr(profile.components, event.dimension.value)
        new_value = current + delta
        new_value = max(self.config.min_trust, min(self.config.max_trust, new_value))
        setattr(profile.components, event.dimension.value, new_value)
    
    def apply_decay(self, agent_id: str, days_passed: float = 1.0) -> TrustProfile:
        """
        Zaman bazlı decay uygula.
        
        Güven zamanla nötre doğru kayar.
        """
        if not self.config.decay_enabled:
            return self.get_profile(agent_id)
        
        profile = self.get_profile(agent_id)
        target = self.config.decay_target
        rate = self.config.decay_rate * days_passed
        
        # Her boyuta decay uygula
        for dim in TrustDimension:
            current = getattr(profile.components, dim.value)
            # Nötre doğru kay
            if current > target:
                new_value = current - rate
                new_value = max(target, new_value)
            else:
                new_value = current + rate
                new_value = min(target, new_value)
            setattr(profile.components, dim.value, new_value)
        
        return profile
    
    def set_initial_trust(
        self,
        agent_id: str,
        trust_type: TrustType,
        components: Optional[TrustComponents] = None,
    ) -> TrustProfile:
        """
        Başlangıç güveni ayarla.
        
        Örn: "arkadaşın arkadaşı" için baştan yüksek güven.
        """
        profile = self.get_profile(agent_id)
        
        if components:
            profile.components = components
        else:
            # Trust tipine göre varsayılan
            defaults = {
                TrustType.BLIND: TrustComponents(0.9, 0.9, 0.9, 0.8),
                TrustType.EARNED: TrustComponents(0.8, 0.8, 0.8, 0.8),
                TrustType.CAUTIOUS: TrustComponents(0.4, 0.4, 0.4, 0.5),
                TrustType.NEUTRAL: TrustComponents(0.5, 0.5, 0.5, 0.5),
                TrustType.CONDITIONAL: TrustComponents(0.6, 0.6, 0.6, 0.5),
                TrustType.DISTRUST: TrustComponents(0.2, 0.2, 0.2, 0.3),
                TrustType.BETRAYED: TrustComponents(0.1, 0.1, 0.1, 0.4),
            }
            profile.components = defaults.get(trust_type, TrustComponents.default())
        
        profile.trust_type = trust_type
        
        return profile
    
    def compare_trust(self, agent_id_1: str, agent_id_2: str) -> str:
        """İki ajan arasında güven karşılaştırması."""
        trust_1 = self.get_trust(agent_id_1)
        trust_2 = self.get_trust(agent_id_2)
        
        diff = trust_1 - trust_2
        
        if abs(diff) < 0.1:
            return "equal"
        elif diff > 0:
            return agent_id_1
        else:
            return agent_id_2
    
    def get_most_trusted(self, limit: int = 5) -> List[TrustProfile]:
        """En güvenilen ajanları getir."""
        profiles = list(self._profiles.values())
        profiles.sort(key=lambda p: p.overall_trust, reverse=True)
        return profiles[:limit]
    
    def get_least_trusted(self, limit: int = 5) -> List[TrustProfile]:
        """En az güvenilen ajanları getir."""
        profiles = list(self._profiles.values())
        profiles.sort(key=lambda p: p.overall_trust)
        return profiles[:limit]
    
    def reset_trust(self, agent_id: str) -> TrustProfile:
        """Güveni sıfırla."""
        if agent_id in self._profiles:
            del self._profiles[agent_id]
        return self.get_profile(agent_id)
    
    def all_profiles(self) -> List[TrustProfile]:
        """Tüm profilleri getir."""
        return list(self._profiles.values())
    
    @property
    def stats(self) -> Dict:
        """Yönetici istatistikleri."""
        profiles = list(self._profiles.values())
        if not profiles:
            return {"profile_count": 0}
        
        trusts = [p.overall_trust for p in profiles]
        
        return {
            "profile_count": len(profiles),
            "avg_trust": sum(trusts) / len(trusts),
            "min_trust": min(trusts),
            "max_trust": max(trusts),
            "high_trust_count": sum(1 for t in trusts if t >= 0.7),
            "low_trust_count": sum(1 for t in trusts if t <= 0.3),
        }
