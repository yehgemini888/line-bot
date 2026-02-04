"""
Infrastructure Layer: Whisper Service

Speech-to-text transcription using OpenAI Whisper API.
"""

import io
from dataclasses import dataclass
from typing import Optional
from openai import AsyncOpenAI


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription."""
    success: bool
    text: Optional[str] = None
    duration_seconds: Optional[float] = None
    language: Optional[str] = None
    error_message: Optional[str] = None


class WhisperService:
    """
    Transcribes audio to text using OpenAI Whisper API.
    
    Supported formats: mp3, mp4, m4a, ogg, wav, webm
    Cost: $0.006 per minute
    """

    def __init__(self, api_key: str):
        """
        Initialize the Whisper service.

        Args:
            api_key: OpenAI API key
        """
        self.client = AsyncOpenAI(api_key=api_key)

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.m4a"
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: Raw audio data
            filename: Filename with extension (helps API detect format)

        Returns:
            TranscriptionResult with transcribed text
        """
        try:
            print(f"🎙️ [Whisper] Transcribing {len(audio_bytes)} bytes...")

            # Create file-like object from bytes
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            # Call Whisper API
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="zh",  # Hint for Chinese, will auto-detect if not specified
                response_format="verbose_json"  # Get additional metadata
            )

            text = response.text.strip()
            duration = getattr(response, 'duration', None)
            language = getattr(response, 'language', 'zh')

            print(f"✅ [Whisper] Transcribed: {text[:50]}...")
            print(f"   Duration: {duration}s, Language: {language}")

            return TranscriptionResult(
                success=True,
                text=text,
                duration_seconds=duration,
                language=language
            )

        except Exception as e:
            print(f"❌ [Whisper] Transcription failed: {e}")
            return TranscriptionResult(
                success=False,
                error_message=str(e)
            )

    async def transcribe_from_url(self, url: str) -> TranscriptionResult:
        """
        Download audio from URL and transcribe.

        Args:
            url: URL to audio file

        Returns:
            TranscriptionResult with transcribed text
        """
        import httpx

        try:
            print(f"🎙️ [Whisper] Downloading audio from URL...")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                audio_bytes = response.content

            # Determine filename from URL or content-type
            filename = "audio.ogg"  # Default for Telegram
            content_type = response.headers.get("content-type", "")
            if "m4a" in content_type or "mp4" in content_type:
                filename = "audio.m4a"
            elif "mpeg" in content_type:
                filename = "audio.mp3"

            return await self.transcribe(audio_bytes, filename)

        except Exception as e:
            print(f"❌ [Whisper] Failed to download audio: {e}")
            return TranscriptionResult(
                success=False,
                error_message=f"Download failed: {str(e)}"
            )
