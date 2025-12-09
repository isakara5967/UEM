"""
tests/unit/test_construction_realizer.py

ConstructionRealizer testleri - Construction + slot values → Cümle üretimi.

Test kategorileri:
1. ConstructionRealizer oluşturma
2. Realize metodu
3. Slot doğrulama
4. Template doldurma
5. Morfoloji uygulama
6. Post-processing
7. Çoklu realize
8. Yardımcı metodlar
"""

import pytest

from core.language.construction.realizer import (
    ConstructionRealizer,
    ConstructionRealizerConfig,
    RealizationResult,
)
from core.language.construction.grammar import ConstructionGrammar
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
def default_realizer():
    """Varsayılan realizer."""
    return ConstructionRealizer()


@pytest.fixture
def custom_config():
    """Özel realizer konfigürasyonu."""
    return ConstructionRealizerConfig(
        apply_morphology=False,
        use_defaults=True,
        strict_validation=True,
        capitalize_first=True,
        add_punctuation=True
    )


@pytest.fixture
def custom_realizer(custom_config):
    """Özel config'li realizer."""
    return ConstructionRealizer(config=custom_config)


@pytest.fixture
def simple_construction():
    """Basit construction."""
    return Construction(
        id=generate_construction_id(),
        level=ConstructionLevel.SURFACE,
        form=ConstructionForm(
            template="{konu} {bilgi}",
            slots={
                "konu": Slot(
                    id=generate_slot_id(),
                    name="konu",
                    slot_type=SlotType.ENTITY,
                    required=True
                ),
                "bilgi": Slot(
                    id=generate_slot_id(),
                    name="bilgi",
                    slot_type=SlotType.ENTITY,
                    required=True
                )
            }
        ),
        meaning=ConstructionMeaning(dialogue_act="inform")
    )


@pytest.fixture
def construction_with_defaults():
    """Varsayılanlı construction."""
    return Construction(
        id=generate_construction_id(),
        level=ConstructionLevel.SURFACE,
        form=ConstructionForm(
            template="Evet, {onay}",
            slots={
                "onay": Slot(
                    id=generate_slot_id(),
                    name="onay",
                    slot_type=SlotType.ENTITY,
                    required=False,
                    default="anladım"
                )
            }
        ),
        meaning=ConstructionMeaning(dialogue_act="acknowledge")
    )


@pytest.fixture
def no_slot_construction():
    """Slot'suz construction."""
    return Construction(
        id=generate_construction_id(),
        level=ConstructionLevel.SURFACE,
        form=ConstructionForm(
            template="Anlıyorum",
            slots={}
        ),
        meaning=ConstructionMeaning(dialogue_act="acknowledge")
    )


@pytest.fixture
def question_construction():
    """Soru construction'ı."""
    return Construction(
        id=generate_construction_id(),
        level=ConstructionLevel.SURFACE,
        form=ConstructionForm(
            template="{soru_kelimesi} {konu}",
            slots={
                "soru_kelimesi": Slot(
                    id=generate_slot_id(),
                    name="soru_kelimesi",
                    slot_type=SlotType.FILLER,
                    required=True
                ),
                "konu": Slot(
                    id=generate_slot_id(),
                    name="konu",
                    slot_type=SlotType.ENTITY,
                    required=True
                )
            },
            intonation="rising"
        ),
        meaning=ConstructionMeaning(dialogue_act="ask")
    )


@pytest.fixture
def warn_construction():
    """Uyarı construction'ı."""
    return Construction(
        id=generate_construction_id(),
        level=ConstructionLevel.SURFACE,
        form=ConstructionForm(
            template="Dikkat! {uyari}",
            slots={
                "uyari": Slot(
                    id=generate_slot_id(),
                    name="uyari",
                    slot_type=SlotType.ENTITY,
                    required=True
                )
            }
        ),
        meaning=ConstructionMeaning(dialogue_act="warn")
    )


# ============================================================================
# 1. ConstructionRealizer Oluşturma Testleri
# ============================================================================

class TestConstructionRealizerCreation:
    """ConstructionRealizer oluşturma testleri."""

    def test_create_default_realizer(self):
        """Varsayılan realizer oluşturma."""
        realizer = ConstructionRealizer()
        assert realizer is not None
        assert realizer.config is not None

    def test_create_with_custom_config(self, custom_config):
        """Özel config ile realizer oluşturma."""
        realizer = ConstructionRealizer(config=custom_config)
        assert realizer.config.apply_morphology is False
        assert realizer.config.strict_validation is True

    def test_default_config_values(self, default_realizer):
        """Varsayılan config değerleri."""
        assert default_realizer.config.apply_morphology is True
        assert default_realizer.config.use_defaults is True
        assert default_realizer.config.capitalize_first is True
        assert default_realizer.config.add_punctuation is True


# ============================================================================
# 2. Realize Metodu Testleri
# ============================================================================

