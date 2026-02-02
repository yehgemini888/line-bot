"""
Infrastructure Layer: Social Media URL Detector

Detects and identifies social media platform URLs (Facebook, Threads).
"""

import re
from typing import Optional
from dataclasses import dataclass

from src.domain.content import SocialPlatform


@dataclass
class SocialDetectionResult:
    """Result of social media URL detection."""
    is_social: bool
    platform: Optional[SocialPlatform] = None
    url: Optional[str] = None


class SocialDetector:
    """
    Detects social media URLs and identifies the platform.
    
    Supports:
    - Facebook (posts, videos, pages)
    - Threads (posts)
    """

    # Facebook URL patterns
    # Matches: facebook.com/*, fb.watch/*
    FACEBOOK_PATTERN = re.compile(
        r'^https?://(www\.)?(facebook\.com|fb\.watch)/.+',
        re.IGNORECASE
    )

    THREADS_PATTERN = re.compile(
        r'^https?://(www\.)?threads\.(net|com)/@[\w.]+(/post/[\w-]+)?',
        re.IGNORECASE
    )

    def detect(self, text: str) -> SocialDetectionResult:
        """
        Detect if the given text is a social media URL.

        Args:
            text: The text to check (should be a URL)

        Returns:
            SocialDetectionResult with platform info if detected
        """
        text = text.strip()

        # Check Facebook
        if self.FACEBOOK_PATTERN.match(text):
            return SocialDetectionResult(
                is_social=True,
                platform=SocialPlatform.FACEBOOK,
                url=text
            )

        # Check Threads
        if self.THREADS_PATTERN.match(text):
            return SocialDetectionResult(
                is_social=True,
                platform=SocialPlatform.THREADS,
                url=text
            )

        return SocialDetectionResult(is_social=False)

    def is_social_url(self, text: str) -> bool:
        """Quick check if text is a social media URL."""
        return self.detect(text).is_social
