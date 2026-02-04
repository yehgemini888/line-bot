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

## ⬜ Phase 8: 進階功能 (BACKLOG)

### 📱 Priority 1: 更多社群平台
- [ ] Instagram 貼文支援
- [ ] X (Twitter) 貼文支援

### 🎧 Priority 2: 多媒體擴充
- [ ] Podcast 音檔摘要 (Spotify/Apple Podcast)
- [ ] PDF 文件摘要

### ⚙️ Priority 3: 使用者體驗
- [ ] 自訂摘要風格 (簡短/詳細/條列)
- [ ] 多語言摘要支援
- [ ] 搜尋已儲存內容
- [ ] Notion 分類資料夾

### 🛠️ Priority 4: 開發體驗
- [ ] 単元測試完善
- [ ] CI/CD 整合

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
| 8 | 進階功能 | ⬜ Backlog | 0/10 |


---

# 🚀 Current Status

**所有核心功能已完成！**

### 生產環境
- 🌐 **Zeabur**: https://line-bot9.zeabur.app
- 📱 **Line Bot Webhook**: /webhook
- 📱 **Telegram Bot Webhook**: /telegram/webhook
- 🤖 **Telegram**: @benson_inspiration_bot

### 支援的內容類型
| 類型 | 來源 |
|------|------|
| 📝 文字 | 純文字訊息 |
| 🔗 網址 | 一般網頁 (SSR) |
| 🌐 SPA | JavaScript 網站 (Jina Reader) ✅ NEW |
| 🂬 YouTube | 影片連結 (含字幕摘要) |
| 📱 社群 | Facebook / Threads |
| 🖼️ 圖片 | Line 圖片 / 圖片 URL |
| 🎙️ 語音 | 語音訊息 (Whisper) ✅ NEW |


---

# 💎 Memory Crystal

```
Project: Line Bot Content Saver
Phase: 7.6 (Voice Input) ✅ COMPLETED
Status: All core features + voice input completed

Production URLs:
- Zeabur: https://line-bot9.zeabur.app
- Line Webhook: /webhook
- Telegram Webhook: /telegram/webhook
- Telegram Bot: @benson_inspiration_bot

Key Changes (2026-02-04):
- SPA Support: Jina Reader fallback for JavaScript websites
- Voice Input: OpenAI Whisper for Line/Telegram
- YouTube Support: Apify streamers/youtube-scraper + zh-TW subtitles

Completed Phases: 1, 2, 2.5, 3, 4, 6, 7, 7.5, 7.6
Next Phase: 8 (Advanced Features - Backlog)
```