class TestRealizeMethod:
    """Realize metodu testleri."""

    def test_realize_returns_result(self, default_realizer, simple_construction):
        """Realize RealizationResult döndürür."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Python", "bilgi": "programlama dilidir"}
        )
        assert isinstance(result, RealizationResult)

    def test_realize_success(self, default_realizer, simple_construction):
        """Başarılı realize."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Python", "bilgi": "programlama dilidir"}
        )
        assert result.success is True
        assert len(result.text) > 0

    def test_realize_has_text(self, default_realizer, simple_construction):
        """Result'ta text var."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Python", "bilgi": "programlama dilidir"}
        )
        assert "Python" in result.text
        assert "programlama dilidir" in result.text

    def test_realize_has_construction_id(self, default_realizer, simple_construction):
        """Result'ta construction ID var."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Python", "bilgi": "test"}
        )
        assert result.construction_id == simple_construction.id

    def test_realize_has_filled_slots(self, default_realizer, simple_construction):
        """Result'ta filled_slots var."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Python", "bilgi": "test"}
        )
        assert "konu" in result.filled_slots
        assert result.filled_slots["konu"] == "Python"

    def test_realize_no_slots(self, default_realizer, no_slot_construction):
        """Slot'suz construction realize."""
        result = default_realizer.realize(no_slot_construction, {})
        assert result.success is True
        assert "Anlıyorum" in result.text


# ============================================================================
# 3. Slot Doğrulama Testleri
# ============================================================================

class TestSlotValidation:
    """Slot doğrulama testleri."""

    def test_validate_slots_success(self, default_realizer, simple_construction):
        """Başarılı slot doğrulama."""
        is_valid, missing, errors = default_realizer.validate_slots(
            simple_construction,
            {"konu": "Python", "bilgi": "test"}
        )
        assert is_valid is True
        assert len(missing) == 0

    def test_validate_slots_missing_required(self, default_realizer, simple_construction):
        """Eksik zorunlu slot."""
        is_valid, missing, errors = default_realizer.validate_slots(
            simple_construction,
            {"konu": "Python"}  # bilgi eksik
        )
        assert "bilgi" in missing

    def test_validate_slots_with_defaults(self, default_realizer, construction_with_defaults):
        """Varsayılanlı slot doğrulama."""
        is_valid, missing, errors = default_realizer.validate_slots(
            construction_with_defaults,
            {}  # onay varsayılan kullanılacak
        )
        assert is_valid is True

    def test_strict_validation_fails(self, custom_realizer, simple_construction):
        """Katı doğrulama başarısız."""
        # custom_realizer has strict_validation=True
        result = custom_realizer.realize(
            simple_construction,
            {"konu": "Python"}  # bilgi eksik
        )
        assert result.success is False


# ============================================================================
# 4. Template Doldurma Testleri
# ============================================================================

class TestTemplateFilling:
    """Template doldurma testleri."""

    def test_fill_template(self, default_realizer, simple_construction):
        """Template doldurma."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Python", "bilgi": "güzeldir"}
        )
        assert "Python" in result.text
        assert "güzeldir" in result.text

    def test_fill_template_uses_defaults(self, default_realizer, construction_with_defaults):
        """Varsayılan değer kullanımı."""
        result = default_realizer.realize(construction_with_defaults, {})
        assert "anladım" in result.text

    def test_fill_template_override_default(self, default_realizer, construction_with_defaults):
        """Varsayılanı override."""
        result = default_realizer.realize(
            construction_with_defaults,
            {"onay": "tamam"}
        )
        assert "tamam" in result.text
        assert "anladım" not in result.text


# ============================================================================
# 5. Post-processing Testleri
# ============================================================================

class TestPostProcessing:
    """Post-processing testleri."""

    def test_capitalize_first(self, default_realizer, simple_construction):
        """İlk harf büyük."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "python", "bilgi": "test"}
        )
        assert result.text[0].isupper()

    def test_add_period(self, default_realizer, simple_construction):
        """Nokta ekleme."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Python", "bilgi": "test"}
        )
        assert result.text.endswith(".")

    def test_add_question_mark(self, default_realizer, question_construction):
        """Soru işareti ekleme."""
        result = default_realizer.realize(
            question_construction,
            {"soru_kelimesi": "Ne", "konu": "yapıyorsun"}
        )
        assert result.text.endswith("?")

    def test_add_exclamation_for_warn(self, default_realizer, warn_construction):
        """Uyarı için ünlem."""
        result = default_realizer.realize(
            warn_construction,
            {"uyari": "Bu tehlikeli"}
        )
        assert "!" in result.text

    def test_no_double_punctuation(self, default_realizer):
        """Çift noktalama yok."""
        construction = Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="{mesaj}.",
                slots={
                    "mesaj": Slot(
                        id=generate_slot_id(),
                        name="mesaj",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(dialogue_act="inform")
        )
        result = default_realizer.realize(construction, {"mesaj": "Test"})
        assert not result.text.endswith("..")

    def test_trim_whitespace(self, default_realizer, simple_construction):
        """Fazla boşluk temizleme."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Python  ", "bilgi": "  test"}
        )
        assert "  " not in result.text


