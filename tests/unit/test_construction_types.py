"""
tests/unit/test_construction_types.py

Construction Grammar types test suite.
Faz 4 - 3 katmanlı dil yapısı testleri.

Test count: 25+
"""

import pytest
from datetime import datetime
from core.language.construction import (
    ConstructionLevel,
    SlotType,
    Slot,
    MorphologyRule,
    ConstructionForm,
    ConstructionMeaning,
    Construction,
    generate_construction_id,
    generate_slot_id,
)
from core.language.construction.types import generate_morphology_rule_id


# ============================================================================
# ConstructionLevel Enum Tests
# ============================================================================

class TestConstructionLevel:
    """ConstructionLevel enum tests."""

    def test_construction_level_values(self):
        """Test ConstructionLevel has all required values."""
        expected = ["deep", "middle", "surface"]
        actual = [level.value for level in ConstructionLevel]
        for exp in expected:
            assert exp in actual

    def test_construction_level_count(self):
        """Test ConstructionLevel has 3 levels."""
        assert len(ConstructionLevel) == 3


# ============================================================================
# SlotType Enum Tests
# ============================================================================

class TestSlotType:
    """SlotType enum tests."""

    def test_slot_type_values(self):
        """Test SlotType has all required values."""
        expected = [
            "entity", "verb", "adjective", "adverb",
            "number", "time", "place", "reason",
            "connector", "filler"
        ]
        actual = [st.value for st in SlotType]
        for exp in expected:
            assert exp in actual

    def test_slot_type_count(self):
        """Test SlotType has 10 types."""
        assert len(SlotType) == 10


# ============================================================================
# Slot Tests
# ============================================================================

class TestSlot:
    """Slot dataclass tests."""

    def test_slot_creation(self):
        """Test Slot creation."""
        slot = Slot(
            id="slot_123",
            name="subject",
            slot_type=SlotType.ENTITY
        )
        assert slot.id == "slot_123"
        assert slot.name == "subject"
        assert slot.slot_type == SlotType.ENTITY

    def test_slot_default_values(self):
        """Test Slot default values."""
        slot = Slot(
            id="slot_1",
            name="verb",
            slot_type=SlotType.VERB
        )
        assert slot.required is True
        assert slot.default is None
        assert slot.constraints == {}

    def test_slot_validate_value_required(self):
        """Test validate_value for required slots."""
        slot = Slot(
            id="slot_1",
            name="subject",
            slot_type=SlotType.ENTITY,
            required=True
        )
        assert not slot.validate_value("")  # Empty string fails for required
        assert slot.validate_value("Ali")

    def test_slot_validate_value_with_default(self):
        """Test validate_value with default."""
        slot = Slot(
            id="slot_1",
            name="subject",
            slot_type=SlotType.ENTITY,
            required=True,
            default="O"  # Default pronoun
        )
        assert slot.validate_value("")  # Empty OK when default exists

    def test_slot_validate_value_min_length(self):
        """Test validate_value with min_length constraint."""
        slot = Slot(
            id="slot_1",
            name="name",
            slot_type=SlotType.ENTITY,
            constraints={"min_length": 3}
        )
        assert not slot.validate_value("AB")  # Too short
        assert slot.validate_value("ABC")

    def test_slot_validate_value_max_length(self):
        """Test validate_value with max_length constraint."""
        slot = Slot(
            id="slot_1",
            name="name",
            slot_type=SlotType.ENTITY,
            constraints={"max_length": 10}
        )
        assert not slot.validate_value("A" * 11)  # Too long
        assert slot.validate_value("A" * 10)

    def test_slot_validate_value_allowed_values(self):
        """Test validate_value with allowed_values constraint."""
        slot = Slot(
            id="slot_1",
            name="connector",
            slot_type=SlotType.CONNECTOR,
            constraints={"allowed_values": ["ve", "ama", "veya"]}
        )
        assert slot.validate_value("ve")
        assert slot.validate_value("ama")
        assert not slot.validate_value("ancak")

    def test_slot_get_value(self):
        """Test get_value method."""
        slot = Slot(
            id="slot_1",
            name="subject",
            slot_type=SlotType.ENTITY,
            default="Ben"
        )
        assert slot.get_value("Ali") == "Ali"  # Provided value
        assert slot.get_value(None) == "Ben"   # Default value


