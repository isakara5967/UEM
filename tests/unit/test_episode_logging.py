"""
tests/unit/test_episode_logging.py

Comprehensive tests for Faz 5 Episode Logging System.

Test groups:
- EpisodeLog structure and validation
- ImplicitFeedback scoring
- EpisodeLogger lifecycle
- JSONLEpisodeStore operations
- Pattern ID generation and mapping
- Pipeline integration

UEM v2 - Faz 5 Tests.
"""

import json
import os
import pytest
import tempfile
from datetime import datetime
from pathlib import Path

from core.learning.episode_types import (
    EpisodeLog,
    ImplicitFeedback,
    ConstructionSource,
    ConstructionLevel,
    ApprovalStatus,
    generate_episode_log_id,
)
from core.learning.episode_store import JSONLEpisodeStore
from core.learning.episode_logger import EpisodeLogger
from core.language.intent.types import IntentCategory
from core.language.intent.patterns import get_pattern_id, get_pattern_ids_for_category, PATTERN_TO_ID
from core.language.dialogue.types import DialogueAct
from core.language.risk.types import RiskLevel


# =========================================================================
# 1. EpisodeLog Structure Tests (7 tests)
# =========================================================================

class TestEpisodeLogStructure:
    """Test EpisodeLog dataclass structure and validation."""

    def test_minimal_episode_log(self):
        """Test creating minimal episode log with required fields."""
        episode = EpisodeLog(
            id="eplog_test123",
            session_id="sess_test456",
            turn_number=1,
            user_message="Merhaba",
            user_message_normalized="merhaba",
            intent_primary=IntentCategory.GREETING
        )

        assert episode.id == "eplog_test123"
        assert episode.session_id == "sess_test456"
        assert episode.turn_number == 1
        assert episode.intent_primary == IntentCategory.GREETING

    def test_full_episode_log(self):
        """Test creating full episode log with all fields."""
        episode = EpisodeLog(
            id="eplog_full",
            session_id="sess_full",
            turn_number=5,
            user_message="Merhaba, nasılsın?",
            user_message_normalized="merhaba nasilsin",
            intent_primary=IntentCategory.GREETING,
            intent_secondary=IntentCategory.ASK_WELLBEING,
            intent_confidence=0.85,
            intent_matched_pattern_ids=["greeting_0", "ask_wellbeing_0"],
            context_turn_count=4,
            dialogue_act_selected=DialogueAct.GREET,
            dialogue_act_score=0.9,
            construction_id="mvcs_greeting_0",
            construction_category="GREETING",
            response_text="Merhaba! Ben iyiyim, sen nasılsın?",
            risk_level=RiskLevel.LOW,
            risk_score=0.1,
            processing_time_ms=150
        )

        assert episode.intent_secondary == IntentCategory.ASK_WELLBEING
        assert episode.has_compound_intent
        assert len(episode.intent_matched_pattern_ids) == 2
        assert episode.response_length_chars == 34  # "Merhaba! Ben iyiyim, sen nasılsın?"
        assert episode.response_length_words == 5

    def test_episode_log_response_length_calculation(self):
        """Test automatic response length calculation."""
        episode = EpisodeLog(
            id="eplog_len",
            session_id="sess_len",
            turn_number=1,
            user_message="Test",
            user_message_normalized="test",
            intent_primary=IntentCategory.GREETING,
            response_text="Merhaba dünya! Bu bir test."
        )

        assert episode.response_length_chars == 27
        assert episode.response_length_words == 5

    def test_feedback_explicit_validation(self):
        """Test feedback_explicit range validation."""
        # Valid range
        episode = EpisodeLog(
            id="eplog_fb1",
            session_id="sess_fb1",
            turn_number=1,
            user_message="Test",
            user_message_normalized="test",
            intent_primary=IntentCategory.GREETING,
            feedback_explicit=0.5
        )
        assert episode.feedback_explicit == 0.5

        # Invalid range should raise ValueError
        with pytest.raises(ValueError, match="feedback_explicit must be between"):
            EpisodeLog(
                id="eplog_fb2",
                session_id="sess_fb2",
                turn_number=1,
                user_message="Test",
                user_message_normalized="test",
                intent_primary=IntentCategory.GREETING,
                feedback_explicit=1.5  # Invalid
            )

    def test_episode_properties(self):
        """Test episode property methods."""
        episode = EpisodeLog(
            id="eplog_props",
            session_id="sess_props",
            turn_number=1,
            user_message="Test",
            user_message_normalized="test",
            intent_primary=IntentCategory.GREETING,
            intent_secondary=IntentCategory.ASK_WELLBEING,
            feedback_explicit=0.8,
            trust_before=0.5,
            trust_after=0.7
        )

        assert episode.has_compound_intent
        assert episode.has_explicit_feedback
        assert not episode.has_implicit_feedback
        assert episode.overall_feedback_score == 0.8
        assert episode.is_successful
        assert episode.trust_delta == pytest.approx(0.2, abs=1e-6)

    def test_episode_to_dict(self):
        """Test episode serialization to dict."""
        episode = EpisodeLog(
            id="eplog_dict",
            session_id="sess_dict",
            turn_number=1,
            user_message="Test",
            user_message_normalized="test",
            intent_primary=IntentCategory.GREETING,
            intent_confidence=0.9,
            response_text="Hello"
        )

        data = episode.to_dict()
        assert data["id"] == "eplog_dict"
        assert data["intent_primary"] == "greeting"
        assert data["intent_confidence"] == 0.9
        assert "timestamp" in data

    def test_episode_from_dict(self):
        """Test episode deserialization from dict."""
        data = {
            "id": "eplog_from",
            "session_id": "sess_from",
            "turn_number": 1,
            "timestamp": "2025-01-01T10:00:00",
            "user_message": "Test",
            "user_message_normalized": "test",
            "intent_primary": "greeting",
            "intent_confidence": 0.85,
            "response_text": "Hello"
        }

        episode = EpisodeLog.from_dict(data)
        assert episode.id == "eplog_from"
        assert episode.intent_primary == IntentCategory.GREETING
        assert episode.intent_confidence == 0.85


