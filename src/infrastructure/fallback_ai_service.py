"""
Infrastructure Layer: Fallback AI Service

Wraps Gemini (primary) and OpenAI (fallback).
Tries Gemini first; if it raises an exception or returns success=False,
automatically retries with OpenAI.

Includes Circuit Breaker: when Gemini fails (429/5xx), skip it for a cooldown
period to avoid redundant failed calls within the same request cycle.
"""

import time

from src.infrastructure.gemini_service import GeminiService, SummaryResult, ImageAnalysisResult
from src.infrastructure.openai_service import OpenAIService

# Circuit breaker cooldown in seconds
CIRCUIT_BREAKER_COOLDOWN = 60


class FallbackAIService:
    """
    AI service that tries Gemini first, falls back to OpenAI on failure.
    Exposes the same summarize() and analyze_image() interface.

    Circuit Breaker: After Gemini fails, subsequent calls skip Gemini
    for CIRCUIT_BREAKER_COOLDOWN seconds to avoid redundant failures.
    """

    def __init__(self, gemini_api_key: str, openai_api_key: str):
        self.primary = GeminiService(api_key=gemini_api_key)
        self.fallback = OpenAIService(api_key=openai_api_key)
        self._circuit_open_until = 0.0

    def _is_circuit_open(self) -> bool:
        """Check if Gemini circuit breaker is active."""
        return time.time() < self._circuit_open_until

    def _trip_circuit(self):
        """Trip the circuit breaker after Gemini failure."""
        self._circuit_open_until = time.time() + CIRCUIT_BREAKER_COOLDOWN
        print(f"⚡ [CircuitBreaker] Gemini 暫停 {CIRCUIT_BREAKER_COOLDOWN} 秒，直接使用 OpenAI")

    async def summarize(
        self,
        content: str,
        content_type: str = "text",
        custom_prompt: str = None
    ) -> SummaryResult:
        """
        Summarize content. Tries Gemini first, falls back to OpenAI.
        """
        if self._is_circuit_open():
            print(f"⚡ [CircuitBreaker] Gemini 熔斷中，直接使用 OpenAI summarize")
            return await self.fallback.summarize(content, content_type, custom_prompt)

        try:
            result = await self.primary.summarize(content, content_type, custom_prompt)
            if result.success:
                return result
            print(f"⚠️ [Fallback] Gemini returned failure: {result.error_message}, switching to OpenAI")
            self._trip_circuit()
        except Exception as e:
            print(f"⚠️ [Fallback] Gemini raised exception: {e}, switching to OpenAI")
            self._trip_circuit()

        return await self.fallback.summarize(content, content_type, custom_prompt)

    async def generate_simple(self, prompt: str) -> str:
        """
        Generate a simple text response. Tries Gemini first, falls back to OpenAI.
        """
        if self._is_circuit_open():
            print(f"⚡ [CircuitBreaker] Gemini 熔斷中，直接使用 OpenAI generate_simple")
            return await self.fallback.generate_simple(prompt)

        try:
            result = await self.primary.generate_simple(prompt)
            if result:
                return result
            print(f"⚠️ [Fallback] Gemini generate_simple empty, switching to OpenAI")
            self._trip_circuit()
        except Exception as e:
            print(f"⚠️ [Fallback] Gemini generate_simple exception: {e}, switching to OpenAI")
            self._trip_circuit()

        return await self.fallback.generate_simple(prompt)

    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        prompt: str = None
    ) -> ImageAnalysisResult:
        """
        Analyze an image. Tries Gemini first, falls back to OpenAI.
        """
        if self._is_circuit_open():
            print(f"⚡ [CircuitBreaker] Gemini 熔斷中，直接使用 OpenAI analyze_image")
            return await self.fallback.analyze_image(image_data, mime_type, prompt)

        try:
            result = await self.primary.analyze_image(image_data, mime_type, prompt)
            if result.success:
                return result
            print(f"⚠️ [Fallback] Gemini Vision returned failure: {result.error_message}, switching to OpenAI")
            self._trip_circuit()
        except Exception as e:
            print(f"⚠️ [Fallback] Gemini Vision raised exception: {e}, switching to OpenAI")
            self._trip_circuit()

        return await self.fallback.analyze_image(image_data, mime_type, prompt)

    async def summarize_with_schema(
        self,
        content: str,
        prompt: str,
        schema: dict
    ) -> dict:
        """
        使用 Schema 進行摘要。優先使用 Gemini，失敗時回退到 OpenAI。
        """
        if self._is_circuit_open():
            print(f"⚡ [CircuitBreaker] Gemini 熔斷中，直接使用 OpenAI summarize_with_schema")
            return await self.fallback.summarize_with_schema(content, prompt, schema)

        try:
            result = await self.primary.summarize_with_schema(content, prompt, schema)
            return result
        except Exception as e:
            print(f"⚠️ [Fallback] Gemini Structured Output 失敗: {e}, 切換到 OpenAI")
            self._trip_circuit()

        return await self.fallback.summarize_with_schema(content, prompt, schema)
