#!/bin/bash
# Switch Telegram webhook to PRODUCTION (Zeabur)
# Usage: ./dev_prod.sh

# Load environment variables
source .env 2>/dev/null || source ../.env 2>/dev/null

# ============================================
# 設定你的 Zeabur 網址
# ============================================
ZEABUR_URL="https://line-bot9.zeabur.app"  # Zeabur 正式環境網址

WEBHOOK_URL="${ZEABUR_URL}/telegram/webhook"

echo "🚀 設定 Telegram Webhook 到 Zeabur..."
echo "   URL: $WEBHOOK_URL"

curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}" | python3 -m json.tool

echo ""
echo "✅ 正式環境模式已啟用！"
