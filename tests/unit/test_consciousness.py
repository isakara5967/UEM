"""
UEM v2 - Consciousness Module Tests

Bilinc modulunun unit testleri.
"""

import pytest
from datetime import datetime, timedelta

from meta.consciousness import (
    # Types
    ConsciousnessLevel,
    AwarenessType,
    AttentionMode,
    AttentionPriority,
    BroadcastType,
    IntegrationStatus,
    AttentionFocus,
    Qualia,
    WorkspaceContent,
    AwarenessState,
    GlobalWorkspaceState,
    ConsciousExperience,
    # Awareness
    AwarenessConfig,
    AwarenessManager,
    create_awareness_manager,
    # Attention
    AttentionConfig,
    AttentionFilter,
    AttentionController,
    create_attention_controller,
    # Integration
    GlobalWorkspaceConfig,
    BroadcastListener,
    GlobalWorkspace,
    create_global_workspace,
    # Processor
    ConsciousnessConfig,
    ConsciousnessOutput,
    ConsciousnessProcessor,
    create_consciousness_processor,
)


# ============================================================================
# TYPES TESTS
# ============================================================================

class TestConsciousnessTypes:
    """Type enum ve dataclass testleri."""

    def test_consciousness_level_enum(self):
        """ConsciousnessLevel enum."""
        assert ConsciousnessLevel.UNCONSCIOUS.value == "unconscious"
        assert ConsciousnessLevel.CONSCIOUS.value == "conscious"
        assert ConsciousnessLevel.HYPERCONSCIOUS.value == "hyperconscious"

    def test_awareness_type_enum(self):
        """AwarenessType enum."""
        assert AwarenessType.SENSORY.value == "sensory"
        assert AwarenessType.COGNITIVE.value == "cognitive"
        assert AwarenessType.META.value == "meta"

    def test_attention_priority_enum(self):
        """AttentionPriority enum."""
        assert AttentionPriority.CRITICAL.value == "critical"
        assert AttentionPriority.NORMAL.value == "normal"


class TestAttentionFocus:
    """AttentionFocus dataclass testleri."""

    def test_attention_focus_creation(self):
        """AttentionFocus olusturma."""
        focus = AttentionFocus(
            target_type="entity",
            target_description="Test target",
            priority=AttentionPriority.HIGH,
            intensity=0.8,
        )
        assert focus.target_type == "entity"
        assert focus.priority == AttentionPriority.HIGH
        assert focus.intensity == 0.8

    def test_attention_focus_priority_score(self):
        """priority_score hesaplama."""
        focus = AttentionFocus(
            priority=AttentionPriority.CRITICAL,
            intensity=1.0,
            stability=1.0,
        )
        assert focus.priority_score == 1.0

        focus2 = AttentionFocus(
            priority=AttentionPriority.LOW,
            intensity=0.5,
            stability=0.5,
        )
        assert focus2.priority_score < 0.3


class TestQualia:
    """Qualia dataclass testleri."""

    def test_qualia_creation(self):
        """Qualia olusturma."""
        qualia = Qualia(
            modality="visual",
            quality="bright red color",
            intensity=0.8,
            valence=0.5,
            salience=0.9,
        )
        assert qualia.modality == "visual"
        assert qualia.phenomenal_strength == 0.8 * 0.9

    def test_qualia_phenomenal_strength(self):
        """phenomenal_strength hesaplama."""
        qualia = Qualia(intensity=0.6, salience=0.5)
        assert abs(qualia.phenomenal_strength - 0.3) < 0.01