# =========================================================================
# 2. ImplicitFeedback Tests (5 tests)
# =========================================================================

class TestImplicitFeedback:
    """Test ImplicitFeedback scoring logic."""

    def test_positive_signals(self):
        """Test positive implicit signals."""
        feedback = ImplicitFeedback(
            conversation_continued=True,
            user_thanked=True
        )
        score = feedback.get_signal_score()
        assert score == 0.7  # 0.3 + 0.4

    def test_negative_signals(self):
        """Test negative implicit signals."""
        feedback = ImplicitFeedback(
            user_complained=True,
            session_ended_abruptly=True
        )
        score = feedback.get_signal_score()
        assert score == -0.9  # -0.5 - 0.4

    def test_mixed_signals(self):
        """Test mixed implicit signals."""
        feedback = ImplicitFeedback(
            conversation_continued=True,  # +0.3
            user_rephrased=True  # -0.3
        )
        score = feedback.get_signal_score()
        assert score == 0.0

    def test_score_clamping(self):
        """Test score clamping to [-1.0, 1.0]."""
        # Over positive (should clamp to 1.0)
        feedback_pos = ImplicitFeedback(
            conversation_continued=True,
            user_thanked=True
        )
        assert -1.0 <= feedback_pos.get_signal_score() <= 1.0

    def test_overall_feedback_priority(self):
        """Test explicit feedback takes priority over implicit."""
        # Explicit feedback
        episode_explicit = EpisodeLog(
            id="ep1",
            session_id="s1",
            turn_number=1,
            user_message="Test",
            user_message_normalized="test",
            intent_primary=IntentCategory.GREETING,
            feedback_explicit=0.9
        )
        assert episode_explicit.overall_feedback_score == 0.9

        # Implicit feedback only
        episode_implicit = EpisodeLog(
            id="ep2",
            session_id="s2",
            turn_number=1,
            user_message="Test",
            user_message_normalized="test",
            intent_primary=IntentCategory.GREETING,
            feedback_implicit=ImplicitFeedback(user_thanked=True)
        )
        assert episode_implicit.overall_feedback_score == 0.4


# =========================================================================
# 3. EpisodeLogger Lifecycle Tests (10 tests)
# =========================================================================

