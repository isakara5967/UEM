"""
tests/unit/test_llm_adapter.py

LLM Adapter unit testleri.
MockLLMAdapter ve config testleri.
"""

import pytest
import os
from unittest.mock import patch

from core.language.llm_adapter import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    LLMAdapter,
    MockLLMAdapter,
    create_adapter,
    get_llm_adapter,
    reset_llm_adapter,
)


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def mock_adapter():
    """Default MockLLMAdapter."""
    return MockLLMAdapter()


@pytest.fixture
def custom_responses_adapter():
    """MockLLMAdapter with custom responses."""
    return MockLLMAdapter(responses=[
        "First response",
        "Second response",
        "Third response",
    ])


# ========================================================================
# LLMPROVIDER TESTS
# ========================================================================

class TestLLMProvider:
    """LLMProvider enum testleri."""

    def test_provider_values(self):
        """Provider degerleri dogru olmali."""
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.OLLAMA.value == "ollama"
        assert LLMProvider.MOCK.value == "mock"

    def test_provider_from_string(self):
        """String'den provider olusturulabilmeli."""
        assert LLMProvider("anthropic") == LLMProvider.ANTHROPIC
        assert LLMProvider("mock") == LLMProvider.MOCK

    def test_provider_is_string(self):
        """LLMProvider str enum olmali."""
        assert isinstance(LLMProvider.MOCK, str)
        assert LLMProvider.MOCK == "mock"


# ========================================================================
# LLMCONFIG TESTS
# ========================================================================

class TestLLMConfig:
    """LLMConfig testleri."""

    def test_default_config(self):
        """Default config degerleri dogru olmali."""
        config = LLMConfig()
        assert config.provider == LLMProvider.MOCK
        assert config.model == "claude-sonnet-4-20250514"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.timeout == 30

    def test_custom_config(self):
        """Custom config degerleri set edilebilmeli."""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-opus",
            temperature=0.5,
            max_tokens=2000,
            timeout=60,
        )
        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model == "claude-3-opus"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.timeout == 60

    def test_temperature_config(self):
        """Temperature degeri set edilebilmeli."""
        config = LLMConfig(temperature=0.0)
        assert config.temperature == 0.0

        config = LLMConfig(temperature=1.0)
        assert config.temperature == 1.0

    def test_max_tokens_config(self):
        """Max tokens degeri set edilebilmeli."""
        config = LLMConfig(max_tokens=100)
        assert config.max_tokens == 100

        config = LLMConfig(max_tokens=4000)
        assert config.max_tokens == 4000

    def test_timeout_config(self):
        """Timeout degeri set edilebilmeli."""
        config = LLMConfig(timeout=10)
        assert config.timeout == 10

        config = LLMConfig(timeout=120)
        assert config.timeout == 120

    def test_api_key_config(self):
        """API key set edilebilmeli."""
        config = LLMConfig(api_key="test-key")
        assert config.api_key == "test-key"

    def test_base_url_config(self):
        """Base URL set edilebilmeli (Ollama icin)."""
        config = LLMConfig(
            provider=LLMProvider.OLLAMA,
            base_url="http://localhost:11434",
        )
        assert config.base_url == "http://localhost:11434"

    def test_config_from_env_anthropic(self):
        """Anthropic API key environment'tan alinabilmeli."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            config = LLMConfig(provider=LLMProvider.ANTHROPIC)
            assert config.api_key == "env-key"

    def test_config_from_env_openai(self):
        """OpenAI API key environment'tan alinabilmeli."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            config = LLMConfig(provider=LLMProvider.OPENAI)
            assert config.api_key == "env-key"


# ========================================================================
# LLMRESPONSE TESTS
# ========================================================================

class TestLLMResponse:
    """LLMResponse testleri."""

    def test_response_required_fields(self):
        """Zorunlu alanlar set edilmeli."""
        response = LLMResponse(
            content="Test content",
            model="test-model",
            provider=LLMProvider.MOCK,
        )
        assert response.content == "Test content"
        assert response.model == "test-model"
        assert response.provider == LLMProvider.MOCK

    def test_response_optional_fields(self):
        """Opsiyonel alanlar default olmali."""
        response = LLMResponse(
            content="Test",
            model="test",
            provider=LLMProvider.MOCK,
        )
        assert response.usage is None
        assert response.latency_ms is None
        assert response.finish_reason is None
        assert response.raw_response is None

    def test_response_with_usage(self):
        """Usage bilgisi set edilebilmeli."""
        response = LLMResponse(
            content="Test",
            model="test",
            provider=LLMProvider.MOCK,
            usage={"input_tokens": 10, "output_tokens": 20},
        )
        assert response.usage["input_tokens"] == 10
        assert response.usage["output_tokens"] == 20

    def test_response_with_latency(self):
        """Latency bilgisi set edilebilmeli."""
        response = LLMResponse(
            content="Test",
            model="test",
            provider=LLMProvider.MOCK,
            latency_ms=150.5,
        )
        assert response.latency_ms == 150.5


