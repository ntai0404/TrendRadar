# coding=utf-8
"""
Message batch processing module

Provides message content batch splitting functionality to ensure message size does not exceed platform limits
"""

from datetime import datetime
from typing import Dict, List, Optional, Callable

from trendradar.report.formatter import format_title_for_platform
from trendradar.report.helpers import format_rank_display
from trendradar.utils.time import DEFAULT_TIMEZONE, format_iso_time_friendly, convert_time_for_display
from trendradar.notification.batch import truncate_at_line_boundary


# === Batch safety helper functions ===

def _split_content_by_lines(
    content: str, footer: str, max_bytes: int, base_header: str
) -> List[str]:
    """Split overly long content into multiple complete batches by line boundaries (each batch with a footer)

    Will not discard any content, overflow parts are automatically allocated to subsequent batches.

    Args:
        content: Body content (excluding footer, may include base_header)
        footer: Tail content (Cập nhật time, etc.)
        max_bytes: Maximum bytes per batch
        base_header: Header for subsequent batches

    Returns:
        List of complete batches (each element = body + footer, size ≤ max_bytes)
    """
    footer_size = len(footer.encode("utf-8"))
    result_batches = []
    lines = content.split("\n")

    current = ""
    for line in lines:
        candidate = current + line + "\n"
        if len(candidate.encode("utf-8")) + footer_size > max_bytes and current.strip():
            result_batches.append(current + footer)
            current = base_header + line + "\n"
        else:
            current = candidate

    if current.strip():
        result_batches.append(current + footer)

    return result_batches


def _safe_append_batch(
    batches: List[str], content: str, footer: str, max_bytes: int,
    base_header: str = ""
) -> None:
    """Safely append batch, split into multiple batches by line when exceeding limit (without discarding content)

    Args:
        batches: Batch list (modified in place)
        content: Body content (excluding footer)
        footer: Tail content (Cập nhật time, etc.)
        max_bytes: Maximum bytes
        base_header: Header for subsequent batches upon overflow
    """
    full = content + footer
    if len(full.encode("utf-8")) <= max_bytes:
        batches.append(full)
        return

    split_batches = _split_content_by_lines(content, footer, max_bytes, base_header)
    if split_batches:
        batches.extend(split_batches)
    else:
        # Extreme case: A single line exceeds the limit, force truncation
        batches.append(truncate_at_line_boundary(full, max_bytes))


def _safe_new_batch(
    new_content: str, footer: str, max_bytes: int, base_header: str,
    batches: List[str] = None
) -> str:
    """Safely create a new batch, split overflow content into batches when exceeding limit, return the last segment as current_batch

    Args:
        new_content: Complete content of the new batch (including base_header + section_header + ...)
        footer: Tail content
        max_bytes: Maximum bytes
        base_header: Base header
        batches: Batch list, overflow parts are appended here (optional)

    Returns:
        current_batch that can safely continue to append content (size + footer ≤ max_bytes)
    """
    if len((new_content + footer).encode("utf-8")) <= max_bytes:
        return new_content

    if batches is None:
        # Cannot split into batches, fallback to line boundary truncation
        footer_size = len(footer.encode("utf-8"))
        available = max_bytes - footer_size
        header_size = len(base_header.encode("utf-8"))
        if available <= header_size:
            return base_header
        return truncate_at_line_boundary(new_content, available)

    # Split: The previous parts are stored in batches, the last segment is returned as current_batch
    split_batches = _split_content_by_lines(new_content, footer, max_bytes, base_header)
    if len(split_batches) <= 1:
        # Cannot split further, return directly (handled by subsequent _safe_append_batch fallback)
        return new_content

    # The first N-1 batches are stored in batches
    batches.extend(split_batches[:-1])
    # The last batch removes the footer to become current_batch (content will be appended later)
    last = split_batches[-1]
    if last.endswith(footer):
        return last[: -len(footer)]
    return last


# Default batch size configuration
DEFAULT_BATCH_SIZES = {
    "dingtalk": 20000,
    "feishu": 29000,
    "ntfy": 3800,
    "default": 4000,
}

# Default region order
DEFAULT_REGION_ORDER = ["hotlist", "rss", "new_items", "standalone", "ai_analysis"]