# ============================================================================
# MorphologyRule Tests
# ============================================================================

class TestMorphologyRule:
    """MorphologyRule dataclass tests."""

    def test_morphology_rule_creation(self):
        """Test MorphologyRule creation."""
        rule = MorphologyRule(
            id="morph_123",
            name="vowel_harmony_a",
            rule_type="vowel_harmony",
            condition="last_vowel in [a, ı]",
            transformation="append_a",
            priority=10
        )
        assert rule.id == "morph_123"
        assert rule.rule_type == "vowel_harmony"
        assert rule.priority == 10

    def test_morphology_rule_with_examples(self):
        """Test MorphologyRule with examples."""
        rule = MorphologyRule(
            id="morph_1",
            name="vowel_harmony_e",
            rule_type="vowel_harmony",
            condition="last_vowel in [e, i]",
            transformation="append_e",
            examples=["ev -> eve", "gemi -> gemiye"]
        )
        assert len(rule.examples) == 2


# ============================================================================
# ConstructionForm Tests
# ============================================================================

class TestConstructionForm:
    """ConstructionForm dataclass tests."""

    def test_construction_form_creation(self):
        """Test ConstructionForm creation."""
        form = ConstructionForm(template="{subject} {object}'ı {verb}")
        assert "{subject}" in form.template

    def test_construction_form_with_slots(self):
        """Test ConstructionForm with slots."""
        subject_slot = Slot(id="s1", name="subject", slot_type=SlotType.ENTITY)
        verb_slot = Slot(id="s2", name="verb", slot_type=SlotType.VERB)

        form = ConstructionForm(
            template="{subject} {verb}",
            slots={"subject": subject_slot, "verb": verb_slot}
        )
        assert form.has_slot("subject")
        assert form.has_slot("verb")
        assert not form.has_slot("object")

    def test_construction_form_get_slot_names(self):
        """Test get_slot_names method."""
        subject_slot = Slot(id="s1", name="subject", slot_type=SlotType.ENTITY)
        verb_slot = Slot(id="s2", name="verb", slot_type=SlotType.VERB)

        form = ConstructionForm(
            template="{subject} {verb}",
            slots={"subject": subject_slot, "verb": verb_slot}
        )
        names = form.get_slot_names()
        assert "subject" in names
        assert "verb" in names

    def test_construction_form_get_required_slots(self):
        """Test get_required_slots method."""
        required_slot = Slot(id="s1", name="subject", slot_type=SlotType.ENTITY, required=True)
        optional_slot = Slot(id="s2", name="adverb", slot_type=SlotType.ADVERB, required=False)

        form = ConstructionForm(
            template="{subject} {adverb} gitti",
            slots={"subject": required_slot, "adverb": optional_slot}
        )
        required = form.get_required_slots()
        assert len(required) == 1
        assert required[0].name == "subject"

    def test_construction_form_validate_slots_success(self):
        """Test validate_slots with valid values."""
        subject_slot = Slot(id="s1", name="subject", slot_type=SlotType.ENTITY)
        verb_slot = Slot(id="s2", name="verb", slot_type=SlotType.VERB)

        form = ConstructionForm(
            template="{subject} {verb}",
            slots={"subject": subject_slot, "verb": verb_slot}
        )
        errors = form.validate_slots({"subject": "Ali", "verb": "geldi"})
        assert errors == []

    def test_construction_form_validate_slots_missing(self):
        """Test validate_slots with missing required value."""
        subject_slot = Slot(id="s1", name="subject", slot_type=SlotType.ENTITY, required=True)

        form = ConstructionForm(
            template="{subject} geldi",
            slots={"subject": subject_slot}
        )
        errors = form.validate_slots({})
        assert len(errors) == 1
        assert "Missing required slot" in errors[0]


