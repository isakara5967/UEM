"""
tests/unit/test_construction_grammar.py

ConstructionGrammar testleri - 3 katmanlı Construction yönetimi.

Test kategorileri:
1. ConstructionGrammar oluşturma
2. Construction ekleme/kaldırma
3. Katmana göre getirme
4. DialogueAct'e göre getirme
5. Eşleşen construction bulma
6. Varsayılan construction'lar
7. Sayım ve istatistikler
"""

import pytest

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
def empty_grammar():
    """Boş grammar (varsayılanlar yüklenmeden)."""
    config = ConstructionGrammarConfig(load_defaults=False)
    return ConstructionGrammar(config=config)


@pytest.fixture
def default_grammar():
    """Varsayılanlarla yüklü grammar."""
    return ConstructionGrammar()


@pytest.fixture
def sample_deep_construction():
    """Örnek DEEP construction."""
    return Construction(
        id=generate_construction_id(),
        level=ConstructionLevel.DEEP,
        form=ConstructionForm(
            template="{konu} hakkında bilgi ver",
            slots={
                "konu": Slot(
                    id=generate_slot_id(),
                    name="konu",
                    slot_type=SlotType.ENTITY,
                    required=True
                )
            }
        ),
        meaning=ConstructionMeaning(
            dialogue_act="inform",
            effects=["user_informed"]
        ),
        source="human"
    )


@pytest.fixture
def sample_middle_construction():
    """Örnek MIDDLE construction."""
    return Construction(
        id=generate_construction_id(),
        level=ConstructionLevel.MIDDLE,
        form=ConstructionForm(
            template="{ozne} {yuklem}",
            slots={
                "ozne": Slot(
                    id=generate_slot_id(),
                    name="ozne",
                    slot_type=SlotType.ENTITY,
                    required=True
                ),
                "yuklem": Slot(
                    id=generate_slot_id(),
                    name="yuklem",
                    slot_type=SlotType.VERB,
                    required=True
                )
            },
            word_order="SOV"
        ),
        meaning=ConstructionMeaning(
            dialogue_act="inform",
            semantic_roles={"agent": "ozne", "action": "yuklem"}
        ),
        source="human"
    )


@pytest.fixture
def sample_surface_construction():
    """Örnek SURFACE construction."""
    return Construction(
        id=generate_construction_id(),
        level=ConstructionLevel.SURFACE,
        form=ConstructionForm(
            template="Anlıyorum.",
            slots={}
        ),
        meaning=ConstructionMeaning(
            dialogue_act="acknowledge"
        ),
        source="human"
    )


# ============================================================================
# 1. ConstructionGrammar Oluşturma Testleri
# ============================================================================

class TestConstructionGrammarCreation:
    """ConstructionGrammar oluşturma testleri."""

    def test_create_default_grammar(self):
        """Varsayılan grammar oluşturma."""
        grammar = ConstructionGrammar()
        assert grammar is not None
        assert grammar.config is not None

    def test_create_with_custom_config(self):
        """Özel config ile grammar oluşturma."""
        config = ConstructionGrammarConfig(
            load_defaults=False,
            max_constructions_per_level=50
        )
        grammar = ConstructionGrammar(config=config)
        assert grammar.config.max_constructions_per_level == 50

    def test_create_empty_grammar(self, empty_grammar):
        """Boş grammar oluşturma."""
        assert empty_grammar.count_total() == 0

    def test_default_grammar_has_constructions(self, default_grammar):
        """Varsayılan grammar construction içerir."""
        assert default_grammar.count_total() > 0

    def test_grammar_has_three_levels(self, default_grammar):
        """Grammar üç katman içerir."""
        counts = default_grammar.count_by_level()
        assert ConstructionLevel.DEEP in counts
        assert ConstructionLevel.MIDDLE in counts
        assert ConstructionLevel.SURFACE in counts


# ============================================================================
# 2. Construction Ekleme/Kaldırma Testleri
# ============================================================================

