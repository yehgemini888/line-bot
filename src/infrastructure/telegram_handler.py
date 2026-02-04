"""
Infrastructure Layer: Telegram Webhook Handler

Handles incoming Telegram messages and coordinates with use cases.
"""

import os
import re
from typing import Optional, Tuple
from dataclasses import dataclass
import httpx

from src.domain.content import Content, ContentType, SocialPlatform
from src.usecase.summarize import SummarizeUseCase
from src.usecase.save_to_notion import SaveToNotionUseCase
from src.infrastructure.social_detector import SocialDetector
from src.infrastructure.image_detector import ImageDetector


@dataclass
class TelegramUpdate:
    """Parsed Telegram update."""
    update_id: int
    chat_id: int
    user_id: int
    username: Optional[str]
    text: str
    message_id: int


class TelegramHandler:
    """
    Handles Telegram text messages.

    Detects if input is URL or text, processes it through
    summarization and saves to Notion.
    """

    # URL pattern for extraction
    URL_PATTERN = re.compile(r'https?://\S+', re.IGNORECASE)

    # Telegram API base URL
    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(
        self,
        bot_token: str,
        summarize_usecase: SummarizeUseCase,
        save_usecase: SaveToNotionUseCase,
        social_detector: SocialDetector,
        image_detector: Optional[ImageDetector] = None,
        youtube_service=None,
        ai_service=None
    ):
        """
        Initialize the handler.

        Args:
            bot_token: Telegram bot token from @BotFather
            summarize_usecase: Use case for summarization
            save_usecase: Use case for saving to Notion
            social_detector: Detector for social media URLs
            image_detector: Detector for image URLs
            youtube_service: Service for fetching YouTube video info
            ai_service: AI service for summarization
        """
        self.bot_token = bot_token
        self.api_base = self.API_BASE.format(token=bot_token)
        self.summarize_usecase = summarize_usecase
        self.save_usecase = save_usecase
        self.social_detector = social_detector
        self.image_detector = image_detector or ImageDetector()
        self.youtube_service = youtube_service
        self.ai_service = ai_service

    def parse_update(self, update: dict) -> Optional[TelegramUpdate]:
        """Parse Telegram update JSON to TelegramUpdate object."""
        try:
            message = update.get("message", {})
            if not message:
                return None

            chat = message.get("chat", {})
            user = message.get("from", {})
            text = message.get("text", "")

            if not text:
                return None

            return TelegramUpdate(
                update_id=update.get("update_id", 0),
                chat_id=chat.get("id"),
                user_id=user.get("id"),
                username=user.get("username"),
                text=text.strip(),
                message_id=message.get("message_id")
            )
        except Exception as e:
            print(f"❌ [Telegram] Error parsing update: {e}")
            return None

    async def send_message(self, chat_id: int, text: str) -> bool:
        """Send a message to a Telegram chat."""
        try:
            url = f"{self.api_base}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"❌ [Telegram] Failed to send message: {e}")
            return False

    async def handle_update(self, update: dict) -> None:
        """
        Handle incoming Telegram update.

        Args:
            update: Raw Telegram update JSON
        """
        parsed = self.parse_update(update)
        if not parsed:
            return

        print(f"📩 [Telegram] Message from @{parsed.username}: {parsed.text[:50]}...")

        # Send processing message
        await self.send_message(parsed.chat_id, "收到！正在處理中... ⏳")

        # Process and get response
        response = await self.process_message(parsed.text)

        # Send response
        await self.send_message(parsed.chat_id, response)

    async def process_message(self, user_text: str) -> str:
        """
        Process user message and return response.

        Args:
            user_text: User's message text

        Returns:
            Response message to send back
        """
        # Detect content type
        content_type, platform, extracted_url = self._analyze_content(user_text)

        # Handle YouTube separately
        if content_type == ContentType.YOUTUBE and extracted_url:
            if self.youtube_service and self.ai_service:
                return await self._handle_youtube(extracted_url)
            else:
                content_type = ContentType.URL

        # Process content
        content_to_process = extracted_url if extracted_url else user_text

        # Summarize
        summarize_result = await self.summarize_usecase.execute(
            raw_input=content_to_process,
            input_type=content_type,
            social_platform=platform
        )

        if not summarize_result.success:
            return f"❌ 處理失敗：{summarize_result.error_message}"

        content = summarize_result.content

        # Save to Notion
        save_result = await self.save_usecase.execute(content)

        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        # Build response
        return self._build_success_response(content, save_result.page_url)

    def _extract_url(self, text: str) -> Optional[str]:
        """Extract URL from text."""
        match = self.URL_PATTERN.search(text)
        return match.group(0) if match else None

    def _analyze_content(self, text: str) -> Tuple[ContentType, Optional[SocialPlatform], Optional[str]]:
        """Analyze content type from user text."""
        extracted_url = self._extract_url(text)

        if extracted_url:
            # Check image URL
            image_result = self.image_detector.detect(extracted_url)
            if image_result.is_image:
                return ContentType.IMAGE, None, extracted_url

            # Check YouTube URL
            if self.social_detector.is_youtube_url(extracted_url):
                return ContentType.YOUTUBE, None, extracted_url

            # Check social media URL
            social_result = self.social_detector.detect(extracted_url)
            if social_result.is_social:
                return ContentType.SOCIAL, social_result.platform, extracted_url

            # Regular URL
            return ContentType.URL, None, extracted_url

        return ContentType.TEXT, None, None

    async def _handle_youtube(self, youtube_url: str) -> str:
        """Handle YouTube URL processing."""
        from src.domain.content import create_youtube_content

        print(f"🎬 [YouTube] Processing: {youtube_url}")

        # Get video info
        video_info = await self.youtube_service.get_video_info(youtube_url)
        if not video_info:
            return "❌ 無法取得 YouTube 影片資訊，請確認網址是否正確"

        # Prepare content for AI
        if video_info.has_captions and video_info.captions:
            text_to_summarize = f"""影片標題：{video_info.title}
頻道：{video_info.channel_name}
時長：{video_info.duration}

字幕內容：
{video_info.captions[:15000]}"""
            has_captions = True
        else:
            text_to_summarize = f"""影片標題：{video_info.title}
頻道：{video_info.channel_name}
時長：{video_info.duration}

影片描述：
{video_info.description[:3000] if video_info.description else '(無描述)'}"""
            has_captions = False

        # AI Summarization
        summary_result = await self.ai_service.summarize(
            content=text_to_summarize,
            content_type="youtube"
        )

        if not summary_result.success:
            return f"❌ AI 摘要失敗：{summary_result.error_message}"

        # Create content entity
        content = create_youtube_content(
            url=youtube_url,
            title=video_info.title,
            channel_name=video_info.channel_name,
            video_duration=video_info.duration
        )
        content.summary = summary_result.summary
        content.title = summary_result.title or video_info.title
        content.tags = summary_result.tags

        # Save to Notion
        save_result = await self.save_usecase.execute(content)
        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        # Build response
        return self._build_youtube_response(content, video_info, has_captions, save_result.page_url)

    def _build_success_response(self, content: Content, page_url: Optional[str] = None) -> str:
        """Build success response message."""
        tags_str = ", ".join(content.tags) if content.tags else "無"

        response = f"""✅ 已儲存至 Notion！

📌 標題：{content.title}

📝 摘要：
{content.summary}

🏷️ 標籤：{tags_str}"""

        if page_url:
            response += f"\n\n📄 Notion 連結：{page_url}"

        return response

    def _build_youtube_response(
        self,
        content: Content,
        video_info,
        has_captions: bool,
        page_url: Optional[str] = None
    ) -> str:
        """Build YouTube success response."""
        tags_str = ", ".join(content.tags) if content.tags else "無"
        caption_note = "" if has_captions else "\n\n⚠️ 此影片無字幕，僅能提供基本摘要"

        response = f"""✅ YouTube 影片已儲存至 Notion！

🎬 頻道：{video_info.channel_name}
⏱️ 時長：{video_info.duration}

📌 標題：{content.title}

📝 摘要：
{content.summary}

🏷️ 標籤：{tags_str}{caption_note}"""

        if page_url:
            response += f"\n\n📄 Notion 連結：{page_url}"

        return response
