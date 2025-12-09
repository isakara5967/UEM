"""
tests/unit/test_learning.py

Learning Module Tests - Feedback ve Pattern testleri.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import numpy as np

from core.learning import (
    FeedbackType,
    PatternType,
    Feedback,
    Pattern,
    LearningOutcome,
    FeedbackCollector,
    PatternStorage,
    generate_feedback_id,
    generate_pattern_id,
)


# ============================================================================
# FeedbackType Tests
# ============================================================================

class TestFeedbackType:
    """FeedbackType enum testleri."""

    def test_feedback_types(self):
        """Test all feedback types exist."""
        assert FeedbackType.POSITIVE == "positive"
        assert FeedbackType.NEGATIVE == "negative"
        assert FeedbackType.NEUTRAL == "neutral"
        assert FeedbackType.EXPLICIT == "explicit"
        assert FeedbackType.IMPLICIT == "implicit"

    def test_feedback_type_is_string(self):
        """Test FeedbackType is string enum."""
        assert isinstance(FeedbackType.POSITIVE, str)
        assert FeedbackType.POSITIVE.value == "positive"


# ============================================================================
# PatternType Tests
# ============================================================================

class TestPatternType:
    """PatternType enum testleri."""

    def test_pattern_types(self):
        """Test all pattern types exist."""
        assert PatternType.RESPONSE == "response"
        assert PatternType.BEHAVIOR == "behavior"
        assert PatternType.EMOTION == "emotion"
        assert PatternType.LANGUAGE == "language"

    def test_pattern_type_is_string(self):
        """Test PatternType is string enum."""
        assert isinstance(PatternType.RESPONSE, str)
        assert PatternType.RESPONSE.value == "response"


# ============================================================================
# Feedback Tests
# ============================================================================

class TestFeedback:
    """Feedback dataclass testleri."""

    def test_create_feedback(self):
        """Test creating feedback."""
        feedback = Feedback(
            id="fb_123",
            interaction_id="int_456",
            feedback_type=FeedbackType.POSITIVE,
            value=0.8,
            timestamp=datetime.now()
        )
        assert feedback.id == "fb_123"
        assert feedback.interaction_id == "int_456"
        assert feedback.feedback_type == FeedbackType.POSITIVE
        assert feedback.value == 0.8

    def test_feedback_value_range_valid(self):
        """Test valid feedback value range."""
        # Valid values
        feedback_low = Feedback(
            id="fb_1", interaction_id="int_1",
            feedback_type=FeedbackType.NEGATIVE,
            value=-1.0, timestamp=datetime.now()
        )
        assert feedback_low.value == -1.0

        feedback_high = Feedback(
            id="fb_2", interaction_id="int_2",
            feedback_type=FeedbackType.POSITIVE,
            value=1.0, timestamp=datetime.now()
        )
        assert feedback_high.value == 1.0

    def test_feedback_value_range_invalid(self):
        """Test invalid feedback value raises error."""
        with pytest.raises(ValueError):
            Feedback(
                id="fb_1", interaction_id="int_1",
                feedback_type=FeedbackType.POSITIVE,
                value=1.5, timestamp=datetime.now()
            )

        with pytest.raises(ValueError):
            Feedback(
                id="fb_2", interaction_id="int_2",
                feedback_type=FeedbackType.NEGATIVE,
                value=-1.5, timestamp=datetime.now()
            )

    def test_feedback_optional_fields(self):
        """Test feedback optional fields."""
        feedback = Feedback(
            id="fb_123",
            interaction_id="int_456",
            feedback_type=FeedbackType.EXPLICIT,
            value=0.5,
            timestamp=datetime.now(),
            user_id="user_789",
            context="test context",
            reason="user liked it"
        )
        assert feedback.user_id == "user_789"
        assert feedback.context == "test context"
        assert feedback.reason == "user liked it"


# ============================================================================
# Pattern Tests
# ============================================================================

class TestPattern:
    """Pattern dataclass testleri."""

    def test_pattern_creation(self):
        """Test creating pattern."""
        pattern = Pattern(
            id="pat_123",
            pattern_type=PatternType.RESPONSE,
            content="Hello, how can I help?"
        )
        assert pattern.id == "pat_123"
        assert pattern.pattern_type == PatternType.RESPONSE
        assert pattern.content == "Hello, how can I help?"
        assert pattern.success_count == 0
        assert pattern.failure_count == 0

    def test_pattern_success_rate_no_uses(self):
        """Test success rate with no uses."""
        pattern = Pattern(
            id="pat_1",
            pattern_type=PatternType.RESPONSE,
            content="test"
        )
        assert pattern.success_rate == 0.5  # Default

    def test_pattern_success_rate_with_uses(self):
        """Test success rate calculation."""
        pattern = Pattern(
            id="pat_1",
            pattern_type=PatternType.RESPONSE,
            content="test",
            success_count=8,
            failure_count=2
        )
        assert pattern.success_rate == 0.8

    def test_pattern_average_reward_no_uses(self):
        """Test average reward with no uses."""
        pattern = Pattern(
            id="pat_1",
            pattern_type=PatternType.BEHAVIOR,
            content="test"
        )
        assert pattern.average_reward == 0.0

    def test_pattern_average_reward_with_uses(self):
        """Test average reward calculation."""
        pattern = Pattern(
            id="pat_1",
            pattern_type=PatternType.BEHAVIOR,
            content="test",
            success_count=5,
            failure_count=5,
            total_reward=10.0
        )
        assert pattern.average_reward == 1.0  # 10.0 / 10 = 1.0

    def test_pattern_total_uses(self):
        """Test total uses property."""
        pattern = Pattern(
            id="pat_1",
            pattern_type=PatternType.EMOTION,
            content="test",
            success_count=7,
            failure_count=3
        )
        assert pattern.total_uses == 10


# ============================================================================
# LearningOutcome Tests
# ============================================================================

class TestLearningOutcome:
    """LearningOutcome dataclass testleri."""

    def test_create_learning_outcome(self):
        """Test creating learning outcome."""
        feedback = Feedback(
            id="fb_123",
            interaction_id="int_456",
            feedback_type=FeedbackType.POSITIVE,
            value=0.9,
            timestamp=datetime.now()
        )
        outcome = LearningOutcome(
            pattern_id="pat_789",
            feedback=feedback,
            reward=0.8,
            pattern_updated=True
        )
        assert outcome.pattern_id == "pat_789"
        assert outcome.feedback == feedback
        assert outcome.reward == 0.8
        assert outcome.pattern_updated is True


# ============================================================================
# FeedbackCollector Tests
# ============================================================================

class TestFeedbackCollector:
    """FeedbackCollector testleri."""

    def test_record_feedback(self):
        """Test recording feedback."""
        collector = FeedbackCollector()
        feedback = collector.record(
            interaction_id="int_123",
            feedback_type=FeedbackType.POSITIVE,
            value=0.7
        )
        assert feedback.interaction_id == "int_123"
        assert feedback.value == 0.7
        assert feedback.id.startswith("fb_")

    def test_record_explicit_positive(self):
        """Test recording explicit positive feedback."""
        collector = FeedbackCollector()
        feedback = collector.record_explicit(
            interaction_id="int_123",
            positive=True,
            reason="Great response!"
        )
        assert feedback.feedback_type == FeedbackType.EXPLICIT
        assert feedback.value == 1.0
        assert feedback.reason == "Great response!"

    def test_record_explicit_negative(self):
        """Test recording explicit negative feedback."""
        collector = FeedbackCollector()
        feedback = collector.record_explicit(
            interaction_id="int_123",
            positive=False,
            reason="Not helpful"
        )
        assert feedback.feedback_type == FeedbackType.EXPLICIT
        assert feedback.value == -1.0
        assert feedback.reason == "Not helpful"

    def test_record_implicit(self):
        """Test recording implicit feedback."""
        collector = FeedbackCollector()
        signals = {
            "continued_conversation": True,
            "response_time": "fast",
            "sentiment_change": "positive"
        }
        feedback = collector.record_implicit(
            interaction_id="int_123",
            signals=signals
        )
        assert feedback.feedback_type == FeedbackType.IMPLICIT
        assert feedback.value > 0  # Should be positive
        assert "continued_conversation=True" in feedback.context

    def test_record_implicit_negative_signals(self):
        """Test recording implicit feedback with negative signals."""
        collector = FeedbackCollector()
        signals = {
            "continued_conversation": False,
            "response_time": "slow",
            "sentiment_change": "negative"
        }
        feedback = collector.record_implicit(
            interaction_id="int_123",
            signals=signals
        )
        assert feedback.value < 0  # Should be negative

    def test_get_feedback_history(self):
        """Test getting feedback history."""
        collector = FeedbackCollector()
        for i in range(5):
            collector.record(
                interaction_id=f"int_{i}",
                feedback_type=FeedbackType.NEUTRAL,
                value=0.0
            )
        history = collector.get_history(limit=3)
        assert len(history) == 3

    def test_get_feedback_by_interaction(self):
        """Test getting feedback by interaction."""
        collector = FeedbackCollector()
        collector.record("int_1", FeedbackType.POSITIVE, 0.5)
        collector.record("int_1", FeedbackType.NEGATIVE, -0.3)
        collector.record("int_2", FeedbackType.NEUTRAL, 0.0)

        feedbacks = collector.get_feedback("int_1")
        assert len(feedbacks) == 2

    def test_get_feedback_by_user(self):
        """Test getting feedback by user."""
        collector = FeedbackCollector()
        collector.record("int_1", FeedbackType.POSITIVE, 0.5, user_id="user_1")
        collector.record("int_2", FeedbackType.NEGATIVE, -0.3, user_id="user_1")
        collector.record("int_3", FeedbackType.NEUTRAL, 0.0, user_id="user_2")

        user1_feedbacks = collector.get_by_user("user_1")
        assert len(user1_feedbacks) == 2

    def test_get_average_score(self):
        """Test getting average score."""
        collector = FeedbackCollector()
        collector.record("int_1", FeedbackType.POSITIVE, 1.0)
        collector.record("int_2", FeedbackType.NEGATIVE, -1.0)
        collector.record("int_3", FeedbackType.NEUTRAL, 0.0)

        avg = collector.get_average_score()
        assert avg == 0.0  # (1.0 + -1.0 + 0.0) / 3

    def test_get_average_score_by_user(self):
        """Test getting average score by user."""
        collector = FeedbackCollector()
        collector.record("int_1", FeedbackType.POSITIVE, 0.8, user_id="user_1")
        collector.record("int_2", FeedbackType.POSITIVE, 0.6, user_id="user_1")

        avg = collector.get_average_score("user_1")
        assert avg == 0.7  # (0.8 + 0.6) / 2

    def test_feedback_stats(self):
        """Test feedback statistics."""
        collector = FeedbackCollector()
        collector.record("int_1", FeedbackType.POSITIVE, 0.8, user_id="user_1")
        collector.record("int_2", FeedbackType.NEGATIVE, -0.5, user_id="user_2")
        collector.record_explicit("int_3", positive=True)
        collector.record_implicit("int_4", {"continued_conversation": True})

        stats = collector.get_stats()
        assert stats["total_feedback"] == 4
        assert stats["unique_users"] == 2
        assert stats["unique_interactions"] == 4
        assert stats["explicit_count"] == 1
        assert stats["implicit_count"] == 1

    def test_feedback_value_clamped(self):
        """Test feedback value is clamped to valid range."""
        collector = FeedbackCollector()
        feedback = collector.record("int_1", FeedbackType.POSITIVE, 5.0)
        assert feedback.value == 1.0  # Clamped to max

        feedback2 = collector.record("int_2", FeedbackType.NEGATIVE, -5.0)
        assert feedback2.value == -1.0  # Clamped to min

    def test_clear_feedback(self):
        """Test clearing all feedback."""
        collector = FeedbackCollector()
        for i in range(10):
            collector.record(f"int_{i}", FeedbackType.NEUTRAL, 0.0)

        count = collector.clear()
        assert count == 10
        assert len(collector.get_history()) == 0


# ============================================================================
# PatternStorage Tests
# ============================================================================

class TestPatternStorage:
    """PatternStorage testleri."""

    def test_store_pattern(self):
        """Test storing pattern."""
        storage = PatternStorage()
        pattern = storage.store(
            content="Hello, how can I help?",
            pattern_type=PatternType.RESPONSE
        )
        assert pattern.content == "Hello, how can I help?"
        assert pattern.pattern_type == PatternType.RESPONSE
        assert pattern.id.startswith("pat_")

    def test_get_pattern(self):
        """Test getting pattern by ID."""
        storage = PatternStorage()
        pattern = storage.store("test content", PatternType.BEHAVIOR)

        retrieved = storage.get(pattern.id)
        assert retrieved is not None
        assert retrieved.content == "test content"

    def test_get_nonexistent_pattern(self):
        """Test getting nonexistent pattern."""
        storage = PatternStorage()
        result = storage.get("nonexistent_id")
        assert result is None

    def test_find_similar_patterns_no_encoder(self):
        """Test finding similar patterns without encoder."""
        storage = PatternStorage()  # No encoder
        storage.store("test", PatternType.RESPONSE)

        similar = storage.find_similar("test")
        assert similar == []  # Empty without encoder

    def test_find_similar_patterns_with_encoder(self):
        """Test finding similar patterns with mock encoder."""
        # Create mock encoder
        encoder = Mock()
        encoder.encode = Mock(side_effect=lambda x: np.array([1.0, 0.0, 0.0]))

        storage = PatternStorage(encoder=encoder)
        pattern = storage.store("hello", PatternType.RESPONSE)

        # Use lower thresholds for testing (production uses min_similarity=0.85, min_uses=3)
        similar = storage.find_similar("hello", k=5, min_similarity=0.5, min_uses=0)
        assert len(similar) == 1
        assert similar[0][0].id == pattern.id
        assert similar[0][1] == 1.0  # Same vector = similarity 1.0

    def test_update_pattern_stats_success(self):
        """Test updating pattern stats on success."""
        storage = PatternStorage()
        pattern = storage.store("test", PatternType.RESPONSE)

        storage.update_stats(pattern.id, success=True, reward=0.5)

        updated = storage.get(pattern.id)
        assert updated.success_count == 1
        assert updated.failure_count == 0
        assert updated.total_reward == 0.5

    def test_update_pattern_stats_failure(self):
        """Test updating pattern stats on failure."""
        storage = PatternStorage()
        pattern = storage.store("test", PatternType.RESPONSE)

        storage.update_stats(pattern.id, success=False, reward=-0.3)

        updated = storage.get(pattern.id)
        assert updated.success_count == 0
        assert updated.failure_count == 1
        assert updated.total_reward == -0.3

    def test_get_best_patterns(self):
        """Test getting best patterns."""
        storage = PatternStorage()

        # Create patterns with different success rates
        p1 = storage.store("pattern1", PatternType.RESPONSE)
        p2 = storage.store("pattern2", PatternType.RESPONSE)
        p3 = storage.store("pattern3", PatternType.RESPONSE)

        # Update stats
        for _ in range(8):
            storage.update_stats(p1.id, True, 1.0)
        for _ in range(2):
            storage.update_stats(p1.id, False, -0.5)

        for _ in range(5):
            storage.update_stats(p2.id, True, 0.5)
        for _ in range(5):
            storage.update_stats(p2.id, False, -0.5)

        for _ in range(2):
            storage.update_stats(p3.id, True, 0.5)
        for _ in range(8):
            storage.update_stats(p3.id, False, -0.5)

        best = storage.get_best_patterns(PatternType.RESPONSE, k=3)
        assert len(best) == 3
        assert best[0].id == p1.id  # 80% success rate
        assert best[1].id == p2.id  # 50% success rate
        assert best[2].id == p3.id  # 20% success rate

    def test_get_worst_patterns(self):
        """Test getting worst patterns."""
        storage = PatternStorage()

        p1 = storage.store("pattern1", PatternType.BEHAVIOR)
        p2 = storage.store("pattern2", PatternType.BEHAVIOR)

        # p1: 20% success
        for _ in range(2):
            storage.update_stats(p1.id, True, 0.5)
        for _ in range(8):
            storage.update_stats(p1.id, False, -0.5)

        # p2: 80% success
        for _ in range(8):
            storage.update_stats(p2.id, True, 1.0)
        for _ in range(2):
            storage.update_stats(p2.id, False, -0.5)

        worst = storage.get_worst_patterns(PatternType.BEHAVIOR, k=2)
        assert len(worst) == 2
        assert worst[0].id == p1.id  # Lowest success rate first

    def test_prune_weak_patterns(self):
        """Test pruning weak patterns."""
        storage = PatternStorage()

        p1 = storage.store("weak", PatternType.RESPONSE)
        p2 = storage.store("strong", PatternType.RESPONSE)

        # p1: 10% success rate (weak)
        storage.update_stats(p1.id, True, 0.5)
        for _ in range(9):
            storage.update_stats(p1.id, False, -0.5)

        # p2: 90% success rate (strong)
        for _ in range(9):
            storage.update_stats(p2.id, True, 1.0)
        storage.update_stats(p2.id, False, -0.5)

        # Prune with min_uses=5 and max_failure_rate=0.7
        pruned = storage.prune_weak_patterns(min_uses=5, max_failure_rate=0.7)
        assert pruned == 1
        assert storage.get(p1.id) is None  # Pruned
        assert storage.get(p2.id) is not None  # Kept

    def test_pattern_stats(self):
        """Test pattern statistics."""
        storage = PatternStorage()
        storage.store("response1", PatternType.RESPONSE)
        storage.store("response2", PatternType.RESPONSE)
        storage.store("behavior1", PatternType.BEHAVIOR)

        stats = storage.stats()
        assert stats["total_patterns"] == 3
        assert stats["by_type"]["response"] == 2
        assert stats["by_type"]["behavior"] == 1

    def test_pattern_count(self):
        """Test pattern count."""
        storage = PatternStorage()
        assert storage.count() == 0

        storage.store("test1", PatternType.RESPONSE)
        storage.store("test2", PatternType.BEHAVIOR)
        assert storage.count() == 2

    def test_clear_patterns(self):
        """Test clearing patterns."""
        storage = PatternStorage()
        storage.store("test1", PatternType.RESPONSE)
        storage.store("test2", PatternType.BEHAVIOR)

        count = storage.clear()
        assert count == 2
        assert storage.count() == 0

    def test_get_all_patterns(self):
        """Test getting all patterns."""
        storage = PatternStorage()
        storage.store("r1", PatternType.RESPONSE)
        storage.store("r2", PatternType.RESPONSE)
        storage.store("b1", PatternType.BEHAVIOR)

        all_patterns = storage.get_all()
        assert len(all_patterns) == 3

        response_only = storage.get_all(PatternType.RESPONSE)
        assert len(response_only) == 2


# ============================================================================
# Integration Tests
# ============================================================================

class TestLearningIntegration:
    """Integration tests for learning module."""

    def test_integration_feedback_pattern(self):
        """Test feedback and pattern integration."""
        collector = FeedbackCollector()
        storage = PatternStorage()

        # Store a pattern
        pattern = storage.store(
            "Merhaba, size nasil yardimci olabilirim?",
            PatternType.RESPONSE
        )

        # Record feedback for this pattern
        feedback = collector.record_explicit(
            interaction_id=f"int_{pattern.id}",
            positive=True,
            reason="Very helpful response"
        )

        # Update pattern stats based on feedback
        storage.update_stats(
            pattern.id,
            success=feedback.value > 0,
            reward=feedback.value
        )

        # Create learning outcome
        outcome = LearningOutcome(
            pattern_id=pattern.id,
            feedback=feedback,
            reward=feedback.value,
            pattern_updated=True
        )

        # Verify
        updated_pattern = storage.get(pattern.id)
        assert updated_pattern.success_count == 1
        assert updated_pattern.total_reward == 1.0
        assert outcome.pattern_updated is True


# ============================================================================
# ID Generation Tests
# ============================================================================

class TestIdGeneration:
    """ID generation tests."""

    def test_generate_feedback_id(self):
        """Test feedback ID generation."""
        id1 = generate_feedback_id()
        id2 = generate_feedback_id()
        assert id1.startswith("fb_")
        assert id2.startswith("fb_")
        assert id1 != id2

    def test_generate_pattern_id(self):
        """Test pattern ID generation."""
        id1 = generate_pattern_id()
        id2 = generate_pattern_id()
        assert id1.startswith("pat_")
        assert id2.startswith("pat_")
        assert id1 != id2
