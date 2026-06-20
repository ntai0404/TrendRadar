# Trạng Thái Dự Án TrendRadar

> Cập nhật: 2026-06-20
> Nhánh: `ntai0404-update`

---

## Tổng quan

TrendRadar là hệ thống **tự động thu thập, phân loại và phân tích tin tức tài chính/kinh doanh Việt Nam** bằng AI, xuất báo cáo HTML và gửi thông báo đến các kênh (Telegram, Email, v.v.).

---

## Kiến trúc hệ thống

```
┌──────────────────────────────────────────────────────────────┐
│                     TrendRadar Pipeline                        │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐  ┌─────────────────┐  ┌────────────────┐   │
│  │  RSS Crawl  │  │ LLM Crawler Bot │  │External Sources│   │
│  │  (8 nguồn)  │  │ (Facebook CDP)  │  │(Twitter,YT,GH) │   │
│  └──────┬──────┘  └───────┬─────────┘  └───────┬────────┘   │
│         │                  │                     │            │
│         └──────────┬───────┴─────────────────────┘            │
│                    ▼                                           │
│         ┌─────────────────┐     ┌─────────────┐              │
│         │  SQLite Storage │     │  AI Filter  │              │
│         └────────┬────────┘     │  (Gemini)   │              │
│                  │              └──────┬──────┘              │
│                  ▼                     │                      │
│         ┌─────────────────┐           │                      │
│         │  AI Analysis    │◄──────────┘                      │
│         │  (Gemini Flash) │                                   │
│         └────────┬────────┘                                   │
│                  │                                             │
│         ┌────────┴────────┐                                   │
│         ▼                 ▼                                   │
│  ┌────────────┐   ┌──────────────┐                           │
│  │ HTML Report│   │ Notification │ (Telegram, Email, v.v.)   │
│  │ (multi-tab)│   └──────────────┘                           │
│  └────────────┘                                               │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## Cấu trúc thư mục chính

```
TrendRadar/
├── .venv/                          # Python virtual environment
├── config/
│   ├── config.yaml                 # Cấu hình chính (RSS, AI, notification)
│   ├── ai_interests.txt            # Mô tả sở thích (tiếng Việt, 11 chủ đề)
│   ├── frequency_words.txt         # Từ khóa filter (tiếng Việt)
│   ├── ai_analysis_prompt.txt      # Prompt phân tích AI
│   ├── ai_translation_prompt.txt   # Prompt dịch thuật
│   ├── social_media_prompt.txt     # Prompt crawl MXH
│   ├── llm_crawler_sources.yaml    # Cấu hình nguồn crawl bot
│   ├── timeline.yaml               # Lịch chạy (hiện tắt)
│   └── ai_filter/                  # Prompts cho AI filter
│       ├── prompt.txt
│       ├── extract_prompt.txt
│       └── update_tags_prompt.txt
├── trendradar/                     # Module chính
│   ├── __main__.py                 # Entry point
│   ├── ai/                         # AI analysis, filter, translation
│   ├── crawler/                    # RSS crawler + External Sources
│   │   ├── fetcher.py              # Hot list fetcher (NewsNow API)
│   │   ├── rss/                    # RSS parser + fetcher
│   │   └── sources/                # 🆕 External Sources (Twitter, YT, Reddit, ...)
│   │       ├── base.py             # Base class
│   │       ├── manager.py          # Orchestrator
│   │       ├── twitter.py          # Twitter/X
│   │       ├── youtube.py          # YouTube
│   │       ├── reddit.py           # Reddit
│   │       ├── github_trending.py  # GitHub
│   │       ├── exa_search.py       # Exa AI Search
│   │       ├── podcast.py          # Podcast Transcript
│   │       └── ...                 # + placeholders
│   ├── report/                     # HTML report generator (multi-tab)
│   ├── notification/               # Multi-channel notification
│   └── storage/                    # SQLite + S3 storage
├── llm_news_crawler_bot/           # Module crawl MXH
│   ├── .env                        # Config bot (API key, CDP, accounts)
│   ├── news_crawler_bot/
│   │   ├── api.py                  # FastAPI server
│   │   ├── crawler.py              # Playwright crawler
│   │   ├── agent.py                # LLM planning agent
│   │   ├── config.py               # Env loader
│   │   └── cdp_manager.py          # Chrome CDP session manager
│   └── output/                     # Kết quả crawl (metadata + screenshots)
├── output/
│   ├── html/                       # HTML reports
│   ├── news/                       # SQLite DB hotlist
│   └── rss/                        # SQLite DB RSS
└── docker/                         # Docker deployment
```

---

## Nguồn dữ liệu hiện tại

### RSS (8 nguồn — tất cả hoạt động ✅)

| ID | Tên | URL |
|----|-----|-----|
| vnexpress_kinhdoanh | VnExpress Kinh Doanh | `vnexpress.net/rss/kinh-doanh.rss` |
| tuoitre_kinhdoanh | Tuổi Trẻ Kinh Doanh | `tuoitre.vn/rss/kinh-doanh.rss` |
| dantri_kinhdoanh | Dân Trí Kinh Doanh | `dantri.com.vn/rss/kinh-doanh.rss` |
| thanhnien_kinhte | Thanh Niên Kinh Tế | `thanhnien.vn/rss/kinh-te.rss` |
| vnexpress_thegioi | VnExpress Thế Giới | `vnexpress.net/rss/the-gioi.rss` |
| cafef | CafeF Chứng Khoán | `cafef.vn/thi-truong-chung-khoan.rss` |
| vneconomy | VnEconomy Chứng Khoán | `vneconomy.vn/chung-khoan.rss` |
| tinnhanhck | Tin Nhanh Chứng Khoán | `tinnhanhchungkhoan.vn/rss/home.rss` |

### Facebook (8 pages/groups — qua LLM Bot + CDP)

| Trang | URL |
|-------|-----|
| CafeF | facebook.com/CafeF |
| VTV24 Money | facebook.com/vtv24money |
| VnEconomy | facebook.com/vneconomy.vn |
| Báo Đầu Tư | facebook.com/baodautu.vn |
| Thanh Niên | facebook.com/thanhnien |
| Tuổi Trẻ | facebook.com/tuoitre.vn |
| VTV24 Tin Tức | facebook.com/TintucVTV24 |
| Cộng đồng CK VN | facebook.com/groups/congdongchungkhoanvietnam |

### Web Crawl (qua LLM Bot — cho trang không có RSS)

| Trang | Lý do |
|-------|-------|
| baodautu.vn | RSS server trả 0 items, cần crawl trực tiếp |

### External Sources (mới — tích hợp 2026-06-20)

| Nguồn | Tool | Status | Ghi chú |
|--------|------|:------:|---------|
| 🐦 Twitter/X | `twitter-cli` (pipx) | ✅ Active | Cookie auth, miễn phí |
| 📺 YouTube | `yt-dlp` (pip) | ✅ Active | Zero config |
| 💻 GitHub Trending | `gh` CLI + API | ✅ Active | Zero config |
| 📖 Reddit | `rdt-cli` (pipx) | ⚠️ Sẵn sàng | Cần fix subprocess trên Windows |
| 🔍 Exa Search | `exa-py` (pip) | 🔲 Cần key | API key miễn phí tại exa.ai |
| 📈 Xueqiu | requests | 🔲 Cần acc | Cookie account TQ |
| 🎙️ Podcast | `yt-dlp` + Groq | ✅ Sẵn sàng | Có key, cần episode URL |
| 📕 XiaoHongShu | `opencli` | 🔲 Placeholder | Cần Chrome extension |
| 💼 LinkedIn | Jina Reader | 🔲 Placeholder | Cần URL profiles |
| 💬 V2EX | requests | ✅ Tắt | Nội dung tiếng Trung, không phù hợp |

Chi tiết: xem `docs/EXTERNAL_SOURCES.md`

---

## Cấu hình AI

| Thành phần | Model | Fallback |
|------------|-------|----------|
| **AI Filter** (phân loại tin) | `ag/claude-sonnet-4-6` | `ag/gemini-3.1-pro-high` → `gc/gemini-3-pro-preview` |
| **AI Analysis** (phân tích xu hướng) | `ag/claude-sonnet-4-6` | (như trên) |
| **LLM Crawler Bot** | `ag/claude-sonnet-4-6` | — |
| **API Endpoint** | `http://127.0.0.1:20128/v1` (9Router local) | — |
| **API Key** | `sk-3970b0ca3a786f01-2cfii4-d6fc14b4` | — |

