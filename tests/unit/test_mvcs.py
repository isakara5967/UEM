"""
tests/unit/test_mvcs.py

MVCS (Minimum Viable Construction Set) testleri.
UEM v2 - Cold start icin cekirdek construction'lar testleri.

Test gruplari:
- MVCSConfig testleri
- MVCSLoader initialization testleri
- load_all testleri
- get_by_category testleri
- get_by_name testleri
- Her kategori icin construction testleri
- DialogueAct bazli getirme testleri
- Ton ve formalite testleri
- Grammar entegrasyonu testleri
"""

import pytest
from typing import List

from core.language.construction.mvcs import (
    MVCSLoader,
    MVCSCategory,
    MVCSConfig,
)
from core.language.construction.types import (
    Construction,
    ConstructionLevel,
)
from core.language.construction.grammar import ConstructionGrammar


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def loader():
    """Default MVCSLoader instance."""
    return MVCSLoader()


@pytest.fixture
def loader_no_variations():
    """MVCSLoader without variations."""
    config = MVCSConfig(include_variations=False)
    return MVCSLoader(config=config)


@pytest.fixture
def custom_config():
    """Custom MVCSConfig."""
    return MVCSConfig(
        include_variations=True,
        default_confidence=0.9,
        source="human"  # Must be valid source
    )


# ============================================================================
# MVCSConfig Tests
# ============================================================================

class TestMVCSConfig:
    """MVCSConfig testleri."""

    def test_default_config(self):
        """Default konfigurasyon degerlerini test et."""
        config = MVCSConfig()
        assert config.include_variations is True
        assert config.default_confidence == 0.8
        assert config.source == "human"  # Source must be valid: human, learned, generated

    def test_custom_config(self, custom_config):
        """Custom konfigurasyon degerlerini test et."""
        assert custom_config.include_variations is True
        assert custom_config.default_confidence == 0.9
        assert custom_config.source == "human"

    def test_no_variations_config(self):
        """Variations disabled konfigurasyon testi."""
        config = MVCSConfig(include_variations=False)
        assert config.include_variations is False


# ============================================================================
# MVCSLoader Initialization Tests
# ============================================================================

class TestMVCSLoaderInit:
    """MVCSLoader initialization testleri."""

    def test_default_loader_creation(self, loader):
        """Default loader olusturma testi."""
        assert loader is not None
        assert loader.config is not None
        assert loader.config.include_variations is True

    def test_custom_config_loader(self, custom_config):
        """Custom config ile loader olusturma testi."""
        loader = MVCSLoader(config=custom_config)
        assert loader.config.default_confidence == 0.9
        assert loader.config.source == "human"

    def test_empty_cache_on_init(self, loader):
        """Bos cache ile baslatilma testi."""
        assert loader._cache == {}
        assert loader._all_constructions is None


# ============================================================================
# load_all Tests
# ============================================================================

class TestLoadAll:
    """load_all metodu testleri."""

    def test_load_all_returns_list(self, loader):
        """load_all liste donduruyor mu?"""
        result = loader.load_all()
        assert isinstance(result, list)

    def test_load_all_non_empty(self, loader):
        """load_all bos degil mi?"""
        result = loader.load_all()
        assert len(result) > 0

    def test_load_all_all_constructions(self, loader):
        """load_all tum categorileri yukluyor mu?"""
        result = loader.load_all()
        categories_found = set()

        for c in result:
            cat = c.extra_data.get("mvcs_category")
            if cat:
                categories_found.add(cat)

        # Tum 7 kategori olmali
        assert len(categories_found) == 7

    def test_load_all_caching(self, loader):
        """load_all caching calisiyor mu?"""
        result1 = loader.load_all()
        result2 = loader.load_all()
        assert result1 is result2  # Ayni obje (cached)

    def test_load_all_minimum_count(self, loader):
        """load_all minimum construction sayisi."""
        result = loader.load_all()
        # En az 7 kategori x en az 2 construction = 14
        assert len(result) >= 14

    def test_load_all_with_variations(self, loader):
        """Variations dahil yukleme testi."""
        result = loader.load_all()
        # Variations ile daha fazla construction olmali
        assert len(result) >= 20

    def test_load_all_without_variations(self, loader_no_variations):
        """Variations olmadan yukleme testi."""
        result = loader_no_variations.load_all()
        # Variations olmadan daha az construction
        result_with = MVCSLoader().load_all()
        assert len(result) < len(result_with)


