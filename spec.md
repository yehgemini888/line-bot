# 📋 Spec: Line Bot Content Saver

## 1. Vision
一個多平台 Bot（Line / Telegram），接收使用者傳送的文字、網址、社群貼文、YouTube 影片或圖片，
使用 AI 進行摘要分析，並儲存至 Notion 資料庫。

## 2. Current Status: ✅ Phase 7.7 Completed

### 已完成功能
- ✅ 文字訊息摘要
- ✅ 網址內容抓取與摘要
- ✅ AI 自動產生標題、摘要、標籤
- ✅ 儲存至 Notion Database
- ✅ 社群貼文偵測與摘要 (Facebook / Threads)
- ✅ 圖片訊息處理 (Line / Telegram / 圖片 URL)
- ✅ 圖片上傳至 Google Drive (OAuth 2.0)
- ✅ 多 AI 提供者支援 (Gemini / OpenAI / 自動切換)
- ✅ **YouTube 影片摘要 (Apify + 繁中字幕)**
- ✅ **Telegram Bot 整合 (無訊息限制 + 圖片上傳 Drive)**
- ✅ **SPA 網站支援 (Jina Reader)**
- ✅ **語音訊息支援 (OpenAI Whisper)**
- ✅ **Prompt Template System (Notion 管理)**
- ✅ **繁體中文 Schema 優化 (動態生成)**

### 生產環境
| 平台 | URL / ID |
|------|----------|
| Zeabur | https://line-bot9.zeabur.app |
| Line Webhook | /webhook |
| Telegram Webhook | /telegram/webhook |
| Telegram Bot | @benson_inspiration_bot |

### 待開發功能 (Backlog)
- ⬜ 更多社群平台 (IG/Twitter)
- ⬜ Podcast / PDF 摘要
- ⬜ 自訂摘要風格

## 3. Tech Stack
| Layer          | Technology                     | Status |
|----------------|--------------------------------|--------|
| Language       | Python 3.10+                   | ✅ |
| Web Framework  | FastAPI                        | ✅ |
| Line SDK       | line-bot-sdk v3                | ✅ |
| Telegram       | httpx (直接呼叫 API)           | ✅ |
| AI (Gemini)    | google-generativeai            | ✅ |
| AI (OpenAI)    | openai (GPT-4o-mini)           | ✅ |
| AI Fallback    | FallbackAIService              | ✅ |
| YouTube        | Apify streamers/youtube-scraper| ✅ |
| Notion         | notion-client                  | ✅ |
| Social Scraper | apify-client                   | ✅ |
| Cloud Storage  | Google Drive API (OAuth 2.0)   | ✅ |
| SPA Scraper    | Jina Reader API                | ✅ |
| Voice STT      | OpenAI Whisper API             | ✅ |
| Deployment     | Zeabur                         | ✅ |

## 4. Architecture
```
┌─────────────────────────────────────────────────────────┐
│                      main.py                            │
│                   (FastAPI Entry)                       │
├──────────────────┬──────────────────────────────────────┤
│  /webhook (Line) │  /telegram/webhook (Telegram)       │
└────────┬─────────┴──────────────┬───────────────────────┘
         │                        │
┌────────▼────────┐      ┌────────▼─────────┐
│ LineMessageHandler│      │ TelegramHandler  │
└────────┬────────┘      └────────┬─────────┘
         │                        │
         └───────────┬────────────┘
                     │ (共用 UseCase)
         ┌───────────▼───────────┐
         │   SummarizeUseCase    │
         │   SaveToNotionUseCase │
         │   YouTubeService      │
         └───────────────────────┘
```

