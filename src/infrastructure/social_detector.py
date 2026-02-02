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

    # Facebook URL patterns (removed ^ anchor for search capability)
    # Matches: facebook.com/*, fb.watch/*
    FACEBOOK_PATTERN = re.compile(
        r'https?://(www\.)?(facebook\.com|fb\.watch)/\S+',
        re.IGNORECASE
    )

    # Threads URL pattern - more permissive to handle various formats
    # Matches: threads.net/@user, threads.com/@user/post/xxx
    THREADS_PATTERN = re.compile(
        r'https?://(www\.)?threads\.(net|com)/@[\w.]+(/post/[^\s?]+)?',
        re.IGNORECASE
    )

    def detect(self, text: str) -> SocialDetectionResult:
        """
        Detect if the given text contains a social media URL.

        Args:
            text: The text to check (can contain URL anywhere)

        Returns:
            SocialDetectionResult with platform info and extracted URL if detected
        """
        text = text.strip()

        # Check Facebook (search anywhere in text)
        fb_match = self.FACEBOOK_PATTERN.search(text)
        if fb_match:
            return SocialDetectionResult(
                is_social=True,
                platform=SocialPlatform.FACEBOOK,
                url=fb_match.group(0)
            )

        # Check Threads (search anywhere in text)
        threads_match = self.THREADS_PATTERN.search(text)
        if threads_match:
            return SocialDetectionResult(
                is_social=True,
                platform=SocialPlatform.THREADS,
                url=threads_match.group(0)
            )

        return SocialDetectionResult(is_social=False)

    def is_social_url(self, text: str) -> bool:
        """Quick check if text is a social media URL."""
        return self.detect(text).is_social
