# Hướng Dẫn Sử Dụng LLM News Crawler Bot

Bot crawl nội dung chi tiết từng bài viết tin tức, có hỗ trợ đăng nhập và sử dụng LLM để phân tích.

## 📋 Mục Lục

1. [Giới Thiệu](#giới-thiệu)
2. [Cài Đặt](#cài-đặt)
3. [Cấu Hình](#cấu-hình)
4. [Sử Dụng CLI](#sử-dụng-cli)
5. [Sử Dụng API](#sử-dụng-api)
6. [Kết Quả](#kết-quả)

---

## 🎯 Giới Thiệu

**LLM News Crawler Bot** là module độc lập trong TrendRadar, chuyên dụng để:

- ✅ Crawl **nội dung chi tiết** từng bài viết (không chỉ tiêu đề)
- ✅ Hỗ trợ **đăng nhập** cho các trang yêu cầu (Facebook, Instagram, TikTok, v.v.)
- ✅ Sử dụng **LLM** để phân tích và trích xuất metadata
- ✅ Chụp **screenshot** toàn trang
- ✅ Lưu **HTML** gốc và nội dung đã làm sạch

### So Sánh với TrendRadar Chính

| Tính Năng | TrendRadar | LLM News Crawler Bot |
|-----------|------------|---------------------|
| Mục đích | Crawl danh sách tin hot | Crawl nội dung chi tiết từng bài |
| Đăng nhập | Không | Có (CDP profiles) |
| Output | HTML report tổng hợp | Thư mục riêng cho từng bài |
| LLM | Phân tích xu hướng | Trích xuất metadata + nội dung |
| Chạy | Tự động theo lịch | Theo yêu cầu (API/CLI) |

---

## 🔧 Cài Đặt

### Bước 1: Cài đặt dependencies (ĐÃ HOÀN THÀNH)

```bash
# Đã cài đặt vào venv chung của TrendRadar
cd /home/aimond/ProjectNews/TrendRadar
./venv/bin/pip install beautifulsoup4 fastapi httpx lxml playwright pydantic python-dotenv uvicorn
./venv/bin/playwright install chromium
```

### Bước 2: Kiểm tra cài đặt

```bash
cd llm_news_crawler_bot
../venv/bin/python -m news_crawler_bot.cli --help
```

Nếu thấy help message → Cài đặt thành công! ✅

---

## ⚙️ Cấu Hình

### File `.env` (ĐÃ TẠO)

File cấu hình đã được tạo tại: `llm_news_crawler_bot/.env`

**Các tham số quan trọng:**

```env
# 9Router Configuration
ROUTER_BASE_URL=http://localhost:20128/v1
ROUTER_API_KEY=sk-your-9router-key          # ⚠️ CẦN ĐIỀN API KEY
ROUTER_MODEL=ag/gemini-3.1-pro-low

# Browser Configuration
PLAYWRIGHT_HEADLESS=true                     # true = không hiện cửa sổ browser
PLAYWRIGHT_TIMEOUT_MS=60000                  # Timeout 60 giây

# Output
OUTPUT_DIR=output                            # Thư mục lưu kết quả
```

**⚠️ QUAN TRỌNG:** Bạn cần điền `ROUTER_API_KEY` với API key thực của 9Router!

---

## 💻 Sử Dụng CLI

### 1. Crawl trang KHÔNG cần đăng nhập

```bash
cd llm_news_crawler_bot
../venv/bin/python -m news_crawler_bot.cli \
  --url "https://vnexpress.net/some-article"
```

### 2. Crawl trang CẦN đăng nhập

```bash
../venv/bin/python -m news_crawler_bot.cli \
  --url "https://example.com/news" \
  --username "your_username" \
  --password "your_password"
```

### 3. Crawl với job ID tùy chỉnh

```bash
../venv/bin/python -m news_crawler_bot.cli \
  --url "https://vnexpress.net/some-article" \
  --job-id "vnexpress_20260529"
```

### 4. Bật chế độ debug

```bash
../venv/bin/python -m news_crawler_bot.cli \
  --url "https://vnexpress.net/some-article" \
  --verbose
```

---

## 🌐 Sử Dụng API

### 1. Khởi động API Server

**Cách 1: Dùng script có sẵn**
```bash
cd llm_news_crawler_bot
./start_api.sh
```

**Cách 2: Chạy trực tiếp**
```bash
cd llm_news_crawler_bot
../venv/bin/python -m uvicorn news_crawler_bot.api:app --host 127.0.0.1 --port 8010
```

Server sẽ chạy tại:
- 🌐 **Web UI**: http://127.0.0.1:8010/
- 📚 **API Docs**: http://127.0.0.1:8010/docs
- 🔌 **API Endpoint**: http://127.0.0.1:8010/api/

### 2. Gọi API để crawl

**Tạo job mới:**
```bash
curl -X POST http://127.0.0.1:8010/api/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://vnexpress.net/some-article",
    "username": "",
    "password": "",
    "instruction": "Lấy nội dung bài viết"
  }'
```

**Response:**
```json
{
  "job_id": "job_abc123",
  "status": "pending",
  "message": "Job created successfully"
}
```

### 3. Kiểm tra trạng thái job

```bash
curl http://127.0.0.1:8010/api/jobs/job_abc123
```

**Response:**
```json
{
  "job_id": "job_abc123",
  "status": "completed",
  "items": [
    {
      "item_id": "item_001",
      "title": "Tiêu đề bài viết",
      "url": "https://...",
      "content_path": "output/job_abc123/items/item_001/content.txt"
    }
  ]
}
```

### 4. Dừng job đang chạy

```bash
curl -X POST http://127.0.0.1:8010/api/jobs/job_abc123/stop
```

---

## 📦 Kết Quả

### Cấu trúc thư mục output

```
llm_news_crawler_bot/output/
└── job_abc123/                    # Thư mục job
    ├── metadata.json              # Metadata tổng quan
    └── items/                     # Danh sách items
        └── item_001/              # Thư mục từng item
            ├── metadata.json      # Metadata chi tiết
            ├── content.txt        # Nội dung đã làm sạch
            ├── screenshot.png     # Ảnh chụp màn hình
            └── page.html          # HTML gốc
```

### Nội dung metadata.json (item)

```json
{
  "item_id": "item_001",
  "url": "https://vnexpress.net/...",
  "title": "Tiêu đề bài viết",
  "author": "Tác giả",
  "published_date": "2026-05-29T10:00:00",
  "description": "Mô tả ngắn",
  "content_length": 1234,
  "screenshot_path": "screenshot.png",
  "html_path": "page.html",
  "extracted_at": "2026-05-29T15:30:00"
}
```

---

## 🔐 Đăng Nhập Tự Động (CDP)

Với các trang khó đăng nhập tự động (Facebook, Instagram, TikTok):

### 1. Bật Auto CDP

Trong file `.env`:
```env
AUTO_CDP=true
AUTO_CDP_CREATE=true
AUTO_CDP_CREATE_DOMAINS=facebook.com,instagram.com,tiktok.com
```

### 2. Lần đầu crawl

- Bot sẽ mở Chrome với CDP profile
- Bạn **đăng nhập thủ công** trong cửa sổ Chrome đó
- Session sẽ được lưu vào `.cdp_profiles/`

### 3. Lần sau

- Bot tự động load session đã lưu
- Không cần đăng nhập lại

---

## 🎯 Use Cases

### 1. Crawl chi tiết bài viết từ TrendRadar

```bash
# Bước 1: TrendRadar tìm tin hot
python -m trendradar

# Bước 2: Lấy URL từ HTML report
# Bước 3: Crawl chi tiết bằng llm_news_crawler_bot
cd llm_news_crawler_bot
../venv/bin/python -m news_crawler_bot.cli \
  --url "https://vnexpress.net/hot-article"
```

### 2. Crawl hàng loạt qua API

```python
import requests

urls = [
    "https://vnexpress.net/article1",
    "https://vnexpress.net/article2",
    "https://vnexpress.net/article3"
]

for url in urls:
    response = requests.post(
        "http://127.0.0.1:8010/api/crawl",
        json={"url": url, "instruction": "Lấy nội dung"}
    )
    print(f"Created job: {response.json()['job_id']}")
```

### 3. Crawl Facebook group posts

```bash
# Lần đầu: Đăng nhập thủ công
../venv/bin/python -m news_crawler_bot.cli \
  --url "https://www.facebook.com/groups/your-group" \
  --verbose

# Lần sau: Tự động dùng session đã lưu
../venv/bin/python -m news_crawler_bot.cli \
  --url "https://www.facebook.com/groups/your-group/posts/123"
```

---

## 🐛 Troubleshooting

### Lỗi: "ROUTER_API_KEY not configured"

**Nguyên nhân:** Chưa điền API key trong `.env`

**Giải pháp:**
```bash
cd llm_news_crawler_bot
nano .env  # Hoặc dùng editor khác
# Sửa dòng: ROUTER_API_KEY=sk-your-actual-key
```

### Lỗi: "Playwright browser not found"

**Nguyên nhân:** Chưa cài Chromium

**Giải pháp:**
```bash
../venv/bin/playwright install chromium
```

### Lỗi: "Connection refused to 127.0.0.1:20128"

**Nguyên nhân:** 9Router chưa chạy hoặc sai port

**Giải pháp:**
1. Kiểm tra 9Router đang chạy
2. Kiểm tra port trong `.env` khớp với 9Router

### Browser mở nhưng không crawl được

**Nguyên nhân:** Timeout quá ngắn hoặc trang load chậm

**Giải pháp:**
```env
# Tăng timeout trong .env
PLAYWRIGHT_TIMEOUT_MS=120000  # 2 phút
```

---

## 📚 Tài Liệu Tham Khảo

- **TrendRadar README**: `/home/aimond/ProjectNews/TrendRadar/README.md`
- **API Documentation**: http://127.0.0.1:8010/docs (khi server đang chạy)
- **Playwright Docs**: https://playwright.dev/python/

---

## ✅ Checklist Cài Đặt

- [x] Cài đặt dependencies vào venv
- [x] Cài đặt Playwright Chromium
- [x] Tạo file `.env`
- [ ] **Điền ROUTER_API_KEY vào `.env`** ⚠️
- [x] Test CLI: `../venv/bin/python -m news_crawler_bot.cli --help`
- [ ] Test API: `./start_api.sh`
- [ ] Crawl thử 1 bài viết

---

**🎉 Chúc bạn sử dụng thành công!**
