"""
Main Entry Point: FastAPI Application

Assembles all components and exposes webhook endpoint.
"""

import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError

# Load environment variables
load_dotenv()

# Infrastructure imports
from src.infrastructure.web_scraper import WebScraper
from src.infrastructure.gemini_service import GeminiService
from src.infrastructure.notion_repo import NotionRepository
from src.infrastructure.line_handler import LineMessageHandler
from src.infrastructure.social_detector import SocialDetector
from src.infrastructure.apify_scraper import ApifyScraper

# UseCase imports
from src.usecase.summarize import SummarizeUseCase
from src.usecase.save_to_notion import SaveToNotionUseCase


# Configuration
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")


def validate_config():
    """Validate required environment variables."""
    required = {
        "LINE_CHANNEL_ACCESS_TOKEN": LINE_CHANNEL_ACCESS_TOKEN,
        "LINE_CHANNEL_SECRET": LINE_CHANNEL_SECRET,
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "NOTION_API_KEY": NOTION_API_KEY,
        "NOTION_DATABASE_ID": NOTION_DATABASE_ID,
        "APIFY_API_TOKEN": APIFY_API_TOKEN,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


# Initialize components (lazy loading)
_handler: LineMessageHandler = None
_parser: WebhookParser = None


def get_handler() -> LineMessageHandler:
    """Get or create the message handler."""
    global _handler
    if _handler is None:
        # Infrastructure
        web_scraper = WebScraper()
        social_detector = SocialDetector()
        apify_scraper = ApifyScraper(api_token=APIFY_API_TOKEN)
        gemini_service = GeminiService(api_key=GEMINI_API_KEY)
        notion_repo = NotionRepository(
            api_key=NOTION_API_KEY,
            database_id=NOTION_DATABASE_ID
        )

        # UseCases
        summarize_usecase = SummarizeUseCase(
            ai_service=gemini_service,
            web_scraper=web_scraper,
            social_scraper=apify_scraper
        )
        save_usecase = SaveToNotionUseCase(repository=notion_repo)

        # Handler
        _handler = LineMessageHandler(
            channel_access_token=LINE_CHANNEL_ACCESS_TOKEN,
            summarize_usecase=summarize_usecase,
            save_usecase=save_usecase,
            social_detector=social_detector
        )
    return _handler


def get_parser() -> WebhookParser:
    """Get or create the webhook parser."""
    global _parser
    if _parser is None:
        _parser = WebhookParser(channel_secret=LINE_CHANNEL_SECRET)
    return _parser


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    validate_config()
    print("🚀 Line Bot Content Saver started!")
    print(f"📦 Notion Database ID: {NOTION_DATABASE_ID[:8]}...")
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
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Queue events for background processing (don't initialize handler here)
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            # Process in background - handler will be initialized there
            background_tasks.add_task(
                process_message,
                user_id=event.source.user_id,
                text=event.message.text.strip(),
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

        # Process and get result
        result = await handler.handle_message_with_push(user_id, text)

        # Send result via push message
        await handler.push_message(user_id, result)

        print(f"✅ Message processed successfully for {user_id}")

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        error_msg = f"❌ 發生錯誤：{str(e)}"
        await handler.push_message(user_id, error_msg)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