def split_content_into_batches(
    report_data: Dict,
    format_type: str,
    update_info: Optional[Dict] = None,
    max_bytes: Optional[int] = None,
    mode: str = "daily",
    batch_sizes: Optional[Dict[str, int]] = None,
    feishu_separator: str = "---",
    region_order: Optional[List[str]] = None,
    get_time_func: Optional[Callable[[], datetime]] = None,
    rss_items: Optional[list] = None,
    rss_new_items: Optional[list] = None,
    timezone: str = DEFAULT_TIMEZONE,
    display_mode: str = "keyword",
    ai_content: Optional[str] = None,
    standalone_data: Optional[Dict] = None,
    rank_threshold: int = 10,
    ai_stats: Optional[Dict] = None,
    report_type: str = "Hotspot Analysis Report",
    show_new_section: bool = True,
) -> List[str]:
    """Batch process message content, ensuring the completeness of phrase titles + at least the first tin news (supports Tin Hot + RSS merge + AI analysis + independent display area)

    Tin Hot statistics and RSS statistics are displayed side by side, Tin Hot additions and RSS additions are displayed side by side.
    region_order controls the display order of each region.
    AI analysis content is displayed according to its position in region_order.
    Independent display area is displayed according to its position in region_order.

    Args:
        report_data: Report data dictionary, containing stats, new_titles, failed_ids, total_new_count
        format_type: Format type (feishu, dingtalk, wework, telegram, ntfy, bark, slack)
        update_info: Version Cập nhật information (optional)
        max_bytes: Maximum number of bytes (optional, uses default configuration if not specified)
        mode: Report mode (daily, incremental, current)
        batch_sizes: Batch size configuration dictionary (optional)
        feishu_separator: Feishu message separator
        region_order: Region display order list
        get_time_func: Function to get hiện tại time (optional)
        rss_items: RSS statistics tin item list (grouped by source, used for merged push)
        rss_new_items: RSS new tin item list (optional, used for new blocks)
        timezone: Timezone name (used for RSS time formatting)
        display_mode: Display mode (keyword=grouped by keyword, platform=grouped by platform)
        ai_content: AI analysis content (rendered string, optional)
        standalone_data: Standalone display area data (optional), contains platforms and rss_feeds lists
        ai_stats: AI analysis statistics data (optional), contains total_news, analyzed_news, max_news_limit, etc.

    Returns:
        List of message contents after batching
    """
    if region_order is None:
        region_order = DEFAULT_REGION_ORDER
    # Merge batch size configuration
    sizes = {**DEFAULT_BATCH_SIZES, **(batch_sizes or {})}

    if max_bytes is None:
        if format_type == "dingtalk":
            max_bytes = sizes.get("dingtalk", 20000)
        elif format_type == "feishu":
            max_bytes = sizes.get("feishu", 29000)
        elif format_type == "ntfy":
            max_bytes = sizes.get("ntfy", 3800)
        else:
            max_bytes = sizes.get("default", 4000)

    batches = []

    total_hotlist_count = sum(
        len(stat["titles"]) for stat in report_data["stats"] if stat["count"] > 0
    )
    total_titles = total_hotlist_count
    
    # Accumulate RSS tin item count
    if rss_items:
        total_titles += sum(stat.get("count", 0) for stat in rss_items)

    now = get_time_func() if get_time_func else datetime.now()

    # Build header information
    base_header = ""

    # Format bold tags
    if format_type == "slack":
        b_s, b_e = "*", "*"
    elif format_type == "telegram":
        b_s, b_e = "", ""
    else:
        b_s, b_e = "**", "**"

    # Extract statistics data
    hotlist_total = report_data.get("hotlist_total", total_hotlist_count)
    new_count = report_data.get("total_new_count", 0)
    platform_total = report_data.get("platform_total", 0)
    failed_count = len(report_data.get("failed_ids", []))
    platform_success = platform_total - failed_count if platform_total else 0
    rss_matched = report_data.get("rss_matched_count", 0)
    rss_total_items = report_data.get("rss_total_count", 0)
    rss_source_total = report_data.get("rss_source_total", 0)
    rss_source_failed = report_data.get("rss_source_failed", 0)
    rss_source_success = max(0, rss_source_total - rss_source_failed)

    # === Upper part: Data statistics ===

    # 1. Tổng tin tức
    rss_new_count = sum(len(stat.get("titles", [])) for stat in (rss_new_items or []))
    total_new = new_count + rss_new_count
    total_news_line = f"{b_s}Tổng tin tức:{b_e} {total_titles} tin"
    if total_new > 0:
        total_news_line += f" (Mới  {new_count} + {rss_new_count}）"
    base_header += f"{total_news_line}\n"

    # 2. Tin Hot
    hotlist_info = f"{b_s}Tin Hot:{b_e} {total_hotlist_count}/{hotlist_total}"
    if platform_total > 0:
        hotlist_info += f" (Nền tảng  {platform_success}/{platform_total}）"
    base_header += f"{hotlist_info}\n"

    # 3. RSS
    if rss_source_total > 0:
        rss_info = f"{b_s}RSS:{b_e} {rss_matched}/{rss_total_items} (Nguồn  {rss_source_success}/{rss_source_total}）"
        base_header += f"{rss_info}\n"

    # 4. Standalone display area (only displayed when there is data)
    if standalone_data:
        sa_platform_count = sum(len(p.get("items", [])) for p in standalone_data.get("platforms", []))
        sa_rss_count = sum(len(f.get("items", [])) for f in standalone_data.get("rss_feeds", []))
        sa_total = sa_platform_count + sa_rss_count
        if sa_total > 0:
            sa_parts = []
            if sa_platform_count > 0:
                sa_parts.append(f"Tin Hot {sa_platform_count}")
            if sa_rss_count > 0:
                sa_parts.append(f"RSS {sa_rss_count}")
            base_header += f"{b_s}Nguồn độc lập:{b_e} {sa_total} tin（{' + '.join(sa_parts)}）\n"

    # 5. AI analysis (only displayed when there is analysis data)
    standalone_analyzed = ai_stats.get("standalone_analyzed", 0) if ai_stats else 0
    ai_has_data = ai_stats and (ai_stats.get("analyzed_news", 0) > 0 or standalone_analyzed > 0)
    if ai_has_data:
        hotlist_analyzed = ai_stats.get("hotlist_analyzed", 0)
        rss_analyzed = ai_stats.get("rss_analyzed", 0)
        ai_mode_val = ai_stats.get("ai_mode", "")

        ai_parts = [str(hotlist_analyzed)]
        if ai_stats.get("include_rss", True):
            ai_parts.append(str(rss_analyzed))
        if ai_stats.get("include_standalone", False):
            ai_parts.append(str(standalone_analyzed))
        ai_display = " + ".join(ai_parts) if sum(int(p) for p in ai_parts) > 0 else "0"

        mode_suffix = ""
        if ai_mode_val and ai_mode_val != mode:
            mode_map = {"daily": "Tổng hợp ngày", "current": "Bảng xếp hạng hiện tại", "incremental": "Phân tích mới"}
            mode_suffix = f" [{mode_map.get(ai_mode_val, ai_mode_val)}]"

        base_header += f"{b_s}AI Phân tích:{b_e} {ai_display}{mode_suffix}\n"

    # === Blank line separator ===
    base_header += "\n"

    # === Lower part: Meta information ===
    base_header += f"{b_s}Loại:{b_e} {report_type}\n"
    base_header += f"{b_s}Thời gian:{b_e} {now.strftime('%Y-%m-%d %H:%M:%S')}\n"

    top_words = report_data.get("stats", [])[:3]
    if top_words:
        topics = " | ".join(f"{s['word']}({s['count']})" for s in top_words)
        base_header += f"{b_s}Chủ đề hot nhất:{b_e} {topics}\n"

    if format_type in ("feishu", "dingtalk"):
        base_header += "\n---\n\n"
    else:
        base_header += "\n"

    base_footer = ""
    if format_type in ("wework", "bark"):
        base_footer = f"\n\n\n> Thời gian cập nhật: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        if update_info:
            base_footer += f"\n> TrendRadar có phiên bản mới **{update_info['remote_version']}**，hiện tại **{update_info['current_version']}**"
    elif format_type == "telegram":
        base_footer = f"\n\nThời gian cập nhật: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        if update_info:
            base_footer += f"\nTrendRadar có phiên bản mới {update_info['remote_version']}，hiện tại {update_info['current_version']}"
    elif format_type == "ntfy":
        base_footer = f"\n\n> Thời gian cập nhật: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        if update_info:
            base_footer += f"\n> TrendRadar có phiên bản mới **{update_info['remote_version']}**，hiện tại **{update_info['current_version']}**"
    elif format_type == "feishu":
        base_footer = f"\n\n<font color='grey'>Thời gian cập nhật: {now.strftime('%Y-%m-%d %H:%M:%S')}</font>"
        if update_info:
            base_footer += f"\n<font color='grey'>TrendRadar có phiên bản mới {update_info['remote_version']}，hiện tại {update_info['current_version']}</font>"
    elif format_type == "dingtalk":
        base_footer = f"\n\n> Thời gian cập nhật: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        if update_info:
            base_footer += f"\n> TrendRadar có phiên bản mới **{update_info['remote_version']}**，hiện tại **{update_info['current_version']}**"
    elif format_type == "slack":
        base_footer = f"\n\n_Thời gian cập nhật: {now.strftime('%Y-%m-%d %H:%M:%S')}_"
        if update_info:
            base_footer += f"\n_TrendRadar có phiên bản mới *{update_info['remote_version']}*，hiện tại *{update_info['current_version']}_"

    # Select statistics title based on display_mode
    stats_title = "Thống kê từ khóa hot" if display_mode == "keyword" else "Thống kê tin hot"
    stats_header = ""
    if report_data["stats"]:
        if format_type in ("wework", "bark"):
            stats_header = f"📊 **{stats_title}** (Tổng {total_hotlist_count} tin)\n\n"
        elif format_type == "telegram":
            stats_header = f"📊 {stats_title} (Tổng {total_hotlist_count} tin)\n\n"
        elif format_type == "ntfy":
            stats_header = f"📊 **{stats_title}** (Tổng {total_hotlist_count} tin)\n\n"
        elif format_type == "feishu":
            stats_header = f"📊 **{stats_title}** (Tổng {total_hotlist_count} tin)\n\n"
        elif format_type == "dingtalk":
            stats_header = f"📊 **{stats_title}** (Tổng {total_hotlist_count} tin)\n\n"
        elif format_type == "slack":
            stats_header = f"📊 *{stats_title}* (Tổng {total_hotlist_count} tin)\n\n"

    current_batch = base_header
    current_batch_has_content = False

    # Handling when there is no Tin Hot data
    # Note: If there is ai_content, it should not return "No match" message, but should continue to process AI content
    if (
        not report_data["stats"]
        and not report_data["new_titles"]
        and not report_data["failed_ids"]
        and not ai_content  # Do not return "No match" when there is AI content
        and not rss_items  # Do not return when there is RSS content either
        and not standalone_data  # Do not return when there is standalone display area data either
    ):
        if mode == "incremental":
            mode_text = "Không có tin mới nào phù hợp"
        elif mode == "current":
            mode_text = "Bảng xếp hạng hiện tại mode Không có từ khóa hot nào phù hợp"
        else:
            mode_text = "Không có từ khóa hot nào phù hợp"
        simple_content = f"📭 {mode_text}\n\n"
        final_content = base_header + simple_content + base_footer
        batches.append(final_content)
        return batches

    # Define function to process Thống kê từ khóa hot
    def process_stats_section(current_batch, current_batch_has_content, batches, add_separator=True):
        """Process Thống kê từ khóa hot"""
        if not report_data["stats"]:
            return current_batch, current_batch_has_content, batches

        total_count = len(report_data["stats"])

        # Decide whether to add a leading separator based on add_separator
        actual_stats_header = ""
        if add_separator and current_batch_has_content:
            # Need to add separator
            if format_type == "feishu":
                actual_stats_header = f"\n{feishu_separator}\n\n{stats_header}"
            elif format_type == "dingtalk":
                actual_stats_header = f"\n---\n\n{stats_header}"
            elif format_type in ("wework", "bark"):
                actual_stats_header = f"\n\n\n\n{stats_header}"
            else:
                actual_stats_header = f"\n\n{stats_header}"
        else:
            # No separator needed (first region)
            actual_stats_header = stats_header

        # Add statistics title
        test_content = current_batch + actual_stats_header
        if (
            len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
            < max_bytes
        ):
            current_batch = test_content
            current_batch_has_content = True
        else:
            if current_batch_has_content:
                _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
            current_batch = _safe_new_batch(
                base_header + stats_header, base_footer, max_bytes, base_header, batches
            )
            current_batch_has_content = True

        # Process phrases one by one (ensure atomicity of phrase title + first tin news)
        for i, stat in enumerate(report_data["stats"]):
            word = stat["word"]
            count = stat["count"]
            sequence_display = f"[{i + 1}/{total_count}]"

            # Build phrase title
            word_header = ""
            if format_type in ("wework", "bark"):
                if count >= 10:
                    word_header = (
                        f"🔥 {sequence_display} **{word}** : **{count}** tin\n\n"
                    )
                elif count >= 5:
                    word_header = (
                        f"📈 {sequence_display} **{word}** : **{count}** tin\n\n"
                    )
                else:
                    word_header = f"📌 {sequence_display} **{word}** : {count} tin\n\n"
            elif format_type == "telegram":
                if count >= 10:
                    word_header = f"🔥 {sequence_display} {word} : {count} tin\n\n"
                elif count >= 5:
                    word_header = f"📈 {sequence_display} {word} : {count} tin\n\n"
                else:
                    word_header = f"📌 {sequence_display} {word} : {count} tin\n\n"
            elif format_type == "ntfy":
                if count >= 10:
                    word_header = (
                        f"🔥 {sequence_display} **{word}** : **{count}** tin\n\n"
                    )
                elif count >= 5:
                    word_header = (
                        f"📈 {sequence_display} **{word}** : **{count}** tin\n\n"
                    )
                else:
                    word_header = f"📌 {sequence_display} **{word}** : {count} tin\n\n"
            elif format_type == "feishu":
                if count >= 10:
                    word_header = f"🔥 <font color='grey'>{sequence_display}</font> **{word}** : <font color='red'>{count}</font> tin\n\n"
                elif count >= 5:
                    word_header = f"📈 <font color='grey'>{sequence_display}</font> **{word}** : <font color='orange'>{count}</font> tin\n\n"
                else:
                    word_header = f"📌 <font color='grey'>{sequence_display}</font> **{word}** : {count} tin\n\n"
            elif format_type == "dingtalk":
                if count >= 10:
                    word_header = (
                        f"🔥 {sequence_display} **{word}** : **{count}** tin\n\n"
                    )
                elif count >= 5:
                    word_header = (
                        f"📈 {sequence_display} **{word}** : **{count}** tin\n\n"
                    )
                else:
                    word_header = f"📌 {sequence_display} **{word}** : {count} tin\n\n"
            elif format_type == "slack":
                if count >= 10:
                    word_header = (
                        f"🔥 {sequence_display} *{word}* : *{count}* tin\n\n"
                    )
                elif count >= 5:
                    word_header = (
                        f"📈 {sequence_display} *{word}* : *{count}* tin\n\n"
                    )
                else:
                    word_header = f"📌 {sequence_display} *{word}* : {count} tin\n\n"

            # Build first tin news
            # display_mode: keyword=display source, platform=display keyword
            show_source = display_mode == "keyword"
            show_keyword = display_mode == "platform"
            first_news_line = ""
            if stat["titles"]:
                first_title_data = stat["titles"][0]
                if format_type in ("wework", "bark"):
                    formatted_title = format_title_for_platform(
                        "wework", first_title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "telegram":
                    formatted_title = format_title_for_platform(
                        "telegram", first_title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "ntfy":
                    formatted_title = format_title_for_platform(
                        "ntfy", first_title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "feishu":
                    formatted_title = format_title_for_platform(
                        "feishu", first_title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "dingtalk":
                    formatted_title = format_title_for_platform(
                        "dingtalk", first_title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "slack":
                    formatted_title = format_title_for_platform(
                        "slack", first_title_data, show_source=show_source, show_keyword=show_keyword
                    )
                else:
                    formatted_title = f"{first_title_data['title']}"

                first_news_line = f"  1. {formatted_title}\n"
                if len(stat["titles"]) > 1:
                    first_news_line += "\n"

            # Atomicity check: phrase title + first tin news must be processed together
            word_with_first_news = word_header + first_news_line
            test_content = current_batch + word_with_first_news

            if (
                len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                >= max_bytes
            ):
                if current_batch_has_content:
                    _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                current_batch = _safe_new_batch(
                    base_header + stats_header + word_with_first_news,
                    base_footer, max_bytes, base_header, batches
                )
                current_batch_has_content = True
                start_index = 1
            else:
                current_batch = test_content
                current_batch_has_content = True
                start_index = 1

            # Process remaining news tin items
            for j in range(start_index, len(stat["titles"])):
                title_data = stat["titles"][j]
                if format_type in ("wework", "bark"):
                    formatted_title = format_title_for_platform(
                        "wework", title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "telegram":
                    formatted_title = format_title_for_platform(
                        "telegram", title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "ntfy":
                    formatted_title = format_title_for_platform(
                        "ntfy", title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "feishu":
                    formatted_title = format_title_for_platform(
                        "feishu", title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "dingtalk":
                    formatted_title = format_title_for_platform(
                        "dingtalk", title_data, show_source=show_source, show_keyword=show_keyword
                    )
                elif format_type == "slack":
                    formatted_title = format_title_for_platform(
                        "slack", title_data, show_source=show_source, show_keyword=show_keyword
                    )
                else:
                    formatted_title = f"{title_data['title']}"

                news_line = f"  {j + 1}. {formatted_title}\n"
                if j < len(stat["titles"]) - 1:
                    news_line += "\n"

                test_content = current_batch + news_line
                if (
                    len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                    >= max_bytes
                ):
                    if current_batch_has_content:
                        _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                    current_batch = _safe_new_batch(
                        base_header + stats_header + word_header + news_line,
                        base_footer, max_bytes, base_header, batches
                    )
                    current_batch_has_content = True
                else:
                    current_batch = test_content
                    current_batch_has_content = True

            # Separator between phrases
            if i < len(report_data["stats"]) - 1:
                separator = ""
                if format_type in ("wework", "bark"):
                    separator = f"\n\n\n\n"
                elif format_type == "telegram":
                    separator = f"\n\n"
                elif format_type == "ntfy":
                    separator = f"\n\n"
                elif format_type == "feishu":
                    separator = f"\n{feishu_separator}\n\n"
                elif format_type == "dingtalk":
                    separator = f"\n---\n\n"
                elif format_type == "slack":
                    separator = f"\n\n"

                test_content = current_batch + separator
                if (
                    len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                    < max_bytes
                ):
                    current_batch = test_content

        return current_batch, current_batch_has_content, batches

    # Define function to process new news
    def process_new_titles_section(current_batch, current_batch_has_content, batches, add_separator=True):
        """Process new news"""
        if not show_new_section or not report_data["new_titles"]:
            return current_batch, current_batch_has_content, batches

        # Decide whether to add a preceding separator based on add_separator
        new_header = ""
        if add_separator and current_batch_has_content:
            # Need to add separator
            if format_type in ("wework", "bark"):
                new_header = f"\n\n\n\n🆕 **Tin hot mới cập nhật** (Tổng {report_data['total_new_count']} tin)\n\n"
            elif format_type == "telegram":
                new_header = (
                    f"\n\n🆕 Tin hot mới cập nhật (Tổng {report_data['total_new_count']} tin)\n\n"
                )
            elif format_type == "ntfy":
                new_header = f"\n\n🆕 **Tin hot mới cập nhật** (Tổng {report_data['total_new_count']} tin)\n\n"
            elif format_type == "feishu":
                new_header = f"\n{feishu_separator}\n\n🆕 **Tin hot mới cập nhật** (Tổng {report_data['total_new_count']} tin)\n\n"
            elif format_type == "dingtalk":
                new_header = f"\n---\n\n🆕 **Tin hot mới cập nhật** (Tổng {report_data['total_new_count']} tin)\n\n"
            elif format_type == "slack":
                new_header = f"\n\n🆕 *Tin hot mới cập nhật* (Tổng {report_data['total_new_count']} tin)\n\n"
        else:
            # No separator needed (first region)
            if format_type in ("wework", "bark"):
                new_header = f"🆕 **Tin hot mới cập nhật** (Tổng {report_data['total_new_count']} tin)\n\n"
            elif format_type == "telegram":
                new_header = f"🆕 Tin hot mới cập nhật (Tổng {report_data['total_new_count']} tin)\n\n"
            elif format_type == "ntfy":
                new_header = f"🆕 **Tin hot mới cập nhật** (Tổng {report_data['total_new_count']} tin)\n\n"
            elif format_type == "feishu":
                new_header = f"🆕 **Tin hot mới cập nhật** (Tổng {report_data['total_new_count']} tin)\n\n"
            elif format_type == "dingtalk":
                new_header = f"🆕 **Tin hot mới cập nhật** (Tổng {report_data['total_new_count']} tin)\n\n"
            elif format_type == "slack":
                new_header = f"🆕 *Tin hot mới cập nhật* (Tổng {report_data['total_new_count']} tin)\n\n"

        test_content = current_batch + new_header
        if (
            len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
            >= max_bytes
        ):
            if current_batch_has_content:
                _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
            current_batch = _safe_new_batch(
                base_header + new_header, base_footer, max_bytes, base_header, batches
            )
            current_batch_has_content = True
        else:
            current_batch = test_content
            current_batch_has_content = True

        # Process new news sources one by one
        for source_data in report_data["new_titles"]:
            source_header = ""
            if format_type in ("wework", "bark"):
                source_header = f"**{source_data['source_name']}** ({len(source_data['titles'])} tin):\n\n"
            elif format_type == "telegram":
                source_header = f"{source_data['source_name']} ({len(source_data['titles'])} tin):\n\n"
            elif format_type == "ntfy":
                source_header = f"**{source_data['source_name']}** ({len(source_data['titles'])} tin):\n\n"
            elif format_type == "feishu":
                source_header = f"**{source_data['source_name']}** ({len(source_data['titles'])} tin):\n\n"
            elif format_type == "dingtalk":
                source_header = f"**{source_data['source_name']}** ({len(source_data['titles'])} tin):\n\n"
            elif format_type == "slack":
                source_header = f"*{source_data['source_name']}* ({len(source_data['titles'])} tin):\n\n"

            # Build first tin new news
            first_news_line = ""
            if source_data["titles"]:
                first_title_data = source_data["titles"][0]
                title_data_copy = first_title_data.copy()
                title_data_copy["is_new"] = False

                if format_type in ("wework", "bark"):
                    formatted_title = format_title_for_platform(
                        "wework", title_data_copy, show_source=False
                    )
                elif format_type == "telegram":
                    formatted_title = format_title_for_platform(
                        "telegram", title_data_copy, show_source=False
                    )
                elif format_type == "feishu":
                    formatted_title = format_title_for_platform(
                        "feishu", title_data_copy, show_source=False
                    )
                elif format_type == "dingtalk":
                    formatted_title = format_title_for_platform(
                        "dingtalk", title_data_copy, show_source=False
                    )
                elif format_type == "slack":
                    formatted_title = format_title_for_platform(
                        "slack", title_data_copy, show_source=False
                    )
                else:
                    formatted_title = f"{title_data_copy['title']}"

                first_news_line = f"  1. {formatted_title}\n"

            # Atomicity check: source title + first tin news
            source_with_first_news = source_header + first_news_line
            test_content = current_batch + source_with_first_news

            if (
                len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                >= max_bytes
            ):
                if current_batch_has_content:
                    _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                current_batch = _safe_new_batch(
                    base_header + new_header + source_with_first_news,
                    base_footer, max_bytes, base_header, batches
                )
                current_batch_has_content = True
                start_index = 1
            else:
                current_batch = test_content
                current_batch_has_content = True
                start_index = 1

            # Process remaining new news
            for j in range(start_index, len(source_data["titles"])):
                title_data = source_data["titles"][j]
                title_data_copy = title_data.copy()
                title_data_copy["is_new"] = False

                if format_type == "wework":
                    formatted_title = format_title_for_platform(
                        "wework", title_data_copy, show_source=False
                    )
                elif format_type == "telegram":
                    formatted_title = format_title_for_platform(
                        "telegram", title_data_copy, show_source=False
                    )
                elif format_type == "feishu":
                    formatted_title = format_title_for_platform(
                        "feishu", title_data_copy, show_source=False
                    )
                elif format_type == "dingtalk":
                    formatted_title = format_title_for_platform(
                        "dingtalk", title_data_copy, show_source=False
                    )
                elif format_type == "slack":
                    formatted_title = format_title_for_platform(
                        "slack", title_data_copy, show_source=False
                    )
                else:
                    formatted_title = f"{title_data_copy['title']}"

                news_line = f"  {j + 1}. {formatted_title}\n"

                test_content = current_batch + news_line
                if (
                    len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                    >= max_bytes
                ):
                    if current_batch_has_content:
                        _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                    current_batch = _safe_new_batch(
                        base_header + new_header + source_header + news_line,
                        base_footer, max_bytes, base_header, batches
                    )
                    current_batch_has_content = True
                else:
                    current_batch = test_content
                    current_batch_has_content = True

            current_batch += "\n"

        return current_batch, current_batch_has_content, batches

    # Define function to process AI analysis
    def process_ai_section(current_batch, current_batch_has_content, batches, add_separator=True):
        """Process AI analysis content"""
        nonlocal ai_content
        if not ai_content:
            return current_batch, current_batch_has_content, batches

        # Decide whether to add a preceding separator based on add_separator
        ai_separator = ""
        if add_separator and current_batch_has_content:
            # Need to add separator
            if format_type == "feishu":
                ai_separator = f"\n{feishu_separator}\n\n"
            elif format_type == "dingtalk":
                ai_separator = "\n---\n\n"
            elif format_type in ("wework", "bark"):
                ai_separator = "\n\n\n\n"
            elif format_type in ("telegram", "ntfy", "slack"):
                ai_separator = "\n\n"
        # If no separator is needed, ai_separator remains an empty string

        # Try to add AI content to hiện tại batch
        test_content = current_batch + ai_separator + ai_content
        if (
            len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
            < max_bytes
        ):
            current_batch = test_content
            current_batch_has_content = True
        else:
            if current_batch_has_content:
                _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)

            # AI content may be very long, split into multiple batches by line
            footer_size = len(base_footer.encode("utf-8"))
            header_size = len(base_header.encode("utf-8"))
            available = max_bytes - footer_size - header_size

            ai_lines = ai_content.split("\n")
            current_batch = base_header
            current_batch_has_content = False

            for line in ai_lines:
                test_line = line + "\n" if not line.endswith("\n") else line
                test_content = current_batch + test_line
                if len(test_content.encode("utf-8")) + footer_size >= max_bytes and current_batch_has_content:
                    _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                    current_batch = base_header + test_line
                else:
                    current_batch = test_content
                current_batch_has_content = True

        return current_batch, current_batch_has_content, batches

    # Define function to process independent display area
    def process_standalone_section_wrapper(current_batch, current_batch_has_content, batches, add_separator=True):
        """Process independent display area"""
        if not standalone_data:
            return current_batch, current_batch_has_content, batches
        return _process_standalone_section(
            standalone_data, format_type, feishu_separator, base_header, base_footer,
            max_bytes, current_batch, current_batch_has_content, batches, timezone,
            rank_threshold, add_separator
        )

    # Define function to process RSS statistics
    def process_rss_stats_wrapper(current_batch, current_batch_has_content, batches, add_separator=True):
        """Process RSS statistics"""
        if not rss_items:
            return current_batch, current_batch_has_content, batches
        return _process_rss_stats_section(
            rss_items, format_type, feishu_separator, base_header, base_footer,
            max_bytes, current_batch, current_batch_has_content, batches, timezone,
            add_separator
        )

    # Define function to process RSS additions
    def process_rss_new_wrapper(current_batch, current_batch_has_content, batches, add_separator=True):
        """Process RSS additions"""
        if not rss_new_items:
            return current_batch, current_batch_has_content, batches
        return _process_rss_new_titles_section(
            rss_new_items, format_type, feishu_separator, base_header, base_footer,
            max_bytes, current_batch, current_batch_has_content, batches, timezone,
            add_separator
        )

    # Process each region in region_order sequence
    # Record whether there is already region content (used to decide whether to add a separator)
    has_region_content = False

    for region in region_order:
        # Record the state before processing, used to determine whether the region generated content
        batch_before = current_batch
        has_content_before = current_batch_has_content
        batches_len_before = len(batches)

        # Decide whether a separator needs to be added (not needed for the first region with content)
        add_separator = has_region_content

        if region == "hotlist":
            # Process Tin Hot statistics
            current_batch, current_batch_has_content, batches = process_stats_section(
                current_batch, current_batch_has_content, batches, add_separator
            )
        elif region == "rss":
            # Process RSS statistics
            current_batch, current_batch_has_content, batches = process_rss_stats_wrapper(
                current_batch, current_batch_has_content, batches, add_separator
            )
        elif region == "new_items":
            # Process Tin Hot additions
            current_batch, current_batch_has_content, batches = process_new_titles_section(
                current_batch, current_batch_has_content, batches, add_separator
            )
            # Process RSS additions (follows new_items, inherits add_separator logic)
            # If Tin Hot additions generated content, RSS additions need a separator
            new_batch_changed = (
                current_batch != batch_before or
                current_batch_has_content != has_content_before or
                len(batches) != batches_len_before
            )
            rss_new_separator = new_batch_changed or has_region_content
            current_batch, current_batch_has_content, batches = process_rss_new_wrapper(
                current_batch, current_batch_has_content, batches, rss_new_separator
            )
        elif region == "standalone":
            # Process independent display area
            current_batch, current_batch_has_content, batches = process_standalone_section_wrapper(
                current_batch, current_batch_has_content, batches, add_separator
            )
        elif region == "ai_analysis":
            # Process AI analysis
            current_batch, current_batch_has_content, batches = process_ai_section(
                current_batch, current_batch_has_content, batches, add_separator
            )

        # Check whether this region generated content
        region_produced_content = (
            current_batch != batch_before or
            current_batch_has_content != has_content_before or
            len(batches) != batches_len_before
        )
        if region_produced_content:
            has_region_content = True

    if report_data["failed_ids"]:
        failed_header = ""
        if format_type == "wework":
            failed_header = f"\n\n\n\n⚠️ **Platforms that failed to fetch data:**\n\n"
        elif format_type == "telegram":
            failed_header = f"\n\n⚠️ Platforms that failed to fetch data:\n\n"
        elif format_type == "ntfy":
            failed_header = f"\n\n⚠️ **Platforms that failed to fetch data:**\n\n"
        elif format_type == "feishu":
            failed_header = f"\n{feishu_separator}\n\n⚠️ **Platforms that failed to fetch data:**\n\n"
        elif format_type == "dingtalk":
            failed_header = f"\n---\n\n⚠️ **Platforms that failed to fetch data:**\n\n"

        test_content = current_batch + failed_header
        if (
            len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
            >= max_bytes
        ):
            if current_batch_has_content:
                _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
            current_batch = _safe_new_batch(
                base_header + failed_header, base_footer, max_bytes, base_header, batches
            )
            current_batch_has_content = True
        else:
            current_batch = test_content
            current_batch_has_content = True

        for i, id_value in enumerate(report_data["failed_ids"], 1):
            if format_type == "feishu":
                failed_line = f"  • <font color='red'>{id_value}</font>\n"
            elif format_type == "dingtalk":
                failed_line = f"  • **{id_value}**\n"
            else:
                failed_line = f"  • {id_value}\n"

            test_content = current_batch + failed_line
            if (
                len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                >= max_bytes
            ):
                if current_batch_has_content:
                    _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                current_batch = _safe_new_batch(
                    base_header + failed_header + failed_line,
                    base_footer, max_bytes, base_header, batches
                )
                current_batch_has_content = True
            else:
                current_batch = test_content
                current_batch_has_content = True

    # Complete the final batch
    if current_batch_has_content:
        _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)

    return batches


def _process_rss_stats_section(
    rss_stats: list,
    format_type: str,
    feishu_separator: str,
    base_header: str,
    base_footer: str,
    max_bytes: int,
    current_batch: str,
    current_batch_has_content: bool,
    batches: List[str],
    timezone: str = DEFAULT_TIMEZONE,
    add_separator: bool = True,
) -> tuple:
    """Process RSS stats block (grouped by keyword, consistent with Tin Hot stats format)

    Args:
        rss_stats: RSS keyword stats list, format consistent with Tin Hot stats:
            [{"word": "AI", "count": 5, "titles": [...]}]
        format_type: Format type
        feishu_separator: Feishu separator
        base_header: Base header
        base_footer: Base footer
        max_bytes: Maximum bytes
        current_batch: hiện tại batch content
        current_batch_has_content: hiện tại whether batch has content
        batches: Completed batch list
        timezone: Timezone name
        add_separator: Whether to add a separator before the block (False for the first area)

    Returns:
        (current_batch, current_batch_has_content, batches) tuple
    """
    if not rss_stats:
        return current_batch, current_batch_has_content, batches

    # Calculate total number of tin items
    total_items = sum(stat["count"] for stat in rss_stats)
    total_keywords = len(rss_stats)

    # RSS stats block title (determine whether to add a leading separator based on add_separator)
    rss_header = ""
    if add_separator and current_batch_has_content:
        # Need to add separator
        if format_type == "feishu":
            rss_header = f"\n{feishu_separator}\n\n📰 **Thống kê RSS** (Tổng {total_items} tin)\n\n"
        elif format_type == "dingtalk":
            rss_header = f"\n---\n\n📰 **Thống kê RSS** (Tổng {total_items} tin)\n\n"
        elif format_type in ("wework", "bark"):
            rss_header = f"\n\n\n\n📰 **Thống kê RSS** (Tổng {total_items} tin)\n\n"
        elif format_type == "telegram":
            rss_header = f"\n\n📰 Thống kê RSS (Tổng {total_items} tin)\n\n"
        elif format_type == "slack":
            rss_header = f"\n\n📰 *Thống kê RSS* (Tổng {total_items} tin)\n\n"
        else:
            rss_header = f"\n\n📰 **Thống kê RSS** (Tổng {total_items} tin)\n\n"
    else:
        # No separator needed (first area)
        if format_type == "feishu":
            rss_header = f"📰 **Thống kê RSS** (Tổng {total_items} tin)\n\n"
        elif format_type == "dingtalk":
            rss_header = f"📰 **Thống kê RSS** (Tổng {total_items} tin)\n\n"
        elif format_type == "telegram":
            rss_header = f"📰 Thống kê RSS (Tổng {total_items} tin)\n\n"
        elif format_type == "slack":
            rss_header = f"📰 *Thống kê RSS* (Tổng {total_items} tin)\n\n"
        else:
            rss_header = f"📰 **Thống kê RSS** (Tổng {total_items} tin)\n\n"

    # Add RSS title
    test_content = current_batch + rss_header
    if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) < max_bytes:
        current_batch = test_content
        current_batch_has_content = True
    else:
        if current_batch_has_content:
            _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
        current_batch = _safe_new_batch(
            base_header + rss_header, base_footer, max_bytes, base_header, batches
        )
        current_batch_has_content = True

    # Process keyword groups one by one (consistent with Tin Hot)
    for i, stat in enumerate(rss_stats):
        word = stat["word"]
        count = stat["count"]
        sequence_display = f"[{i + 1}/{total_keywords}]"

        # Build keyword title (consistent with Tin Hot format)
        word_header = ""
        if format_type in ("wework", "bark"):
            if count >= 10:
                word_header = f"🔥 {sequence_display} **{word}** : **{count}** tin\n\n"
            elif count >= 5:
                word_header = f"📈 {sequence_display} **{word}** : **{count}** tin\n\n"
            else:
                word_header = f"📌 {sequence_display} **{word}** : {count} tin\n\n"
        elif format_type == "telegram":
            if count >= 10:
                word_header = f"🔥 {sequence_display} {word} : {count} tin\n\n"
            elif count >= 5:
                word_header = f"📈 {sequence_display} {word} : {count} tin\n\n"
            else:
                word_header = f"📌 {sequence_display} {word} : {count} tin\n\n"
        elif format_type == "ntfy":
            if count >= 10:
                word_header = f"🔥 {sequence_display} **{word}** : **{count}** tin\n\n"
            elif count >= 5:
                word_header = f"📈 {sequence_display} **{word}** : **{count}** tin\n\n"
            else:
                word_header = f"📌 {sequence_display} **{word}** : {count} tin\n\n"
        elif format_type == "feishu":
            if count >= 10:
                word_header = f"🔥 <font color='grey'>{sequence_display}</font> **{word}** : <font color='red'>{count}</font> tin\n\n"
            elif count >= 5:
                word_header = f"📈 <font color='grey'>{sequence_display}</font> **{word}** : <font color='orange'>{count}</font> tin\n\n"
            else:
                word_header = f"📌 <font color='grey'>{sequence_display}</font> **{word}** : {count} tin\n\n"
        elif format_type == "dingtalk":
            if count >= 10:
                word_header = f"🔥 {sequence_display} **{word}** : **{count}** tin\n\n"
            elif count >= 5:
                word_header = f"📈 {sequence_display} **{word}** : **{count}** tin\n\n"
            else:
                word_header = f"📌 {sequence_display} **{word}** : {count} tin\n\n"
        elif format_type == "slack":
            if count >= 10:
                word_header = f"🔥 {sequence_display} *{word}* : *{count}* tin\n\n"
            elif count >= 5:
                word_header = f"📈 {sequence_display} *{word}* : *{count}* tin\n\n"
            else:
                word_header = f"📌 {sequence_display} *{word}* : {count} tin\n\n"

        # Build first tin news (using format_title_for_platform)
        first_news_line = ""
        if stat["titles"]:
            first_title_data = stat["titles"][0]
            if format_type in ("wework", "bark"):
                formatted_title = format_title_for_platform("wework", first_title_data, show_source=True)
            elif format_type == "telegram":
                formatted_title = format_title_for_platform("telegram", first_title_data, show_source=True)
            elif format_type == "ntfy":
                formatted_title = format_title_for_platform("ntfy", first_title_data, show_source=True)
            elif format_type == "feishu":
                formatted_title = format_title_for_platform("feishu", first_title_data, show_source=True)
            elif format_type == "dingtalk":
                formatted_title = format_title_for_platform("dingtalk", first_title_data, show_source=True)
            elif format_type == "slack":
                formatted_title = format_title_for_platform("slack", first_title_data, show_source=True)
            else:
                formatted_title = f"{first_title_data['title']}"

            first_news_line = f"  1. {formatted_title}\n"
            if len(stat["titles"]) > 1:
                first_news_line += "\n"

        # Atomicity check: keyword title + first tin news must be processed together
        word_with_first_news = word_header + first_news_line
        test_content = current_batch + word_with_first_news

        if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) >= max_bytes:
            if current_batch_has_content:
                _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
            current_batch = _safe_new_batch(
                base_header + rss_header + word_with_first_news,
                base_footer, max_bytes, base_header, batches
            )
            current_batch_has_content = True
            start_index = 1
        else:
            current_batch = test_content
            current_batch_has_content = True
            start_index = 1

        # Process remaining news tin items
        for j in range(start_index, len(stat["titles"])):
            title_data = stat["titles"][j]
            if format_type in ("wework", "bark"):
                formatted_title = format_title_for_platform("wework", title_data, show_source=True)
            elif format_type == "telegram":
                formatted_title = format_title_for_platform("telegram", title_data, show_source=True)
            elif format_type == "ntfy":
                formatted_title = format_title_for_platform("ntfy", title_data, show_source=True)
            elif format_type == "feishu":
                formatted_title = format_title_for_platform("feishu", title_data, show_source=True)
            elif format_type == "dingtalk":
                formatted_title = format_title_for_platform("dingtalk", title_data, show_source=True)
            elif format_type == "slack":
                formatted_title = format_title_for_platform("slack", title_data, show_source=True)
            else:
                formatted_title = f"{title_data['title']}"

            news_line = f"  {j + 1}. {formatted_title}\n"
            if j < len(stat["titles"]) - 1:
                news_line += "\n"

            test_content = current_batch + news_line
            if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) >= max_bytes:
                if current_batch_has_content:
                    _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                current_batch = _safe_new_batch(
                    base_header + rss_header + word_header + news_line,
                    base_footer, max_bytes, base_header, batches
                )
                current_batch_has_content = True
            else:
                current_batch = test_content
                current_batch_has_content = True

        # Separator between keywords
        if i < len(rss_stats) - 1:
            separator = ""
            if format_type in ("wework", "bark"):
                separator = "\n\n\n\n"
            elif format_type == "telegram":
                separator = "\n\n"
            elif format_type == "ntfy":
                separator = "\n\n"
            elif format_type == "feishu":
                separator = f"\n{feishu_separator}\n\n"
            elif format_type == "dingtalk":
                separator = "\n---\n\n"
            elif format_type == "slack":
                separator = "\n\n"

            test_content = current_batch + separator
            if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) < max_bytes:
                current_batch = test_content

    return current_batch, current_batch_has_content, batches


def _process_rss_new_titles_section(
    rss_new_stats: list,
    format_type: str,
    feishu_separator: str,
    base_header: str,
    base_footer: str,
    max_bytes: int,
    current_batch: str,
    current_batch_has_content: bool,
    batches: List[str],
    timezone: str = DEFAULT_TIMEZONE,
    add_separator: bool = True,
) -> tuple:
    """Process RSS new block (grouped by source, consistent with Tin Hot new format)

    Args:
        rss_new_stats: RSS new keyword stats list, format consistent with Tin Hot stats:
            [{"word": "AI", "count": 5, "titles": [...]}]
        format_type: Format type
        feishu_separator: Feishu separator
        base_header: Base header
        base_footer: Base footer
        max_bytes: Maximum bytes
        current_batch: hiện tại batch content
        current_batch_has_content: hiện tại whether batch has content
        batches: Completed batch list
        timezone: Timezone name
        add_separator: Whether to add a separator before the block (False for the first area)

    Returns:
        (current_batch, current_batch_has_content, batches) tuple
    """
    if not rss_new_stats:
        return current_batch, current_batch_has_content, batches

    # Extract all items from keyword grouping, regroup by source
    source_map = {}
    for stat in rss_new_stats:
        for title_data in stat.get("titles", []):
            source_name = title_data.get("source_name", "Unknown source")
            if source_name not in source_map:
                source_map[source_name] = []
            source_map[source_name].append(title_data)

    if not source_map:
        return current_batch, current_batch_has_content, batches

    # Calculate total number of items
    total_items = sum(len(titles) for titles in source_map.values())

    # RSS newly added block title (decide whether to add a preceding separator based on add_separator)
    new_header = ""
    if add_separator and current_batch_has_content:
        # Need to add separator
        if format_type in ("wework", "bark"):
            new_header = f"\n\n\n\n🆕 **RSS newly added this time** (Tổng {total_items} tin)\n\n"
        elif format_type == "telegram":
            new_header = f"\n\n🆕 RSS newly added this time (Tổng {total_items} tin)\n\n"
        elif format_type == "ntfy":
            new_header = f"\n\n🆕 **RSS newly added this time** (Tổng {total_items} tin)\n\n"
        elif format_type == "feishu":
            new_header = f"\n{feishu_separator}\n\n🆕 **RSS newly added this time** (Tổng {total_items} tin)\n\n"
        elif format_type == "dingtalk":
            new_header = f"\n---\n\n🆕 **RSS newly added this time** (Tổng {total_items} tin)\n\n"
        elif format_type == "slack":
            new_header = f"\n\n🆕 *RSS newly added this time* (Tổng {total_items} tin)\n\n"
    else:
        # No separator needed (first area)
        if format_type in ("wework", "bark"):
            new_header = f"🆕 **RSS newly added this time** (Tổng {total_items} tin)\n\n"
        elif format_type == "telegram":
            new_header = f"🆕 RSS newly added this time (Tổng {total_items} tin)\n\n"
        elif format_type == "ntfy":
            new_header = f"🆕 **RSS newly added this time** (Tổng {total_items} tin)\n\n"
        elif format_type == "feishu":
            new_header = f"🆕 **RSS newly added this time** (Tổng {total_items} tin)\n\n"
        elif format_type == "dingtalk":
            new_header = f"🆕 **RSS newly added this time** (Tổng {total_items} tin)\n\n"
        elif format_type == "slack":
            new_header = f"🆕 *RSS newly added this time* (Tổng {total_items} tin)\n\n"

    # Add RSS newly added title
    test_content = current_batch + new_header
    if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) >= max_bytes:
        if current_batch_has_content:
            _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
        current_batch = _safe_new_batch(
            base_header + new_header, base_footer, max_bytes, base_header, batches
        )
        current_batch_has_content = True
    else:
        current_batch = test_content
        current_batch_has_content = True

    # Display grouped by source (consistent with Tin Hot newly added format)
    source_list = list(source_map.items())
    for i, (source_name, titles) in enumerate(source_list):
        count = len(titles)

        # Build source title (consistent with Tin Hot newly added format)
        source_header = ""
        if format_type in ("wework", "bark"):
            source_header = f"**{source_name}** ({count} tin):\n\n"
        elif format_type == "telegram":
            source_header = f"{source_name} ({count} tin):\n\n"
        elif format_type == "ntfy":
            source_header = f"**{source_name}** ({count} tin):\n\n"
        elif format_type == "feishu":
            source_header = f"**{source_name}** ({count} tin):\n\n"
        elif format_type == "dingtalk":
            source_header = f"**{source_name}** ({count} tin):\n\n"
        elif format_type == "slack":
            source_header = f"*{source_name}* ({count} tin):\n\n"

        # Build first news item (do not display source, disable new emoji)
        first_news_line = ""
        if titles:
            first_title_data = titles[0].copy()
            first_title_data["is_new"] = False
            if format_type in ("wework", "bark"):
                formatted_title = format_title_for_platform("wework", first_title_data, show_source=False)
            elif format_type == "telegram":
                formatted_title = format_title_for_platform("telegram", first_title_data, show_source=False)
            elif format_type == "ntfy":
                formatted_title = format_title_for_platform("ntfy", first_title_data, show_source=False)
            elif format_type == "feishu":
                formatted_title = format_title_for_platform("feishu", first_title_data, show_source=False)
            elif format_type == "dingtalk":
                formatted_title = format_title_for_platform("dingtalk", first_title_data, show_source=False)
            elif format_type == "slack":
                formatted_title = format_title_for_platform("slack", first_title_data, show_source=False)
            else:
                formatted_title = f"{first_title_data['title']}"

            first_news_line = f"  1. {formatted_title}\n"

        # Atomicity check: source title + first news item must be processed together
        source_with_first_news = source_header + first_news_line
        test_content = current_batch + source_with_first_news

        if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) >= max_bytes:
            if current_batch_has_content:
                _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
            current_batch = _safe_new_batch(
                base_header + new_header + source_with_first_news,
                base_footer, max_bytes, base_header, batches
            )
            current_batch_has_content = True
            start_index = 1
        else:
            current_batch = test_content
            current_batch_has_content = True
            start_index = 1

        # Process remaining news items (disable new emoji)
        for j in range(start_index, len(titles)):
            title_data = titles[j].copy()
            title_data["is_new"] = False
            if format_type in ("wework", "bark"):
                formatted_title = format_title_for_platform("wework", title_data, show_source=False)
            elif format_type == "telegram":
                formatted_title = format_title_for_platform("telegram", title_data, show_source=False)
            elif format_type == "ntfy":
                formatted_title = format_title_for_platform("ntfy", title_data, show_source=False)
            elif format_type == "feishu":
                formatted_title = format_title_for_platform("feishu", title_data, show_source=False)
            elif format_type == "dingtalk":
                formatted_title = format_title_for_platform("dingtalk", title_data, show_source=False)
            elif format_type == "slack":
                formatted_title = format_title_for_platform("slack", title_data, show_source=False)
            else:
                formatted_title = f"{title_data['title']}"

            news_line = f"  {j + 1}. {formatted_title}\n"

            test_content = current_batch + news_line
            if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) >= max_bytes:
                if current_batch_has_content:
                    _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                current_batch = _safe_new_batch(
                    base_header + new_header + source_header + news_line,
                    base_footer, max_bytes, base_header, batches
                )
                current_batch_has_content = True
            else:
                current_batch = test_content
                current_batch_has_content = True

        # Add blank line between sources (consistent with Tin Hot newly added format)
        current_batch += "\n"

    return current_batch, current_batch_has_content, batches


