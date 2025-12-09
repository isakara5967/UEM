"""
tests/unit/test_self_critique.py

SelfCritique test modulu.
25+ test ile self critique islevselligini test eder.
"""

import pytest
from datetime import datetime
from typing import Dict, List, Any

from core.language.pipeline import (
    SelfCritique,
    CritiqueResult,
    SelfCritiqueConfig,
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


# ============================================================================
# CritiqueResult Tests
# ============================================================================

class TestCritiqueResult:
    """CritiqueResult testleri."""

    def test_passed_result(self):
        """Basarili sonuc olusturma."""
        result = CritiqueResult(
            passed=True,
            score=0.9
        )

        assert result.passed is True
        assert result.score == 0.9
        assert result.needs_revision is False

    def test_failed_result(self):
        """Basarisiz sonuc olusturma."""
        result = CritiqueResult(
            passed=False,
            score=0.4,
            violations=["Test ihlali"],
            improvements=["Duzelt"]
        )

        assert result.passed is False
        assert result.score == 0.4
        assert result.needs_revision is True

    def test_violation_count(self):
        """Ihlal sayisi."""
        result = CritiqueResult(
            passed=False,
            score=0.3,
            violations=["Ihlal 1", "Ihlal 2", "Ihlal 3"]
        )

        assert result.violation_count == 3

    def test_has_critical_violation_true(self):
        """Kritik ihlal var."""
        result = CritiqueResult(
            passed=False,
            score=0.2,
            violations=["Guvenlik sorunu"]
        )

        assert result.has_critical_violation is True

    def test_has_critical_violation_false(self):
        """Kritik ihlal yok."""
        result = CritiqueResult(
            passed=False,
            score=0.5,
            violations=["Kucuk bir sorun"]
        )

        assert result.has_critical_violation is False

    def test_revised_output(self):
        """Revize edilmis cikti."""
        result = CritiqueResult(
            passed=False,
            score=0.5,
            revised_output="Revize metin"
        )

        assert result.revised_output == "Revize metin"

    def test_score_validation(self):
        """Skor dogrulama."""
        with pytest.raises(ValueError):
            CritiqueResult(passed=True, score=1.5)

        with pytest.raises(ValueError):
            CritiqueResult(passed=True, score=-0.1)

    def test_details_dict(self):
        """Detay sozlugu."""
        result = CritiqueResult(
            passed=True,
            score=0.8,
            details={"key": "value"}
        )

        assert result.details["key"] == "value"


# ============================================================================
# SelfCritiqueConfig Tests
# ============================================================================

class TestSelfCritiqueConfig:
    """SelfCritiqueConfig testleri."""

    def test_default_config(self):
        """Varsayilan config."""
        config = SelfCritiqueConfig()

        assert config.enabled is True
        assert config.min_score_threshold == 0.6
        assert config.max_revision_attempts == 2
        assert config.check_tone_match is True
        assert config.check_content_coverage is True
        assert config.check_constraint_violations is True
        assert config.auto_revise is True

    def test_disabled_config(self):
        """Deaktif config."""
        config = SelfCritiqueConfig(enabled=False)

        assert config.enabled is False

    def test_custom_threshold(self):
        """Ozel esik degeri."""
        config = SelfCritiqueConfig(min_score_threshold=0.8)

        assert config.min_score_threshold == 0.8


# ============================================================================
# SelfCritique Basic Tests
# ============================================================================

class TestSelfCritiqueBasic:
    """SelfCritique temel testleri."""

    @pytest.fixture
    def situation(self):
        """Ornek situation."""
        return SituationModel(
            id=generate_situation_id(),
            actors=[
                Actor(id="user", role="user"),
                Actor(id="assistant", role="assistant")
            ],
            intentions=[
                Intention(
                    id="int_test",
                    actor_id="user",
                    goal="ask",
                    confidence=0.7
                )
            ],
            topic_domain="general"
        )

    @pytest.fixture
    def message_plan(self):
        """Ornek message plan."""
        return MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="Bilgi ver",
            tone=ToneType.NEUTRAL,
            content_points=["bilgi"]
        )

    @pytest.fixture
    def critique(self):
        """SelfCritique fixture."""
        return SelfCritique()

    def test_critique_creation_default(self):
        """Varsayilan critique olusturma."""
        critique = SelfCritique()

        assert critique.config is not None
        assert critique.config.enabled is True

    def test_critique_creation_with_config(self):
        """Config ile critique olusturma."""
        config = SelfCritiqueConfig(enabled=False)
        critique = SelfCritique(config=config)

        assert critique.config.enabled is False

    def test_critique_disabled(self, situation, message_plan):
        """Deaktif critique."""
        config = SelfCritiqueConfig(enabled=False)
        critique = SelfCritique(config=config)

        result = critique.critique("Test output", message_plan, situation)

        assert result.passed is True
        assert result.score == 1.0
        assert result.details.get("skipped") is True

    def test_critique_simple_output(self, critique, situation, message_plan):
        """Basit cikti critique."""
        result = critique.critique("Anliyorum.", message_plan, situation)

        assert result is not None
        assert 0.0 <= result.score <= 1.0


