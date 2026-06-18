# TrendRadar — Hệ thống theo dõi tin tức tài chính Việt Nam

Tự động crawl tin tức từ 8 nguồn RSS + 8 trang Facebook, phân loại bằng AI, phân tích xu hướng và xuất báo cáo HTML.

## Cài đặt nhanh

```powershell
cd C:\SINHVIEN\myprocj\TrendRadar
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pip install -r llm_news_crawler_bot\requirements.txt
.venv\Scripts\playwright install chromium
```

## Chạy

```powershell
$env:PYTHONIOENCODING="utf-8"; .venv\Scripts\python -m trendradar
```

### Yêu cầu
- Python 3.11+
- 9Router chạy tại `localhost:20128`
- Chrome CDP profile đã login Facebook (tại `llm_news_crawler_bot/.cdp_profiles/`)

## Cấu hình

| File | Mô tả |
|------|--------|
| `config/config.yaml` | Cấu hình chính (RSS, AI model, notification, report) |
| `config/ai_interests.txt` | 11 chủ đề AI filter (tiếng Việt) |
| `config/frequency_words.txt` | Từ khóa filter backup (tiếng Việt) |
| `config/llm_crawler_sources.yaml` | Nguồn crawl bot (Facebook, web) |
| `llm_news_crawler_bot/.env` | API key, model, CDP, accounts MXH |

## Output

- **HTML Report**: `output/html/YYYY-MM-DD/HH-MM.html`
- **Latest**: `output/html/latest/current.html`
- **Bot output**: `llm_news_crawler_bot/output/<job_id>/`

## Models (qua 9Router)

- Chính: `ag/claude-sonnet-4-6`
- Fallback 1: `ag/gemini-3.1-pro-high`
- Fallback 2: `gc/gemini-3-pro-preview`

## Trạng thái

Xem chi tiết tại [TRANG_THAI_DU_AN.md](./TRANG_THAI_DU_AN.md)

**Còn cần**: Điền Telegram bot_token + chat_id vào `config/config.yaml` để nhận thông báo.
