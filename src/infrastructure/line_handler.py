"""
Infrastructure Layer: Line Webhook Handler

Handles incoming Line messages and coordinates with use cases.
"""

import re
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.domain.content import ContentType
from src.usecase.summarize import SummarizeUseCase
from src.usecase.save_to_notion import SaveToNotionUseCase


class LineMessageHandler:
    """
    Handles Line text messages.

    Detects if input is URL or text, processes it through
    summarization and saves to Notion.
    """

    # URL pattern for detection
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    def __init__(
        self,
        channel_access_token: str,
        summarize_usecase: SummarizeUseCase,
        save_usecase: SaveToNotionUseCase
    ):
        """
        Initialize the handler.

        Args:
            channel_access_token: Line channel access token
            summarize_usecase: Use case for summarization
            save_usecase: Use case for saving to Notion
        """
        configuration = Configuration(access_token=channel_access_token)
        self.api_client = AsyncApiClient(configuration)
        self.messaging_api = AsyncMessagingApi(self.api_client)
        self.summarize_usecase = summarize_usecase
        self.save_usecase = save_usecase

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

        # Detect content type
        content_type = self._detect_content_type(user_text)

        # Process the content
        result = await self._process_content(user_text, content_type)

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
        # Detect content type
        content_type = self._detect_content_type(user_text)

        # Step 1: Summarize
        summarize_result = await self.summarize_usecase.execute(
            raw_input=user_text,
            input_type=content_type
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

    def _detect_content_type(self, text: str) -> ContentType:
        """Detect if text is a URL or plain text."""
        if self.URL_PATTERN.match(text.strip()):
            return ContentType.URL
        return ContentType.TEXT

    async def _process_content(self, text: str, content_type: ContentType) -> str:
        """Process content through summarization and save."""
        # Step 1: Summarize
        summarize_result = await self.summarize_usecase.execute(
            raw_input=text,
            input_type=content_type
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
