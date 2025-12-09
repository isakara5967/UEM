"""
tests/unit/test_chat_agent_pipeline.py

ChatAgent Pipeline entegrasyonu test modulu.
20+ test ile pipeline entegrasyonunu test eder.
"""

import pytest
from typing import Dict, List, Any, Optional

from core.language.chat_agent import (
    UEMChatAgent,
    ChatConfig,
    ChatResponse,
    PIPELINE_AVAILABLE,
)
from core.language.llm_adapter import MockLLMAdapter


# ============================================================================
# ChatConfig Pipeline Tests
# ============================================================================

class TestChatConfigPipeline:
    """ChatConfig pipeline ayarlari testleri."""

    def test_default_pipeline_disabled(self):
        """Varsayilana pipeline kapali."""
        config = ChatConfig()

        assert config.use_pipeline is False
        assert config.pipeline_config is None

    def test_enable_pipeline_config(self):
        """Pipeline aktif config."""
        config = ChatConfig(use_pipeline=True)

        assert config.use_pipeline is True

    def test_pipeline_config_with_custom_config(self):
        """Ozel pipeline config."""
        from core.language.pipeline import PipelineConfig

        pipeline_config = PipelineConfig.minimal()
        config = ChatConfig(use_pipeline=True, pipeline_config=pipeline_config)

        assert config.use_pipeline is True
        assert config.pipeline_config is not None


# ============================================================================
# ChatResponse Pipeline Tests
# ============================================================================

class TestChatResponsePipeline:
    """ChatResponse pipeline alanlari testleri."""

    def test_response_with_pipeline_source(self):
        """Pipeline kaynakli cevap."""
        response = ChatResponse(
            content="Test response",
            source="pipeline"
        )

        assert response.source == "pipeline"
        assert response.pipeline_result is None

    def test_response_with_pipeline_result(self):
        """Pipeline sonucu ile cevap."""
        from core.language.pipeline import PipelineResult

        result = PipelineResult(success=True, output="Test")
        response = ChatResponse(
            content="Test",
            source="pipeline",
            pipeline_result=result
        )

        assert response.pipeline_result is not None
        assert response.pipeline_result.success is True


# ============================================================================
# UEMChatAgent Pipeline Initialization Tests
# ============================================================================

