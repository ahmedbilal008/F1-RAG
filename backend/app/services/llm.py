"""LLM provider abstraction layer."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("llm")


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""
    text: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    model: str = ""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        """Generate a response synchronously."""
        ...

    @abstractmethod
    async def agenerate(self, prompt: str) -> LLMResponse:
        """Generate a response asynchronously."""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        ...


class GeminiLLMProvider(LLMProvider):
    """Google Gemini LLM provider using the official SDK."""

    def __init__(self):
        settings = get_settings()
        import google.generativeai as genai

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self._model = genai.GenerativeModel(settings.LLM_MODEL)
        self._model_name = settings.LLM_MODEL
        self._temperature = settings.LLM_TEMPERATURE
        self._max_tokens = settings.MAX_TOKENS

        self._generation_config = genai.types.GenerationConfig(
            temperature=self._temperature,
            max_output_tokens=self._max_tokens,
        )

        logger.info(f"GeminiLLMProvider initialized (model={self._model_name})")

    def generate(self, prompt: str) -> LLMResponse:
        """Synchronous generation."""
        start = time.perf_counter()
        try:
            response = self._model.generate_content(
                prompt,
                generation_config=self._generation_config,
            )
            latency = (time.perf_counter() - start) * 1000

            text = response.text if response.text else ""

            # Estimate tokens (Gemini provides usage metadata when available)
            tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens = getattr(response.usage_metadata, "total_token_count", 0)
            if tokens == 0:
                tokens = len(prompt.split()) + len(text.split())  # rough estimate

            return LLMResponse(
                text=text.strip(),
                tokens_used=tokens,
                latency_ms=round(latency, 2),
                model=self._model_name,
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def agenerate(self, prompt: str) -> LLMResponse:
        """Async generation (uses Gemini's async API)."""
        start = time.perf_counter()
        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config=self._generation_config,
            )
            latency = (time.perf_counter() - start) * 1000

            text = response.text if response.text else ""
            tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens = getattr(response.usage_metadata, "total_token_count", 0)
            if tokens == 0:
                tokens = len(prompt.split()) + len(text.split())

            return LLMResponse(
                text=text.strip(),
                tokens_used=tokens,
                latency_ms=round(latency, 2),
                model=self._model_name,
            )
        except Exception as e:
            logger.error(f"Async LLM generation failed: {e}")
            raise

    def get_model_name(self) -> str:
        return self._model_name


_llm_instance: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Get or create the singleton LLM provider."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = GeminiLLMProvider()
    return _llm_instance