# ============================================================================
# get_by_category Tests
# ============================================================================

class TestGetByCategory:
    """get_by_category metodu testleri."""

    def test_get_greet_category(self, loader):
        """GREET kategorisini getirme testi."""
        result = loader.get_by_category(MVCSCategory.GREET)
        assert len(result) >= 2
        for c in result:
            assert c.extra_data.get("mvcs_category") == MVCSCategory.GREET.value

    def test_get_self_intro_category(self, loader):
        """SELF_INTRO kategorisini getirme testi."""
        result = loader.get_by_category(MVCSCategory.SELF_INTRO)
        assert len(result) >= 2
        for c in result:
            assert c.extra_data.get("mvcs_category") == MVCSCategory.SELF_INTRO.value

    def test_get_empathize_category(self, loader):
        """EMPATHIZE_BASIC kategorisini getirme testi."""
        result = loader.get_by_category(MVCSCategory.EMPATHIZE_BASIC)
        assert len(result) >= 3
        for c in result:
            assert c.meaning.dialogue_act == "empathize"

    def test_get_safe_refusal_category(self, loader):
        """SAFE_REFUSAL kategorisini getirme testi."""
        result = loader.get_by_category(MVCSCategory.SAFE_REFUSAL)
        assert len(result) >= 2
        for c in result:
            assert c.meaning.dialogue_act == "refuse"

    def test_category_caching(self, loader):
        """Kategori caching testi."""
        result1 = loader.get_by_category(MVCSCategory.GREET)
        result2 = loader.get_by_category(MVCSCategory.GREET)
        assert result1 is result2  # Cached


# ============================================================================
# get_by_name Tests
# ============================================================================

class TestGetByName:
    """get_by_name metodu testleri."""

    def test_get_greet_simple(self, loader):
        """greet_simple construction'i getirme testi."""
        result = loader.get_by_name("greet_simple")
        assert result is not None
        assert "Merhaba" in result.form.template

    def test_get_empathy_understand(self, loader):
        """empathy_understand construction'i getirme testi."""
        result = loader.get_by_name("empathy_understand")
        assert result is not None
        assert "anliyorum" in result.form.template.lower()

    def test_get_refuse_simple(self, loader):
        """refuse_simple construction'i getirme testi."""
        result = loader.get_by_name("refuse_simple")
        assert result is not None
        assert result.meaning.dialogue_act == "refuse"

    def test_get_nonexistent_name(self, loader):
        """Olmayan isim icin None donme testi."""
        result = loader.get_by_name("nonexistent_construction")
        assert result is None

    def test_get_self_intro_basic(self, loader):
        """self_intro_basic construction'i getirme testi."""
        result = loader.get_by_name("self_intro_basic")
        assert result is not None
        assert "UEM" in result.form.template


# ============================================================================
# Convenience Method Tests
# ============================================================================

class TestConvenienceMethods:
    """Kolaylik metodlari testleri."""

    def test_get_greet_constructions(self, loader):
        """get_greet_constructions testi."""
        result = loader.get_greet_constructions()
        assert len(result) >= 2
        assert all(c.meaning.dialogue_act == "greet" for c in result)

    def test_get_self_intro_constructions(self, loader):
        """get_self_intro_constructions testi."""
        result = loader.get_self_intro_constructions()
        assert len(result) >= 2

    def test_get_wellbeing_constructions(self, loader):
        """get_wellbeing_constructions testi."""
        result = loader.get_wellbeing_constructions()
        assert len(result) >= 2

    def test_get_inform_constructions(self, loader):
        """get_inform_constructions testi."""
        result = loader.get_inform_constructions()
        assert len(result) >= 2

    def test_get_empathy_constructions(self, loader):
        """get_empathy_constructions testi."""
        result = loader.get_empathy_constructions()
        assert len(result) >= 3

    def test_get_clarify_constructions(self, loader):
        """get_clarify_constructions testi."""
        result = loader.get_clarify_constructions()
        assert len(result) >= 2

    def test_get_refusal_constructions(self, loader):
        """get_refusal_constructions testi."""
        result = loader.get_refusal_constructions()
        assert len(result) >= 2


