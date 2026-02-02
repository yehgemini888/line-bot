"""
Infrastructure Layer: Line Webhook Handler

Handles incoming Line messages and coordinates with use cases.
"""

import re
from typing import Optional
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.domain.content import ContentType, SocialPlatform
from src.usecase.summarize import SummarizeUseCase
from src.usecase.save_to_notion import SaveToNotionUseCase
from src.infrastructure.social_detector import SocialDetector


class LineMessageHandler:
    """
    Handles Line text messages.

    Detects if input is URL or text, processes it through
    summarization and saves to Notion.
    """

    # URL pattern for extraction - simple and permissive
    # Matches https:// or http:// followed by any non-whitespace characters
    URL_PATTERN = re.compile(
        r'https?://\S+',
        re.IGNORECASE
    )

    def __init__(
        self,
        channel_access_token: str,
        summarize_usecase: SummarizeUseCase,
        save_usecase: SaveToNotionUseCase,
        social_detector: SocialDetector
    ):
        """
        Initialize the handler.

        Args:
            channel_access_token: Line channel access token
            summarize_usecase: Use case for summarization
            save_usecase: Use case for saving to Notion
            social_detector: Detector for social media URLs
        """
        configuration = Configuration(access_token=channel_access_token)
        self.api_client = AsyncApiClient(configuration)
        self.messaging_api = AsyncMessagingApi(self.api_client)
        self.summarize_usecase = summarize_usecase
        self.save_usecase = save_usecase
        self.social_detector = social_detector

    async def handle_message(self, event: MessageEvent) -> None:
        """
        Handle incoming text message event.

        Args:
            event: Line message event
        """
        if not isinstance(event.message, TextMessageContent):
            return

        user_text = event.message.text.strip()
        reply_token = event.reply_token

        # Send processing message
        await self._reply(reply_token, "收到！正在處理中... ⏳")

        # Detect content type and extract URL if present
        content_type, platform, extracted_url = self._analyze_content(user_text)

        # Process the content (use extracted URL for URL/SOCIAL types)
        content_to_process = extracted_url if extracted_url else user_text
        result = await self._process_content(content_to_process, content_type, platform)

        # Note: We can't reply twice with the same token
        # The result will be sent via push message if needed
        # For now, the processing message serves as acknowledgment

    async def handle_message_with_push(
        self,
        user_id: str,
        user_text: str
    ) -> str:
        """
        Handle message and return result (for push message response).

        Args:
            user_id: Line user ID for push message
            user_text: The text content from user

        Returns:
            Result message to send back to user
        """
        # Detect content type and extract URL if present
        content_type, platform, extracted_url = self._analyze_content(user_text)

        # Use extracted URL for URL/SOCIAL types, otherwise use original text
        content_to_process = extracted_url if extracted_url else user_text

        # Step 1: Summarize
        summarize_result = await self.summarize_usecase.execute(
            raw_input=content_to_process,
            input_type=content_type,
            social_platform=platform
        )

        if not summarize_result.success:
            return f"❌ 處理失敗：{summarize_result.error_message}"

        content = summarize_result.content

        # Step 2: Save to Notion
        save_result = await self.save_usecase.execute(content)

        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        # Build success response
        response = self._build_success_response(content, save_result.page_url)
        return response

    def _extract_url(self, text: str) -> Optional[str]:
        """Extract URL from text if present."""
        match = self.URL_PATTERN.search(text)
        if match:
            url = match.group(0)
            # Strip trailing punctuation that might have been captured
            # (common when URL is embedded in text like "Check this: https://example.com.")
            url = url.rstrip('.,;:!?)]\'"')
            return url
        return None

    def _analyze_content(self, text: str) -> tuple[ContentType, Optional[SocialPlatform], Optional[str]]:
        """
        Analyze text to determine content type, platform, and extract URL.

        Returns:
            tuple of (ContentType, SocialPlatform or None, extracted_url or None)
        """
        # First, extract URL from anywhere in the text
        extracted_url = self._extract_url(text)

        if extracted_url:
            # Check if it's a social media URL
            social_result = self.social_detector.detect(extracted_url)
            if social_result.is_social:
                print(f"🕵️ [Debug] Detected SOCIAL: {social_result.platform} (URL: {extracted_url})")
                return ContentType.SOCIAL, social_result.platform, extracted_url

            # It's a regular URL
            print(f"🕵️ [Debug] Detected URL: {extracted_url}")
            return ContentType.URL, None, extracted_url

        print(f"🕵️ [Debug] Detected TEXT: {text[:50]}...")
        return ContentType.TEXT, None, None

    async def _process_content(
        self, 
        text: str, 
        content_type: ContentType,
        platform: Optional[SocialPlatform] = None
    ) -> str:
        """Process content through summarization and save."""
        print(f"⚙️ [Debug] Processing content: type={content_type}, platform={platform}")
        # Step 1: Summarize
        summarize_result = await self.summarize_usecase.execute(
            raw_input=text,
            input_type=content_type,
            social_platform=platform
        )

        if not summarize_result.success:
            return f"❌ 處理失敗：{summarize_result.error_message}"

        content = summarize_result.content

        # Step 2: Save to Notion
        save_result = await self.save_usecase.execute(content)

        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        return self._build_success_response(content, save_result.page_url)

    def _build_success_response(self, content, page_url: str = None) -> str:
        """Build success response message."""
        tags_str = ", ".join(content.tags) if content.tags else "無"

        response = f"""✅ 已儲存至 Notion！

📌 標題：{content.title}

📝 摘要：
{content.summary}

🏷️ 標籤：{tags_str}"""

        if page_url:
            response += f"\n\n🔗 連結：{page_url}"

        return response

    async def _reply(self, reply_token: str, message: str) -> None:
        """Send reply message."""
        try:
            await self.messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=message)]
                )
            )
        except Exception:
            pass  # Reply token may have expired

    async def push_message(self, user_id: str, message: str) -> None:
        """Send push message to user."""
        from linebot.v3.messaging import PushMessageRequest

        try:
            await self.messaging_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=message)]
                )
            )
        except Exception as e:
            print(f"Failed to push message: {e}")
