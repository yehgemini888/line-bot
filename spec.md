# 📋 Spec: Line Bot Content Saver

## 1. Vision
一個 Line Bot，接收使用者傳送的文字或網址，
使用 Gemini AI 進行摘要分析，並儲存至 Notion 資料庫。

## 2. Current Status: ✅ MVP Complete

### 已完成功能
- ✅ 文字訊息摘要
- ✅ 網址內容抓取與摘要
- ✅ AI 自動產生標題、摘要、標籤
- ✅ 儲存至 Notion Database
- ✅ 本地開發環境 (ngrok)

### 待開發功能
- ⬜ 圖片處理 (OCR / Vision AI)
- ⬜ 社群貼文支援 (IG/FB/Twitter)
- ⬜ 雲端部署 (Railway / Render)
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
| Dev Server     | uvicorn                        | ✅ |
| Tunnel         | ngrok                          | ✅ |

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
│  ┌──────────────┐                                       │
│  │ web_scraper  │                                       │
│  └──────────────┘                                       │
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
│  │     (Entity)        │ │      (Enum)         │        │
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
│   │   └── content.py          # Content Entity, ContentType Enum
│   ├── usecase/
│   │   ├── __init__.py
│   │   ├── summarize.py        # SummarizeUseCase
│   │   └── save_to_notion.py   # SaveToNotionUseCase
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── line_handler.py     # Line Webhook Handler
│   │   ├── gemini_service.py   # Gemini AI Adapter
│   │   ├── notion_repo.py      # Notion Repository
│   │   └── web_scraper.py      # URL Content Fetcher
│   └── main.py                 # FastAPI Entry Point
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
class ContentType(Enum):
    TEXT = "text"
    URL = "url"
    IMAGE = "image"      # Phase 2
    SOCIAL = "social"    # Phase 3

@dataclass
class Content:
    id: str
    content_type: ContentType
    raw_content: str
    source_url: Optional[str]
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

## 10. Data Flow
```
User sends message to Line Bot
            │
            ▼
    Line Webhook (/webhook)
            │
            ▼
    Detect Content Type
    (URL or Text)
            │
            ▼
    ┌───────┴───────┐
    │               │
    ▼               ▼
  [URL]          [Text]
    │               │
    ▼               │
 WebScraper         │
 (抓取內容)          │
    │               │
    └───────┬───────┘
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