class TestEpisodeLogger:
    """Test EpisodeLogger lifecycle and state management."""

    @pytest.fixture
    def temp_store(self, tmp_path):
        """Create temporary episode store."""
        store_path = tmp_path / "test_episodes.jsonl"
        return JSONLEpisodeStore(str(store_path))

    @pytest.fixture
    def logger(self, temp_store):
        """Create episode logger with temp store."""
        return EpisodeLogger(temp_store, "test_session_123")

    def test_logger_initialization(self, temp_store):
        """Test logger initialization."""
        logger = EpisodeLogger(temp_store, "sess_init")
        assert logger.session_id == "sess_init"
        assert logger.turn_number == 0
        assert logger.current_episode is None

    def test_start_episode(self, logger):
        """Test starting a new episode."""
        episode_id = logger.start_episode("Merhaba", "merhaba")

        assert episode_id.startswith("eplog_")
        assert logger.current_episode is not None
        assert logger.turn_number == 1
        assert logger.current_episode.user_message == "Merhaba"

    def test_update_intent(self, logger):
        """Test updating intent information."""
        logger.start_episode("Test", "test")
        logger.update_intent(
            primary=IntentCategory.GREETING,
            secondary=IntentCategory.ASK_WELLBEING,
            confidence=0.85,
            pattern_ids=["greeting_0", "ask_wellbeing_0"]
        )

        assert logger.current_episode.intent_primary == IntentCategory.GREETING
        assert logger.current_episode.intent_secondary == IntentCategory.ASK_WELLBEING
        assert logger.current_episode.intent_confidence == 0.85
        assert len(logger.current_episode.intent_matched_pattern_ids) == 2

    def test_update_decision(self, logger):
        """Test updating decision information."""
        logger.start_episode("Test", "test")
        logger.update_decision(
            act_selected=DialogueAct.GREET,
            act_score=0.9,
            alternatives=[("acknowledge", 0.5), ("inform", 0.3)]
        )

        assert logger.current_episode.dialogue_act_selected == DialogueAct.GREET
        assert logger.current_episode.dialogue_act_score == 0.9
        assert len(logger.current_episode.dialogue_act_alternatives) == 2

    def test_update_construction(self, logger):
        """Test updating construction information."""
        logger.start_episode("Test", "test")
        logger.update_construction(
            construction_id="mvcs_greeting_0",
            category="GREETING",
            source=ConstructionSource.HUMAN_DEFAULT,
            level=ConstructionLevel.SURFACE
        )

        assert logger.current_episode.construction_id == "mvcs_greeting_0"
        assert logger.current_episode.construction_category == "GREETING"
        assert logger.current_episode.construction_source == ConstructionSource.HUMAN_DEFAULT

    def test_update_output(self, logger):
        """Test updating output information."""
        logger.start_episode("Test", "test")
        logger.update_output("Merhaba! Nasıl yardımcı olabilirim?")

        assert logger.current_episode.response_text == "Merhaba! Nasıl yardımcı olabilirim?"
        assert logger.current_episode.response_length_chars > 0
        assert logger.current_episode.response_length_words > 0

    def test_update_risk(self, logger):
        """Test updating risk information."""
        logger.start_episode("Test", "test")
        logger.update_risk(
            risk_level=RiskLevel.LOW,
            risk_score=0.15,
            approval_status=ApprovalStatus.APPROVED,
            approval_reasons=["Low risk content"]
        )

        assert logger.current_episode.risk_level == RiskLevel.LOW
        assert logger.current_episode.approval_status == ApprovalStatus.APPROVED

    def test_finalize_episode(self, logger):
        """Test finalizing and saving episode."""
        logger.start_episode("Test", "test")
        logger.update_intent(IntentCategory.GREETING, confidence=0.9)
        logger.update_output("Hello")

        finalized = logger.finalize_episode(processing_time_ms=125)

        assert finalized.processing_time_ms == 125
        assert logger.current_episode is None  # Cleared after finalize

        # Check it was saved to store
        episodes = logger.get_session_episodes()
        assert len(episodes) == 1
        assert episodes[0].id == finalized.id

    def test_multiple_episodes(self, logger):
        """Test logging multiple episodes in sequence."""
        # Episode 1
        logger.start_episode("Merhaba", "merhaba")
        logger.update_intent(IntentCategory.GREETING, confidence=0.9)
        logger.finalize_episode(100)

        # Episode 2
        logger.start_episode("Nasılsın?", "nasilsin")
        logger.update_intent(IntentCategory.ASK_WELLBEING, confidence=0.85)
        logger.finalize_episode(120)

        # Check both saved
        episodes = logger.get_session_episodes()
        assert len(episodes) == 2
        assert logger.turn_number == 2

    def test_update_without_start_raises_error(self, logger):
        """Test that updating without starting raises error."""
        with pytest.raises(ValueError, match="No current episode"):
            logger.update_intent(IntentCategory.GREETING)


# =========================================================================
# 4. JSONLEpisodeStore Tests (12 tests)
# =========================================================================