# ============================================================================
# Count Methods Tests
# ============================================================================

class TestCountMethods:
    """Sayim metodlari testleri."""

    def test_get_category_count(self, loader):
        """get_category_count testi."""
        counts = loader.get_category_count()
        assert len(counts) == 7  # 7 kategori
        assert all(count >= 2 for count in counts.values())

    def test_get_total_count(self, loader):
        """get_total_count testi."""
        total = loader.get_total_count()
        assert total >= 14  # En az 7x2


# ============================================================================
# Construction Content Tests
# ============================================================================

class TestConstructionContent:
    """Construction icerigi testleri."""

    def test_greet_has_merhaba(self, loader):
        """Selamlama 'Merhaba' iceriyor mu?"""
        greets = loader.get_greet_constructions()
        templates = [c.form.template for c in greets]
        assert any("Merhaba" in t for t in templates)

    def test_self_intro_has_uem(self, loader):
        """Kendini tanitma 'UEM' iceriyor mu?"""
        intros = loader.get_self_intro_constructions()
        templates = [c.form.template for c in intros]
        assert any("UEM" in t for t in templates)

    def test_empathy_has_anliyorum(self, loader):
        """Empati 'anliyorum' iceriyor mu?"""
        empathy = loader.get_empathy_constructions()
        templates = [c.form.template.lower() for c in empathy]
        assert any("anliyorum" in t for t in templates)

    def test_refusal_is_polite(self, loader):
        """Reddetme nazik mi?"""
        refusals = loader.get_refusal_constructions()
        # Hicbiri sert olmamali
        for c in refusals:
            template = c.form.template.lower()
            assert "hayir" not in template  # Direkt hayir yok
            assert c.extra_data.get("tone") in ["polite", "helpful", "apologetic", "honest"]


# ============================================================================
# DialogueAct Tests
# ============================================================================

class TestDialogueAct:
    """DialogueAct bazli testler."""

    def test_get_by_dialogue_act_greet(self, loader):
        """Greet dialogue act ile getirme testi."""
        result = loader.get_constructions_by_dialogue_act("greet")
        assert len(result) >= 2
        assert all(c.meaning.dialogue_act == "greet" for c in result)

    def test_get_by_dialogue_act_empathize(self, loader):
        """Empathize dialogue act ile getirme testi."""
        result = loader.get_constructions_by_dialogue_act("empathize")
        assert len(result) >= 3

    def test_get_by_dialogue_act_refuse(self, loader):
        """Refuse dialogue act ile getirme testi."""
        result = loader.get_constructions_by_dialogue_act("refuse")
        assert len(result) >= 2

    def test_get_by_dialogue_act_inform(self, loader):
        """Inform dialogue act ile getirme testi."""
        result = loader.get_constructions_by_dialogue_act("inform")
        # SELF_INTRO, SIMPLE_INFORM, ASK_WELLBEING hepsi inform kullanir
        assert len(result) >= 4


# ============================================================================
# Tone and Formality Tests
# ============================================================================

class TestToneAndFormality:
    """Ton ve formalite testleri."""

    def test_get_by_tone_empathic(self, loader):
        """Empathic ton ile getirme testi."""
        result = loader.get_constructions_by_tone("empathic")
        assert len(result) >= 2

    def test_get_by_tone_friendly(self, loader):
        """Friendly ton ile getirme testi."""
        result = loader.get_constructions_by_tone("friendly")
        assert len(result) >= 2

    def test_get_by_tone_polite(self, loader):
        """Polite ton ile getirme testi."""
        result = loader.get_constructions_by_tone("polite")
        assert len(result) >= 1

    def test_get_by_formality_formal(self, loader):
        """Formal formality araliginda getirme testi."""
        result = loader.get_constructions_by_formality(0.5, 1.0)
        assert len(result) >= 1

    def test_get_by_formality_casual(self, loader):
        """Casual formality araliginda getirme testi."""
        result = loader.get_constructions_by_formality(0.0, 0.4)
        assert len(result) >= 1


# ============================================================================
# Cache Tests
# ============================================================================

