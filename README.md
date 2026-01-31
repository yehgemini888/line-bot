# Line Bot Content Saver

將 Line 訊息中的文字或網址，透過 Gemini AI 摘要分析後儲存至 Notion。

## 功能

- 📝 **文字摘要**：傳送任意文字，AI 自動產生標題、摘要、標籤
- 🔗 **網址摘要**：傳送網址，自動抓取內容並摘要
- 📦 **Notion 整合**：所有內容自動儲存至 Notion 資料庫

---

# 🚀 快速啟動（每次開啟專案）

## Step 1: 開啟終端機，進入專案目錄

```bash
cd "/mnt/c/Users/Benson/Desktop/Line bot"
```

## Step 2: 啟動虛擬環境

```bash
source venv/bin/activate
```

啟動成功後，終端機開頭會顯示 `(venv)`

## Step 3: 啟動伺服器

```bash
python3 -m src.main
```

看到以下訊息表示成功：
```
🚀 Line Bot Content Saver started!
📦 Notion Database ID: 2f9994e1...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: 開啟新終端機視窗，啟動 ngrok

```bash
ngrok http 8000
```

複製產生的 https 網址，例如：
```
https://xxxxx-xxxxx-xxxxx.ngrok-free.dev
```

## Step 5: 更新 Line Webhook URL

1. 前往 [Line Developers Console](https://developers.line.biz/)
2. 進入你的 Channel → Messaging API
3. 找到 Webhook URL → Edit
4. 貼上新網址：`https://你的ngrok網址/webhook`
5. 點選 Update
6. 確認 Use webhook 是開啟狀態

## Step 6: 測試

在 Line 上傳送訊息給你的 Bot，確認收到回覆即可！

---

# 📁 專案結構

```
Line bot/
├── src/
│   ├── domain/
│   │   └── content.py          # Domain Entity
│   ├── usecase/
│   │   ├── summarize.py        # 摘要 UseCase
│   │   └── save_to_notion.py   # 儲存 UseCase
│   ├── infrastructure/
│   │   ├── line_handler.py     # Line Webhook
│   │   ├── gemini_service.py   # Gemini AI
│   │   ├── notion_repo.py      # Notion Repository
│   │   └── web_scraper.py      # 網頁抓取
│   └── main.py                 # FastAPI Entry
├── venv/                       # Python 虛擬環境
├── .env                        # 環境變數（API Keys）
├── .env.example                # 環境變數範本
├── requirements.txt            # Python 依賴
├── spec.md                     # 技術規格
├── active_plan.md              # 開發計畫
└── README.md                   # 本文件
```

---

# 🔧 首次安裝（僅需一次）

如果是全新環境，需要先完成以下設定：

## 1. 安裝 Python

```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

## 2. 建立虛擬環境

```bash
cd "/mnt/c/Users/Benson/Desktop/Line bot"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. 設定環境變數

複製 `.env.example` 為 `.env`，填入 API Keys：

```bash
cp .env.example .env
```

需要的 API Keys：
- **LINE_CHANNEL_ACCESS_TOKEN** - [Line Developers Console](https://developers.line.biz/)
- **LINE_CHANNEL_SECRET** - [Line Developers Console](https://developers.line.biz/)
- **GEMINI_API_KEY** - [Google AI Studio](https://aistudio.google.com/)
- **NOTION_API_KEY** - [Notion Integrations](https://www.notion.so/my-integrations)
- **NOTION_DATABASE_ID** - 從 Notion Database URL 取得

## 4. 安裝 ngrok

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok -y
ngrok config add-authtoken 你的authtoken
```

## 5. Notion Database 欄位

確保 Notion Database 有以下欄位：

| 欄位名稱 | 類型 |
|---------|------|
| Title | Title |
| Summary | Text |
| Content | Text |
| Source URL | URL |
| Type | Select (text, url) |
| Tags | Multi-select |
| Created | Date |

---

# 🛠️ 常見問題

## Q: ngrok 網址每次都不一樣？
A: 免費版限制。每次重啟需更新 Line Webhook URL。付費版可固定網址。

## Q: Gemini API 報錯 429？
A: 免費額度用盡，等待一分鐘後重試，或升級付費方案。

## Q: Notion 儲存失敗？
A: 檢查欄位名稱是否與上表一致（注意大小寫）。

## Q: 如何停止伺服器？
A: 在終端機按 `Ctrl + C`

---

# 📚 相關資源

- [Line Messaging API 文件](https://developers.line.biz/en/docs/messaging-api/)
- [Google Gemini API 文件](https://ai.google.dev/docs)
- [Notion API 文件](https://developers.notion.com/)

---

# 📜 License

MIT
