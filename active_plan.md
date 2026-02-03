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

## ✅ Phase 4: 社群貼文支援 (COMPLETED)
- [x] Task 21: 社群網址偵測 (Facebook / Threads)
- [x] Task 22: Domain Layer 擴充 (SocialPlatform Enum)
- [x] Task 23: SummarizeUseCase 擴充 (支援 SOCIAL ContentType)
- [x] Task 24: Apify Scraper 修復 (Facebook + Threads)
  - [x] 切換 Threads Actor: `apify/threads-profile-api-scraper` → `sinam7/threads-post-scraper`
  - [x] 修正 Facebook 輸出欄位對應
  - [x] 支援 Photo 類型貼文與 engagement 數據
- [x] Task 25: URL 提取優化
  - [x] 從「文字 + URL」混合輸入中提取 URL
  - [x] 使用 `re.search()` 取代 `re.match()` 進行 URL 偵測
  - [x] 修正 Threads URL 被截斷問題
- [x] Task 26: 整合測試 (Line Bot + Social Posts)

**成果：** 使用者可傳送 Facebook/Threads 貼文網址（可含額外文字），自動擷取內容並摘要

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

**成果：** 使用者可傳送圖片或圖片網址，AI 會分析圖片內容，上傳至 Google Drive，並儲存至 Notion

---

## ✅ Phase 2.5: 多 AI 提供者支援 (COMPLETED)
- [x] Task 20: OpenAI Service (文字摘要 + 圖片辨識)
- [x] Task 21: AI Provider 切換機制 (環境變數 AI_PROVIDER)
- [x] Task 22: Main.py 整合 (動態選擇 AI 服務)

**成果：** 可透過 `AI_PROVIDER` 環境變數切換 Gemini 或 OpenAI

---

## ✅ Phase 3: 雲端部署 (COMPLETED)
- [x] Task 20: ~~Dockerfile 建立~~ (Zeabur 自動偵測 Python，不需要)
- [x] Task 21: Zeabur 部署設定 (main.py + Procfile)
- [x] Task 22: 環境變數設定 (含 GOOGLE_CREDENTIALS_BASE64 / GOOGLE_TOKEN_BASE64)
- [x] Task 23: 部署與測試 ✅ https://line-bot4.zeabur.app
- [x] Task 24: 設定固定 Webhook URL

**成果：** Bot 24/7 運行於 Zeabur，固定網址 `line-bot4.zeabur.app`

---

## ⬜ Phase 5: 進階功能 (PLANNED)
- [ ] Task 25: 自訂摘要風格 (簡短/詳細/條列)
- [ ] Task 26: 多語言摘要支援
- [ ] Task 27: Notion 分類資料夾
- [ ] Task 28: 使用統計與回顧
- [ ] Task 29: 更多社群平台 (IG/Twitter)

---

# 📊 Progress Summary

| Phase | 名稱 | 狀態 | 進度 |
|-------|------|------|------|
| 1 | MVP Foundation | ✅ 完成 | 10/10 |
| 4 | 社群貼文支援 | ✅ 完成 | 6/6 |
| 2 | 圖片支援 | ✅ 完成 | 9/9 |
| 2.5 | 多 AI 提供者 | ✅ 完成 | 3/3 |
| 3 | 雲端部署 (Zeabur) | ✅ 完成 | 5/5 |
| 5 | 進階功能 | ⬜ 待開始 | 0/5 |

---

# 🚀 Current Focus

**Phase 3 已完成！** Bot 已部署至 Zeabur：
- 🌐 URL: https://line-bot4.zeabur.app
- ✅ Webhook: https://line-bot4.zeabur.app/webhook

**可選下一步：**
- Phase 5: 進階功能 (自訂摘要風格、多語言等)

---

# 💎 Memory Crystal

```
Project: Line Bot Content Saver
Phase: 3 (雲端部署) ✅ COMPLETED
Status: Bot deployed and running on Zeabur 24/7
Production URL: https://line-bot4.zeabur.app

Key Changes (2026-02-03):
- Zeabur Deployment: 自動偵測 Python + Procfile
- Environment Variables: 完整設定於 Zeabur Dashboard
- Google OAuth: GOOGLE_CREDENTIALS_BASE64 + GOOGLE_TOKEN_BASE64 雲端還原
- Fixed Webhook: https://line-bot4.zeabur.app/webhook

Deployment Files:
- main.py (根目錄入口點，支援 PORT 環境變數)
- Procfile (uvicorn 啟動指令)
- requirements.txt (所有依賴)

Cloud Environment Variables:
- LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
- GEMINI_API_KEY, OPENAI_API_KEY, AI_PROVIDER
- NOTION_API_KEY, NOTION_DATABASE_ID
- APIFY_API_TOKEN
- GOOGLE_CREDENTIALS_BASE64, GOOGLE_TOKEN_BASE64, GOOGLE_DRIVE_FOLDER_ID

Completed Phases:
- Phase 1: MVP Foundation ✅
- Phase 4: 社群貼文支援 ✅
- Phase 2: 圖片支援 ✅
- Phase 2.5: 多 AI 提供者 ✅
- Phase 3: 雲端部署 (Zeabur) ✅
```