# ============================================================================
# ConstructionMeaning Tests
# ============================================================================

class TestConstructionMeaning:
    """ConstructionMeaning dataclass tests."""

    def test_construction_meaning_creation(self):
        """Test ConstructionMeaning creation."""
        meaning = ConstructionMeaning(
            dialogue_act="inform",
            semantic_roles={"agent": "subject", "patient": "object"}
        )
        assert meaning.dialogue_act == "inform"
        assert meaning.semantic_roles["agent"] == "subject"

    def test_construction_meaning_with_preconditions(self):
        """Test ConstructionMeaning with preconditions."""
        meaning = ConstructionMeaning(
            dialogue_act="answer",
            preconditions=["user_asked_question", "topic_is_clear"],
            effects=["question_answered", "user_informed"]
        )
        assert len(meaning.preconditions) == 2
        assert len(meaning.effects) == 2

    def test_construction_meaning_matches_context(self):
        """Test matches_context method."""
        meaning = ConstructionMeaning(
            dialogue_act="empathize",
            context_requirements={"user_emotional": True, "topic": "personal"}
        )

        matching_ctx = {"user_emotional": True, "topic": "personal", "other": "data"}
        assert meaning.matches_context(matching_ctx)

        missing_ctx = {"user_emotional": True}
        assert not meaning.matches_context(missing_ctx)

        wrong_ctx = {"user_emotional": False, "topic": "personal"}
        assert not meaning.matches_context(wrong_ctx)


# ============================================================================
# Construction Tests
# ============================================================================