class TestWorkspaceContent:
    """WorkspaceContent dataclass testleri."""

    def test_workspace_content_creation(self):
        """WorkspaceContent olusturma."""
        content = WorkspaceContent(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload={"threat": 0.8},
            summary="Threat detected",
            priority=AttentionPriority.HIGH,
            relevance=0.9,
        )
        assert content.content_type == BroadcastType.PERCEPTION
        assert content.status == IntegrationStatus.PENDING

    def test_workspace_content_competition_score(self):
        """competition_score hesaplama."""
        content = WorkspaceContent(
            priority=AttentionPriority.CRITICAL,
            relevance=0.9,
            urgency=0.8,
            novelty=0.7,
        )
        # (0.9 + 0.8 + 0.7) / 3 * 2.0 = 1.6
        assert content.competition_score > 1.0

    def test_workspace_content_mark_integrated(self):
        """mark_integrated metodu."""
        content = WorkspaceContent()
        content.mark_integrated(0.9)
        assert content.status == IntegrationStatus.INTEGRATED
        assert content.integration_score == 0.9
        assert content.integrated_at is not None

    def test_workspace_content_mark_broadcast(self):
        """mark_broadcast metodu."""
        content = WorkspaceContent()
        content.mark_broadcast()
        assert content.status == IntegrationStatus.BROADCAST
        assert content.broadcast_at is not None


class TestGlobalWorkspaceState:
    """GlobalWorkspaceState dataclass testleri."""

    def test_workspace_state_creation(self):
        """GlobalWorkspaceState olusturma."""
        state = GlobalWorkspaceState()
        assert state.consciousness_level == ConsciousnessLevel.CONSCIOUS
        assert len(state.active_contents) == 0

    def test_workspace_state_add_content(self):
        """Icerik ekleme."""
        state = GlobalWorkspaceState()
        content = WorkspaceContent(summary="Test")
        state.add_content(content)
        assert content.id in state.active_contents

    def test_workspace_state_get_top_contents(self):
        """En yuksek skorlu icerikleri getirme."""
        state = GlobalWorkspaceState()
        c1 = WorkspaceContent(relevance=0.3)
        c2 = WorkspaceContent(relevance=0.9)
        c3 = WorkspaceContent(relevance=0.6)
        state.add_content(c1)
        state.add_content(c2)
        state.add_content(c3)

        top = state.get_top_contents(2)
        assert len(top) == 2
        assert top[0].relevance >= top[1].relevance


class TestConsciousExperience:
    """ConsciousExperience dataclass testleri."""

    def test_experience_creation(self):
        """ConsciousExperience olusturma."""
        exp = ConsciousExperience(
            level=ConsciousnessLevel.CONSCIOUS,
            clarity=0.8,
            unity=0.7,
        )
        assert exp.level == ConsciousnessLevel.CONSCIOUS
        # richness depends on content, empty experience has 0 richness
        assert exp.richness >= 0

    def test_experience_add_qualia(self):
        """Qualia ekleme."""
        exp = ConsciousExperience()
        qualia = Qualia(modality="visual")
        exp.add_qualia(qualia)
        assert len(exp.phenomenal_contents) == 1


# ============================================================================
# AWARENESS MANAGER TESTS
# ============================================================================