# ============================================================================
# 6. Morfoloji Testleri
# ============================================================================

class TestMorphology:
    """Morfoloji testleri."""

    def test_morphology_applied_by_default(self, default_realizer, simple_construction):
        """Morfoloji varsayılan olarak uygulanır."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Kitap", "bilgi": "güzel"}
        )
        assert result.success is True

    def test_morphology_disabled(self, simple_construction):
        """Morfoloji devre dışı."""
        config = ConstructionRealizerConfig(apply_morphology=False)
        realizer = ConstructionRealizer(config=config)
        result = realizer.realize(
            simple_construction,
            {"konu": "Kitap", "bilgi": "güzel"}
        )
        assert result.success is True


# ============================================================================
# 7. Çoklu Realize Testleri
# ============================================================================

class TestRealizeMultiple:
    """Çoklu realize testleri."""

    def test_realize_multiple(self, default_realizer, simple_construction, no_slot_construction):
        """Birden fazla construction realize."""
        result = default_realizer.realize_multiple(
            [no_slot_construction, simple_construction],
            {"konu": "Python", "bilgi": "test"}
        )
        assert result.success is True
        assert len(result.text) > 0

    def test_realize_multiple_with_separator(self, default_realizer, no_slot_construction):
        """Özel ayraç ile çoklu realize."""
        construction2 = Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(template="Tamam", slots={}),
            meaning=ConstructionMeaning(dialogue_act="acknowledge")
        )
        result = default_realizer.realize_multiple(
            [no_slot_construction, construction2],
            {},
            separator=" - "
        )
        assert " - " in result.text

    def test_realize_multiple_empty_list(self, default_realizer):
        """Boş liste ile çoklu realize."""
        result = default_realizer.realize_multiple([], {})
        assert result.success is False
        assert result.text == ""


# ============================================================================
# 8. Yardımcı Metod Testleri
# ============================================================================

class TestHelperMethods:
    """Yardımcı metod testleri."""

    def test_get_required_slots(self, default_realizer, simple_construction):
        """Gerekli slot'ları getir."""
        required = default_realizer.get_required_slots(simple_construction)
        assert "konu" in required
        assert "bilgi" in required

    def test_get_required_slots_with_defaults(self, default_realizer, construction_with_defaults):
        """Varsayılanlı slot'lar gerekli değil."""
        required = default_realizer.get_required_slots(construction_with_defaults)
        assert "onay" not in required

    def test_get_slot_types(self, default_realizer, simple_construction):
        """Slot tiplerini getir."""
        types = default_realizer.get_slot_types(simple_construction)
        assert types["konu"] == SlotType.ENTITY
        assert types["bilgi"] == SlotType.ENTITY

    def test_get_slot_types_empty(self, default_realizer, no_slot_construction):
        """Slot'suz construction için boş dict."""
        types = default_realizer.get_slot_types(no_slot_construction)
        assert types == {}


# ============================================================================
# 9. Hata Durumu Testleri
# ============================================================================

class TestErrorCases:
    """Hata durumu testleri."""

    def test_missing_slot_non_strict(self, default_realizer, simple_construction):
        """Katı olmayan modda eksik slot."""
        result = default_realizer.realize(
            simple_construction,
            {"konu": "Python"}  # bilgi eksik
        )
        # Non-strict mode still succeeds but with unfilled slot
        assert result.success is True

    def test_result_has_errors(self, custom_realizer, simple_construction):
        """Result'ta errors var."""
        result = custom_realizer.realize(
            simple_construction,
            {"konu": "Python"}  # bilgi eksik
        )
        assert len(result.errors) > 0

    def test_result_has_missing_slots(self, default_realizer, simple_construction):
        """Result'ta missing_slots var."""
        is_valid, missing, errors = default_realizer.validate_slots(
            simple_construction,
            {"konu": "Python"}
        )
        assert "bilgi" in missing


# ============================================================================
# 10. Entegrasyon Testleri
# ============================================================================

class TestIntegration:
    """Entegrasyon testleri."""

    def test_full_realization_flow(self, default_realizer):
        """Tam realize akışı."""
        construction = Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="{konu} hakkında bilgi: {bilgi}",
                slots={
                    "konu": Slot(
                        id=generate_slot_id(),
                        name="konu",
                        slot_type=SlotType.ENTITY,
                        required=True
                    ),
                    "bilgi": Slot(
                        id=generate_slot_id(),
                        name="bilgi",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(dialogue_act="inform")
        )

        result = default_realizer.realize(
            construction,
            {"konu": "Python", "bilgi": "harika bir dil"}
        )

        assert result.success is True
        assert "Python" in result.text
        assert "harika bir dil" in result.text
        assert result.text[0].isupper()
        assert result.text.endswith(".")

    def test_realize_from_grammar(self, default_realizer):
        """Grammar'dan construction realize."""
        grammar = ConstructionGrammar()
        constructions = grammar.get_by_dialogue_act("acknowledge")

        if constructions:
            result = default_realizer.realize(constructions[0], {})
            assert result.success is True
