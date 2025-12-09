"""
tests/unit/test_thought_to_speech.py

ThoughtToSpeechPipeline test modulu.
40+ test ile tam pipeline islevselligini test eder.
"""

import pytest
from datetime import datetime
from typing import Dict, List, Any

from core.language.pipeline import (
    ThoughtToSpeechPipeline,
    PipelineResult,
    PipelineConfig,
    SelfCritiqueConfig,
    generate_pipeline_result_id,
)
from core.language.dialogue.types import (
    DialogueAct,
    ToneType,
    SituationModel,
    MessagePlan,
    Actor,
    Intention,
    Risk,
    EmotionalState,
    generate_situation_id,
    generate_message_plan_id,
)
from core.language.dialogue.situation_builder import SituationBuilder
from core.language.dialogue.act_selector import DialogueActSelector, ActSelectionResult
from core.language.dialogue.message_planner import MessagePlanner
from core.language.risk.types import RiskLevel, RiskAssessment, RiskCategory, RiskFactor
from core.language.risk.scorer import RiskScorer
from core.language.risk.approver import InternalApprover, ApprovalDecision, ApprovalResult
from core.language.construction.grammar import ConstructionGrammar
from core.language.construction.selector import ConstructionSelector
from core.language.construction.realizer import ConstructionRealizer
from core.language.pipeline.self_critique import SelfCritique, CritiqueResult


# ============================================================================
# PipelineConfig Tests
# ============================================================================

class TestPipelineConfig:
    """PipelineConfig testleri."""

    def test_default_config(self):
        """Varsayilan config olusturma."""
        config = PipelineConfig()

        assert config.enable_self_critique is True
        assert config.max_revision_attempts == 2
        assert config.min_approval_level == RiskLevel.MEDIUM
        assert config.enable_risk_assessment is True
        assert config.enable_approval_check is True

    def test_minimal_config(self):
        """Minimal config olusturma."""
        config = PipelineConfig.minimal()

        assert config.enable_self_critique is False
        assert config.enable_risk_assessment is False
        assert config.enable_approval_check is False

    def test_strict_config(self):
        """Kati config olusturma."""
        config = PipelineConfig.strict()

        assert config.enable_self_critique is True
        assert config.enable_risk_assessment is True
        assert config.min_approval_level == RiskLevel.LOW

    def test_balanced_config(self):
        """Dengeli config olusturma."""
        config = PipelineConfig.balanced()

        assert config.enable_self_critique is True

    def test_with_self_critique(self):
        """Self critique toggle."""
        config = PipelineConfig().with_self_critique(False)

        assert config.enable_self_critique is False

    def test_with_risk_level(self):
        """Risk seviyesi degistirme."""
        config = PipelineConfig().with_risk_level(RiskLevel.HIGH)

        assert config.min_approval_level == RiskLevel.HIGH

    def test_fallback_response(self):
        """Fallback response."""
        config = PipelineConfig()

        assert "Anlayamadim" in config.fallback_response

    def test_validation_max_revision_attempts(self):
        """Negatif max_revision_attempts hatasi."""
        with pytest.raises(ValueError):
            PipelineConfig(max_revision_attempts=-1)

    def test_validation_construction_timeout(self):
        """Negatif construction_timeout hatasi."""
        with pytest.raises(ValueError):
            PipelineConfig(construction_timeout=-1)

    def test_validation_max_output_length(self):
        """Sifir max_output_length hatasi."""
        with pytest.raises(ValueError):
            PipelineConfig(max_output_length=0)


# ============================================================================
# PipelineResult Tests
# ============================================================================

class TestPipelineResult:
    """PipelineResult testleri."""

    def test_success_result(self):
        """Basarili sonuc olusturma."""
        result = PipelineResult(
            success=True,
            output="Merhaba!"
        )

        assert result.success is True
        assert result.output == "Merhaba!"
        assert result.error is None

    def test_failure_result(self):
        """Basarisiz sonuc olusturma."""
        result = PipelineResult.failure(
            error="Bir hata olustu",
            fallback_output="Uzgunum."
        )

        assert result.success is False
        assert result.error == "Bir hata olustu"
        assert result.output == "Uzgunum."

    def test_result_id(self):
        """Result ID uretimi."""
        result = PipelineResult(success=True, output="Test")

        assert result.id.startswith("pr_")

    def test_is_approved_property(self):
        """is_approved ozellik kontrolu."""
        # Onaysiz
        result = PipelineResult(success=True, output="Test")
        assert result.is_approved is False

        # Onaylandi
        approval = ApprovalResult(
            decision=ApprovalDecision.APPROVED,
            approver="auto",
            risk_assessment=RiskAssessment(
                id="test",
                level=RiskLevel.LOW,
                overall_score=0.1
            )
        )
        result = PipelineResult(
            success=True,
            output="Test",
            approval=approval
        )
        assert result.is_approved is True

    def test_risk_level_property(self):
        """risk_level ozellik kontrolu."""
        # Risk yok
        result = PipelineResult(success=True, output="Test")
        assert result.risk_level is None

        # Risk var
        assessment = RiskAssessment(
            id="test",
            level=RiskLevel.HIGH,
            overall_score=0.7
        )
        result = PipelineResult(
            success=True,
            output="Test",
            risk_assessment=assessment
        )
        assert result.risk_level == RiskLevel.HIGH

    def test_was_revised_property(self):
        """was_revised ozellik kontrolu."""
        # Revize edilmedi
        result = PipelineResult(success=True, output="Test")
        assert result.was_revised is False

        # Revize edildi
        critique = CritiqueResult(
            passed=False,
            score=0.5,
            revised_output="Revize edilmis"
        )
        result = PipelineResult(
            success=True,
            output="Test",
            critique_result=critique
        )
        assert result.was_revised is True