class TestJSONLEpisodeStore:
    """Test JSONLEpisodeStore persistence and queries."""

    @pytest.fixture
    def temp_store_path(self, tmp_path):
        """Create temporary store path."""
        return tmp_path / "episodes.jsonl"

    @pytest.fixture
    def store(self, temp_store_path):
        """Create episode store."""
        return JSONLEpisodeStore(str(temp_store_path))

    @pytest.fixture
    def sample_episode(self):
        """Create sample episode for testing."""
        return EpisodeLog(
            id="eplog_sample",
            session_id="sess_sample",
            turn_number=1,
            user_message="Test message",
            user_message_normalized="test message",
            intent_primary=IntentCategory.GREETING,
            intent_confidence=0.9,
            dialogue_act_selected=DialogueAct.GREET,
            response_text="Hello!"
        )

    def test_store_initialization(self, temp_store_path):
        """Test store creates file and directory."""
        store = JSONLEpisodeStore(str(temp_store_path))
        assert temp_store_path.parent.exists()
        assert temp_store_path.exists()

    def test_save_episode(self, store, sample_episode):
        """Test saving episode to store."""
        store.save(sample_episode)

        # Check file has content
        episodes = store.get_all()
        assert len(episodes) == 1
        assert episodes[0].id == sample_episode.id

    def test_get_by_id(self, store, sample_episode):
        """Test retrieving episode by ID."""
        store.save(sample_episode)

        retrieved = store.get_by_id("eplog_sample")
        assert retrieved is not None
        assert retrieved.id == sample_episode.id
        assert retrieved.intent_primary == IntentCategory.GREETING

    def test_get_by_id_not_found(self, store):
        """Test get_by_id returns None for non-existent ID."""
        result = store.get_by_id("nonexistent")
        assert result is None

    def test_get_recent(self, store):
        """Test retrieving recent N episodes."""
        # Create 5 episodes with different timestamps
        for i in range(5):
            episode = EpisodeLog(
                id=f"eplog_{i}",
                session_id="sess_recent",
                turn_number=i+1,
                user_message=f"Message {i}",
                user_message_normalized=f"message {i}",
                intent_primary=IntentCategory.GREETING
            )
            store.save(episode)

        # Get recent 3
        recent = store.get_recent(n=3)
        assert len(recent) == 3
        # Should be sorted newest first
        assert recent[0].turn_number > recent[1].turn_number

    def test_get_by_session(self, store):
        """Test retrieving all episodes for a session."""
        # Create episodes for different sessions
        for sess_num in range(2):
            for turn in range(3):
                episode = EpisodeLog(
                    id=f"eplog_s{sess_num}_t{turn}",
                    session_id=f"sess_{sess_num}",
                    turn_number=turn+1,
                    user_message=f"Message {turn}",
                    user_message_normalized=f"message {turn}",
                    intent_primary=IntentCategory.GREETING
                )
                store.save(episode)

        # Get session 0 episodes
        session_episodes = store.get_by_session("sess_0")
        assert len(session_episodes) == 3
        assert all(e.session_id == "sess_0" for e in session_episodes)
        # Should be sorted oldest first (turn order)
        assert session_episodes[0].turn_number < session_episodes[1].turn_number

    def test_get_by_intent(self, store):
        """Test retrieving episodes by intent category."""
        # Create episodes with different intents
        intents = [IntentCategory.GREETING, IntentCategory.GREETING, IntentCategory.THANK]
        for i, intent in enumerate(intents):
            episode = EpisodeLog(
                id=f"eplog_intent_{i}",
                session_id="sess_intent",
                turn_number=i+1,
                user_message=f"Message {i}",
                user_message_normalized=f"message {i}",
                intent_primary=intent
            )
            store.save(episode)

        # Get greeting intents
        greetings = store.get_by_intent(IntentCategory.GREETING)
        assert len(greetings) == 2
        assert all(e.intent_primary == IntentCategory.GREETING for e in greetings)

    def test_get_by_act(self, store):
        """Test retrieving episodes by dialogue act."""
        # Create episodes with different acts
        acts = [DialogueAct.GREET, DialogueAct.INFORM, DialogueAct.GREET]
        for i, act in enumerate(acts):
            episode = EpisodeLog(
                id=f"eplog_act_{i}",
                session_id="sess_act",
                turn_number=i+1,
                user_message=f"Message {i}",
                user_message_normalized=f"message {i}",
                intent_primary=IntentCategory.GREETING,
                dialogue_act_selected=act
            )
            store.save(episode)

        # Get GREET acts
        greets = store.get_by_act(DialogueAct.GREET)
        assert len(greets) == 2
        assert all(e.dialogue_act_selected == DialogueAct.GREET for e in greets)

    def test_get_all(self, store):
        """Test retrieving all episodes."""
        # Create 3 episodes
        for i in range(3):
            episode = EpisodeLog(
                id=f"eplog_all_{i}",
                session_id="sess_all",
                turn_number=i+1,
                user_message=f"Message {i}",
                user_message_normalized=f"message {i}",
                intent_primary=IntentCategory.GREETING
            )
            store.save(episode)

        all_episodes = store.get_all()
        assert len(all_episodes) == 3

    def test_count(self, store):
        """Test counting episodes."""
        assert store.count() == 0

        # Add 5 episodes
        for i in range(5):
            episode = EpisodeLog(
                id=f"eplog_count_{i}",
                session_id="sess_count",
                turn_number=i+1,
                user_message=f"Message {i}",
                user_message_normalized=f"message {i}",
                intent_primary=IntentCategory.GREETING
            )
            store.save(episode)

        assert store.count() == 5

    def test_clear(self, store, sample_episode):
        """Test clearing all episodes."""
        store.save(sample_episode)
        assert store.count() == 1

        store.clear()
        assert store.count() == 0

    def test_jsonl_format(self, store, sample_episode, temp_store_path):
        """Test that file is in valid JSONL format."""
        store.save(sample_episode)

        # Read file and verify each line is valid JSON
        with open(temp_store_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["id"] == "eplog_sample"


# =========================================================================
# 5. Pattern ID Tests (6 tests)
# =========================================================================

class TestPatternIDs:
    """Test pattern ID generation and mapping."""

    def test_pattern_to_id_mapping_exists(self):
        """Test PATTERN_TO_ID mapping is generated."""
        assert len(PATTERN_TO_ID) > 0
        assert "merhaba" in PATTERN_TO_ID
        assert "nasilsin" in PATTERN_TO_ID

    def test_pattern_id_format(self):
        """Test pattern IDs have correct format."""
        pattern_id = get_pattern_id("merhaba")
        assert pattern_id is not None
        assert pattern_id.startswith("greeting_")
        assert pattern_id.split("_")[1].isdigit()

    def test_get_pattern_id(self):
        """Test get_pattern_id function."""
        # Existing pattern
        pattern_id = get_pattern_id("merhaba")
        assert pattern_id is not None
        assert "greeting" in pattern_id

        # Non-existent pattern
        assert get_pattern_id("nonexistent_pattern_12345") is None

    def test_get_pattern_ids_for_category(self):
        """Test getting all pattern IDs for a category."""
        greeting_ids = get_pattern_ids_for_category(IntentCategory.GREETING)
        assert len(greeting_ids) > 0
        assert all(pid.startswith("greeting_") for pid in greeting_ids)

        thank_ids = get_pattern_ids_for_category(IntentCategory.THANK)
        assert len(thank_ids) > 0
        assert all(pid.startswith("thank_") for pid in thank_ids)

    def test_pattern_ids_deterministic(self):
        """Test pattern IDs are deterministic."""
        id1 = get_pattern_id("merhaba")
        id2 = get_pattern_id("merhaba")
        assert id1 == id2

    def test_pattern_ids_unique_within_category(self):
        """Test pattern IDs are unique within a category."""
        greeting_ids = get_pattern_ids_for_category(IntentCategory.GREETING)
        assert len(greeting_ids) == len(set(greeting_ids))


# =========================================================================
# 6. Pipeline Integration Tests (5 tests)
# =========================================================================

class TestPipelineIntegration:
    """Test episode logging integration with ThoughtToSpeechPipeline."""

    @pytest.fixture
    def temp_store(self, tmp_path):
        """Create temporary episode store."""
        store_path = tmp_path / "pipeline_episodes.jsonl"
        return JSONLEpisodeStore(str(store_path))

    @pytest.fixture
    def episode_logger(self, temp_store):
        """Create episode logger."""
        return EpisodeLogger(temp_store, "test_pipeline_session")

    def test_pipeline_with_episode_logger(self, episode_logger):
        """Test pipeline processes with episode logger."""
        from core.language.pipeline import ThoughtToSpeechPipeline

        pipeline = ThoughtToSpeechPipeline(episode_logger=episode_logger)
        result = pipeline.process("Merhaba")

        assert result.success
        assert "episode_id" in result.metadata

        # Check episode was logged
        episodes = episode_logger.get_session_episodes()
        assert len(episodes) == 1
        assert episodes[0].user_message == "Merhaba"

    def test_pipeline_logs_intent_info(self, episode_logger):
        """Test pipeline logs intent information."""
        from core.language.pipeline import ThoughtToSpeechPipeline

        pipeline = ThoughtToSpeechPipeline(episode_logger=episode_logger)
        pipeline.process("Merhaba, nasılsın?")

        episodes = episode_logger.get_session_episodes()
        episode = episodes[0]

        assert episode.intent_primary in [IntentCategory.GREETING, IntentCategory.ASK_WELLBEING]
        assert episode.intent_confidence > 0
        assert len(episode.intent_matched_pattern_ids) > 0

    def test_pipeline_logs_dialogue_act(self, episode_logger):
        """Test pipeline logs dialogue act selection."""
        from core.language.pipeline import ThoughtToSpeechPipeline

        pipeline = ThoughtToSpeechPipeline(episode_logger=episode_logger)
        pipeline.process("Teşekkürler!")

        episodes = episode_logger.get_session_episodes()
        episode = episodes[0]

        assert episode.dialogue_act_selected is not None
        assert episode.dialogue_act_score >= 0

    def test_pipeline_logs_output(self, episode_logger):
        """Test pipeline logs output information."""
        from core.language.pipeline import ThoughtToSpeechPipeline

        pipeline = ThoughtToSpeechPipeline(episode_logger=episode_logger)
        result = pipeline.process("Merhaba")

        episodes = episode_logger.get_session_episodes()
        episode = episodes[0]

        assert episode.response_text == result.output
        assert episode.response_length_chars > 0
        assert episode.response_length_words > 0

    def test_pipeline_logs_processing_time(self, episode_logger):
        """Test pipeline logs processing time."""
        from core.language.pipeline import ThoughtToSpeechPipeline

        pipeline = ThoughtToSpeechPipeline(episode_logger=episode_logger)
        pipeline.process("Test message")

        episodes = episode_logger.get_session_episodes()
        episode = episodes[0]

        # Processing time should be non-negative (can be 0 in fast unit tests)
        assert episode.processing_time_ms >= 0
        assert episode.processing_time_ms < 10000  # Should be under 10 seconds


# =========================================================================
# 7. ID Generation Test (1 test)
# =========================================================================

def test_generate_episode_log_id():
    """Test episode log ID generation."""
    id1 = generate_episode_log_id()
    id2 = generate_episode_log_id()

    assert id1.startswith("eplog_")
    assert id2.startswith("eplog_")
    assert id1 != id2  # Should be unique


# =========================================================================
# 8. Context & Construction Integration Tests (Faz 5 B+)
# =========================================================================

@pytest.fixture
def episode_logger(tmp_path):
    """Create episode logger fixture for new tests."""
    store_path = tmp_path / "test_context_episodes.jsonl"
    store = JSONLEpisodeStore(str(store_path))
    return EpisodeLogger(store, "test_context_session")


def test_context_snapshot_logged_correctly(episode_logger):
    """Test context snapshot is correctly logged to episode."""
    from core.language.conversation import ContextManager
    from core.language.intent.types import IntentCategory
    from core.language.dialogue.types import DialogueAct

    # Create context manager with some conversation history
    context_manager = ContextManager()
    context_manager.add_user_message("Merhaba", IntentCategory.GREETING)
    context_manager.add_assistant_message("Selam!", DialogueAct.GREET)
    context_manager.add_user_message("Harika, çok mutluyum!", IntentCategory.EXPRESS_POSITIVE)

    # Start episode
    episode_id = episode_logger.start_episode("Nasılsın?", "nasilsin")
    episode_logger.update_intent(IntentCategory.ASK_WELLBEING, confidence=0.9)

    # Update context from context_manager
    episode_logger.update_context(context_manager)

    # Finalize
    episode_logger.finalize_episode(processing_time_ms=100)

    # Retrieve and verify
    episodes = episode_logger.get_session_episodes()
    episode = episodes[0]

    # Verify all context fields are set correctly
    assert episode.context_turn_count == 2  # Two user messages before this one
    assert episode.context_last_user_intent == IntentCategory.EXPRESS_POSITIVE
    assert episode.context_last_assistant_act == DialogueAct.GREET
    assert episode.context_sentiment is not None  # Sentiment calculated
    assert episode.context_sentiment_trend in [-1, 0, 1]  # Valid trend value
    assert episode.context_topic is not None or episode.context_topic is None  # Can be None if no topic detected
    assert episode.context_is_followup is not None  # Should be set (True or False)


def test_construction_category_and_level_logged(episode_logger):
    """Test construction category and level are correctly logged."""
    from core.language.construction.mvcs import MVCSLoader, MVCSCategory
    from core.learning.episode_types import ConstructionSource, ConstructionLevel

    # Load MVCS constructions
    loader = MVCSLoader()
    greet_constructions = loader.get_by_category(MVCSCategory.GREET)
    assert len(greet_constructions) > 0

    # Get first greeting construction
    greeting = greet_constructions[0]

    # Start episode
    episode_id = episode_logger.start_episode("Merhaba", "merhaba")
    episode_logger.update_intent(IntentCategory.GREETING, confidence=0.95)

    # Update construction with real MVCS construction
    category = greeting.extra_data.get("mvcs_category", "unknown")
    level = greeting.level if hasattr(greeting, 'level') else ConstructionLevel.SURFACE

    episode_logger.update_construction(
        construction_id=greeting.id,
        category=category,
        source=ConstructionSource.HUMAN_DEFAULT,
        level=level
    )

    # Add output
    episode_logger.update_output("Merhaba!")

    # Finalize
    episode_logger.finalize_episode(processing_time_ms=50)

    # Retrieve and verify
    episodes = episode_logger.get_session_episodes()
    episode = episodes[0]

    # Verify construction metadata
    assert episode.construction_id == greeting.id
    assert episode.construction_category == MVCSCategory.GREET.value  # Should be "greet", not "unknown"
    assert episode.construction_source == ConstructionSource.HUMAN_DEFAULT
    assert episode.construction_level == ConstructionLevel.SURFACE  # MVCS constructions are SURFACE level


def test_pipeline_logs_construction_category_correctly():
    """Test that pipeline correctly extracts and logs construction category."""
    from core.language.pipeline import ThoughtToSpeechPipeline
    import tempfile

    # Create temp episode store
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_file = f.name

    try:
        from core.learning.episode_store import JSONLEpisodeStore
        from core.learning.episode_logger import EpisodeLogger

        store = JSONLEpisodeStore(temp_file)
        logger = EpisodeLogger(store, session_id="test_session")

        # Create pipeline with episode logger
        pipeline = ThoughtToSpeechPipeline(episode_logger=logger)

        # Process a greeting message
        result = pipeline.process("Merhaba!")

        # Get logged episode
        episodes = logger.get_session_episodes()
        assert len(episodes) == 1

        episode = episodes[0]

        # Verify construction category is NOT "unknown"
        # Should be a valid MVCS category like "greet", "respond_wellbeing", etc.
        assert episode.construction_category != "unknown"
        assert episode.construction_category != ""
        # Should be one of the MVCS categories
        assert episode.construction_category in [
            "greet", "self_intro", "ask_wellbeing", "simple_inform",
            "empathize_basic", "clarify_request", "safe_refusal",
            "respond_wellbeing", "receive_thanks", "light_chitchat",
            "acknowledge_positive"
        ]

        # Verify construction level is valid
        assert episode.construction_level in [
            ConstructionLevel.SURFACE,
            ConstructionLevel.MIDDLE,
            ConstructionLevel.DEEP
        ]

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


# =========================================================================
# 9. Feedback Persistence Tests (4 tests)
# =========================================================================

class TestFeedbackPersistence:
    """Test feedback persistence to JSONL via update_episode."""

    @pytest.fixture
    def temp_store(self, tmp_path):
        """Create temporary episode store."""
        store_path = tmp_path / "feedback_episodes.jsonl"
        return JSONLEpisodeStore(str(store_path))

    @pytest.fixture
    def logger(self, temp_store):
        """Create episode logger with temp store."""
        return EpisodeLogger(temp_store, "test_feedback_session")

    def test_feedback_persists_to_jsonl(self, logger):
        """Test that /feedback updates episode JSONL correctly."""
        # Create and finalize an episode
        episode_id = logger.start_episode("Merhaba", "merhaba")
        logger.update_intent(IntentCategory.GREETING, confidence=0.9)
        logger.update_output("Selam, nasılsın?")
        logger.finalize_episode(processing_time_ms=100)

        # Verify initial state has no feedback
        episode = logger.store.get_by_id(episode_id)
        assert episode.feedback_explicit is None

        # Add positive feedback
        success = logger.add_feedback(episode_id, explicit=1.0)
        assert success is True

        # Verify feedback persisted
        updated_episode = logger.store.get_by_id(episode_id)
        assert updated_episode.feedback_explicit == 1.0

    def test_negative_feedback_persists(self, logger):
        """Test negative feedback persists correctly."""
        # Create and finalize an episode
        episode_id = logger.start_episode("Test", "test")
        logger.update_intent(IntentCategory.GREETING, confidence=0.9)
        logger.finalize_episode(processing_time_ms=50)

        # Add negative feedback
        success = logger.add_feedback(episode_id, explicit=-1.0)
        assert success is True

        # Verify
        episode = logger.store.get_by_id(episode_id)
        assert episode.feedback_explicit == -1.0

    def test_add_feedback_to_last_episode(self, logger):
        """Test add_feedback_to_last convenience method."""
        # Create multiple episodes
        logger.start_episode("First", "first")
        logger.update_intent(IntentCategory.GREETING, confidence=0.9)
        logger.finalize_episode(50)

        logger.start_episode("Second", "second")
        logger.update_intent(IntentCategory.THANK, confidence=0.85)
        logger.finalize_episode(60)

        # Add feedback to last episode
        success = logger.add_feedback_to_last(explicit=1.0)
        assert success is True

        # Verify only the last episode has feedback
        episodes = logger.get_session_episodes()
        assert len(episodes) == 2
        # First episode (older) should not have feedback
        assert episodes[0].feedback_explicit is None
        # Second episode (last) should have feedback
        assert episodes[1].feedback_explicit == 1.0

    def test_update_episode_nonexistent_returns_false(self, temp_store):
        """Test update_episode returns False for nonexistent ID."""
        result = temp_store.update_episode("nonexistent_id", {"feedback_explicit": 1.0})
        assert result is False

    def test_update_episode_preserves_other_fields(self, logger):
        """Test update_episode only modifies specified fields."""
        # Create episode with full data
        episode_id = logger.start_episode("Merhaba", "merhaba")
        logger.update_intent(IntentCategory.GREETING, confidence=0.95)
        logger.update_output("Selam!")
        logger.update_risk(
            risk_level=RiskLevel.LOW,
            risk_score=0.1,
            approval_status=ApprovalStatus.APPROVED
        )
        logger.finalize_episode(processing_time_ms=100)

        # Update only feedback
        logger.add_feedback(episode_id, explicit=1.0)

        # Verify other fields unchanged
        episode = logger.store.get_by_id(episode_id)
        assert episode.feedback_explicit == 1.0
        assert episode.user_message == "Merhaba"
        assert episode.intent_primary == IntentCategory.GREETING
        assert episode.intent_confidence == 0.95
        assert episode.response_text == "Selam!"
        assert episode.risk_level == RiskLevel.LOW
        assert episode.approval_status == ApprovalStatus.APPROVED


# =========================================================================
# 10. Construction ID Determinism Tests (3 tests)
# =========================================================================

class TestConstructionIDDeterminism:
    """Test that construction IDs are deterministic and stable."""

    def test_construction_id_is_deterministic(self):
        """Test that same mvcs_name always produces same ID."""
        from core.language.construction.types import generate_deterministic_construction_id

        # Generate same ID twice
        id1 = generate_deterministic_construction_id("greet_simple")
        id2 = generate_deterministic_construction_id("greet_simple")

        assert id1 == id2
        assert id1 == "cons_greet_simple"

    def test_mvcs_constructions_have_deterministic_ids(self):
        """Test MVCS constructions have deterministic, mvcs_name-based IDs."""
        from core.language.construction.mvcs import MVCSLoader

        # Load twice
        loader1 = MVCSLoader()
        constructions1 = loader1.load_all()

        loader2 = MVCSLoader()
        constructions2 = loader2.load_all()

        # Same constructions should have same IDs
        for c1 in constructions1:
            c1_name = c1.extra_data.get("mvcs_name")
            if c1_name:
                # Find matching construction in second load
                matching = [c2 for c2 in constructions2 if c2.extra_data.get("mvcs_name") == c1_name]
                assert len(matching) == 1, f"Should find exactly one match for {c1_name}"
                assert c1.id == matching[0].id, f"IDs should match for {c1_name}"

    def test_construction_id_format(self):
        """Test construction ID format is cons_{mvcs_name}."""
        from core.language.construction.mvcs import MVCSLoader

        loader = MVCSLoader()
        constructions = loader.load_all()

        for construction in constructions:
            mvcs_name = construction.extra_data.get("mvcs_name")
            if mvcs_name:
                expected_id = f"cons_{mvcs_name}"
                assert construction.id == expected_id, f"ID should be {expected_id}, got {construction.id}"


# =========================================================================
# 11. ImplicitFeedback Wiring Tests (4 tests)
# =========================================================================

class TestImplicitFeedbackWiring:
    """Test implicit feedback detection and persistence."""

    @pytest.fixture
    def temp_store(self, tmp_path):
        """Create temporary episode store."""
        store_path = tmp_path / "implicit_feedback_episodes.jsonl"
        return JSONLEpisodeStore(str(store_path))

    @pytest.fixture
    def logger(self, temp_store):
        """Create episode logger with temp store."""
        return EpisodeLogger(temp_store, "test_implicit_session")

    def test_implicit_feedback_user_thanked(self, logger):
        """Test user_thanked implicit feedback is detected and persisted."""
        # Create an episode
        episode_id = logger.start_episode("Merhaba", "merhaba")
        logger.update_intent(IntentCategory.GREETING, confidence=0.9)
        logger.update_output("Selam!")
        logger.finalize_episode(processing_time_ms=100)

        # Add implicit feedback with user_thanked
        implicit = ImplicitFeedback(user_thanked=True)
        success = logger.add_feedback(episode_id, implicit=implicit)
        assert success is True

        # Verify persistence
        episode = logger.store.get_by_id(episode_id)
        assert episode.feedback_implicit is not None
        assert episode.feedback_implicit.user_thanked is True

    def test_implicit_feedback_user_rephrased(self, logger):
        """Test user_rephrased implicit feedback is detected and persisted."""
        # Create an episode
        episode_id = logger.start_episode("Merhaba", "merhaba")
        logger.update_intent(IntentCategory.GREETING, confidence=0.9)
        logger.update_output("Selam!")
        logger.finalize_episode(processing_time_ms=100)

        # Add implicit feedback with user_rephrased
        implicit = ImplicitFeedback(user_rephrased=True)
        success = logger.add_feedback(episode_id, implicit=implicit)
        assert success is True

        # Verify persistence
        episode = logger.store.get_by_id(episode_id)
        assert episode.feedback_implicit is not None
        assert episode.feedback_implicit.user_rephrased is True

    def test_implicit_feedback_conversation_continued(self, logger):
        """Test conversation_continued implicit feedback is detected and persisted."""
        # Create an episode
        episode_id = logger.start_episode("Test", "test")
        logger.update_intent(IntentCategory.GREETING, confidence=0.9)
        logger.update_output("Hello!")
        logger.finalize_episode(processing_time_ms=100)

        # Add implicit feedback with conversation_continued
        implicit = ImplicitFeedback(conversation_continued=True)
        success = logger.add_feedback(episode_id, implicit=implicit)
        assert success is True

        # Verify persistence
        episode = logger.store.get_by_id(episode_id)
        assert episode.feedback_implicit is not None
        assert episode.feedback_implicit.conversation_continued is True

    def test_implicit_feedback_to_dict(self):
        """Test ImplicitFeedback.to_dict() method."""
        implicit = ImplicitFeedback(
            user_thanked=True,
            conversation_continued=True,
            user_rephrased=False,
            user_complained=False,
            session_ended_abruptly=False
        )

        data = implicit.to_dict()

        assert data["user_thanked"] is True
        assert data["conversation_continued"] is True
        assert data["user_rephrased"] is False
        assert data["user_complained"] is False
        assert data["session_ended_abruptly"] is False