class TestChatAgentPipelineInit:
    """Chat agent pipeline baslatma testleri."""

    def test_agent_default_no_pipeline(self):
        """Varsayilan agent pipeline olmadan."""
        agent = UEMChatAgent(llm=MockLLMAdapter())

        assert agent._use_pipeline is False
        assert agent._pipeline is None

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_agent_with_pipeline_enabled(self):
        """Pipeline aktif agent."""
        config = ChatConfig(use_pipeline=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        assert agent._use_pipeline is True
        assert agent._pipeline is not None

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_agent_with_custom_pipeline(self):
        """Ozel pipeline ile agent."""
        from core.language.pipeline import ThoughtToSpeechPipeline

        pipeline = ThoughtToSpeechPipeline()
        agent = UEMChatAgent(llm=MockLLMAdapter(), pipeline=pipeline)

        assert agent._pipeline is pipeline
        assert agent._use_pipeline is True

    def test_agent_stats_include_pipeline(self):
        """Agent stats pipeline icermeli."""
        agent = UEMChatAgent(llm=MockLLMAdapter())

        assert "pipeline_responses" in agent._stats


# ============================================================================
# Pipeline Mode Control Tests
# ============================================================================

class TestPipelineModeControl:
    """Pipeline mod kontrol testleri."""

    @pytest.fixture
    def agent(self):
        """Agent fixture."""
        return UEMChatAgent(llm=MockLLMAdapter())

    def test_get_pipeline_mode_default(self, agent):
        """Varsayilan pipeline modu."""
        assert agent.get_pipeline_mode() is False

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_set_pipeline_mode_on(self, agent):
        """Pipeline modu ac."""
        result = agent.set_pipeline_mode(True)

        assert result is True
        assert agent.get_pipeline_mode() is True
        assert agent._pipeline is not None

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_set_pipeline_mode_off(self):
        """Pipeline modu kapat."""
        config = ChatConfig(use_pipeline=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        agent.set_pipeline_mode(False)

        assert agent.get_pipeline_mode() is False

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_toggle_pipeline_mode(self, agent):
        """Pipeline modu ac/kapat."""
        # Baslangicta kapali
        assert agent.get_pipeline_mode() is False

        # Ac
        agent.set_pipeline_mode(True)
        assert agent.get_pipeline_mode() is True

        # Kapat
        agent.set_pipeline_mode(False)
        assert agent.get_pipeline_mode() is False


# ============================================================================
# Pipeline Status Tests
# ============================================================================

class TestPipelineStatus:
    """Pipeline durum testleri."""

    @pytest.fixture
    def agent(self):
        """Agent fixture."""
        return UEMChatAgent(llm=MockLLMAdapter())

    def test_get_pipeline_status_disabled(self, agent):
        """Pipeline kapali durum."""
        status = agent.get_pipeline_status()

        assert status["enabled"] is False
        assert "available" in status
        assert status["pipeline_exists"] is False

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_get_pipeline_status_enabled(self):
        """Pipeline acik durum."""
        config = ChatConfig(use_pipeline=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        status = agent.get_pipeline_status()

        assert status["enabled"] is True
        assert status["pipeline_exists"] is True
        assert "pipeline_info" in status

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_pipeline_status_contains_info(self):
        """Pipeline durumu bilgi icermeli."""
        config = ChatConfig(use_pipeline=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        status = agent.get_pipeline_status()
        info = status.get("pipeline_info", {})

        assert "config" in info
        assert "components" in info


# ============================================================================
# Pipeline Chat Tests
# ============================================================================

@pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
class TestPipelineChat:
    """Pipeline ile chat testleri."""

    @pytest.fixture
    def agent(self):
        """Pipeline aktif agent fixture."""
        config = ChatConfig(use_pipeline=True)
        return UEMChatAgent(config=config, llm=MockLLMAdapter())

    def test_chat_with_pipeline(self, agent):
        """Pipeline ile chat."""
        response = agent.chat("Merhaba")

        assert response is not None
        assert response.content != ""
        assert response.source == "pipeline"

    def test_chat_pipeline_returns_result(self, agent):
        """Pipeline chat sonuc dondurur."""
        response = agent.chat("Merhaba")

        assert response.pipeline_result is not None

    def test_chat_pipeline_stats(self, agent):
        """Pipeline chat istatistik gunceller."""
        initial_count = agent._stats["pipeline_responses"]

        agent.chat("Merhaba")

        assert agent._stats["pipeline_responses"] == initial_count + 1

    def test_chat_pipeline_with_emotion(self, agent):
        """Pipeline chat duygu algilama."""
        response = agent.chat("Cok uzgunum")

        # Duygu algilanmali
        assert response.emotion is not None or response.pipeline_result is not None


# ============================================================================
# Pipeline Debug Info Tests
# ============================================================================

class TestPipelineDebugInfo:
    """Pipeline debug bilgi testleri."""

    @pytest.fixture
    def agent(self):
        """Agent fixture."""
        return UEMChatAgent(llm=MockLLMAdapter())

    def test_debug_info_none_before_use(self, agent):
        """Kullanim oncesi debug bilgisi yok."""
        debug = agent.get_pipeline_debug_info()

        assert debug is None

    def test_last_pipeline_result_none_before_use(self, agent):
        """Kullanim oncesi pipeline sonucu yok."""
        result = agent.get_last_pipeline_result()

        assert result is None

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_debug_info_after_chat(self):
        """Chat sonrasi debug bilgisi."""
        config = ChatConfig(use_pipeline=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        agent.chat("Merhaba")
        debug = agent.get_pipeline_debug_info()

        assert debug is not None
        assert "success" in debug
        assert "output" in debug

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_debug_info_contains_situation(self):
        """Debug bilgisi durum icermeli."""
        config = ChatConfig(use_pipeline=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        agent.chat("Merhaba")
        debug = agent.get_pipeline_debug_info()

        assert "situation" in debug

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_debug_info_contains_plan(self):
        """Debug bilgisi plan icermeli."""
        config = ChatConfig(use_pipeline=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        agent.chat("Merhaba")
        debug = agent.get_pipeline_debug_info()

        assert "message_plan" in debug


# ============================================================================
# Fallback Tests
# ============================================================================

class TestPipelineFallback:
    """Pipeline fallback testleri."""

    def test_llm_mode_by_default(self):
        """Varsayilan LLM modu."""
        agent = UEMChatAgent(llm=MockLLMAdapter())

        response = agent.chat("Merhaba")

        # LLM veya learned kaynaklı olmali
        assert response.source in ["llm", "learned"]

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_switch_from_pipeline_to_llm(self):
        """Pipeline'dan LLM'e gecis."""
        config = ChatConfig(use_pipeline=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        # Pipeline ile chat
        response1 = agent.chat("Test 1")
        assert response1.source == "pipeline"

        # LLM'e gec
        agent.set_pipeline_mode(False)

        # LLM ile chat
        response2 = agent.chat("Test 2")
        assert response2.source in ["llm", "learned"]

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_switch_from_llm_to_pipeline(self):
        """LLM'den Pipeline'a gecis."""
        agent = UEMChatAgent(llm=MockLLMAdapter())

        # LLM ile chat
        response1 = agent.chat("Test 1")
        assert response1.source in ["llm", "learned"]

        # Pipeline'a gec
        agent.set_pipeline_mode(True)

        # Pipeline ile chat
        response2 = agent.chat("Test 2")
        assert response2.source == "pipeline"


# ============================================================================
# Session Stats Tests
# ============================================================================

class TestSessionStatsPipeline:
    """Session istatistikleri pipeline testleri."""

    @pytest.mark.skipif(not PIPELINE_AVAILABLE, reason="Pipeline not available")
    def test_stats_track_pipeline_responses(self):
        """Stats pipeline cevaplari izlemeli."""
        config = ChatConfig(use_pipeline=True)
        agent = UEMChatAgent(config=config, llm=MockLLMAdapter())

        agent.chat("Test 1")
        agent.chat("Test 2")

        stats = agent.get_session_stats()
        assert stats["pipeline_responses"] == 2

    def test_stats_no_pipeline_responses_in_llm_mode(self):
        """LLM modunda pipeline cevabi yok."""
        agent = UEMChatAgent(llm=MockLLMAdapter())

        agent.chat("Test 1")
        agent.chat("Test 2")

        stats = agent.get_session_stats()
        assert stats["pipeline_responses"] == 0
