# coding=utf-8
"""
Dashboard HTML renderer - NewsPulse-style dark dashboard layout.
Maps TrendRadar data to a 3-column news dashboard.
"""

import html as html_lib
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from trendradar.report.helpers import html_escape, calculate_rank_trend
from trendradar.utils.time import convert_time_for_display


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GRAD_PALETTES = [
    ("135deg", "#1a1a2e", "#16213e"),
    ("135deg", "#0f3460", "#533483"),
    ("135deg", "#1b4332", "#2d6a4f"),
    ("135deg", "#7b2d00", "#c1440e"),
    ("135deg", "#1a0533", "#4a0e8f"),
    ("135deg", "#003049", "#0077b6"),
    ("135deg", "#2b2d42", "#8d99ae"),
    ("135deg", "#370617", "#9d0208"),
]


def _source_color(source: str) -> str:
    idx = sum(ord(c) for c in source) % len(_GRAD_PALETTES)
    d, c1, c2 = _GRAD_PALETTES[idx]
    return f"linear-gradient({d},{c1},{c2})"


def _initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "??"


def _rank_badge(ranks: list, rank_threshold: int = 3) -> str:
    if not ranks:
        return ""
    mn = min(ranks)
    cls = "top" if mn <= 3 else ("high" if mn <= rank_threshold else "")
    return f'<span class="rank-badge {cls}">#{mn}</span>'


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _render_top_news_cards(all_titles: list) -> str:
    """Top 3 featured cards (hero row)."""
    top = all_titles[:3]
    if not top:
        return ""
    cards = ""
    for item in top:
        title = html_escape(item.get("title", ""))
        source = html_escape(item.get("source_name", ""))
        url = html_escape(item.get("url", "") or item.get("mobile_url", ""))
        ranks = item.get("ranks", [])
        time_d = html_escape(item.get("time_display", ""))
        grad = _source_color(source)
        init = _initials(source)
        ai_badge = '<span class="ai-badge">AI</span>' if ranks and min(ranks) <= 3 else ""
        href = f'href="{url}" target="_blank"' if url else ""
        cards += f"""
        <a class="top-card" {href}>
          <div class="top-card-img" style="background:{grad}">
            <span class="top-card-init">{init}</span>
            {ai_badge}
          </div>
          <div class="top-card-body">
            <div class="top-card-title">{title}</div>
            <div class="top-card-meta">
              <span class="top-card-source">{source}</span>
              {f'<span class="top-card-time">{time_d}</span>' if time_d else ""}
            </div>
          </div>
        </a>"""
    return f'<section class="top-news-section"><div class="section-heading">TOP NEWS</div><div class="top-cards-row">{cards}</div></section>'


def _render_ai_highlights(ai_analysis: Any) -> str:
    """AI SUMMARIES panel — maps keyword groups to columns."""
    if not ai_analysis or not ai_analysis.success:
        return ""
    blocks = []
    fields = [
        ("core_trends", "Xu hướng cốt lõi"),
        ("sentiment_controversy", "Tranh cãi dư luận"),
        ("signals", "Tín hiệu yếu"),
        ("rss_insights", "Góc nhìn RSS"),
        ("outlook_strategy", "Đề xuất chiến lược"),
    ]
    for attr, label in fields:
        text = getattr(ai_analysis, attr, None)
        if not text:
            continue
        if not isinstance(text, str):
            import json
            text = json.dumps(text, ensure_ascii=False)
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        items_html = "".join(f"<li>{html_escape(l)}</li>" for l in lines[:4])
        blocks.append(f"""
        <div class="ai-col">
          <div class="ai-col-title">{label} <span class="ai-tag">AI</span></div>
          <ul class="ai-col-list">{items_html}</ul>
        </div>""")
    if not blocks:
        return ""
    cols = "".join(blocks[:3])
    return f"""
    <section class="ai-highlights-section">
      <div class="ai-highlights-header">
        <span>✨ AI SUMMARIES: TODAY'S HIGHLIGHTS</span>
        <button class="ai-collapse-btn" onclick="toggleAI(this)">▲</button>
      </div>
      <div class="ai-highlights-body" id="aiHighlightsBody">
        <div class="ai-cols-row">{cols}</div>
      </div>
    </section>"""


