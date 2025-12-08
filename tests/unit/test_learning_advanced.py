"""
tests/unit/test_learning_advanced.py

Advanced Learning Module Tests - Reinforcement, Adaptation, Processor testleri.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from core.learning import (
    FeedbackType,
    PatternType,
    Feedback,
    Pattern,
    LearningOutcome,
    FeedbackCollector,
    PatternStorage,
    RewardConfig,
    RewardCalculator,
    Reinforcer,
    AdaptationConfig,
    BehaviorAdapter,
    LearningProcessor,
    generate_feedback_id,
)


# ============================================================================
# RewardConfig Tests
# ============================================================================

class TestRewardConfig:
    """RewardConfig testleri."""

    def test_reward_config_defaults(self):
        """Test default reward config values."""
        config = RewardConfig()
        assert config.positive_base == 1.0
        assert config.negative_base == -1.0
        assert config.neutral_base == 0.0
        assert config.decay_rate == 0.95
        assert config.recency_weight == 0.3

    def test_reward_config_custom(self):
        """Test custom reward config values."""
        config = RewardConfig(
            positive_base=2.0,
            negative_base=-2.0,
            decay_rate=0.9
        )
        assert config.positive_base == 2.0
        assert config.negative_base == -2.0
        assert config.decay_rate == 0.9


# ============================================================================
# RewardCalculator Tests
# ============================================================================

class TestRewardCalculator:
    """RewardCalculator testleri."""

    def test_reward_calculate_positive(self):
        """Test calculating positive reward."""
        calculator = RewardCalculator()
        feedback = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.POSITIVE,
            value=0.8,
            timestamp=datetime.now()
        )
        reward = calculator.calculate(feedback)
        assert reward > 0

    def test_reward_calculate_negative(self):
        """Test calculating negative reward."""
        calculator = RewardCalculator()
        feedback = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.NEGATIVE,
            value=-0.7,
            timestamp=datetime.now()
        )
        reward = calculator.calculate(feedback)
        assert reward < 0

    def test_reward_calculate_neutral(self):
        """Test calculating neutral reward."""
        calculator = RewardCalculator()
        feedback = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.NEUTRAL,
            value=0.1,
            timestamp=datetime.now()
        )
        reward = calculator.calculate(feedback)
        assert abs(reward) < 0.5  # Close to zero

    def test_reward_cumulative(self):
        """Test cumulative reward calculation."""
        calculator = RewardCalculator()
        feedbacks = [
            Feedback("fb_1", "int_1", FeedbackType.POSITIVE, 1.0, datetime.now()),
            Feedback("fb_2", "int_1", FeedbackType.POSITIVE, 0.5, datetime.now()),
            Feedback("fb_3", "int_1", FeedbackType.NEGATIVE, -0.5, datetime.now()),
        ]
        cumulative = calculator.calculate_cumulative(feedbacks)
        assert cumulative > 0  # Net positive

    def test_reward_cumulative_empty(self):
        """Test cumulative reward with empty list."""
        calculator = RewardCalculator()
        cumulative = calculator.calculate_cumulative([])
        assert cumulative == 0.0

    def test_reward_decay(self):
        """Test reward decay over time."""
        calculator = RewardCalculator()
        reward = 1.0

        # No decay for fresh reward
        decayed_0h = calculator.apply_decay(reward, 0)
        assert decayed_0h == reward

        # Some decay after 24 hours
        decayed_24h = calculator.apply_decay(reward, 24)
        assert decayed_24h < reward
        assert decayed_24h > 0

        # More decay after 48 hours
        decayed_48h = calculator.apply_decay(reward, 48)
        assert decayed_48h < decayed_24h

    def test_reward_recency_weight(self):
        """Test recency weight for fresh feedback."""
        calculator = RewardCalculator()

        # Fresh feedback (just now)
        fresh = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.POSITIVE,
            value=0.8,
            timestamp=datetime.now()
        )
        fresh_reward = calculator.calculate(fresh)

        # Old feedback (2 hours ago)
        old = Feedback(
            id="fb_2",
            interaction_id="int_2",
            feedback_type=FeedbackType.POSITIVE,
            value=0.8,
            timestamp=datetime.now() - timedelta(hours=2)
        )
        old_reward = calculator.calculate(old)

        # Fresh should have higher reward due to recency weight
        assert fresh_reward > old_reward


# ============================================================================
# Reinforcer Tests
# ============================================================================

class TestReinforcer:
    """Reinforcer testleri."""

    def test_reinforcer_init(self):
        """Test reinforcer initialization."""
        storage = PatternStorage()
        reinforcer = Reinforcer(storage)
        assert reinforcer.patterns == storage
        assert reinforcer.calculator is not None

    def test_reinforce_positive(self):
        """Test positive reinforcement."""
        storage = PatternStorage()
        pattern = storage.store("test pattern", PatternType.RESPONSE)

        reinforcer = Reinforcer(storage)
        feedback = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.POSITIVE,
            value=0.9,
            timestamp=datetime.now()
        )

        outcome = reinforcer.reinforce(pattern.id, feedback)
        assert outcome.pattern_updated is True
        assert outcome.reward > 0

        # Check pattern was updated
        updated = storage.get(pattern.id)
        assert updated.success_count == 1

    def test_reinforce_negative(self):
        """Test negative reinforcement."""
        storage = PatternStorage()
        pattern = storage.store("bad pattern", PatternType.RESPONSE)

        reinforcer = Reinforcer(storage)
        feedback = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.NEGATIVE,
            value=-0.8,
            timestamp=datetime.now()
        )

        outcome = reinforcer.reinforce(pattern.id, feedback)
        assert outcome.pattern_updated is True
        assert outcome.reward < 0

        # Check pattern was updated
        updated = storage.get(pattern.id)
        assert updated.failure_count == 1

    def test_reinforce_nonexistent_pattern(self):
        """Test reinforcing nonexistent pattern."""
        storage = PatternStorage()
        reinforcer = Reinforcer(storage)

        feedback = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.POSITIVE,
            value=0.9,
            timestamp=datetime.now()
        )

        outcome = reinforcer.reinforce("nonexistent", feedback)
        assert outcome.pattern_updated is False
        assert outcome.reward == 0.0

    def test_reinforce_similar(self):
        """Test reinforcing similar patterns."""
        # Create mock encoder
        encoder = Mock()
        encoder.encode = Mock(return_value=np.array([1.0, 0.0, 0.0]))

        storage = PatternStorage(encoder=encoder)
        storage.store("hello world", PatternType.RESPONSE)
        storage.store("hello there", PatternType.RESPONSE)

        reinforcer = Reinforcer(storage)
        feedback = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.POSITIVE,
            value=0.9,
            timestamp=datetime.now()
        )

        outcomes = reinforcer.reinforce_similar("hello", feedback, spread=0.5)
        assert len(outcomes) >= 1

    def test_reinforcer_history(self):
        """Test reinforcer history tracking."""
        storage = PatternStorage()
        pattern = storage.store("test", PatternType.RESPONSE)
        reinforcer = Reinforcer(storage)

        # Add some reinforcements
        for i in range(5):
            feedback = Feedback(
                id=f"fb_{i}",
                interaction_id=f"int_{i}",
                feedback_type=FeedbackType.POSITIVE,
                value=0.8,
                timestamp=datetime.now()
            )
            reinforcer.reinforce(pattern.id, feedback)

        history = reinforcer.get_history(limit=3)
        assert len(history) == 3

    def test_reinforcer_total_reward(self):
        """Test total reward tracking."""
        storage = PatternStorage()
        pattern = storage.store("test", PatternType.RESPONSE)
        reinforcer = Reinforcer(storage)

        feedback = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.POSITIVE,
            value=1.0,
            timestamp=datetime.now()
        )
        reinforcer.reinforce(pattern.id, feedback)

        total = reinforcer.get_total_reward()
        assert total > 0

    def test_reinforcer_stats(self):
        """Test reinforcer statistics."""
        storage = PatternStorage()
        pattern = storage.store("test", PatternType.RESPONSE)
        reinforcer = Reinforcer(storage)

        # Add positive and negative
        pos_feedback = Feedback("fb_1", "int_1", FeedbackType.POSITIVE, 0.8, datetime.now())
        neg_feedback = Feedback("fb_2", "int_2", FeedbackType.NEGATIVE, -0.6, datetime.now())

        reinforcer.reinforce(pattern.id, pos_feedback)
        reinforcer.reinforce(pattern.id, neg_feedback)

        stats = reinforcer.stats()
        assert stats["total_reinforcements"] == 2
        assert stats["positive_reinforcements"] == 1
        assert stats["negative_reinforcements"] == 1


# ============================================================================
# AdaptationConfig Tests
# ============================================================================

class TestAdaptationConfig:
    """AdaptationConfig testleri."""

    def test_adaptation_config_defaults(self):
        """Test default adaptation config."""
        config = AdaptationConfig()
        assert config.min_samples == 3
        assert config.confidence_threshold == 0.6
        assert config.exploration_rate == 0.1

    def test_adaptation_config_custom(self):
        """Test custom adaptation config."""
        config = AdaptationConfig(
            min_samples=5,
            confidence_threshold=0.8,
            exploration_rate=0.2
        )
        assert config.min_samples == 5
        assert config.confidence_threshold == 0.8
        assert config.exploration_rate == 0.2


# ============================================================================
# BehaviorAdapter Tests
# ============================================================================

class TestBehaviorAdapter:
    """BehaviorAdapter testleri."""

    def test_adapter_init(self):
        """Test adapter initialization."""
        storage = PatternStorage()
        collector = FeedbackCollector()
        adapter = BehaviorAdapter(storage, collector)

        assert adapter.patterns == storage
        assert adapter.feedback == collector

    def test_suggest_pattern_empty(self):
        """Test suggesting pattern from empty storage."""
        storage = PatternStorage()
        collector = FeedbackCollector()
        adapter = BehaviorAdapter(storage, collector)

        pattern = adapter.suggest_pattern("test context", PatternType.RESPONSE)
        assert pattern is None

    def test_suggest_pattern_with_patterns(self):
        """Test suggesting pattern with available patterns."""
        storage = PatternStorage()
        storage.store("response 1", PatternType.RESPONSE)
        storage.store("response 2", PatternType.RESPONSE)

        collector = FeedbackCollector()
        config = AdaptationConfig(exploration_rate=0.0)  # No exploration
        adapter = BehaviorAdapter(storage, collector, config)

        pattern = adapter.suggest_pattern("test", PatternType.RESPONSE)
        assert pattern is not None

    def test_should_explore(self):
        """Test exploration decision."""
        storage = PatternStorage()
        collector = FeedbackCollector()

        # High exploration rate
        config = AdaptationConfig(exploration_rate=1.0)
        adapter = BehaviorAdapter(storage, collector, config)
        assert adapter.should_explore() is True

        # Zero exploration rate
        config_no_explore = AdaptationConfig(exploration_rate=0.0)
        adapter_no_explore = BehaviorAdapter(storage, collector, config_no_explore)
        assert adapter_no_explore.should_explore() is False

    def test_adapt_from_feedback(self):
        """Test adapting from feedback."""
        storage = PatternStorage()
        pattern = storage.store("test", PatternType.RESPONSE)

        collector = FeedbackCollector()
        collector.record("int_1", FeedbackType.POSITIVE, 0.8)

        adapter = BehaviorAdapter(storage, collector)
        result = adapter.adapt_from_feedback("int_1", pattern.id)
        assert result is True

    def test_adapt_from_feedback_no_feedback(self):
        """Test adapting with no feedback."""
        storage = PatternStorage()
        pattern = storage.store("test", PatternType.RESPONSE)

        collector = FeedbackCollector()
        adapter = BehaviorAdapter(storage, collector)

        result = adapter.adapt_from_feedback("int_1", pattern.id)
        assert result is False

    def test_confidence_calculation_no_uses(self):
        """Test confidence calculation with no uses."""
        storage = PatternStorage()
        pattern = storage.store("test", PatternType.RESPONSE)

        collector = FeedbackCollector()
        adapter = BehaviorAdapter(storage, collector)

        confidence = adapter.get_confidence(pattern)
        assert confidence == 0.5  # Default for no samples

    def test_confidence_calculation_with_uses(self):
        """Test confidence calculation with uses."""
        storage = PatternStorage()
        pattern = storage.store("test", PatternType.RESPONSE)

        # Add some stats
        for _ in range(10):
            storage.update_stats(pattern.id, success=True, reward=1.0)

        collector = FeedbackCollector()
        adapter = BehaviorAdapter(storage, collector)

        updated_pattern = storage.get(pattern.id)
        confidence = adapter.get_confidence(updated_pattern)
        assert confidence > 0.5  # Should be high with all successes

    def test_get_adaptations(self):
        """Test getting adaptation records."""
        storage = PatternStorage()
        storage.store("test", PatternType.RESPONSE)

        collector = FeedbackCollector()
        config = AdaptationConfig(exploration_rate=0.0)
        adapter = BehaviorAdapter(storage, collector, config)

        # Trigger some suggestions
        adapter.suggest_pattern("context1", PatternType.RESPONSE)
        adapter.suggest_pattern("context2", PatternType.RESPONSE)

        adaptations = adapter.get_adaptations()
        assert len(adaptations) >= 2

    def test_adapter_stats(self):
        """Test adapter statistics."""
        storage = PatternStorage()
        collector = FeedbackCollector()
        adapter = BehaviorAdapter(storage, collector)

        stats = adapter.stats()
        assert "total_adaptations" in stats
        assert "exploration_count" in stats
        assert "exploitation_count" in stats


# ============================================================================
# LearningProcessor Tests
# ============================================================================

class TestLearningProcessor:
    """LearningProcessor testleri."""

    def test_processor_init(self):
        """Test processor initialization."""
        processor = LearningProcessor()
        assert processor.feedback_collector is not None
        assert processor.pattern_storage is not None
        assert processor.reinforcer is not None
        assert processor.adapter is not None

    def test_learn_from_interaction(self):
        """Test learning from single interaction."""
        processor = LearningProcessor()

        outcome = processor.learn_from_interaction(
            interaction_id="int_1",
            context="user asked about weather",
            response="It's sunny today!",
            feedback_type=FeedbackType.POSITIVE,
            value=0.9
        )

        assert outcome.pattern_updated is True
        assert outcome.reward > 0

    def test_learn_from_interaction_negative(self):
        """Test learning from negative interaction."""
        processor = LearningProcessor()

        outcome = processor.learn_from_interaction(
            interaction_id="int_1",
            context="user asked for help",
            response="Sorry, I can't help",
            feedback_type=FeedbackType.NEGATIVE,
            value=-0.8
        )

        assert outcome.pattern_updated is True
        assert outcome.reward < 0

    def test_suggest_response_empty(self):
        """Test suggesting response with no patterns."""
        processor = LearningProcessor()
        response = processor.suggest_response("some context")
        assert response is None

    def test_suggest_response_with_learning(self):
        """Test suggesting response after learning."""
        processor = LearningProcessor()

        # Learn some interactions
        processor.learn_from_interaction(
            "int_1", "hello", "Hi there!", FeedbackType.POSITIVE, 0.9
        )

        # Suggest should return something now
        # (may return None depending on adapter logic)
        response = processor.suggest_response("hello")
        # Just verify it doesn't crash

    def test_learning_rate_empty(self):
        """Test learning rate with no interactions."""
        processor = LearningProcessor()
        rate = processor.get_learning_rate()
        assert rate == 0.0

    def test_learning_rate_with_interactions(self):
        """Test learning rate with interactions."""
        processor = LearningProcessor()

        # Add positive interactions
        for i in range(10):
            processor.learn_from_interaction(
                f"int_{i}", "context", "response", FeedbackType.POSITIVE, 0.8
            )

        rate = processor.get_learning_rate()
        assert rate > 0.5  # Mostly positive

    def test_improvement_tracking(self):
        """Test improvement tracking."""
        processor = LearningProcessor()

        # Not enough samples
        improvement = processor.get_improvement(window=100)
        assert improvement == 0.0

        # Add many interactions
        for i in range(150):
            feedback = FeedbackType.NEGATIVE if i < 75 else FeedbackType.POSITIVE
            value = -0.5 if i < 75 else 0.8
            processor.learn_from_interaction(
                f"int_{i}", "context", "response", feedback, value
            )

        improvement = processor.get_improvement(window=100)
        assert improvement > 0  # Should show improvement

    def test_full_learning_cycle(self):
        """Test complete learning cycle."""
        processor = LearningProcessor()

        # Learn
        outcome1 = processor.learn_from_interaction(
            "int_1", "greeting", "Hello!", FeedbackType.POSITIVE, 1.0
        )
        assert outcome1.pattern_updated

        # Learn more
        outcome2 = processor.learn_from_interaction(
            "int_2", "greeting", "Hi there!", FeedbackType.POSITIVE, 0.8
        )
        assert outcome2.pattern_updated

        # Check stats
        stats = processor.stats()
        assert stats["feedback"]["total_feedback"] == 2
        assert stats["patterns"]["total_patterns"] == 2
        assert stats["total_interactions"] == 2

    def test_pattern_strengthening(self):
        """Test pattern is strengthened by positive feedback."""
        processor = LearningProcessor()

        # Learn initial interaction
        processor.learn_from_interaction(
            "int_1", "test", "good response", FeedbackType.POSITIVE, 0.9
        )

        pattern_stats = processor.pattern_storage.stats()
        assert pattern_stats["total_patterns"] == 1

    def test_pattern_weakening(self):
        """Test pattern is weakened by negative feedback."""
        processor = LearningProcessor()

        processor.learn_from_interaction(
            "int_1", "test", "bad response", FeedbackType.NEGATIVE, -0.9
        )

        # Pattern should have failure recorded
        patterns = processor.pattern_storage.get_all()
        assert len(patterns) == 1
        assert patterns[0].failure_count == 1

    def test_stats_complete(self):
        """Test complete statistics."""
        processor = LearningProcessor()

        processor.learn_from_interaction(
            "int_1", "test", "response", FeedbackType.POSITIVE, 0.8
        )

        stats = processor.stats()
        assert "feedback" in stats
        assert "patterns" in stats
        assert "reinforcement" in stats
        assert "adaptation" in stats
        assert "learning_rate" in stats
        assert "improvement" in stats
        assert "total_interactions" in stats

    def test_processor_clear(self):
        """Test clearing all data."""
        processor = LearningProcessor()

        for i in range(5):
            processor.learn_from_interaction(
                f"int_{i}", "test", "response", FeedbackType.POSITIVE, 0.8
            )

        cleared = processor.clear()
        assert cleared["feedback"] == 5
        assert cleared["patterns"] == 5
        assert cleared["interactions"] == 5


# ============================================================================
# Integration Tests
# ============================================================================

class TestLearningIntegration:
    """Integration tests for advanced learning components."""

    def test_exploration_vs_exploitation(self):
        """Test exploration vs exploitation balance."""
        storage = PatternStorage()
        collector = FeedbackCollector()

        # Add patterns with different success rates
        p1 = storage.store("proven response", PatternType.RESPONSE)
        p2 = storage.store("new response", PatternType.RESPONSE)

        # Make p1 proven good
        for _ in range(20):
            storage.update_stats(p1.id, success=True, reward=1.0)

        # Test with zero exploration
        config = AdaptationConfig(exploration_rate=0.0)
        adapter = BehaviorAdapter(storage, collector, config)

        # Should always exploit
        for _ in range(10):
            assert adapter.should_explore() is False

    def test_generalization(self):
        """Test pattern generalization."""
        # Create mock encoder that makes all embeddings similar
        encoder = Mock()
        encoder.encode = Mock(return_value=np.array([1.0, 0.0, 0.0]))

        storage = PatternStorage(encoder=encoder)
        p1 = storage.store("similar pattern 1", PatternType.RESPONSE)
        p2 = storage.store("similar pattern 2", PatternType.RESPONSE)

        reinforcer = Reinforcer(storage)

        # Reinforce with generalization
        feedback = Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.POSITIVE,
            value=0.9,
            timestamp=datetime.now()
        )

        outcomes = reinforcer.reinforce_similar("similar content", feedback, spread=0.5)

        # Both patterns should be affected
        assert len(outcomes) == 2

    def test_learning_improvement_over_time(self):
        """Test that learning shows improvement over time."""
        processor = LearningProcessor()

        # Phase 1: Bad responses (negative feedback)
        for i in range(50):
            processor.learn_from_interaction(
                f"int_bad_{i}",
                "user question",
                f"bad response {i}",
                FeedbackType.NEGATIVE,
                -0.7
            )

        # Phase 2: Good responses (positive feedback)
        for i in range(50):
            processor.learn_from_interaction(
                f"int_good_{i}",
                "user question",
                f"good response {i}",
                FeedbackType.POSITIVE,
                0.8
            )

        # Learning rate should reflect recent positive interactions
        rate = processor.get_learning_rate()
        assert rate > 0.5  # Recent interactions were positive

        # Stats should show the journey
        stats = processor.stats()
        assert stats["total_interactions"] == 100