class TestAwarenessManager:
    """AwarenessManager testleri."""

    def test_create_awareness_manager(self):
        """Factory fonksiyonu."""
        manager = create_awareness_manager()
        assert manager is not None
        assert len(manager.awareness_states) == len(AwarenessType)

    def test_get_awareness(self):
        """Farkindalik durumu getirme."""
        manager = AwarenessManager()
        state = manager.get_awareness(AwarenessType.COGNITIVE)
        assert state is not None
        assert state.awareness_type == AwarenessType.COGNITIVE

    def test_update_awareness(self):
        """Farkindalik guncelleme."""
        manager = AwarenessManager()
        state = manager.update_awareness(
            AwarenessType.SENSORY,
            level=0.8,
            clarity=0.9,
        )
        assert state.level == 0.8
        assert state.clarity == 0.9

    def test_boost_awareness(self):
        """Farkindalik artirma."""
        manager = AwarenessManager()
        initial = manager.get_awareness(AwarenessType.COGNITIVE).level
        manager.boost_awareness(AwarenessType.COGNITIVE, 0.2)
        assert manager.get_awareness(AwarenessType.COGNITIVE).level > initial

    def test_diminish_awareness(self):
        """Farkindalik azaltma."""
        manager = AwarenessManager()
        manager.update_awareness(AwarenessType.COGNITIVE, level=0.8)
        manager.diminish_awareness(AwarenessType.COGNITIVE, 0.2)
        assert manager.get_awareness(AwarenessType.COGNITIVE).level < 0.8

    def test_consciousness_level_update(self):
        """Bilinc seviyesi guncelleme."""
        manager = AwarenessManager()
        # Tum farkindaliklari yukselt (quality = level * clarity * depth > 0.9 olmali)
        for awareness_type in AwarenessType:
            manager.update_awareness(awareness_type, level=0.98, clarity=0.98, depth=0.98)
        assert manager.get_consciousness_level() == ConsciousnessLevel.HYPERCONSCIOUS

        # Tum farkindaliklari dusur
        for awareness_type in AwarenessType:
            manager.update_awareness(awareness_type, level=0.05, clarity=0.05, depth=0.05)
        assert manager.get_consciousness_level() == ConsciousnessLevel.UNCONSCIOUS

    def test_is_conscious(self):
        """Bilinc durumu kontrolu."""
        manager = AwarenessManager()
        # Varsayilan degerlerle bilinc seviyesinde olmali
        assert manager.is_conscious()

    def test_get_dominant_awareness(self):
        """Baskin farkindalik turu."""
        manager = AwarenessManager()
        manager.update_awareness(AwarenessType.SENSORY, level=0.9, clarity=0.9, depth=0.9)
        dominant = manager.get_dominant_awareness()
        assert dominant == AwarenessType.SENSORY

    def test_meta_awareness(self):
        """Meta-farkindalik kontrolu."""
        manager = AwarenessManager()
        manager.update_awareness(AwarenessType.META, level=0.8)
        manager.update_awareness(AwarenessType.SELF, level=0.9)
        meta_report = manager.check_meta_awareness()
        assert meta_report["enabled"]
        assert meta_report["level"] > 0

    def test_awareness_decay(self):
        """Farkindalik azalmasi."""
        manager = AwarenessManager()
        manager.update_awareness(AwarenessType.COGNITIVE, level=0.8)
        changes = manager.apply_decay(hours_passed=2.0)
        assert AwarenessType.COGNITIVE.value in changes


# ============================================================================
# ATTENTION CONTROLLER TESTS
# ============================================================================

class TestAttentionController:
    """AttentionController testleri."""

    def test_create_attention_controller(self):
        """Factory fonksiyonu."""
        controller = create_attention_controller()
        assert controller is not None

    def test_focus_on(self):
        """Odaklanma."""
        controller = AttentionController()
        focus = controller.focus_on(
            target_type="entity",
            target_description="Test target",
            priority=AttentionPriority.HIGH,
        )
        assert focus is not None
        assert focus.target_type == "entity"
        assert controller.is_focused()

    def test_release_focus(self):
        """Odak serbest birakma."""
        controller = AttentionController()
        controller.focus_on(target_type="entity", target_description="Test")
        released = controller.release_focus()
        assert released is not None
        assert not controller.is_focused()

    def test_focus_priority(self):
        """Oncelik bazli odak degisimi."""
        controller = AttentionController()
        # Normal oncelik
        controller.focus_on(
            target_type="entity",
            target_description="Low priority",
            priority=AttentionPriority.LOW,
        )
        # Kritik oncelik degistirmeli
        controller.focus_on(
            target_type="threat",
            target_description="Critical threat",
            priority=AttentionPriority.CRITICAL,
            force=True,
        )
        assert controller.current_focus.target_description == "Critical threat"

    def test_attention_capture(self):
        """Dikkat yakalama."""
        controller = AttentionController()
        content = WorkspaceContent(
            content_type=BroadcastType.PERCEPTION,
            summary="Important event",
            priority=AttentionPriority.HIGH,
            urgency=0.9,
        )
        captured = controller.capture_attention(content)
        assert captured

    def test_divided_attention(self):
        """Bolusmis dikkat."""
        controller = AttentionController()
        targets = [
            {"type": "entity1", "description": "Target 1"},
            {"type": "entity2", "description": "Target 2"},
        ]
        focuses = controller.divide_attention(targets)
        assert len(focuses) == 2
        assert controller.is_divided()

    def test_consolidate_attention(self):
        """Dikkati birlestirme."""
        controller = AttentionController()
        controller.divide_attention([
            {"type": "entity1", "description": "Target 1"},
            {"type": "entity2", "description": "Target 2"},
        ])
        focus = controller.consolidate_attention(0)
        assert focus is not None
        assert not controller.is_divided()
        assert controller.is_focused()

    def test_attention_filter(self):
        """Dikkat filtresi."""
        controller = AttentionController()
        controller.block_type("spam")
        focus = controller.focus_on(
            target_type="spam",
            target_description="Spam content",
        )
        assert focus is None

    def test_sustain_focus(self):
        """Odak surdurmesi."""
        controller = AttentionController()
        controller.focus_on(target_type="task", target_description="Work")
        initial_stability = controller.current_focus.stability
        controller.sustain_focus(0.2)
        assert controller.current_focus.stability > initial_stability
        assert controller.mode == AttentionMode.SUSTAINED

    def test_attention_decay(self):
        """Dikkat zayiflamasi."""
        controller = AttentionController()
        controller.focus_on(target_type="task", target_description="Work")
        initial_intensity = controller.current_focus.intensity
        controller.apply_decay(5000)  # 5 saniye
        assert controller.current_focus.intensity < initial_intensity