def _render_news_updates(stats: list) -> str:
    """Main news list below the hero — grouped by keyword."""
    if not stats:
        return ""
    groups_html = ""
    for stat in stats:
        word = html_escape(stat.get("word", ""))
        titles = stat.get("titles", [])
        if not titles:
            continue
        items_html = ""
        for item in titles:
            title = html_escape(item.get("title", ""))
            source = html_escape(item.get("source_name", ""))
            url = html_escape(item.get("url", "") or item.get("mobile_url", ""))
            ranks = item.get("ranks", [])
            time_d = html_escape(item.get("time_display", ""))
            is_new = item.get("is_new", False)
            new_dot = '<span class="new-dot">NEW</span>' if is_new else ""
            badge = _rank_badge(ranks)
            href = f'href="{url}" target="_blank"' if url else ""
            items_html += f"""
            <div class="news-row">
              <div class="news-row-left">
                <div class="news-row-source-dot" style="background:{_source_color(source)}"></div>
              </div>
              <div class="news-row-body">
                <a class="news-row-title" {href}>{title}</a>
                <div class="news-row-meta">
                  {badge}
                  <span class="news-row-source">{source}</span>
                  {f'<span class="news-row-time">{time_d}</span>' if time_d else ""}
                  {new_dot}
                </div>
              </div>
            </div>"""
        groups_html += f"""
        <div class="news-group">
          <div class="news-group-label">{word} <span class="news-group-count">{len(titles)}</span></div>
          {items_html}
        </div>"""
    return f'<section class="news-updates-section"><div class="section-heading">News Updates</div>{groups_html}</section>'


def _render_rss_items_html(rss_items: list) -> tuple:
    """Render RSS feed items HTML and return (html, count)."""
    items_html = ""
    total = 0
    if not rss_items:
        return "", 0
    for stat in rss_items:
        word = html_escape(stat.get("word", ""))
        titles = stat.get("titles", [])
        for item in titles[:5]:
            title = html_escape(item.get("title", ""))
            source = html_escape(item.get("source_name", ""))
            url = html_escape(item.get("url", ""))
            time_d = html_escape(item.get("time_display", ""))
            href = f'href="{url}" target="_blank"' if url else ""
            items_html += f"""
            <div class="news-row">
              <div class="news-row-left">
                <div class="news-row-source-dot" style="background:{_source_color(source)}"></div>
              </div>
              <div class="news-row-body">
                <a class="news-row-title" {href}>{title}</a>
                <div class="news-row-meta">
                  <span class="news-row-source">{source}</span>
                  {f'<span class="news-row-time">{time_d}</span>' if time_d else ""}
                  {f'<span class="rss-tag">{word}</span>' if word else ""}
                </div>
              </div>
            </div>"""
            total += 1
    return items_html, total


def _render_facebook_items_html(crawled_bot_items: list) -> tuple:
    """Render Facebook/LLM Bot crawled items HTML and return (html, count)."""
    items_html = ""
    total = 0
    if not crawled_bot_items:
        return "", 0
    for item in crawled_bot_items:
        title = html_escape(item.get("title", "Không có tiêu đề"))
        url = html_escape(item.get("url", ""))
        author = html_escape(item.get("author", ""))
        summary = html_escape(item.get("summary", ""))
        time_d = html_escape(item.get("extracted_at", ""))
        href = f'href="{url}" target="_blank"' if url else ""

        # Format extracted_at time
        if "T" in time_d:
            try:
                from datetime import datetime as dt
                dt_obj = dt.fromisoformat(time_d.replace("Z", "+00:00"))
                time_d = dt_obj.strftime("%m-%d %H:%M")
            except:
                pass

        summary_html = f'<div class="fb-summary">{summary}</div>' if summary else ""

        screenshot_path = item.get("screenshot_path", "")
        screenshot_html = ""
        if screenshot_path:
            import base64
            from pathlib import Path as _Path
            img_path = _Path(screenshot_path)
            if img_path.exists():
                try:
                    img_data = base64.b64encode(img_path.read_bytes()).decode("ascii")
                    screenshot_html = f'<div class="fb-screenshot"><img src="data:image/png;base64,{img_data}" alt="Screenshot" style="max-width:100%;border-radius:8px;margin-top:8px;cursor:pointer" onclick="window.open(this.src)" /></div>'
                except Exception:
                    pass

        items_html += f"""
        <div class="news-row">
          <div class="news-row-left">
            <div class="news-row-source-dot" style="background:linear-gradient(135deg,#1877f2,#0d63d0)"></div>
          </div>
          <div class="news-row-body">
            <a class="news-row-title" {href}>{title}</a>
            <div class="news-row-meta">
              <span class="news-row-source">{author if author and author != 'None' else 'Facebook'}</span>
              {f'<span class="news-row-time">{time_d}</span>' if time_d else ""}
              <span class="fb-tag">📘 Facebook</span>
            </div>
            {summary_html}
            {screenshot_html}
          </div>
        </div>"""
        total += 1
    return items_html, total


