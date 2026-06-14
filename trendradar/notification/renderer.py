# coding=utf-8
"""
Notification content rendering module

Provide multi-platform notification content rendering function and generate formatted push messages
"""

from datetime import datetime
from typing import Dict, List, Optional, Callable

from trendradar.report.formatter import format_title_for_platform


#Default region order
DEFAULT_REGION_ORDER = ["hotlist", "rss", "new_items", "standalone", "ai_analysis"]


def render_feishu_content(
    report_data: Dict,
    update_info: Optional[Dict] = None,
    mode: str = "daily",
    separator: str = "---",
    region_order: Optional[List[str]] = None,
    get_time_func: Optional[Callable[[], datetime]] = None,
    rss_items: Optional[list] = None,
    show_new_section: bool = True,
) -> str:
    """Render Feishu notification content (supports hot list + RSS merging)

    Args:
        report_data: report data dictionary, including stats, new_titles, failed_ids, total_new_count
        update_info: version Cập nhật information (optional)
        mode: reporting mode ("daily", "incremental", "current")
        separator: content separator
        region_order: region display order list
        get_time_func: function to get the current time (optional, datetime.now() is used by default)
        rss_items: RSS item list (optional, used for merge push)
        show_new_section: Whether to display new hotspot areas

    Returns:
        Formatted Feishu message content
    """
    if region_order is None:
        region_order = DEFAULT_REGION_ORDER

    # Generate hot word statistics part
    stats_content = ""
    if report_data["stats"]:
        stats_content += "📊 **Hot word statistics**\n\n"

        total_count = len(report_data["stats"])

        for i, stat in enumerate(report_data["stats"]):
            word = stat["word"]
            count = stat["count"]

            sequence_display = f"<font color='grey'>[{i + 1}/{total_count}]</font>"

            if count >= 10:
                stats_content += f"🔥 {sequence_display} **{word}** : <font color='red'>{count}</font> items\n\n"
            elif count >= 5:
                stats_content += f"📈 {sequence_display} **{word}** : <font color='orange'>{count}</font> items\n\n"
            else:
                stats_content += f"📌 {sequence_display} **{word}** : {count} items\n\n"

            for j, title_data in enumerate(stat["titles"], 1):
                formatted_title = format_title_for_platform(
                    "feishu", title_data, show_source=True
                )
                stats_content += f"  {j}. {formatted_title}\n"

                if j < len(stat["titles"]):
                    stats_content += "\n"

            if i < len(report_data["stats"]) - 1:
                stats_content += f"\n{separator}\n\n"

    # Generate new news section
    new_titles_content = ""
    if show_new_section and report_data["new_titles"]:
        new_titles_content += (
            f"🆕 **New hot news this time** ({report_data['total_new_count']} in total)\n\n"
        )

        for source_data in report_data["new_titles"]:
            new_titles_content += (
                f"**{source_data['source_name']}** ({len(source_data['titles'])} items):\n"
            )

            for j, title_data in enumerate(source_data["titles"], 1):
                title_data_copy = title_data.copy()
                title_data_copy["is_new"] = False
                formatted_title = format_title_for_platform(
                    "feishu", title_data_copy, show_source=False
                )
                new_titles_content += f"  {j}. {formatted_title}\n"

            new_titles_content += "\n"

    # RSS content
    rss_content = ""
    if rss_items:
        rss_content = _render_rss_section_feishu(rss_items, separator)

    # Prepare content mapping for each region
    region_contents = {
        "hotlist": stats_content,
        "new_items": new_titles_content,
        "rss": rss_content,
    }

    # Assemble content in region_order order
    text_content = ""
    for region in region_order:
        content = region_contents.get(region, "")
        if content:
            if text_content:
                text_content += f"\n{separator}\n\n"
            text_content += content

    if not text_content:
        if mode == "incremental":
            mode_text = "There are no new matching hot words in incremental mode"
        elif mode == "current":
            mode_text = "There are no matching hot words in Bảng xếp hạng hiện tại mode"
        else:
            mode_text = "No matching hot words yet"
        text_content = f"📭 {mode_text}\n\n"

    if report_data["failed_ids"]:
        if text_content and "No match yet" not in text_content:
            text_content += f"\n{separator}\n\n"

        text_content += "⚠️ **Platform where data acquisition failed:**\n\n"
        for i, id_value in enumerate(report_data["failed_ids"], 1):
            text_content += f"  • <font color='red'>{id_value}</font>\n"

    # Get the current time
    now = get_time_func() if get_time_func else datetime.now()
    text_content += (
        f"\n\n<font color='grey'>Thời gian cập nhật: {now.strftime('%Y-%m-%d %H:%M:%S')}</font>"
    )

    if update_info:
        text_content += f"\n<font color='grey'>TrendRadar found new version {update_info['remote_version']}, current {update_info['current_version']}</font>"

    return text_content


