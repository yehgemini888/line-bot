#!/bin/bash
# Switch Telegram webhook to LOCAL development (ngrok)
# Usage: ./dev_local.sh https://xxx.ngrok-free.app

# Load environment variables
source .env 2>/dev/null || source ../.env 2>/dev/null

if [ -z "$1" ]; then
    echo "❌ 請提供 ngrok URL"
    echo "   用法: ./dev_local.sh https://xxx.ngrok-free.app"
    exit 1
fi

NGROK_URL=$1
WEBHOOK_URL="${NGROK_URL}/telegram/webhook"

echo "🔄 設定 Telegram Webhook 到本地..."
echo "   URL: $WEBHOOK_URL"

curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}" | python3 -m json.tool

echo ""
echo "✅ 本地開發模式已啟用！"
echo "💡 記得啟動 uvicorn: python3 -m uvicorn src.main:app --reload --port 8000"
