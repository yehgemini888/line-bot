# 📅 Active Plan: Line Bot Content Saver

## ✅ Phase 1: MVP Foundation (COMPLETED)
- [x] Task 01: Project Setup (資料夾結構 + requirements.txt + .env.example)
- [x] Task 02: Domain Layer (Content Entity + ContentType Enum)
- [x] Task 03: Web Scraper (抓取網址內容)
- [x] Task 04: Gemini Service (呼叫 Gemini API 進行摘要)
- [x] Task 05: Notion Repository (儲存至 Notion)
- [x] Task 06: Summarize UseCase (整合 Scraper + Gemini)
- [x] Task 07: Save UseCase (整合 Notion Repo)
- [x] Task 08: Line Webhook Handler (接收訊息 + 呼叫 UseCase)
- [x] Task 09: FastAPI Main (組裝所有元件)
- [x] Task 10: Local Testing (ngrok + Line 測試)

---

## ✅ Phase 2: 圖片支援 (COMPLETED)
- [x] Task 11: Domain Layer 擴充 (新增 IMAGE 類型 + image_url/image_description 欄位)
- [x] Task 12: Google Drive Service (OAuth 2.0 圖片上傳)
- [x] Task 13: Image Detector (偵測圖片 URL)
- [x] Task 14: Gemini Vision Service (圖片分析 analyze_image())
- [x] Task 15: ProcessImage UseCase (整合 Drive + Gemini + Notion)
- [x] Task 16: Line Handler 擴充 (下載 Line 圖片 + 圖片 URL)
- [x] Task 17: Notion Repository 擴充 (新增 Image URL / Image Description 欄位)
- [x] Task 18: Main.py 整合 (處理 ImageMessageContent 事件)
- [x] Task 19: Dependencies 更新 (google-api-python-client, google-auth-oauthlib)

---

## ✅ Phase 2.5: 多 AI 提供者支援 (COMPLETED)
- [x] Task 20: OpenAI Service (文字摘要 + 圖片辨識)
- [x] Task 21: AI Provider 切換機制 (環境變數 AI_PROVIDER)
- [x] Task 22: Main.py 整合 (動態選擇 AI 服務)

---

## ✅ Phase 3: 雲端部署 (COMPLETED)
- [x] Task 20: Zeabur 部署設定 (main.py + Procfile)
- [x] Task 21: 環境變數設定 (含 GOOGLE_CREDENTIALS_BASE64 / GOOGLE_TOKEN_BASE64)
- [x] Task 22: 部署與測試 ✅ https://line-bot9.zeabur.app
- [x] Task 23: 設定固定 Webhook URL

---

## ✅ Phase 4: 社群貼文支援 (COMPLETED)
- [x] Task 21: 社群網址偵測 (Facebook / Threads)
- [x] Task 22: Domain Layer 擴充 (SocialPlatform Enum)
- [x] Task 23: SummarizeUseCase 擴充 (支援 SOCIAL ContentType)
- [x] Task 24: Apify Scraper 修復 (Facebook + Threads)
- [x] Task 25: URL 提取優化 (從混合輸入中提取 URL)
- [x] Task 26: 整合測試 (Line Bot + Social Posts)

---

## ✅ Phase 6: YouTube 影片摘要 (COMPLETED)
- [x] Task 01: Domain Layer - 新增 ContentType.YOUTUBE
- [x] Task 02: YouTube Service - Apify streamers/youtube-scraper
- [x] Task 03: Social Detector - YouTube URL 偵測
- [x] Task 04: save_to_notion - 支援 YouTube 類型
- [x] Task 05: Notion Repo - 新增 Duration / Channel 欄位
- [x] Task 06: Line Handler - YouTube 處理流程
- [x] Task 07: Main.py 整合

**成果：** 支援 YouTube 影片連結，自動擷取繁體中文字幕進行 AI 摘要

---

