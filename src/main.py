"""
Main Entry Point: FastAPI Application

Assembles all components and exposes webhook endpoint.
"""

import os
import base64
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent, AudioMessageContent
from linebot.v3.exceptions import InvalidSignatureError

# Load environment variables
load_dotenv()

# Infrastructure imports
from src.infrastructure.web_scraper import WebScraper
from src.infrastructure.gemini_service import GeminiService
from src.infrastructure.openai_service import OpenAIService
from src.infrastructure.notion_repo import NotionRepository
from src.infrastructure.fallback_ai_service import FallbackAIService
from src.infrastructure.line_handler import LineMessageHandler
from src.infrastructure.social_detector import SocialDetector
from src.infrastructure.apify_scraper import ApifyScraper
from src.infrastructure.image_detector import ImageDetector
from src.infrastructure.drive_service import GoogleDriveService
from src.infrastructure.youtube_service import YouTubeService
from src.infrastructure.telegram_handler import TelegramHandler
from src.infrastructure.whisper_service import WhisperService

# UseCase imports
from src.usecase.summarize import SummarizeUseCase
from src.usecase.save_to_notion import SaveToNotionUseCase
from src.usecase.process_image import ProcessImageUseCase

# Domain imports
from src.domain.content import ContentType


# Configuration
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").lower()  # "auto", "gemini", or "openai"
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_TEMPLATE_DATABASE_ID = os.getenv("NOTION_TEMPLATE_DATABASE_ID")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def validate_config():
    """Validate required environment variables."""
    required = {
        "LINE_CHANNEL_ACCESS_TOKEN": LINE_CHANNEL_ACCESS_TOKEN,
        "LINE_CHANNEL_SECRET": LINE_CHANNEL_SECRET,
        "NOTION_API_KEY": NOTION_API_KEY,
        "NOTION_DATABASE_ID": NOTION_DATABASE_ID,
        "APIFY_API_TOKEN": APIFY_API_TOKEN,
    }

    # Validate AI provider configuration
    if AI_PROVIDER == "auto":
        required["GEMINI_API_KEY"] = GEMINI_API_KEY
        required["OPENAI_API_KEY"] = OPENAI_API_KEY
    elif AI_PROVIDER == "openai":
        required["OPENAI_API_KEY"] = OPENAI_API_KEY
    else:
        required["GEMINI_API_KEY"] = GEMINI_API_KEY

    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def get_ai_service():
    """Get AI service based on AI_PROVIDER setting."""
    if AI_PROVIDER == "auto":
        return FallbackAIService(
            gemini_api_key=GEMINI_API_KEY,
            openai_api_key=OPENAI_API_KEY
        )
    elif AI_PROVIDER == "openai":
        return OpenAIService(api_key=OPENAI_API_KEY)
    else:
        return GeminiService(api_key=GEMINI_API_KEY)


# Initialize components (lazy loading)
_handler: LineMessageHandler = None
_telegram_handler: TelegramHandler = None
_parser: WebhookParser = None
_process_image_usecase: ProcessImageUseCase = None
_image_enabled: bool = False


def get_process_image_usecase() -> ProcessImageUseCase:
    """Get or create the process image use case."""
    global _process_image_usecase, _image_enabled
    if _process_image_usecase is None and _image_enabled:
        try:
            # Ensure we use the latest credentials file path (it might have been updated in lifespan)
            current_credentials_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
            
            # Check for restored token file
            token_file = "/tmp/token.json" if os.path.exists("/tmp/token.json") else None
            
            ai_service = get_ai_service()
            drive_service = GoogleDriveService(
                credentials_file=current_credentials_file,
                folder_id=GOOGLE_DRIVE_FOLDER_ID,
                token_file=token_file
            )
            notion_repo = NotionRepository(
                api_key=NOTION_API_KEY,
                database_id=NOTION_DATABASE_ID
            )
            _process_image_usecase = ProcessImageUseCase(
                image_analyzer=ai_service,
                image_uploader=drive_service,
                repository=notion_repo
            )
        except Exception as e:
            print(f"⚠️ Image processing init failed, disabling: {e}")
            _image_enabled = False
    return _process_image_usecase


