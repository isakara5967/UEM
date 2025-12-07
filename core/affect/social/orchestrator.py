"""
UEM v2 - Social Affect Orchestrator (StateVector Integrated)

Empathy, Sympathy ve Trust modüllerini entegre eden orkestratör.
StateVector ile tam entegrasyon - sonuçlar otomatik olarak yazılır.

Memory Entegrasyonu:
- Her etkileşim Episode olarak Memory'ye kaydedilir
- Relationship context Memory'den okunur
- Trust hesabında Memory'deki geçmiş kullanılır

Akış:
    StateVector (okuma)
           ↓
    ┌─────────────────┐
    │     EMPATHY     │  "Bu kişi ne durumda?"
    │  (Simulation)   │  → EmpathyResult → StateVector
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │    SYMPATHY     │  "Bu bende ne uyandırıyor?"
    │   (Response)    │  → SympathyResult → StateVector
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │      TRUST      │  Sympathy'ye göre güven güncelle
    │    (Update)     │  → TrustProfile → StateVector
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │     MEMORY      │  Episode kaydet
    └────────┬────────┘
             ↓
    StateVector (yazma) + SocialAffectResult

Kullanım:
    from foundation.state import StateVector
    from core.affect.social import SocialAffectOrchestrator

    # StateVector ile başlat
    state = StateVector(resource=0.8, threat=0.1, wellbeing=0.7)
    orchestrator = SocialAffectOrchestrator.from_state_vector(state)

    # İşle - sonuçlar otomatik StateVector'a yazılır
    result = orchestrator.process(agent_state)

    # StateVector güncellendi
    print(state.get(SVField.EMPATHY_TOTAL))  # Empati değeri
    print(state.get(SVField.TRUST_VALUE))    # Güven değeri
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import sys
sys.path.insert(0, '.')

from foundation.state import StateVector, SVField, StateVectorBridge, get_state_bridge
from core.affect.emotion.core import PADState, BasicEmotion

# Memory entegrasyonu
from core.memory import get_memory_store, Episode, EpisodeType

from core.affect.social.empathy import (
    Empathy,
    EmpathyConfig,
    AgentState,
    EmpathyResult,
)

from core.affect.social.sympathy import (
    Sympathy,
    SympathyModuleConfig,
    SympathyConfig,
    SympathyResult,
    SympathyType,
    RelationshipContext,
)

from core.affect.social.trust import (
    Trust,
    TrustConfig,
    TrustLevel,
    TrustType,
    TrustProfile,
)


# ═══════════════════════════════════════════════════════════════════════════
# SYMPATHY → TRUST MAPPING
# ═══════════════════════════════════════════════════════════════════════════

SYMPATHY_TRUST_EFFECTS: Dict[SympathyType, Tuple[str, float]] = {
    SympathyType.COMPASSION: ("helped_emotionally", 0.15),
    SympathyType.EMPATHIC_JOY: ("shared_joy", 0.10),
    SympathyType.GRATITUDE: ("grateful_interaction", 0.12),
    SympathyType.EMPATHIC_SADNESS: ("shared_sorrow", 0.08),
    SympathyType.EMPATHIC_ANGER: ("defended_me", 0.18),
    SympathyType.PITY: ("condescending", -0.05),
    SympathyType.SCHADENFREUDE: ("enjoyed_misfortune", -0.20),
    SympathyType.ENVY: ("envied_success", -0.15),
}

SYMPATHY_TO_TRUST_EVENT: Dict[SympathyType, str] = {
    SympathyType.COMPASSION: "helped_me",
    SympathyType.EMPATHIC_JOY: "consistent_behavior",
    SympathyType.GRATITUDE: "honest_feedback",
    SympathyType.EMPATHIC_SADNESS: "consistent_behavior",
    SympathyType.EMPATHIC_ANGER: "defended_me",
    SympathyType.PITY: "unpredictable_behavior",
    SympathyType.SCHADENFREUDE: "harmed_me",
    SympathyType.ENVY: "unpredictable_behavior",
}


@dataclass
class SocialAffectResult:
    """Social affect işleminin entegre sonucu."""
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Modül sonuçları
    empathy: Optional[EmpathyResult] = None
    sympathy: Optional[SympathyResult] = None
    trust_before: float = 0.5
    trust_after: float = 0.5
    trust_profile: Optional[TrustProfile] = None
    
    # Türetilen değerler
    trust_delta: float = 0.0
    trust_level: TrustLevel = TrustLevel.MODERATE
    
    # PAD etkisi
    self_pad_before: Optional[PADState] = None
    self_pad_after: Optional[PADState] = None
    
    # StateVector referansı
    state_vector: Optional[StateVector] = None
    
    # Öneriler
    suggested_action: str = "observe"
    action_confidence: float = 0.5
    warnings: List[str] = field(default_factory=list)
    
    # Meta
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "empathy": self.empathy.to_dict() if self.empathy else None,
            "sympathy": self.sympathy.to_dict() if self.sympathy else None,
            "trust_before": self.trust_before,
            "trust_after": self.trust_after,
            "trust_delta": self.trust_delta,
            "trust_level": self.trust_level.value,
            "suggested_action": self.suggested_action,
            "action_confidence": self.action_confidence,
            "warnings": self.warnings,
            "state_vector_fields": {
                "empathy_total": self.state_vector.get(SVField.EMPATHY_TOTAL) if self.state_vector else None,
                "sympathy_level": self.state_vector.get(SVField.SYMPATHY_LEVEL) if self.state_vector else None,
                "trust_value": self.state_vector.get(SVField.TRUST_VALUE) if self.state_vector else None,
            },
        }
    
    def summary(self) -> str:
        """İnsan okunabilir özet."""
        parts = [f"Social Affect for {self.agent_id}:"]
        
        if self.empathy:
            parts.append(f"  Empathy: {self.empathy.total_empathy:.2f}")
        
        if self.sympathy:
            parts.append(f"  Sympathy: {self.sympathy.dominant_sympathy.value if self.sympathy.dominant_sympathy else 'none'}")
        
        parts.append(f"  Trust: {self.trust_before:.2f} → {self.trust_after:.2f} ({self.trust_delta:+.2f})")
        parts.append(f"  Action: {self.suggested_action} (conf: {self.action_confidence:.2f})")
        
        if self.state_vector:
            parts.append(f"  StateVector: empathy={self.state_vector.get(SVField.EMPATHY_TOTAL):.2f}, "
                        f"trust={self.state_vector.get(SVField.TRUST_VALUE):.2f}")
        
        if self.warnings:
            parts.append(f"  Warnings: {', '.join(self.warnings)}")
        
        return "\n".join(parts)


@dataclass
class OrchestratorConfig:
    """Orkestratör yapılandırması."""
    
    # Modül yapılandırmaları
    empathy_config: EmpathyConfig = field(default_factory=EmpathyConfig)
    sympathy_config: SympathyModuleConfig = field(default_factory=SympathyModuleConfig)
    trust_config: TrustConfig = field(default_factory=TrustConfig)
    
    # Trust güncelleme
    update_trust: bool = True
    trust_update_threshold: float = 0.3
    
    # StateVector entegrasyonu
    write_to_state_vector: bool = True  # Sonuçları SV'ye yaz
    read_from_state_vector: bool = True  # Self PAD'i SV'den oku
    
    # PAD güncelleme
    update_self_pad: bool = True
    pad_update_strength: float = 0.3
    
    # Aksiyon seçimi
    enable_action_suggestion: bool = True
    
    # Context
    default_empathy_context: str = "default"


class SocialAffectOrchestrator:
    """
    Social affect modüllerini koordine eden orkestratör.
    StateVector ile tam entegrasyon.
    """
    
    def __init__(
        self,
        self_state: PADState,
        config: Optional[OrchestratorConfig] = None,
        state_vector: Optional[StateVector] = None,
        bridge: Optional[StateVectorBridge] = None,
    ):
        """
        Args:
            self_state: Kendi PAD durumum
            config: Yapılandırma
            state_vector: Bağlı StateVector (opsiyonel)
            bridge: StateVectorBridge (opsiyonel)
        """
        self.self_state = self_state
        self.config = config or OrchestratorConfig()
        self.state_vector = state_vector
        self.bridge = bridge or get_state_bridge()

        # Modülleri oluştur
        self._empathy = Empathy(self_state, self.config.empathy_config)
        self._sympathy = Sympathy(self_state, self.config.sympathy_config)
        self._trust = Trust(self.config.trust_config)

        # Memory entegrasyonu
        self._memory = get_memory_store()

        # İstatistikler
        self._process_count = 0
        self._total_time_ms = 0.0
    
    @classmethod
    def from_state_vector(
        cls,
        state_vector: StateVector,
        config: Optional[OrchestratorConfig] = None,
        bridge: Optional[StateVectorBridge] = None,
    ) -> "SocialAffectOrchestrator":
        """
        StateVector'dan orchestrator oluştur.
        Self PAD otomatik olarak StateVector'dan okunur.
        
        Args:
            state_vector: Kaynak StateVector
            config: Yapılandırma
            bridge: StateVectorBridge
            
        Returns:
            Yeni SocialAffectOrchestrator
        """
        bridge = bridge or get_state_bridge()
        self_pad = bridge.read_self_pad(state_vector)
        
        orchestrator = cls(
            self_state=self_pad,
            config=config,
            state_vector=state_vector,
            bridge=bridge,
        )
        
        return orchestrator
    
    def process(
        self,
        agent: AgentState,
        relationship: Optional[RelationshipContext] = None,
        empathy_context: Optional[str] = None,
    ) -> SocialAffectResult:
        """
        Tam social affect işlemi.
        Sonuçlar otomatik olarak StateVector'a yazılır.
        
        Args:
            agent: Gözlemlenen ajan
            relationship: İlişki bağlamı
            empathy_context: Empati context'i
            
        Returns:
            SocialAffectResult
        """
        import time
        start_time = time.perf_counter()
        
        result = SocialAffectResult(agent_id=agent.agent_id)
        result.state_vector = self.state_vector
        result.self_pad_before = self.self_state
        
        # StateVector'dan self state oku (config'e göre)
        if self.config.read_from_state_vector and self.state_vector:
            self.self_state = self.bridge.read_self_pad(self.state_vector)
            self._empathy.update_self_state(self.self_state)
            self._sympathy.update_self_state(self.self_state)
        
        # 1. EMPATHY
        empathy_result = self._compute_empathy(agent, empathy_context)
        result.empathy = empathy_result
        
        # StateVector'a yaz
        if self.config.write_to_state_vector and self.state_vector:
            self.bridge.write_empathy(self.state_vector, empathy_result)
        
        # 2. SYMPATHY
        if relationship is None:
            relationship = self._infer_relationship(agent)
        
        sympathy_result = self._compute_sympathy(empathy_result, relationship)
        
        # Hostile/enemy için sympathy azalt
        if self._is_hostile(agent):
            sympathy_result = self._apply_hostile_sympathy_modifier(sympathy_result)
        
        result.sympathy = sympathy_result
        
        # StateVector'a yaz
        if self.config.write_to_state_vector and self.state_vector:
            self.bridge.write_sympathy(self.state_vector, sympathy_result)
        
        # 3. TRUST
        # Hostile/enemy için düşük başlangıç trust
        is_hostile = self._is_hostile(agent)
        if is_hostile:
            # İlk kez görüyorsak düşük trust ile başlat
            current_trust = self._trust.get(agent.agent_id)
            if current_trust == 0.5:  # Henüz etkileşim yok (default)
                self._trust.set_initial(agent.agent_id, TrustType.DISTRUST)
        
        result.trust_before = self._trust.get(agent.agent_id)
        
        if self.config.update_trust and sympathy_result.has_sympathy:
            self._update_trust(agent.agent_id, sympathy_result)
        
        result.trust_after = self._trust.get(agent.agent_id)
        result.trust_delta = result.trust_after - result.trust_before
        result.trust_level = self._trust.get_level(agent.agent_id)
        result.trust_profile = self._trust.get_profile(agent.agent_id)
        
        # StateVector'a yaz
        if self.config.write_to_state_vector and self.state_vector and result.trust_profile:
            self.bridge.write_trust(self.state_vector, result.trust_profile)
        
        # 4. PAD etkisi
        if self.config.update_self_pad and sympathy_result.combined_pad_effect:
            new_pad = self._compute_pad_effect(sympathy_result)
            result.self_pad_after = new_pad
            self.self_state = new_pad
            
            # StateVector'a yaz
            if self.config.write_to_state_vector and self.state_vector:
                self.bridge.write_pad(self.state_vector, new_pad)
        
        # 5. Aksiyon önerisi
        if self.config.enable_action_suggestion:
            action, confidence = self._suggest_action(
                empathy_result, sympathy_result, result.trust_level
            )
            result.suggested_action = action
            result.action_confidence = confidence
        
        # 6. Uyarılar
        result.warnings = self._generate_warnings(
            empathy_result, sympathy_result, result.trust_level
        )

        # 7. Episode kaydet (Memory entegrasyonu)
        self._store_interaction_episode(agent, result)

        # Meta
        result.processing_time_ms = (time.perf_counter() - start_time) * 1000

        self._process_count += 1
        self._total_time_ms += result.processing_time_ms

        return result
    
    def _compute_empathy(
        self,
        agent: AgentState,
        context: Optional[str] = None,
    ) -> EmpathyResult:
        """Empati hesapla."""
        ctx = context or self.config.default_empathy_context
        return self._empathy.compute(agent, context=ctx)
    
    def _compute_sympathy(
        self,
        empathy_result: EmpathyResult,
        relationship: RelationshipContext,
    ) -> SympathyResult:
        """Sempati hesapla."""
        return self._sympathy.compute(empathy_result, relationship)
    
    def _update_trust(
        self,
        agent_id: str,
        sympathy_result: SympathyResult,
    ) -> None:
        """Sempati sonucuna göre güveni güncelle."""
        if not sympathy_result.dominant_sympathy:
            return
        
        for response in sympathy_result.responses:
            if response.intensity < self.config.trust_update_threshold:
                continue
            
            event_type = SYMPATHY_TO_TRUST_EVENT.get(
                response.sympathy_type,
                "consistent_behavior"
            )
            
            self._trust.record(
                agent_id,
                event_type,
                context=f"sympathy:{response.sympathy_type.value}",
            )
    
    def _compute_pad_effect(
        self,
        sympathy_result: SympathyResult,
    ) -> PADState:
        """Sempati'nin kendi PAD'ime etkisini hesapla."""
        if not sympathy_result.combined_pad_effect:
            return self.self_state
        
        effect = sympathy_result.combined_pad_effect
        strength = self.config.pad_update_strength
        
        return PADState(
            pleasure=self.self_state.pleasure + (effect.pleasure * strength),
            arousal=self.self_state.arousal + (effect.arousal - 0.5) * strength,
            dominance=self.self_state.dominance + (effect.dominance - 0.5) * strength,
        )
    
    def _suggest_action(
        self,
        empathy: EmpathyResult,
        sympathy: SympathyResult,
        trust_level: TrustLevel,
    ) -> Tuple[str, float]:
        """Aksiyon önerisi."""
        if sympathy.dominant_sympathy:
            action = sympathy.get_action_tendency()
            
            trust_confidence_map = {
                TrustLevel.BLIND: 1.0,
                TrustLevel.HIGH: 0.9,
                TrustLevel.MODERATE: 0.7,
                TrustLevel.CAUTIOUS: 0.5,
                TrustLevel.LOW: 0.3,
                TrustLevel.DISTRUST: 0.1,
            }
            base_confidence = trust_confidence_map.get(trust_level, 0.5)
            empathy_factor = empathy.total_empathy
            confidence = (base_confidence * 0.6) + (empathy_factor * 0.4)
            
            return action, confidence
        
        return "observe", 0.3
    
    def _generate_warnings(
        self,
        empathy: EmpathyResult,
        sympathy: SympathyResult,
        trust_level: TrustLevel,
    ) -> List[str]:
        """Uyarı mesajları oluştur."""
        warnings = []
        
        if empathy.total_empathy < 0.3:
            warnings.append("Low empathy - limited understanding")
        
        if sympathy.is_antisocial():
            warnings.append(f"Antisocial sympathy detected: {sympathy.dominant_sympathy.value}")
        
        if trust_level in [TrustLevel.LOW, TrustLevel.DISTRUST]:
            warnings.append(f"Low trust level: {trust_level.value}")
        
        if trust_level in [TrustLevel.HIGH, TrustLevel.BLIND] and sympathy.is_antisocial():
            warnings.append("CONFLICT: High trust but antisocial feelings")
        
        return warnings
    
    def _is_hostile(self, agent: AgentState) -> bool:
        """Agent'ın hostile/enemy olup olmadığını kontrol et."""
        # Hardcoded hostile flag
        if hasattr(agent, 'hostile') and agent.hostile:
            return True
        
        # Attributes içinde hostile flag
        if hasattr(agent, 'attributes') and agent.attributes:
            if agent.attributes.get('hostile', False):
                return True
        
        # Relationship enemy ise
        if agent.relationship_to_self == "enemy":
            return True
        
        return False
    
    def _apply_hostile_sympathy_modifier(
        self, 
        sympathy_result: SympathyResult,
    ) -> SympathyResult:
        """
        Hostile agent için sympathy'yi azalt.
        Empathy sabit kalır (onu anlıyorum), ama sempati duymam.
        """
        HOSTILE_SYMPATHY_MODIFIER = 0.1  # %10'a düşür
        
        # Intensity'leri düşür
        for response in sympathy_result.responses:
            response.intensity *= HOSTILE_SYMPATHY_MODIFIER
        
        # Total intensity güncelle
        if sympathy_result.responses:
            sympathy_result.total_intensity = sum(
                r.intensity for r in sympathy_result.responses
            ) / len(sympathy_result.responses)
        else:
            sympathy_result.total_intensity = 0.0
        
        return sympathy_result
    
    def _infer_relationship(self, agent: AgentState) -> RelationshipContext:
        """
        Ajan bilgisinden ilişki bağlamı çıkar.

        Memory'den relationship record alır ve buna göre context oluşturur.
        """
        # Memory'den relationship record al
        relationship = self._memory.get_relationship(agent.agent_id)

        # Relationship type'a göre context oluştur
        rel_type = relationship.relationship_type.value

        if rel_type == "friend" or rel_type == "close_friend":
            return RelationshipContext.friend()
        elif rel_type == "family":
            return RelationshipContext(valence=0.8, positive_history=0.9)
        elif rel_type == "colleague":
            return RelationshipContext(valence=0.3, positive_history=0.5)
        elif rel_type == "rival":
            return RelationshipContext.rival()
        elif rel_type == "enemy":
            return RelationshipContext(valence=-0.7, negative_history=0.8)
        else:
            # Memory'deki sentiment'a göre context oluştur
            if relationship.total_interactions > 0:
                valence = relationship.overall_sentiment
                pos_ratio = relationship.positive_interactions / relationship.total_interactions
                return RelationshipContext(
                    valence=valence,
                    positive_history=pos_ratio,
                    negative_history=1 - pos_ratio,
                )
            # Agent'ın kendi bildirdiği relationship'e bak
            agent_rel_type = agent.relationship_to_self
            if agent_rel_type == "friend":
                return RelationshipContext.friend()
            elif agent_rel_type == "rival":
                return RelationshipContext.rival()
            elif agent_rel_type == "enemy":
                return RelationshipContext(valence=-0.7, negative_history=0.8)
            return RelationshipContext.stranger()

    def _store_interaction_episode(
        self,
        agent: AgentState,
        result: SocialAffectResult,
    ) -> None:
        """
        Etkileşimi episode olarak Memory'ye kaydet.

        Bu kayıt ileride:
        - Benzer durumları hatırlamak için
        - Relationship context oluşturmak için
        - Trust hesaplamak için kullanılacak
        """
        # Outcome valence hesapla - action'a göre
        outcome_valence = 0.0
        if result.suggested_action in ["help", "comfort", "support"]:
            outcome_valence = 0.5
        elif result.suggested_action in ["avoid", "withdraw"]:
            outcome_valence = -0.3
        elif result.suggested_action == "observe":
            outcome_valence = 0.0

        # Episode oluştur
        episode = Episode(
            what=f"Interaction with {agent.agent_id}",
            who=[agent.agent_id],
            episode_type=EpisodeType.INTERACTION,

            outcome=result.suggested_action,
            outcome_valence=outcome_valence,

            # Empathy'den duygu bilgisi
            self_emotion_during=(
                result.empathy.get_inferred_emotion().value
                if result.empathy else None
            ),

            # Sympathy'den duygusal valence
            emotional_valence=(
                result.sympathy.total_intensity
                if result.sympathy else 0.0
            ),

            # Importance - empathy ve trust'a göre
            importance=(
                result.empathy.total_empathy * 0.5 + abs(result.trust_delta) * 0.5
                if result.empathy else 0.5
            ),

            # PAD state
            pad_state=(
                {
                    "pleasure": result.self_pad_after.pleasure,
                    "arousal": result.self_pad_after.arousal,
                    "dominance": result.self_pad_after.dominance,
                }
                if result.self_pad_after else None
            ),
        )

        # Memory'ye kaydet
        self._memory.store_episode(episode)
    
    # ═══════════════════════════════════════════════════════════════════
    # BATCH & CONVENIENCE
    # ═══════════════════════════════════════════════════════════════════
    
    def process_batch(
        self,
        agents: List[AgentState],
        relationships: Optional[Dict[str, RelationshipContext]] = None,
    ) -> List[SocialAffectResult]:
        """Birden fazla ajanı işle."""
        results = []
        
        for agent in agents:
            rel = relationships.get(agent.agent_id) if relationships else None
            result = self.process(agent, rel)
            results.append(result)
        
        return results
    
    def quick_process(
        self,
        agent_id: str,
        emotion: BasicEmotion,
        relationship_type: str = "stranger",
    ) -> SocialAffectResult:
        """Hızlı işlem - minimal bilgiyle."""
        from core.affect.emotion.core import get_emotion_pad
        
        agent = AgentState(
            agent_id=agent_id,
            observed_pad=get_emotion_pad(emotion),
            relationship_to_self=relationship_type,
        )
        
        return self.process(agent)
    
    # ═══════════════════════════════════════════════════════════════════
    # STATE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def bind_state_vector(self, state_vector: StateVector) -> None:
        """StateVector bağla."""
        self.state_vector = state_vector
        # Self PAD'i güncelle
        if self.config.read_from_state_vector:
            self.self_state = self.bridge.read_self_pad(state_vector)
            self._empathy.update_self_state(self.self_state)
            self._sympathy.update_self_state(self.self_state)
    
    def update_self_state(self, new_state: PADState) -> None:
        """Kendi PAD durumumu güncelle."""
        self.self_state = new_state
        self._empathy.update_self_state(new_state)
        self._sympathy.update_self_state(new_state)
        
        # StateVector'a yaz
        if self.config.write_to_state_vector and self.state_vector:
            self.bridge.write_pad(self.state_vector, new_state)
    
    def get_trust_profile(self, agent_id: str) -> TrustProfile:
        """Ajan güven profilini getir."""
        return self._trust.get_profile(agent_id)
    
    def reset_trust(self, agent_id: str) -> None:
        """Ajan güvenini sıfırla."""
        self._trust.reset(agent_id)
    
    def get_state_vector_summary(self) -> Dict:
        """StateVector'dan affect özetini al."""
        if not self.state_vector:
            return {}
        return self.bridge.get_affect_summary(self.state_vector)
    
    @property
    def stats(self) -> Dict:
        """Orkestratör istatistikleri."""
        return {
            "process_count": self._process_count,
            "total_time_ms": self._total_time_ms,
            "avg_time_ms": self._total_time_ms / max(1, self._process_count),
            "trust_stats": self._trust.stats,
            "state_vector_bound": self.state_vector is not None,
        }


# ═══════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def create_orchestrator(
    self_pad: Optional[PADState] = None,
    state_vector: Optional[StateVector] = None,
    config: Optional[OrchestratorConfig] = None,
) -> SocialAffectOrchestrator:
    """Orkestratör oluştur."""
    if state_vector:
        return SocialAffectOrchestrator.from_state_vector(state_vector, config)
    
    pad = self_pad or PADState.neutral()
    return SocialAffectOrchestrator(pad, config)


def process_social_affect(
    agent: AgentState,
    state_vector: StateVector,
    relationship: Optional[RelationshipContext] = None,
) -> SocialAffectResult:
    """
    Tek seferlik social affect işlemi.
    StateVector otomatik güncellenir.
    """
    orchestrator = SocialAffectOrchestrator.from_state_vector(state_vector)
    return orchestrator.process(agent, relationship)
