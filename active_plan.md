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

## 🎯 Phase 4: 社群貼文支援 (IN PROGRESS)
- [x] Task 21: 社群網址偵測 (Facebook / Threads)
- [x] Task 22: Domain Layer 擴充 (SocialPlatform Enum)
- [x] Task 23: SummarizeUseCase 擴充 (支援 SOCIAL ContentType)
- [👉] Task 24: Apify Scraper 修復 (Facebook + Threads)
  - [x] 切換 Threads Actor: `apify/threads-profile-api-scraper` → `sinam7/threads-post-scraper`
  - [x] 修正 Facebook 輸出欄位對應
  - [ ] 實際測試驗證
- [ ] Task 25: 整合測試 (Line Bot + Social Posts)

**預期成果：** 使用者可傳送 Facebook/Threads 貼文網址，自動擷取內容並摘要

---

## ⬜ Phase 2: 圖片支援 (PLANNED)
- [ ] Task 11: 擴充 ContentType (新增 IMAGE 類型)
- [ ] Task 12: Image Handler (接收 Line 圖片訊息)
- [ ] Task 13: Gemini Vision Service (圖片分析與描述)
- [ ] Task 14: 整合圖片處理流程
- [ ] Task 15: 測試圖片摘要功能

**預期成果：** 使用者可傳送圖片，AI 會描述圖片內容並儲存至 Notion

---

## ⬜ Phase 3: 雲端部署 (PLANNED)
- [ ] Task 16: Dockerfile 建立
- [ ] Task 17: Railway / Render 部署設定
- [ ] Task 18: 環境變數設定
- [ ] Task 19: 部署與測試
- [ ] Task 20: 設定固定 Webhook URL

**預期成果：** Bot 24/7 運行，不需要每次手動啟動 ngrok

---

## ⬜ Phase 5: 進階功能 (PLANNED)
- [ ] Task 26: 自訂摘要風格 (簡短/詳細/條列)
- [ ] Task 27: 多語言摘要支援
- [ ] Task 28: Notion 分類資料夾
- [ ] Task 29: 使用統計與回顧
- [ ] Task 30: 更多社群平台 (IG/Twitter)

---

# 📊 Progress Summary

| Phase | 名稱 | 狀態 | 進度 |
|-------|------|------|------|
| 1 | MVP Foundation | ✅ 完成 | 10/10 |
| 4 | 社群貼文支援 | 👉 進行中 | 3/5 |
| 2 | 圖片支援 | ⬜ 待開始 | 0/5 |
| 3 | 雲端部署 | ⬜ 待開始 | 0/5 |
| 5 | 進階功能 | ⬜ 待開始 | 0/5 |

---

# 🚀 Current Focus

**Task 24: Apify Scraper 修復**

修復內容：
1. ✅ Threads: 改用 `sinam7/threads-post-scraper` (支援單一貼文 URL，使用 `caption` 欄位)
2. ✅ Facebook: 調整 `apify/facebook-posts-scraper` 輸出欄位對應

下一步：
- 進行實際測試驗證爬取功能
- 完成 Phase 4 整合測試

---

# 💎 Memory Crystal

```
Project: Line Bot Content Saver
Phase: 4 (社群貼文支援)
Current Task: 24 - Apify Scraper 修復
Status: Code updated, pending verification

Key Changes (2026-02-02):
- Threads actor: sinam7/threads-post-scraper
- Facebook actor: apify/facebook-posts-scraper
- Output field mapping improved for both platforms

Files Modified:
- src/infrastructure/apify_scraper.py
- spec.md
- active_plan.md
```