## 5. Directory Structure
```
Line bot/
├── src/
│   ├── domain/
│   │   └── content.py          # Content, ContentType, SocialPlatform
│   ├── usecase/
│   │   ├── summarize.py        # SummarizeUseCase
│   │   ├── save_to_notion.py   # SaveToNotionUseCase
│   │   └── process_image.py    # ProcessImageUseCase
│   ├── infrastructure/
│   │   ├── line_handler.py     # Line Webhook Handler
│   │   ├── telegram_handler.py # Telegram Webhook Handler ✅ NEW
│   │   ├── youtube_service.py  # YouTube 影片+字幕 (Apify) ✅ NEW
│   │   ├── gemini_service.py   # Gemini AI
│   │   ├── openai_service.py   # OpenAI
│   │   ├── fallback_ai_service.py # AI 自動切換
│   │   ├── notion_repo.py      # Notion Repository
│   │   ├── web_scraper.py      # URL Content Fetcher
│   │   ├── social_detector.py  # 社群/YouTube URL 偵測
│   │   ├── apify_scraper.py    # 社群貼文爬取 (Apify)
│   │   ├── drive_service.py    # Google Drive 上傳
│   │   └── image_detector.py   # 圖片 URL 偵測
│   └── main.py
├── requirements.txt
├── spec.md
└── active_plan.md
```

## 6. Domain Model
```python
class ContentType(Enum):
    TEXT = "text"
    URL = "url"
    SOCIAL = "social"
    IMAGE = "image"
    YOUTUBE = "youtube"
    AUDIO = "audio"  # ✅ NEW

@dataclass
class Content:
    id: str
    content_type: ContentType
    raw_content: str
    source_url: Optional[str]
    title: Optional[str]
    summary: Optional[str]
    tags: List[str]
    # Social metadata
    author: Optional[str]
    likes: Optional[int]
    # Image metadata
    image_url: Optional[str]
    image_description: Optional[str]
    # YouTube metadata ✅ NEW
    video_duration: Optional[str]
    channel_name: Optional[str]
```

## 7. API Endpoints
| Method | Path               | Description              |
|--------|-------------------|--------------------------|
| POST   | /webhook          | Line Webhook             |
| POST   | /telegram/webhook | Telegram Webhook ✅ NEW  |
| GET    | /health           | Health check             |

## 8. Environment Variables
| Variable                    | Description                    |
|-----------------------------|--------------------------------|
| LINE_CHANNEL_ACCESS_TOKEN   | Line Channel Access Token      |
| LINE_CHANNEL_SECRET         | Line Channel Secret            |
| TELEGRAM_BOT_TOKEN          | Telegram Bot Token ✅ NEW      |
| GEMINI_API_KEY              | Google Gemini API Key          |
| OPENAI_API_KEY              | OpenAI API Key                 |
| AI_PROVIDER                 | AI 提供者 (auto/gemini/openai) |
| NOTION_API_KEY              | Notion Integration Token       |
| NOTION_DATABASE_ID          | Notion Database ID             |
| APIFY_API_TOKEN             | Apify API Token                |
| GOOGLE_CREDENTIALS_BASE64   | Google OAuth credentials       |
| GOOGLE_TOKEN_BASE64         | Google OAuth token             |
| GOOGLE_DRIVE_FOLDER_ID      | Google Drive 資料夾 ID         |

## 9. Notion Schema
| Field             | Type         | Description          |
|-------------------|--------------|----------------------|
| Title             | title        | AI 產生的標題        |
| Summary           | rich_text    | AI 摘要              |
| Source URL        | url          | 來源網址             |
| Type              | select       | text/url/social/image/youtube |
| Tags              | multi_select | AI 自動標籤          |
| Duration          | rich_text    | 影片時長 ✅ NEW      |
| Channel           | rich_text    | 頻道名稱 ✅ NEW      |
| Image URL         | url          | 圖片連結 (Drive)     |

## 10. Apify Actors
| Platform | Actor ID                        |
|----------|--------------------------------|
| Facebook | apify/facebook-posts-scraper   |
| Threads  | sinam7/threads-post-scraper    |
| YouTube  | streamers/youtube-scraper ✅ NEW |