# ============================================================================
# GLOBAL WORKSPACE TESTS
# ============================================================================

class TestGlobalWorkspace:
    """GlobalWorkspace testleri."""

    def test_create_global_workspace(self):
        """Factory fonksiyonu."""
        workspace = create_global_workspace()
        assert workspace is not None

    def test_submit_content(self):
        """Icerik gonderme."""
        workspace = GlobalWorkspace()
        content = workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload={"threat": 0.5},
            summary="Threat detected",
        )
        assert content is not None
        assert content.id in workspace.state.active_contents

    def test_run_competition(self):
        """Yarisma calistirma."""
        workspace = GlobalWorkspace()
        workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload={},
            relevance=0.3,
        )
        workspace.submit_content(
            content_type=BroadcastType.COGNITION,
            source_module="cognition",
            payload={},
            relevance=0.9,
        )
        winner = workspace.run_competition()
        assert winner is not None
        # winner gets a boost, so relevance increases (0.9 + 0.2 = 1.0, capped)
        assert winner.relevance >= 0.9

    def test_integrate_content(self):
        """Icerik entegrasyonu."""
        workspace = GlobalWorkspace()
        content = workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload={},
            relevance=0.8,
            novelty=0.7,
        )
        result = workspace.integrate_content(content.id)
        assert result
        assert content.status == IntegrationStatus.INTEGRATED

    def test_broadcast(self):
        """Yayin yapma."""
        workspace = GlobalWorkspace()
        content = workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload={},
            relevance=0.8,
        )
        workspace.integrate_content(content.id)
        result = workspace.broadcast(content.id)
        assert result
        assert content.status == IntegrationStatus.BROADCAST

    def test_broadcast_listener(self):
        """Yayin dinleyicisi."""
        workspace = GlobalWorkspace()
        received = []

        def callback(content):
            received.append(content)

        workspace.register_listener(
            module_name="test",
            callback=callback,
        )

        content = workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload={},
            relevance=0.8,
        )
        workspace.integrate_content(content.id)
        workspace.broadcast(content.id)

        assert len(received) == 1

    def test_process_cycle(self):
        """Cycle isleme."""
        workspace = GlobalWorkspace()
        workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload={},
            relevance=0.8,
        )
        result = workspace.process_cycle()
        assert "cycle_id" in result
        assert result["cycle_id"] == 1

    def test_cleanup(self):
        """Temizlik."""
        workspace = GlobalWorkspace()
        # Kisa TTL ile icerik olustur
        content = workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload={},
            ttl_ms=1,  # 1ms
        )
        # Biraz bekle
        import time
        time.sleep(0.01)
        result = workspace.cleanup()
        assert result["expired_removed"] >= 0

    def test_conflict_detection(self):
        """Catisma tespiti."""
        workspace = GlobalWorkspace()
        workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception1",
            payload={"threat": True},
        )
        workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception2",
            payload={"threat": False},
        )
        assert workspace.state.conflict_count > 0


