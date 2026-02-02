"""
Infrastructure Layer: Notion Repository

Handles saving content to Notion database.
"""

from notion_client import AsyncClient
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SaveResult:
    """Result of saving to Notion."""
    success: bool
    page_id: Optional[str] = None
    page_url: Optional[str] = None
    error_message: Optional[str] = None


class NotionRepository:
    """
    Repository for saving content to Notion database.
    """

    def __init__(self, api_key: str, database_id: str):
        """
        Initialize Notion repository.

        Args:
            api_key: Notion integration token
            database_id: Target database ID
        """
        self.client = AsyncClient(auth=api_key)
        self.database_id = database_id

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
    ) -> SaveResult:
        """
        Save content to Notion database.

        Args:
            title: Content title
            summary: AI-generated summary
            content: Original content (truncated if needed)
            content_type: "text" or "url"
            tags: List of tags
            source_url: Source URL if applicable
            created_at: Creation timestamp

        Returns:
            SaveResult with page ID and URL
        """
        try:
            # Truncate content if too long (Notion has limits)
            max_content_length = 2000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "...(truncated)"

            # Build properties
            properties = {
                "Title": {
                    "title": [{"text": {"content": title}}]
                },
                "Summary": {
                    "rich_text": [{"text": {"content": summary}}]
                },
                "Content": {
                    "rich_text": [{"text": {"content": content}}]
                },
                "Type": {
                    "select": {"name": content_type}
                },
                "Tags": {
                    "multi_select": [{"name": tag} for tag in tags[:5]]  # Limit to 5 tags
                },
                "Created": {
                    "date": {"start": (created_at or datetime.now()).isoformat()}
                }
            }

            # Add source URL if provided
            if source_url:
                properties["Source URL"] = {
                    "url": source_url
                }

            # Add social media metadata if provided
            if author:
                properties["Author"] = {
                    "rich_text": [{"text": {"content": author}}]
                }
            if likes is not None:
                properties["Likes"] = {
                    "number": likes
                }
            if comments is not None:
                properties["Comments"] = {
                    "number": comments
                }

            # Create page in database
            response = await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )

            return SaveResult(
                success=True,
                page_id=response["id"],
                page_url=response.get("url")
            )

        except Exception as e:
            return SaveResult(
                success=False,
                error_message=str(e)
            )

    async def verify_database(self) -> bool:
        """
        Verify that the database exists and is accessible.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            await self.client.databases.retrieve(database_id=self.database_id)
            return True
        except Exception:
            return False
