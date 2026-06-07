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


def _render_rss_section(rss_items: list) -> str:
    """RSS feeds section."""
    if not rss_items:
        return ""
    items_html = ""
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
    if not items_html:
        return ""
    return f'<section class="news-updates-section"><div class="section-heading">RSS Updates</div>{items_html}</section>'


def _render_llm_bot_section(crawled_bot_items: list) -> str:
    """LLM Bot crawled data section."""
    if not crawled_bot_items:
        return ""
    items_html = ""
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
                
        summary_html = f'<div style="font-size: 11px; color: #94a3b8; margin-top: 6px; background: #1e2535; padding: 8px; border-radius: 4px; border-left: 2px solid #6366f1;">{summary}</div>' if summary else ""
        
        screenshot_path = item.get("screenshot_path", "")
        screenshot_html = ""
        if screenshot_path:
            import urllib.parse
            # Ensure it works when opened in browser via file:// protocol
            img_url = f"file://{urllib.parse.quote(screenshot_path)}"
            screenshot_html = f'<div style="margin-top: 8px;"><img src="{img_url}" alt="Screenshot" style="max-width: 100%; max-height: 300px; border-radius: 4px; object-fit: contain; border: 1px solid #334155; cursor: pointer;" onclick="window.open(this.src)" /></div>'
            
        items_html += f"""
        <div class="news-row">
          <div class="news-row-left">
            <div class="news-row-source-dot" style="background:#6366f1"></div>
          </div>
          <div class="news-row-body">
            <a class="news-row-title" {href}>{title}</a>
            <div class="news-row-meta">
              <span class="news-row-source">{author}</span>
              {f'<span class="news-row-time">{time_d}</span>' if time_d else ""}
              <span class="rss-tag" style="background:#4f46e5; color:#fff">Crawl Bot</span>
            </div>
            {summary_html}
            {screenshot_html}
          </div>
        </div>"""
    if not items_html:
        return ""
    return f'<section class="news-updates-section"><div class="section-heading">LLM Bot Data</div>{items_html}</section>'



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
// Restore preferences
(function(){
  var tabs=document.querySelectorAll('.nav-tab');
  tabs.forEach(function(t){
    t.addEventListener('click',function(){
      tabs.forEach(function(x){x.classList.remove('active')});
      t.classList.add('active');
    });
  });
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

    # Sections
    top_news_html = _render_top_news_cards(all_titles)
    ai_html = _render_ai_highlights(ai_analysis)
    news_updates_html = _render_news_updates(stats)
    rss_html = _render_rss_section(rss_items) if rss_items else ""
    llm_bot_html = _render_llm_bot_section(crawled_bot_items)
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
      <button class="nav-icon-btn" title="Chế độ tối/sáng" onclick="document.body.classList.toggle('light-mode')">☽</button>
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
      {rss_html}
      {llm_bot_html}
    </main>

    {sidebar_right}
  </div>

  <footer class="app-footer">
    Tạo bởi <a href="https://github.com/sansan0/TrendRadar" target="_blank">TrendRadar</a> ·
    {hot_count} tin hot · {rss_count} RSS · {mode_label}
    {f'<br><span style="color:#eab308">Phiên bản mới {update_info["remote_version"]} có sẵn</span>' if update_info else ""}
  </footer>
</div>
<script>{_JS}</script>
</body>
</html>"""