def _format_rss_item_line(
    item: Dict,
    index: int,
    format_type: str,
    timezone: str = DEFAULT_TIMEZONE,
) -> str:
    """Format single RSS item

    Args:
        item: RSS item dictionary
        index: Index
        format_type: Format type
        timezone: Timezone name

    Returns:
        Formatted item line string
    """
    title = item.get("title", "")
    url = item.get("url", "")
    published_at = item.get("published_at", "")

    # Use friendly time format
    if published_at:
        friendly_time = format_iso_time_friendly(published_at, timezone, include_date=True)
    else:
        friendly_time = ""

    # Build item line
    if format_type == "feishu":
        if url:
            item_line = f"  {index}. [{title}]({url})"
        else:
            item_line = f"  {index}. {title}"
        if friendly_time:
            item_line += f" <font color='grey'>- {friendly_time}</font>"
    elif format_type == "telegram":
        if url:
            item_line = f"  {index}. {title} ({url})"
        else:
            item_line = f"  {index}. {title}"
        if friendly_time:
            item_line += f" - {friendly_time}"
    else:
        if url:
            item_line = f"  {index}. [{title}]({url})"
        else:
            item_line = f"  {index}. {title}"
        if friendly_time:
            item_line += f" `{friendly_time}`"

    item_line += "\n"
    return item_line