def render_dingtalk_content(
    report_data: Dict,
    update_info: Optional[Dict] = None,
    mode: str = "daily",
    region_order: Optional[List[str]] = None,
    get_time_func: Optional[Callable[[], datetime]] = None,
    rss_items: Optional[list] = None,
    show_new_section: bool = True,
) -> str:
    """Render DingTalk notification content (supports hot list + RSS merging)

    Args:
        report_data: report data dictionary, including stats, new_titles, failed_ids, total_new_count
        update_info: version Cập nhật information (optional)
        mode: reporting mode ("daily", "incremental", "current")
        region_order: region display order list
        get_time_func: function to get the current time (optional, datetime.now() is used by default)
        rss_items: RSS item list (optional, used for merge push)
        show_new_section: Whether to display new hotspot areas

    Returns:
        Formatted DingTalk message content
    """
    if region_order is None:
        region_order = DEFAULT_REGION_ORDER

    total_titles = sum(
        len(stat["titles"]) for stat in report_data["stats"] if stat["count"] > 0
    )
    now = get_time_func() if get_time_func else datetime.now()

    #Header information is constructed uniformly by splitter and will not be repeated here.
    header_content = ""

    # Generate hot word statistics part
    stats_content = ""
    if report_data["stats"]:
        stats_content += "📊 **Hot word statistics**\n\n"

        total_count = len(report_data["stats"])

        for i, stat in enumerate(report_data["stats"]):
            word = stat["word"]
            count = stat["count"]

            sequence_display = f"[{i + 1}/{total_count}]"

            if count >= 10:
                stats_content += f"🔥 {sequence_display} **{word}** : **{count}** items\n\n"
            elif count >= 5:
                stats_content += f"📈 {sequence_display} **{word}** : **{count}** items\n\n"
            else:
                stats_content += f"📌 {sequence_display} **{word}** : {count} items\n\n"

            for j, title_data in enumerate(stat["titles"], 1):
                formatted_title = format_title_for_platform(
                    "dingtalk", title_data, show_source=True
                )
                stats_content += f"  {j}. {formatted_title}\n"

                if j < len(stat["titles"]):
                    stats_content += "\n"

            if i < len(report_data["stats"]) - 1:
                stats_content += "\n---\n\n"

    # Generate new news section
    new_titles_content = ""
    if show_new_section and report_data["new_titles"]:
        new_titles_content += (
            f"🆕 **New hot news this time** ({report_data['total_new_count']} in total)\n\n"
        )

        for source_data in report_data["new_titles"]:
            new_titles_content += f"**{source_data['source_name']}** ({len(source_data['titles'])} items):\n\n"

            for j, title_data in enumerate(source_data["titles"], 1):
                title_data_copy = title_data.copy()
                title_data_copy["is_new"] = False
                formatted_title = format_title_for_platform(
                    "dingtalk", title_data_copy, show_source=False
                )
                new_titles_content += f"  {j}. {formatted_title}\n"

            new_titles_content += "\n"

    # RSS content
    rss_content = ""
    if rss_items:
        rss_content = _render_rss_section_markdown(rss_items)

    # Prepare content mapping for each region
    region_contents = {
        "hotlist": stats_content,
        "new_items": new_titles_content,
        "rss": rss_content,
    }

    # Assemble content in region_order order
    text_content = header_content
    has_content = False
    for region in region_order:
        content = region_contents.get(region, "")
        if content:
            if has_content:
                text_content += "\n---\n\n"
            text_content += content
            has_content = True

    if not has_content:
        if mode == "incremental":
            mode_text = "There are no new matching hot words in incremental mode"
        elif mode == "current":
            mode_text = "There are no matching hot words in Bảng xếp hạng hiện tại mode"
        else:
            mode_text = "No matching hot words yet"
        text_content += f"📭 {mode_text}\n\n"

    if report_data["failed_ids"]:
        if "No match" not in text_content:
            text_content += "\n---\n\n"

        text_content += "⚠️ **Platform where data acquisition failed:**\n\n"
        for i, id_value in enumerate(report_data["failed_ids"], 1):
            text_content += f"  • **{id_value}**\n"

    text_content += f"\n\n> Thời gian cập nhật: {now.strftime('%Y-%m-%d %H:%M:%S')}"

    if update_info:
        text_content += f"\n> TrendRadar found new version **{update_info['remote_version']}**, current **{update_info['current_version']}**"

    return text_content



