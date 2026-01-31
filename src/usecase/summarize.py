"""
UseCase Layer: Summarize Content

Orchestrates web scraping and AI summarization.
"""

from dataclasses import dataclass
from typing import Protocol, Optional, List

from src.domain.content import Content, ContentType, create_text_content, create_url_content


# Define interfaces (ports) for dependency injection
class AIService(Protocol):
    """Interface for AI summarization service."""

    async def summarize(self, content: str, content_type: str) -> "AISummaryResult":
        ...


class WebScraperService(Protocol):
    """Interface for web scraping service."""

    async def scrape(self, url: str) -> "ScrapeResult":
        ...


@dataclass
class AISummaryResult:
    """Expected result from AI service."""
    title: str
    summary: str
    tags: List[str]
    success: bool
    error_message: Optional[str] = None


@dataclass
class ScrapeResult:
    """Expected result from web scraper."""
    url: str
    title: Optional[str]
    text_content: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class SummarizeResult:
    """Result of the summarize use case."""
    content: Content
    success: bool
    error_message: Optional[str] = None


class SummarizeUseCase:
    """
    Use case for summarizing content.

    Takes raw input (text or URL), processes it, and returns
    a Content entity with AI-generated summary and tags.
    """

    def __init__(self, ai_service: AIService, web_scraper: WebScraperService):
        """
        Initialize the use case.

        Args:
            ai_service: AI service for summarization (Gemini)
            web_scraper: Web scraper for URL content extraction
        """
        self.ai_service = ai_service
        self.web_scraper = web_scraper

    async def execute(self, raw_input: str, input_type: ContentType) -> SummarizeResult:
        """
        Execute the summarize use case.

        Args:
            raw_input: The raw text or URL from user
            input_type: ContentType.TEXT or ContentType.URL

        Returns:
            SummarizeResult containing the processed Content entity
        """
        # Step 1: Create content entity based on type
        if input_type == ContentType.URL:
            content = create_url_content(raw_input)
            # Scrape the URL content
            scrape_result = await self.web_scraper.scrape(raw_input)

            if not scrape_result.success:
                return SummarizeResult(
                    content=content,
                    success=False,
                    error_message=f"無法抓取網頁內容: {scrape_result.error_message}"
                )

            # Use scraped content for summarization
            text_to_summarize = scrape_result.text_content
            if scrape_result.title:
                content.title = scrape_result.title

        else:
            content = create_text_content(raw_input)
            text_to_summarize = raw_input

        # Step 2: Summarize with AI
        if not text_to_summarize.strip():
            return SummarizeResult(
                content=content,
                success=False,
                error_message="內容為空，無法進行摘要"
            )

        summary_result = await self.ai_service.summarize(
            content=text_to_summarize,
            content_type=input_type.value
        )

        if not summary_result.success:
            return SummarizeResult(
                content=content,
                success=False,
                error_message=f"AI 摘要失敗: {summary_result.error_message}"
            )

        # Step 3: Update content entity with AI results
        content.title = summary_result.title
        content.summary = summary_result.summary
        content.tags = summary_result.tags

        return SummarizeResult(
            content=content,
            success=True
        )