def _process_standalone_section(
    standalone_data: Dict,
    format_type: str,
    feishu_separator: str,
    base_header: str,
    base_footer: str,
    max_bytes: int,
    current_batch: str,
    current_batch_has_content: bool,
    batches: List[str],
    timezone: str = DEFAULT_TIMEZONE,
    rank_threshold: int = 10,
    add_separator: bool = True,
) -> tuple:
    """Process standalone display area block

    The standalone display area shows the complete Tin Hot or RSS source content of the specified platform, unaffected by keyword filtering.
    Tin Hot is sorted by original ranking, RSS is sorted by publish time.

    Args:
        standalone_data: Standalone display data, format:
            {
                "platforms": [{"id": "zhihu", "name": "Zhihu Tin Hot", "items": [...]}],
                "rss_feeds": [{"id": "hacker-news", "name": "Hacker News", "items": [...]}]
            }
        format_type: Format type
        feishu_separator: Feishu separator
        base_header: Base header
        base_footer: Base footer
        max_bytes: Maximum bytes
        current_batch: hiện tại batch content
        current_batch_has_content: whether hiện tại batch has content
        batches: Completed batch list
        timezone: Timezone name
        rank_threshold: Rank highlight threshold
        add_separator: Whether to add a separator before the block (False for the first area)

    Returns:
        (current_batch, current_batch_has_content, batches) tuple
    """
    if not standalone_data:
        return current_batch, current_batch_has_content, batches

    platforms = standalone_data.get("platforms", [])
    rss_feeds = standalone_data.get("rss_feeds", [])

    if not platforms and not rss_feeds:
        return current_batch, current_batch_has_content, batches

    # Calculate total tin count
    total_platform_items = sum(len(p.get("items", [])) for p in platforms)
    total_rss_items = sum(len(f.get("items", [])) for f in rss_feeds)
    total_items = total_platform_items + total_rss_items

    # Independent display area title (decide whether to add a front separator based on add_separator)
    section_header = ""
    if add_separator and current_batch_has_content:
        # Need to add separator
        if format_type == "feishu":
            section_header = f"\n{feishu_separator}\n\n📋 **Independent display area** (Tổng {total_items} tin)\n\n"
        elif format_type == "dingtalk":
            section_header = f"\n---\n\n📋 **Independent display area** (Tổng {total_items} tin)\n\n"
        elif format_type in ("wework", "bark"):
            section_header = f"\n\n\n\n📋 **Independent display area** (Tổng {total_items} tin)\n\n"
        elif format_type == "telegram":
            section_header = f"\n\n📋 Independent display area (Tổng {total_items} tin)\n\n"
        elif format_type == "slack":
            section_header = f"\n\n📋 *Independent display area* (Tổng {total_items} tin)\n\n"
        else:
            section_header = f"\n\n📋 **Independent display area** (Tổng {total_items} tin)\n\n"
    else:
        # No separator needed (first area)
        if format_type == "feishu":
            section_header = f"📋 **Independent display area** (Tổng {total_items} tin)\n\n"
        elif format_type == "dingtalk":
            section_header = f"📋 **Independent display area** (Tổng {total_items} tin)\n\n"
        elif format_type == "telegram":
            section_header = f"📋 Independent display area (Tổng {total_items} tin)\n\n"
        elif format_type == "slack":
            section_header = f"📋 *Independent display area* (Tổng {total_items} tin)\n\n"
        else:
            section_header = f"📋 **Independent display area** (Tổng {total_items} tin)\n\n"

    # Add block title
    test_content = current_batch + section_header
    if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) < max_bytes:
        current_batch = test_content
        current_batch_has_content = True
    else:
        if current_batch_has_content:
            _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
        current_batch = _safe_new_batch(
            base_header + section_header, base_footer, max_bytes, base_header, batches
        )
        current_batch_has_content = True

    # Process Tin Hot platform
    for platform in platforms:
        platform_name = platform.get("name", platform.get("id", ""))
        items = platform.get("items", [])
        if not items:
            continue

        # Platform title
        platform_header = ""
        if format_type in ("wework", "bark"):
            platform_header = f"**{platform_name}** ({len(items)} tin):\n\n"
        elif format_type == "telegram":
            platform_header = f"{platform_name} ({len(items)} tin):\n\n"
        elif format_type == "ntfy":
            platform_header = f"**{platform_name}** ({len(items)} tin):\n\n"
        elif format_type == "feishu":
            platform_header = f"**{platform_name}** ({len(items)} tin):\n\n"
        elif format_type == "dingtalk":
            platform_header = f"**{platform_name}** ({len(items)} tin):\n\n"
        elif format_type == "slack":
            platform_header = f"*{platform_name}* ({len(items)} tin):\n\n"

        # Build first tin news
        first_item_line = ""
        if items:
            first_item_line = _format_standalone_platform_item(items[0], 1, format_type, rank_threshold)

        # Atomicity check
        platform_with_first = platform_header + first_item_line
        test_content = current_batch + platform_with_first

        if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) >= max_bytes:
            if current_batch_has_content:
                _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
            current_batch = _safe_new_batch(
                base_header + section_header + platform_with_first,
                base_footer, max_bytes, base_header, batches
            )
            current_batch_has_content = True
            start_index = 1
        else:
            current_batch = test_content
            current_batch_has_content = True
            start_index = 1

        # Process remaining tin items
        for j in range(start_index, len(items)):
            item_line = _format_standalone_platform_item(items[j], j + 1, format_type, rank_threshold)

            test_content = current_batch + item_line
            if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) >= max_bytes:
                if current_batch_has_content:
                    _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                current_batch = _safe_new_batch(
                    base_header + section_header + platform_header + item_line,
                    base_footer, max_bytes, base_header, batches
                )
                current_batch_has_content = True
            else:
                current_batch = test_content
                current_batch_has_content = True

        current_batch += "\n"

    # Process RSS source
    for feed in rss_feeds:
        feed_name = feed.get("name", feed.get("id", ""))
        items = feed.get("items", [])
        if not items:
            continue

        # RSS source title
        feed_header = ""
        if format_type in ("wework", "bark"):
            feed_header = f"**{feed_name}** ({len(items)} tin):\n\n"
        elif format_type == "telegram":
            feed_header = f"{feed_name} ({len(items)} tin):\n\n"
        elif format_type == "ntfy":
            feed_header = f"**{feed_name}** ({len(items)} tin):\n\n"
        elif format_type == "feishu":
            feed_header = f"**{feed_name}** ({len(items)} tin):\n\n"
        elif format_type == "dingtalk":
            feed_header = f"**{feed_name}** ({len(items)} tin):\n\n"
        elif format_type == "slack":
            feed_header = f"*{feed_name}* ({len(items)} tin):\n\n"

        # Build first tin RSS
        first_item_line = ""
        if items:
            first_item_line = _format_standalone_rss_item(items[0], 1, format_type, timezone)

        # Atomicity check
        feed_with_first = feed_header + first_item_line
        test_content = current_batch + feed_with_first

        if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) >= max_bytes:
            if current_batch_has_content:
                _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
            current_batch = _safe_new_batch(
                base_header + section_header + feed_with_first,
                base_footer, max_bytes, base_header, batches
            )
            current_batch_has_content = True
            start_index = 1
        else:
            current_batch = test_content
            current_batch_has_content = True
            start_index = 1

        # Process remaining tin items
        for j in range(start_index, len(items)):
            item_line = _format_standalone_rss_item(items[j], j + 1, format_type, timezone)

            test_content = current_batch + item_line
            if len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8")) >= max_bytes:
                if current_batch_has_content:
                    _safe_append_batch(batches, current_batch, base_footer, max_bytes, base_header)
                current_batch = _safe_new_batch(
                    base_header + section_header + feed_header + item_line,
                    base_footer, max_bytes, base_header, batches
                )
                current_batch_has_content = True
            else:
                current_batch = test_content
                current_batch_has_content = True

        current_batch += "\n"

    return current_batch, current_batch_has_content, batches


