# 📋 Spec: Line Bot Content Saver

## 1. Vision
一個 Line Bot，接收使用者傳送的文字、網址、社群貼文或圖片，
使用 Gemini AI 進行摘要分析，並儲存至 Notion 資料庫。
圖片會上傳至 Google Drive 並產生公開連結。

## 2. Current Status: ✅ Phase 2 Completed

### 已完成功能
- ✅ 文字訊息摘要
- ✅ 網址內容抓取與摘要
- ✅ AI 自動產生標題、摘要、標籤
- ✅ 儲存至 Notion Database
- ✅ 本地開發環境 (ngrok / VS Code Port Forwarding)
- ✅ 社群貼文偵測 (Facebook / Threads)
- ✅ 社群貼文爬取 (Apify)
- ✅ 智慧 URL 提取 (支援「文字 + URL」混合輸入)
- ✅ **圖片訊息處理 (Line 圖片 / 圖片 URL)**
- ✅ **圖片上傳至 Google Drive (OAuth 2.0)**
- ✅ **Gemini Vision 圖片分析**

### 待開發功能
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
| AI Vision      | Gemini 2.0 Flash (Vision)      | ✅ |
| Notion         | notion-client                  | ✅ |
| HTTP Client    | httpx                          | ✅ |
| HTML Parser    | beautifulsoup4                 | ✅ |
| Social Scraper | apify-client                   | ✅ |
| Cloud Storage  | Google Drive API (OAuth 2.0)   | ✅ |
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
│  ┌──────────────┐ ┌───────────────┐                    │
│  │drive_service │ │image_detector │  (Phase 2 ✅)      │
│  └──────────────┘ └───────────────┘                    │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    UseCase Layer                         │
│  ┌─────────────────────┐ ┌─────────────────────┐        │
│  │  SummarizeUseCase   │ │ SaveToNotionUseCase │        │
│  └─────────────────────┘ └─────────────────────┘        │
│  ┌─────────────────────┐                                │
│  │ ProcessImageUseCase │  (Phase 2 ✅)                  │
│  └─────────────────────┘                                │
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
│   │   ├── save_to_notion.py   # SaveToNotionUseCase
│   │   └── process_image.py    # ProcessImageUseCase (Phase 2 ✅)
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── line_handler.py     # Line Webhook Handler (含圖片處理)
│   │   ├── gemini_service.py   # Gemini AI Adapter (含 Vision)
│   │   ├── notion_repo.py      # Notion Repository (含圖片欄位)
│   │   ├── web_scraper.py      # URL Content Fetcher
│   │   ├── social_detector.py  # 社群網址偵測 (FB/Threads)
│   │   ├── apify_scraper.py    # 社群貼文爬取 (Apify)
│   │   ├── drive_service.py    # Google Drive 上傳 (Phase 2 ✅)
│   │   └── image_detector.py   # 圖片 URL 偵測 (Phase 2 ✅)
│   └── main.py                 # FastAPI Entry Point
├── tests/                      # 測試檔案
├── venv/                       # Python Virtual Environment
├── credentials.json            # Google OAuth 憑證 (Phase 2 ✅)
├── token.json                  # Google OAuth Token (Phase 2 ✅)
├── authorize_drive.py          # Drive 授權腳本 (Phase 2 ✅)
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
    IMAGE = "image"      # Phase 2 ✅

@dataclass
class Content:
    id: str
    content_type: ContentType
    raw_content: str
    source_url: Optional[str]
    social_platform: Optional[SocialPlatform]
    title: Optional[str]
    summary: Optional[str]
    tags: List[str]
    created_at: datetime
    # Social metadata
    author: Optional[str]
    likes: Optional[int]
    comments: Optional[int]
    shares: Optional[int]
    # Image metadata (Phase 2 ✅)
    image_url: Optional[str]
    image_description: Optional[str]
