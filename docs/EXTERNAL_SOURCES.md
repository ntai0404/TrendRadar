# External Sources - Nguồn dữ liệu mở rộng

## Tổng quan

TrendRadar hỗ trợ 10 nguồn dữ liệu mở rộng ngoài RSS và Facebook Bot có sẵn. Mỗi nguồn có tab riêng trong HTML report.

## Nguồn hiện có

| # | Nguồn | Tool | Auth | Status |
|---|--------|------|------|:------:|
| 1 | Twitter/X | `twitter-cli` (pipx) | Cookie (env `TWITTER_AUTH_TOKEN` + `TWITTER_CT0`) | ✅ Active |
| 2 | YouTube | `yt-dlp` (pip) | Không cần | ✅ Active |
| 3 | Exa Search | `exa-py` (pip) | API key miễn phí (exa.ai) | 🔲 Cần key |
| 4 | Reddit | `rdt-cli` (pipx) | `rdt login` (browser cookie) | 🔲 Cần login |
| 5 | Xueqiu (雪球) | requests | Cookie (env `XUEQIU_COOKIE`) | 🔲 Cần acc TQ |
| 6 | GitHub Trending | `gh` CLI + API | Không cần | ✅ Active |
| 7 | Podcast | `yt-dlp` + Groq API | Groq key (env `GROQ_API_KEY`) | ✅ Sẵn sàng |
| 8 | XiaoHongShu | `opencli` | Browser extension | 🔲 Placeholder |
| 9 | LinkedIn | Jina Reader | Không cần (public) | 🔲 Placeholder |
| 10 | V2EX | requests | Không cần | 🔲 Tắt (tiếng Trung) |

## Cài đặt CLI tools

```bash
# pipx (quản lý CLI tools isolated)
pip install pipx
pipx ensurepath

# Twitter
pipx install twitter-cli

# Reddit
pipx install "git+https://github.com/public-clis/rdt-cli.git"

# GitHub CLI
winget install GitHub.cli    # Windows
brew install gh              # macOS

# YouTube (thường đã có sẵn)
pip install yt-dlp

# Exa Search SDK
pip install exa-py
```

## Cấu hình

Tất cả trong `config/config.yaml` section `external_sources`:

```yaml
external_sources:
  enabled: true
  sources:
    twitter:
      enabled: true
      queries: ["VN-Index", "chứng khoán"]
      max_results: 10
    youtube:
      enabled: true
      search_queries: ["phân tích chứng khoán VN"]
      max_results: 5
    github:
      enabled: true
      since: "daily"
      max_results: 15
```

## Authentication

### Twitter/X
1. Login https://x.com trên Chrome
2. Cài [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
3. Export cookie → lấy `auth_token` và `ct0`
4. Set env (persistent):
```powershell
[System.Environment]::SetEnvironmentVariable("TWITTER_AUTH_TOKEN", "your_token", "User")
[System.Environment]::SetEnvironmentVariable("TWITTER_CT0", "your_ct0", "User")
```

### Reddit
1. Login https://www.reddit.com trên Chrome
2. Chạy `rdt login` (cần quyền Admin trên Windows)
3. Hoặc export cookie thủ công vào `~/.config/rdt-cli/credential.json`

### Exa Search
1. Đăng ký miễn phí tại https://dashboard.exa.ai/login
2. Tạo API key tại https://dashboard.exa.ai/api-keys
3. Điền vào config hoặc set env `EXA_API_KEY`

### Podcast (Groq Whisper)
1. Đăng ký miễn phí tại https://console.groq.com
2. Tạo key tại https://console.groq.com/keys
3. Set env: `GROQ_API_KEY=gsk_xxxxx`

## Kiến trúc

```
trendradar/crawler/sources/
├── __init__.py           # Module exports
├── base.py              # ExternalSource base class, SourceItem, SourceResult
├── manager.py           # ExternalSourceManager - orchestrator
├── twitter.py           # Twitter/X via twitter-cli
├── youtube.py           # YouTube via yt-dlp
├── reddit.py            # Reddit via rdt-cli
├── exa_search.py        # Exa AI Search
├── xueqiu.py            # Xueqiu (雪球)
├── github_trending.py   # GitHub Trending
├── podcast.py           # Podcast Transcript via Groq Whisper
├── xiaohongshu.py       # XiaoHongShu (placeholder)
├── linkedin.py          # LinkedIn (placeholder)
└── v2ex.py              # V2EX (placeholder)
```

### Data Flow

```
External Sources → _fetch_external_sources()
    → Ghi metadata.json vào llm_news_crawler_bot/output/ext_*/
    → _get_crawled_bot_items() đọc lên
    → _group_crawled_items_by_source() phân loại theo nguồn
    → _render_tabbed_data_section() tạo tab riêng cho mỗi nguồn
    → HTML report với multi-tab UI
```

### Thêm nguồn mới

1. Tạo file `trendradar/crawler/sources/my_source.py`
2. Kế thừa `ExternalSource`, implement `source_id`, `source_name`, `fetch(config)`
3. Đăng ký trong `manager.py` → `ALL_SOURCES`
4. Thêm config vào `SOURCE_CONFIG` trong `html_dashboard.py`
5. Thêm section config vào `config/config.yaml`

## Environment Variables

| Variable | Nguồn | Mô tả |
|----------|-------|-------|
| `TWITTER_AUTH_TOKEN` | Twitter | Cookie auth_token |
| `TWITTER_CT0` | Twitter | Cookie ct0 |
| `GROQ_API_KEY` | Podcast | Groq Whisper API key |
| `EXA_API_KEY` | Exa Search | Exa API key |
| `XUEQIU_COOKIE` | Xueqiu | Full cookie string |
| `TRENDRADAR_SKIP_BOT` | System | Set "1" để skip Facebook Bot (testing) |
