# 📋 Spec: Line Bot Content Saver

## 1. Vision
一個多平台 Bot（Line / Telegram），接收使用者傳送的文字、網址、社群貼文、YouTube 影片、圖片、語音或文件檔案，
使用 AI 進行摘要分析，並儲存至 Notion 資料庫。

## 2. Current Status: ✅ Phase 9 Completed

### 已完成功能
- ✅ 文字訊息摘要
- ✅ 網址內容抓取與摘要（含 SPA / Jina Reader）
- ✅ AI 自動產生標題、摘要、標籤
- ✅ 儲存至 Notion Database
- ✅ 社群貼文偵測與摘要（Facebook / Threads）
- ✅ 圖片訊息處理（Line / Telegram / 圖片 URL）
- ✅ 圖片上傳至 Google Drive（Service Account）
- ✅ 多 AI 提供者支援（Gemini / OpenAI / Circuit Breaker 自動切換）
- ✅ YouTube 影片摘要（Apify + 繁中字幕）
- ✅ Telegram Bot 整合（無訊息限制 + 完整功能對齊）
- ✅ 語音訊息支援（OpenAI Whisper STT）
- ✅ Prompt Template System（Notion 動態管理 + 加權關鍵字匹配）
- ✅ 動態 Schema 生成（Structured Output API）
- ✅ **文件檔案處理（PDF / DOCX / XLSX / PPTX / CSV / TXT）**
- ✅ **PDF OCR 回退（PyMuPDF + AI Vision）**
- ✅ **Structured Logging（統一日誌框架 + LOG_LEVEL 控制）**
- ✅ **合併分類 + Schema 生成（1 次 AI 呼叫取代 2 次）**
- ✅ **Circuit Breaker（Gemini 429/5xx → OpenAI 60s 冷卻）**

### 生產環境
| 平台 | URL / ID |
|------|----------|
| Zeabur | https://line-bot9.zeabur.app |
| Line Webhook | /webhook |
| Telegram Webhook | /telegram/webhook |
| Telegram Bot | @benson_inspiration_bot |

## 3. Tech Stack
| Layer | Technology | Status |
|-------|-----------|--------|
| Language | Python 3.10+ | ✅ |
| Web Framework | FastAPI | ✅ |
| Line SDK | line-bot-sdk v3 | ✅ |
| Telegram | httpx（直接呼叫 API） | ✅ |
| AI (Gemini) | google-generativeai | ✅ |
| AI (OpenAI) | openai (GPT-4o-mini) | ✅ |
| AI Fallback | FallbackAIService + Circuit Breaker | ✅ |
| YouTube | Apify streamers/youtube-scraper | ✅ |
| Voice STT | OpenAI Whisper API | ✅ |
| Notion | notion-client (API v2022-06-28) | ✅ |
| Social Scraper | apify-client | ✅ |
| Cloud Storage | Google Drive API (Service Account) | ✅ |
| SPA Scraper | Jina Reader API | ✅ |
| Document (PDF) | PyPDF2 + PyMuPDF (OCR) | ✅ |
| Document (Office) | python-docx / openpyxl / python-pptx | ✅ |
| Logging | Python logging (structured) | ✅ |
| Deployment | Zeabur | ✅ |

## 4. Architecture
```
┌──────────────────────────────────────────────────────────────┐
│                         main.py                               │
│                      (FastAPI Entry)                          │
├──────────────────┬───────────────────────────────────────────┤
│  /webhook (Line) │  /telegram/webhook (Telegram)             │
└────────┬─────────┴──────────────┬────────────────────────────┘
         │                        │
┌────────▼────────┐      ┌────────▼─────────┐
│ LineMessageHandler│      │ TelegramHandler  │
│ (text/img/audio/ │      │ (text/photo/voice/│
│  file/youtube)   │      │  document/youtube)│
└────────┬────────┘      └────────┬─────────┘
         │                        │
         └───────────┬────────────┘
                     │ (共用 UseCase + Infrastructure)
         ┌───────────▼───────────┐
         │   SummarizeUseCase    │  ← PromptTemplateManager (Notion 模板)
         │   SaveToNotionUseCase │  ← SchemaGenerator (動態 Schema)
         │   ProcessImageUseCase │  ← ContentClassifier (分類)
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────────┐
    │                │                    │
┌───▼────┐   ┌──────▼──────┐   ┌────────▼────────┐
│ AI Layer│   │ Data Layer  │   │ External Services│
│ Gemini  │   │ Notion Repo │   │ Google Drive     │
│ OpenAI  │   │ Schema Cache│   │ Apify (FB/TH/YT)│
│ Whisper │   │             │   │ Jina Reader      │
│ Fallback│   │             │   │ DocumentExtractor│
└─────────┘   └─────────────┘   └──────────────────┘
```