```

## 7. Notion Schema
| Field             | Type         | Description          | Status |
|-------------------|--------------|----------------------|--------|
| Title             | title        | AI 產生的標題        | ✅ |
| Summary           | rich_text    | AI 摘要              | ✅ |
| Content           | rich_text    | 原始內容             | ✅ |
| Source URL        | url          | 來源網址             | ✅ |
| Type              | select       | text/url/social/image| ✅ |
| Tags              | multi_select | AI 自動標籤          | ✅ |
| Created           | date         | 建立時間             | ✅ |
| Author            | rich_text    | 作者 (社群貼文)      | ✅ |
| Likes             | number       | 按讚數               | ✅ |
| Comments          | number       | 留言數               | ✅ |
| Shares            | number       | 分享數               | ✅ |
| Image URL         | url          | 圖片連結 (Drive)     | ✅ |
| Image Description | rich_text    | 圖片描述 (AI 產生)   | ✅ |

## 8. API Endpoints
| Method | Path      | Description          | Status |
|--------|-----------|----------------------|--------|
| POST   | /webhook  | Line Webhook 接收訊息 | ✅ |
| GET    | /health   | Health check         | ✅ |

## 9. Environment Variables
| Variable                    | Description                    | Status |
|-----------------------------|--------------------------------|--------|
| LINE_CHANNEL_ACCESS_TOKEN   | Line Channel Access Token      | ✅ |
| LINE_CHANNEL_SECRET         | Line Channel Secret            | ✅ |
| GEMINI_API_KEY              | Google Gemini API Key          | ✅ |
| NOTION_API_KEY              | Notion Integration Token       | ✅ |
| NOTION_DATABASE_ID          | Notion Database ID             | ✅ |
| APIFY_API_TOKEN             | Apify API Token (社群爬取)     | ✅ |
| GOOGLE_SERVICE_ACCOUNT_FILE | OAuth credentials.json 路徑    | ✅ |
| GOOGLE_DRIVE_FOLDER_ID      | Google Drive 資料夾 ID         | ✅ |

## 10. Data Flow

### 文字/網址/社群貼文
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
    (IMAGE → SOCIAL → URL → Text)
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

### 圖片處理 (Phase 2 ✅)
```
User sends Image to Line Bot
(Line 圖片訊息或圖片 URL)
            │
            ▼
    Line Webhook (/webhook)
            │
            ▼
    Detect ImageMessageContent
    or Image URL (.jpg/.png/imgur等)
            │
            ▼
    Download Image
    (從 Line API 或 URL 下載)
            │
            ▼
    Google Drive Service
    (上傳圖片，取得公開連結)
            │
            ▼
    Gemini Vision API
    (分析圖片，產生標題/描述/標籤)
            │
            ▼
    Notion Repository
    (儲存：標題、描述、標籤、Drive 連結)
            │
            ▼
    Push Message to User
    (回覆：標題、描述、標籤、連結)
```

## 11. Apify Actors (社群貼文爬取)
| Platform | Actor ID                        | Input                   | Key Output Fields                |
|----------|--------------------------------|-------------------------|----------------------------------|
| Facebook | apify/facebook-posts-scraper   | startUrls: [{url}]     | text, user.name, likes, comments |
| Threads  | sinam7/threads-post-scraper    | url: string            | content, authorId, like_count    |

## 12. Google Drive Integration (Phase 2 ✅)
- **認證方式**: OAuth 2.0 Desktop App
- **權限範圍**: `https://www.googleapis.com/auth/drive.file`
- **首次授權**: 執行 `python authorize_drive.py`，瀏覽器授權後貼上授權碼
- **Token 儲存**: `token.json` (自動更新)
- **上傳設定**: 檔案上傳後設為公開可讀

## 13. Image Detection
支援的圖片格式：
- 副檔名: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.tiff`, `.svg`
- 圖床服務: Imgur, Giphy, Unsplash, Pexels, Flickr, Discord CDN, Twitter Media