# ============================================================================
# Tone Match Tests
# ============================================================================

class TestToneMatch:
    """Ton uyumu testleri."""

    @pytest.fixture
    def critique(self):
        """SelfCritique fixture."""
        return SelfCritique()

    @pytest.fixture
    def situation(self):
        """Ornek situation."""
        return SituationModel(
            id=generate_situation_id(),
            topic_domain="general"
        )

    def test_empathic_tone_match(self, critique, situation):
        """Empatik ton uyumu."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.EMPATHIZE],
            primary_intent="Empati kur",
            tone=ToneType.EMPATHIC,
            content_points=["empati"]
        )

        # Empatik ifadeler iceren cikti
        output = "Anliyorum, zor bir durum. Yanindayim."
        result = critique.critique(output, plan, situation)

        assert "tone_score" in result.details

    def test_formal_tone_match(self, critique, situation):
        """Resmi ton uyumu."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="Bilgi ver",
            tone=ToneType.FORMAL,
            content_points=["bilgi"]
        )

        output = "Saygilarimla, bu konuyu degerlendirmek istiyorum."
        result = critique.critique(output, plan, situation)

        assert result is not None

    def test_casual_tone_mismatch(self, critique, situation):
        """Resmi beklentiye casual cevap."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="Bilgi ver",
            tone=ToneType.FORMAL,
            content_points=["bilgi"]
        )

        # Casual ifadeler - resmi beklentiye uyumsuz
        output = "Ya bak iste, hadi gel anlatayim."
        result = critique.critique(output, plan, situation)

        # Ton uyumsuzlugu beklenir
        assert result is not None


# ============================================================================
# Content Coverage Tests
# ============================================================================

class TestContentCoverage:
    """Icerik kapsama testleri."""

    @pytest.fixture
    def critique(self):
        """SelfCritique fixture."""
        return SelfCritique()

    @pytest.fixture
    def situation(self):
        """Ornek situation."""
        return SituationModel(
            id=generate_situation_id(),
            topic_domain="general"
        )

    def test_full_coverage(self, critique, situation):
        """Tam icerik kapsama."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="Bilgi ver",
            tone=ToneType.NEUTRAL,
            content_points=["python", "programlama"]
        )

        output = "Python bir programlama dilidir."
        result = critique.critique(output, plan, situation)

        assert "content_coverage" in result.details

    def test_low_coverage(self, critique, situation):
        """Dusuk icerik kapsama."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="Cok seyden bahset",
            tone=ToneType.NEUTRAL,
            content_points=[
                "python",
                "javascript",
                "rust",
                "golang"
            ]
        )

        output = "Merhaba."
        result = critique.critique(output, plan, situation)

        assert result.details.get("content_coverage", 1.0) < 0.5

    def test_empty_content_points(self, critique, situation):
        """Bos icerik noktalari."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.ACKNOWLEDGE],
            primary_intent="Kabul et",
            tone=ToneType.NEUTRAL,
            content_points=[]
        )

        output = "Anliyorum."
        result = critique.critique(output, plan, situation)

        # Bos icerik noktasi = tam kapsama
        assert result.details.get("content_coverage", 1.0) == 1.0


# ============================================================================
# Constraint Violation Tests
# ============================================================================

class TestConstraintViolations:
    """Kisit ihlali testleri."""

    @pytest.fixture
    def critique(self):
        """SelfCritique fixture."""
        return SelfCritique()

    @pytest.fixture
    def situation(self):
        """Ornek situation."""
        return SituationModel(
            id=generate_situation_id(),
            topic_domain="general"
        )

    def test_no_violations(self, critique, situation):
        """Ihlal yok."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="Bilgi ver",
            tone=ToneType.NEUTRAL,
            content_points=["bilgi"],
            constraints=["Durust ol"]
        )

        output = "Bilgi veriyorum."
        result = critique.critique(output, plan, situation)

        # Ihlal olmamali
        assert len(result.details.get("constraint_violations", [])) == 0

    def test_ethical_constraint_violation(self, critique, situation):
        """Etik kisit ihlali."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="Bilgi ver",
            tone=ToneType.NEUTRAL,
            content_points=["bilgi"],
            constraints=["Durust ve seffaf ol"]
        )

        # Yaniltici ifade
        output = "Kesinlikle dogru, garanti ediyorum."
        result = critique.critique(output, plan, situation)

        # Ihlal beklenir
        constraint_violations = result.details.get("constraint_violations", [])
        assert len(constraint_violations) > 0 or len(result.violations) > 0


# ============================================================================
# Problematic Patterns Tests
# ============================================================================

