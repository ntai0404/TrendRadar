# coding=utf-8
"""
report generation module

Provides report data preparation and HTML generation capabilities:
- prepare_report_data: prepare report data
- generate_html_report: generate HTML report
"""

from pathlib import Path
from typing import Dict, List, Optional, Callable


def prepare_report_data(
    stats: List[Dict],
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
    rank_threshold: int = 3,
    matches_word_groups_func: Optional[Callable] = None,
    load_frequency_words_func: Optional[Callable] = None,
    show_new_section: bool = True,
) -> Dict:
    """
    Prepare reporting data

    Args:
        stats: list of statistical results
        failed_ids: list of failed IDs
        new_titles: add new titles
        id_to_name: ID to name mapping
        mode: reporting mode (daily/incremental/current)
        rank_threshold: ranking threshold
        matches_word_groups_func: word matching function
        load_frequency_words_func: Load frequency word function
        show_new_section: Whether to display new hotspot areas

    Returns:
        Dict: Prepared report data
    """
    processed_new_titles = []

    #Always filter new titles for counting (required for header statistics), but regional display is controlled by configuration
    filtered_new_titles = {}
    if new_titles and id_to_name:
        if matches_word_groups_func and load_frequency_words_func:
            word_groups, filter_words, global_filters = load_frequency_words_func()
            for source_id, titles_data in new_titles.items():
                filtered_titles = {}
                for title, title_data in titles_data.items():
                    if matches_word_groups_func(title, word_groups, filter_words, global_filters):
                        filtered_titles[title] = title_data
                if filtered_titles:
                    filtered_new_titles[source_id] = filtered_titles
        else:
            filtered_new_titles = new_titles

        original_new_count = sum(len(titles) for titles in new_titles.values()) if new_titles else 0
        filtered_new_count = sum(len(titles) for titles in filtered_new_titles.values()) if filtered_new_titles else 0
        if original_new_count > 0:
            print(f"After frequency word filtering: {filtered_new_count} new hotspot matches (original {original_new_count})")

    # Hide the new news area in incremental mode or when configuration is turned off (but counting is complete)
    hide_new_section = mode == "incremental" or not show_new_section

    if not hide_new_section and filtered_new_titles and id_to_name:
        for source_id, titles_data in filtered_new_titles.items():
            source_name = id_to_name.get(source_id, source_id)
            source_titles = []

            for title, title_data in titles_data.items():
                url = title_data.get("url", "")
                mobile_url = title_data.get("mobileUrl", "")
                ranks = title_data.get("ranks", [])

                processed_title = {
                    "title": title,
                    "source_name": source_name,
                    "time_display": "",
                    "count": 1,
                    "ranks": ranks,
                    "rank_threshold": rank_threshold,
                    "url": url,
                    "mobile_url": mobile_url,
                    "is_new": True,
                    "rank_timeline": title_data.get("rank_timeline", []),
                }
                source_titles.append(processed_title)

            if source_titles:
                processed_new_titles.append(
                    {
                        "source_id": source_id,
                        "source_name": source_name,
                        "titles": source_titles,
                    }
                )

    processed_stats = []
    for stat in stats:
        if stat["count"] <= 0:
            continue

        processed_titles = []
        for title_data in stat["titles"]:
            processed_title = {
                "title": title_data["title"],
                "source_name": title_data["source_name"],
                "time_display": title_data["time_display"],
                "count": title_data["count"],
                "ranks": title_data["ranks"],
                "rank_threshold": title_data["rank_threshold"],
                "url": title_data.get("url", ""),
                "mobile_url": title_data.get("mobileUrl", ""),
                "is_new": title_data.get("is_new", False),
                "rank_timeline": title_data.get("rank_timeline", []),
            }
            processed_titles.append(processed_title)

        processed_stats.append(
            {
                "word": stat["word"],
                "count": stat["count"],
                "percentage": stat.get("percentage", 0),
                "titles": processed_titles,
            }
        )

    # total_new_count is always calculated from filtered results (used for header statistics) and is not affected by hide_new_section
    total_new_count = sum(len(titles) for titles in filtered_new_titles.values())

    return {
        "stats": processed_stats,
        "new_titles": processed_new_titles,
        "failed_ids": failed_ids or [],
        "total_new_count": total_new_count,
    }


def generate_html_report(
    stats: List[Dict],
    total_titles: int,
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
    update_info: Optional[Dict] = None,
    rank_threshold: int = 3,
    output_dir: str = "output",
    date_folder: str = "",
    time_filename: str = "",
    render_html_func: Optional[Callable] = None,
    matches_word_groups_func: Optional[Callable] = None,
    load_frequency_words_func: Optional[Callable] = None,
    report_metadata: Optional[Dict] = None,
) -> str:
    """
    Generate HTML report

    Each time HTML is generated:
    1. Save the timestamp snapshot to output/html/date/time.html (history)
    2. Copy to output/html/latest/{mode}.html (latest report)
    3. Copy to output/index.html and root directory index.html (entry)

    Args:
        stats: list of statistical results
        total_titles: total number of titles
        failed_ids: list of failed IDs
        new_titles: add new titles
        id_to_name: ID to name mapping
        mode: reporting mode (daily/incremental/current)
        update_info: Cập nhật information
        rank_threshold: ranking threshold
        output_dir: output directory
        date_folder: date folder name
        time_filename: time file name
        render_html_func: HTML rendering function
        matches_word_groups_func: word matching function
        load_frequency_words_func: Load frequency word function

    Returns:
        str: generated HTML file path (time stamp snapshot path)
    """
    # Timestamp snapshot file name
    snapshot_filename = f"{time_filename}.html"

    # Build the output path (flattened structure: output/html/date/)
    snapshot_path = Path(output_dir) / "html" / date_folder
    snapshot_path.mkdir(parents=True, exist_ok=True)
    snapshot_file = str(snapshot_path / snapshot_filename)

    # Prepare report data
    report_data = prepare_report_data(
        stats,
        failed_ids,
        new_titles,
        id_to_name,
        mode,
        rank_threshold,
        matches_word_groups_func,
        load_frequency_words_func,
    )

    if report_metadata:
        _METADATA_KEYS = {
            "hotlist_total", "platform_total", "rss_matched_count",
            "rss_total_count", "rss_source_total", "rss_source_failed",
        }
        for key in _METADATA_KEYS:
            if key in report_metadata:
                report_data[key] = report_metadata[key]

    # Render HTML content
    if render_html_func:
        html_content = render_html_func(
            report_data, total_titles, mode, update_info
        )
    else:
        # Default simple HTML
        html_content = f"<html><body><h1>Report</h1><pre>{report_data}</pre></body></html>"

    # 1. Save timestamp snapshot (history)
    with open(snapshot_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 2. Copy to html/latest/{mode}.html (latest report)
    latest_dir = Path(output_dir) / "html" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_file = latest_dir / f"{mode}.html"
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 3. Copy to index.html (entry)
    # output/index.html (for Docker Volume mounting access)
    output_index = Path(output_dir) / "index.html"
    with open(output_index, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Root directory index.html (accessed by GitHub Pages)
    root_index = Path("index.html")
    with open(root_index, "w", encoding="utf-8") as f:
        f.write(html_content)

    return snapshot_file