class TestConstruction:
    """Construction dataclass tests."""

    @pytest.fixture
    def simple_construction(self):
        """Create a simple construction for testing."""
        subject_slot = Slot(id="s1", name="subject", slot_type=SlotType.ENTITY)
        form = ConstructionForm(
            template="{subject} geldi",
            slots={"subject": subject_slot}
        )
        meaning = ConstructionMeaning(dialogue_act="inform")

        return Construction(
            id="cons_123",
            level=ConstructionLevel.MIDDLE,
            form=form,
            meaning=meaning
        )

    def test_construction_creation(self, simple_construction):
        """Test Construction creation."""
        assert simple_construction.id == "cons_123"
        assert simple_construction.level == ConstructionLevel.MIDDLE
        assert simple_construction.source == "human"

    def test_construction_confidence_validation(self):
        """Test Construction confidence validation."""
        form = ConstructionForm(template="test")
        meaning = ConstructionMeaning(dialogue_act="inform")

        with pytest.raises(ValueError):
            Construction(
                id="c1",
                level=ConstructionLevel.DEEP,
                form=form,
                meaning=meaning,
                confidence=1.5
            )

    def test_construction_source_validation(self):
        """Test Construction source validation."""
        form = ConstructionForm(template="test")
        meaning = ConstructionMeaning(dialogue_act="inform")

        with pytest.raises(ValueError):
            Construction(
                id="c1",
                level=ConstructionLevel.DEEP,
                form=form,
                meaning=meaning,
                source="invalid_source"
            )

    def test_construction_valid_sources(self):
        """Test all valid sources."""
        form = ConstructionForm(template="test")
        meaning = ConstructionMeaning(dialogue_act="inform")

        for source in ["human", "learned", "generated"]:
            c = Construction(
                id=f"c_{source}",
                level=ConstructionLevel.DEEP,
                form=form,
                meaning=meaning,
                source=source
            )
            assert c.source == source

    def test_construction_success_rate(self, simple_construction):
        """Test success_rate property."""
        assert simple_construction.success_rate == 0.5  # Default with no uses

        simple_construction.success_count = 8
        simple_construction.failure_count = 2
        assert simple_construction.success_rate == 0.8

    def test_construction_total_uses(self, simple_construction):
        """Test total_uses property."""
        assert simple_construction.total_uses == 0

        simple_construction.success_count = 5
        simple_construction.failure_count = 3
        assert simple_construction.total_uses == 8

    def test_construction_is_reliable(self, simple_construction):
        """Test is_reliable property."""
        # Not reliable initially
        assert not simple_construction.is_reliable

        # Still not reliable (not enough uses)
        simple_construction.success_count = 2
        simple_construction.failure_count = 0
        assert not simple_construction.is_reliable

        # Reliable: enough uses + high success rate
        simple_construction.success_count = 8
        simple_construction.failure_count = 2
        assert simple_construction.is_reliable

        # Not reliable: enough uses but low success rate
        simple_construction.success_count = 2
        simple_construction.failure_count = 8
        assert not simple_construction.is_reliable

    def test_construction_record_success(self, simple_construction):
        """Test record_success method."""
        initial_confidence = simple_construction.confidence

        simple_construction.record_success()

        assert simple_construction.success_count == 1
        assert simple_construction.last_used is not None
        assert simple_construction.confidence > initial_confidence

    def test_construction_record_failure(self, simple_construction):
        """Test record_failure method."""
        simple_construction.confidence = 0.5
        initial_confidence = simple_construction.confidence

        simple_construction.record_failure()

        assert simple_construction.failure_count == 1
        assert simple_construction.last_used is not None
        assert simple_construction.confidence < initial_confidence

    def test_construction_realize(self, simple_construction):
        """Test realize method."""
        result = simple_construction.realize({"subject": "Ali"})
        assert result == "Ali geldi"

    def test_construction_realize_missing_slot(self, simple_construction):
        """Test realize with missing required slot."""
        result = simple_construction.realize({})
        assert result is None  # Validation failed

    def test_construction_matches_dialogue_act(self, simple_construction):
        """Test matches_dialogue_act method."""
        assert simple_construction.matches_dialogue_act("inform")
        assert not simple_construction.matches_dialogue_act("warn")

    def test_construction_to_dict(self, simple_construction):
        """Test to_dict method."""
        d = simple_construction.to_dict()

        assert d["id"] == "cons_123"
        assert d["level"] == "middle"
        assert d["template"] == "{subject} geldi"
        assert d["dialogue_act"] == "inform"
        assert d["source"] == "human"


# ============================================================================
# ID Generation Tests
# ============================================================================

class TestConstructionIDGeneration:
    """Construction ID generation function tests."""

    def test_construction_id_format(self):
        """Test construction ID format."""
        cid = generate_construction_id()
        assert cid.startswith("cons_")
        assert len(cid) == 17  # "cons_" + 12 hex chars

    def test_construction_id_uniqueness(self):
        """Test construction ID uniqueness."""
        ids = [generate_construction_id() for _ in range(100)]
        assert len(ids) == len(set(ids))

    def test_slot_id_format(self):
        """Test slot ID format."""
        sid = generate_slot_id()
        assert sid.startswith("slot_")
        assert len(sid) == 17  # "slot_" + 12 hex chars

    def test_slot_id_uniqueness(self):
        """Test slot ID uniqueness."""
        ids = [generate_slot_id() for _ in range(100)]
        assert len(ids) == len(set(ids))

    def test_morphology_rule_id_format(self):
        """Test morphology rule ID format."""
        mid = generate_morphology_rule_id()
        assert mid.startswith("morph_")
        assert len(mid) == 18  # "morph_" + 12 hex chars

    def test_morphology_rule_id_uniqueness(self):
        """Test morphology rule ID uniqueness."""
        ids = [generate_morphology_rule_id() for _ in range(100)]
        assert len(ids) == len(set(ids))