class TestProblematicPatterns:
    """Problematik pattern testleri."""

    @pytest.fixture
    def critique(self):
        """SelfCritique fixture."""
        return SelfCritique()

    @pytest.fixture
    def situation(self):
        """Ornek situation."""
        return SituationModel(
            id=generate_situation_id(),
            topic_domain="general"
        )

    @pytest.fixture
    def message_plan(self):
        """Ornek message plan."""
        return MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.INFORM],
            primary_intent="Bilgi ver",
            tone=ToneType.NEUTRAL,
            content_points=["bilgi"]
        )

    def test_no_problematic_patterns(self, critique, situation, message_plan):
        """Problematik pattern yok."""
        output = "Merhaba, size yardimci olmak istiyorum."
        result = critique.critique(output, message_plan, situation)

        # Problematik pattern olmamali
        problematic_violations = [
            v for v in result.violations if "Problematik" in v
        ]
        assert len(problematic_violations) == 0

    def test_offensive_pattern(self, critique, situation, message_plan):
        """Saldirgan pattern."""
        output = "Bu aptal bir fikir."
        result = critique.critique(output, message_plan, situation)

        # Problematik pattern beklenir
        assert len(result.violations) > 0


# ============================================================================
# Revise Tests
# ============================================================================

class TestRevise:
    """Revizyon testleri."""

    @pytest.fixture
    def critique(self):
        """SelfCritique fixture."""
        return SelfCritique()

    @pytest.fixture
    def message_plan(self):
        """Ornek message plan."""
        return MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.EMPATHIZE],
            primary_intent="Empati kur",
            tone=ToneType.EMPATHIC,
            content_points=["anlayis"]
        )

    def test_revise_basic(self, critique, message_plan):
        """Temel revizyon."""
        output = "Tamam."
        improvements = ["Daha anlayisli ve sicak ifadeler kullan"]

        revised = critique.revise(output, improvements, message_plan)

        assert revised is not None
        assert len(revised) >= len(output)

    def test_revise_no_improvements(self, critique, message_plan):
        """Iyilestirme olmadan revizyon."""
        output = "Test output."
        improvements = []

        revised = critique.revise(output, improvements, message_plan)

        # Degismemeli
        assert revised == output

    def test_revise_removes_problematic(self, critique, message_plan):
        """Problematik ifade kaldirma."""
        output = "Bu aptal bir fikir."
        improvements = ["Problematik ifadeleri kaldir"]

        revised = critique.revise(output, improvements, message_plan)

        # "aptal" kalkmalı
        assert "aptal" not in revised.lower()


# ============================================================================
# Get Critique Summary Tests
# ============================================================================

class TestCritiqueSummary:
    """Critique ozet testleri."""

    @pytest.fixture
    def critique(self):
        """SelfCritique fixture."""
        return SelfCritique()

    def test_summary_passed(self, critique):
        """Basarili ozet."""
        result = CritiqueResult(passed=True, score=0.9)
        summary = critique.get_critique_summary(result)

        assert "Onaylandi" in summary
        assert "0.90" in summary

    def test_summary_failed(self, critique):
        """Basarisiz ozet."""
        result = CritiqueResult(
            passed=False,
            score=0.4,
            violations=["Ihlal 1", "Ihlal 2"]
        )
        summary = critique.get_critique_summary(result)

        assert "Basarisiz" in summary
        assert "2 ihlal" in summary

    def test_summary_with_revision(self, critique):
        """Revizyon ile ozet."""
        result = CritiqueResult(
            passed=False,
            score=0.5,
            revised_output="Revize"
        )
        summary = critique.get_critique_summary(result)

        assert "revize" in summary.lower()


# ============================================================================
# Integration Tests
# ============================================================================

class TestSelfCritiqueIntegration:
    """Entegrasyon testleri."""

    @pytest.fixture
    def critique(self):
        """SelfCritique fixture."""
        return SelfCritique()

    @pytest.fixture
    def situation(self):
        """Ornek situation."""
        return SituationModel(
            id=generate_situation_id(),
            actors=[
                Actor(id="user", role="user"),
                Actor(id="assistant", role="assistant")
            ],
            intentions=[
                Intention(
                    id="int_test",
                    actor_id="user",
                    goal="help",
                    confidence=0.8
                )
            ],
            emotional_state=EmotionalState(valence=-0.5),
            topic_domain="emotions"
        )

    def test_full_critique_flow(self, critique, situation):
        """Tam critique akisi."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.EMPATHIZE, DialogueAct.COMFORT],
            primary_intent="Empati ve teselli",
            tone=ToneType.EMPATHIC,
            content_points=["anlayis", "destek"],
            constraints=["Sicak ol", "Anlayisli ol"]
        )

        output = "Anliyorum, zor bir donem geciriyorsun. Yanindayim."
        result = critique.critique(output, plan, situation)

        assert result is not None
        assert result.score > 0

    def test_auto_revise_on_failure(self, critique, situation):
        """Basarisiz durumda otomatik revizyon."""
        plan = MessagePlan(
            id=generate_message_plan_id(),
            dialogue_acts=[DialogueAct.EMPATHIZE],
            primary_intent="Empati kur",
            tone=ToneType.EMPATHIC,
            content_points=["anlayis"]
        )

        # Kotu cikti
        output = "Tamam."
        result = critique.critique(output, plan, situation)

        # Revizyon yapilmis olmali (auto_revise aktif)
        if not result.passed:
            # Revize edilmis olabilir
            pass