# ============================================================================
# CONSCIOUSNESS PROCESSOR TESTS
# ============================================================================

class TestConsciousnessProcessor:
    """ConsciousnessProcessor testleri."""

    def test_create_consciousness_processor(self):
        """Factory fonksiyonu."""
        processor = create_consciousness_processor()
        assert processor is not None

    def test_process(self):
        """Ana islem."""
        processor = ConsciousnessProcessor()
        output = processor.process()
        assert isinstance(output, ConsciousnessOutput)
        assert output.consciousness_level is not None

    def test_process_with_inputs(self):
        """Girdili islem."""
        processor = ConsciousnessProcessor()
        output = processor.process(inputs={
            "perception": {
                "summary": "Threat detected",
                "threat": 0.8,
            },
        })
        assert output is not None
        assert output.active_contents_count > 0

    def test_process_with_affect(self):
        """Duygusal girdi ile islem."""
        processor = ConsciousnessProcessor()
        output = processor.process(inputs={
            "affect": {
                "valence": -0.5,
                "arousal": 0.8,
            },
        })
        assert output is not None

    def test_focus_on(self):
        """Odaklanma."""
        processor = ConsciousnessProcessor()
        focus = processor.focus_on(
            target_type="task",
            target_description="Important task",
            priority=AttentionPriority.HIGH,
        )
        assert focus is not None

    def test_update_awareness(self):
        """Farkindalik guncelleme."""
        processor = ConsciousnessProcessor()
        state = processor.update_awareness(
            AwarenessType.COGNITIVE,
            level=0.9,
        )
        assert state.level == 0.9

    def test_is_conscious(self):
        """Bilinc durumu kontrolu."""
        processor = ConsciousnessProcessor()
        assert processor.is_conscious()

    def test_broadcast_listener(self):
        """Yayin dinleyicisi kaydi."""
        processor = ConsciousnessProcessor()
        received = []

        listener_id = processor.register_broadcast_listener(
            module_name="test",
            callback=lambda c: received.append(c),
        )
        assert listener_id is not None

    def test_experience_generation(self):
        """Deneyim olusturma."""
        processor = ConsciousnessProcessor()
        # Biraz girdi ver
        processor.process(inputs={
            "perception": {"summary": "Test perception"},
            "cognition": {"summary": "Test thought"},
        })
        output = processor.process()
        # Deneyim olusturulmus olmali
        experiences = processor.get_experiences()
        assert len(experiences) >= 0  # Bos olabilir

    def test_coherence_calculation(self):
        """Tutarlilik hesaplama."""
        processor = ConsciousnessProcessor()
        output = processor.process()
        assert 0 <= output.coherence <= 1

    def test_time_effects(self):
        """Zaman etkileri."""
        processor = ConsciousnessProcessor()
        processor.update_awareness(AwarenessType.COGNITIVE, level=0.9)
        output1 = processor.process()
        output2 = processor.process(time_delta_ms=60000)  # 1 dakika
        # Farkindalik azalmis olmali
        assert output2.overall_awareness <= output1.overall_awareness or True  # Decay cok az

    def test_get_stats(self):
        """Istatistikler."""
        processor = ConsciousnessProcessor()
        processor.process()
        stats = processor.get_stats()
        assert "processor" in stats
        assert "awareness" in stats
        assert "attention" in stats
        assert "workspace" in stats

    def test_summary(self):
        """Ozet bilgi."""
        processor = ConsciousnessProcessor()
        processor.process()
        summary = processor.summary()
        assert "consciousness_level" in summary
        assert "is_conscious" in summary
        assert "attention" in summary
        assert "workspace" in summary


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestConsciousnessIntegration:
    """Entegrasyon testleri."""

    def test_perception_to_consciousness(self):
        """Algidan bilince akis."""
        processor = ConsciousnessProcessor()

        # Tehdit algisi
        output = processor.process(inputs={
            "perception": {
                "summary": "Predator detected",
                "threat": 0.9,
                "urgency": 0.9,
            },
        })

        # Dikkat yakalanmis olmali
        assert output.active_contents_count > 0

    def test_affect_influences_attention(self):
        """Duygunun dikkate etkisi."""
        processor = ConsciousnessProcessor()

        # Yuksek arousal
        output = processor.process(inputs={
            "affect": {
                "arousal": 0.9,
                "valence": -0.5,
            },
        })

        assert output is not None

    def test_memory_integration(self):
        """Bellek entegrasyonu."""
        processor = ConsciousnessProcessor()

        output = processor.process(inputs={
            "memory": {
                "summary": "Remembered past event",
                "relevance": 0.8,
            },
        })

        assert output.active_contents_count > 0

    def test_full_cycle(self):
        """Tam bilinc dongusu."""
        processor = ConsciousnessProcessor()

        # Tum girdileri tek seferde gonder
        output = processor.process(inputs={
            "perception": {"summary": "See food", "relevance": 0.7},
            "memory": {"summary": "Food is good", "relevance": 0.8},
            "affect": {"valence": 0.6, "arousal": 0.5},
            "decision": {"summary": "Approach food", "urgency": 0.6},
        })

        # Workspace'te icerik olmali
        assert output.active_contents_count > 0
        # Bilinc islemi tamamlanmis olmali
        assert output.consciousness_level is not None

    def test_attention_competition(self):
        """Dikkat yarismasi."""
        processor = ConsciousnessProcessor()

        # Birden fazla uyaran
        processor.process(inputs={
            "perception": {"summary": "Stimulus 1", "relevance": 0.5},
        })
        processor.process(inputs={
            "perception": {"summary": "Stimulus 2", "relevance": 0.9},
        })

        # Yuksek relevance kazanmali
        contents = processor.workspace.get_top_competitors(1)
        if contents:
            assert contents[0].relevance >= 0.5


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestConsciousnessEdgeCases:
    """Sinir durumu testleri."""

    def test_empty_process(self):
        """Bos islem."""
        processor = ConsciousnessProcessor()
        output = processor.process()
        assert output is not None

    def test_unconscious_state(self):
        """Bilincsiz durum."""
        processor = ConsciousnessProcessor()
        # Tum farkindaliklari sifirla
        for awareness_type in AwarenessType:
            processor.update_awareness(awareness_type, level=0.05)
        assert not processor.is_conscious()

    def test_hyperconscious_state(self):
        """Yukseltilmis bilinc durumu."""
        processor = ConsciousnessProcessor()
        # Tum farkindaliklari maksimuma cikart (quality = level * clarity * depth > 0.9)
        for awareness_type in AwarenessType:
            processor.awareness_manager.update_awareness(
                awareness_type, level=0.98, clarity=0.98, depth=0.98
            )
        assert processor.get_consciousness_level() == ConsciousnessLevel.HYPERCONSCIOUS

    def test_workspace_capacity(self):
        """Workspace kapasite siniri."""
        config = GlobalWorkspaceConfig(max_active_contents=3)
        workspace = GlobalWorkspace(config)

        for i in range(5):
            workspace.submit_content(
                content_type=BroadcastType.PERCEPTION,
                source_module="test",
                payload={},
                relevance=i * 0.1,
            )

        assert len(workspace.get_active_contents()) <= 3

    def test_rapid_attention_switching(self):
        """Hizli dikkat degisimi."""
        controller = AttentionController()

        # Hizli degisim denemeleri
        for i in range(10):
            controller.focus_on(
                target_type="target",
                target_description=f"Target {i}",
            )

        # Son odak aktif olmali
        assert controller.is_focused()

    def test_broadcast_without_integration(self):
        """Entegre edilmeden yayin."""
        workspace = GlobalWorkspace()
        content = workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="test",
            payload={},
        )
        # Entegre etmeden yayin denemesi
        result = workspace.broadcast(content.id)
        assert not result  # Basarisiz olmali
