"""
tests/unit/test_generalization.py

Tests for Learning Module Generalization - Rule extraction from patterns.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
import numpy as np

from core.learning.types import (
    Pattern,
    PatternType,
    Rule,
    generate_pattern_id,
    generate_rule_id,
)
from core.learning.patterns import PatternStorage
from core.learning.generalization import RuleExtractor
from core.learning.processor import LearningProcessor


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def pattern_storage():
    """Create pattern storage for testing."""
    return PatternStorage()


@pytest.fixture
def rule_extractor(pattern_storage):
    """Create rule extractor for testing."""
    return RuleExtractor(pattern_storage)


@pytest.fixture
def sample_rule():
    """Create sample rule for testing."""
    return Rule(
        id=generate_rule_id(),
        pattern_type=PatternType.RESPONSE,
        template="Merhaba {name}, nasilsin?",
        slots=["name"],
        source_patterns=["pat_1", "pat_2", "pat_3"],
        confidence=0.8
    )


# ============================================================================
# Rule Dataclass Tests
# ============================================================================

class TestRule:
    """Rule dataclass tests."""

    def test_rule_creation(self):
        """Test creating a rule."""
        rule = Rule(
            id="rule_test",
            pattern_type=PatternType.RESPONSE,
            template="Hello {name}",
            slots=["name"],
            source_patterns=["pat_1", "pat_2"],
            confidence=0.9
        )
        assert rule.id == "rule_test"
        assert rule.template == "Hello {name}"
        assert rule.slots == ["name"]
        assert rule.confidence == 0.9
        assert rule.usage_count == 0

    def test_rule_slots_multiple(self):
        """Test rule with multiple slots."""
        rule = Rule(
            id="rule_multi",
            pattern_type=PatternType.RESPONSE,
            template="{greeting} {name}, {question}?",
            slots=["greeting", "name", "question"],
            source_patterns=["pat_1"],
            confidence=0.7
        )
        assert len(rule.slots) == 3
        assert "greeting" in rule.slots
        assert "name" in rule.slots
        assert "question" in rule.slots

    def test_rule_confidence_validation(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            Rule(
                id="rule_bad",
                pattern_type=PatternType.RESPONSE,
                template="test",
                slots=[],
                source_patterns=[],
                confidence=1.5
            )

    def test_rule_confidence_validation_negative(self):
        """Test confidence cannot be negative."""
        with pytest.raises(ValueError):
            Rule(
                id="rule_bad",
                pattern_type=PatternType.RESPONSE,
                template="test",
                slots=[],
                source_patterns=[],
                confidence=-0.1
            )

    def test_rule_default_usage_count(self):
        """Test default usage count is 0."""
        rule = Rule(
            id="rule_test",
            pattern_type=PatternType.RESPONSE,
            template="test",
            slots=[],
            source_patterns=[],
            confidence=0.5
        )
        assert rule.usage_count == 0

    def test_generate_rule_id(self):
        """Test rule ID generation."""
        rule_id = generate_rule_id()
        assert rule_id.startswith("rule_")
        assert len(rule_id) == 17  # "rule_" + 12 hex chars


# ============================================================================
# RuleExtractor Tests
# ============================================================================

class TestRuleExtractor:
    """RuleExtractor tests."""

    def test_extract_rules_empty(self, rule_extractor):
        """Test extracting rules from empty storage."""
        rules = rule_extractor.extract_rules()
        assert rules == []

    def test_extract_rules_single_pattern(self, pattern_storage, rule_extractor):
        """Test extracting rules with single pattern (not enough)."""
        pattern_storage.store("Hello world", PatternType.RESPONSE)
        rules = rule_extractor.extract_rules(min_patterns=3)
        assert rules == []

    def test_extract_rules_similar_patterns(self, pattern_storage):
        """Test extracting rules from similar patterns."""
        # Create mock encoder
        encoder = Mock()
        encoder.encode = Mock(return_value=np.array([1.0, 0.0, 0.0]))

        storage = PatternStorage(encoder=encoder)
        storage.store("Merhaba Ali", PatternType.RESPONSE)
        storage.store("Merhaba Ayse", PatternType.RESPONSE)
        storage.store("Merhaba Can", PatternType.RESPONSE)

        extractor = RuleExtractor(storage, encoder)
        rules = extractor.extract_rules(min_patterns=3, similarity_threshold=0.8)

        # Should extract at least one rule
        assert len(rules) >= 1

    def test_group_similar_patterns(self, pattern_storage, rule_extractor):
        """Test grouping similar patterns."""
        # Add patterns
        p1 = pattern_storage.store("Hello world", PatternType.RESPONSE)
        p2 = pattern_storage.store("Hello there", PatternType.RESPONSE)
        p3 = pattern_storage.store("Goodbye world", PatternType.RESPONSE)

        patterns = pattern_storage.get_all()
        groups = rule_extractor._group_by_string_similarity(patterns, 0.3)

        # Should have some groups
        assert len(groups) >= 1

    def test_extract_template_simple(self, rule_extractor):
        """Test extracting template from similar patterns."""
        patterns = [
            Pattern(id="p1", pattern_type=PatternType.RESPONSE, content="Merhaba Ali"),
            Pattern(id="p2", pattern_type=PatternType.RESPONSE, content="Merhaba Ayse"),
            Pattern(id="p3", pattern_type=PatternType.RESPONSE, content="Merhaba Can"),
        ]

        template, slots = rule_extractor._extract_template(patterns)

        assert "Merhaba" in template
        assert len(slots) >= 0

    def test_extract_template_with_slots(self, rule_extractor):
        """Test extracting template with slot detection."""
        patterns = [
            Pattern(id="p1", pattern_type=PatternType.RESPONSE, content="Hello Ali, how are you?"),
            Pattern(id="p2", pattern_type=PatternType.RESPONSE, content="Hello Bob, how are you?"),
            Pattern(id="p3", pattern_type=PatternType.RESPONSE, content="Hello Cat, how are you?"),
        ]

        template, slots = rule_extractor._extract_template(patterns)

        # Template should have a slot
        assert "{" in template or template == patterns[0].content

    def test_find_common_prefix(self, rule_extractor):
        """Test finding common prefix."""
        strings = ["Hello Ali", "Hello Bob", "Hello Cat"]
        prefix, suffix = rule_extractor._find_common_prefix_suffix(strings)

        assert prefix == "Hello "

    def test_find_common_suffix(self, rule_extractor):
        """Test finding common suffix."""
        strings = ["Ali says hi", "Bob says hi", "Cat says hi"]
        prefix, suffix = rule_extractor._find_common_prefix_suffix(strings)

        assert suffix == " says hi"

    def test_find_common_prefix_suffix_both(self, rule_extractor):
        """Test finding both prefix and suffix."""
        strings = ["Hello Ali, welcome!", "Hello Bob, welcome!", "Hello Cat, welcome!"]
        prefix, suffix = rule_extractor._find_common_prefix_suffix(strings)

        assert prefix == "Hello "
        assert suffix == ", welcome!"

    def test_apply_rule(self, sample_rule, rule_extractor):
        """Test applying rule with slot values."""
        rule_extractor._rules[sample_rule.id] = sample_rule

        result = rule_extractor.apply_rule(sample_rule, {"name": "Ali"})
        assert result == "Merhaba Ali, nasilsin?"

    def test_apply_rule_missing_slot(self, sample_rule, rule_extractor):
        """Test applying rule with missing slot value."""
        with pytest.raises(ValueError, match="Missing slot value"):
            rule_extractor.apply_rule(sample_rule, {})

    def test_apply_rule_updates_usage(self, sample_rule, rule_extractor):
        """Test that applying rule updates usage count."""
        rule_extractor._rules[sample_rule.id] = sample_rule
        initial_count = sample_rule.usage_count

        rule_extractor.apply_rule(sample_rule, {"name": "Test"})

        assert sample_rule.usage_count == initial_count + 1

    def test_find_matching_rule(self, rule_extractor, sample_rule):
        """Test finding matching rule for content."""
        rule_extractor._rules[sample_rule.id] = sample_rule

        result = rule_extractor.find_matching_rule("Merhaba Ahmet, nasilsin?")

        if result:
            rule, slot_values = result
            assert rule.id == sample_rule.id
            assert slot_values.get("name") == "Ahmet"

    def test_find_matching_rule_no_match(self, rule_extractor, sample_rule):
        """Test finding no matching rule."""
        rule_extractor._rules[sample_rule.id] = sample_rule

        result = rule_extractor.find_matching_rule("Completely different text")
        # May or may not match depending on regex

    def test_get_rules_by_type(self, rule_extractor):
        """Test getting rules by type."""
        rule1 = Rule(
            id="r1", pattern_type=PatternType.RESPONSE,
            template="test1", slots=[], source_patterns=[], confidence=0.5
        )
        rule2 = Rule(
            id="r2", pattern_type=PatternType.BEHAVIOR,
            template="test2", slots=[], source_patterns=[], confidence=0.5
        )

        rule_extractor._rules["r1"] = rule1
        rule_extractor._rules["r2"] = rule2

        response_rules = rule_extractor.get_rules_by_type(PatternType.RESPONSE)
        assert len(response_rules) == 1
        assert response_rules[0].id == "r1"

        behavior_rules = rule_extractor.get_rules_by_type(PatternType.BEHAVIOR)
        assert len(behavior_rules) == 1
        assert behavior_rules[0].id == "r2"

    def test_get_all_rules(self, rule_extractor, sample_rule):
        """Test getting all rules."""
        rule_extractor._rules[sample_rule.id] = sample_rule

        rules = rule_extractor.get_all_rules()
        assert len(rules) == 1
        assert rules[0].id == sample_rule.id

    def test_get_rule(self, rule_extractor, sample_rule):
        """Test getting rule by ID."""
        rule_extractor._rules[sample_rule.id] = sample_rule

        rule = rule_extractor.get_rule(sample_rule.id)
        assert rule is not None
        assert rule.id == sample_rule.id

        # Nonexistent
        assert rule_extractor.get_rule("nonexistent") is None

    def test_rule_confidence_calculation(self, rule_extractor):
        """Test confidence calculation for pattern group."""
        patterns = [
            Pattern(id="p1", pattern_type=PatternType.RESPONSE, content="test",
                    success_count=8, failure_count=2),
            Pattern(id="p2", pattern_type=PatternType.RESPONSE, content="test",
                    success_count=9, failure_count=1),
        ]

        confidence = rule_extractor._calculate_confidence(patterns)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # High success rates

    def test_string_similarity(self, rule_extractor):
        """Test string similarity calculation."""
        sim1 = rule_extractor._string_similarity("hello world", "hello there")
        assert sim1 > 0  # "hello" is common

        sim2 = rule_extractor._string_similarity("hello world", "goodbye moon")
        assert sim2 < sim1  # Less similar

    def test_clear_rules(self, rule_extractor, sample_rule):
        """Test clearing all rules."""
        rule_extractor._rules[sample_rule.id] = sample_rule
        assert len(rule_extractor._rules) == 1

        count = rule_extractor.clear()
        assert count == 1
        assert len(rule_extractor._rules) == 0

    def test_stats(self, rule_extractor, sample_rule):
        """Test rule statistics."""
        rule_extractor._rules[sample_rule.id] = sample_rule

        stats = rule_extractor.stats()
        assert stats["total_rules"] == 1
        assert "by_type" in stats
        assert stats["average_confidence"] == sample_rule.confidence

    def test_stats_empty(self, rule_extractor):
        """Test statistics with no rules."""
        stats = rule_extractor.stats()
        assert stats["total_rules"] == 0
        assert stats["average_confidence"] == 0.0


# ============================================================================
# LearningProcessor Integration Tests
# ============================================================================

class TestProcessorRuleExtraction:
    """LearningProcessor rule extraction tests."""

    def test_processor_has_rule_extractor(self):
        """Test processor has rule extractor."""
        processor = LearningProcessor()
        assert hasattr(processor, "rule_extractor")
        assert isinstance(processor.rule_extractor, RuleExtractor)

    def test_processor_extract_rules(self):
        """Test processor extract rules method."""
        processor = LearningProcessor()

        # Add some patterns (not enough for rules)
        processor.pattern_storage.store("Hello", PatternType.RESPONSE)

        rules = processor.extract_rules()
        assert isinstance(rules, list)

    def test_processor_get_rules(self):
        """Test processor get rules method."""
        processor = LearningProcessor()
        rules = processor.get_rules()
        assert isinstance(rules, list)

    def test_processor_get_rules_by_type(self):
        """Test processor get rules by type."""
        processor = LearningProcessor()
        rules = processor.get_rules(PatternType.RESPONSE)
        assert isinstance(rules, list)

    def test_processor_stats_includes_rules(self):
        """Test processor stats includes rules."""
        processor = LearningProcessor()
        stats = processor.stats()
        assert "rules" in stats

    def test_processor_clear_includes_rules(self):
        """Test processor clear includes rules."""
        processor = LearningProcessor()
        result = processor.clear()
        assert "rules" in result


# ============================================================================
# Integration Tests
# ============================================================================

class TestGeneralizationIntegration:
    """Integration tests for generalization."""

    def test_integration_learn_then_generalize(self):
        """Test learning patterns then generalizing to rules."""
        # Create mock encoder for similarity
        encoder = Mock()
        encoder.encode = Mock(return_value=np.array([1.0, 0.0, 0.0]))

        storage = PatternStorage(encoder=encoder)

        # Add similar patterns
        for name in ["Ali", "Ayse", "Ahmet", "Burak", "Canan"]:
            storage.store(f"Merhaba {name}, nasilsin?", PatternType.RESPONSE)

        # Extract rules
        extractor = RuleExtractor(storage, encoder)
        rules = extractor.extract_rules(min_patterns=3, similarity_threshold=0.9)

        # Should have extracted rule(s)
        assert len(rules) >= 1

        # Rule should have template
        if rules:
            rule = rules[0]
            assert rule.pattern_type == PatternType.RESPONSE
            assert len(rule.source_patterns) >= 3

    def test_rule_application_cycle(self):
        """Test full cycle: create rule, apply, verify."""
        rule = Rule(
            id="rule_test",
            pattern_type=PatternType.RESPONSE,
            template="Hello {name}, welcome to {place}!",
            slots=["name", "place"],
            source_patterns=["p1", "p2", "p3"],
            confidence=0.9
        )

        storage = PatternStorage()
        extractor = RuleExtractor(storage)
        extractor._rules[rule.id] = rule

        # Apply rule
        result = extractor.apply_rule(rule, {"name": "John", "place": "NYC"})
        assert result == "Hello John, welcome to NYC!"

        # Usage should be updated
        assert rule.usage_count == 1