# ========================================================================
# MOCKLLMADAPTER TESTS
# ========================================================================

class TestMockLLMAdapterInit:
    """MockLLMAdapter initialization testleri."""

    def test_init_default(self):
        """Default init calismali."""
        adapter = MockLLMAdapter()
        assert adapter.config.provider == LLMProvider.MOCK
        assert len(adapter.responses) == 1

    def test_init_with_responses(self):
        """Responses ile init calismali."""
        adapter = MockLLMAdapter(responses=["R1", "R2"])
        assert len(adapter.responses) == 2
        assert adapter.responses[0] == "R1"

    def test_init_forces_mock_provider(self):
        """Config verilse bile provider MOCK olmali."""
        config = LLMConfig(provider=LLMProvider.ANTHROPIC)
        adapter = MockLLMAdapter(config=config)
        assert adapter.config.provider == LLMProvider.MOCK


class TestMockLLMAdapterGenerate:
    """MockLLMAdapter.generate() testleri."""

    def test_generate_returns_response(self, mock_adapter):
        """Generate LLMResponse dondurmeli."""
        response = mock_adapter.generate("Test prompt")
        assert isinstance(response, LLMResponse)
        assert response.content == "Bu bir test yanitdir."
        assert response.provider == LLMProvider.MOCK

    def test_generate_with_system_prompt(self, mock_adapter):
        """System prompt ile generate calismali."""
        response = mock_adapter.generate(
            "Test prompt",
            system="You are a helpful assistant.",
        )
        assert isinstance(response, LLMResponse)
        assert response.content == "Bu bir test yanitdir."

    def test_generate_without_system_prompt(self, mock_adapter):
        """System prompt olmadan generate calismali."""
        response = mock_adapter.generate("Test prompt")
        assert isinstance(response, LLMResponse)

    def test_mock_adapter_multiple_responses(self, custom_responses_adapter):
        """Birden fazla response cycle etmeli."""
        r1 = custom_responses_adapter.generate("P1")
        r2 = custom_responses_adapter.generate("P2")
        r3 = custom_responses_adapter.generate("P3")
        r4 = custom_responses_adapter.generate("P4")  # Cycles back

        assert r1.content == "First response"
        assert r2.content == "Second response"
        assert r3.content == "Third response"
        assert r4.content == "First response"  # Cycles

    def test_generate_has_usage(self, mock_adapter):
        """Response usage bilgisi icermeli."""
        response = mock_adapter.generate("Test prompt")
        assert response.usage is not None
        assert "input_tokens" in response.usage
        assert "output_tokens" in response.usage

    def test_generate_has_latency(self, mock_adapter):
        """Response latency bilgisi icermeli."""
        response = mock_adapter.generate("Test prompt")
        assert response.latency_ms is not None
        assert response.latency_ms >= 0


class TestMockLLMAdapterCallTracking:
    """MockLLMAdapter call tracking testleri."""

    def test_call_count(self, mock_adapter):
        """Call count dogru olmali."""
        assert mock_adapter.get_call_count() == 0

        mock_adapter.generate("P1")
        assert mock_adapter.get_call_count() == 1

        mock_adapter.generate("P2")
        assert mock_adapter.get_call_count() == 2

    def test_last_prompt(self, mock_adapter):
        """Last prompt dogru olmali."""
        assert mock_adapter.get_last_prompt() is None

        mock_adapter.generate("First")
        assert mock_adapter.get_last_prompt() == "First"

        mock_adapter.generate("Second")
        assert mock_adapter.get_last_prompt() == "Second"

    def test_last_system_prompt(self, mock_adapter):
        """Last system prompt dogru olmali."""
        assert mock_adapter.get_last_system_prompt() is None

        mock_adapter.generate("P1", system="System 1")
        assert mock_adapter.get_last_system_prompt() == "System 1"

        mock_adapter.generate("P2", system=None)
        assert mock_adapter.get_last_system_prompt() is None

    def test_all_prompts(self, mock_adapter):
        """All prompts dogru olmali."""
        mock_adapter.generate("P1")
        mock_adapter.generate("P2")
        mock_adapter.generate("P3")

        prompts = mock_adapter.get_all_prompts()
        assert prompts == ["P1", "P2", "P3"]


class TestMockLLMAdapterReset:
    """MockLLMAdapter.reset() testleri."""

    def test_reset_clears_call_count(self, mock_adapter):
        """Reset call count'u sifirlamali."""
        mock_adapter.generate("P1")
        mock_adapter.generate("P2")
        assert mock_adapter.get_call_count() == 2

        mock_adapter.reset()
        assert mock_adapter.get_call_count() == 0

    def test_reset_clears_prompts(self, mock_adapter):
        """Reset prompts'lari temizlemeli."""
        mock_adapter.generate("P1")
        assert len(mock_adapter.get_all_prompts()) == 1

        mock_adapter.reset()
        assert len(mock_adapter.get_all_prompts()) == 0

    def test_reset_clears_stats(self, mock_adapter):
        """Reset stats'i temizlemeli."""
        mock_adapter.generate("P1")
        assert mock_adapter.stats["total_calls"] == 1

        mock_adapter.reset()
        assert mock_adapter.stats["total_calls"] == 0