## 5. Directory Structure
```
Line bot/
├── src/
│   ├── domain/
│   │   └── content.py              # Content, ContentType, SocialPlatform
│   ├── usecase/
│   │   ├── summarize.py            # SummarizeUseCase (7 content types)
│   │   ├── save_to_notion.py       # SaveToNotionUseCase
│   │   └── process_image.py        # ProcessImageUseCase
│   ├── infrastructure/
│   │   ├── line_handler.py         # Line Webhook Handler
│   │   ├── telegram_handler.py     # Telegram Webhook Handler
│   │   ├── gemini_service.py       # Gemini AI
│   │   ├── openai_service.py       # OpenAI (GPT + Vision + Whisper)
│   │   ├── fallback_ai_service.py  # AI 自動切換 + Circuit Breaker
│   │   ├── notion_repo.py          # Notion Repository
│   │   ├── web_scraper.py          # URL Content Fetcher + Jina fallback
│   │   ├── social_detector.py      # 社群/YouTube URL 偵測
│   │   ├── apify_scraper.py        # 社群貼文爬取 (Facebook/Threads)
│   │   ├── youtube_service.py      # YouTube 影片+字幕 (Apify)
│   │   ├── drive_service.py        # Google Drive 上傳
│   │   ├── image_detector.py       # 圖片 URL 偵測
│   │   ├── whisper_service.py      # OpenAI Whisper STT
│   │   ├── document_extractor.py   # 文件文字萃取 (PDF/Office/CSV/TXT)
│   │   ├── response_builder.py     # 統一回應建構器
│   │   ├── prompt_template_manager.py # Notion 模板管理 + 關鍵字匹配
│   │   ├── schema_generator.py     # 動態 Schema 生成器
│   │   ├── schema_cache.py         # Schema TTL 快取
│   │   ├── output_schemas.py       # 預設 Schema 定義
│   │   ├── content_classifier.py   # 內容分類器 (URL/Keyword/AI)
│   │   └── logging_config.py       # 統一日誌設定
│   └── main.py                     # FastAPI 入口 + 路由
├── requirements.txt
├── spec.md
├── active_plan.md
└── CLAUDE.md
```

## 6. Domain Model
```python
class ContentType(Enum):
    TEXT = "text"       # 純文字訊息
    URL = "url"         # 網頁連結
    SOCIAL = "social"   # 社群貼文 (Facebook/Threads)
    IMAGE = "image"     # 圖片
    YOUTUBE = "youtube"  # YouTube 影片
    AUDIO = "audio"     # 語音訊息
    FILE = "file"       # 文件檔案 (PDF/DOCX/XLSX/PPTX/CSV/TXT)

class SocialPlatform(Enum):
    FACEBOOK = "facebook"
    THREADS = "threads"

@dataclass
class Content:
    content_type: ContentType
    raw_content: str
    id: str                              # UUID
    source_url: Optional[str]            # 來源 URL
    social_platform: Optional[SocialPlatform]
    title: Optional[str]                 # AI 產生的標題
    summary: Optional[str]               # AI 產生的摘要
    tags: List[str]                      # AI 產生的標籤
    created_at: datetime
    # Social metadata
    author: Optional[str]
    likes: Optional[int]
    comments: Optional[int]
    shares: Optional[int]
    # Image metadata
    image_url: Optional[str]             # Drive 連結
    image_description: Optional[str]
    # YouTube/Audio metadata
    video_duration: Optional[str]        # "MM:SS" 格式
    channel_name: Optional[str]
    # File metadata
    file_url: Optional[str]              # Drive 連結
    file_name: Optional[str]             # 原始檔名
```

## 7. API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /webhook | Line Webhook |
| POST | /telegram/webhook | Telegram Webhook |
| GET | /health | Health check |

