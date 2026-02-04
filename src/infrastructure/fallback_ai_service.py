"""
Infrastructure Layer: Fallback AI Service

Wraps Gemini (primary) and OpenAI (fallback).
Tries Gemini first; if it raises an exception or returns success=False,
automatically retries with OpenAI.
"""

from src.infrastructure.gemini_service import GeminiService, SummaryResult, ImageAnalysisResult
from src.infrastructure.openai_service import OpenAIService


class FallbackAIService:
    """
    AI service that tries Gemini first, falls back to OpenAI on failure.
    Exposes the same summarize() and analyze_image() interface.
    """

    def __init__(self, gemini_api_key: str, openai_api_key: str):
        self.primary = GeminiService(api_key=gemini_api_key)
        self.fallback = OpenAIService(api_key=openai_api_key)

    async def summarize(
        self, 
        content: str, 
        content_type: str = "text",
        custom_prompt: str = None
    ) -> SummaryResult:
        """
        Summarize content. Tries Gemini first, falls back to OpenAI.
        """
        try:
            result = await self.primary.summarize(content, content_type, custom_prompt)
            if result.success:
                return result
            print(f"⚠️ [Fallback] Gemini returned failure: {result.error_message}, switching to OpenAI")
        except Exception as e:
            print(f"⚠️ [Fallback] Gemini raised exception: {e}, switching to OpenAI")

        return await self.fallback.summarize(content, content_type, custom_prompt)

    async def generate_simple(self, prompt: str) -> str:
        """
        Generate a simple text response. Tries Gemini first, falls back to OpenAI.
        """
        try:
            result = await self.primary.generate_simple(prompt)
            if result:
                return result
            print(f"⚠️ [Fallback] Gemini generate_simple empty, switching to OpenAI")
        except Exception as e:
            print(f"⚠️ [Fallback] Gemini generate_simple exception: {e}, switching to OpenAI")

        return await self.fallback.generate_simple(prompt)

    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg"
    ) -> ImageAnalysisResult:
        """
        Analyze an image. Tries Gemini first, falls back to OpenAI.
        """
        try:
            result = await self.primary.analyze_image(image_data, mime_type)
            if result.success:
                return result
            print(f"⚠️ [Fallback] Gemini Vision returned failure: {result.error_message}, switching to OpenAI")
        except Exception as e:
            print(f"⚠️ [Fallback] Gemini Vision raised exception: {e}, switching to OpenAI")

        return await self.fallback.analyze_image(image_data, mime_type)