# ============================================================================
# ThoughtToSpeechPipeline Basic Tests
# ============================================================================

class TestThoughtToSpeechPipelineBasic:
    """Pipeline temel testleri."""

    def test_pipeline_creation_default(self):
        """Varsayilan pipeline olusturma."""
        pipeline = ThoughtToSpeechPipeline()

        assert pipeline.config is not None
        assert pipeline.situation_builder is not None
        assert pipeline.act_selector is not None
        assert pipeline.message_planner is not None
        assert pipeline.risk_scorer is not None
        assert pipeline.approver is not None
        assert pipeline.construction_grammar is not None
        assert pipeline.construction_selector is not None
        assert pipeline.construction_realizer is not None
        assert pipeline.self_critique is not None

    def test_pipeline_creation_with_config(self):
        """Config ile pipeline olusturma."""
        config = PipelineConfig.minimal()
        pipeline = ThoughtToSpeechPipeline(config=config)

        assert pipeline.config.enable_self_critique is False

    def test_pipeline_creation_with_custom_components(self):
        """Ozel bilesenlerle pipeline olusturma."""
        builder = SituationBuilder()
        pipeline = ThoughtToSpeechPipeline(situation_builder=builder)

        assert pipeline.situation_builder is builder

    def test_get_pipeline_info(self):
        """Pipeline bilgisi alma."""
        pipeline = ThoughtToSpeechPipeline()
        info = pipeline.get_pipeline_info()

        assert "config" in info
        assert "components" in info
        assert "construction_count" in info

    def test_generate_pipeline_result_id(self):
        """Pipeline result ID uretimi."""
        id1 = generate_pipeline_result_id()
        id2 = generate_pipeline_result_id()

        assert id1.startswith("pr_")
        assert id2.startswith("pr_")
        assert id1 != id2


# ============================================================================
# ThoughtToSpeechPipeline Process Tests
# ============================================================================

class TestThoughtToSpeechPipelineProcess:
    """Pipeline process testleri."""

    @pytest.fixture
    def pipeline(self):
        """Pipeline fixture."""
        return ThoughtToSpeechPipeline()

    @pytest.fixture
    def minimal_pipeline(self):
        """Minimal pipeline fixture."""
        config = PipelineConfig.minimal()
        return ThoughtToSpeechPipeline(config=config)

    def test_process_simple_message(self, pipeline):
        """Basit mesaj isleme."""
        result = pipeline.process("Merhaba")

        assert result.success is True
        assert result.output != ""
        assert result.situation is not None
        assert result.message_plan is not None

    def test_process_with_context(self, pipeline):
        """Baglamla mesaj isleme."""
        context = [
            {"role": "user", "content": "Merhaba"},
            {"role": "assistant", "content": "Merhaba, nasilsin?"}
        ]
        result = pipeline.process("Iyiyim", context)

        assert result.success is True
        assert result.situation is not None

    def test_process_emotional_message(self, pipeline):
        """Duygusal mesaj isleme."""
        result = pipeline.process("Cok uzgunum, kendimi kotu hissediyorum")

        assert result.success is True
        assert result.situation is not None
        if result.situation.emotional_state:
            assert result.situation.emotional_state.valence < 0

    def test_process_question_message(self, pipeline):
        """Soru mesaji isleme."""
        result = pipeline.process("Python nedir?")

        assert result.success is True
        assert result.message_plan is not None

    def test_process_help_request(self, pipeline):
        """Yardim istegi isleme."""
        result = pipeline.process("Bana yardim eder misin?")

        assert result.success is True

    def test_process_minimal_pipeline(self, minimal_pipeline):
        """Minimal pipeline ile isleme."""
        result = minimal_pipeline.process("Merhaba")

        assert result.success is True
        assert result.risk_assessment is None
        assert result.approval is None
        assert result.critique_result is None

    def test_process_returns_situation(self, pipeline):
        """Situation donusunu test et."""
        result = pipeline.process("Test mesaji")

        assert result.situation is not None
        assert result.situation.id.startswith("sit_")

    def test_process_returns_message_plan(self, pipeline):
        """MessagePlan donusunu test et."""
        result = pipeline.process("Test mesaji")

        assert result.message_plan is not None
        assert len(result.message_plan.dialogue_acts) > 0

    def test_process_with_metadata(self, pipeline):
        """Metadata ile isleme."""
        result = pipeline.process(
            "Merhaba",
            metadata={"custom_key": "custom_value"}
        )

        assert result.success is True
        assert "custom_key" in result.metadata

    def test_process_fallback_on_empty_constructions(self, pipeline):
        """Construction bulunamayinca fallback."""
        # Normal islem - her zaman bir sey donmeli
        result = pipeline.process("Merhaba")

        assert result.output != ""

    def test_process_output_length_limit(self):
        """Cikti uzunluk siniri."""
        config = PipelineConfig(max_output_length=50)
        pipeline = ThoughtToSpeechPipeline(config=config)

        result = pipeline.process("Bu cok uzun bir mesaj olabilir")

        assert len(result.output) <= 53  # 50 + "..."


