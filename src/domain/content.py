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


class ContentType(Enum):
    """Type of content received from user."""
    TEXT = "text"
    URL = "url"


@dataclass
class Content:
    """
    Core domain entity representing user-submitted content.

    Attributes:
        id: Unique identifier for the content
        content_type: Type of content (TEXT or URL)
        raw_content: Original content from user
        source_url: URL if content_type is URL, None otherwise
        title: AI-generated title
        summary: AI-generated summary
        tags: AI-generated tags for categorization
        created_at: Timestamp when content was created
    """
    content_type: ContentType
    raw_content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_url: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def is_url(self) -> bool:
        """Check if content is a URL type."""
        return self.content_type == ContentType.URL

    def is_text(self) -> bool:
        """Check if content is a TEXT type."""
        return self.content_type == ContentType.TEXT

    def has_summary(self) -> bool:
        """Check if content has been summarized."""
        return self.summary is not None


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
