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
| 4 | 社群貼文支援 | ✅ 完成 | 6/6 |
| 2 | 圖片支援 | ⬜ 待開始 | 0/5 |
| 3 | 雲端部署 | ⬜ 待開始 | 0/5 |
| 5 | 進階功能 | ⬜ 待開始 | 0/5 |

---

# 🚀 Current Focus

**Phase 4 已完成！** 可進入下一階段：
- Phase 2: 圖片支援 (Gemini Vision)
- Phase 3: 雲端部署 (Railway/Render)

---

# 💎 Memory Crystal

```
Project: Line Bot Content Saver
Phase: 4 (社群貼文支援) ✅ COMPLETED
Status: All features implemented and tested

Key Changes (2026-02-02):
- URL extraction: 支援從混合文字中提取 URL
- Threads scraper: sinam7/threads-post-scraper (修正 URL 截斷問題)
- Facebook scraper: apify/facebook-posts-scraper (支援 Photo 類型)
- Social detector: 使用 search() 取代 match() 進行模式匹配

Files Modified:
- src/infrastructure/line_handler.py (URL 提取邏輯)
- src/infrastructure/social_detector.py (搜尋模式優化)
- src/infrastructure/apify_scraper.py (爬蟲欄位對應)
- src/usecase/summarize.py
- src/usecase/save_to_notion.py
- src/infrastructure/notion_repo.py
- src/domain/content.py
```