def _render_tabbed_data_section(rss_items: list, crawled_bot_items: list) -> str:
    """Unified tabbed section combining RSS and Facebook data."""
    rss_html, rss_count = _render_rss_items_html(rss_items)
    fb_html, fb_count = _render_facebook_items_html(crawled_bot_items)

    if not rss_html and not fb_html:
        return ""

    rss_badge = f'<span class="data-tab-badge">{rss_count}</span>' if rss_count else ""
    fb_badge = f'<span class="data-tab-badge fb">{fb_count}</span>' if fb_count else ""

    # Default active tab: RSS if available, else Facebook
    rss_active = "active" if rss_html else ""
    fb_active = "active" if not rss_html and fb_html else ""
    rss_panel_style = "" if rss_html else "display:none"
    fb_panel_style = "" if not rss_html and fb_html else "display:none"

    rss_panel = f'<div id="data-panel-rss" class="data-tab-panel" style="{rss_panel_style}">{rss_html}</div>' if rss_html else ''
    fb_panel = f'<div id="data-panel-fb" class="data-tab-panel" style="{fb_panel_style}">{fb_html}</div>' if fb_html else ''

    rss_tab = f'<button class="data-tab {rss_active}" onclick="switchDataTab(this,\'rss\')" data-panel="data-panel-rss">📰 RSS {rss_badge}</button>' if rss_html else ''
    fb_tab = f'<button class="data-tab {fb_active}" onclick="switchDataTab(this,\'fb\')" data-panel="data-panel-fb">📘 Facebook {fb_badge}</button>' if fb_html else ''

    return f"""
    <section class="data-section">
      <div class="data-section-header">
        <div class="data-tab-bar">
          {rss_tab}
          {fb_tab}
        </div>
      </div>
      <div class="data-section-body">
        {rss_panel}
        {fb_panel}
      </div>
    </section>"""


# Keep legacy wrappers for any other callers
def _render_rss_section(rss_items: list) -> str:
    """Legacy wrapper - use _render_tabbed_data_section instead."""
    rss_html, _ = _render_rss_items_html(rss_items)
    if not rss_html:
        return ""
    return f'<section class="news-updates-section"><div class="section-heading">RSS Updates</div>{rss_html}</section>'


def _render_llm_bot_section(crawled_bot_items: list) -> str:
    """Legacy wrapper - use _render_tabbed_data_section instead."""
    fb_html, _ = _render_facebook_items_html(crawled_bot_items)
    if not fb_html:
        return ""
    return f'<section class="news-updates-section"><div class="section-heading">Facebook Data</div>{fb_html}</section>'



