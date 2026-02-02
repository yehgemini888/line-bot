"""
UseCase Layer: Save to Notion

Orchestrates saving content to Notion database.
"""

from dataclasses import dataclass
from typing import Protocol, Optional, List
from datetime import datetime

from src.domain.content import Content


# Define interface (port) for dependency injection
class ContentRepository(Protocol):
    """Interface for content persistence."""

    async def save(
        self,
        title: str,
        summary: str,
        content: str,
        content_type: str,
        tags: List[str],
        source_url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        author: Optional[str] = None,
        likes: Optional[int] = None,
        comments: Optional[int] = None
    ) -> "RepositorySaveResult":
        ...


@dataclass
class RepositorySaveResult:
    """Expected result from repository."""
    success: bool
    page_id: Optional[str] = None
    page_url: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SaveResult:
    """Result of the save use case."""
    success: bool
    page_url: Optional[str] = None
    error_message: Optional[str] = None


class SaveToNotionUseCase:
    """
    Use case for saving content to Notion.

    Takes a Content entity and persists it to Notion database.
    """

    def __init__(self, repository: ContentRepository):
        """
        Initialize the use case.

        Args:
            repository: Content repository (Notion)
        """
        self.repository = repository

    async def execute(self, content: Content) -> SaveResult:
        """
        Execute the save use case.

        Args:
            content: The Content entity to save

        Returns:
            SaveResult with page URL if successful
        """
        # Validate content has required fields
        if not content.title:
            return SaveResult(
                success=False,
                error_message="Content must have a title before saving"
            )

        if not content.summary:
            return SaveResult(
                success=False,
                error_message="Content must have a summary before saving"
            )

        # Save to repository
        result = await self.repository.save(
            title=content.title,
            summary=content.summary,
            content=content.raw_content,
            content_type=content.content_type.value,
            tags=content.tags,
            source_url=content.source_url,
            created_at=content.created_at,
            author=content.author,
            likes=content.likes,
            comments=content.comments
        )

        if not result.success:
            return SaveResult(
                success=False,
                error_message=f"儲存至 Notion 失敗: {result.error_message}"
            )

        return SaveResult(
            success=True,
            page_url=result.page_url
        )
