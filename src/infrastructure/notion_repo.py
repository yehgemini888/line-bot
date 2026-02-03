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

    def _split_text(self, text: str, max_length: int = 2000) -> List[dict]:
        """Split text into chunks of max_length for Notion's rich_text property."""
        if not text:
            return []
        
        # Ensure we don't exceed 2000 chars (Notion API limit)
        return [
            {"text": {"content": text[i : i + max_length]}}
            for i in range(0, len(text), max_length)
        ]

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
        comments: Optional[int] = None,
        shares: Optional[int] = None,
        image_url: Optional[str] = None,
        image_description: Optional[str] = None
    ) -> SaveResult:
        """
        Save content to Notion database.

        Args:
            title: Content title
            summary: AI-generated summary
            content: Original content
            content_type: "text" or "url"
            tags: List of tags
            source_url: Source URL if applicable
            created_at: Creation timestamp

        Returns:
            SaveResult with page ID and URL
        """
        try:
            # Build properties
            properties = {
                "Title": {
                    "title": [{"text": {"content": title[:2000]}}] # Title also has 2000 limit
                },
                "Summary": {
                    "rich_text": self._split_text(summary)
                },
                "Content": {
                    "rich_text": self._split_text(content)
                },
                "Type": {
                    "select": {"name": content_type}
                },
                "Tags": {
                    "multi_select": [{"name": tag[:100]} for tag in tags[:10]]  # Notion tag limit (100 chars, limit count)
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
                    "rich_text": self._split_text(author)
                }
            if likes is not None:
                properties["Likes"] = {
                    "number": likes
                }
            if comments is not None:
                properties["Comments"] = {
                    "number": comments
                }
            if shares is not None:
                properties["Shares"] = {
                    "number": shares
                }

            # Add image properties if provided
            if image_url:
                properties["Image URL"] = {
                    "url": image_url
                }
            if image_description:
                properties["Image Description"] = {
                    "rich_text": self._split_text(image_description)
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