class TestAddRemoveConstruction:
    """Construction ekleme/kaldırma testleri."""

    def test_add_construction(self, empty_grammar, sample_deep_construction):
        """Construction ekleme."""
        result = empty_grammar.add_construction(sample_deep_construction)
        assert result is True
        assert empty_grammar.count_total() == 1

    def test_add_multiple_constructions(self, empty_grammar, sample_deep_construction, sample_middle_construction):
        """Birden fazla construction ekleme."""
        empty_grammar.add_construction(sample_deep_construction)
        empty_grammar.add_construction(sample_middle_construction)
        assert empty_grammar.count_total() == 2

    def test_add_respects_max_limit(self, sample_deep_construction):
        """Max limit saygısı."""
        config = ConstructionGrammarConfig(
            load_defaults=False,
            max_constructions_per_level=1
        )
        grammar = ConstructionGrammar(config=config)

        # İlk ekleme başarılı
        grammar.add_construction(sample_deep_construction)

        # İkinci ekleme başarısız (aynı level)
        another = Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.DEEP,
            form=ConstructionForm(template="test", slots={}),
            meaning=ConstructionMeaning(dialogue_act="test")
        )
        result = grammar.add_construction(another)
        assert result is False

    def test_remove_construction(self, empty_grammar, sample_deep_construction):
        """Construction kaldırma."""
        empty_grammar.add_construction(sample_deep_construction)
        result = empty_grammar.remove_construction(sample_deep_construction.id)
        assert result is True
        assert empty_grammar.count_total() == 0

    def test_remove_nonexistent_construction(self, empty_grammar):
        """Olmayan construction kaldırma."""
        result = empty_grammar.remove_construction("nonexistent_id")
        assert result is False

    def test_get_construction_by_id(self, empty_grammar, sample_deep_construction):
        """ID ile construction getirme."""
        empty_grammar.add_construction(sample_deep_construction)
        retrieved = empty_grammar.get_construction(sample_deep_construction.id)
        assert retrieved is not None
        assert retrieved.id == sample_deep_construction.id

    def test_get_nonexistent_construction(self, empty_grammar):
        """Olmayan construction getirme."""
        result = empty_grammar.get_construction("nonexistent_id")
        assert result is None


# ============================================================================
# 3. Katmana Göre Getirme Testleri
# ============================================================================

class TestGetByLevel:
    """Katmana göre getirme testleri."""

    def test_get_deep_constructions(self, default_grammar):
        """DEEP construction'ları getir."""
        deep = default_grammar.get_by_level(ConstructionLevel.DEEP)
        assert len(deep) > 0
        for c in deep:
            assert c.level == ConstructionLevel.DEEP

    def test_get_middle_constructions(self, default_grammar):
        """MIDDLE construction'ları getir."""
        middle = default_grammar.get_by_level(ConstructionLevel.MIDDLE)
        assert len(middle) > 0
        for c in middle:
            assert c.level == ConstructionLevel.MIDDLE

    def test_get_surface_constructions(self, default_grammar):
        """SURFACE construction'ları getir."""
        surface = default_grammar.get_by_level(ConstructionLevel.SURFACE)
        assert len(surface) > 0
        for c in surface:
            assert c.level == ConstructionLevel.SURFACE

    def test_get_empty_level(self, empty_grammar):
        """Boş katmandan getirme."""
        result = empty_grammar.get_by_level(ConstructionLevel.DEEP)
        assert result == []


# ============================================================================
# 4. DialogueAct'e Göre Getirme Testleri
# ============================================================================

class TestGetByDialogueAct:
    """DialogueAct'e göre getirme testleri."""

    def test_get_inform_constructions(self, default_grammar):
        """INFORM construction'ları getir."""
        inform = default_grammar.get_by_dialogue_act("inform")
        assert len(inform) > 0
        for c in inform:
            assert c.meaning.dialogue_act == "inform"

    def test_get_warn_constructions(self, default_grammar):
        """WARN construction'ları getir."""
        warn = default_grammar.get_by_dialogue_act("warn")
        assert len(warn) > 0
        for c in warn:
            assert c.meaning.dialogue_act == "warn"

    def test_get_empathize_constructions(self, default_grammar):
        """EMPATHIZE construction'ları getir."""
        empathize = default_grammar.get_by_dialogue_act("empathize")
        assert len(empathize) > 0
        for c in empathize:
            assert c.meaning.dialogue_act == "empathize"

    def test_get_nonexistent_act(self, default_grammar):
        """Olmayan act için getirme."""
        result = default_grammar.get_by_dialogue_act("nonexistent_act")
        assert result == []

    def test_dialogue_act_index_updated_on_add(self, empty_grammar, sample_deep_construction):
        """Ekleme sonrası index güncellenir."""
        empty_grammar.add_construction(sample_deep_construction)
        inform = empty_grammar.get_by_dialogue_act("inform")
        assert len(inform) == 1

    def test_dialogue_act_index_updated_on_remove(self, empty_grammar, sample_deep_construction):
        """Kaldırma sonrası index güncellenir."""
        empty_grammar.add_construction(sample_deep_construction)
        empty_grammar.remove_construction(sample_deep_construction.id)
        inform = empty_grammar.get_by_dialogue_act("inform")
        assert len(inform) == 0


# ============================================================================
# 5. Eşleşen Construction Bulma Testleri
# ============================================================================