# === RSS content rendering helper function (for combined push) ===

def _render_rss_section_feishu(rss_items: list, separator: str = "---") -> str:
    """Render RSS content block (Feishu format, used for combined push)"""
    if not rss_items:
        return ""

    #Group by feed_id
    feeds_map: Dict[str, list] = {}
    for item in rss_items:
        feed_id = item.get("feed_id", "unknown")
        if feed_id not in feeds_map:
            feeds_map[feed_id] = []
        feeds_map[feed_id].append(item)

    text_content = f"📰 **RSS Subscribe Cập nhật** ({len(rss_items)} items in total)\n\n"

    for feed_id, items in feeds_map.items():
        feed_name = items[0].get("feed_name", feed_id) if items else feed_id

        text_content += f"**{feed_name}** ({len(items)} items)\n\n"

        for i, item in enumerate(items, 1):
            title = item.get("title", "")
            url = item.get("url", "")
            published_at = item.get("published_at", "")

            if url:
                text_content += f"  {i}. [{title}]({url})"
            else:
                text_content += f"  {i}. {title}"

            if published_at:
                text_content += f" <font color='grey'>- {published_at}</font>"

            text_content += "\n"

            if i < len(items):
                text_content += "\n"

        text_content += "\n"

    return text_content.rstrip("\n")


def _render_rss_section_markdown(rss_items: list) -> str:
    """Render RSS content block (general Markdown format, used for combined push)"""
    if not rss_items:
        return ""

    #Group by feed_id
    feeds_map: Dict[str, list] = {}
    for item in rss_items:
        feed_id = item.get("feed_id", "unknown")
        if feed_id not in feeds_map:
            feeds_map[feed_id] = []
        feeds_map[feed_id].append(item)

    text_content = f"📰 **RSS Subscribe Cập nhật** ({len(rss_items)} items in total)\n\n"

    for feed_id, items in feeds_map.items():
        feed_name = items[0].get("feed_name", feed_id) if items else feed_id

        text_content += f"**{feed_name}** ({len(items)} items)\n"

        for i, item in enumerate(items, 1):
            title = item.get("title", "")
            url = item.get("url", "")
            published_at = item.get("published_at", "")

            if url:
                text_content += f"  {i}. [{title}]({url})"
            else:
                text_content += f"  {i}. {title}"

            if published_at:
                text_content += f" `{published_at}`"

            text_content += "\n"

        text_content += "\n"

    return text_content.rstrip("\n")
