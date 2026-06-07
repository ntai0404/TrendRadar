#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#           LLM News Crawler Bot - API Server Starter
# ═══════════════════════════════════════════════════════════════

cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════"
echo "  Starting LLM News Crawler Bot API Server"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  API Endpoint: http://127.0.0.1:8010"
echo "  Web UI:       http://127.0.0.1:8010/"
echo "  API Docs:     http://127.0.0.1:8010/docs"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Activate virtual environment and start server
../venv/bin/python -m uvicorn news_crawler_bot.api:app --host 127.0.0.1 --port 8010