---

## Lệnh chạy

```powershell
# Chạy full pipeline (RSS + Facebook + AI + Report)
cd C:\SINHVIEN\myprocj\TrendRadar
$env:PYTHONIOENCODING="utf-8"; .venv\Scripts\python -m trendradar

# Chạy LLM Bot API server riêng (nếu cần)
cd llm_news_crawler_bot
..\.venv\Scripts\python -m uvicorn news_crawler_bot.api:app --host 127.0.0.1 --port 8010
```

### Yêu cầu trước khi chạy
1. **9Router** phải đang chạy ở `localhost:20128`
2. **Chrome CDP** cho Facebook: profile đã login tại `.cdp_profiles/facebook_com/`
3. **Python 3.11+** với `.venv` đã cài dependencies

---

## Trạng thái hoàn thành

### ✅ Đã hoàn thành
- [x] Clone repo, setup venv, cài dependencies
- [x] Cấu hình 8 nguồn RSS hoạt động (bao gồm CafeF, VnEconomy)
- [x] Cấu hình LLM Crawler Bot cho Facebook (8 pages/groups)
- [x] Tạo CDP Chrome profile cho Facebook (đã login)
- [x] AI Filter bằng Gemini Flash (batch=50, 136+ bài match)
- [x] AI Analysis xuất báo cáo tiếng Việt (Gemini Flash)
- [x] Facebook data được đưa vào AI Analysis (luồng thống nhất RSS+FB→AI)
- [x] HTML Report: multi-tab per source (RSS, Facebook, Twitter, YouTube, GitHub, V2EX, AI Analysis)
- [x] Screenshots Facebook: copy vào output/html/screenshots/, relative path
- [x] AI SUMMARIES button: switch sang tab AI Analysis
- [x] Trending filter: hiện top items có tag
- [x] Fallback models: Gemini Flash → Gemini Pro Low → GC Gemini Pro
- [x] Từ khóa + sở thích AI hoàn toàn tiếng Việt
- [x] Tất cả prompts AI filter đã Việt hóa
- [x] Env variables cho social media accounts
- [x] Fix stream+fallback bug (litellm)
- [x] Fix index.html write error (file quá lớn)
- [x] **Tích hợp 10 external sources** (Twitter, YouTube, Reddit, GitHub, Exa, Xueqiu, Podcast, XiaoHongShu, LinkedIn, V2EX)
- [x] **Cài đặt CLI tools** (pipx, twitter-cli, rdt-cli, gh, exa-py)
- [x] **Multi-tab HTML UI** theo từng nguồn (không còn gom chung Facebook)
- [x] **Tab bar responsive** scroll ngang khi nhiều tabs
- [x] **Docs** EXTERNAL_SOURCES.md hướng dẫn setup đầy đủ
- [x] Push code lên nhánh `ntai0404-update`