def _render_sidebar_filters(stats: list) -> str:
    """Left sidebar: keyword filters."""
    icons = ["🔥", "📈", "💻", "🏛️", "💰", "🔬", "🌍"]
    items = '<li class="filter-item active" onclick="filterAll(this)"><span class="filter-icon">📰</span> All Topics</li>\n'
    items += '<li class="filter-item" onclick="filterAll(this)"><span class="filter-icon">📊</span> Trending</li>\n'
    for i, stat in enumerate(stats[:6]):
        word = html_escape(stat.get("word", ""))
        icon = icons[i % len(icons)]
        items += f'<li class="filter-item" onclick="filterKeyword(this,\'{word}\')" data-kw="{word}"><span class="filter-icon">{icon}</span> {word}</li>\n'
    # hashtags
    tags_html = ""
    for stat in stats[:4]:
        word = html_escape(stat.get("word", ""))
        tags_html += f'<span class="hashtag" onclick="filterKeyword(null,\'{word}\')" data-kw="{word}">#{word}</span> '
    return f"""
    <aside class="sidebar-left">
      <div class="sidebar-title">Filters</div>
      <ul class="filter-list">{items}</ul>
      <div class="hashtags">{tags_html}</div>
    </aside>"""


def _render_sidebar_latest(all_titles: list) -> str:
    """Right sidebar: latest updates list."""
    items_html = ""
    for item in all_titles[:10]:
        title = html_escape(item.get("title", ""))
        source = html_escape(item.get("source_name", ""))
        url = html_escape(item.get("url", "") or item.get("mobile_url", ""))
        time_d = html_escape(item.get("time_display", ""))
        grad = _source_color(source)
        init = _initials(source)
        href = f'href="{url}" target="_blank"' if url else ""
        items_html += f"""
        <a class="latest-item" {href}>
          <div class="latest-thumb" style="background:{grad}">
            <span class="latest-init">{init}</span>
          </div>
          <div class="latest-body">
            <div class="latest-title">{title}</div>
            <div class="latest-meta">{source}{f" · {time_d}" if time_d else ""}</div>
          </div>
        </a>"""
    return f"""
    <aside class="sidebar-right">
      <div class="sidebar-title">Latest Updates</div>
      {items_html}
    </aside>"""


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh;line-height:1.5}
a{text-decoration:none;color:inherit}

