"""
tests/unit/test_chat_learning.py

Chat Agent Learning Integration Tests.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from io import StringIO

from core.language.chat_agent import (
    UEMChatAgent,
    ChatConfig,
    ChatResponse,
    create_chat_agent,
)
from core.language.llm_adapter import MockLLMAdapter


# ============================================================================
# Chat Agent with Learning Tests
# ============================================================================

class TestChatAgentLearning:
    """Chat Agent learning integration tests."""

    def test_agent_with_learning_enabled(self):
        """Test agent initializes with learning enabled."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        assert agent.learning is not None

    def test_agent_with_learning_disabled(self):
        """Test agent initializes with learning disabled."""
        config = ChatConfig(enable_learning=False)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        assert agent.learning is None

    def test_chat_response_has_source(self):
        """Test chat response includes source field."""
        config = ChatConfig(enable_learning=True, use_learned_responses=False)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        response = agent.chat("Hello")

        assert hasattr(response, 'source')
        assert response.source == "llm"

    def test_chat_response_has_interaction_id(self):
        """Test chat response includes interaction_id."""
        agent = UEMChatAgent(llm=MockLLMAdapter())
        agent.start_session("test_user")

        response = agent.chat("Hello")

        assert hasattr(response, 'interaction_id')
        assert response.interaction_id is not None
        assert response.interaction_id.startswith("int_")

    def test_feedback_positive(self):
        """Test positive feedback recording."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        # First chat to create an interaction
        agent.chat("Hello")

        # Then give feedback
        result = agent.feedback(positive=True, reason="Great response!")

        assert result is True

    def test_feedback_negative(self):
        """Test negative feedback recording."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        # First chat to create an interaction
        agent.chat("Hello")

        # Then give feedback
        result = agent.feedback(positive=False, reason="Not helpful")

        assert result is True

    def test_feedback_without_interaction(self):
        """Test feedback fails without prior interaction."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        # Try feedback without chatting first
        result = agent.feedback(positive=True)

        assert result is False

    def test_feedback_without_learning(self):
        """Test feedback fails when learning disabled."""
        config = ChatConfig(enable_learning=False)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        agent.chat("Hello")
        result = agent.feedback(positive=True)

        assert result is False

    def test_get_learned_count(self):
        """Test getting learned pattern count."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        initial_count = agent.get_learned_count()

        # Chat creates patterns
        agent.chat("Hello")
        agent.chat("How are you?")

        new_count = agent.get_learned_count()

        assert new_count >= initial_count

    def test_get_learned_count_without_learning(self):
        """Test get_learned_count returns 0 when learning disabled."""
        config = ChatConfig(enable_learning=False)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        count = agent.get_learned_count()

        assert count == 0

    def test_get_learning_stats(self):
        """Test getting learning statistics."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        agent.chat("Hello")
        agent.feedback(positive=True)

        stats = agent.get_learning_stats()

        assert "feedback" in stats
        assert "patterns" in stats

    def test_get_learning_stats_without_learning(self):
        """Test get_learning_stats returns empty when learning disabled."""
        config = ChatConfig(enable_learning=False)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        stats = agent.get_learning_stats()

        assert stats == {}

    def test_session_stats_includes_patterns(self):
        """Test session stats include pattern count."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        agent.chat("Hello")

        stats = agent.get_session_stats()

        assert "patterns_learned" in stats

    def test_pattern_stored_on_llm_response(self):
        """Test pattern is stored when LLM generates response."""
        config = ChatConfig(enable_learning=True, use_learned_responses=False)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        initial_count = agent.get_learned_count()
        agent.chat("Hello")
        new_count = agent.get_learned_count()

        assert new_count > initial_count

    def test_last_interaction_id_tracking(self):
        """Test last interaction ID is tracked."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        response = agent.chat("Hello")

        assert agent._last_interaction_id == response.interaction_id


# ============================================================================
# CLI Feedback Command Tests
# ============================================================================

class TestCLIFeedbackCommands:
    """CLI feedback command tests."""

    def test_cmd_good_with_learning(self):
        """Test /good command with learning enabled."""
        from interface.chat.cli import CLIChat

        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        cli = CLIChat(agent=agent, user_id="test_user")
        cli._session_id = agent.start_session("test_user")

        # Chat first
        agent.chat("Hello")

        # Capture output
        import sys
        captured = StringIO()
        sys.stdout = captured

        cli._cmd_good("")

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert "Pozitif feedback kaydedildi" in output

    def test_cmd_bad_with_learning(self):
        """Test /bad command with learning enabled."""
        from interface.chat.cli import CLIChat

        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        cli = CLIChat(agent=agent, user_id="test_user")
        cli._session_id = agent.start_session("test_user")

        # Chat first
        agent.chat("Hello")

        # Capture output
        import sys
        captured = StringIO()
        sys.stdout = captured

        cli._cmd_bad("")

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert "Negatif feedback kaydedildi" in output

    def test_cmd_learned(self):
        """Test /learned command."""
        from interface.chat.cli import CLIChat

        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        cli = CLIChat(agent=agent, user_id="test_user")
        cli._session_id = agent.start_session("test_user")

        # Chat to create patterns
        agent.chat("Hello")

        # Capture output
        import sys
        captured = StringIO()
        sys.stdout = captured

        cli._cmd_learned()

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert "Ogrenilen pattern sayisi" in output

    def test_cmd_stats_shows_learning(self):
        """Test /stats shows learning info."""
        from interface.chat.cli import CLIChat

        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        cli = CLIChat(agent=agent, user_id="test_user")
        cli._session_id = agent.start_session("test_user")

        agent.chat("Hello")

        # Capture output
        import sys
        captured = StringIO()
        sys.stdout = captured

        cli._cmd_stats()

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert "Ogrenilen pattern" in output


# ============================================================================
# Integration Tests
# ============================================================================

class TestChatLearningIntegration:
    """Integration tests for chat + learning."""

    def test_feedback_reinforces_pattern(self):
        """Test feedback reinforces the associated pattern."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        # Chat and give positive feedback
        agent.chat("Hello")
        agent.feedback(positive=True)

        # Check reinforcement stats
        stats = agent.get_learning_stats()
        reinforcement = stats.get("reinforcement", {})

        assert reinforcement.get("total_reinforcements", 0) >= 1

    def test_multiple_feedback_accumulates(self):
        """Test multiple feedback accumulates correctly."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        # Multiple chats with feedback
        for i in range(3):
            agent.chat(f"Message {i}")
            agent.feedback(positive=True)

        stats = agent.get_learning_stats()
        feedback_stats = stats.get("feedback", {})

        assert feedback_stats.get("total_feedback", 0) >= 3

    def test_learning_stats_complete(self):
        """Test learning stats are complete."""
        config = ChatConfig(enable_learning=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        agent.start_session("test_user")

        agent.chat("Hello")
        agent.feedback(positive=True)

        stats = agent.get_learning_stats()

        assert "feedback" in stats
        assert "patterns" in stats
        assert "reinforcement" in stats
        assert "adaptation" in stats
        assert "learning_rate" in stats
