"""
UEM v2 - Sympathy Calculator

Empati sonucundan sempati tepkisi hesaplama.

Akış:
    EmpathyResult → SympathyCalculator → SympathyResult
    
    "O üzgün" (empati) → "Bu bende şefkat/acıma uyandırıyor" (sempati)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

import sys
sys.path.insert(0, '.')
from core.affect.emotion.core import PADState, BasicEmotion, identify_emotion
from core.affect.social.empathy import EmpathyResult

from .types import (
    SympathyType,
    SympathyResponse,
    SympathyTrigger,
    SYMPATHY_TRIGGERS,
    SYMPATHY_PAD_EFFECTS,
    SYMPATHY_ACTION_TENDENCIES,
    get_sympathy_pad,
    get_action_tendency,
    get_trigger,
)


@dataclass
class RelationshipContext:
    """
    İlişki bağlamı - sempati hesaplamada kullanılır.
    """
    # İlişki değeri: -1 (düşman) to +1 (yakın)
    valence: float = 0.0
    
    # Güç dengesi: -1 (hedef güçlü) to +1 (ben güçlüyüm)
    power_balance: float = 0.0
    
    # Geçmiş etkileşimler
    positive_history: float = 0.5  # 0-1
    negative_history: float = 0.0  # 0-1
    
    # Bağlamsal faktörler
    perceived_injustice: float = 0.0   # 0-1 haksızlık algısı
    perceived_deservedness: float = 0.5  # 0-1 hak etme algısı
    
    @classmethod
    def stranger(cls) -> "RelationshipContext":
        """Yabancı için varsayılan."""
        return cls(valence=0.0)
    
    @classmethod
    def friend(cls) -> "RelationshipContext":
        """Arkadaş için."""
        return cls(valence=0.6, positive_history=0.7)
    
    @classmethod
    def rival(cls) -> "RelationshipContext":
        """Rakip için."""
        return cls(valence=-0.4, negative_history=0.5)
    
    @classmethod
    def from_relationship_type(cls, rel_type: str) -> "RelationshipContext":
        """İlişki türünden bağlam oluştur."""
        mapping = {
            "stranger": cls.stranger(),
            "acquaintance": cls(valence=0.2),
            "colleague": cls(valence=0.3),
            "friend": cls.friend(),
            "close_friend": cls(valence=0.8, positive_history=0.85),
            "family": cls(valence=0.7, positive_history=0.8),
            "rival": cls.rival(),
            "enemy": cls(valence=-0.7, negative_history=0.7),
        }
        return mapping.get(rel_type, cls.stranger())


@dataclass
class SympathyConfig:
    """Sempati hesaplama yapılandırması."""
    
    # Eşikler
    min_empathy_for_sympathy: float = 0.2   # Sempati için min empati
    min_trigger_match: float = 0.4           # Tetikleme eşiği
    
    # Ağırlıklar
    empathy_weight: float = 0.4              # Empati seviyesinin etkisi
    relationship_weight: float = 0.3         # İlişkinin etkisi
    context_weight: float = 0.3              # Bağlamın etkisi
    
    # Modülatörler
    personality_compassion: float = 0.5      # Kişilik: şefkat eğilimi
    personality_schadenfreude: float = 0.1   # Kişilik: schadenfreude eğilimi
    
    # Çoklu sempati
    allow_multiple: bool = True              # Birden fazla sempati olabilir mi
    max_sympathies: int = 3                  # Maksimum eşzamanlı sempati


class SympathyCalculator:
    """
    Sempati hesaplayıcı.
    
    Empati sonucu + ilişki bağlamı → Sempati tepkisi
    """
    
    def __init__(
        self,
        self_state: PADState,
        config: Optional[SympathyConfig] = None,
    ):
        """
        Args:
            self_state: Kendi PAD durumum
            config: Yapılandırma
        """
        self.self_state = self_state
        self.config = config or SympathyConfig()
    
    def calculate(
        self,
        empathy_result: EmpathyResult,
        relationship: Optional[RelationshipContext] = None,
    ) -> "SympathyResult":
        """
        Empati sonucundan sempati hesapla.
        
        Args:
            empathy_result: Empati hesaplama sonucu
            relationship: İlişki bağlamı
            
        Returns:
            SympathyResult
        """
        if relationship is None:
            relationship = RelationshipContext.stranger()
        
        # Empati yeterli mi?
        if empathy_result.total_empathy < self.config.min_empathy_for_sympathy:
            return SympathyResult(
                agent_id=empathy_result.agent_id,
                responses=[],
                dominant_sympathy=None,
                total_intensity=0.0,
                empathy_source=empathy_result,
            )
        
        # Hedefin PAD'i (empatiyle çıkarsanmış)
        target_pad = empathy_result.inferred_pad
        
        # Tüm sempati türlerini değerlendir
        candidates: List[Tuple[SympathyType, float]] = []
        
        for sympathy_type in SympathyType:
            score = self._evaluate_sympathy(
                sympathy_type=sympathy_type,
                target_pad=target_pad,
                empathy_level=empathy_result.total_empathy,
                relationship=relationship,
            )
            
            if score >= self.config.min_trigger_match:
                candidates.append((sympathy_type, score))
        
        # Sırala ve seç
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        if not self.config.allow_multiple:
            candidates = candidates[:1]
        else:
            candidates = candidates[:self.config.max_sympathies]
        
        # Sempati tepkileri oluştur
        responses = []
        for sympathy_type, score in candidates:
            response = self._create_response(
                sympathy_type=sympathy_type,
                score=score,
                empathy_level=empathy_result.total_empathy,
                relationship=relationship,
            )
            responses.append(response)
        
        # Toplam PAD etkisi
        combined_pad = self._combine_pad_effects(responses)
        
        return SympathyResult(
            agent_id=empathy_result.agent_id,
            responses=responses,
            dominant_sympathy=responses[0].sympathy_type if responses else None,
            total_intensity=sum(r.intensity for r in responses) / len(responses) if responses else 0.0,
            combined_pad_effect=combined_pad,
            empathy_source=empathy_result,
        )
    
    def _evaluate_sympathy(
        self,
        sympathy_type: SympathyType,
        target_pad: PADState,
        empathy_level: float,
        relationship: RelationshipContext,
    ) -> float:
        """Bir sempati türünün uygunluğunu değerlendir."""
        
        # Tetikleme kuralını al
        trigger = get_trigger(sympathy_type)
        
        # Kural uyumu
        trigger_match = trigger.matches(
            target_pad=target_pad,
            relationship_valence=relationship.valence,
            perceived_injustice=relationship.perceived_injustice,
            perceived_deservedness=relationship.perceived_deservedness,
        )
        
        if trigger_match < self.config.min_trigger_match:
            return 0.0
        
        # Temel skor
        base_score = trigger_match
        
        # Empati modülasyonu
        empathy_factor = empathy_level * self.config.empathy_weight
        
        # İlişki modülasyonu
        relationship_factor = self._relationship_modifier(
            sympathy_type, relationship
        ) * self.config.relationship_weight
        
        # Kişilik modülasyonu
        personality_factor = self._personality_modifier(sympathy_type)
        
        # Toplam skor
        total = (
            base_score * 0.4 +
            empathy_factor +
            relationship_factor +
            personality_factor * 0.1
        )
        
        return max(0.0, min(1.0, total))
    
    def _relationship_modifier(
        self,
        sympathy_type: SympathyType,
        relationship: RelationshipContext,
    ) -> float:
        """İlişkinin sempati üzerindeki etkisi."""
        
        # Prososyal sempatiler pozitif ilişkiyle artar
        if sympathy_type in SympathyType.prosocial():
            return max(0, relationship.valence + 0.5)  # 0-1.5 range
        
        # Schadenfreude negatif ilişkiyle artar
        if sympathy_type == SympathyType.SCHADENFREUDE:
            return max(0, -relationship.valence + 0.5)
        
        # Envy nötr
        return 0.5
    
    def _personality_modifier(self, sympathy_type: SympathyType) -> float:
        """Kişiliğin sempati üzerindeki etkisi."""
        
        if sympathy_type == SympathyType.COMPASSION:
            return self.config.personality_compassion
        elif sympathy_type == SympathyType.SCHADENFREUDE:
            return self.config.personality_schadenfreude
        
        return 0.5
    
    def _create_response(
        self,
        sympathy_type: SympathyType,
        score: float,
        empathy_level: float,
        relationship: RelationshipContext,
    ) -> SympathyResponse:
        """Sempati tepkisi oluştur."""
        
        # Yoğunluk: skor * empati * ilişki
        intensity = score * (0.5 + empathy_level * 0.5)
        
        # İlişki bonusu
        if sympathy_type in SympathyType.prosocial():
            intensity *= (1 + relationship.valence * 0.3)
        
        intensity = max(0.0, min(1.0, intensity))
        
        # PAD etkisi
        base_pad = get_sympathy_pad(sympathy_type)
        scaled_pad = PADState(
            pleasure=base_pad.pleasure * intensity,
            arousal=base_pad.arousal * intensity,
            dominance=base_pad.dominance,
            intensity=intensity,
        )
        
        return SympathyResponse(
            sympathy_type=sympathy_type,
            intensity=intensity,
            pad_effect=scaled_pad,
            action_tendency=get_action_tendency(sympathy_type),
        )
    
    def _combine_pad_effects(
        self,
        responses: List[SympathyResponse],
    ) -> PADState:
        """Birden fazla sempati tepkisinin PAD etkisini birleştir."""
        
        if not responses:
            return PADState.neutral()
        
        total_intensity = sum(r.intensity for r in responses)
        if total_intensity == 0:
            return PADState.neutral()
        
        # Ağırlıklı ortalama
        pleasure = sum(r.pad_effect.pleasure * r.intensity for r in responses) / total_intensity
        arousal = sum(r.pad_effect.arousal * r.intensity for r in responses) / total_intensity
        dominance = sum(r.pad_effect.dominance * r.intensity for r in responses) / total_intensity
        
        return PADState(
            pleasure=pleasure,
            arousal=arousal,
            dominance=dominance,
            intensity=min(1.0, total_intensity / len(responses)),
        )


@dataclass
class SympathyResult:
    """
    Sempati hesaplama sonucu.
    """
    agent_id: str
    responses: List[SympathyResponse]
    dominant_sympathy: Optional[SympathyType]
    total_intensity: float
    
    # PAD etkisi
    combined_pad_effect: PADState = field(default_factory=PADState.neutral)
    
    # Kaynak empati
    empathy_source: Optional[EmpathyResult] = None
    
    def __repr__(self) -> str:
        if self.dominant_sympathy:
            return (
                f"SympathyResult(agent={self.agent_id}, "
                f"dominant={self.dominant_sympathy.value}, "
                f"intensity={self.total_intensity:.2f})"
            )
        return f"SympathyResult(agent={self.agent_id}, no_sympathy)"
    
    def has_sympathy(self) -> bool:
        """Sempati tepkisi var mı?"""
        return len(self.responses) > 0
    
    def get_action_tendency(self) -> Optional[str]:
        """Baskın davranış eğilimini döndür."""
        if self.responses:
            return self.responses[0].action_tendency
        return None
    
    def is_prosocial(self) -> bool:
        """Prososyal sempati mi?"""
        if self.dominant_sympathy:
            return self.dominant_sympathy in SympathyType.prosocial()
        return False
    
    def is_antisocial(self) -> bool:
        """Antisosyal sempati mi?"""
        if self.dominant_sympathy:
            return self.dominant_sympathy in SympathyType.antisocial()
        return False
    
    def to_dict(self) -> Dict:
        """Dict formatında döndür."""
        return {
            "agent_id": self.agent_id,
            "has_sympathy": self.has_sympathy(),
            "dominant": self.dominant_sympathy.value if self.dominant_sympathy else None,
            "total_intensity": self.total_intensity,
            "responses": [
                {
                    "type": r.sympathy_type.value,
                    "intensity": r.intensity,
                    "action": r.action_tendency,
                }
                for r in self.responses
            ],
            "combined_pad": self.combined_pad_effect.to_dict(),
            "is_prosocial": self.is_prosocial(),
        }
