"""
tests/unit/test_pattern_analyzer.py

Unit tests for PatternAnalyzer.

Test groups:
- Intent frequency calculation
- Dialogue act frequency calculation
- Construction usage calculation
- Feedback correlation calculation
- Fallback rate calculation
- Report generation

UEM v2 - Faz 5 Pattern Evolution Tests.
"""

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
)
from core.learning.episode_store import JSONLEpisodeStore
from core.learning.pattern_analyzer import PatternAnalyzer, create_analyzer
from core.language.intent.types import IntentCategory
from core.language.dialogue.types import DialogueAct
from core.language.risk.types import RiskLevel


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def temp_store():
    """Create a temporary episode store for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        filepath = f.name

    store = JSONLEpisodeStore(filepath)
    yield store

    # Cleanup
    Path(filepath).unlink(missing_ok=True)


@pytest.fixture
def sample_episodes(temp_store):
    """Create sample episodes for testing."""
    episodes = [
        # Greeting episodes
        EpisodeLog(
            id="eplog_001",
            session_id="sess_001",
            turn_number=1,
            user_message="Merhaba",
            user_message_normalized="merhaba",
            intent_primary=IntentCategory.GREETING,
            dialogue_act_selected=DialogueAct.GREET,
            construction_category="GREETING",
            response_text="Merhaba! Nasılsınız?",
            feedback_explicit=1.0,
        ),
        EpisodeLog(
            id="eplog_002",
            session_id="sess_001",
            turn_number=2,
            user_message="Selam",
            user_message_normalized="selam",
            intent_primary=IntentCategory.GREETING,
            dialogue_act_selected=DialogueAct.GREET,
            construction_category="GREETING",
            response_text="Selam! Hoş geldiniz.",
            feedback_explicit=1.0,
        ),
        # Express positive
        EpisodeLog(
            id="eplog_003",
            session_id="sess_001",
            turn_number=3,
            user_message="İyiyim teşekkürler",
            user_message_normalized="iyiyim tesekkurler",
            intent_primary=IntentCategory.EXPRESS_POSITIVE,
            dialogue_act_selected=DialogueAct.ACKNOWLEDGE_POSITIVE,
            construction_category="ACKNOWLEDGE",
            response_text="Ne güzel! Bunu duymak sevindirici.",
            feedback_explicit=0.5,
        ),
        # Unknown intent (fallback scenario)
        EpisodeLog(
            id="eplog_004",
            session_id="sess_001",
            turn_number=4,
            user_message="asdfghjkl",
            user_message_normalized="asdfghjkl",
            intent_primary=IntentCategory.UNKNOWN,
            dialogue_act_selected=DialogueAct.ACKNOWLEDGE,
            construction_category="FALLBACK",
            response_text="Anlıyorum.",
            feedback_explicit=-1.0,
        ),
        # Thank intent
        EpisodeLog(
            id="eplog_005",
            session_id="sess_002",
            turn_number=1,
            user_message="Teşekkür ederim",
            user_message_normalized="tesekkur ederim",
            intent_primary=IntentCategory.THANK,
            dialogue_act_selected=DialogueAct.RECEIVE_THANKS,
            construction_category="THANKS_RESPONSE",
            response_text="Rica ederim!",
            feedback_explicit=1.0,
        ),
        # Episode without feedback
        EpisodeLog(
            id="eplog_006",
            session_id="sess_002",
            turn_number=2,
            user_message="Nasılsın?",
            user_message_normalized="nasilsin",
            intent_primary=IntentCategory.ASK_WELLBEING,
            dialogue_act_selected=DialogueAct.RESPOND_WELLBEING,
            construction_category="WELLBEING",
            response_text="İyiyim, teşekkürler!",
            feedback_explicit=None,
        ),
        # Another unknown for fallback rate testing
        EpisodeLog(
            id="eplog_007",
            session_id="sess_002",
            turn_number=3,
            user_message="xyz123",
            user_message_normalized="xyz123",
            intent_primary=IntentCategory.UNKNOWN,
            dialogue_act_selected=DialogueAct.ACKNOWLEDGE,
            construction_category="FALLBACK",
            response_text="Hmm, anlıyorum.",
            feedback_explicit=-0.5,
        ),
        # Farewell
        EpisodeLog(
            id="eplog_008",
            session_id="sess_002",
            turn_number=4,
            user_message="Görüşürüz",
            user_message_normalized="gorusuruz",
            intent_primary=IntentCategory.FAREWELL,
            dialogue_act_selected=DialogueAct.CLOSE_CONVERSATION,
            construction_category="FAREWELL",
            response_text="Hoşça kalın! Görüşmek üzere.",
            feedback_explicit=1.0,
        ),
    ]

    for ep in episodes:
        temp_store.save(ep)

    return temp_store


# =========================================================================
# 1. Intent Frequency Tests
# =========================================================================

class TestIntentFrequency:
    """Test intent frequency analysis."""

    def test_intent_frequency_counts_correctly(self, sample_episodes):
        """Test that intent frequencies are counted correctly."""
        analyzer = PatternAnalyzer(sample_episodes)
        freq = analyzer.analyze_intent_frequency()

        assert freq["greeting"] == 2
        assert freq["unknown"] == 2
        assert freq["express_positive"] == 1
        assert freq["thank"] == 1
        assert freq["ask_wellbeing"] == 1
        assert freq["farewell"] == 1

    def test_intent_frequency_sorted_by_count(self, sample_episodes):
        """Test that intent frequencies are sorted by count (descending)."""
        analyzer = PatternAnalyzer(sample_episodes)
        freq = analyzer.analyze_intent_frequency()

        counts = list(freq.values())
        assert counts == sorted(counts, reverse=True)

    def test_intent_frequency_empty_store(self, temp_store):
        """Test intent frequency with empty store."""
        analyzer = PatternAnalyzer(temp_store)
        freq = analyzer.analyze_intent_frequency()

        assert freq == {}


# =========================================================================
# 2. Dialogue Act Frequency Tests
# =========================================================================

class TestActFrequency:
    """Test dialogue act frequency analysis."""

    def test_act_frequency_counts_correctly(self, sample_episodes):
        """Test that dialogue act frequencies are counted correctly."""
        analyzer = PatternAnalyzer(sample_episodes)
        freq = analyzer.analyze_act_frequency()

        assert freq["greet"] == 2
        assert freq["acknowledge"] == 2
        assert freq["acknowledge_positive"] == 1
        assert freq["receive_thanks"] == 1
        assert freq["respond_wellbeing"] == 1
        assert freq["close_conversation"] == 1

    def test_act_frequency_sorted(self, sample_episodes):
        """Test that act frequencies are sorted by count."""
        analyzer = PatternAnalyzer(sample_episodes)
        freq = analyzer.analyze_act_frequency()

        counts = list(freq.values())
        assert counts == sorted(counts, reverse=True)


# =========================================================================
# 3. Construction Usage Tests
# =========================================================================

class TestConstructionUsage:
    """Test construction usage analysis."""

    def test_construction_usage_counts_correctly(self, sample_episodes):
        """Test that construction usage is counted correctly."""
        analyzer = PatternAnalyzer(sample_episodes)
        usage = analyzer.analyze_construction_usage()

        assert usage["GREETING"] == 2
        assert usage["FALLBACK"] == 2
        assert usage["ACKNOWLEDGE"] == 1
        assert usage["THANKS_RESPONSE"] == 1
        assert usage["WELLBEING"] == 1
        assert usage["FAREWELL"] == 1


# =========================================================================
# 4. Feedback Correlation Tests
# =========================================================================

class TestFeedbackCorrelation:
    """Test feedback correlation analysis."""

    def test_feedback_correlation_calculation(self, sample_episodes):
        """Test feedback correlation is calculated correctly."""
        analyzer = PatternAnalyzer(sample_episodes)
        corr = analyzer.analyze_feedback_correlation()

        # Greeting: 2 episodes with 1.0 feedback each -> avg 1.0
        assert "greeting" in corr
        assert corr["greeting"]["avg_feedback"] == 1.0
        assert corr["greeting"]["count"] == 2
        assert corr["greeting"]["positive_rate"] == 1.0

        # Unknown: 2 episodes with -1.0 and -0.5 feedback -> avg -0.75
        assert "unknown" in corr
        assert corr["unknown"]["avg_feedback"] == -0.75
        assert corr["unknown"]["count"] == 2
        assert corr["unknown"]["positive_rate"] == 0.0

    def test_feedback_correlation_excludes_null_feedback(self, sample_episodes):
        """Test that episodes without feedback are excluded."""
        analyzer = PatternAnalyzer(sample_episodes)
        corr = analyzer.analyze_feedback_correlation()

        # ask_wellbeing has no feedback, should not appear
        # (only 1 episode with null feedback)
        if "ask_wellbeing" in corr:
            # If it appears, it should have 0 count from feedback episodes
            assert corr["ask_wellbeing"]["count"] == 0

    def test_feedback_correlation_sorted_by_avg(self, sample_episodes):
        """Test that correlation is sorted by avg feedback (best first)."""
        analyzer = PatternAnalyzer(sample_episodes)
        corr = analyzer.analyze_feedback_correlation()

        avgs = [stats["avg_feedback"] for stats in corr.values()]
        assert avgs == sorted(avgs, reverse=True)

    def test_act_feedback_correlation(self, sample_episodes):
        """Test dialogue act feedback correlation."""
        analyzer = PatternAnalyzer(sample_episodes)
        corr = analyzer.analyze_act_feedback_correlation()

        assert "greet" in corr
        assert corr["greet"]["avg_feedback"] == 1.0
        assert corr["greet"]["count"] == 2


# =========================================================================
# 5. Fallback Rate Tests
# =========================================================================

class TestFallbackRate:
    """Test fallback rate analysis."""

    def test_fallback_rate_calculation(self, sample_episodes):
        """Test fallback rate is calculated correctly."""
        analyzer = PatternAnalyzer(sample_episodes)
        fallback = analyzer.analyze_fallback_rate()

        # 8 total episodes, 2 unknown intent -> 25% unknown rate
        assert fallback["total_episodes"] == 8
        assert fallback["unknown_count"] == 2
        assert fallback["unknown_intent_rate"] == 0.25

    def test_fallback_response_rate(self, sample_episodes):
        """Test fallback response detection."""
        analyzer = PatternAnalyzer(sample_episodes)
        fallback = analyzer.analyze_fallback_rate()

        # 2 episodes with fallback responses: "Anlıyorum." and "Hmm, anlıyorum."
        assert fallback["fallback_response_count"] == 2
        assert fallback["fallback_response_rate"] == 0.25

    def test_fallback_rate_empty_store(self, temp_store):
        """Test fallback rate with empty store."""
        analyzer = PatternAnalyzer(temp_store)
        fallback = analyzer.analyze_fallback_rate()

        assert fallback["total_episodes"] == 0
        assert fallback["unknown_intent_rate"] == 0.0
        assert fallback["fallback_response_rate"] == 0.0


# =========================================================================
# 6. Session Stats Tests
# =========================================================================

class TestSessionStats:
    """Test session statistics analysis."""

    def test_session_stats(self, sample_episodes):
        """Test session statistics are correct."""
        analyzer = PatternAnalyzer(sample_episodes)
        stats = analyzer.analyze_session_stats()

        assert stats["total_sessions"] == 2
        assert stats["total_episodes"] == 8
        # sess_001 has 4 turns, sess_002 has 4 turns -> avg 4.0
        assert stats["avg_turns_per_session"] == 4.0


# =========================================================================
# 7. Feedback Summary Tests
# =========================================================================

class TestFeedbackSummary:
    """Test feedback summary analysis."""

    def test_feedback_summary(self, sample_episodes):
        """Test feedback summary is correct."""
        analyzer = PatternAnalyzer(sample_episodes)
        summary = analyzer.analyze_feedback_summary()

        assert summary["total_episodes"] == 8
        # 7 episodes with feedback (1 null)
        assert summary["episodes_with_feedback"] == 7
        assert summary["feedback_coverage"] == 0.88 or summary["feedback_coverage"] == 0.87

        # Positive: 5 (1.0, 1.0, 0.5, 1.0, 1.0)
        # Negative: 2 (-1.0, -0.5)
        assert summary["positive_count"] == 5
        assert summary["negative_count"] == 2
        assert summary["neutral_count"] == 0


# =========================================================================
# 8. Report Generation Tests
# =========================================================================

class TestReportGeneration:
    """Test report generation."""

    def test_report_generation(self, sample_episodes):
        """Test report is generated in markdown format."""
        analyzer = PatternAnalyzer(sample_episodes)
        report = analyzer.generate_report()

        # Check headers
        assert "# Episode Analysis Report" in report
        assert "## Overview" in report
        assert "## Intent Frequency" in report
        assert "## Dialogue Act Frequency" in report
        assert "## Construction Usage" in report
        assert "## Feedback Summary" in report
        assert "## Feedback Correlation" in report
        assert "## Fallback Rate" in report
        assert "## Recommendations" in report

    def test_report_contains_tables(self, sample_episodes):
        """Test report contains markdown tables."""
        analyzer = PatternAnalyzer(sample_episodes)
        report = analyzer.generate_report()

        # Check for table separators
        assert "|--------|" in report or "|-----|" in report

    def test_report_empty_store(self, temp_store):
        """Test report generation with empty store."""
        analyzer = PatternAnalyzer(temp_store)
        report = analyzer.generate_report()

        assert "# Episode Analysis Report" in report
        assert "**Total Episodes:** 0" in report


# =========================================================================
# 9. Recommendations Tests
# =========================================================================

class TestRecommendations:
    """Test recommendations generation."""

    def test_recommendations_for_high_unknown_rate(self, sample_episodes):
        """Test recommendations when unknown rate is high."""
        analyzer = PatternAnalyzer(sample_episodes)
        recs = analyzer.generate_recommendations()

        # 25% unknown rate is > 10%, should have recommendation
        has_unknown_rec = any("unknown" in r.lower() for r in recs)
        assert has_unknown_rec

    def test_recommendations_for_negative_feedback(self, sample_episodes):
        """Test recommendations for intents with negative feedback."""
        analyzer = PatternAnalyzer(sample_episodes)
        recs = analyzer.generate_recommendations()

        # unknown intent has negative avg feedback (-0.75)
        # Should be mentioned in recommendations
        has_negative_rec = any("negatif" in r.lower() or "negative" in r.lower() for r in recs)
        assert has_negative_rec


# =========================================================================
# 10. Helper Function Tests
# =========================================================================

class TestHelperFunctions:
    """Test helper functions."""

    def test_create_analyzer(self, temp_store):
        """Test create_analyzer helper."""
        analyzer = create_analyzer(str(temp_store.filepath))

        assert isinstance(analyzer, PatternAnalyzer)

    def test_lazy_loading(self, sample_episodes):
        """Test that episodes are lazily loaded."""
        analyzer = PatternAnalyzer(sample_episodes)

        # Episodes should not be loaded yet
        assert analyzer._episodes is None

        # After first analysis, episodes should be loaded
        analyzer.analyze_intent_frequency()
        assert analyzer._episodes is not None
        assert len(analyzer._episodes) == 8