## ✅ Phase 7: Telegram Bot 整合 (COMPLETED)
- [x] Task 01: 建立 Telegram Bot (@BotFather)
- [x] Task 02: 新增 telegram_handler.py
- [x] Task 03: 更新 main.py 新增 /telegram/webhook 路由
- [x] Task 04: 設定 Webhook URL
- [x] Task 05: 測試驗證

**成果：** Telegram Bot @benson_inspiration_bot 上線，無訊息限制

---

## ✅ Phase 7.8: 系統架構重構與穩定性修復 (COMPLETED)
- [x] Task 01: 統一 ResponseBuilder (Line/Telegram 共用)
- [x] Task 02: 統一 Template System 整合 (Telegram 圖片/語音/影片)
- [x] Task 03: OpenAI Strict Mode 相容性修復 (Schema Required Fields)
- [x] Task 04: Gemini Schema 相容性修復 (Remove additionalProperties)
- [x] Task 05: 跨平台功能對齊 (YouTube/Audio/Photo)

**成果：** 系統架構統一，跨 AI 模型 Schema 相容，所有平台功能一致

---

## ✅ Phase 8: AI Pipeline 優化 (COMPLETED)
- [x] Task 01: Circuit Breaker (Gemini 429/5xx → OpenAI 自動切換，60s 冷卻)
- [x] Task 02: 合併分類 + Schema 生成 (1 次 AI 呼叫取代 2 次)
- [x] Task 03: Notion API 版本鎖定 (v2022-06-28 相容性修復)

**成果：** AI 呼叫次數減半，429 錯誤自動恢復

---

## ✅ Phase 9: 文件支援 + 關鍵字優化 + Structured Logging (COMPLETED)
- [x] Task 01: 加權關鍵字匹配 (獨有 w=2, 共用 w=1, 模糊 → AI fallback)
- [x] Task 02: Domain Layer - 新增 ContentType.FILE + file_url/file_name
- [x] Task 03: DocumentExtractor (PDF/DOCX/XLSX/PPTX/CSV/TXT 文字萃取)
- [x] Task 04: PDF OCR 回退 (PyMuPDF 渲染 → AI Vision，最多 5 頁)
- [x] Task 05: Line Handler - handle_file_message_with_push()
- [x] Task 06: Telegram Handler - _handle_document_message()
- [x] Task 07: SummarizeUseCase 支援 FILE 類型
- [x] Task 08: Notion Repo 新增 File URL / File Name 欄位
- [x] Task 09: Main.py - FileMessageContent 路由 + DocumentExtractor 注入
- [x] Task 10: Structured Logging (logging_config.py + 245 個 print → logger)

**成果：** 支援 6 種文件格式（含圖片式 PDF OCR），統一日誌框架

---

## 👉 Phase 10: 穩定性與可維護性 (NEXT)

### 🔴 Priority 1: 品質基礎建設
- [ ] Task 01: 單元測試 — 核心邏輯測試 (keyword matching, document extraction, content classification)
- [ ] Task 02: Rate Limiting — 防止 API 濫用 (per-user 限流)
- [ ] Task 03: 錯誤重試機制 — 外部 API 呼叫失敗自動重試 (Notion, Drive, Apify)

### 🟡 Priority 2: 功能擴充
- [ ] Task 04: X (Twitter) 支援 — Apify 有 X scraper，新增 SocialPlatform.TWITTER
- [ ] Task 05: 管理員指令 — `/reload_templates`, `/status`, `/stats` 等管理命令
- [ ] Task 06: 使用者偏好設定 — 每人可設定預設模板、摘要長度

### 🟢 Priority 3: 進階功能
- [ ] Task 07: 批次處理 — 一次傳多個檔案/連結的排隊處理
- [ ] Task 08: 舊版 Office 格式 — .doc / .xls / .ppt 支援
- [ ] Task 09: 監控 Dashboard — 處理量、錯誤率、AI 用量統計
- [ ] Task 10: Instagram 貼文支援

---

# 📊 Progress Summary