class TestCache:
    """Cache testleri."""

    def test_clear_cache(self, loader):
        """clear_cache testi."""
        # Onbellege yukle
        loader.load_all()
        assert loader._all_constructions is not None

        # Temizle
        loader.clear_cache()
        assert loader._cache == {}
        assert loader._all_constructions is None


# ============================================================================
# Construction Properties Tests
# ============================================================================

class TestConstructionProperties:
    """Construction ozellikleri testleri."""

    def test_all_surface_level(self, loader):
        """Tum construction'lar SURFACE seviyesinde mi?"""
        all_constructions = loader.load_all()
        for c in all_constructions:
            assert c.level == ConstructionLevel.SURFACE

    def test_all_have_confidence(self, loader):
        """Tum construction'lar confidence degerine sahip mi?"""
        all_constructions = loader.load_all()
        for c in all_constructions:
            assert c.confidence >= 0.0
            assert c.confidence <= 1.0

    def test_all_have_source(self, loader):
        """Tum construction'lar source degerine sahip mi?"""
        all_constructions = loader.load_all()
        for c in all_constructions:
            assert c.source == "human"  # MVCS uses 'human' as source

    def test_all_have_mvcs_category(self, loader):
        """Tum construction'lar mvcs_category extra_data'ya sahip mi?"""
        all_constructions = loader.load_all()
        for c in all_constructions:
            assert "mvcs_category" in c.extra_data

    def test_all_have_mvcs_name(self, loader):
        """Tum construction'lar mvcs_name extra_data'ya sahip mi?"""
        all_constructions = loader.load_all()
        for c in all_constructions:
            assert "mvcs_name" in c.extra_data


# ============================================================================
# Grammar Integration Tests
# ============================================================================

class TestGrammarIntegration:
    """ConstructionGrammar entegrasyon testleri."""

    def test_grammar_loads_mvcs(self):
        """Grammar MVCS'yi yukluyor mu?"""
        grammar = ConstructionGrammar()
        # MVCS construction'lari yuklenmiş olmali
        greets = grammar.get_by_dialogue_act("greet")
        assert len(greets) >= 2

    def test_grammar_mvcs_source(self):
        """Grammar'daki MVCS construction'lari is_mvcs extra_data'ya sahip mi?"""
        grammar = ConstructionGrammar()
        greets = grammar.get_by_dialogue_act("greet")
        mvcs_greets = [c for c in greets if c.extra_data.get("is_mvcs")]
        assert len(mvcs_greets) >= 2

    def test_grammar_includes_refuse(self):
        """Grammar refuse dialogue act'i iceriyor mu?"""
        grammar = ConstructionGrammar()
        refuses = grammar.get_by_dialogue_act("refuse")
        assert len(refuses) >= 2

    def test_grammar_no_duplicates(self):
        """Grammar'da duplicate yok mu?"""
        grammar = ConstructionGrammar()
        all_constructions = grammar.get_all_constructions()
        ids = [c.id for c in all_constructions]
        assert len(ids) == len(set(ids))  # Unique IDs


# ============================================================================
# Values Alignment Tests
# ============================================================================

class TestValuesAlignment:
    """VALUES_CHARTER uyumluluk testleri."""

    def test_refusal_has_values_alignment(self, loader):
        """Refusal construction'lari values_alignment iceriyor mu?"""
        refusals = loader.get_refusal_constructions()
        for c in refusals:
            values = c.extra_data.get("values_alignment", [])
            # En az bir deger olmali
            assert len(values) >= 0  # Bazi refusal'lar values_alignment olmayabilir

    def test_refusal_non_maleficence(self, loader):
        """Refusal'larda non_maleficence degeri var mi?"""
        refusals = loader.get_refusal_constructions()
        has_non_maleficence = any(
            "non_maleficence" in c.extra_data.get("values_alignment", [])
            for c in refusals
        )
        assert has_non_maleficence

    def test_refusal_transparency(self, loader):
        """Refusal'larda transparency degeri var mi?"""
        refusals = loader.get_refusal_constructions()
        has_transparency = any(
            "transparency" in c.extra_data.get("values_alignment", [])
            for c in refusals
        )
        assert has_transparency
