"""
Infrastructure Layer: Line Webhook Handler

Handles incoming Line messages and coordinates with use cases.
"""

import re
import uuid
import httpx
from typing import Optional, Tuple
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.domain.content import Content, ContentType, SocialPlatform
from src.infrastructure.response_builder import ResponseBuilder
from src.usecase.summarize import SummarizeUseCase
from src.usecase.save_to_notion import SaveToNotionUseCase
from src.infrastructure.social_detector import SocialDetector
from src.infrastructure.image_detector import ImageDetector


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
        social_detector: SocialDetector,
        image_detector: Optional[ImageDetector] = None,
        process_image_usecase = None,
        youtube_service = None,
        ai_service = None,
        whisper_service = None
    ):
        """
        Initialize the handler.

        Args:
            channel_access_token: Line channel access token
            summarize_usecase: Use case for summarization
            save_usecase: Use case for saving to Notion
            social_detector: Detector for social media URLs
            image_detector: Detector for image URLs
            process_image_usecase: Use case for processing images
            youtube_service: Service for fetching YouTube video info and captions
            ai_service: AI service for summarization (Gemini/OpenAI)
            whisper_service: Service for speech-to-text transcription
        """
        configuration = Configuration(access_token=channel_access_token)
        self.api_client = AsyncApiClient(configuration)
        self.messaging_api = AsyncMessagingApi(self.api_client)
        self.channel_access_token = channel_access_token
        self.summarize_usecase = summarize_usecase
        self.save_usecase = save_usecase
        self.social_detector = social_detector
        self.image_detector = image_detector or ImageDetector()
        self.process_image_usecase = process_image_usecase
        self.youtube_service = youtube_service
        self.ai_service = ai_service
        self.whisper_service = whisper_service

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

        # Handle YouTube separately (needs youtube_service)
        if content_type == ContentType.YOUTUBE and extracted_url:
            if hasattr(self, 'youtube_service') and self.youtube_service:
                return await self.handle_youtube_with_push(user_id, extracted_url)
            else:
                # Fall back to regular URL processing if youtube_service not available
                content_type = ContentType.URL

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

        # Build success response with template info
        response = self._build_success_response(
            content, 
            save_result.page_url,
            summarize_result.template_used,
            summarize_result.output_format_used
        )
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

    def _analyze_content(self, text: str) -> Tuple[ContentType, Optional[SocialPlatform], Optional[str]]:
        """
        Analyze text to determine content type, platform, and extract URL.

        Returns:
            tuple of (ContentType, SocialPlatform or None, extracted_url or None)
        """
        # First, extract URL from anywhere in the text
        extracted_url = self._extract_url(text)

        if extracted_url:
            # Check if it's an image URL
            image_result = self.image_detector.detect(extracted_url)
            if image_result.is_image:
                print(f"🖼️ [Debug] Detected IMAGE URL: {extracted_url}")
                return ContentType.IMAGE, None, extracted_url

            # Check if it's a YouTube URL (before social media)
            if self.social_detector.is_youtube_url(extracted_url):
                print(f"🎬 [Debug] Detected YOUTUBE URL: {extracted_url}")
                return ContentType.YOUTUBE, None, extracted_url

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

        return self._build_success_response(
            content, 
            save_result.page_url,
            summarize_result.template_used,
            summarize_result.output_format_used
        )

    def _build_success_response(
        self, 
        content, 
        page_url: str = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:
        """Build success response message."""
        tags_str = ", ".join(content.tags) if content.tags else "無"
        template_info = f"🧠 使用模板：{template_used}\n" if template_used else ""
        format_info = f"📋 輸出格式：{output_format_used}\n" if output_format_used else ""

        response = f"""✅ 已儲存至 Notion！

{template_info}{format_info}
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

    async def download_line_image(self, message_id: str) -> Optional[bytes]:
        """
        Download image from Line servers.

        Args:
            message_id: Line message ID containing the image

        Returns:
            Image binary data or None if failed
        """
        try:
            url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
            headers = {"Authorization": f"Bearer {self.channel_access_token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)

                if response.status_code == 200:
                    print(f"📥 [Line] Downloaded image: {len(response.content)} bytes")
                    return response.content
                else:
                    print(f"❌ [Line] Failed to download image: {response.status_code}")
                    return None

        except Exception as e:
            print(f"❌ [Line] Error downloading image: {e}")
            return None

    async def download_image_from_url(self, url: str) -> Optional[bytes]:
        """
        Download image from a URL.

        Args:
            url: Image URL to download

        Returns:
            Image binary data or None if failed
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, timeout=30.0)

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "image" in content_type or self._is_image_response(response.content):
                        print(f"📥 [HTTP] Downloaded image from URL: {len(response.content)} bytes")
                        return response.content
                    else:
                        print(f"⚠️ [HTTP] URL did not return image content: {content_type}")
                        return None
                else:
                    print(f"❌ [HTTP] Failed to download image: {response.status_code}")
                    return None

        except Exception as e:
            print(f"❌ [HTTP] Error downloading image: {e}")
            return None

    def _is_image_response(self, content: bytes) -> bool:
        """Check if response content is an image based on magic bytes."""
        if len(content) < 8:
            return False

        # Check common image magic bytes
        # JPEG: FF D8 FF
        if content[:3] == b'\xff\xd8\xff':
            return True
        # PNG: 89 50 4E 47 0D 0A 1A 0A
        if content[:8] == b'\x89PNG\r\n\x1a\n':
            return True
        # GIF: 47 49 46 38
        if content[:4] == b'GIF8':
            return True
        # WebP: 52 49 46 46 ... 57 45 42 50
        if content[:4] == b'RIFF' and len(content) > 11 and content[8:12] == b'WEBP':
            return True

        return False

    async def handle_image_message_with_push(
        self,
        user_id: str,
        message_id: str
    ) -> str:
        """
        Handle Line image message and return result.

        Args:
            user_id: Line user ID for push message
            message_id: Line message ID containing the image

        Returns:
            Result message to send back to user
        """
        if not self.drive_service:
            return "❌ 圖片處理功能未啟用（需要 Google Drive）"

        # Step 1: Download image from Line
        image_data = await self.download_line_image(message_id)
        if not image_data:
            return "❌ 無法下載圖片"

        # Generate filename
        filename = f"line_image_{uuid.uuid4().hex[:8]}.jpg"

        # Step 2: Upload to Google Drive first
        upload_result = await self.drive_service.upload_image(
            image_data=image_data,
            filename=filename,
            mime_type="image/jpeg"
        )

        if not upload_result.success:
            return f"❌ 上傳圖片失敗：{upload_result.error_message}"

        # Step 3: Analyze and summarize via SummarizeUseCase (NEW - uses template system)
        summarize_result = await self.summarize_usecase.execute(
            raw_input="[Image]",
            input_type=ContentType.IMAGE,
            image_data=image_data,
            image_mime_type="image/jpeg",
            image_url=upload_result.file_url
        )

        if not summarize_result.success:
            return f"❌ 處理失敗：{summarize_result.error_message}"

        content = summarize_result.content
        # Update with Drive URL (in case it wasn't set)
        content.image_url = upload_result.file_url

        # Step 4: Save to Notion
        save_result = await self.save_usecase.execute(content)

        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        return self._build_image_success_response(
            content,
            save_result.page_url,
            template_used=summarize_result.template_used,
            output_format_used=summarize_result.output_format_used
        )

    async def handle_image_url_with_push(
        self,
        user_id: str,
        image_url: str
    ) -> str:
        """
        Handle image URL and return result.

        Args:
            user_id: Line user ID for push message
            image_url: URL of the image

        Returns:
            Result message to send back to user
        """
        if not self.drive_service:
            return "❌ 圖片處理功能未啟用（需要 Google Drive）"

        # Step 1: Download image from URL
        image_data = await self.download_image_from_url(image_url)
        if not image_data:
            return "❌ 無法下載圖片，請確認網址是否正確"

        # Determine MIME type from URL
        mime_type = self.image_detector.get_mime_type(image_url)

        # Generate filename with appropriate extension
        ext = ".jpg"
        if "png" in mime_type:
            ext = ".png"
        elif "gif" in mime_type:
            ext = ".gif"
        elif "webp" in mime_type:
            ext = ".webp"

        filename = f"url_image_{uuid.uuid4().hex[:8]}{ext}"

        # Step 2: Upload to Google Drive first
        upload_result = await self.drive_service.upload_image(
            image_data=image_data,
            filename=filename,
            mime_type=mime_type
        )

        if not upload_result.success:
            return f"❌ 上傳圖片失敗：{upload_result.error_message}"

        # Step 3: Analyze and summarize via SummarizeUseCase (NEW - uses template system)
        summarize_result = await self.summarize_usecase.execute(
            raw_input=image_url,
            input_type=ContentType.IMAGE,
            image_data=image_data,
            image_mime_type=mime_type,
            image_url=upload_result.file_url
        )

        if not summarize_result.success:
            return f"❌ 處理失敗：{summarize_result.error_message}"

        content = summarize_result.content
        # Update with Drive URL
        content.image_url = upload_result.file_url

        # Step 4: Save to Notion
        save_result = await self.save_usecase.execute(content)

        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        return self._build_image_success_response(
            content,
            save_result.page_url,
            template_used=summarize_result.template_used,
            output_format_used=summarize_result.output_format_used
        )

    def _build_image_success_response(
        self,
        content: Content,
        page_url: Optional[str] = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:
        """Build success response message for image processing."""
        return ResponseBuilder.build_image_response(
            content=content,
            page_url=page_url,
            template_used=template_used,
            output_format_used=output_format_used
        )

    async def handle_youtube_with_push(
        self,
        user_id: str,
        youtube_url: str
    ) -> str:
        """
        Handle YouTube URL and return result.

        Args:
            user_id: Line user ID for push message
            youtube_url: YouTube video URL

        Returns:
            Result message to send back to user
        """
        if not self.youtube_service:
            return "❌ YouTube 功能未啟用"

        print(f"🎬 [YouTube] Processing: {youtube_url}")

        # Step 1: Get video info and captions
        video_info = await self.youtube_service.get_video_info(youtube_url)

        if not video_info:
            return "❌ 無法取得 YouTube 影片資訊，請確認網址是否正確"

        # Step 2: Summarize via SummarizeUseCase (NEW - uses template system)
        summarize_result = await self.summarize_usecase.execute(
            raw_input=youtube_url,
            input_type=ContentType.YOUTUBE,
            youtube_info={
                "title": video_info.title,
                "captions": video_info.captions,
                "description": video_info.description,
                "channel": video_info.channel_name,
                "duration": video_info.duration
            }
        )

        if not summarize_result.success:
            return f"❌ 處理失敗：{summarize_result.error_message}"

        content = summarize_result.content

        # Step 3: Save to Notion
        save_result = await self.save_usecase.execute(content)

        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        # Build success response with template info
        has_captions = video_info.has_captions and video_info.captions
        return self._build_youtube_success_response(
            content, 
            video_info, 
            has_captions,
            save_result.page_url,
            template_used=summarize_result.template_used,
            output_format_used=summarize_result.output_format_used
        )

    def _build_youtube_success_response(
        self,
        content,
        video_info,
        has_captions: bool,
        page_url: Optional[str] = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:
        """Build success response message for YouTube processing."""
        return ResponseBuilder.build_youtube_response(
            content=content,
            video_info=video_info,
            has_captions=has_captions,
            page_url=page_url,
            template_used=template_used,
            output_format_used=output_format_used
        )

    async def handle_audio_message(self, user_id: str, message_id: str) -> str:
        """
        Handle audio/voice message.

        Args:
            user_id: Line user ID
            message_id: Line message ID

        Returns:
            Response message string
        """
        if not self.whisper_service:
            return "❌ 語音功能未啟用"

        print(f"🎙️ [Audio] Processing audio message: {message_id}")

        try:
            # Download audio from Line
            audio_bytes = await self._get_message_content(message_id)
            if not audio_bytes:
                return "❌ 無法下載音檔"

            print(f"🎙️ [Audio] Downloaded {len(audio_bytes)} bytes")

            # Transcribe with Whisper
            transcription_result = await self.whisper_service.transcribe(
                audio_bytes,
                filename="audio.m4a"  # Line uses m4a format
            )

            if not transcription_result.success:
                return f"❌ 語音轉文字失敗：{transcription_result.error_message}"

            transcribed_text = transcription_result.text
            duration = transcription_result.duration_seconds

            print(f"🎙️ [Audio] Transcribed: {transcribed_text[:50]}...")

            # Step 3: Summarize via SummarizeUseCase (NEW - uses template system)
            summarize_result = await self.summarize_usecase.execute(
                raw_input=transcribed_text,
                input_type=ContentType.AUDIO,
                audio_transcription=transcribed_text,
                audio_duration=duration
            )

            if not summarize_result.success:
                # Return transcription even if summarization fails
                return f"✅ 語音轉文字完成（摘要失敗）：\n\n{transcribed_text}"

            content = summarize_result.content

            # Step 4: Save to Notion
            save_result = await self.save_usecase.execute(content)

            if not save_result.success:
                return f"❌ 儲存失敗：{save_result.error_message}"

            # Build response with template info
            return self._build_audio_success_response(
                content,
                transcribed_text,
                duration,
                save_result.page_url,
                template_used=summarize_result.template_used,
                output_format_used=summarize_result.output_format_used
            )

        except Exception as e:
            print(f"❌ [Audio] Error: {e}")
            return f"❌ 處理語音訊息時發生錯誤：{str(e)}"

    def _build_audio_success_response(
        self,
        content,
        transcription: str,
        duration: Optional[float],
        page_url: Optional[str] = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:
        """Build success response for audio processing."""
        return ResponseBuilder.build_audio_response(
            content=content,
            transcription=transcription,
            duration=duration,
            page_url=page_url,
            template_used=template_used,
            output_format_used=output_format_used
        )
