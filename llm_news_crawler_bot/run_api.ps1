$ErrorActionPreference = "Stop"
python -m uvicorn news_crawler_bot.api:app `
  --host 127.0.0.1 `
  --port 8010 `
  --loop asyncio
