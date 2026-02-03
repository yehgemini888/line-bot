"""
Domain Layer: Content Entity

This module contains the core domain model for content.
No external dependencies allowed in this layer.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid


class SocialPlatform(Enum):
    """Supported social media platforms."""
    FACEBOOK = "facebook"
    THREADS = "threads"


class ContentType(Enum):
    """Type of content received from user."""
    TEXT = "text"
    URL = "url"
    SOCIAL = "social"
    IMAGE = "image"
    YOUTUBE = "youtube"


@dataclass
class Content:
    """
    Core domain entity representing user-submitted content.

    Attributes:
        id: Unique identifier for the content
        content_type: Type of content (TEXT, URL, or SOCIAL)
        raw_content: Original content from user
        source_url: URL if content_type is URL or SOCIAL, None otherwise
        social_platform: Platform if content_type is SOCIAL, None otherwise
        title: AI-generated title
        summary: AI-generated summary
        tags: AI-generated tags for categorization
        created_at: Timestamp when content was created
        author: Author name (for social media posts)
        likes: Like count (for social media posts)
        comments: Comment count (for social media posts)
        shares: Share count (for social media posts)
    """
    content_type: ContentType
    raw_content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_url: Optional[str] = None
    social_platform: Optional[SocialPlatform] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    author: Optional[str] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    image_url: Optional[str] = None
    image_description: Optional[str] = None
    video_duration: Optional[str] = None  # For YouTube videos (e.g., "10:30")
    channel_name: Optional[str] = None    # For YouTube videos

    def is_url(self) -> bool:
        """Check if content is a URL type."""
        return self.content_type == ContentType.URL

    def is_text(self) -> bool:
        """Check if content is a TEXT type."""
        return self.content_type == ContentType.TEXT

    def has_summary(self) -> bool:
        """Check if content has been summarized."""
        return self.summary is not None

    def is_image(self) -> bool:
        """Check if content is an IMAGE type."""
        return self.content_type == ContentType.IMAGE

    def is_youtube(self) -> bool:
        """Check if content is a YOUTUBE type."""
        return self.content_type == ContentType.YOUTUBE


def create_text_content(text: str) -> Content:
    """Factory function to create a TEXT type content."""
    return Content(
        content_type=ContentType.TEXT,
        raw_content=text
    )


def create_url_content(url: str) -> Content:
    """Factory function to create a URL type content."""
    return Content(
        content_type=ContentType.URL,
        raw_content=url,
        source_url=url
    )


def create_social_content(url: str, platform: SocialPlatform) -> Content:
    """Factory function to create a SOCIAL type content."""
    return Content(
        content_type=ContentType.SOCIAL,
        raw_content=url,
        source_url=url,
        social_platform=platform
    )


def create_image_content(
    image_url: str,
    image_description: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Content:
    """
    Factory function to create an IMAGE type content.

    Args:
        image_url: URL of the uploaded image (e.g., Google Drive link)
        image_description: AI-generated description of the image
        title: AI-generated title for the image
        tags: AI-generated tags

    Returns:
        Content entity with IMAGE type
    """
    return Content(
        content_type=ContentType.IMAGE,
        raw_content="[Image]",
        image_url=image_url,
        image_description=image_description,
        title=title,
        summary=image_description,
        tags=tags or []
    )


def create_youtube_content(
    url: str,
    title: Optional[str] = None,
    channel_name: Optional[str] = None,
    video_duration: Optional[str] = None
) -> Content:
    """
    Factory function to create a YOUTUBE type content.

    Args:
        url: YouTube video URL
        title: Video title
        channel_name: YouTube channel name
        video_duration: Video duration (e.g., "10:30")

    Returns:
        Content entity with YOUTUBE type
    """
    return Content(
        content_type=ContentType.YOUTUBE,
        raw_content=url,
        source_url=url,
        title=title,
        author=channel_name,
        channel_name=channel_name,
        video_duration=video_duration
    )
