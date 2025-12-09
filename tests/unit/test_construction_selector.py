"""
tests/unit/test_construction_selector.py

ConstructionSelector testleri - MessagePlan → Construction seçimi.

Test kategorileri:
1. ConstructionSelector oluşturma
2. Select metodu
3. Score hesaplama
4. DialogueAct eşleşme
5. Ton uyumu
6. Kısıt uyumu
7. Katmana göre seçim
8. En iyi seçim
"""

import pytest

from core.language.construction.selector import (
    ConstructionSelector,
    ConstructionSelectorConfig,
    ConstructionScore,
    SelectionResult,
)
from core.language.construction.grammar import (
    ConstructionGrammar,
    ConstructionGrammarConfig,
)
from core.language.construction.types import (
    Construction,
    ConstructionLevel,
    ConstructionForm,
    ConstructionMeaning,
    Slot,
    SlotType,
    generate_construction_id,
    generate_slot_id,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def default_grammar():
    """Varsayılan grammar."""
    return ConstructionGrammar()


@pytest.fixture
def default_selector(default_grammar):
    """Varsayılan selector."""
    return ConstructionSelector(default_grammar)


@pytest.fixture
def custom_config():
    """Özel selector konfigürasyonu."""
    return ConstructionSelectorConfig(
        dialogue_act_weight=0.5,
        tone_weight=0.3,
        constraint_weight=0.1,
        confidence_weight=0.1,
        min_score_threshold=0.2,
        max_selections_per_act=5
    )


@pytest.fixture
def custom_selector(default_grammar, custom_config):
    """Özel config'li selector."""
    return ConstructionSelector(default_grammar, config=custom_config)


@pytest.fixture
def empathic_construction():
    """Empatik construction."""
    return Construction(
        id=generate_construction_id(),
        level=ConstructionLevel.SURFACE,
        form=ConstructionForm(
            template="Seni anlıyorum.",
            slots={}
        ),
        meaning=ConstructionMeaning(
            dialogue_act="empathize"
        ),
        source="human",
        confidence=0.8,
        extra_data={"tone": "empathic"}
    )


# ============================================================================
# 1. ConstructionSelector Oluşturma Testleri
# ============================================================================

class TestConstructionSelectorCreation:
    """ConstructionSelector oluşturma testleri."""

    def test_create_default_selector(self, default_grammar):
        """Varsayılan selector oluşturma."""
        selector = ConstructionSelector(default_grammar)
        assert selector is not None
        assert selector.config is not None

    def test_create_with_custom_config(self, default_grammar, custom_config):
        """Özel config ile selector oluşturma."""
        selector = ConstructionSelector(default_grammar, config=custom_config)
        assert selector.config.dialogue_act_weight == 0.5
        assert selector.config.tone_weight == 0.3

    def test_selector_has_grammar(self, default_selector):
        """Selector grammar'a sahip."""
        assert default_selector.grammar is not None

    def test_default_config_values(self, default_selector):
        """Varsayılan config değerleri."""
        assert default_selector.config.dialogue_act_weight == 0.40
        assert default_selector.config.tone_weight == 0.25
        assert default_selector.config.min_score_threshold == 0.3


# ============================================================================
# 2. Select Metodu Testleri
# ============================================================================

class TestSelectMethod:
    """Select metodu testleri."""

    def test_select_returns_result(self, default_selector):
        """Select SelectionResult döndürür."""
        result = default_selector.select(["inform"])
        assert isinstance(result, SelectionResult)

    def test_select_has_selected(self, default_selector):
        """Result'ta selected var."""
        result = default_selector.select(["inform"])
        assert hasattr(result, "selected")
        assert isinstance(result.selected, list)

    def test_select_has_all_scores(self, default_selector):
        """Result'ta all_scores var."""
        result = default_selector.select(["inform"])
        assert hasattr(result, "all_scores")
        assert isinstance(result.all_scores, list)

    def test_select_has_level_counts(self, default_selector):
        """Result'ta level_counts var."""
        result = default_selector.select(["inform"])
        assert hasattr(result, "level_counts")
        assert isinstance(result.level_counts, dict)

    def test_select_single_act(self, default_selector):
        """Tek act için seçim."""
        result = default_selector.select(["inform"])
        assert len(result.selected) > 0

    def test_select_multiple_acts(self, default_selector):
        """Birden fazla act için seçim."""
        result = default_selector.select(["inform", "suggest"])
        assert len(result.selected) > 0

    def test_select_with_tone(self, default_selector):
        """Ton ile seçim."""
        result = default_selector.select(["empathize"], tone="empathic")
        assert len(result.selected) > 0

    def test_select_with_constraints(self, default_selector):
        """Kısıtlarla seçim."""
        result = default_selector.select(["inform"], constraints=["formal"])
        # Kısıtlar skor etkiler ama sonuç döner
        assert isinstance(result, SelectionResult)

    def test_select_empty_acts(self, default_selector):
        """Boş act listesi."""
        result = default_selector.select([])
        assert len(result.selected) == 0

    def test_select_nonexistent_act(self, default_selector):
        """Olmayan act için seçim."""
        result = default_selector.select(["nonexistent_act"])
        assert len(result.selected) == 0


# ============================================================================
# 3. Score Hesaplama Testleri
# ============================================================================

class TestScoreCalculation:
    """Score hesaplama testleri."""

    def test_score_construction(self, default_selector, default_grammar):
        """Construction skorlama."""
        constructions = default_grammar.get_by_dialogue_act("inform")
        if constructions:
            score = default_selector.score_construction(
                constructions[0], "inform"
            )
            assert isinstance(score, ConstructionScore)

    def test_score_has_total(self, default_selector, default_grammar):
        """Score'da total var."""
        constructions = default_grammar.get_by_dialogue_act("inform")
        if constructions:
            score = default_selector.score_construction(
                constructions[0], "inform"
            )
            assert 0.0 <= score.total_score <= 1.0

    def test_score_has_components(self, default_selector, default_grammar):
        """Score'da bileşenler var."""
        constructions = default_grammar.get_by_dialogue_act("inform")
        if constructions:
            score = default_selector.score_construction(
                constructions[0], "inform"
            )
            assert hasattr(score, "dialogue_act_score")
            assert hasattr(score, "tone_score")
            assert hasattr(score, "constraint_score")
            assert hasattr(score, "confidence_score")

    def test_score_has_reasons(self, default_selector, default_grammar):
        """Score'da gerekçeler var."""
        constructions = default_grammar.get_by_dialogue_act("inform")
        if constructions:
            score = default_selector.score_construction(
                constructions[0], "inform"
            )
            assert isinstance(score.reasons, list)

    def test_score_matching_act_higher(self, default_selector, default_grammar):
        """Eşleşen act daha yüksek skor."""
        constructions = default_grammar.get_by_dialogue_act("inform")
        if constructions:
            matching_score = default_selector.score_construction(
                constructions[0], "inform"
            )
            non_matching_score = default_selector.score_construction(
                constructions[0], "warn"
            )
            assert matching_score.dialogue_act_score > non_matching_score.dialogue_act_score


# ============================================================================
# 4. DialogueAct Eşleşme Testleri
# ============================================================================

class TestDialogueActMatching:
    """DialogueAct eşleşme testleri."""

    def test_exact_match_full_score(self, default_selector, default_grammar):
        """Tam eşleşme tam skor."""
        constructions = default_grammar.get_by_dialogue_act("inform")
        if constructions:
            score = default_selector._match_dialogue_act(constructions[0], "inform")
            assert score == 1.0

    def test_no_match_zero_score(self, default_selector, default_grammar):
        """Eşleşme yok sıfır skor."""
        constructions = default_grammar.get_by_dialogue_act("inform")
        if constructions:
            score = default_selector._match_dialogue_act(constructions[0], "unknown_act")
            assert score == 0.0

    def test_similar_acts_partial_score(self, default_selector, default_grammar):
        """Benzer act'ler kısmi skor."""
        constructions = default_grammar.get_by_dialogue_act("inform")
        if constructions:
            score = default_selector._match_dialogue_act(constructions[0], "explain")
            assert 0.0 < score < 1.0


# ============================================================================
# 5. Ton Uyumu Testleri
# ============================================================================

class TestToneMatching:
    """Ton uyumu testleri."""

    def test_exact_tone_match(self, default_selector, empathic_construction):
        """Tam ton eşleşmesi."""
        score = default_selector._match_tone(empathic_construction, "empathic")
        assert score == 1.0

    def test_similar_tone_partial_score(self, default_selector, empathic_construction):
        """Benzer ton kısmi skor."""
        score = default_selector._match_tone(empathic_construction, "supportive")
        assert 0.5 < score < 1.0

    def test_no_tone_neutral_score(self, default_selector, default_grammar):
        """Ton belirtilmemişse nötr skor."""
        constructions = default_grammar.get_by_level(ConstructionLevel.MIDDLE)
        if constructions:
            # Tone olmayan construction
            no_tone = None
            for c in constructions:
                if "tone" not in c.extra_data:
                    no_tone = c
                    break
            if no_tone:
                score = default_selector._match_tone(no_tone, "formal")
                assert score == 0.5


# ============================================================================
# 6. Kısıt Uyumu Testleri
# ============================================================================

class TestConstraintMatching:
    """Kısıt uyumu testleri."""

    def test_constraint_matching_bonus(self, default_selector, empathic_construction):
        """Kısıt eşleşme bonusu."""
        score = default_selector._match_constraints(
            empathic_construction,
            ["be_empathic"]
        )
        assert score > 0.3

    def test_no_constraints_neutral(self, default_selector, empathic_construction):
        """Kısıt yoksa nötr."""
        score = default_selector._match_constraints(empathic_construction, [])
        assert score == 0.5

    def test_multiple_constraints(self, default_selector, empathic_construction):
        """Birden fazla kısıt."""
        score = default_selector._match_constraints(
            empathic_construction,
            ["be_empathic", "supportive"]
        )
        assert score > 0.3


# ============================================================================
# 7. Katmana Göre Seçim Testleri
# ============================================================================

class TestSelectByLevel:
    """Katmana göre seçim testleri."""

    def test_select_deep_level(self, default_selector):
        """DEEP katmandan seçim."""
        result = default_selector.select_by_level(["inform"], ConstructionLevel.DEEP)
        for score in result:
            assert score.construction.level == ConstructionLevel.DEEP

    def test_select_middle_level(self, default_selector):
        """MIDDLE katmandan seçim."""
        result = default_selector.select_by_level(["inform"], ConstructionLevel.MIDDLE)
        for score in result:
            assert score.construction.level == ConstructionLevel.MIDDLE

    def test_select_surface_level(self, default_selector):
        """SURFACE katmandan seçim."""
        result = default_selector.select_by_level(["acknowledge"], ConstructionLevel.SURFACE)
        for score in result:
            assert score.construction.level == ConstructionLevel.SURFACE

    def test_select_by_level_with_tone(self, default_selector):
        """Katman ve ton ile seçim."""
        result = default_selector.select_by_level(
            ["empathize"],
            ConstructionLevel.SURFACE,
            tone="empathic"
        )
        assert isinstance(result, list)


# ============================================================================
# 8. En İyi Seçim Testleri
# ============================================================================

class TestGetBestForAct:
    """En iyi seçim testleri."""

    def test_get_best_returns_score(self, default_selector):
        """En iyi, ConstructionScore döndürür."""
        result = default_selector.get_best_for_act("inform")
        if result:
            assert isinstance(result, ConstructionScore)

    def test_get_best_with_tone(self, default_selector):
        """Ton ile en iyi."""
        result = default_selector.get_best_for_act("empathize", tone="empathic")
        if result:
            assert isinstance(result, ConstructionScore)

    def test_get_best_nonexistent_act(self, default_selector):
        """Olmayan act için en iyi."""
        result = default_selector.get_best_for_act("nonexistent_act")
        assert result is None

    def test_get_best_is_highest_score(self, default_selector):
        """En iyi, en yüksek skorlu."""
        result = default_selector.select(["inform"])
        best = default_selector.get_best_for_act("inform")
        if best and result.selected:
            assert best.total_score == result.selected[0].total_score


# ============================================================================
# 9. Sıralama ve Filtreleme Testleri
# ============================================================================

class TestSortingAndFiltering:
    """Sıralama ve filtreleme testleri."""

    def test_results_sorted_by_score(self, default_selector):
        """Sonuçlar skora göre sıralı."""
        result = default_selector.select(["inform"])
        if len(result.selected) > 1:
            for i in range(len(result.selected) - 1):
                assert result.selected[i].total_score >= result.selected[i + 1].total_score

    def test_results_above_threshold(self, default_selector):
        """Sonuçlar eşik üstünde."""
        result = default_selector.select(["inform"])
        for score in result.selected:
            assert score.total_score >= default_selector.config.min_score_threshold

    def test_max_selections_per_act(self, custom_selector):
        """Act başına max seçim."""
        result = custom_selector.select(["inform"])
        # max_selections_per_act = 5
        # Aynı act için max 5 seçim
        assert len(result.selected) <= custom_selector.config.max_selections_per_act

    def test_no_duplicate_selections(self, default_selector):
        """Tekrarsız seçimler."""
        result = default_selector.select(["inform", "explain"])
        ids = [s.construction.id for s in result.selected]
        assert len(ids) == len(set(ids))
