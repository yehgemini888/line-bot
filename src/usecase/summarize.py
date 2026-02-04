"""
UseCase Layer: Summarize Content

Orchestrates web scraping, social media scraping, and AI summarization.
Includes smart prompt selection based on content category.
"""

from dataclasses import dataclass
from typing import Protocol, Optional, List

from src.domain.content import (
    Content, ContentType, SocialPlatform,
    create_text_content, create_url_content, create_social_content
)
from src.infrastructure.content_classifier import ContentClassifier
from src.infrastructure.prompt_template_manager import PromptTemplateManager


# Define interfaces (ports) for dependency injection
class AIService(Protocol):
    """Interface for AI summarization service."""

    async def summarize(self, content: str, content_type: str, custom_prompt: str = None) -> "AISummaryResult":
        ...

    async def generate_simple(self, prompt: str) -> str:
        ...


class WebScraperService(Protocol):
    """Interface for web scraping service."""

    async def scrape(self, url: str) -> "ScrapeResult":
        ...


class SocialScraperService(Protocol):
    """Interface for social media scraping service."""

    async def scrape(self, url: str, platform: SocialPlatform) -> "SocialScrapeResult":
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
class SocialScrapeResult:
    """Expected result from social scraper."""
    platform: SocialPlatform
    url: str
    author: Optional[str]
    text_content: str
    likes: Optional[int]
    comments: Optional[int]
    shares: Optional[int] = None
    success: bool = False
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
    
    Includes smart prompt selection based on content category.
    """

    def __init__(
        self,
        ai_service: AIService,
        web_scraper: WebScraperService,
        social_scraper: SocialScraperService,
        enable_smart_prompt: bool = True,
        notion_client=None,
        template_database_id: Optional[str] = None
    ):
        """
        Initialize the use case.

        Args:
            ai_service: AI service for summarization (Gemini)
            web_scraper: Web scraper for URL content extraction
            social_scraper: Social scraper for social media content
            enable_smart_prompt: Enable smart prompt selection
            notion_client: Optional Notion client for custom templates
            template_database_id: Optional Notion database ID for templates
        """
        self.ai_service = ai_service
        self.web_scraper = web_scraper
        self.social_scraper = social_scraper
        self.enable_smart_prompt = enable_smart_prompt
        
        # Initialize smart prompt components
        if enable_smart_prompt:
            self.template_manager = PromptTemplateManager(
                notion_client=notion_client,
                template_database_id=template_database_id
            )
            # Pass template_manager to classifier for dynamic categories
            self.classifier = ContentClassifier(
                ai_service=ai_service,
                template_manager=self.template_manager
            )
        else:
            self.classifier = None
            self.template_manager = None

    async def execute(
        self,
        raw_input: str,
        input_type: ContentType,
        social_platform: Optional[SocialPlatform] = None
    ) -> SummarizeResult:
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

        elif input_type == ContentType.SOCIAL:
            if not social_platform:
                return SummarizeResult(
                    content=create_text_content(raw_input),
                    success=False,
                    error_message="缺少社群平台資訊"
                )

            content = create_social_content(raw_input, social_platform)
            
            # Scrape social content
            scrape_result = await self.social_scraper.scrape(raw_input, social_platform)

            if not scrape_result.success:
                return SummarizeResult(
                    content=content,
                    success=False,
                    error_message=f"無法抓取社群貼文: {scrape_result.error_message}"
                )

            text_to_summarize = scrape_result.text_content

            # Update raw_content with actual post text (for saving to Notion)
            content.raw_content = scrape_result.text_content

            # Store social media metadata in content entity
            print(f"🐛 [Summarize] Scrape result - Likes: {scrape_result.likes}, Comments: {scrape_result.comments}, Shares: {scrape_result.shares}")
            content.author = scrape_result.author
            content.likes = scrape_result.likes
            content.comments = scrape_result.comments
            content.shares = scrape_result.shares
            print(f"🐛 [Summarize] Content entity - Likes: {content.likes}, Comments: {content.comments}, Shares: {content.shares}")

            # Add metadata to summary context for AI
            meta_info = []
            if scrape_result.author:
                meta_info.append(f"作者: {scrape_result.author}")
            if scrape_result.likes:
                meta_info.append(f"按讚數: {scrape_result.likes}")
            if scrape_result.comments:
                meta_info.append(f"留言數: {scrape_result.comments}")

            if meta_info:
                text_to_summarize = f"{' | '.join(meta_info)}\n\n{text_to_summarize}"

        else:
            content = create_text_content(raw_input)
            text_to_summarize = raw_input

        # Step 2: Check if content is empty
        if not text_to_summarize.strip():
            return SummarizeResult(
                content=content,
                success=False,
                error_message="內容為空，無法進行摘要"
            )

        # Step 3: Smart prompt selection (classify content and get template)
        custom_prompt = None
        if self.enable_smart_prompt and self.classifier and self.template_manager:
            try:
                # Classify the content
                url_for_classify = raw_input if input_type == ContentType.URL else None
                classification = await self.classifier.classify(
                    content=text_to_summarize[:1500],
                    url=url_for_classify
                )
                
                # Get the prompt template
                custom_prompt = self.template_manager.get_prompt(classification.category)
                print(f"🏷️ [Summarize] Using {classification.category} template")
                
            except Exception as e:
                print(f"⚠️ [Summarize] Smart prompt failed, using default: {e}")
                custom_prompt = None

        # Step 4: Summarize with AI
        summary_result = await self.ai_service.summarize(
            content=text_to_summarize,
            content_type=input_type.value,
            custom_prompt=custom_prompt
        )

        if not summary_result.success:
            return SummarizeResult(
                content=content,
                success=False,
                error_message=f"AI 摘要失敗: {summary_result.error_message}"
            )

        # Step 5: Update content entity with AI results
        content.title = summary_result.title
        content.summary = summary_result.summary
        content.tags = summary_result.tags

        return SummarizeResult(
            content=content,
            success=True
        )
