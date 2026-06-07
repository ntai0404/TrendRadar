# Tích Hợp TrendRadar + LLM News Crawler Bot

Hướng dẫn sử dụng kết hợp hai module để có workflow hoàn chỉnh.

---

## 🎯 Workflow Tổng Quan

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKFLOW HOÀN CHỈNH                      │
└─────────────────────────────────────────────────────────────┘

1. TrendRadar (Module Chính)
   ↓
   Crawl danh sách tin hot từ các nền tảng + RSS
   ↓
   Tạo HTML report với links
   ↓
   
2. LLM News Crawler Bot (Module Bổ Sung)
   ↓
   Chọn tin quan tâm từ HTML report
   ↓
   Crawl chi tiết nội dung từng bài
   ↓
   Lưu full content + screenshot + metadata
```

---

## 📁 Cấu Trúc Project

```
TrendRadar/
├── trendradar/                    # Module chính
│   ├── __main__.py               # Entry point
│   ├── crawler/                  # Crawl tin hot
│   ├── notification/             # Gửi thông báo
│   └── report/                   # Tạo HTML report
│
├── llm_news_crawler_bot/         # Module bổ sung
│   ├── news_crawler_bot/         # Core logic
│   │   ├── api.py               # API server
│   │   ├── cli.py               # CLI interface
│   │   └── crawler.py           # Crawler engine
│   ├── .env                      # Config (ĐÃ TẠO)
│   ├── start_api.sh              # Script khởi động API
│   └── HUONG_DAN_SU_DUNG.md     # Hướng dẫn chi tiết
│
├── venv/                          # Virtual environment CHUNG
├── config/                        # Config chung
│   └── config.yaml               # Cấu hình TrendRadar
└── output/                        # Output chung
    ├── html/                     # TrendRadar HTML reports
    └── llm_news_crawler_bot/     # Bot crawl results
```

---

## 🚀 Cài Đặt (ĐÃ HOÀN THÀNH)

### ✅ Đã cài đặt:

1. ✅ Virtual environment chung: `/home/aimond/ProjectNews/TrendRadar/venv/`
2. ✅ Dependencies TrendRadar
3. ✅ Dependencies LLM News Crawler Bot
4. ✅ Playwright Chromium
5. ✅ File `.env` cho bot
6. ✅ Script khởi động API

### ⚠️ CẦN LÀM:

**Điền API Key vào file `.env`:**

```bash
cd /home/aimond/ProjectNews/TrendRadar/llm_news_crawler_bot
nano .env

# Sửa dòng:
ROUTER_API_KEY=sk-your-actual-9router-key
```

---

## 💡 Use Cases Thực Tế

### Use Case 1: Tìm Tin Hot → Đọc Chi Tiết

**Bước 1: Chạy TrendRadar để tìm tin hot**

```bash
cd /home/aimond/ProjectNews/TrendRadar
./venv/bin/python -m trendradar
```

**Kết quả:**
- HTML report: `output/html/2026-05-29/15-35.html`
- Danh sách tin hot từ VnExpress, Tuổi Trẻ, Dân Trí

**Bước 2: Mở HTML report và chọn tin quan tâm**

```bash
# Mở bằng browser
firefox output/html/latest/current.html
```

**Bước 3: Copy URL tin muốn đọc chi tiết**

Ví dụ: `https://vnexpress.net/some-interesting-article-123456.html`

**Bước 4: Crawl chi tiết bằng Bot**

```bash
cd llm_news_crawler_bot
../venv/bin/python -m news_crawler_bot.cli \
  --url "https://vnexpress.net/some-interesting-article-123456.html"
```

**Kết quả:**
```
output/job_abc123/items/item_001/
├── content.txt        # Nội dung đầy đủ
├── screenshot.png     # Ảnh chụp màn hình
├── metadata.json      # Metadata chi tiết
└── page.html          # HTML gốc
```

---

### Use Case 2: Crawl Hàng Loạt Qua API

**Bước 1: Khởi động API Server**

```bash
cd /home/aimond/ProjectNews/TrendRadar/llm_news_crawler_bot
./start_api.sh
```

**Bước 2: Tạo script Python để crawl hàng loạt**

```python
#!/usr/bin/env python3
# crawl_batch.py

import requests
import time
import json

# Danh sách URL từ TrendRadar HTML report
urls = [
    "https://vnexpress.net/article1",
    "https://vnexpress.net/article2",
    "https://vnexpress.net/article3",
]

API_BASE = "http://127.0.0.1:8010/api"

# Tạo jobs
job_ids = []
for url in urls:
    response = requests.post(
        f"{API_BASE}/crawl",
        json={
            "url": url,
            "instruction": "Lấy toàn bộ nội dung bài viết"
        }
    )
    job_id = response.json()["job_id"]
    job_ids.append(job_id)
    print(f"✅ Created job: {job_id} for {url}")

# Đợi và kiểm tra kết quả
print("\n⏳ Waiting for jobs to complete...")
time.sleep(30)  # Đợi 30 giây

for job_id in job_ids:
    response = requests.get(f"{API_BASE}/jobs/{job_id}")
    result = response.json()
    print(f"\n📊 Job {job_id}:")
    print(f"   Status: {result['status']}")
    if result['status'] == 'completed':
        print(f"   Items: {len(result.get('items', []))}")
```

**Chạy script:**

```bash
cd /home/aimond/ProjectNews/TrendRadar
./venv/bin/python crawl_batch.py
```

---

### Use Case 3: Tự Động Hóa Hoàn Toàn

**Tạo script tự động:**