## 8. Environment Variables
| Variable | Description |
|----------|-------------|
| LINE_CHANNEL_ACCESS_TOKEN | Line Channel Access Token |
| LINE_CHANNEL_SECRET | Line Channel Secret |
| TELEGRAM_BOT_TOKEN | Telegram Bot Token |
| GEMINI_API_KEY | Google Gemini API Key |
| OPENAI_API_KEY | OpenAI API Key (GPT + Whisper) |
| AI_PROVIDER | AI 提供者 (auto/gemini/openai) |
| NOTION_API_KEY | Notion Integration Token |
| NOTION_DATABASE_ID | Notion Database ID |
| NOTION_TEMPLATE_DATABASE_ID | Notion 模板資料庫 ID |
| APIFY_API_TOKEN | Apify API Token |
| GOOGLE_SERVICE_ACCOUNT_FILE | Google Service Account JSON 路徑 |
| GOOGLE_CREDENTIALS_BASE64 | Google credentials (Base64，雲端部署) |
| GOOGLE_TOKEN_BASE64 | Google OAuth token (Base64，雲端部署) |
| GOOGLE_DRIVE_FOLDER_ID | Google Drive 資料夾 ID |
| LOG_LEVEL | 日誌等級 (DEBUG/INFO/WARNING/ERROR，預設 INFO) |

## 9. Notion Database Schema

### 主資料庫 (Content)
| Field | Type | Description |
|-------|------|-------------|
| Title | title | AI 產生的標題 |
| Summary | rich_text | AI 摘要 |
| Content | rich_text | 原始內容 |
| Source URL | url | 來源網址 |
| Type | select | text/url/social/image/youtube/audio/file |
| Tags | multi_select | AI 自動標籤 |
| Created | date | 建立時間 |
| Author | rich_text | 作者名稱 |
| Likes | number | 按讚數 |
| Comments | number | 留言數 |
| Shares | number | 分享數 |
| Image URL | url | 圖片 Drive 連結 |
| Image Description | rich_text | 圖片描述 |
| Duration | rich_text | 影片/音訊時長 |
| Channel | rich_text | 頻道名稱 |
| File URL | url | 文件 Drive 連結 |
| File Name | rich_text | 原始檔名 |

### 模板資料庫 (Templates)
| Field | Type | Description |
|-------|------|-------------|
| Name | title | 模板名稱 |
| Category | select | 分類 (tech/parenting/finance/lifestyle/casual) |
| Prompt | rich_text | AI 角色 prompt |
| Keywords | rich_text | 關鍵字（逗號分隔） |
| Output Format | select | 標準摘要/閒聊模式/自動推斷 |
| Active | checkbox | 是否啟用 |

## 10. External Service Actors
| Service | Actor / API |
|---------|------------|
| Facebook | apify/facebook-posts-scraper |
| Threads | sinam7/threads-post-scraper |
| YouTube | streamers/youtube-scraper |
| SPA Scraper | Jina Reader (r.jina.ai) |
| Voice STT | OpenAI Whisper API |
| Document OCR | PyMuPDF → AI Vision (Gemini/OpenAI) |

## 11. Key Design Decisions

### Clean Architecture
- **Domain Layer**: 純 Python，無外部依賴。Content entity + factory functions。
- **UseCase Layer**: 業務邏輯編排。SummarizeUseCase 處理 7 種內容類型。
- **Infrastructure Layer**: 所有外部服務整合。依賴注入於 main.py。

### AI Pipeline 優化
- **合併分類 + Schema**: 1 次 AI 呼叫同時完成內容分類與 Schema 生成（原本需 2 次）。
- **Circuit Breaker**: Gemini 收到 429/5xx 時自動切換 OpenAI，60 秒冷卻。
- **Schema 快取**: 相同模板的 Schema 快取 5 分鐘，避免重複生成。

### 模板匹配策略
1. **URL pattern** → 快速匹配（無 AI 呼叫）
2. **加權關鍵字** → 獨有關鍵字權重 2，共用權重 1；模糊（差距 < 2）→ 交由 AI
3. **AI 分類** → 合併呼叫（分類 + Schema 同時生成）

### 文件處理
- 所有操作在記憶體中完成（`io.BytesIO`），不寫入磁碟。
- 文字上限 15,000 字，避免 AI token 溢出。
- 圖片式 PDF 自動偵測，使用 PyMuPDF 渲染 → AI Vision OCR（最多 5 頁）。