/* ── Layout ── */
.app-shell{display:flex;flex-direction:column;min-height:100vh}
.topnav{display:flex;align-items:center;gap:0;background:#161b27;border-bottom:1px solid #1e2535;padding:0 20px;height:52px;position:sticky;top:0;z-index:100}
.topnav-brand{display:flex;align-items:center;gap:10px;margin-right:32px}
.brand-icon{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:16px}
.brand-name{font-weight:700;font-size:15px;color:#f1f5f9}
.brand-sub{font-size:11px;color:#64748b}
.nav-tabs{display:flex;gap:2px;flex:1}
.nav-tab{padding:6px 14px;border-radius:6px;font-size:13px;font-weight:500;color:#94a3b8;cursor:pointer;border:none;background:none;transition:all .15s}
.nav-tab:hover{color:#e2e8f0;background:#1e2535}
.nav-tab.active{color:#fff;background:#1e2535;border-bottom:2px solid #6366f1}
.nav-ai-btn{background:#eab308;color:#000;font-weight:700;font-size:12px;padding:6px 14px;border-radius:6px;border:none;cursor:pointer;margin-left:8px}
.nav-actions{display:flex;align-items:center;gap:12px;margin-left:auto}
.nav-icon-btn{background:none;border:none;color:#94a3b8;cursor:pointer;font-size:18px;padding:4px}
.nav-icon-btn:hover{color:#e2e8f0}

.body-layout{display:grid;grid-template-columns:180px 1fr 240px;gap:0;flex:1;max-width:1400px;margin:0 auto;width:100%;padding:0 16px}
@media(max-width:1100px){.body-layout{grid-template-columns:160px 1fr}.sidebar-right{display:none}}
@media(max-width:768px){.body-layout{grid-template-columns:1fr}.sidebar-left{display:none}}

/* ── Left sidebar ── */
.sidebar-left{padding:20px 12px;border-right:1px solid #1e2535}
.sidebar-title{font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px}
.filter-list{list-style:none;display:flex;flex-direction:column;gap:2px}
.filter-item{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;font-size:13px;color:#94a3b8;cursor:pointer;transition:all .15s}
.filter-item:hover{background:#1e2535;color:#e2e8f0}
.filter-item.active{background:#1e2535;color:#e2e8f0;font-weight:600}
.filter-icon{font-size:14px;width:18px;text-align:center}
.hashtags{margin-top:20px;display:flex;flex-wrap:wrap;gap:6px}
.hashtag{background:#1e2535;color:#6366f1;font-size:11px;padding:4px 8px;border-radius:20px;cursor:pointer;transition:all .15s}
.hashtag:hover{background:#6366f1;color:#fff}

/* ── Main content ── */
.main-content{padding:20px 20px;overflow:hidden}
.section-heading{font-size:13px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:14px}

/* ── Top cards ── */
.top-news-section{margin-bottom:24px}
.top-cards-row{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
@media(max-width:900px){.top-cards-row{grid-template-columns:repeat(2,1fr)}}
.top-card{background:#161b27;border:1px solid #1e2535;border-radius:12px;overflow:hidden;transition:transform .15s,border-color .15s;display:block}
.top-card:hover{transform:translateY(-2px);border-color:#6366f1}
.top-card-img{height:130px;display:flex;align-items:center;justify-content:center;position:relative}
.top-card-init{font-size:36px;font-weight:900;color:rgba(255,255,255,.25);user-select:none}
.ai-badge{position:absolute;top:8px;right:8px;background:#6366f1;color:#fff;font-size:10px;font-weight:700;padding:2px 6px;border-radius:4px}
.top-card-body{padding:12px}
.top-card-title{font-size:13px;font-weight:600;color:#e2e8f0;line-height:1.4;margin-bottom:6px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.top-card-meta{display:flex;align-items:center;gap:8px}
.top-card-source{font-size:11px;color:#64748b;font-weight:500}
.top-card-time{font-size:11px;color:#475569}
"""

_CSS += """
/* ── AI Highlights ── */
.ai-highlights-section{background:#161b27;border:1px solid #2d3748;border-radius:12px;margin-bottom:24px;overflow:hidden}
.ai-highlights-header{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#1a2035;font-size:13px;font-weight:700;color:#a5b4fc;letter-spacing:.04em}
.ai-collapse-btn{background:none;border:none;color:#64748b;cursor:pointer;font-size:14px;transition:transform .2s}
.ai-highlights-body{padding:16px}
.ai-cols-row{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
@media(max-width:900px){.ai-cols-row{grid-template-columns:1fr}}
.ai-col{background:#0f1117;border:1px solid #1e2535;border-radius:10px;padding:14px}
.ai-col-title{font-size:12px;font-weight:700;color:#e2e8f0;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.ai-tag{background:#6366f1;color:#fff;font-size:9px;font-weight:700;padding:1px 5px;border-radius:3px}
.ai-col-list{list-style:none;display:flex;flex-direction:column;gap:6px}
.ai-col-list li{font-size:12px;color:#94a3b8;line-height:1.4;padding-left:12px;position:relative}
.ai-col-list li::before{content:"•";position:absolute;left:0;color:#6366f1}

/* ── News rows ── */
.news-updates-section{margin-bottom:24px}
.news-group{margin-bottom:20px}
.news-group-label{font-size:12px;font-weight:700;color:#6366f1;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.news-group-count{background:#1e2535;color:#94a3b8;font-size:10px;padding:1px 6px;border-radius:10px;font-weight:600}
.news-row{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid #1e2535}
.news-row:last-child{border-bottom:none}
.news-row-left{padding-top:4px}
.news-row-source-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:4px}
.news-row-body{flex:1;min-width:0}
.news-row-title{font-size:13px;color:#e2e8f0;line-height:1.4;display:block;margin-bottom:4px;transition:color .15s}
.news-row-title:hover{color:#818cf8}
.news-row-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.news-row-source{font-size:11px;color:#64748b;font-weight:500}
.news-row-time{font-size:11px;color:#475569}
.new-dot{background:#dc2626;color:#fff;font-size:9px;font-weight:700;padding:1px 5px;border-radius:3px}
.rank-badge{font-size:10px;font-weight:700;padding:1px 5px;border-radius:3px;background:#374151;color:#9ca3af}
.rank-badge.top{background:#dc2626;color:#fff}
.rank-badge.high{background:#ea580c;color:#fff}
.rss-tag{background:#0f3460;color:#60a5fa;font-size:10px;padding:1px 5px;border-radius:3px}

/* ── Tabbed Data Section (RSS / Facebook) ── */
.data-section{background:#161b27;border:1px solid #1e2535;border-radius:12px;margin-bottom:24px;overflow:hidden}
.data-section-header{background:#1a2035;border-bottom:1px solid #1e2535;padding:0 16px}
.data-tab-bar{display:flex;gap:4px;padding:8px 0}
.data-tab{display:flex;align-items:center;gap:6px;padding:7px 16px;border-radius:8px;font-size:13px;font-weight:600;color:#94a3b8;cursor:pointer;border:none;background:none;transition:all .18s;position:relative}
.data-tab:hover{color:#e2e8f0;background:rgba(255,255,255,.05)}
.data-tab.active{color:#fff;background:#0f1117;border:1px solid #2d3748;box-shadow:0 1px 6px rgba(0,0,0,.4)}
.data-tab.active::after{content:'';position:absolute;bottom:-9px;left:50%;transform:translateX(-50%);width:40px;height:2px;background:#6366f1;border-radius:2px}
.data-tab-badge{background:#1e2535;color:#94a3b8;font-size:10px;font-weight:700;padding:1px 7px;border-radius:10px;min-width:20px;text-align:center}
.data-tab-badge.fb{background:#1a3a6b;color:#60a5fa}
.data-section-body{padding:16px}
.data-tab-panel{animation:fadeInPanel .2s ease}
@keyframes fadeInPanel{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}

/* ── Facebook specific ── */
.fb-tag{background:#1a3a6b;color:#60a5fa;font-size:10px;padding:1px 6px;border-radius:3px;font-weight:600}
.fb-summary{font-size:11px;color:#94a3b8;margin-top:6px;background:#1a2035;padding:8px 10px;border-radius:6px;border-left:2px solid #1877f2;line-height:1.5;white-space:pre-wrap}
.fb-screenshot{margin-top:8px}
.fb-screenshot img{max-width:100%;max-height:300px;border-radius:6px;object-fit:contain;border:1px solid #2d3748;cursor:pointer;transition:opacity .15s}
.fb-screenshot img:hover{opacity:.85}

/* ── Right sidebar ── */
.sidebar-right{padding:20px 12px;border-left:1px solid #1e2535}
.latest-item{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid #1e2535;cursor:pointer;transition:opacity .15s}
.latest-item:last-child{border-bottom:none}
.latest-item:hover{opacity:.8}
.latest-thumb{width:52px;height:44px;border-radius:6px;flex-shrink:0;display:flex;align-items:center;justify-content:center}
.latest-init{font-size:14px;font-weight:800;color:rgba(255,255,255,.3);user-select:none}
.latest-body{flex:1;min-width:0}
.latest-title{font-size:12px;color:#e2e8f0;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin-bottom:3px}
.latest-meta{font-size:10px;color:#64748b}

/* ── Footer ── */
.app-footer{text-align:center;padding:16px;font-size:11px;color:#475569;border-top:1px solid #1e2535;margin-top:auto}
.app-footer a{color:#6366f1}

/* ── Light Mode ── */
body.light-mode { background: #f8fafc; color: #0f172a; }
body.light-mode .topnav { background: #ffffff; border-bottom: 1px solid #e2e8f0; }
body.light-mode .brand-name { color: #0f172a; }
body.light-mode .nav-tab { color: #64748b; }
body.light-mode .nav-tab:hover { color: #0f172a; background: #f1f5f9; }
body.light-mode .nav-tab.active { color: #0f172a; background: #ffffff; border-bottom: 2px solid #6366f1; }
body.light-mode .nav-icon-btn { color: #64748b; }
body.light-mode .nav-icon-btn:hover { color: #0f172a; }
body.light-mode .sidebar-left { border-right: 1px solid #e2e8f0; }
body.light-mode .sidebar-right { border-left: 1px solid #e2e8f0; }
body.light-mode .filter-item { color: #64748b; }
body.light-mode .filter-item:hover { background: #f1f5f9; color: #0f172a; }
body.light-mode .filter-item.active { background: #e2e8f0; color: #0f172a; font-weight: 600; }
body.light-mode .hashtag { background: #e0e7ff; color: #4338ca; }
body.light-mode .hashtag:hover { background: #4f46e5; color: #fff; }
body.light-mode .section-heading, body.light-mode .sidebar-title { color: #475569; }
body.light-mode .top-card { background: #ffffff; border-color: #e2e8f0; }
body.light-mode .top-card:hover { border-color: #6366f1; }
body.light-mode .top-card-title { color: #0f172a; }
body.light-mode .ai-highlights-section { background: #ffffff; border-color: #e2e8f0; }
body.light-mode .ai-highlights-header { background: #f8fafc; color: #4338ca; }
body.light-mode .ai-col { background: #f8fafc; border-color: #e2e8f0; }
body.light-mode .ai-col-title { color: #0f172a; }
body.light-mode .ai-col-list li { color: #475569; }
body.light-mode .news-row { border-bottom-color: #e2e8f0; }
body.light-mode .news-row-title { color: #0f172a; }
body.light-mode .news-row-title:hover { color: #4f46e5; }
body.light-mode .news-group-count { background: #e2e8f0; color: #475569; }
body.light-mode .data-section { background: #ffffff; border-color: #e2e8f0; }
body.light-mode .data-section-header { background: #f8fafc; border-bottom-color: #e2e8f0; }
body.light-mode .data-tab { color: #64748b; }
body.light-mode .data-tab:hover { background: #f1f5f9; color: #0f172a; }
body.light-mode .data-tab.active { background: #ffffff; color: #0f172a; border-color: #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
body.light-mode .data-tab-badge { background: #e2e8f0; color: #475569; }
body.light-mode .data-tab-badge.fb { background: #dbeafe; color: #1e3a8a; }
body.light-mode .latest-item { border-bottom-color: #e2e8f0; }
body.light-mode .latest-title { color: #0f172a; }
body.light-mode .app-footer { border-top-color: #e2e8f0; color: #64748b; }
body.light-mode .fb-summary { background: #f8fafc; color: #475569; border-left-color: #1877f2; }
body.light-mode .fb-screenshot img { border-color: #e2e8f0; }
"""


# ---------------------------------------------------------------------------
# JS
# ---------------------------------------------------------------------------

_JS = """
function toggleAI(btn){
  var body=document.getElementById('aiHighlightsBody');
  if(!body)return;
  var hidden=body.style.display==='none';
  body.style.display=hidden?'':'none';
  btn.textContent=hidden?'▲':'▼';
}
function filterAll(el){
  document.querySelectorAll('.filter-item').forEach(function(i){i.classList.remove('active')});
  if(el)el.classList.add('active');
  document.querySelectorAll('.news-group').forEach(function(g){g.style.display=''});
}
function filterKeyword(el,kw){
  document.querySelectorAll('.filter-item').forEach(function(i){i.classList.remove('active')});
  if(el)el.classList.add('active');
  document.querySelectorAll('.news-group').forEach(function(g){
    var label=g.querySelector('.news-group-label');
    if(!label){g.style.display='';return;}
    g.style.display=(label.textContent.trim().toLowerCase().indexOf(kw.toLowerCase())>=0)?'':'none';
  });
}
function switchDataTab(btn, panelKey){
  // Deactivate all tabs in same bar
  var bar=btn.closest('.data-tab-bar');
  if(bar)bar.querySelectorAll('.data-tab').forEach(function(t){t.classList.remove('active');});
  btn.classList.add('active');
  // Hide all panels in same section body
  var body=btn.closest('.data-section').querySelector('.data-section-body');
  if(body)body.querySelectorAll('.data-tab-panel').forEach(function(p){
    p.style.display='none';
  });
  var target=document.getElementById('data-panel-'+panelKey);
  if(target){target.style.display='';target.style.animation='none';target.offsetHeight;target.style.animation='';}
}
function toggleTheme(btn){
  var isLight = document.body.classList.toggle('light-mode');
  localStorage.setItem('trendradar-theme', isLight ? 'light' : 'dark');
  btn.textContent = isLight ? '☀' : '☽';
}
// Restore preferences
(function(){
  var tabs=document.querySelectorAll('.nav-tab');
  tabs.forEach(function(t){
    t.addEventListener('click',function(){
      tabs.forEach(function(x){x.classList.remove('active')});
      t.classList.add('active');
    });
  });
  
  var theme = localStorage.getItem('trendradar-theme');
  if (theme === 'light') {
    document.body.classList.add('light-mode');
    var btn = document.querySelector('.nav-icon-btn[title="Chế độ tối/sáng"]');
    if(btn) btn.textContent = '☀';
  }
})();
"""

# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_html_dashboard(
    report_data: Dict,
    total_titles: int,
    mode: str = "daily",
    update_info: Optional[Dict] = None,
    *,
    get_time_func: Optional[Callable[[], datetime]] = None,
    rss_items: Optional[List[Dict]] = None,
    rss_new_items: Optional[List[Dict]] = None,
    ai_analysis: Optional[Any] = None,
    standalone_data: Optional[Dict] = None,
    display_mode: str = "keyword",
    show_new_section: bool = True,
    region_order: Optional[List[str]] = None,
    crawled_bot_items: Optional[List[Dict]] = None,
) -> str:
    now = get_time_func() if get_time_func else datetime.now()
    time_str = now.strftime("%H:%M · %d/%m/%Y")

    stats = report_data.get("stats", [])
    new_titles_data = report_data.get("new_titles", [])

    # Flatten all titles for top cards and sidebar
    all_titles: List[Dict] = []
    for stat in stats:
        all_titles.extend(stat.get("titles", []))
    # Also include new_titles
    for src in new_titles_data:
        all_titles.extend(src.get("titles", []))

    # Build nav tabs from keyword groups
    nav_tabs_html = '<button class="nav-tab active">Home</button>'
    for stat in stats[:6]:
        word = html_escape(stat.get("word", ""))
        nav_tabs_html += f'<button class="nav-tab">{word}</button>'

    # Stats summary
    hot_count = sum(len(s.get("titles", [])) for s in stats)
    rss_count = sum(len(s.get("titles", [])) for s in (rss_items or []))
    fb_count = len(crawled_bot_items) if crawled_bot_items else 0

    # Sections
    top_news_html = _render_top_news_cards(all_titles)
    ai_html = _render_ai_highlights(ai_analysis)
    news_updates_html = _render_news_updates(stats)
    # Use unified tabbed section for RSS + Facebook
    tabbed_data_html = _render_tabbed_data_section(rss_items or [], crawled_bot_items or [])
    sidebar_left = _render_sidebar_filters(stats)
    sidebar_right = _render_sidebar_latest(all_titles)

    mode_label = {"current": "Bảng xếp hạng hiện tại", "incremental": "Phân tích mới", "daily": "Tổng hợp cả ngày"}.get(mode, mode)

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TrendRadar · {mode_label}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="app-shell">

  <!-- Top nav -->
  <nav class="topnav">
    <div class="topnav-brand">
      <div class="brand-icon">📡</div>
      <div>
        <div class="brand-name">TrendRadar</div>
        <div class="brand-sub">AI synthesis</div>
      </div>
    </div>
    <div class="nav-tabs">{nav_tabs_html}</div>
    <button class="nav-ai-btn">AI SUMMARIES</button>
    <div class="nav-actions">
      <button class="nav-icon-btn" title="Tìm kiếm">🔍</button>
      <button class="nav-icon-btn" title="Chế độ tối/sáng" onclick="toggleTheme(this)">☽</button>
      <span style="font-size:11px;color:#475569">{time_str}</span>
    </div>
  </nav>

  <!-- Body -->
  <div class="body-layout">
    {sidebar_left}

    <main class="main-content">
      {top_news_html}
      {ai_html}
      {news_updates_html}
      {tabbed_data_html}
    </main>

    {sidebar_right}
  </div>

  <footer class="app-footer">
    Tạo bởi <a href="https://github.com/sansan0/TrendRadar" target="_blank">TrendRadar</a> ·
    {hot_count} tin hot · {rss_count} RSS · {fb_count} Facebook · {mode_label}
    {f'<br><span style="color:#eab308">Phiên bản mới {update_info["remote_version"]} có sẵn</span>' if update_info else ""}
  </footer>
</div>
<script>{_JS}</script>
</body>
</html>"""