```bash
#!/bin/bash
# auto_crawl.sh

cd /home/aimond/ProjectNews/TrendRadar

echo "════════════════════════════════════════════════════════════"
echo "  BƯỚC 1: Crawl tin hot bằng TrendRadar"
echo "════════════════════════════════════════════════════════════"
./venv/bin/python -m trendradar

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  BƯỚC 2: Trích xuất top 5 URL từ HTML report"
echo "════════════════════════════════════════════════════════════"

# Parse HTML để lấy top 5 URLs (cần cài jq hoặc dùng Python)
# Ví dụ đơn giản:
TOP_URLS=(
    "https://vnexpress.net/article1"
    "https://vnexpress.net/article2"
    "https://vnexpress.net/article3"
)

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  BƯỚC 3: Crawl chi tiết từng bài"
echo "════════════════════════════════════════════════════════════"

cd llm_news_crawler_bot
for url in "${TOP_URLS[@]}"; do
    echo "📰 Crawling: $url"
    ../venv/bin/python -m news_crawler_bot.cli --url "$url"
done

echo ""
echo "✅ HOÀN THÀNH!"
```

---

## 🔧 Cấu Hình Chung

### 1. Cấu Hình 9Router (CHUNG cho cả 2 module)

**TrendRadar:** `config/config.yaml`
```yaml
ai:
  model: "openai/ag/gemini-3.1-pro-low"
  api_key: "sk-your-key"
  api_base: "http://localhost:20128/v1"
```

**LLM Bot:** `llm_news_crawler_bot/.env`
```env
ROUTER_BASE_URL=http://localhost:20128/v1
ROUTER_API_KEY=sk-your-key
ROUTER_MODEL=ag/gemini-3.1-pro-low
```

⚠️ **Lưu ý:** API Key phải giống nhau!

### 2. Cấu Hình Output

**TrendRadar:** Lưu vào `output/html/`
**LLM Bot:** Lưu vào `llm_news_crawler_bot/output/`

Có thể thay đổi trong `.env`:
```env
OUTPUT_DIR=../output/llm_crawler  # Lưu chung với TrendRadar
```

---

## 📊 So Sánh Hai Module

| Tiêu Chí | TrendRadar | LLM News Crawler Bot |
|----------|------------|---------------------|
| **Mục đích** | Tìm tin hot | Đọc chi tiết |
| **Input** | Config platforms/RSS | URL cụ thể |
| **Output** | HTML report | Full content + screenshot |
| **Chạy** | Tự động theo lịch | Theo yêu cầu |
| **LLM** | Phân tích xu hướng | Trích xuất nội dung |
| **Đăng nhập** | Không | Có (CDP) |
| **Thời gian** | Nhanh (chỉ metadata) | Chậm (full content) |

---

## 🎯 Khi Nào Dùng Module Nào?

### Dùng TrendRadar khi:
- ✅ Muốn xem tổng quan tin hot
- ✅ Theo dõi nhiều nguồn cùng lúc
- ✅ Cần báo cáo định kỳ
- ✅ Chỉ cần tiêu đề + link

### Dùng LLM Bot khi:
- ✅ Cần đọc full content bài viết
- ✅ Cần screenshot để lưu trữ
- ✅ Crawl trang cần đăng nhập
- ✅ Phân tích chi tiết từng bài

### Dùng CẢ HAI khi:
- ✅ Workflow: Tìm tin hot → Đọc chi tiết
- ✅ Cần cả tổng quan lẫn chi tiết
- ✅ Xây dựng knowledge base

---

## 🐛 Troubleshooting

### Lỗi: Module not found

**Nguyên nhân:** Chạy sai thư mục

**Giải pháp:**
```bash
# TrendRadar: Chạy từ thư mục gốc
cd /home/aimond/ProjectNews/TrendRadar
./venv/bin/python -m trendradar

# LLM Bot: Chạy từ thư mục llm_news_crawler_bot
cd /home/aimond/ProjectNews/TrendRadar/llm_news_crawler_bot
../venv/bin/python -m news_crawler_bot.cli --url "..."
```

### Lỗi: API Key không hoạt động

**Kiểm tra:**
1. API Key giống nhau trong `config.yaml` và `.env`
2. 9Router đang chạy
3. Port đúng (20128)

### Lỗi: Output không tìm thấy

**TrendRadar output:**
```bash
ls -la output/html/latest/
```

**LLM Bot output:**
```bash
ls -la llm_news_crawler_bot/output/
```

---

## 📚 Tài Liệu

- **TrendRadar:** `README.md`
- **LLM Bot:** `llm_news_crawler_bot/HUONG_DAN_SU_DUNG.md`
- **API Docs:** http://127.0.0.1:8010/docs (khi API đang chạy)

---

## ✅ Checklist Hoàn Chỉnh

### TrendRadar
- [x] Cài đặt dependencies
- [x] Cấu hình `config.yaml`
- [x] Test chạy: `./venv/bin/python -m trendradar`
- [x] Kiểm tra HTML output

### LLM News Crawler Bot
- [x] Cài đặt dependencies
- [x] Cài đặt Playwright
- [x] Tạo file `.env`
- [ ] **Điền API Key vào `.env`** ⚠️
- [ ] Test CLI
- [ ] Test API

### Tích Hợp
- [ ] Chạy TrendRadar → Lấy URLs
- [ ] Crawl chi tiết bằng Bot
- [ ] Kiểm tra output cả 2 module

---

**🎉 Chúc bạn sử dụng thành công!**

Nếu có vấn đề, hãy kiểm tra:
1. 9Router đang chạy
2. API Key đã điền
3. Chạy đúng thư mục
4. Virtual environment đã activate