def _format_standalone_platform_item(item: Dict, index: int, format_type: str, rank_threshold: int = 10) -> str:
    """Format Tin Hot tin items in the independent display area (reuse Thống kê từ khóa hot area style)

    Args:
        item: Tin Hot tin item, including title, url, rank, ranks, first_time, last_time, count
        index: Index
        format_type: format type
        rank_threshold: rank highlight threshold

    Returns:
        Formatted tin item line string
    """
    title = item.get("title", "")
    url = item.get("url", "") or item.get("mobileUrl", "")
    ranks = item.get("ranks", [])
    rank = item.get("rank", 0)
    first_time = item.get("first_time", "")
    last_time = item.get("last_time", "")
    count = item.get("count", 1)

    # Use format_rank_display to format rank (reuse Thống kê từ khóa hot area logic)
    # If there is no ranks list, construct using a single rank
    if not ranks and rank > 0:
        ranks = [rank]
    rank_timeline = item.get("rank_timeline")
    rank_display = format_rank_display(ranks, rank_threshold, format_type, rank_timeline=rank_timeline) if ranks else ""

    # Build time display (use ~ to connect range, consistent with Thống kê từ khóa hot area)
    # Convert HH-MM format to HH:MM format
    time_display = ""
    if first_time and last_time and first_time != last_time:
        first_time_display = convert_time_for_display(first_time)
        last_time_display = convert_time_for_display(last_time)
        time_display = f"{first_time_display}~{last_time_display}"
    elif first_time:
        time_display = convert_time_for_display(first_time)

    # Build count display (format is (N times), consistent with Thống kê từ khóa hot area)
    count_display = f"({count} times)" if count > 1 else ""

    # Build tin item line according to format type (reuse Thống kê từ khóa hot area style)
    if format_type == "feishu":
        if url:
            item_line = f"  {index}. [{title}]({url})"
        else:
            item_line = f"  {index}. {title}"
        if rank_display:
            item_line += f" {rank_display}"
        if time_display:
            item_line += f" <font color='grey'>- {time_display}</font>"
        if count_display:
            item_line += f" <font color='green'>{count_display}</font>"

    elif format_type == "dingtalk":
        if url:
            item_line = f"  {index}. [{title}]({url})"
        else:
            item_line = f"  {index}. {title}"
        if rank_display:
            item_line += f" {rank_display}"
        if time_display:
            item_line += f" - {time_display}"
        if count_display:
            item_line += f" {count_display}"

    elif format_type == "telegram":
        if url:
            item_line = f"  {index}. {title} ({url})"
        else:
            item_line = f"  {index}. {title}"
        if rank_display:
            item_line += f" {rank_display}"
        if time_display:
            item_line += f" - {time_display}"
        if count_display:
            item_line += f" {count_display}"

    elif format_type == "slack":
        if url:
            item_line = f"  {index}. <{url}|{title}>"
        else:
            item_line = f"  {index}. {title}"
        if rank_display:
            item_line += f" {rank_display}"
        if time_display:
            item_line += f" _{time_display}_"
        if count_display:
            item_line += f" {count_display}"

    else:
        # wework, bark, ntfy
        if url:
            item_line = f"  {index}. [{title}]({url})"
        else:
            item_line = f"  {index}. {title}"
        if rank_display:
            item_line += f" {rank_display}"
        if time_display:
            item_line += f" - {time_display}"
        if count_display:
            item_line += f" {count_display}"

    item_line += "\n"
    return item_line