def get_handler() -> LineMessageHandler:
    """Get or create the message handler."""
    global _handler
    if _handler is None:
        # Infrastructure
        web_scraper = WebScraper()
        social_detector = SocialDetector()
        image_detector = ImageDetector()
        apify_scraper = ApifyScraper(api_token=APIFY_API_TOKEN)
        ai_service = get_ai_service()
        youtube_service = YouTubeService(api_token=APIFY_API_TOKEN)
        notion_repo = NotionRepository(
            api_key=NOTION_API_KEY,
            database_id=NOTION_DATABASE_ID
        )

        # UseCases (with Notion client for template loading)
        summarize_usecase = SummarizeUseCase(
            ai_service=ai_service,
            web_scraper=web_scraper,
            social_scraper=apify_scraper,
            notion_client=notion_repo.client if NOTION_TEMPLATE_DATABASE_ID else None,
            template_database_id=NOTION_TEMPLATE_DATABASE_ID
        )
        save_usecase = SaveToNotionUseCase(repository=notion_repo)
        process_image_usecase = get_process_image_usecase()

        # Whisper Service (for voice messages)
        whisper_service = None
        if OPENAI_API_KEY:
            whisper_service = WhisperService(api_key=OPENAI_API_KEY)
            print("🎙️ Whisper service: ENABLED")

        # Handler
        _handler = LineMessageHandler(
            channel_access_token=LINE_CHANNEL_ACCESS_TOKEN,
            summarize_usecase=summarize_usecase,
            save_usecase=save_usecase,
            social_detector=social_detector,
            image_detector=image_detector,
            process_image_usecase=process_image_usecase,
            youtube_service=youtube_service,
            ai_service=ai_service,
            whisper_service=whisper_service
        )
    return _handler


def get_parser() -> WebhookParser:
    """Get or create the webhook parser."""
    global _parser
    if _parser is None:
        _parser = WebhookParser(channel_secret=LINE_CHANNEL_SECRET)
    return _parser


def get_telegram_handler() -> TelegramHandler:
    """Get or create the Telegram handler."""
    global _telegram_handler
    if _telegram_handler is None and TELEGRAM_BOT_TOKEN:
        # Infrastructure (reuse same components)
        web_scraper = WebScraper()
        social_detector = SocialDetector()
        image_detector = ImageDetector()
        apify_scraper = ApifyScraper(api_token=APIFY_API_TOKEN)
        ai_service = get_ai_service()
        youtube_service = YouTubeService(api_token=APIFY_API_TOKEN)
        notion_repo = NotionRepository(
            api_key=NOTION_API_KEY,
            database_id=NOTION_DATABASE_ID
        )

        # Whisper Service (for voice messages)
        whisper_service = None
        if OPENAI_API_KEY:
            whisper_service = WhisperService(api_key=OPENAI_API_KEY)

        # UseCases (with Notion client for template loading)
        summarize_usecase = SummarizeUseCase(
            ai_service=ai_service,
            web_scraper=web_scraper,
            social_scraper=apify_scraper,
            notion_client=notion_repo.client if NOTION_TEMPLATE_DATABASE_ID else None,
            template_database_id=NOTION_TEMPLATE_DATABASE_ID
        )
        save_usecase = SaveToNotionUseCase(repository=notion_repo)
        
        # Get ProcessImageUseCase and Drive service
        process_image_usecase = get_process_image_usecase()
        drive_service = None
        if process_image_usecase:
            drive_service = process_image_usecase.image_uploader

        # Telegram Handler
        _telegram_handler = TelegramHandler(
            bot_token=TELEGRAM_BOT_TOKEN,
            summarize_usecase=summarize_usecase,
            save_usecase=save_usecase,
            social_detector=social_detector,
            image_detector=image_detector,
            youtube_service=youtube_service,
            ai_service=ai_service,
            whisper_service=whisper_service,
            process_image_usecase=process_image_usecase,
            drive_service=drive_service
        )
    return _telegram_handler


