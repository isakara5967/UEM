"""
tests/unit/test_learning_persistence.py

Tests for Learning Module PostgreSQL Persistence.

Uses SQLite in-memory database for testing.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.memory.persistence.models import Base, PatternModel, FeedbackModel
from core.learning.types import (
    Pattern,
    PatternType,
    Feedback,
    FeedbackType,
    generate_pattern_id,
    generate_feedback_id,
)
from core.learning.persistence.pattern_repo import PatternRepository
from core.learning.persistence.feedback_repo import FeedbackRepository
from core.learning.patterns import PatternStorage
from core.learning.feedback import FeedbackCollector


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session_factory(db_engine):
    """Create session factory for testing."""
    return sessionmaker(bind=db_engine)


@pytest.fixture
def pattern_repo(session_factory):
    """Create pattern repository for testing."""
    return PatternRepository(session_factory)


@pytest.fixture
def feedback_repo(session_factory):
    """Create feedback repository for testing."""
    return FeedbackRepository(session_factory)


@pytest.fixture
def sample_pattern():
    """Create sample pattern for testing."""
    return Pattern(
        id=generate_pattern_id(),
        pattern_type=PatternType.RESPONSE,
        content="Hello, how can I help you?",
        embedding=[0.1, 0.2, 0.3],
        success_count=5,
        failure_count=1,
        total_reward=4.5,
        created_at=datetime.now(),
        last_used=datetime.now(),
        extra_data={"context": "greeting"}
    )


@pytest.fixture
def sample_feedback():
    """Create sample feedback for testing."""
    return Feedback(
        id=generate_feedback_id(),
        interaction_id="int_123",
        feedback_type=FeedbackType.POSITIVE,
        value=0.8,
        timestamp=datetime.now(),
        user_id="user_456",
        context="test context",
        reason="helpful response"
    )


# ============================================================================
# PatternRepository Tests
# ============================================================================

class TestPatternRepository:
    """PatternRepository tests."""

    def test_pattern_repo_save(self, pattern_repo, sample_pattern):
        """Test saving pattern to database."""
        pattern_id = pattern_repo.save(sample_pattern)
        assert pattern_id == sample_pattern.id

    def test_pattern_repo_get(self, pattern_repo, sample_pattern):
        """Test getting pattern from database."""
        pattern_repo.save(sample_pattern)
        retrieved = pattern_repo.get(sample_pattern.id)

        assert retrieved is not None
        assert retrieved.id == sample_pattern.id
        assert retrieved.content == sample_pattern.content
        assert retrieved.pattern_type == sample_pattern.pattern_type

    def test_pattern_repo_get_nonexistent(self, pattern_repo):
        """Test getting nonexistent pattern."""
        result = pattern_repo.get("nonexistent_id")
        assert result is None

    def test_pattern_repo_update(self, pattern_repo, sample_pattern):
        """Test updating pattern in database."""
        pattern_repo.save(sample_pattern)

        # Modify pattern
        sample_pattern.success_count = 10
        sample_pattern.content = "Updated content"

        result = pattern_repo.update(sample_pattern)
        assert result is True

        # Verify update
        retrieved = pattern_repo.get(sample_pattern.id)
        assert retrieved.success_count == 10
        assert retrieved.content == "Updated content"

    def test_pattern_repo_update_nonexistent(self, pattern_repo, sample_pattern):
        """Test updating nonexistent pattern."""
        result = pattern_repo.update(sample_pattern)
        assert result is False

    def test_pattern_repo_delete(self, pattern_repo, sample_pattern):
        """Test deleting pattern from database."""
        pattern_repo.save(sample_pattern)
        result = pattern_repo.delete(sample_pattern.id)

        assert result is True
        assert pattern_repo.get(sample_pattern.id) is None

    def test_pattern_repo_delete_nonexistent(self, pattern_repo):
        """Test deleting nonexistent pattern."""
        result = pattern_repo.delete("nonexistent_id")
        assert result is False

    def test_pattern_repo_get_all(self, pattern_repo):
        """Test getting all patterns."""
        # Add multiple patterns
        for i in range(5):
            pattern = Pattern(
                id=f"pat_{i}",
                pattern_type=PatternType.RESPONSE,
                content=f"Content {i}"
            )
            pattern_repo.save(pattern)

        patterns = pattern_repo.get_all()
        assert len(patterns) == 5

    def test_pattern_repo_find_by_type(self, pattern_repo):
        """Test finding patterns by type."""
        # Add patterns of different types
        pattern_repo.save(Pattern(
            id="pat_1", pattern_type=PatternType.RESPONSE, content="Response 1"
        ))
        pattern_repo.save(Pattern(
            id="pat_2", pattern_type=PatternType.RESPONSE, content="Response 2"
        ))
        pattern_repo.save(Pattern(
            id="pat_3", pattern_type=PatternType.BEHAVIOR, content="Behavior 1"
        ))

        response_patterns = pattern_repo.find_by_type(PatternType.RESPONSE)
        assert len(response_patterns) == 2

        behavior_patterns = pattern_repo.find_by_type(PatternType.BEHAVIOR)
        assert len(behavior_patterns) == 1

    def test_pattern_repo_get_top_patterns(self, pattern_repo):
        """Test getting top patterns by success count."""
        # Add patterns with different success counts
        for i in range(5):
            pattern = Pattern(
                id=f"pat_{i}",
                pattern_type=PatternType.RESPONSE,
                content=f"Content {i}",
                success_count=i * 2
            )
            pattern_repo.save(pattern)

        top = pattern_repo.get_top_patterns(k=3)
        assert len(top) == 3
        assert top[0].success_count == 8  # Highest
        assert top[1].success_count == 6
        assert top[2].success_count == 4

    def test_pattern_repo_count(self, pattern_repo):
        """Test pattern count."""
        assert pattern_repo.count() == 0

        for i in range(3):
            pattern_repo.save(Pattern(
                id=f"pat_{i}",
                pattern_type=PatternType.RESPONSE,
                content=f"Content {i}"
            ))

        assert pattern_repo.count() == 3

    def test_pattern_repo_stats(self, pattern_repo):
        """Test pattern statistics."""
        # Add patterns
        pattern_repo.save(Pattern(
            id="pat_1",
            pattern_type=PatternType.RESPONSE,
            content="Response",
            success_count=8,
            failure_count=2
        ))
        pattern_repo.save(Pattern(
            id="pat_2",
            pattern_type=PatternType.BEHAVIOR,
            content="Behavior",
            success_count=5,
            failure_count=5
        ))

        stats = pattern_repo.get_stats()
        assert stats["total_patterns"] == 2
        assert stats["by_type"]["response"] == 1
        assert stats["by_type"]["behavior"] == 1
        assert stats["total_uses"] == 20

    def test_pattern_repo_clear(self, pattern_repo):
        """Test clearing all patterns."""
        for i in range(5):
            pattern_repo.save(Pattern(
                id=f"pat_{i}",
                pattern_type=PatternType.RESPONSE,
                content=f"Content {i}"
            ))

        count = pattern_repo.clear()
        assert count == 5
        assert pattern_repo.count() == 0


# ============================================================================
# FeedbackRepository Tests
# ============================================================================

class TestFeedbackRepository:
    """FeedbackRepository tests."""

    def test_feedback_repo_save(self, feedback_repo, sample_feedback):
        """Test saving feedback to database."""
        feedback_id = feedback_repo.save(sample_feedback)
        assert feedback_id == sample_feedback.id

    def test_feedback_repo_get(self, feedback_repo, sample_feedback):
        """Test getting feedback from database."""
        feedback_repo.save(sample_feedback)
        retrieved = feedback_repo.get(sample_feedback.id)

        assert retrieved is not None
        assert retrieved.id == sample_feedback.id
        assert retrieved.value == sample_feedback.value
        assert retrieved.interaction_id == sample_feedback.interaction_id

    def test_feedback_repo_get_nonexistent(self, feedback_repo):
        """Test getting nonexistent feedback."""
        result = feedback_repo.get("nonexistent_id")
        assert result is None

    def test_feedback_repo_get_by_interaction(self, feedback_repo):
        """Test getting feedbacks by interaction."""
        # Add feedbacks for same interaction
        for i in range(3):
            feedback = Feedback(
                id=f"fb_{i}",
                interaction_id="int_123",
                feedback_type=FeedbackType.POSITIVE,
                value=0.5 + i * 0.1,
                timestamp=datetime.now()
            )
            feedback_repo.save(feedback)

        # Add feedback for different interaction
        feedback_repo.save(Feedback(
            id="fb_other",
            interaction_id="int_456",
            feedback_type=FeedbackType.NEGATIVE,
            value=-0.5,
            timestamp=datetime.now()
        ))

        feedbacks = feedback_repo.get_by_interaction("int_123")
        assert len(feedbacks) == 3

    def test_feedback_repo_get_by_user(self, feedback_repo):
        """Test getting feedbacks by user."""
        # Add feedbacks for same user
        for i in range(3):
            feedback = Feedback(
                id=f"fb_{i}",
                interaction_id=f"int_{i}",
                feedback_type=FeedbackType.POSITIVE,
                value=0.8,
                timestamp=datetime.now(),
                user_id="user_123"
            )
            feedback_repo.save(feedback)

        # Add feedback for different user
        feedback_repo.save(Feedback(
            id="fb_other",
            interaction_id="int_other",
            feedback_type=FeedbackType.NEGATIVE,
            value=-0.5,
            timestamp=datetime.now(),
            user_id="user_456"
        ))

        feedbacks = feedback_repo.get_by_user("user_123")
        assert len(feedbacks) == 3

    def test_feedback_repo_get_recent(self, feedback_repo):
        """Test getting recent feedbacks."""
        for i in range(10):
            feedback = Feedback(
                id=f"fb_{i}",
                interaction_id=f"int_{i}",
                feedback_type=FeedbackType.NEUTRAL,
                value=0.0,
                timestamp=datetime.now()
            )
            feedback_repo.save(feedback)

        recent = feedback_repo.get_recent(limit=5)
        assert len(recent) == 5

    def test_feedback_repo_delete(self, feedback_repo, sample_feedback):
        """Test deleting feedback."""
        feedback_repo.save(sample_feedback)
        result = feedback_repo.delete(sample_feedback.id)

        assert result is True
        assert feedback_repo.get(sample_feedback.id) is None

    def test_feedback_repo_count(self, feedback_repo):
        """Test feedback count."""
        assert feedback_repo.count() == 0

        for i in range(5):
            feedback_repo.save(Feedback(
                id=f"fb_{i}",
                interaction_id=f"int_{i}",
                feedback_type=FeedbackType.POSITIVE,
                value=0.5,
                timestamp=datetime.now()
            ))

        assert feedback_repo.count() == 5

    def test_feedback_repo_stats(self, feedback_repo):
        """Test feedback statistics."""
        # Add various feedbacks
        feedback_repo.save(Feedback(
            id="fb_1",
            interaction_id="int_1",
            feedback_type=FeedbackType.EXPLICIT,
            value=0.9,
            timestamp=datetime.now(),
            user_id="user_1"
        ))
        feedback_repo.save(Feedback(
            id="fb_2",
            interaction_id="int_2",
            feedback_type=FeedbackType.IMPLICIT,
            value=-0.5,
            timestamp=datetime.now(),
            user_id="user_2"
        ))

        stats = feedback_repo.get_stats()
        assert stats["total_feedback"] == 2
        assert stats["positive_count"] == 1
        assert stats["negative_count"] == 1
        assert stats["explicit_count"] == 1
        assert stats["implicit_count"] == 1
        assert stats["unique_users"] == 2

    def test_feedback_repo_get_average_score(self, feedback_repo):
        """Test getting average feedback score."""
        feedback_repo.save(Feedback(
            id="fb_1", interaction_id="int_1",
            feedback_type=FeedbackType.POSITIVE, value=1.0,
            timestamp=datetime.now(), user_id="user_1"
        ))
        feedback_repo.save(Feedback(
            id="fb_2", interaction_id="int_2",
            feedback_type=FeedbackType.NEGATIVE, value=-1.0,
            timestamp=datetime.now(), user_id="user_1"
        ))

        avg = feedback_repo.get_average_score()
        assert avg == 0.0

        avg_user = feedback_repo.get_average_score("user_1")
        assert avg_user == 0.0

    def test_feedback_repo_clear(self, feedback_repo):
        """Test clearing all feedbacks."""
        for i in range(5):
            feedback_repo.save(Feedback(
                id=f"fb_{i}",
                interaction_id=f"int_{i}",
                feedback_type=FeedbackType.POSITIVE,
                value=0.5,
                timestamp=datetime.now()
            ))

        count = feedback_repo.clear()
        assert count == 5
        assert feedback_repo.count() == 0


# ============================================================================
# PatternStorage with DB Tests
# ============================================================================

class TestPatternStorageWithDB:
    """PatternStorage with database integration tests."""

    def test_pattern_storage_with_db(self, pattern_repo):
        """Test PatternStorage with database repository."""
        storage = PatternStorage(repository=pattern_repo)

        # Store pattern
        pattern = storage.store("Hello!", PatternType.RESPONSE)

        # Verify in DB
        db_pattern = pattern_repo.get(pattern.id)
        assert db_pattern is not None
        assert db_pattern.content == "Hello!"

    def test_pattern_storage_persistence(self, session_factory):
        """Test pattern persists across storage instances."""
        repo = PatternRepository(session_factory)

        # First storage instance
        storage1 = PatternStorage(repository=repo)
        pattern = storage1.store("Persistent pattern", PatternType.RESPONSE)

        # Update stats
        storage1.update_stats(pattern.id, success=True, reward=1.0)

        # Second storage instance (simulating restart)
        storage2 = PatternStorage(repository=repo)

        # Pattern should be loaded
        assert pattern.id in storage2._patterns
        retrieved = storage2.get(pattern.id)
        assert retrieved is not None
        assert retrieved.content == "Persistent pattern"
        assert retrieved.success_count == 1

    def test_pattern_storage_update_persists(self, pattern_repo):
        """Test that updates persist to database."""
        storage = PatternStorage(repository=pattern_repo)
        pattern = storage.store("Test", PatternType.RESPONSE)

        # Update stats multiple times
        for _ in range(5):
            storage.update_stats(pattern.id, success=True, reward=1.0)

        # Verify in DB
        db_pattern = pattern_repo.get(pattern.id)
        assert db_pattern.success_count == 5
        assert db_pattern.total_reward == 5.0

    def test_pattern_storage_clear_persists(self, pattern_repo):
        """Test that clear affects database."""
        storage = PatternStorage(repository=pattern_repo)

        for i in range(3):
            storage.store(f"Pattern {i}", PatternType.RESPONSE)

        assert pattern_repo.count() == 3

        storage.clear()

        assert pattern_repo.count() == 0


# ============================================================================
# FeedbackCollector with DB Tests
# ============================================================================

class TestFeedbackCollectorWithDB:
    """FeedbackCollector with database integration tests."""

    def test_feedback_collector_with_db(self, feedback_repo):
        """Test FeedbackCollector with database repository."""
        collector = FeedbackCollector(repository=feedback_repo)

        # Record feedback
        feedback = collector.record(
            interaction_id="int_1",
            feedback_type=FeedbackType.POSITIVE,
            value=0.9
        )

        # Verify in DB
        db_feedback = feedback_repo.get(feedback.id)
        assert db_feedback is not None
        assert db_feedback.value == 0.9

    def test_feedback_collector_persistence(self, session_factory):
        """Test feedback persists across collector instances."""
        repo = FeedbackRepository(session_factory)

        # First collector instance
        collector1 = FeedbackCollector(repository=repo)
        feedback = collector1.record(
            interaction_id="int_persist",
            feedback_type=FeedbackType.EXPLICIT,
            value=0.8,
            user_id="user_persist"
        )

        # Second collector instance (simulating restart)
        collector2 = FeedbackCollector(repository=repo)

        # Feedback should be loaded
        assert len(collector2._feedback_history) == 1
        assert feedback.id == collector2._feedback_history[0].id

    def test_feedback_collector_clear_persists(self, feedback_repo):
        """Test that clear affects database."""
        collector = FeedbackCollector(repository=feedback_repo)

        for i in range(3):
            collector.record(
                interaction_id=f"int_{i}",
                feedback_type=FeedbackType.POSITIVE,
                value=0.5
            )

        assert feedback_repo.count() == 3

        collector.clear()

        assert feedback_repo.count() == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestLearningPersistenceIntegration:
    """Integration tests for learning persistence."""

    def test_learning_survives_restart(self, session_factory):
        """Test that learning data survives simulated restart."""
        # Phase 1: Create and populate
        pattern_repo = PatternRepository(session_factory)
        feedback_repo = FeedbackRepository(session_factory)

        storage = PatternStorage(repository=pattern_repo)
        collector = FeedbackCollector(repository=feedback_repo)

        # Store patterns
        p1 = storage.store("Response 1", PatternType.RESPONSE)
        p2 = storage.store("Response 2", PatternType.RESPONSE)

        # Update stats
        storage.update_stats(p1.id, success=True, reward=1.0)
        storage.update_stats(p1.id, success=True, reward=1.0)
        storage.update_stats(p2.id, success=False, reward=-0.5)

        # Record feedbacks
        collector.record("int_1", FeedbackType.POSITIVE, 0.9)
        collector.record("int_2", FeedbackType.NEGATIVE, -0.7)

        # Phase 2: Simulate restart with new instances
        storage2 = PatternStorage(repository=pattern_repo)
        collector2 = FeedbackCollector(repository=feedback_repo)

        # Verify patterns survived
        assert storage2.count() == 2
        retrieved = storage2.get(p1.id)
        assert retrieved.success_count == 2

        # Verify feedbacks survived
        assert len(collector2._feedback_history) == 2

    def test_memory_only_mode_still_works(self):
        """Test that memory-only mode (no repository) still works."""
        # Without repository
        storage = PatternStorage()
        collector = FeedbackCollector()

        # Should work normally
        pattern = storage.store("Test", PatternType.RESPONSE)
        assert pattern is not None
        assert storage.get(pattern.id) is not None

        feedback = collector.record("int_1", FeedbackType.POSITIVE, 0.5)
        assert feedback is not None
        assert len(collector.get_feedback("int_1")) == 1

    def test_full_learning_cycle_with_persistence(self, session_factory):
        """Test complete learning cycle with persistence."""
        pattern_repo = PatternRepository(session_factory)
        feedback_repo = FeedbackRepository(session_factory)

        storage = PatternStorage(repository=pattern_repo)
        collector = FeedbackCollector(repository=feedback_repo)

        # Learn from interactions
        interactions = [
            ("How are you?", "I'm doing well!", True, 0.9),
            ("What's the weather?", "It's sunny!", True, 0.8),
            ("Tell me a joke", "Why did...", False, -0.3),
        ]

        for context, response, positive, value in interactions:
            # Store pattern
            pattern = storage.store(response, PatternType.RESPONSE, {"context": context})

            # Record feedback
            feedback = collector.record(
                interaction_id=f"int_{pattern.id}",
                feedback_type=FeedbackType.POSITIVE if positive else FeedbackType.NEGATIVE,
                value=value
            )

            # Update stats based on feedback
            storage.update_stats(pattern.id, success=positive, reward=value)

        # Verify stats
        assert storage.count() == 3
        assert len(collector._feedback_history) == 3

        # Get top patterns
        top = storage.get_best_patterns(PatternType.RESPONSE, k=2)
        assert len(top) == 2
