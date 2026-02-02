# 📋 Spec: Line Bot Content Saver

## 1. Vision
一個 Line Bot，接收使用者傳送的文字、網址或社群貼文，
使用 Gemini AI 進行摘要分析，並儲存至 Notion 資料庫。

## 2. Current Status: ✅ Phase 4 Completed

### 已完成功能
- ✅ 文字訊息摘要
- ✅ 網址內容抓取與摘要
- ✅ AI 自動產生標題、摘要、標籤
- ✅ 儲存至 Notion Database
- ✅ 本地開發環境 (ngrok / VS Code Port Forwarding)
- ✅ 社群貼文偵測 (Facebook / Threads)
- ✅ 社群貼文爬取 (Apify)
- ✅ 智慧 URL 提取 (支援「文字 + URL」混合輸入)

### 待開發功能
- ⬜ 圖片處理 (OCR / Vision AI)
- ⬜ 雲端部署 (Railway / Render)
- ⬜ 更多社群平台 (IG/Twitter)
- ⬜ 多語言摘要支援
- ⬜ 自訂摘要風格

## 3. Tech Stack
| Layer          | Technology                     | Status |
|----------------|--------------------------------|--------|
| Language       | Python 3.10+                   | ✅ |
| Web Framework  | FastAPI                        | ✅ |
| Line SDK       | line-bot-sdk v3                | ✅ |
| AI             | google-generativeai (Gemini)   | ✅ |
| Notion         | notion-client                  | ✅ |
| HTTP Client    | httpx                          | ✅ |
| HTML Parser    | beautifulsoup4                 | ✅ |
| Social Scraper | apify-client                   | ✅ |
| Dev Server     | uvicorn                        | ✅ |
| Tunnel         | ngrok / VS Code Port Forward   | ✅ |

## 4. Architecture (Clean Architecture)
```
┌─────────────────────────────────────────────────────────┐
│                      main.py                            │
│                   (FastAPI Entry)                       │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 Infrastructure Layer                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ line_handler │ │gemini_service│ │ notion_repo  │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────┐   │
│  │ web_scraper  │ │social_detector│ │apify_scraper │   │
│  └──────────────┘ └───────────────┘ └──────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    UseCase Layer                         │
│  ┌─────────────────────┐ ┌─────────────────────┐        │
│  │  SummarizeUseCase   │ │ SaveToNotionUseCase │        │
│  └─────────────────────┘ └─────────────────────┘        │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    Domain Layer                          │
│  ┌─────────────────────┐ ┌─────────────────────┐        │
│  │      Content        │ │    ContentType      │        │
│  │     (Entity)        │ │  SocialPlatform     │        │
│  └─────────────────────┘ └─────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

## 5. Directory Structure
```
Line bot/
├── src/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   └── content.py          # Content Entity, ContentType, SocialPlatform
│   ├── usecase/
│   │   ├── __init__.py
│   │   ├── summarize.py        # SummarizeUseCase (支援 SOCIAL 類型)
│   │   └── save_to_notion.py   # SaveToNotionUseCase
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── line_handler.py     # Line Webhook Handler
│   │   ├── gemini_service.py   # Gemini AI Adapter
│   │   ├── notion_repo.py      # Notion Repository
│   │   ├── web_scraper.py      # URL Content Fetcher
│   │   ├── social_detector.py  # 社群網址偵測 (FB/Threads)
│   │   └── apify_scraper.py    # 社群貼文爬取 (Apify)
│   └── main.py                 # FastAPI Entry Point
├── tests/                      # 測試檔案
│   ├── test_social_detector.py
│   └── verify_social.py
├── venv/                       # Python Virtual Environment
├── .env                        # Environment Variables (實際值)
├── .env.example                # Environment Variables (範本)
├── requirements.txt            # Python Dependencies
├── spec.md                     # This File
├── active_plan.md              # Development Plan
├── CLAUDE.md                   # AI Assistant Instructions
└── README.md                   # Quick Start Guide
```

## 6. Domain Model
```python
class SocialPlatform(Enum):
    FACEBOOK = "facebook"
    THREADS = "threads"

class ContentType(Enum):
    TEXT = "text"
    URL = "url"
    SOCIAL = "social"    # Phase 4 ✅
    IMAGE = "image"      # Phase 2 (Future)

@dataclass
class Content:
    id: str
    content_type: ContentType
    raw_content: str
    source_url: Optional[str]
    social_platform: Optional[SocialPlatform]  # Phase 4 ✅
    title: Optional[str]
    summary: Optional[str]
    tags: List[str]
    created_at: datetime
```

## 7. Notion Schema
| Field      | Type         | Description      | Status |
|------------|--------------|------------------|--------|
| Title      | title        | AI 產生的標題    | ✅ |
| Summary    | rich_text    | AI 摘要          | ✅ |
| Content    | rich_text    | 原始內容         | ✅ |
| Source URL | url          | 來源網址         | ✅ |
| Type       | select       | text / url       | ✅ |
| Tags       | multi_select | AI 自動標籤      | ✅ |
| Created    | date         | 建立時間         | ✅ |

## 8. API Endpoints
| Method | Path      | Description          | Status |
|--------|-----------|----------------------|--------|
| POST   | /webhook  | Line Webhook 接收訊息 | ✅ |
| GET    | /health   | Health check         | ✅ |

## 9. Environment Variables
| Variable                    | Description                | Status |
|-----------------------------|----------------------------|--------|
| LINE_CHANNEL_ACCESS_TOKEN   | Line Channel Access Token  | ✅ |
| LINE_CHANNEL_SECRET         | Line Channel Secret        | ✅ |
| GEMINI_API_KEY              | Google Gemini API Key      | ✅ |
| NOTION_API_KEY              | Notion Integration Token   | ✅ |
| NOTION_DATABASE_ID          | Notion Database ID         | ✅ |
| APIFY_API_TOKEN             | Apify API Token (社群爬取) | ✅ |

## 10. Data Flow
```
User sends message to Line Bot
(可包含純文字、純 URL、或「文字 + URL」混合)
            │
            ▼
    Line Webhook (/webhook)
            │
            ▼
    Extract URL from Text
    (使用 re.search() 從任意位置提取 URL)
            │
            ▼
    Detect Content Type
    (SOCIAL → URL → Text)
            │
            ▼
    ┌───────┼───────┐
    │       │       │
    ▼       ▼       ▼
[SOCIAL]  [URL]  [Text]
    │       │       │
    ▼       ▼       │
 Apify   WebScraper │
(FB/Threads) (抓取網頁)│
    │       │       │
    └───────┴───────┘
            │
            ▼
    Gemini AI Service
    (產生標題/摘要/標籤)
            │
            ▼
    Notion Repository
    (儲存至 Database)
            │
            ▼
    Push Message to User
    (回覆結果)
```

## 11. Apify Actors (社群貼文爬取)
| Platform | Actor ID                        | Input                   | Key Output Fields                |
|----------|--------------------------------|-------------------------|----------------------------------|
| Facebook | apify/facebook-posts-scraper   | startUrls: [{url}]     | text, user.name, likes, comments |
| Threads  | sinam7/threads-post-scraper    | url: string            | content, authorId, like_count    |

### URL 提取邏輯
- 使用 `re.search(r'https?://\S+')` 從任意位置提取 URL
- 自動去除結尾標點符號 (`.`, `,`, `;` 等)
- 支援「文字 + URL」混合輸入，例如：
  ```
  ▋GitHub 專案連結
  https://github.com/example/repo
  ```
