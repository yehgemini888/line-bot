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
    template_used: Optional[str] = None  # Which prompt template was used
    output_format_used: Optional[str] = None  # Which output format was used


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
            self._templates_loaded = False  # Flag to track if templates are loaded
        else:
            self.classifier = None
            self.template_manager = None
            self._templates_loaded = True  # No need to load

    async def _ensure_templates_loaded(self):
        """
        每次都從 Notion 重新載入模板。
        確保 Notion 的變更能即時反映。
        """
        if self.template_manager:
            print(f"🔄 [Summarize] Loading templates from Notion...")
            try:
                await self.template_manager.load_from_notion()
                print(f"📋 [Summarize] Available categories: {self.template_manager.get_all_categories()}")
            except Exception as e:
                print(f"❌ [Summarize] Template loading failed: {e}")

    async def execute(
        self,
        raw_input: str,
        input_type: ContentType,
        social_platform: Optional[SocialPlatform] = None,
        # Image-specific parameters
        image_data: Optional[bytes] = None,
        image_mime_type: Optional[str] = None,
        image_url: Optional[str] = None,  # For already-uploaded images
        # YouTube-specific parameters
        youtube_info: Optional[dict] = None,
        # Audio-specific parameters
        audio_transcription: Optional[str] = None,
        audio_duration: Optional[float] = None
    ) -> SummarizeResult:
        """
        Execute the summarize use case.

        Args:
            raw_input: The raw text or URL from user
            input_type: ContentType (TEXT, URL, SOCIAL, IMAGE, YOUTUBE, AUDIO)
            social_platform: Platform if SOCIAL type
            image_data: Image binary data if IMAGE type
            image_mime_type: Image MIME type if IMAGE type
            image_url: Image URL (e.g., Drive link) if already uploaded
            youtube_info: Dict with title, captions, description, channel, duration
            audio_transcription: Transcribed text if AUDIO type
            audio_duration: Audio duration in seconds if AUDIO type

        Returns:
            SummarizeResult containing the processed Content entity
        """
        # Step 0: Ensure templates are loaded from Notion
        await self._ensure_templates_loaded()
        
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


        elif input_type == ContentType.IMAGE:
            # Image processing
            from src.domain.content import create_image_content
            
            if not image_data and not image_url:
                return SummarizeResult(
                    content=create_image_content(image_url="", image_description=""),
                    success=False,
                    error_message="缺少圖片資料或 URL"
                )
            
            # Create content entity
            content = create_image_content(
                image_url=image_url or "[Processing]",
                image_description=None
            )
            
            # For AI analysis, we'll use image_data
            # The actual analysis will happen in Step 4
            text_to_summarize = "[Image Analysis]"
            print(f"🖼️ [Summarize] Processing image (has_data={image_data is not None}, has_url={image_url is not None})")

        elif input_type == ContentType.YOUTUBE:
            # YouTube processing
            from src.domain.content import create_youtube_content
            
            if not youtube_info:
                return SummarizeResult(
                    content=create_youtube_content(url=raw_input),
                    success=False,
                    error_message="缺少 YouTube 影片資訊"
                )
            
            # Create content entity with metadata
            content = create_youtube_content(
                url=raw_input,
                title=youtube_info.get("title"),
                channel_name=youtube_info.get("channel"),
                video_duration=youtube_info.get("duration")
            )
            
            # Prepare text for summarization
            has_captions = youtube_info.get("captions") and len(youtube_info.get("captions", "")) > 0
            
            if has_captions:
                text_to_summarize = f"""影片標題：{youtube_info.get('title')}
頻道：{youtube_info.get('channel')}
時長：{youtube_info.get('duration')}

字幕內容：
{youtube_info.get('captions')[:15000]}"""
            else:
                text_to_summarize = f"""影片標題：{youtube_info.get('title')}
頻道：{youtube_info.get('channel')}
時長：{youtube_info.get('duration')}

影片描述：
{youtube_info.get('description', '(無描述)')[:3000]}"""
            
            print(f"🎬 [Summarize] Processing YouTube (has_captions={has_captions})")

        elif input_type == ContentType.AUDIO:
            # Audio processing
            from src.domain.content import create_audio_content
            
            if not audio_transcription:
                return SummarizeResult(
                    content=create_audio_content(transcription=""),
                    success=False,
                    error_message="缺少語音轉錄文字"
                )
            
            # Create content entity
            content = create_audio_content(
                transcription=audio_transcription,
                duration_seconds=audio_duration
            )
            
            # Use transcription for summarization
            text_to_summarize = audio_transcription
            print(f"🎙️ [Summarize] Processing audio ({len(audio_transcription)} chars)")

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

        # Step 3: Smart prompt selection (classify content and get template + schema)
        template = None
        schema = None
        template_used = None
        
        if self.enable_smart_prompt and self.classifier and self.template_manager:
            try:
                # Classify the content
                url_for_classify = raw_input if input_type == ContentType.URL else None
                classification = await self.classifier.classify(
                    content=text_to_summarize[:1500],
                    url=url_for_classify
                )
                
                # Get the prompt template AND schema
                template, schema = await self.template_manager.get_template_with_schema(
                    classification.category,
                    text_to_summarize,  # 傳入內容以便動態生成 Schema
                    self.ai_service
                )
                template_used = template.name if template else classification.category
                print(f"🏷️ [Summarize] 使用模板: {classification.category}")
                print(f"📋 [Summarize] 輸出格式: {template.output_format if template else 'default'}")
                
            except Exception as e:
                print(f"⚠️ [Summarize] Smart prompt 失敗，使用預設: {e}")
                template = None
                schema = None

        # Step 4: Summarize with AI
        try:
            # Special handling for IMAGE type (uses vision API)
            if input_type == ContentType.IMAGE and image_data:
                print(f"🖼️ [Summarize] Using Vision API for image analysis")
                
                # Use vision API to analyze image
                vision_result = await self.ai_service.analyze_image(
                    image_data=image_data,
                    mime_type=image_mime_type or "image/jpeg",
                    prompt=template.prompt if template else None
                )
                
                if not vision_result.success:
                    return SummarizeResult(
                        content=content,
                        success=False,
                        error_message=f"圖片分析失敗: {vision_result.error_message}"
                    )
                
                # Update content with vision results
                content.image_description = vision_result.description
                content.title = vision_result.title or "圖片"
                content.summary = vision_result.description
                content.tags = vision_result.tags
                
                # Return early for images
                return SummarizeResult(
                    content=content,
                    success=True,
                    template_used=template.name if template else "image",
                    output_format_used=template.output_format if template else "圖片分析"
                )
            
            if template and schema:
                # 使用新的 Structured Output API
                print(f"🎯 [Summarize] 使用 Structured Output API")
                result_dict = await self.ai_service.summarize_with_schema(
                    content=text_to_summarize,
                    prompt=template.prompt,
                    schema=schema
                )
                
                # 從結果中提取標準欄位
                # Schema 使用繁體中文欄位名稱
                result_title = result_dict.get("標題", result_dict.get("title", "未能取得標題"))
                result_tags = result_dict.get("標籤", result_dict.get("tags", []))
                
                # 摘要欄位可能是 摘要, summary, description, 或其他
                # 優先順序：摘要 > summary > description > 其他欄位組合
                if "摘要" in result_dict:
                    result_summary = result_dict["摘要"]
                elif "summary" in result_dict:
                    result_summary = result_dict["summary"]
                elif "description" in result_dict:
                    result_summary = result_dict["description"]
                else:
                    # 將所有非 標題/標籤 的欄位組合成摘要
                    summary_parts = []
                    for key, value in result_dict.items():
                        if key in ["標題", "標籤", "title", "tags"]:
                            continue
                        if isinstance(value, list):
                            summary_parts.append(f"**{key}**:\n" + "\n".join(f"- {item}" for item in value))
                        elif isinstance(value, str):
                            summary_parts.append(f"**{key}**: {value}")
                    result_summary = "\n\n".join(summary_parts) if summary_parts else str(result_dict)
                
            else:
                # 回退到舊的 summarize 方法
                print(f"⚠️ [Summarize] 回退到傳統摘要方法")
                summary_result = await self.ai_service.summarize(
                    content=text_to_summarize,
                    content_type=input_type.value,
                    custom_prompt=template.prompt if template else None
                )
                
                if not summary_result.success:
                    return SummarizeResult(
                        content=content,
                        success=False,
                        error_message=f"AI 摘要失敗: {summary_result.error_message}"
                    )
                
                result_title = summary_result.title
                result_summary = summary_result.summary
                result_tags = summary_result.tags
                
        except Exception as e:
            print(f"❌ [Summarize] AI 摘要失敗: {e}")
            return SummarizeResult(
                content=content,
                success=False,
                error_message=f"AI 摘要失敗: {str(e)}"
            )

        # Step 5: Update content entity with AI results
        content.title = result_title
        content.summary = result_summary
        content.tags = result_tags

        return SummarizeResult(
            content=content,
            success=True,
            template_used=template_used,
            output_format_used=template.output_format if template else None
        )