class TestMockLLMAdapterSetResponses:
    """MockLLMAdapter.set_responses() testleri."""

    def test_set_responses(self, mock_adapter):
        """Responses guncellenebilmeli."""
        mock_adapter.set_responses(["New response"])
        response = mock_adapter.generate("P1")
        assert response.content == "New response"


class TestMockLLMAdapterIsAvailable:
    """MockLLMAdapter.is_available() testleri."""

    def test_is_available_mock(self, mock_adapter):
        """Mock her zaman available olmali."""
        assert mock_adapter.is_available() is True

    def test_get_provider(self, mock_adapter):
        """Provider MOCK olmali."""
        assert mock_adapter.get_provider() == LLMProvider.MOCK


# ========================================================================
# CONTENT TESTS
# ========================================================================

class TestContentHandling:
    """Content handling testleri."""

    def test_turkish_prompt(self, mock_adapter):
        """Turkce prompt islenmeli."""
        response = mock_adapter.generate("Merhaba, nasilsin?")
        assert mock_adapter.get_last_prompt() == "Merhaba, nasilsin?"

    def test_long_prompt(self, mock_adapter):
        """Uzun prompt islenmeli."""
        long_prompt = "Bu cok uzun bir test promptudur. " * 100
        response = mock_adapter.generate(long_prompt)
        assert mock_adapter.get_last_prompt() == long_prompt

    def test_empty_prompt(self, mock_adapter):
        """Bos prompt islenmeli."""
        response = mock_adapter.generate("")
        assert mock_adapter.get_last_prompt() == ""
        assert isinstance(response, LLMResponse)

    def test_special_characters(self, mock_adapter):
        """Ozel karakterler islenmeli."""
        prompt = "Test with special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"
        response = mock_adapter.generate(prompt)
        assert mock_adapter.get_last_prompt() == prompt

    def test_multiline_prompt(self, mock_adapter):
        """Cok satirli prompt islenmeli."""
        prompt = "Line 1\nLine 2\nLine 3"
        response = mock_adapter.generate(prompt)
        assert mock_adapter.get_last_prompt() == prompt


# ========================================================================
# ASYNC TESTS
# ========================================================================

class TestAsyncGenerate:
    """Async generate testleri."""

    @pytest.mark.asyncio
    async def test_async_generate(self, mock_adapter):
        """Async generate calismali."""
        response = await mock_adapter.generate_async("Test prompt")
        assert isinstance(response, LLMResponse)
        assert response.content == "Bu bir test yanitdir."

    @pytest.mark.asyncio
    async def test_async_with_system(self, mock_adapter):
        """Async with system prompt calismali."""
        response = await mock_adapter.generate_async(
            "Test",
            system="System prompt",
        )
        assert isinstance(response, LLMResponse)


# ========================================================================
# FACTORY TESTS
# ========================================================================

class TestCreateAdapter:
    """create_adapter() testleri."""

    def test_create_mock_adapter(self):
        """Mock adapter olusturulmali."""
        config = LLMConfig(provider=LLMProvider.MOCK)
        adapter = create_adapter(config)
        assert isinstance(adapter, MockLLMAdapter)

    def test_create_default_adapter(self):
        """Default config mock olusturmali."""
        adapter = create_adapter()
        assert isinstance(adapter, MockLLMAdapter)


class TestGetLLMAdapter:
    """get_llm_adapter() testleri."""

    def test_get_llm_adapter_singleton(self):
        """Singleton dondurmeli."""
        reset_llm_adapter()

        adapter1 = get_llm_adapter()
        adapter2 = get_llm_adapter()

        assert adapter1 is adapter2

    def test_reset_llm_adapter(self):
        """Reset singleton'i temizlemeli."""
        reset_llm_adapter()

        adapter1 = get_llm_adapter()
        reset_llm_adapter()
        adapter2 = get_llm_adapter()

        assert adapter1 is not adapter2


# ========================================================================
# STATS TESTS
# ========================================================================

class TestAdapterStats:
    """Adapter stats testleri."""

    def test_stats_initial(self, mock_adapter):
        """Initial stats dogru olmali."""
        stats = mock_adapter.stats
        assert stats["total_calls"] == 0
        assert stats["total_tokens"] == 0
        assert stats["provider"] == "mock"

    def test_stats_after_calls(self, mock_adapter):
        """Calls sonrasi stats guncel olmali."""
        mock_adapter.generate("Test prompt")
        mock_adapter.generate("Another prompt")

        stats = mock_adapter.stats
        assert stats["total_calls"] == 2
        assert stats["total_tokens"] > 0