def _format_standalone_rss_item(
    item: Dict, index: int, format_type: str, timezone: str = "Asia/Shanghai"
) -> str:
    """Format RSS tin item in the independent display area

    Args:
        item: RSS tin item, containing title, url, published_at, author
        index: index
        format_type: format type
        timezone: timezone name

    Returns:
        Formatted tin item line string
    """
    title = item.get("title", "")
    url = item.get("url", "")
    published_at = item.get("published_at", "")
    author = item.get("author", "")

    # Use friendly time format
    friendly_time = ""
    if published_at:
        friendly_time = format_iso_time_friendly(published_at, timezone, include_date=True)

    # Build meta information
    meta_parts = []
    if friendly_time:
        meta_parts.append(friendly_time)
    if author:
        meta_parts.append(author)
    meta_str = ", ".join(meta_parts)

    # Build tin item line according to format type
    if format_type == "feishu":
        if url:
            item_line = f"  {index}. [{title}]({url})"
        else:
            item_line = f"  {index}. {title}"
        if meta_str:
            item_line += f" <font color='grey'>- {meta_str}</font>"
    elif format_type == "telegram":
        if url:
            item_line = f"  {index}. {title} ({url})"
        else:
            item_line = f"  {index}. {title}"
        if meta_str:
            item_line += f" - {meta_str}"
    elif format_type == "slack":
        if url:
            item_line = f"  {index}. <{url}|{title}>"
        else:
            item_line = f"  {index}. {title}"
        if meta_str:
            item_line += f" _{meta_str}_"
    else:
        # wework, bark, ntfy, dingtalk
        if url:
            item_line = f"  {index}. [{title}]({url})"
        else:
            item_line = f"  {index}. {title}"
        if meta_str:
            item_line += f" `{meta_str}`"

    item_line += "\n"
    return item_line