# ============================================================================
# Risk Assessment Tests
# ============================================================================

class TestPipelineRiskAssessment:
    """Risk degerlendirme testleri."""

    @pytest.fixture
    def pipeline(self):
        """Pipeline fixture."""
        return ThoughtToSpeechPipeline()

    def test_risk_assessment_enabled(self, pipeline):
        """Risk degerlendirmesi aktif."""
        result = pipeline.process("Normal mesaj")

        assert result.risk_assessment is not None

    def test_risk_assessment_disabled(self):
        """Risk degerlendirmesi deaktif."""
        config = PipelineConfig(enable_risk_assessment=False)
        pipeline = ThoughtToSpeechPipeline(config=config)

        result = pipeline.process("Normal mesaj")

        assert result.risk_assessment is None

    def test_low_risk_message(self, pipeline):
        """Dusuk riskli mesaj."""
        result = pipeline.process("Merhaba, nasilsin?")

        if result.risk_assessment:
            assert result.risk_assessment.level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_high_risk_indicators(self, pipeline):
        """Yuksek risk belirtecleri."""
        # Bu mesaj risk algılayıcıları tetikleyebilir
        result = pipeline.process("Kendimi cok kotu hissediyorum")

        assert result.risk_assessment is not None


# ============================================================================
# Approval Tests
# ============================================================================

class TestPipelineApproval:
    """Onay mekanizmasi testleri."""

    @pytest.fixture
    def pipeline(self):
        """Pipeline fixture."""
        return ThoughtToSpeechPipeline()

    def test_approval_enabled(self, pipeline):
        """Onay aktif."""
        result = pipeline.process("Merhaba")

        assert result.approval is not None

    def test_approval_disabled(self):
        """Onay deaktif."""
        config = PipelineConfig(enable_approval_check=False)
        pipeline = ThoughtToSpeechPipeline(config=config)

        result = pipeline.process("Merhaba")

        assert result.approval is None

    def test_auto_approval_low_risk(self, pipeline):
        """Dusuk riskli otomatik onay."""
        result = pipeline.process("Merhaba")

        if result.approval:
            assert result.approval.decision in [
                ApprovalDecision.APPROVED,
                ApprovalDecision.APPROVED_WITH_MODIFICATIONS
            ]


# ============================================================================
# Self Critique Integration Tests
# ============================================================================

class TestPipelineSelfCritique:
    """Self critique entegrasyon testleri."""

    @pytest.fixture
    def pipeline(self):
        """Pipeline fixture."""
        return ThoughtToSpeechPipeline()

    def test_self_critique_enabled(self, pipeline):
        """Self critique aktif."""
        result = pipeline.process("Merhaba")

        assert result.critique_result is not None

    def test_self_critique_disabled(self):
        """Self critique deaktif."""
        config = PipelineConfig(enable_self_critique=False)
        pipeline = ThoughtToSpeechPipeline(config=config)

        result = pipeline.process("Merhaba")

        assert result.critique_result is None

    def test_critique_score_in_metadata(self, pipeline):
        """Critique skoru metadata'da."""
        result = pipeline.process("Merhaba")

        if result.critique_result:
            assert "critique_score" in result.metadata


# ============================================================================
# Pipeline Retry Tests
# ============================================================================