def restore_google_token():
    """Restore token.json from Base64 environment variable (for cloud deployment with OAuth)."""
    token_b64 = os.getenv("GOOGLE_TOKEN_BASE64")
    if token_b64:
        token_path = "/tmp/token.json"
        try:
            with open(token_path, "w") as f:
                f.write(base64.b64decode(token_b64).decode("utf-8"))
            print(f"☁️ Google token restored to {token_path}")
        except Exception as e:
            print(f"❌ Failed to restore Google token: {e}")

def restore_google_credentials():
    """Restore credentials.json from Base64 environment variable (for cloud deployment)."""
    global GOOGLE_SERVICE_ACCOUNT_FILE
    creds_b64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
    if creds_b64:
        creds_path = "/tmp/credentials.json"
        try:
            # Decode Base64
            json_str = base64.b64decode(creds_b64).decode("utf-8")
            
            # Parse JSON to sanitize private_key
            import json
            creds_data = json.loads(json_str)
            
            # Fix private_key newlines if they are escaped (e.g. "\\n" -> "\n")
            if "private_key" in creds_data:
                private_key = creds_data["private_key"]
                if "\\n" in private_key:
                    creds_data["private_key"] = private_key.replace("\\n", "\n")
            
            # Write sanitized JSON to file
            with open(creds_path, "w") as f:
                json.dump(creds_data, f, indent=2)
                
            GOOGLE_SERVICE_ACCOUNT_FILE = creds_path
            os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"] = creds_path
            print(f"☁️ Google credentials restored and sanitized at {creds_path}")
            
        except Exception as e:
            print(f"❌ Failed to restore Google credentials: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _image_enabled
    # Startup
    restore_google_credentials()
    restore_google_token()
    validate_config()
    print("🚀 Line Bot Content Saver started!")
    print(f"📦 Notion Database ID: {NOTION_DATABASE_ID[:8]}...")
    if NOTION_TEMPLATE_DATABASE_ID:
        print(f"📋 Notion Template DB: {NOTION_TEMPLATE_DATABASE_ID[:8]}...")
    else:
        print("⚠️ Notion Template DB: NOT CONFIGURED (using defaults)")
    print(f"🤖 AI Provider: {AI_PROVIDER.upper()}")

    # Check if image processing is configured
    if GOOGLE_SERVICE_ACCOUNT_FILE and GOOGLE_DRIVE_FOLDER_ID:
        if os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
            _image_enabled = True
            print("🖼️ Image processing: ENABLED")
        else:
            print(f"⚠️ Image processing: DISABLED (service account file not found: {GOOGLE_SERVICE_ACCOUNT_FILE})")
    else:
        print("⚠️ Image processing: DISABLED (missing GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_DRIVE_FOLDER_ID)")

    yield
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Line Bot Content Saver",
    description="Save and summarize content to Notion via Line",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Line Bot is running"}


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Line Webhook endpoint.

    Receives events from Line and processes messages.
    Returns 200 OK immediately, processes in background.
    """
    # Get request body and signature
    body = await request.body()
    body_str = body.decode("utf-8")
    signature = request.headers.get("X-Line-Signature", "")

    print(f"📥 Webhook received (body: {len(body_str)} bytes)")

    # Parse events (fast operation)
    parser = get_parser()
    try:
        events = parser.parse(body_str, signature)
    except InvalidSignatureError:
        print("❌ Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        print(f"❌ Error parsing webhook events: {e}")
        # Return 200 OK to Line even if parsing fails to avoid retry storms
        return {"status": "ok", "error": str(e)}

    # Queue events for background processing (don't initialize handler here)
    print(f"📋 Received {len(events)} events")
    for event in events:
        if isinstance(event, MessageEvent):
            if isinstance(event.message, TextMessageContent):
                # Process text message in background
                background_tasks.add_task(
                    process_message,
                    user_id=event.source.user_id,
                    text=event.message.text.strip(),
                    reply_token=event.reply_token
                )
            elif isinstance(event.message, ImageMessageContent):
                # Process image message in background
                background_tasks.add_task(
                    process_image_message,
                    user_id=event.source.user_id,
                    message_id=event.message.id,
                    reply_token=event.reply_token
                )
            elif isinstance(event.message, AudioMessageContent):
                # Process audio/voice message in background
                background_tasks.add_task(
                    process_audio_message,
                    user_id=event.source.user_id,
                    message_id=event.message.id,
                    reply_token=event.reply_token
                )

    # Return immediately - Line requires fast response
    return {"status": "ok"}


async def process_message(
    user_id: str,
    text: str,
    reply_token: str
):
    """
    Process message in background.

    Args:
        user_id: User ID for push message
        text: Message text
        reply_token: Reply token (may expire)
    """
    # Get handler (lazy initialization happens here, not in webhook)
    handler = get_handler()

    try:
        print(f"⚙️ Processing message from {user_id}: {text[:50]}...")

        # Check if text contains an image URL
        content_type, _, image_url = handler._analyze_content(text)

        if content_type == ContentType.IMAGE and image_url:
            # Process as image URL
            result = await handler.handle_image_url_with_push(user_id, image_url)
        else:
            # Process as normal text/URL
            result = await handler.handle_message_with_push(user_id, text)

        # Send result via push message
        await handler.push_message(user_id, result)

        print(f"✅ Message processed successfully for {user_id}")

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        error_msg = f"❌ 發生錯誤：{str(e)}"
        await handler.push_message(user_id, error_msg)


async def process_image_message(
    user_id: str,
    message_id: str,
    reply_token: str
):
    """
    Process image message in background.

    Args:
        user_id: User ID for push message
        message_id: Line message ID containing the image
        reply_token: Reply token (may expire)
    """
    # Get handler (lazy initialization happens here, not in webhook)
    handler = get_handler()

    try:
        print(f"📸 Processing image from {user_id} (message_id: {message_id})")

        # Process image
        result = await handler.handle_image_message_with_push(user_id, message_id)

        # Send result via push message
        await handler.push_message(user_id, result)

        print(f"✅ Image processed successfully for {user_id}")

    except Exception as e:
        print(f"❌ Error processing image: {e}")
        error_msg = f"❌ 發生錯誤：{str(e)}"
        await handler.push_message(user_id, error_msg)


async def process_audio_message(
    user_id: str,
    message_id: str,
    reply_token: str
):
    """
    Process audio/voice message in background.

    Args:
        user_id: User ID for push message
        message_id: Message ID for downloading audio
        reply_token: Reply token (may expire)
    """
    handler = get_handler()

    try:
        print(f"🎙️ Processing audio from {user_id}: {message_id}")

        # Send processing message
        await handler.push_message(user_id, "收到語音訊息！正在轉錄中... 🎙️")

        # Process audio
        result = await handler.handle_audio_message(user_id, message_id)

        # Send result via push message
        await handler.push_message(user_id, result)

        print(f"✅ Audio processed successfully for {user_id}")

    except Exception as e:
        print(f"❌ Error processing audio: {e}")
        error_msg = f"❌ 處理語音訊息時發生錯誤：{str(e)}"
        await handler.push_message(user_id, error_msg)


# ============================================
# Telegram Webhook
# ============================================

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Telegram Webhook endpoint.

    Receives updates from Telegram and processes messages.
    Returns 200 OK immediately, processes in background.
    """
    try:
        update = await request.json()
        print(f"📩 [Telegram] Webhook received")

        # Process in background
        background_tasks.add_task(process_telegram_update, update)

        return {"status": "ok"}
    except Exception as e:
        print(f"❌ [Telegram] Webhook error: {e}")
        return {"status": "ok", "error": str(e)}


async def process_telegram_update(update: dict):
    """Process Telegram update in background."""
    handler = get_telegram_handler()

    if handler is None:
        print("❌ [Telegram] Handler not initialized (missing TELEGRAM_BOT_TOKEN)")
        return

    try:
        await handler.handle_update(update)
    except Exception as e:
        print(f"❌ [Telegram] Error processing update: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
