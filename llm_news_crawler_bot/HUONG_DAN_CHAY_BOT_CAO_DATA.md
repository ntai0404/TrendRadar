# Huong dan set va chay bot cao data

Thu muc nay chua bot crawl tin/bai viet co LLM tham gia lap ke hoach dieu huong, chon target, trich xuat metadata, noi dung va anh chup rieng cho tung item.

## 1. Yeu cau

- Windows + PowerShell.
- Python 3.11+.
- 9Router dang chay local, mac dinh OpenAI-compatible endpoint: `http://127.0.0.1:20128/v1`.
- Chrome/Chromium cho Playwright. Bot co the dung Chromium bundled hoac Chrome CDP.

## 2. Cai dat

```powershell
cd C:\SINHVIEN\myprocj\AAA-temp\26-5-26\TrendRadar\llm_news_crawler_bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

Mo `.env` va dien key/router that:

```env
ROUTER_BASE_URL=http://127.0.0.1:20128/v1
ROUTER_API_KEY=sk-your-9router-key
ROUTER_MODEL=ag/gemini-3.1-pro-low
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT_MS=60000
OUTPUT_DIR=output
```

Khong commit `.env`, `.venv`, `.cdp_profiles`, `output` hoac log.

## 3. Chay giao dien web

Chay foreground:

```powershell
python -m uvicorn news_crawler_bot.api:app --host 127.0.0.1 --port 8010
```

Mo trinh duyet:

```text
http://127.0.0.1:8010/
```

Chay background bang script:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_background.ps1
```

Dung server:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_server.ps1
```

Restart server:

```powershell
powershell -ExecutionPolicy Bypass -File .\restart_server.ps1
```

## 4. Cach nhap job

Trong UI:

- `URL bai viet`: URL nguon, vi du `https://vnexpress.net/` hoac `https://www.facebook.com`.
- `Tai khoan`, `Mat khau`: bo trong neu khong can login.
- `Cau lenh chi tiet`: ghi ro so luong, chu de, nen mo tung item hay lay tu listing.

Vi du:

```text
lay 10 bai moi ve chung khoan
```

```text
cao 5 bai ve chung khoan 5 bai ve AI
```

```text
lay du lieu cac bai viet moi nhat cua group https://www.facebook.com/groups/comailo
```

Bot se tach cac goal rieng neu cau lenh co nhieu quota/chu de, vi du `5 bai chung khoan + 5 bai AI`.

## 5. Dau ra

Moi job ghi vao:

```text
output/<job_id>/
```

Moi item co thu muc rieng:

```text
output/<job_id>/items/item_001/
  metadata.json
  screenshot.png
  content.txt
  page.html
```

Manifest tong:

```text
output/<job_id>/metadata.json
```

Moi item co metadata va anh rieng, khong dung chung metadata/anh cho ca job.

## 6. CDP va login

Voi cac trang kho login bang username/password nhu Facebook, Instagram, TikTok:

- `AUTO_CDP=true` cho phep bot tu tao Chrome CDP profile neu chua co session.
- Lan dau vao domain social, bot mo Chrome/CDP de user login thu cong.
- Session se luu trong `.cdp_profiles` va duoc tai su dung o lan sau.

Neu khong co CDP phu hop, bot fallback sang browser bundled theo `AUTO_CDP_FALLBACK_MODE=bundled`.

## 7. Kiem tra job bang API

```powershell
Invoke-RestMethod http://127.0.0.1:8010/api/jobs/<job_id>
```

Dung job dang chay:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8010/api/jobs/<job_id>/stop
```

## 8. Ghi chu chat luong

- Bot uu tien URL detail that, cung domain voi nguon, tranh link quang cao/redirect.
- Metadata uu tien JSON-LD, OpenGraph, article meta, `time[datetime]`, sau do moi den LLM.
- Neu trang co nhieu chu de/nhieu quota, bot goi LLM de tach thanh cac goal doc lap truoc khi crawl.