### ⚠️ Cần làm
- [ ] **Điền Telegram bot_token + chat_id** vào `config/config.yaml`
- [ ] Test gửi thông báo Telegram
- [ ] (Tùy chọn) Bật schedule tự động

### 📝 Ghi chú kỹ thuật
- **Báo Đầu Tư RSS**: Server trả HTTP 200 nhưng 0 items trong channel. Không phải lỗi code — phía server đã ngừng cung cấp nội dung qua RSS. Workaround: crawl bằng LLM Bot.
- **Rate limit 429**: `ag/claude-sonnet-4-6` có quota giới hạn. Khi bị limit, hệ thống tự fallback sang Gemini Pro.
- **Facebook CDP**: Session có thể hết hạn. Khi bị đá ra, cần mở lại Chrome CDP và login thủ công 1 lần.
- **Encoding Windows**: Luôn cần `$env:PYTHONIOENCODING="utf-8"` khi chạy trên Windows CMD/PowerShell do console mặc định là cp1252.

---

## Lịch sử thay đổi

| Ngày | Thay đổi |
|------|----------|
| 2026-06-20 | **Tích hợp External Sources**: Twitter, YouTube, GitHub, Reddit, Exa, Podcast, V2EX + multi-tab UI |
| 2026-06-20 | Cài CLI tools (pipx, twitter-cli, rdt-cli, gh, exa-py), setup cookies |
| 2026-06-20 | HTML report multi-tab per source, tab bar scroll ngang |
| 2026-06-18 | Setup ban đầu, fix RSS URLs, fix AI model, Việt hóa config |
| 2026-06-18 | Fix ảnh lỗi (base64), thêm CafeF + VnEconomy RSS |
| 2026-06-18 | Cấu hình Facebook CDP, test full pipeline thành công |
| 2026-06-18 | Thêm fallback models chất lượng, tạo tài liệu |