| Phase | 名稱 | 狀態 | 進度 |
|-------|------|------|------|
| 1 | MVP Foundation | ✅ 完成 | 10/10 |
| 2 | 圖片支援 | ✅ 完成 | 9/9 |
| 2.5 | 多 AI 提供者 | ✅ 完成 | 3/3 |
| 3 | 雲端部署 (Zeabur) | ✅ 完成 | 4/4 |
| 4 | 社群貼文支援 | ✅ 完成 | 6/6 |
| 6 | YouTube 影片摘要 | ✅ 完成 | 7/7 |
| 7 | Telegram Bot | ✅ 完成 | 5/5 |
| 7.5 | SPA 網站支援 | ✅ 完成 | 2/2 |
| 7.6 | 語音訊息支援 | ✅ 完成 | 4/4 |
| 7.7 | 系統優化 | ✅ 完成 | 5/5 |
| 7.8 | 架構重構 | ✅ 完成 | 5/5 |
| 8 | AI Pipeline 優化 | ✅ 完成 | 3/3 |
| 9 | 文件支援 + Logging | ✅ 完成 | 10/10 |
| 10 | 穩定性與可維護性 | 👉 Next | 0/10 |

---

# 🚀 Current Status

**Phase 9 完成！所有核心功能已實作。**

### 支援的內容類型（7 種，雙平台完整對齊）
| 類型 | Line | Telegram | AI 處理特點 |
|------|------|----------|------------|
| 📝 文字 | ✅ | ✅ | 智慧模板 + 動態 Schema + 閒聊偵測 |
| 🔗 網址 | ✅ | ✅ | 智慧模板 + Jina Reader (SPA) |
| 📱 社群 | ✅ | ✅ | Facebook / Threads 自動擷取 |
| 🎬 YouTube | ✅ | ✅ | 繁中字幕 + 影片結構分析 |
| 🖼️ 圖片 | ✅ | ✅ | Vision API + Drive 備份 |
| 🎙️ 語音 | ✅ | ✅ | Whisper 轉錄 + 摘要 |
| 📄 文件 | ✅ | ✅ | 6 格式萃取 + OCR + Drive 備份 |

### 系統特性
| 特性 | 說明 |
|------|------|
| AI 高可用 | Circuit Breaker: Gemini → OpenAI 自動切換 |
| 智慧分類 | URL → Keyword → AI 三層匹配策略 |
| 動態 Schema | 依內容自動生成結構化輸出格式 |
| Structured Logging | LOG_LEVEL 環境變數控制日誌等級 |
| 文件 OCR | 圖片式 PDF 自動偵測 → AI Vision 辨識 |

### 生產環境
- 🌐 **Zeabur**: https://line-bot9.zeabur.app
- 📱 **Line Bot Webhook**: /webhook
- 📱 **Telegram Bot Webhook**: /telegram/webhook
- 🤖 **Telegram**: @benson_inspiration_bot

---

# 💎 Memory Crystal

```
Project: Line Bot Content Saver
Phase: 9 (文件支援 + Structured Logging) ✅ COMPLETED
Status: Production Ready

Production URLs:
- Zeabur: https://line-bot9.zeabur.app
- Line Webhook: /webhook
- Telegram Webhook: /telegram/webhook
- Telegram Bot: @benson_inspiration_bot

Key Changes (2026-02-10):
- DocumentExtractor: PDF/DOCX/XLSX/PPTX/CSV/TXT + OCR fallback
- Structured Logging: 245 print() → logger with LOG_LEVEL control
- Weighted Keywords: unique=2, shared=1, ambiguity → AI fallback
- Circuit Breaker: Gemini 429/5xx → OpenAI 60s cooldown
- Merged Classify+Schema: 1 AI call instead of 2

Content Types: TEXT, URL, SOCIAL, IMAGE, YOUTUBE, AUDIO, FILE (7 types)
Platforms: Line + Telegram (fully aligned)

Completed Phases: 1, 2, 2.5, 3, 4, 6, 7, 7.5, 7.6, 7.7, 7.8, 8, 9
Next Phase: 10 (穩定性與可維護性)
```