class TestPipelineRetry:
    """Pipeline retry testleri."""

    @pytest.fixture
    def pipeline(self):
        """Pipeline fixture."""
        return ThoughtToSpeechPipeline()

    def test_process_with_retry_success(self, pipeline):
        """Basarili retry."""
        result = pipeline.process_with_retry("Merhaba", max_retries=2)

        assert result.success is True

    def test_process_with_retry_zero_retries(self, pipeline):
        """Sifir retry ile islem."""
        result = pipeline.process_with_retry("Merhaba", max_retries=0)

        assert result is not None


# ============================================================================
# Construction Integration Tests
# ============================================================================

class TestPipelineConstruction:
    """Construction entegrasyon testleri."""

    @pytest.fixture
    def pipeline(self):
        """Pipeline fixture."""
        return ThoughtToSpeechPipeline()

    def test_construction_selection(self, pipeline):
        """Construction secimi."""
        result = pipeline.process("Merhaba")

        # Construction secilmis olmali
        assert result.metadata.get("construction_count", 0) >= 0

    def test_constructions_used_list(self, pipeline):
        """Kullanilan construction listesi."""
        result = pipeline.process("Merhaba")

        # Liste olmali (bos olabilir)
        assert isinstance(result.constructions_used, list)


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestPipelineEdgeCases:
    """Sinir durum testleri."""

    @pytest.fixture
    def pipeline(self):
        """Pipeline fixture."""
        return ThoughtToSpeechPipeline()

    def test_empty_message(self, pipeline):
        """Bos mesaj."""
        result = pipeline.process("")

        # Bos mesaj da islenmeli
        assert result is not None

    def test_very_long_message(self, pipeline):
        """Cok uzun mesaj."""
        long_message = "A" * 1000
        result = pipeline.process(long_message)

        assert result is not None

    def test_special_characters_message(self, pipeline):
        """Ozel karakterli mesaj."""
        result = pipeline.process("Merhaba! @#$%^&*()")

        assert result is not None

    def test_unicode_message(self, pipeline):
        """Unicode mesaj."""
        result = pipeline.process("Merhaba dünya! Türkçe karakterler: şçğüöı")

        assert result is not None

    def test_numbers_only_message(self, pipeline):
        """Sadece sayi mesaji."""
        result = pipeline.process("12345")

        assert result is not None

    def test_multiple_sentences(self, pipeline):
        """Cok cumleli mesaj."""
        result = pipeline.process(
            "Merhaba. Nasilsin? Ben iyiyim. Tesekkurler."
        )

        assert result is not None
        assert result.success is True


# ============================================================================
# Fallback Tests
# ============================================================================

class TestPipelineFallback:
    """Fallback testleri."""

    def test_custom_fallback_response(self):
        """Ozel fallback cevabi."""
        config = PipelineConfig(fallback_response="Ozel hata mesaji")
        pipeline = ThoughtToSpeechPipeline(config=config)

        # Fallback olusturma
        result = PipelineResult.failure(
            error="Test hatasi",
            fallback_output=config.fallback_response
        )

        assert result.output == "Ozel hata mesaji"

    def test_fallback_on_error(self):
        """Hata durumunda fallback."""
        result = PipelineResult.failure(
            error="Bilinmeyen hata",
            fallback_output="Varsayilan cevap"
        )

        assert result.success is False
        assert result.output == "Varsayilan cevap"


# ============================================================================
# Integration Tests
# ============================================================================

class TestPipelineIntegration:
    """Entegrasyon testleri."""

    @pytest.fixture
    def pipeline(self):
        """Pipeline fixture."""
        return ThoughtToSpeechPipeline()

    def test_full_pipeline_flow(self, pipeline):
        """Tam pipeline akisi."""
        result = pipeline.process("Merhaba, nasilsin?")

        # Tum adimlar tamamlanmali
        assert result.situation is not None
        assert result.message_plan is not None
        assert result.output != ""

    def test_conversation_flow(self, pipeline):
        """Konusma akisi."""
        # Ilk mesaj
        result1 = pipeline.process("Merhaba")
        assert result1.success is True

        # Ikinci mesaj
        context = [
            {"role": "user", "content": "Merhaba"},
            {"role": "assistant", "content": result1.output}
        ]
        result2 = pipeline.process("Nasilsin?", context)
        assert result2.success is True

    def test_emotional_context_handling(self, pipeline):
        """Duygusal bagam yonetimi."""
        context = [
            {"role": "user", "content": "Kendimi kotu hissediyorum"},
            {"role": "assistant", "content": "Anliyorum..."}
        ]
        result = pipeline.process("Cok uzgunum", context)

        assert result.success is True
        # Empatik cevap beklenir
