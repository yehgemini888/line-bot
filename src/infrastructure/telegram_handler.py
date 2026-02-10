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
from src.infrastructure.response_builder import ResponseBuilder
from src.usecase.summarize import SummarizeUseCase
from src.usecase.save_to_notion import SaveToNotionUseCase
from src.infrastructure.social_detector import SocialDetector
from src.infrastructure.image_detector import ImageDetector

import logging

logger = logging.getLogger(__name__)


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
        ai_service=None,
        whisper_service=None,
        process_image_usecase=None,
        drive_service=None,
        document_extractor=None
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
            whisper_service: Service for speech-to-text
            process_image_usecase: Use case for processing images (upload to Drive + AI analysis)
            drive_service: Service for uploading images to Google Drive
        """
        self.bot_token = bot_token
        self.api_base = self.API_BASE.format(token=bot_token)
        self.summarize_usecase = summarize_usecase
        self.save_usecase = save_usecase
        self.social_detector = social_detector
        self.image_detector = image_detector or ImageDetector()
        self.youtube_service = youtube_service
        self.ai_service = ai_service
        self.whisper_service = whisper_service
        self.process_image_usecase = process_image_usecase
        self.drive_service = drive_service
        self.document_extractor = document_extractor

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
            logger.error(f"❌ [Telegram] Error parsing update: {e}")
            return None

    async def send_message(self, chat_id: int, text: str) -> bool:
        """Send a message to a Telegram chat.

        Handles messages longer than Telegram's 4096 char limit by splitting.
        Falls back to plain text if HTML parsing fails.
        """
        MAX_LENGTH = 4096
        chunks = [text[i:i + MAX_LENGTH] for i in range(0, len(text), MAX_LENGTH)]

        for chunk in chunks:
            success = await self._send_single_message(chat_id, chunk)
            if not success:
                return False
        return True

    async def _send_single_message(self, chat_id: int, text: str) -> bool:
        """Send a single message, falling back to plain text if HTML fails."""
        url = f"{self.api_base}/sendMessage"

        # Try without parse_mode first (safe for any content)
        try:
            payload = {"chat_id": chat_id, "text": text}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"❌ [Telegram] Failed to send message: {e}")
            return False

    async def handle_update(self, update: dict) -> None:
        """
        Handle incoming Telegram update.

        Args:
            update: Raw Telegram update JSON
        """
        message = update.get("message", {})
        if not message:
            return

        chat_id = message.get("chat", {}).get("id")
        username = message.get("from", {}).get("username", "Unknown")

        # Check for voice message
        voice = message.get("voice")
        if voice:
            logger.info(f"🎙️ [Telegram] Voice from @{username}")
            await self.send_message(chat_id, "收到語音訊息！正在轉錄中... 🎙️")
            response = await self._handle_voice_message(voice, chat_id)
            await self.send_message(chat_id, response)
            return

        # Check for photo message
        photo = message.get("photo")
        if photo:
            logger.info(f"📸 [Telegram] Photo from @{username}")
            await self.send_message(chat_id, "收到圖片！正在分析中... 🖼️")
            response = await self._handle_photo_message(photo, message.get("caption", ""), chat_id)
            await self.send_message(chat_id, response)
            return

        # Check for document/file message
        document = message.get("document")
        if document:
            file_name = document.get("file_name", "unknown")
            logger.info(f"📄 [Telegram] Document from @{username}: {file_name}")
            await self.send_message(chat_id, f"收到文件：{file_name}\n正在處理中... 📄")
            response = await self._handle_document_message(document, chat_id)
            await self.send_message(chat_id, response)
            return

        # Check for text message
        parsed = self.parse_update(update)
        if not parsed:
            return

        logger.info(f"📩 [Telegram] Message from @{parsed.username}: {parsed.text[:50]}...")

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
        return self._build_success_response(
            content, 
            save_result.page_url, 
            summarize_result.template_used,
            summarize_result.output_format_used
        )

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
        logger.info(f"🎬 [YouTube] Processing: {youtube_url}")

        # Get video info
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

        # Save to Notion
        save_result = await self.save_usecase.execute(content)
        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        # Build response with template info
        has_captions = video_info.has_captions and video_info.captions
        return self._build_youtube_response(
            content,
            video_info,
            has_captions,
            save_result.page_url,
            template_used=summarize_result.template_used,
            output_format_used=summarize_result.output_format_used
        )

    def _build_success_response(
        self, 
        content: Content, 
        page_url: Optional[str] = None, 
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
            response += f"\n\n📄 Notion 連結：{page_url}"

        return response

    def _build_youtube_response(
        self,
        content,
        video_info,
        has_captions: bool,
        page_url: Optional[str] = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:
        """Build YouTube success response."""
        return ResponseBuilder.build_youtube_response(
            content=content,
            video_info=video_info,
            has_captions=has_captions,
            page_url=page_url,
            template_used=template_used,
            output_format_used=output_format_used
        )

    async def _handle_voice_message(self, voice: dict, chat_id: int) -> str:
        """
        Handle voice message with Whisper transcription.

        Args:
            voice: Voice object from Telegram update
            chat_id: Chat ID for sending messages

        Returns:
            Response message string
        """
        if not self.whisper_service:
            return "❌ 語音功能未啟用"

        try:
            file_id = voice.get("file_id")
            duration = voice.get("duration", 0)

            logger.info(f"🎙️ [Telegram] Voice file_id: {file_id}, duration: {duration}s")

            # Get file path from Telegram
            file_info = await self._get_file_info(file_id)
            if not file_info:
                return "❌ 無法取得音檔資訊"

            file_path = file_info.get("file_path")
            if not file_path:
                return "❌ 無法取得音檔路徑"

            # Download file
            file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            audio_bytes = await self._download_file(file_url)
            if not audio_bytes:
                return "❌ 無法下載音檔"

            logger.info(f"🎙️ [Telegram] Downloaded {len(audio_bytes)} bytes")

            # Transcribe with Whisper
            result = await self.whisper_service.transcribe(
                audio_bytes,
                filename="voice.ogg"  # Telegram uses ogg format
            )

            if not result.success:
                return f"❌ 語音轉文字失敗：{result.error_message}"

            transcribed_text = result.text
            logger.info(f"🎙️ [Telegram] Transcribed: {transcribed_text[:50]}...")

            # Step 3: Summarize via SummarizeUseCase (NEW - uses template system)
            summarize_result = await self.summarize_usecase.execute(
                raw_input=transcribed_text,
                input_type=ContentType.AUDIO,
                audio_transcription=transcribed_text,
                audio_duration=duration
            )

            if not summarize_result.success:
                return f"✅ 語音轉文字完成（摘要失敗）：\n\n{transcribed_text}"

            content = summarize_result.content

            # Save to Notion
            save_result = await self.save_usecase.execute(content)

            if not save_result.success:
                return f"❌ 儲存失敗：{save_result.error_message}"

            # Build response
            return self._build_audio_success_response(
                content,
                transcribed_text,
                duration,
                save_result.page_url,
                template_used=summarize_result.template_used,
                output_format_used=summarize_result.output_format_used
            )

        except Exception as e:
            logger.error(f"❌ [Telegram] Voice error: {e}")
            return f"❌ 處理語音訊息時發生錯誤：{str(e)}"

    async def _get_file_info(self, file_id: str) -> Optional[dict]:
        """Get file info from Telegram API."""
        try:
            url = f"{self.api_base}/getFile"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json={"file_id": file_id})
                response.raise_for_status()
                data = response.json()
                if data.get("ok"):
                    return data.get("result")
        except Exception as e:
            logger.error(f"❌ [Telegram] getFile error: {e}")
        return None

    async def _download_file(self, url: str) -> Optional[bytes]:
        """Download file from URL."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"❌ [Telegram] Download error: {e}")
        return None

    def _build_audio_success_response(
        self,
        content,
        transcription: str,
        duration: float,
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

    async def _handle_document_message(self, document: dict, chat_id: int) -> str:
        """
        Handle document/file message with text extraction and AI summarization.

        Args:
            document: Document object from Telegram update
            chat_id: Chat ID for sending messages

        Returns:
            Response message string
        """
        if not self.document_extractor:
            return "❌ 文件處理功能未啟用"

        try:
            file_id = document.get("file_id")
            file_name = document.get("file_name", "unknown")
            tg_mime_type = document.get("mime_type", "")

            # Detect MIME from filename (more reliable than Telegram's mime_type)
            mime_type = self.document_extractor.detect_mime_type(file_name) or tg_mime_type

            if not self.document_extractor.is_supported(mime_type=mime_type, filename=file_name):
                supported = "PDF, DOCX, XLSX, PPTX, CSV, TXT"
                return f"❌ 不支援的檔案格式。\n目前支援：{supported}"

            # Step 1: Download file from Telegram
            file_info = await self._get_file_info(file_id)
            if not file_info:
                return "❌ 無法取得檔案資訊"

            file_path = file_info.get("file_path")
            if not file_path:
                return "❌ 無法取得檔案路徑"

            file_url_tg = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            file_data = await self._download_file(file_url_tg)
            if not file_data:
                return "❌ 無法下載檔案"

            logger.info(f"📄 [Telegram] Downloaded: {file_name} ({len(file_data)} bytes)")

            # Step 2: Upload to Google Drive (if available)
            file_url = None
            if self.drive_service:
                upload_result = self.drive_service.upload_image(
                    image_data=file_data,
                    filename=file_name,
                    mime_type=mime_type
                )
                if upload_result.success:
                    file_url = upload_result.file_url
                    logger.info(f"📁 [Telegram] Uploaded to Drive: {file_url}")
                else:
                    logger.warning(f"⚠️ [Telegram] Drive upload failed: {upload_result.error_message}")

            # Step 3: Extract text
            extraction_result = await self.document_extractor.extract(file_data, mime_type, ai_service=self.ai_service)
            if not extraction_result.success:
                return f"❌ 文字萃取失敗：{extraction_result.error_message}"

            page_info = f"（共 {extraction_result.page_count} 頁）" if extraction_result.page_count else ""
            logger.info(f"📄 [Telegram] Extracted {len(extraction_result.text)} chars {page_info}")

            # Step 4: Summarize
            summarize_result = await self.summarize_usecase.execute(
                raw_input=extraction_result.text,
                input_type=ContentType.FILE,
                file_name=file_name,
                file_url=file_url,
                extracted_text=extraction_result.text
            )

            if not summarize_result.success:
                return f"❌ 處理失敗：{summarize_result.error_message}"

            content = summarize_result.content

            # Step 5: Save to Notion
            save_result = await self.save_usecase.execute(content)

            if not save_result.success:
                return f"❌ 儲存失敗：{save_result.error_message}"

            return ResponseBuilder.build_file_response(
                content=content,
                page_url=save_result.page_url,
                page_count=extraction_result.page_count,
                template_used=summarize_result.template_used,
                output_format_used=summarize_result.output_format_used
            )

        except Exception as e:
            logger.error(f"❌ [Telegram] Document error: {e}")
            return f"❌ 處理文件時發生錯誤：{str(e)}"

    async def _handle_photo_message(self, photo: list, caption: str, chat_id: int) -> str:
        """
        Handle photo message with AI image analysis and Google Drive upload.

        Args:
            photo: Photo array from Telegram (multiple sizes)
            caption: Optional caption text
            chat_id: Chat ID for sending messages

        Returns:
            Response message string
        """
        import uuid

        # Check if drive_service is available (preferred method with Drive upload)
        if self.drive_service:
            try:
                # Telegram sends multiple photo sizes, get the largest one
                largest_photo = photo[-1] if photo else None
                if not largest_photo:
                    return "❌ 無法取得圖片"

                file_id = largest_photo.get("file_id")
                logger.info(f"📸 [Telegram] Photo file_id: {file_id}")

                # Get file path from Telegram
                file_info = await self._get_file_info(file_id)
                if not file_info:
                    return "❌ 無法取得圖片資訊"

                file_path = file_info.get("file_path")
                if not file_path:
                    return "❌ 無法取得圖片路徑"

                # Download file
                file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                image_bytes = await self._download_file(file_url)
                if not image_bytes:
                    return "❌ 無法下載圖片"

                logger.info(f"📸 [Telegram] Downloaded {len(image_bytes)} bytes")

                # Determine MIME type from file extension
                mime_type = "image/jpeg"
                ext = ".jpg"
                if file_path.endswith(".png"):
                    mime_type = "image/png"
                    ext = ".png"
                elif file_path.endswith(".gif"):
                    mime_type = "image/gif"
                    ext = ".gif"
                elif file_path.endswith(".webp"):
                    mime_type = "image/webp"
                    ext = ".webp"

                # Generate filename
                filename = f"telegram_photo_{uuid.uuid4().hex[:8]}{ext}"

                # Step 1: Upload to Google Drive first
                upload_result = self.drive_service.upload_image(
                    image_data=image_bytes,
                    filename=filename,
                    mime_type=mime_type
                )

                if not upload_result.success:
                    return f"❌ 上傳圖片失敗：{upload_result.error_message}"

                # Step 2: Analyze and summarize via SummarizeUseCase (NEW - uses template system)
                summarize_result = await self.summarize_usecase.execute(
                    raw_input="[Telegram Photo]",
                    input_type=ContentType.IMAGE,
                    image_data=image_bytes,
                    image_mime_type=mime_type,
                    image_url=upload_result.file_url
                )

                if not summarize_result.success:
                    return f"❌ 處理失敗：{summarize_result.error_message}"

                content = summarize_result.content
                content.image_url = upload_result.file_url

                # Update content with caption if provided
                if caption:
                    content.summary = f"📝 用戶說明：{caption}\n\n🖼️ 圖片分析：\n{content.image_description}"

                # Step 3: Save to Notion
                save_result = await self.save_usecase.execute(content)

                if not save_result.success:
                    return f"❌ 儲存失敗：{save_result.error_message}"

                # Build response with template info
                return self._build_photo_success_response(
                    content,
                    caption,
                    save_result.page_url,
                    template_used=summarize_result.template_used,
                    output_format_used=summarize_result.output_format_used
                )

            except Exception as e:
                logger.error(f"❌ [Telegram] Photo error: {e}")
                return f"❌ 處理圖片時發生錯誤：{str(e)}"

        # Fallback: Use ai_service directly (no Drive upload)
        elif self.ai_service:
            return await self._handle_photo_message_fallback(photo, caption, chat_id)

        else:
            return "❌ 圖片處理功能未啟用"

    async def _handle_photo_message_fallback(self, photo: list, caption: str, chat_id: int) -> str:
        """Fallback photo handling without Google Drive upload."""
        from src.domain.content import create_image_content

        try:
            largest_photo = photo[-1] if photo else None
            if not largest_photo:
                return "❌ 無法取得圖片"

            file_id = largest_photo.get("file_id")
            file_info = await self._get_file_info(file_id)
            if not file_info:
                return "❌ 無法取得圖片資訊"

            file_path = file_info.get("file_path")
            if not file_path:
                return "❌ 無法取得圖片路徑"

            file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            image_bytes = await self._download_file(file_url)
            if not image_bytes:
                return "❌ 無法下載圖片"

            mime_type = "image/jpeg"
            if file_path.endswith(".png"):
                mime_type = "image/png"

            analysis_result = await self.ai_service.analyze_image(image_bytes, mime_type)
            if not analysis_result.success:
                return f"❌ 圖片分析失敗：{analysis_result.error_message}"

            content = create_image_content(
                image_url="",  # No Drive URL in fallback mode
                image_description=analysis_result.description,
                title=analysis_result.title,
                tags=analysis_result.tags
            )

            if caption:
                content.summary = f"📝 用戶說明：{caption}\n\n🖼️ 圖片分析：\n{analysis_result.description}"

            save_result = await self.save_usecase.execute(content)
            if not save_result.success:
                return f"❌ 儲存失敗：{save_result.error_message}"

            return self._build_photo_success_response(content, caption, save_result.page_url)

        except Exception as e:
            logger.error(f"❌ [Telegram] Photo fallback error: {e}")
            return f"❌ 處理圖片時發生錯誤：{str(e)}"

    def _build_photo_success_response(
        self,
        content,
        caption: str,
        page_url: Optional[str] = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:
        """Build success response for photo processing."""
        return ResponseBuilder.build_image_response(
            content=content,
            page_url=page_url,
            caption=caption if caption else None,
            template_used=template_used,
            output_format_used=output_format_used
        )