class TestFindMatching:
    """Eşleşen construction bulma testleri."""

    def test_find_matching_single_act(self, default_grammar):
        """Tek act için eşleşme."""
        matching = default_grammar.find_matching(["inform"])
        assert len(matching) > 0

    def test_find_matching_multiple_acts(self, default_grammar):
        """Birden fazla act için eşleşme."""
        matching = default_grammar.find_matching(["inform", "suggest"])
        assert len(matching) > 0

    def test_find_matching_with_tone(self, default_grammar):
        """Ton ile eşleşme."""
        matching = default_grammar.find_matching(["empathize"], tone="empathic")
        assert len(matching) > 0

    def test_find_matching_sorted_by_confidence(self, default_grammar):
        """Sonuçlar güvene göre sıralı."""
        matching = default_grammar.find_matching(["inform"])
        if len(matching) > 1:
            for i in range(len(matching) - 1):
                assert matching[i].confidence >= matching[i + 1].confidence

    def test_find_matching_empty_acts(self, default_grammar):
        """Boş act listesi."""
        matching = default_grammar.find_matching([])
        assert matching == []


# ============================================================================
# 6. Varsayılan Construction'lar Testleri
# ============================================================================

class TestDefaultConstructions:
    """Varsayılan construction testleri."""

    def test_load_defaults(self, empty_grammar):
        """Varsayılanları yükle."""
        count = empty_grammar.load_defaults()
        assert count > 0

    def test_defaults_have_deep_layer(self, default_grammar):
        """Varsayılanlarda DEEP var."""
        deep = default_grammar.get_by_level(ConstructionLevel.DEEP)
        assert len(deep) >= 5

    def test_defaults_have_middle_layer(self, default_grammar):
        """Varsayılanlarda MIDDLE var."""
        middle = default_grammar.get_by_level(ConstructionLevel.MIDDLE)
        assert len(middle) >= 5

    def test_defaults_have_surface_layer(self, default_grammar):
        """Varsayılanlarda SURFACE var."""
        surface = default_grammar.get_by_level(ConstructionLevel.SURFACE)
        assert len(surface) >= 5

    def test_defaults_have_inform(self, default_grammar):
        """Varsayılanlarda INFORM var."""
        inform = default_grammar.get_by_dialogue_act("inform")
        assert len(inform) > 0

    def test_defaults_have_warn(self, default_grammar):
        """Varsayılanlarda WARN var."""
        warn = default_grammar.get_by_dialogue_act("warn")
        assert len(warn) > 0

    def test_defaults_have_empathize(self, default_grammar):
        """Varsayılanlarda EMPATHIZE var."""
        empathize = default_grammar.get_by_dialogue_act("empathize")
        assert len(empathize) > 0

    def test_defaults_have_ask(self, default_grammar):
        """Varsayılanlarda ASK var."""
        ask = default_grammar.get_by_dialogue_act("ask")
        assert len(ask) > 0

    def test_defaults_at_least_15(self, default_grammar):
        """En az 15 varsayılan construction."""
        assert default_grammar.count_total() >= 15


# ============================================================================
# 7. Sayım ve İstatistik Testleri
# ============================================================================

class TestCountAndStats:
    """Sayım ve istatistik testleri."""

    def test_count_total(self, default_grammar):
        """Toplam sayım."""
        total = default_grammar.count_total()
        assert total > 0

    def test_count_by_level(self, default_grammar):
        """Katman başına sayım."""
        counts = default_grammar.count_by_level()
        assert counts[ConstructionLevel.DEEP] > 0
        assert counts[ConstructionLevel.MIDDLE] > 0
        assert counts[ConstructionLevel.SURFACE] > 0

    def test_count_matches_get_all(self, default_grammar):
        """Sayım, tümünü getirme ile tutarlı."""
        total = default_grammar.count_total()
        all_constructions = default_grammar.get_all_constructions()
        assert total == len(all_constructions)

    def test_get_all_constructions(self, default_grammar):
        """Tüm construction'ları getir."""
        all_constructions = default_grammar.get_all_constructions()
        assert len(all_constructions) > 0


# ============================================================================
# 8. Clear ve Temizleme Testleri
# ============================================================================

class TestClear:
    """Temizleme testleri."""

    def test_clear_removes_all(self, default_grammar):
        """Clear tüm construction'ları kaldırır."""
        default_grammar.clear()
        assert default_grammar.count_total() == 0

    def test_clear_clears_index(self, default_grammar):
        """Clear index'i de temizler."""
        default_grammar.clear()
        inform = default_grammar.get_by_dialogue_act("inform")
        assert len(inform) == 0
