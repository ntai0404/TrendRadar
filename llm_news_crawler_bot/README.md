# LLM News Crawler Bot

Bot crawl trang tin tuc co dang nhap tuy chon, co LLM tham gia suy luan selector va trich xuat noi dung.

## Dau vao

- `url`: link trang tin tuc
- `username`: tai khoan, co the bo trong
- `password`: mat khau, co the bo trong

## Dau ra

Moi job tao mot thu muc trong `output/<job_id>/`:

- `metadata.json`: metadata, noi dung sach, thong tin anh chup
- `article.txt`: noi dung bai viet da lam sach
- `screenshot.png`: anh chup toan trang tin tuc
- `page.html`: HTML sau khi dang nhap va tai trang

## Cai dat

```powershell
cd llm_news_crawler_bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

Sua `.env` neu can. Mac dinh bot dung 9Router local giong `hyper-MAS`:

```env
ROUTER_BASE_URL=http://127.0.0.1:20128/v1
ROUTER_API_KEY=sk-...
ROUTER_MODEL=openai/ag/gemini-3.1-pro-low
```

## Chay bang CLI

```powershell
python -m news_crawler_bot.cli --url "https://example.com/news" --username "acc" --password "pass"
```

Neu trang khong can dang nhap:

```powershell
python -m news_crawler_bot.cli --url "https://example.com/news"
```

## Chay API

```powershell
python -m uvicorn news_crawler_bot.api:app --host 127.0.0.1 --port 8010
```

Goi API:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8010/api/crawl `
  -ContentType "application/json" `
  -Body '{"url":"https://example.com/news","username":"acc","password":"pass"}'
```

Xem ket qua:

```powershell
Invoke-RestMethod http://127.0.0.1:8010/api/jobs/<job_id>
```
