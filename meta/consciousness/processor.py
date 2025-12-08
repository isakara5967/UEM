"""
UEM v2 - Consciousness Processor

Bilinc modulu ana islemcisi.
Awareness, Attention ve Global Workspace'i entegre eder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .types import (
    ConsciousnessLevel,
    AwarenessType,
    AwarenessState,
    AttentionFocus,
    AttentionMode,
    AttentionPriority,
    BroadcastType,
    WorkspaceContent,
    GlobalWorkspaceState,
    ConsciousExperience,
    Qualia,
)
from .awareness import AwarenessManager, AwarenessConfig
from .attention import AttentionController, AttentionConfig
from .integration import GlobalWorkspace, GlobalWorkspaceConfig


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ConsciousnessConfig:
    """Bilinc islemcisi yapilandirmasi."""
    # Alt modul konfigurasyonlari
    awareness_config: Optional[AwarenessConfig] = None
    attention_config: Optional[AttentionConfig] = None
    workspace_config: Optional[GlobalWorkspaceConfig] = None

    # Bilinc parametreleri
    consciousness_threshold: float = 0.5  # Bilinc icin min farkindalik
    experience_richness_threshold: float = 0.4  # Zengin deneyim esigi

    # Entegrasyon parametreleri
    auto_integrate: bool = True           # Otomatik entegrasyon
    auto_broadcast: bool = True           # Otomatik yayin

    # Zaman parametreleri
    experience_duration_ms: float = 1000.0  # Deneyim penceresi

    # Ozellikler
    generate_qualia: bool = True          # Oznel deneyim uret
    track_experiences: bool = True        # Deneyim gecmisi


# ============================================================================
# CONSCIOUSNESS OUTPUT
# ============================================================================

@dataclass
class ConsciousnessOutput:
    """Bilinc islemcisi ciktisi."""
    # Bilinc durumu
    consciousness_level: ConsciousnessLevel
    overall_awareness: float
    coherence: float

    # Dikkat
    current_focus: Optional[AttentionFocus] = None
    attention_mode: AttentionMode = AttentionMode.AUTOMATIC

    # Deneyim
    current_experience: Optional[ConsciousExperience] = None

    # Workspace
    active_contents_count: int = 0
    last_broadcast: Optional[WorkspaceContent] = None

    # Meta
    is_conscious: bool = True
    processing_time_ms: float = 0.0
    cycle_id: int = 0


# ============================================================================
# CONSCIOUSNESS PROCESSOR
# ============================================================================

class ConsciousnessProcessor:
    """
    Bilinc islemcisi.

    Tum bilinc alt modullerini koordine eder:
    - Awareness (farkindalik)
    - Attention (dikkat)
    - Global Workspace (entegrasyon ve yayin)

    Cikti: Butunlesik bilinc deneyimi
    """

    def __init__(self, config: Optional[ConsciousnessConfig] = None):
        """
        ConsciousnessProcessor baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or ConsciousnessConfig()

        # Alt modulleri olustur
        self.awareness_manager = AwarenessManager(self.config.awareness_config)
        self.attention_controller = AttentionController(self.config.attention_config)
        self.workspace = GlobalWorkspace(self.config.workspace_config)

        # Deneyim gecmisi
        self._experiences: List[ConsciousExperience] = []

        # Cycle sayaci
        self._cycle_count = 0

        # Istatistikler
        self._stats = {
            "process_calls": 0,
            "experiences_generated": 0,
            "attention_captures": 0,
            "broadcasts_processed": 0,
        }

    # ========================================================================
    # MAIN PROCESSING
    # ========================================================================

    def process(
        self,
        inputs: Optional[Dict[str, Any]] = None,
        time_delta_ms: float = 0.0,
    ) -> ConsciousnessOutput:
        """
        Bilinc islemi calistir.

        Args:
            inputs: Modullerden gelen girdiler
            time_delta_ms: Gecen sure (ms)

        Returns:
            ConsciousnessOutput
        """
        start_time = datetime.now()
        self._cycle_count += 1
        self._stats["process_calls"] += 1

        inputs = inputs or {}

        # 1. Zaman bazli decay/update
        if time_delta_ms > 0:
            self._apply_time_effects(time_delta_ms)

        # 2. Girdileri workspace'e ekle
        self._process_inputs(inputs)

        # 3. Dikkat guncelle
        self._update_attention()

        # 4. Farkindalik guncelle
        self._update_awareness(inputs)

        # 5. Workspace cycle
        workspace_result = {}
        if self.config.auto_integrate:
            workspace_result = self.workspace.process_cycle()

        # 6. Bilinc deneyimi olustur
        experience = None
        if self.config.generate_qualia:
            experience = self._generate_experience()
            if experience:
                self._stats["experiences_generated"] += 1

        # 7. Bilinc seviyesi ve tutarlilik
        consciousness_level = self.awareness_manager.get_consciousness_level()
        overall_awareness = self.awareness_manager.get_overall_awareness()
        coherence = self._calculate_coherence()

        # Cikti olustur
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return ConsciousnessOutput(
            consciousness_level=consciousness_level,
            overall_awareness=overall_awareness,
            coherence=coherence,
            current_focus=self.attention_controller.get_current_focus(),
            attention_mode=self.attention_controller.get_mode(),
            current_experience=experience,
            active_contents_count=len(self.workspace.get_active_contents()),
            last_broadcast=self._get_last_broadcast(),
            is_conscious=self.awareness_manager.is_conscious(),
            processing_time_ms=processing_time,
            cycle_id=self._cycle_count,
        )

    # ========================================================================
    # INPUT PROCESSING
    # ========================================================================

    def _process_inputs(self, inputs: Dict[str, Any]) -> None:
        """Girdileri isleyerek workspace'e ekle."""
        # Perception girdileri
        if "perception" in inputs:
            self._submit_perception(inputs["perception"])

        # Cognition girdileri
        if "cognition" in inputs:
            self._submit_cognition(inputs["cognition"])

        # Affect girdileri
        if "affect" in inputs:
            self._submit_affect(inputs["affect"])

        # Memory girdileri
        if "memory" in inputs:
            self._submit_memory(inputs["memory"])

        # Decision girdileri
        if "decision" in inputs:
            self._submit_decision(inputs["decision"])

        # Direct content
        if "content" in inputs:
            self._submit_direct_content(inputs["content"])

    def _submit_perception(self, perception_data: Dict[str, Any]) -> None:
        """Algi verisini workspace'e gonder."""
        priority = AttentionPriority.NORMAL
        if perception_data.get("threat", 0) > 0.7:
            priority = AttentionPriority.CRITICAL
        elif perception_data.get("salience", 0) > 0.7:
            priority = AttentionPriority.HIGH

        self.workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload=perception_data,
            summary=perception_data.get("summary", "Perception input"),
            priority=priority,
            relevance=perception_data.get("relevance", 0.5),
            urgency=perception_data.get("urgency", 0.3),
            novelty=perception_data.get("novelty", 0.5),
        )

    def _submit_cognition(self, cognition_data: Dict[str, Any]) -> None:
        """Bilissel veriyi workspace'e gonder."""
        self.workspace.submit_content(
            content_type=BroadcastType.COGNITION,
            source_module="cognition",
            payload=cognition_data,
            summary=cognition_data.get("summary", "Cognition result"),
            priority=AttentionPriority.NORMAL,
            relevance=cognition_data.get("relevance", 0.6),
            urgency=cognition_data.get("urgency", 0.3),
            novelty=cognition_data.get("novelty", 0.4),
        )

    def _submit_affect(self, affect_data: Dict[str, Any]) -> None:
        """Duygusal veriyi workspace'e gonder."""
        # Yuksek arousal = yuksek oncelik
        arousal = affect_data.get("arousal", 0.5)
        priority = AttentionPriority.HIGH if arousal > 0.7 else AttentionPriority.NORMAL

        self.workspace.submit_content(
            content_type=BroadcastType.AFFECT,
            source_module="affect",
            payload=affect_data,
            summary=affect_data.get("summary", "Emotional state"),
            priority=priority,
            relevance=affect_data.get("relevance", 0.5),
            urgency=arousal,  # Arousal aciliyet olarak
            novelty=affect_data.get("novelty", 0.3),
        )

    def _submit_memory(self, memory_data: Dict[str, Any]) -> None:
        """Bellek verisini workspace'e gonder."""
        self.workspace.submit_content(
            content_type=BroadcastType.MEMORY,
            source_module="memory",
            payload=memory_data,
            summary=memory_data.get("summary", "Memory retrieval"),
            priority=AttentionPriority.NORMAL,
            relevance=memory_data.get("relevance", 0.7),
            urgency=memory_data.get("urgency", 0.2),
            novelty=memory_data.get("novelty", 0.3),
        )

    def _submit_decision(self, decision_data: Dict[str, Any]) -> None:
        """Karar verisini workspace'e gonder."""
        self.workspace.submit_content(
            content_type=BroadcastType.DECISION,
            source_module="executive",
            payload=decision_data,
            summary=decision_data.get("summary", "Decision"),
            priority=AttentionPriority.HIGH,
            relevance=0.8,
            urgency=decision_data.get("urgency", 0.5),
            novelty=0.6,
        )

    def _submit_direct_content(self, content_data: Dict[str, Any]) -> None:
        """Direkt icerik gonder."""
        content_type = BroadcastType(content_data.get("type", "perception"))
        self.workspace.submit_content(
            content_type=content_type,
            source_module=content_data.get("source", "unknown"),
            payload=content_data.get("payload", {}),
            summary=content_data.get("summary", ""),
            priority=AttentionPriority(content_data.get("priority", "normal")),
            relevance=content_data.get("relevance", 0.5),
            urgency=content_data.get("urgency", 0.3),
            novelty=content_data.get("novelty", 0.5),
        )

    # ========================================================================
    # ATTENTION
    # ========================================================================

    def _update_attention(self) -> None:
        """Dikkati guncelle."""
        # Timeout kontrolu
        if self.attention_controller.check_timeout():
            pass  # Odak serbest kaldi

        # En yuksek skorlu icerik dikkati yakalasin mi?
        top_contents = self.workspace.get_top_competitors(3)
        for content in top_contents:
            if content.priority == AttentionPriority.CRITICAL:
                if self.attention_controller.capture_attention(content, force=True):
                    self._stats["attention_captures"] += 1
                    break
            elif content.competition_score > 0.7:
                if self.attention_controller.capture_attention(content):
                    self._stats["attention_captures"] += 1
                    break

    def focus_on(
        self,
        target_type: str,
        target_id: Optional[str] = None,
        target_description: str = "",
        priority: AttentionPriority = AttentionPriority.NORMAL,
    ) -> Optional[AttentionFocus]:
        """Belirli bir hedefe odaklan."""
        return self.attention_controller.focus_on(
            target_type=target_type,
            target_id=target_id,
            target_description=target_description,
            priority=priority,
        )

    def release_attention(self) -> None:
        """Dikkati serbest birak."""
        self.attention_controller.release_focus()

    # ========================================================================
    # AWARENESS
    # ========================================================================

    def _update_awareness(self, inputs: Dict[str, Any]) -> None:
        """Farkindaligi guncelle."""
        # Input bazli farkindalik guncellemesi
        if "perception" in inputs:
            self.awareness_manager.boost_awareness(AwarenessType.SENSORY, 0.1)

        if "cognition" in inputs:
            self.awareness_manager.boost_awareness(AwarenessType.COGNITIVE, 0.1)

        if "affect" in inputs:
            self.awareness_manager.boost_awareness(AwarenessType.EMOTIONAL, 0.1)

        if "social" in inputs:
            self.awareness_manager.boost_awareness(AwarenessType.SOCIAL, 0.1)

        # Self-awareness her zaman biraz artsin
        self.awareness_manager.boost_awareness(AwarenessType.SELF, 0.02)

        # Meta-awareness check
        if self.awareness_manager.config.enable_meta_awareness:
            self.awareness_manager.boost_awareness(AwarenessType.META, 0.01)

    def update_awareness(
        self,
        awareness_type: AwarenessType,
        level: float,
        focus: Optional[str] = None,
    ) -> AwarenessState:
        """Belirli bir farkindalik turunu guncelle."""
        return self.awareness_manager.update_awareness(
            awareness_type=awareness_type,
            level=level,
            focus=focus,
        )

    # ========================================================================
    # TIME EFFECTS
    # ========================================================================

    def _apply_time_effects(self, duration_ms: float) -> None:
        """Zaman etkilerini uygula."""
        hours = duration_ms / (1000 * 3600)

        # Farkindalik decay
        self.awareness_manager.apply_decay(hours)

        # Dikkat decay
        self.attention_controller.apply_decay(duration_ms)

    # ========================================================================
    # EXPERIENCE GENERATION
    # ========================================================================

    def _generate_experience(self) -> Optional[ConsciousExperience]:
        """Bilinc deneyimi olustur."""
        if not self.awareness_manager.is_conscious():
            return None

        # Temel deneyim
        experience = ConsciousExperience(
            level=self.awareness_manager.get_consciousness_level(),
            clarity=self.awareness_manager.get_overall_awareness(),
            unity=self._calculate_unity(),
            attention_focus=self.attention_controller.get_current_focus(),
            self_awareness_level=self.awareness_manager.get_awareness_level(AwarenessType.SELF),
            meta_awareness_level=self.awareness_manager.get_awareness_level(AwarenessType.META),
            cycle_id=self._cycle_count,
        )

        # Qualia ekle (oznel deneyimler)
        self._add_qualia_to_experience(experience)

        # Bilissel icerikler ekle
        self._add_cognitive_contents(experience)

        # Duygusal ton ekle
        self._add_emotional_tone(experience)

        # Gecmise ekle
        if self.config.track_experiences:
            self._experiences.append(experience)
            if len(self._experiences) > 100:
                self._experiences.pop(0)

        return experience

    def _add_qualia_to_experience(self, experience: ConsciousExperience) -> None:
        """Deneyime qualia ekle."""
        # Aktif iceriklerden qualia uret
        for content in self.workspace.get_active_contents():
            if content.status.value in ("integrated", "broadcast"):
                qualia = Qualia(
                    modality=content.content_type.value,
                    quality=content.summary,
                    content=content.payload,
                    intensity=content.relevance,
                    valence=content.payload.get("valence", 0.0),
                    salience=content.novelty,
                    source_stimulus=content.source_module,
                )
                experience.add_qualia(qualia)

    def _add_cognitive_contents(self, experience: ConsciousExperience) -> None:
        """Deneyime bilissel icerikler ekle."""
        cognition_contents = self.workspace.get_contents_by_type(BroadcastType.COGNITION)
        for content in cognition_contents:
            if content.summary:
                experience.cognitive_contents.append(content.summary)

    def _add_emotional_tone(self, experience: ConsciousExperience) -> None:
        """Deneyime duygusal ton ekle."""
        affect_contents = self.workspace.get_contents_by_type(BroadcastType.AFFECT)
        for content in affect_contents:
            if "valence" in content.payload:
                experience.emotional_tone["valence"] = content.payload["valence"]
            if "arousal" in content.payload:
                experience.emotional_tone["arousal"] = content.payload["arousal"]

    # ========================================================================
    # COHERENCE & UNITY
    # ========================================================================

    def _calculate_coherence(self) -> float:
        """Tutarlilik hesapla."""
        # Workspace catisma sayisi
        conflict_factor = 1.0 - min(1.0, self.workspace.state.conflict_count * 0.1)

        # Farkindalik tutarliligi
        awareness_levels = [
            s.level for s in self.awareness_manager.awareness_states.values()
        ]
        awareness_variance = 0.0
        if awareness_levels:
            mean = sum(awareness_levels) / len(awareness_levels)
            awareness_variance = sum((l - mean) ** 2 for l in awareness_levels) / len(awareness_levels)
        awareness_coherence = 1.0 - min(1.0, awareness_variance)

        return (conflict_factor + awareness_coherence) / 2

    def _calculate_unity(self) -> float:
        """Birlestiricilik hesapla."""
        # Entegre icerik orani
        total = len(self.workspace.get_active_contents())
        if total == 0:
            return 0.5

        integrated = sum(
            1 for c in self.workspace.get_active_contents()
            if c.status.value in ("integrated", "broadcast")
        )

        integration_ratio = integrated / total

        # Dikkat odagi var mi?
        focus_factor = 1.0 if self.attention_controller.is_focused() else 0.5

        return (integration_ratio + focus_factor) / 2

    # ========================================================================
    # BROADCAST
    # ========================================================================

    def _get_last_broadcast(self) -> Optional[WorkspaceContent]:
        """Son yayini getir."""
        history = self.workspace.get_broadcast_history(1)
        return history[0] if history else None

    def broadcast_content(self, content: WorkspaceContent) -> bool:
        """Icerigi yayin yap."""
        result = self.workspace.broadcast(content.id)
        if result:
            self._stats["broadcasts_processed"] += 1
        return result

    def register_broadcast_listener(
        self,
        module_name: str,
        callback: Callable[[WorkspaceContent], None],
        content_types: Optional[List[BroadcastType]] = None,
    ) -> str:
        """Yayin dinleyicisi kaydet."""
        return self.workspace.register_listener(
            module_name=module_name,
            callback=callback,
            content_types=content_types,
        )

    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================

    def is_conscious(self) -> bool:
        """Agent bilinc durumunda mi?"""
        return self.awareness_manager.is_conscious()

    def get_consciousness_level(self) -> ConsciousnessLevel:
        """Bilinc seviyesini getir."""
        return self.awareness_manager.get_consciousness_level()

    def get_overall_awareness(self) -> float:
        """Genel farkindaligi getir."""
        return self.awareness_manager.get_overall_awareness()

    def get_current_focus(self) -> Optional[AttentionFocus]:
        """Mevcut odagi getir."""
        return self.attention_controller.get_current_focus()

    def get_experiences(self, limit: int = 10) -> List[ConsciousExperience]:
        """Son deneyimleri getir."""
        return self._experiences[-limit:]

    # ========================================================================
    # STATISTICS & STATE
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Tum istatistikleri getir."""
        return {
            "processor": self._stats.copy(),
            "awareness": self.awareness_manager.get_stats(),
            "attention": self.attention_controller.get_stats(),
            "workspace": self.workspace.get_stats(),
        }

    def summary(self) -> Dict[str, Any]:
        """Genel ozet."""
        return {
            "consciousness_level": self.awareness_manager.get_consciousness_level().value,
            "is_conscious": self.is_conscious(),
            "overall_awareness": self.get_overall_awareness(),
            "coherence": self._calculate_coherence(),
            "attention": self.attention_controller.summary(),
            "awareness": self.awareness_manager.summary(),
            "workspace": self.workspace.summary(),
            "experience_count": len(self._experiences),
            "cycle_count": self._cycle_count,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_consciousness_processor(
    config: Optional[ConsciousnessConfig] = None,
) -> ConsciousnessProcessor:
    """ConsciousnessProcessor factory."""
    return ConsciousnessProcessor(config)


def get_consciousness_processor() -> ConsciousnessProcessor:
    """Singleton benzeri global processor."""
    if not hasattr(get_consciousness_processor, "_instance"):
        get_consciousness_processor._instance = ConsciousnessProcessor()
    return get_consciousness_processor._instance


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ConsciousnessConfig",
    "ConsciousnessOutput",
    "ConsciousnessProcessor",
    "create_consciousness_processor",
    "get_consciousness_processor",
]
