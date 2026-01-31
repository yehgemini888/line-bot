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

## 🎯 Phase 2: 圖片支援 (NEXT)
- [ ] Task 11: 擴充 ContentType (新增 IMAGE 類型)
- [ ] Task 12: Image Handler (接收 Line 圖片訊息)
- [ ] Task 13: Gemini Vision Service (圖片分析與描述)
- [ ] Task 14: 整合圖片處理流程
- [ ] Task 15: 測試圖片摘要功能

**預期成果：** 使用者可傳送圖片，AI 會描述圖片內容並儲存至 Notion

---

## 🌐 Phase 3: 雲端部署
- [ ] Task 16: Dockerfile 建立
- [ ] Task 17: Railway / Render 部署設定
- [ ] Task 18: 環境變數設定
- [ ] Task 19: 部署與測試
- [ ] Task 20: 設定固定 Webhook URL

**預期成果：** Bot 24/7 運行，不需要每次手動啟動 ngrok

---

## 📱 Phase 4: 社群貼文支援
- [ ] Task 21: 社群網址偵測 (IG/FB/Twitter/Threads)
- [ ] Task 22: 社群內容擷取器
- [ ] Task 23: 整合社群處理流程
- [ ] Task 24: 測試社群貼文摘要

**預期成果：** 使用者可傳送社群貼文網址，自動擷取內容並摘要

---

## 🔧 Phase 5: 進階功能
- [ ] Task 25: 自訂摘要風格 (簡短/詳細/條列)
- [ ] Task 26: 多語言摘要支援
- [ ] Task 27: Notion 分類資料夾
- [ ] Task 28: 使用統計與回顧

---

# 📊 Progress Summary

| Phase | 名稱 | 狀態 | 進度 |
|-------|------|------|------|
| 1 | MVP Foundation | ✅ 完成 | 10/10 |
| 2 | 圖片支援 | 🔜 下一步 | 0/5 |
| 3 | 雲端部署 | ⬜ 待開始 | 0/5 |
| 4 | 社群貼文 | ⬜ 待開始 | 0/4 |
| 5 | 進階功能 | ⬜ 待開始 | 0/4 |

---

# 🚀 Next Action

**建議下一步：Phase 2 - 圖片支援**

理由：
1. Gemini 原生支援 Vision (圖片分析)，實作成本低
2. 圖片是 Line 常見的訊息類型
3. 不需要額外 API，只需擴充現有架構

**或者：Phase 3 - 雲端部署**

理由：
1. 目前每次都需要手動啟動 ngrok
2. 部署後可 24/7 運行
3. 可以分享給其他人使用

---

請選擇你想進行的下一步：
- **A) Phase 2: 圖片支援** - 讓 Bot 能處理圖片
- **B) Phase 3: 雲端部署** - 讓 Bot 24/7 運行
- **C) 其他** - 你有其他想法
