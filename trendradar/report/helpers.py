# coding=utf-8
"""
Report helper module

Provides general auxiliary functions related to report generation
"""

import re
from typing import Dict, List, Optional


def clean_title(title: str) -> str:
    """Clean special characters in titles

    Cleanup rules:
    - Replace newlines (\n, \r) with spaces
    - Combine multiple consecutive whitespace characters into a single space
    - Remove leading and trailing whitespace

    Args:
        title: original title string

    Returns:
        Cleaned title string
    """
    if not isinstance(title, str):
        title = str(title)
    cleaned_title = title.replace("\n", " ").replace("\r", " ")
    cleaned_title = re.sub(r"\s+", " ", cleaned_title)
    cleaned_title = cleaned_title.strip()
    return cleaned_title


def html_escape(text: str) -> str:
    """HTML special character escaping

    Escape rules (in order):
    - & → &amp;
    - < → &lt;
    - > → &gt;
    - " → &quot;
    - ' → &#x27;

    Args:
        text: original text

    Returns:
        escaped text
    """
    if not isinstance(text, str):
        text = str(text)

    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def calculate_rank_trend(rank_timeline=None, ranks=None):
    """Calculate trend direction based on ranking timeline or ranking list

    Args:
        rank_timeline: List of ranking records in chronological order, such as [{"time": "10:00", "rank": 5}, ...]
        ranks: ranking list

    Returns:
        "up" (the ranking increases/the value becomes smaller), "down" (the ranking decreases/the value becomes larger), or None
    """
    prev_rank = None
    curr_rank = None

    if rank_timeline:
        valid_ranks = [r["rank"] for r in rank_timeline if r.get("rank") is not None]
        if len(valid_ranks) >= 2:
            prev_rank = valid_ranks[-2]
            curr_rank = valid_ranks[-1]
    elif ranks and len(ranks) >= 2:
        prev_rank = ranks[-2]
        curr_rank = ranks[-1]

    if prev_rank is not None and curr_rank is not None:
        if curr_rank < prev_rank:
            return "up"
        elif curr_rank > prev_rank:
            return "down"
    return None


def format_rank_display(
    ranks: List[int],
    rank_threshold: int,
    format_type: str,
    rank_timeline: Optional[List[Dict]] = None,
) -> str:
    """Format ranking display

    Generate ranking strings in corresponding formats according to different platform types.
    When the minimum ranking is less than or equal to the threshold, highlight format is used.

    Args:
        ranks: Ranking list (unique value after deduplication, used for range display)
        rank_threshold: Highlighting threshold, rankings less than or equal to this value will be highlighted.
        format_type: platform type, supports:
            - "html": HTML format
            - "feishu": Feishu format
            - "dingtalk": DingTalk format
            - "wework": Enterprise WeChat format
            - "telegram": Telegram format
            - "slack": Slack format
            - Others: Default markdown format
        rank_timeline: List of ranked records in chronological order (optional, used to calculate trends)

    Returns:
        Formatted ranking string, such as "[1]" or "[1 - 5]"
        If the ranking list is empty, returns an empty string
    """
    if not ranks:
        return ""

    unique_ranks = sorted(set(ranks))
    min_rank = unique_ranks[0]
    max_rank = unique_ranks[-1]

    #Select the highlighting format according to the platform type
    if format_type == "html":
        highlight_start = "<font color='red'><strong>"
        highlight_end = "</strong></font>"
    elif format_type == "feishu":
        highlight_start = "<font color='red'>**"
        highlight_end = "**</font>"
    elif format_type == "dingtalk":
        highlight_start = "**"
        highlight_end = "**"
    elif format_type == "wework":
        highlight_start = "**"
        highlight_end = "**"
    elif format_type == "telegram":
        highlight_start = "<b>"
        highlight_end = "</b>"
    elif format_type == "slack":
        highlight_start = "*"
        highlight_end = "*"
    else:
        #Default markdown format
        highlight_start = "**"
        highlight_end = "**"

    # Generate ranking display
    rank_str = ""
    if min_rank <= rank_threshold:
        if min_rank == max_rank:
            rank_str = f"{highlight_start}[{min_rank}]{highlight_end}"
        else:
            rank_str = f"{highlight_start}[{min_rank} - {max_rank}]{highlight_end}"
    else:
        if min_rank == max_rank:
            rank_str = f"[{min_rank}]"
        else:
            rank_str = f"[{min_rank} - {max_rank}]"

    trend = calculate_rank_trend(rank_timeline, ranks)
    trend_arrow = {"up": "📈", "down": "📉"}.get(trend, "")

    return f"{rank_str} {trend_arrow}" if trend_arrow else rank_str
