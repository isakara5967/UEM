"""
UEM v2 - Trust Module

Güven hesaplama ana modülü.

Trust = Geçmiş etkileşimlere dayalı güven değerlendirmesi

Kullanım:
    from core.affect.social.trust import Trust
    
    trust = Trust()
    
    # Olay kaydet
    trust.record("alice", "promise_kept")
    trust.record("alice", "helped_me")
    trust.record("bob", "lied_to_me")
    
    # Güven sorgula
    print(f"Alice güveni: {trust.get('alice'):.2f}")
    print(f"Bob güveni: {trust.get('bob'):.2f}")
    
    # Karar desteği
    should_trust = trust.should_trust("alice", threshold=0.6)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .types import (
    TrustLevel,
    TrustType,
    TrustDimension,
    TrustComponents,
    TrustEvent,
    create_trust_event,
    determine_trust_type,
)
from .manager import (
    TrustProfile,
    TrustConfig,
    TrustManager,
)


class Trust:
    """
    Güven hesaplama facade sınıfı.
    
    Basit API ile güven yönetimi.
    """
    
    def __init__(self, config: Optional[TrustConfig] = None):
        """
        Args:
            config: Yapılandırma
        """
        self.config = config or TrustConfig()
        self._manager = TrustManager(config=self.config)
    
    # ═══════════════════════════════════════════════════════════════════════
    # TEMEL İŞLEMLER
    # ═══════════════════════════════════════════════════════════════════════
    
    def get(self, agent_id: str) -> float:
        """
        Ajan için güven skoru getir.
        
        Args:
            agent_id: Ajan ID
            
        Returns:
            0-1 arası güven skoru
        """
        return self._manager.get_trust(agent_id)
    
    def get_level(self, agent_id: str) -> TrustLevel:
        """
        Ajan için güven seviyesi getir.
        
        Args:
            agent_id: Ajan ID
            
        Returns:
            TrustLevel enum
        """
        return self._manager.get_trust_level(agent_id)
    
    def get_profile(self, agent_id: str) -> TrustProfile:
        """
        Ajan için tam güven profili getir.
        
        Args:
            agent_id: Ajan ID
            
        Returns:
            TrustProfile
        """
        return self._manager.get_profile(agent_id)
    
    def record(
        self,
        agent_id: str,
        event_type: str,
        context: str = "",
    ) -> float:
        """
        Güven olayı kaydet.
        
        Args:
            agent_id: Ajan ID
            event_type: Olay tipi
            context: Bağlam
            
        Returns:
            Güncellenmiş güven skoru
        """
        profile = self._manager.record_event(agent_id, event_type, context)
        return profile.overall_trust
    
    def set_initial(
        self,
        agent_id: str,
        trust_type: TrustType,
    ) -> float:
        """
        Başlangıç güveni ayarla.
        
        Args:
            agent_id: Ajan ID
            trust_type: Güven tipi
            
        Returns:
            Ayarlanan güven skoru
        """
        profile = self._manager.set_initial_trust(agent_id, trust_type)
        return profile.overall_trust
    
    # ═══════════════════════════════════════════════════════════════════════
    # KARAR DESTEĞİ
    # ═══════════════════════════════════════════════════════════════════════
    
    def should_trust(
        self,
        agent_id: str,
        threshold: float = 0.5,
    ) -> bool:
        """
        Ajana güvenilmeli mi?
        
        Args:
            agent_id: Ajan ID
            threshold: Güven eşiği
            
        Returns:
            True/False
        """
        return self.get(agent_id) >= threshold
    
    def trust_for_action(
        self,
        agent_id: str,
        action_risk: float,
    ) -> Tuple[bool, str]:
        """
        Belirli bir aksiyon için güven yeterli mi?
        
        Args:
            agent_id: Ajan ID
            action_risk: Aksiyon riski (0-1)
            
        Returns:
            (güvenilir_mi, açıklama)
        """
        trust = self.get(agent_id)
        profile = self.get_profile(agent_id)
        
        # Risk-güven dengesi
        # Yüksek riskli aksiyonlar daha yüksek güven gerektirir
        required_trust = 0.3 + (action_risk * 0.5)
        
        if trust >= required_trust:
            return (True, f"Trust ({trust:.2f}) sufficient for risk ({action_risk:.2f})")
        else:
            weakest = profile.components.weakest_dimension()
            return (False, f"Trust ({trust:.2f}) insufficient. Weakest: {weakest.value}")
    
    def compare(self, agent_id_1: str, agent_id_2: str) -> str:
        """
        İki ajanı güven açısından karşılaştır.
        
        Returns:
            Daha güvenilir olanın ID'si veya "equal"
        """
        return self._manager.compare_trust(agent_id_1, agent_id_2)
    
    def rank(self, agent_ids: List[str]) -> List[Tuple[str, float]]:
        """
        Ajanları güvene göre sırala.
        
        Args:
            agent_ids: Ajan ID listesi
            
        Returns:
            [(agent_id, trust_score), ...] sıralı liste
        """
        results = [(aid, self.get(aid)) for aid in agent_ids]
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    # ═══════════════════════════════════════════════════════════════════════
    # ANALİZ
    # ═══════════════════════════════════════════════════════════════════════
    
    def analyze(self, agent_id: str) -> Dict:
        """
        Güven analizi yap.
        
        Args:
            agent_id: Ajan ID
            
        Returns:
            Analiz sonuçları
        """
        profile = self.get_profile(agent_id)
        
        analysis = {
            "agent_id": agent_id,
            "overall_trust": profile.overall_trust,
            "trust_level": profile.trust_level.value,
            "trust_type": profile.trust_type.value,
            "components": profile.components.to_dict(),
            "interaction_count": profile.interaction_count,
            "trust_ratio": profile.trust_ratio,
            "weakest_dimension": profile.components.weakest_dimension().value,
            "strongest_dimension": profile.components.strongest_dimension().value,
        }
        
        # Öneriler
        recommendations = []
        
        if profile.overall_trust < 0.3:
            recommendations.append("Low trust - exercise caution")
        
        if profile.betrayal_count > 0:
            recommendations.append(f"History of betrayal ({profile.betrayal_count}x)")
        
        if profile.interaction_count < 3:
            recommendations.append("Limited interaction history - insufficient data")
        
        weakest = profile.components.weakest_dimension()
        weakest_val = getattr(profile.components, weakest.value)
        if weakest_val < 0.4:
            recommendations.append(f"Low {weakest.value} ({weakest_val:.2f})")
        
        analysis["recommendations"] = recommendations
        
        return analysis
    
    def explain_trust(self, agent_id: str) -> str:
        """
        Güven durumunu açıkla (insan okunabilir).
        
        Args:
            agent_id: Ajan ID
            
        Returns:
            Açıklama metni
        """
        profile = self.get_profile(agent_id)
        
        level_desc = {
            TrustLevel.BLIND: "very high (possibly naive)",
            TrustLevel.HIGH: "high",
            TrustLevel.MODERATE: "moderate",
            TrustLevel.CAUTIOUS: "cautious",
            TrustLevel.LOW: "low",
            TrustLevel.DISTRUST: "very low (distrust)",
        }
        
        desc = level_desc.get(profile.trust_level, "unknown")
        
        explanation = f"Trust in {agent_id} is {desc} ({profile.overall_trust:.2f}). "
        
        if profile.interaction_count == 0:
            explanation += "No prior interactions."
        else:
            explanation += f"Based on {profile.interaction_count} interactions "
            explanation += f"({profile.positive_events} positive, {profile.negative_events} negative). "
        
        if profile.betrayal_count > 0:
            explanation += f"WARNING: {profile.betrayal_count} betrayal(s) recorded. "
        
        weakest = profile.components.weakest_dimension()
        explanation += f"Weakest area: {weakest.value}."
        
        return explanation
    
    # ═══════════════════════════════════════════════════════════════════════
    # YARDIMCI
    # ═══════════════════════════════════════════════════════════════════════
    
    def reset(self, agent_id: str) -> None:
        """Güveni sıfırla."""
        self._manager.reset_trust(agent_id)
    
    def apply_time_decay(self, agent_id: str, days: float = 1.0) -> float:
        """
        Zaman bazlı decay uygula.
        
        Args:
            agent_id: Ajan ID
            days: Geçen gün sayısı
            
        Returns:
            Güncellenmiş güven
        """
        profile = self._manager.apply_decay(agent_id, days)
        return profile.overall_trust
    
    def most_trusted(self, limit: int = 5) -> List[Tuple[str, float]]:
        """En güvenilen ajanları getir."""
        profiles = self._manager.get_most_trusted(limit)
        return [(p.agent_id, p.overall_trust) for p in profiles]
    
    def least_trusted(self, limit: int = 5) -> List[Tuple[str, float]]:
        """En az güvenilen ajanları getir."""
        profiles = self._manager.get_least_trusted(limit)
        return [(p.agent_id, p.overall_trust) for p in profiles]
    
    @property
    def stats(self) -> Dict:
        """İstatistikler."""
        return self._manager.stats


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def quick_trust_check(
    interaction_count: int,
    positive_ratio: float,
    had_betrayal: bool = False,
) -> TrustLevel:
    """
    Hızlı güven tahmini.
    
    Args:
        interaction_count: Etkileşim sayısı
        positive_ratio: Pozitif olay oranı (0-1)
        had_betrayal: İhanet var mı
        
    Returns:
        TrustLevel
    """
    if had_betrayal:
        return TrustLevel.DISTRUST if positive_ratio < 0.5 else TrustLevel.CAUTIOUS
    
    if interaction_count < 3:
        return TrustLevel.CAUTIOUS
    
    if positive_ratio >= 0.9:
        return TrustLevel.HIGH
    elif positive_ratio >= 0.7:
        return TrustLevel.MODERATE
    elif positive_ratio >= 0.5:
        return TrustLevel.CAUTIOUS
    elif positive_ratio >= 0.3:
        return TrustLevel.LOW
    else:
        return TrustLevel.DISTRUST


def calculate_risk_threshold(trust_level: TrustLevel) -> float:
    """
    Güven seviyesine göre kabul edilebilir risk eşiği.
    
    Args:
        trust_level: Güven seviyesi
        
    Returns:
        Kabul edilebilir maksimum risk (0-1)
    """
    thresholds = {
        TrustLevel.BLIND: 0.9,
        TrustLevel.HIGH: 0.7,
        TrustLevel.MODERATE: 0.5,
        TrustLevel.CAUTIOUS: 0.3,
        TrustLevel.LOW: 0.15,
        TrustLevel.DISTRUST: 0.05,
    }
    return thresholds.get(trust_level, 0.3)
