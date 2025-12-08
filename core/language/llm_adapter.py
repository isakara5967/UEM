"""
core/language/llm_adapter.py

LLM Adapter - Degistirilebilir LLM backend wrapper.
UEM v2 - Provider-agnostic LLM entegrasyonu.

Ozellikler:
- Multiple provider destegi (Anthropic, OpenAI, Ollama)
- Mock adapter (test icin)
- Async destek
- Usage tracking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from abc import ABC, abstractmethod
import os
import time
import logging

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Desteklenen LLM provider'lar."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """LLM yapilandirmasi."""

    provider: LLMProvider = LLMProvider.MOCK
    model: str = "claude-sonnet-4-20250514"
    api_key: Optional[str] = None           # Environment'tan alinabilir
    base_url: Optional[str] = None          # Ollama icin
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30

    def __post_init__(self):
        """Initialize with environment variables if not set."""
        if self.api_key is None:
            if self.provider == LLMProvider.ANTHROPIC:
                self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            elif self.provider == LLMProvider.OPENAI:
                self.api_key = os.environ.get("OPENAI_API_KEY")


@dataclass
class LLMResponse:
    """LLM yanit yapisi."""

    content: str
    model: str
    provider: LLMProvider
    usage: Optional[Dict[str, int]] = None      # {"input_tokens": N, "output_tokens": M}
    latency_ms: Optional[float] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None


class LLMAdapter(ABC):
    """
    LLM Adapter base class.

    Degistirilebilir backend ile LLM entegrasyonu.
    Subclass'lar spesifik provider'lari implement eder.

    Kullanim:
        adapter = MockLLMAdapter()
        response = adapter.generate("Merhaba!")
        print(response.content)
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM Adapter.

        Args:
            config: LLM yapilandirmasi
        """
        self.config = config or LLMConfig()

        # Stats
        self._stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_latency_ms": 0,
            "errors": 0,
        }

        logger.info(
            f"LLMAdapter initialized (provider={self.config.provider.value}, "
            f"model={self.config.model})"
        )

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate response from LLM.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            LLMResponse with generated content
        """
        pass

    async def generate_async(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate response asynchronously.

        Default implementation calls sync version.
        Override for true async support.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            LLMResponse with generated content
        """
        return self.generate(prompt, system)

    def is_available(self) -> bool:
        """
        Check if LLM is available.

        Returns:
            True if ready to use
        """
        return True

    def get_provider(self) -> LLMProvider:
        """
        Get current provider.

        Returns:
            LLMProvider enum value
        """
        return self.config.provider

    @property
    def stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            **self._stats,
            "provider": self.config.provider.value,
            "model": self.config.model,
        }


class MockLLMAdapter(LLMAdapter):
    """
    Mock LLM Adapter - Test icin.

    Gercek API cagrisi yapmaz, onceden tanimli yanitlar dondurur.

    Kullanim:
        adapter = MockLLMAdapter(responses=["Yanit 1", "Yanit 2"])
        response = adapter.generate("Test prompt")
        assert response.content == "Yanit 1"
    """

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        config: Optional[LLMConfig] = None,
    ):
        """
        Initialize Mock LLM Adapter.

        Args:
            responses: List of responses to return (cycles through)
            config: Optional config (defaults to MOCK provider)
        """
        # Force MOCK provider
        if config is None:
            config = LLMConfig(provider=LLMProvider.MOCK, model="mock-model")
        else:
            config.provider = LLMProvider.MOCK

        super().__init__(config)

        self.responses = responses or ["Bu bir test yanitdir."]
        self._call_count = 0
        self._prompts: List[str] = []
        self._system_prompts: List[Optional[str]] = []

        logger.info(f"MockLLMAdapter initialized with {len(self.responses)} responses")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate mock response.

        Args:
            prompt: User prompt (stored for inspection)
            system: Optional system prompt (stored for inspection)

        Returns:
            LLMResponse with mock content
        """
        start_time = time.perf_counter()

        # Store prompt for inspection
        self._prompts.append(prompt)
        self._system_prompts.append(system)

        # Get response (cycle through list)
        response_content = self.responses[self._call_count % len(self.responses)]
        self._call_count += 1

        # Calculate mock latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Mock token counts
        input_tokens = len(prompt.split()) + (len(system.split()) if system else 0)
        output_tokens = len(response_content.split())

        # Update stats
        self._stats["total_calls"] += 1
        self._stats["total_tokens"] += input_tokens + output_tokens
        self._stats["total_latency_ms"] += latency_ms

        return LLMResponse(
            content=response_content,
            model=self.config.model,
            provider=LLMProvider.MOCK,
            usage={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            latency_ms=latency_ms,
            finish_reason="stop",
        )

    async def generate_async(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate mock response asynchronously.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            LLMResponse with mock content
        """
        # Mock async - just call sync version
        return self.generate(prompt, system)

    def is_available(self) -> bool:
        """Mock is always available."""
        return True

    def get_call_count(self) -> int:
        """
        Get number of generate() calls.

        Returns:
            Call count
        """
        return self._call_count

    def get_last_prompt(self) -> Optional[str]:
        """
        Get last prompt sent.

        Returns:
            Last prompt or None if no calls
        """
        if self._prompts:
            return self._prompts[-1]
        return None

    def get_last_system_prompt(self) -> Optional[str]:
        """
        Get last system prompt sent.

        Returns:
            Last system prompt or None
        """
        if self._system_prompts:
            return self._system_prompts[-1]
        return None

    def get_all_prompts(self) -> List[str]:
        """
        Get all prompts sent.

        Returns:
            List of all prompts
        """
        return list(self._prompts)

    def get_all_system_prompts(self) -> List[Optional[str]]:
        """
        Get all system prompts sent.

        Returns:
            List of all system prompts
        """
        return list(self._system_prompts)

    def reset(self) -> None:
        """Reset mock state."""
        self._call_count = 0
        self._prompts.clear()
        self._system_prompts.clear()
        self._stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_latency_ms": 0,
            "errors": 0,
        }
        logger.debug("MockLLMAdapter reset")

    def set_responses(self, responses: List[str]) -> None:
        """
        Set new responses.

        Args:
            responses: New list of responses
        """
        self.responses = responses
        logger.debug(f"MockLLMAdapter responses updated: {len(responses)} responses")


class AnthropicAdapter(LLMAdapter):
    """
    Anthropic Claude Adapter.

    NOT: Bu sinif sadece interface tanimlar.
    Gercek implementation icin anthropic paketi gerekli.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize Anthropic Adapter.

        Args:
            config: LLM config (provider should be ANTHROPIC)
        """
        if config is None:
            config = LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model="claude-sonnet-4-20250514",
            )

        super().__init__(config)

        self._client = None
        self._available = False

        # Try to initialize client
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic

            if self.config.api_key:
                self._client = Anthropic(api_key=self.config.api_key)
                self._available = True
                logger.info("Anthropic client initialized")
            else:
                logger.warning("ANTHROPIC_API_KEY not set")

        except ImportError:
            logger.warning("anthropic package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate response using Anthropic API.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            LLMResponse with generated content
        """
        if not self._available or not self._client:
            raise RuntimeError("Anthropic client not available")

        start_time = time.perf_counter()

        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Call API
            response = self._client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=system or "",
                messages=messages,
                temperature=self.config.temperature,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Update stats
            self._stats["total_calls"] += 1
            if response.usage:
                self._stats["total_tokens"] += (
                    response.usage.input_tokens + response.usage.output_tokens
                )
            self._stats["total_latency_ms"] += latency_ms

            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                provider=LLMProvider.ANTHROPIC,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                } if response.usage else None,
                latency_ms=latency_ms,
                finish_reason=response.stop_reason,
                raw_response=response,
            )

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Anthropic API error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return self._available


class OpenAIAdapter(LLMAdapter):
    """
    OpenAI Adapter.

    NOT: Bu sinif sadece interface tanimlar.
    Gercek implementation icin openai paketi gerekli.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize OpenAI Adapter.

        Args:
            config: LLM config (provider should be OPENAI)
        """
        if config is None:
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4",
            )

        super().__init__(config)

        self._client = None
        self._available = False

        # Try to initialize client
        self._init_client()

    def _init_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI

            if self.config.api_key:
                self._client = OpenAI(api_key=self.config.api_key)
                self._available = True
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OPENAI_API_KEY not set")

        except ImportError:
            logger.warning("openai package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate response using OpenAI API.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            LLMResponse with generated content
        """
        if not self._available or not self._client:
            raise RuntimeError("OpenAI client not available")

        start_time = time.perf_counter()

        try:
            # Build messages
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Call API
            response = self._client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=messages,
                temperature=self.config.temperature,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Update stats
            self._stats["total_calls"] += 1
            if response.usage:
                self._stats["total_tokens"] += response.usage.total_tokens
            self._stats["total_latency_ms"] += latency_ms

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                provider=LLMProvider.OPENAI,
                usage={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                } if response.usage else None,
                latency_ms=latency_ms,
                finish_reason=response.choices[0].finish_reason,
                raw_response=response,
            )

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"OpenAI API error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return self._available


# ========================================================================
# FACTORY FUNCTIONS
# ========================================================================

def create_adapter(config: Optional[LLMConfig] = None) -> LLMAdapter:
    """
    Create LLM adapter based on config.

    Args:
        config: LLM config

    Returns:
        Appropriate LLMAdapter instance
    """
    if config is None:
        config = LLMConfig()

    if config.provider == LLMProvider.MOCK:
        return MockLLMAdapter(config=config)
    elif config.provider == LLMProvider.ANTHROPIC:
        return AnthropicAdapter(config=config)
    elif config.provider == LLMProvider.OPENAI:
        return OpenAIAdapter(config=config)
    else:
        logger.warning(f"Unknown provider {config.provider}, using MockLLMAdapter")
        return MockLLMAdapter(config=config)


_llm_adapter: Optional[LLMAdapter] = None


def get_llm_adapter(config: Optional[LLMConfig] = None) -> LLMAdapter:
    """Get LLM adapter singleton."""
    global _llm_adapter

    if _llm_adapter is None:
        _llm_adapter = create_adapter(config)

    return _llm_adapter


def reset_llm_adapter() -> None:
    """Reset LLM adapter singleton (test icin)."""
    global _llm_adapter
    _llm_adapter = None
