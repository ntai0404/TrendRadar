# coding=utf-8
"""
Statistical analysis module

Provide news statistics and analysis functions:
- calculate_news_weight: Calculate news weight
- format_time_display: Format time display
- count_word_frequency: Count word frequency
"""

from typing import Dict, List, Tuple, Optional, Callable

from trendradar.core.frequency import matches_word_groups, _word_matches
from trendradar.utils.time import DEFAULT_TIMEZONE


def calculate_news_weight(
    title_data: Dict,
    rank_threshold: int,
    weight_config: Dict,
) -> float:
    """
    Calculate news weight, used for sorting

    Args:
        title_data: Title data, including ranks and count
        rank_threshold: Rank threshold
        weight_config: Weight configuration {RANK_WEIGHT, FREQUENCY_WEIGHT, HOTNESS_WEIGHT}

    Returns:
        float: Calculated weight value
    """
    ranks = title_data.get("ranks", [])
    if not ranks:
        return 0.0

    count = title_data.get("count", len(ranks))

    # Single pass to calculate the sum of rank scores and the number of high ranks
    rank_score_sum = 0
    high_rank_count = 0
    for rank in ranks:
        rank_score_sum += 11 - min(rank, 10)
        if rank <= rank_threshold:
            high_rank_count += 1

    # Normalize to 0~100 (align dimensions with frequency_weight, hotness_weight)
    rank_weight = (rank_score_sum / len(ranks)) * 10

    # Frequency weight: min(number of occurrences, 10) × 10
    frequency_weight = min(count, 10) * 10

    # Hotness bonus: number of high ranks / total number of occurrences × 100
    hotness_ratio = high_rank_count / len(ranks)
    hotness_weight = hotness_ratio * 100

    total_weight = (
        rank_weight * weight_config["RANK_WEIGHT"]
        + frequency_weight * weight_config["FREQUENCY_WEIGHT"]
        + hotness_weight * weight_config["HOTNESS_WEIGHT"]
    )

    return total_weight


def format_time_display(
    first_time: str,
    last_time: str,
    convert_time_func: Callable[[str], str],
) -> str:
    """
    Format time display (convert HH-MM to HH:MM)

    Args:
        first_time: First appearance time
        last_time: Last appearance time
        convert_time_func: Time format conversion function

    Returns:
        str: Formatted time display string
    """
    if not first_time:
        return ""
    # Convert to display format
    first_display = convert_time_func(first_time)
    last_display = convert_time_func(last_time)
    if first_display == last_display or not last_display:
        return first_display
    else:
        return f"[{first_display} ~ {last_display}]"


def count_word_frequency(
    results: Dict,
    word_groups: List[Dict],
    filter_words: List[str],
    id_to_name: Dict,
    title_info: Optional[Dict] = None,
    rank_threshold: int = 3,
    new_titles: Optional[Dict] = None,
    mode: str = "daily",
    global_filters: Optional[List[str]] = None,
    weight_config: Optional[Dict] = None,
    max_news_per_keyword: int = 0,
    sort_by_position_first: bool = False,
    is_first_crawl_func: Optional[Callable[[], bool]] = None,
    convert_time_func: Optional[Callable[[str], str]] = None,
    quiet: bool = False,
) -> Tuple[List[Dict], int]:
    """
    Count word frequency, support required words, frequency words, filter words, global filter words, and mark new titles

    Args:
        results: Crawl results {source_id: {title: title_data}}
        word_groups: Word group configuration list
        filter_words: Filter word list
        id_to_name: Mapping from ID to name
        title_info: Title statistics information (optional)
        rank_threshold: Rank threshold
        new_titles: New titles (optional)
        mode: Report mode (daily/incremental/current)
        global_filters: Global filter words (optional)
        weight_config: Weight configuration
        max_news_per_keyword: Maximum display quantity per keyword
        sort_by_position_first: Whether to prioritize sorting by configuration position
        is_first_crawl_func: Function to detect if it is the first crawl of the day
        convert_time_func: Time format conversion function
        quiet: Whether in quiet mode (do not print logs)

    Returns:
        Tuple[List[Dict], int]: (List of statistical results, total number of titles)
    """
    # Default weight configuration
    if weight_config is None:
        weight_config = {
            "RANK_WEIGHT": 0.6,
            "FREQUENCY_WEIGHT": 0.3,
            "HOTNESS_WEIGHT": 0.1,
        }

    # Default time conversion function
    if convert_time_func is None:
        convert_time_func = lambda x: x

    # Default first crawl detection function
    if is_first_crawl_func is None:
        is_first_crawl_func = lambda: True

    # If no word groups are configured, create a virtual word group containing all news
    if not word_groups:
        print("Frequency word configuration is empty, all news will be displayed")
        word_groups = [{"required": [], "normal": [], "group_key": "All news"}]
        filter_words = []  # Clear filter words, display all news

    is_first_today = is_first_crawl_func()

    # Determine the data source to process and the new tag logic
    if mode == "incremental":
        if is_first_today:
            # Incremental mode + first time of the day: process all news, all marked as new
            results_to_process = results
            all_news_are_new = True
        else:
            # Incremental mode + not the first time of the day: only process new news
            results_to_process = new_titles if new_titles else {}
            all_news_are_new = True
    elif mode == "current":
        # current mode: only process news of the current time batch, but statistics come from all history
        if title_info:
            latest_time = None
            for source_titles in title_info.values():
                for title_data in source_titles.values():
                    last_time = title_data.get("last_time", "")
                    if last_time:
                        if latest_time is None or last_time > latest_time:
                            latest_time = last_time

            # Only process news where last_time equals the latest time
            if latest_time:
                results_to_process = {}
                for source_id, source_titles in results.items():
                    if source_id in title_info:
                        filtered_titles = {}
                        for title, title_data in source_titles.items():
                            if title in title_info[source_id]:
                                info = title_info[source_id][title]
                                if info.get("last_time") == latest_time:
                                    filtered_titles[title] = title_data
                        if filtered_titles:
                            results_to_process[source_id] = filtered_titles

                if not quiet:
                    print(
                        f"Bảng xếp hạng hiện tại mode: latest time {latest_time}, filtered out {sum(len(titles) for titles in results_to_process.values())} Bảng xếp hạng hiện tại news"
                    )
            else:
                results_to_process = results
        else:
            results_to_process = results
        all_news_are_new = False
    else:
        # Daily summary mode: process all news
        results_to_process = results
        all_news_are_new = False
        total_input_news = sum(len(titles) for titles in results.values())
        filter_status = (
            "Display all"
            if len(word_groups) == 1 and word_groups[0]["group_key"] == "All news"
            else "Frequency word filtering"
        )
        print(f"Daily summary mode: processed {total_input_news} news, mode: {filter_status}")

    word_stats = {}
    total_titles = 0
    processed_titles = {}
    matched_new_count = 0

    if title_info is None:
        title_info = {}
    if new_titles is None:
        new_titles = {}

    for group in word_groups:
        group_key = group["group_key"]
        word_stats[group_key] = {"count": 0, "titles": {}}

    for source_id, titles_data in results_to_process.items():
        total_titles += len(titles_data)

        if source_id not in processed_titles:
            processed_titles[source_id] = {}

        for title, title_data in titles_data.items():
            if title in processed_titles.get(source_id, {}):
                continue

            # Use unified matching logic
            matches_frequency_words = matches_word_groups(
                title, word_groups, filter_words, global_filters
            )

            if not matches_frequency_words:
                continue

            # If it is incremental mode or current mode first time, count the number of matched new news
            if (mode == "incremental" and all_news_are_new) or (
                mode == "current" and is_first_today
            ):
                matched_new_count += 1

            source_ranks = title_data.get("ranks", [])
            source_url = title_data.get("url", "")
            source_mobile_url = title_data.get("mobileUrl", "")

            # Find matching word groups (defensive conversion to ensure type safety)
            title_lower = str(title).lower() if not isinstance(title, str) else title.lower()
            for group in word_groups:
                required_words = group["required"]
                normal_words = group["normal"]

                # If it is "All news" mode, all titles match the first (only) word group
                if len(word_groups) == 1 and word_groups[0]["group_key"] == "All news":
                    group_key = group["group_key"]
                    word_stats[group_key]["count"] += 1
                    if source_id not in word_stats[group_key]["titles"]:
                        word_stats[group_key]["titles"][source_id] = []
                else:
                    # Original matching logic (supports regex syntax)
                    if required_words:
                        all_required_present = all(
                            _word_matches(req_item, title_lower)
                            for req_item in required_words
                        )
                        if not all_required_present:
                            continue

                    if normal_words:
                        any_normal_present = any(
                            _word_matches(normal_item, title_lower)
                            for normal_item in normal_words
                        )
                        if not any_normal_present:
                            continue

                    group_key = group["group_key"]
                    word_stats[group_key]["count"] += 1
                    if source_id not in word_stats[group_key]["titles"]:
                        word_stats[group_key]["titles"][source_id] = []

                first_time = ""
                last_time = ""
                count_info = 1
                ranks = source_ranks if source_ranks else []
                url = source_url
                mobile_url = source_mobile_url
                rank_timeline = []

                # For current mode, get complete data from historical statistics
                if (
                    mode == "current"
                    and title_info
                    and source_id in title_info
                    and title in title_info[source_id]
                ):
                    info = title_info[source_id][title]
                    first_time = info.get("first_time", "")
                    last_time = info.get("last_time", "")
                    count_info = info.get("count", 1)
                    if "ranks" in info and info["ranks"]:
                        ranks = info["ranks"]
                    url = info.get("url", source_url)
                    mobile_url = info.get("mobileUrl", source_mobile_url)
                    rank_timeline = info.get("rank_timeline", [])
                elif (
                    title_info
                    and source_id in title_info
                    and title in title_info[source_id]
                ):
                    info = title_info[source_id][title]
                    first_time = info.get("first_time", "")
                    last_time = info.get("last_time", "")
                    count_info = info.get("count", 1)
                    if "ranks" in info and info["ranks"]:
                        ranks = info["ranks"]
                    url = info.get("url", source_url)
                    mobile_url = info.get("mobileUrl", source_mobile_url)
                    rank_timeline = info.get("rank_timeline", [])

                if not ranks:
                    ranks = [99]

                time_display = format_time_display(first_time, last_time, convert_time_func)

                source_name = id_to_name.get(source_id, source_id)

                # Determine if it is new
                is_new = False
                if all_news_are_new:
                    # In incremental mode, all processed news are new, or all news from the first time of the day are new
                    is_new = True
                elif new_titles and source_id in new_titles:
                    # Check if it is in the new list
                    new_titles_for_source = new_titles[source_id]
                    is_new = title in new_titles_for_source

                word_stats[group_key]["titles"][source_id].append(
                    {
                        "title": title,
                        "source_name": source_name,
                        "first_time": first_time,
                        "last_time": last_time,
                        "time_display": time_display,
                        "count": count_info,
                        "ranks": ranks,
                        "rank_threshold": rank_threshold,
                        "url": url,
                        "mobileUrl": mobile_url,
                        "is_new": is_new,
                        "rank_timeline": rank_timeline,
                    }
                )

                if source_id not in processed_titles:
                    processed_titles[source_id] = {}
                processed_titles[source_id][title] = True

                break

    # Finally, print summary information uniformly
    if mode == "incremental":
        if is_first_today:
            total_input_news = sum(len(titles) for titles in results.values())
            filter_status = (
                "Display all"
                if len(word_groups) == 1 and word_groups[0]["group_key"] == "All news"
                else "Frequency word matching"
            )
            if not quiet:
                print(
                    f"Incremental mode: first crawl of the day, among {total_input_news} news there are {matched_new_count} {filter_status}"
                )
        else:
            if new_titles:
                total_new_count = sum(len(titles) for titles in new_titles.values())
                filter_status = (
                    "Display all"
                    if len(word_groups) == 1
                    and word_groups[0]["group_key"] == "All news"
                    else "Match frequency words"
                )
                if not quiet:
                    print(
                        f"Incremental mode: among {total_new_count} new news, there are {matched_new_count} {filter_status}"
                    )
                    if matched_new_count == 0 and len(word_groups) > 1:
                        print("Incremental mode: no new news matches frequency words, no notification will be sent")
            else:
                if not quiet:
                    print("Incremental mode: no new news detected")
    elif mode == "current":
        total_input_news = sum(len(titles) for titles in results_to_process.values())
        if is_first_today:
            filter_status = (
                "Display all"
                if len(word_groups) == 1 and word_groups[0]["group_key"] == "All news"
                else "Frequency word matching"
            )
            if not quiet:
                print(
                    f"Bảng xếp hạng hiện tại mode: first crawl of the day, among {total_input_news} Bảng xếp hạng hiện tại news there are {matched_new_count} {filter_status}"
                )
        else:
            matched_count = sum(stat["count"] for stat in word_stats.values())
            filter_status = (
                "Show all"
                if len(word_groups) == 1 and word_groups[0]["group_key"] == "All news"
                else "Frequency word matching"
            )
            if not quiet:
                print(
                    f"Bảng xếp hạng hiện tại mode: {total_input_news} items Bảng xếp hạng hiện tại news contains {matched_count} items {filter_status}"
                )

    stats = []
    # Create mapping of group_key to position, max quantity, and display name
    group_key_to_position = {
        group["group_key"]: idx for idx, group in enumerate(word_groups)
    }
    group_key_to_max_count = {
        group["group_key"]: group.get("max_count", 0) for group in word_groups
    }
    group_key_to_display_name = {
        group["group_key"]: group.get("display_name") for group in word_groups
    }

    for group_key, data in word_stats.items():
        all_titles = []
        for source_id, title_list in data["titles"].items():
            all_titles.extend(title_list)

        # Sort by weight
        sorted_titles = sorted(
            all_titles,
            key=lambda x: (
                -calculate_news_weight(x, rank_threshold, weight_config),
                min(x["ranks"]) if x["ranks"] else 999,
                -x["count"],
            ),
        )

        # Apply max display quantity limit (priority: individual config > global config)
        group_max_count = group_key_to_max_count.get(group_key, 0)
        if group_max_count == 0:
            # Use global config
            group_max_count = max_news_per_keyword

        if group_max_count > 0:
            sorted_titles = sorted_titles[:group_max_count]

        # Prefer display_name, otherwise use group_key
        display_word = group_key_to_display_name.get(group_key) or group_key

        stats.append(
            {
                "word": display_word,
                "count": data["count"],
                "position": group_key_to_position.get(group_key, 999),
                "titles": sorted_titles,
                "percentage": (
                    round(data["count"] / total_titles * 100, 2)
                    if total_titles > 0
                    else 0
                ),
            }
        )

    # Select sorting priority based on config
    if sort_by_position_first:
        # First by config position, then by number of hot items
        stats.sort(key=lambda x: (x["position"], -x["count"]))
    else:
        # First by number of hot items, then by config position (original logic)
        stats.sort(key=lambda x: (-x["count"], x["position"]))

    # Print matched news count after filtering
    matched_news_count = sum(len(stat["titles"]) for stat in stats if stat["count"] > 0)
    if not quiet and mode == "daily":
        print(f"Daily summary mode: processed {total_titles} news items, mode: frequency word filtering")
        print(f"After frequency word filtering: {matched_news_count} news items matched")

    return stats, total_titles


def count_rss_frequency(
    rss_items: List[Dict],
    word_groups: List[Dict],
    filter_words: List[str],
    global_filters: Optional[List[str]] = None,
    new_items: Optional[List[Dict]] = None,
    max_news_per_keyword: int = 0,
    sort_by_position_first: bool = False,
    timezone: str = DEFAULT_TIMEZONE,
    rank_threshold: int = 5,
    quiet: bool = False,
) -> Tuple[List[Dict], int]:
    """
    Group and count RSS items by keyword (consistent with hotlist stats format)

    Args:
        rss_items: RSS item list, each item contains:
            - title: Title
            - feed_id: RSS feed ID
            - feed_name: RSS feed name
            - url: Article link
            - published_at: Publish time (ISO format)
        word_groups: Word group config list
        filter_words: Filter word list
        global_filters: Global filter words (optional)
        new_items: New item list (optional, used to mark is_new)
        max_news_per_keyword: Max display quantity per keyword
        sort_by_position_first: Whether to prioritize sorting by config position
        timezone: Timezone name (used for time formatting)
        quiet: Whether in quiet mode

    Returns:
        Tuple[List[Dict], int]: (Stats result list, total item count)
        Stats result format is consistent with hotlist:
        [
            {
                "word": "Keyword",
                "count": 5,
                "position": 0,
                "titles": [
                    {
                        "title": "Title",
                        "source_name": "Hacker News",
                        "time_display": "12-29 08:20",
                        "count": 1,
                        "ranks": [1],  # RSS uses publish time order as ranking
                        "rank_threshold": 50,
                        "url": "...",
                        "mobile_url": "",
                        "is_new": True/False
                    }
                ],
                "percentage": 10.0
            }
        ]
    """
    from trendradar.utils.time import format_iso_time_friendly

    if not rss_items:
        return [], 0

    # If no word group is configured, create a virtual word group containing all items
    if not word_groups:
        if not quiet:
            print("[RSS] Frequency word config is empty, will display all RSS items")
        word_groups = [{"required": [], "normal": [], "group_key": "All RSS"}]
        filter_words = []

    # Create URL set of new items for quick lookup
    new_urls = set()
    if new_items:
        for item in new_items:
            if item.get("url"):
                new_urls.add(item["url"])

    # Initialize word group stats
    word_stats = {}
    for group in word_groups:
        group_key = group["group_key"]
        word_stats[group_key] = {"count": 0, "titles": []}

    total_items = len(rss_items)
    processed_urls = set()  # Used for deduplication

    # Assign a "rank" to each item based on publish time
    # Sort by publish time, newest first
    sorted_items = sorted(
        rss_items,
        key=lambda x: x.get("published_at", ""),
        reverse=True
    )
    url_to_rank = {item.get("url", ""): idx + 1 for idx, item in enumerate(sorted_items)}

    for item in rss_items:
        title = item.get("title", "")
        url = item.get("url", "")

        # Deduplicate
        if url and url in processed_urls:
            continue
        if url:
            processed_urls.add(url)

        # Use unified matching logic
        if not matches_word_groups(title, word_groups, filter_words, global_filters):
            continue

        # Find matching word groups
        title_lower = title.lower()
        for group in word_groups:
            required_words = group["required"]
            normal_words = group["normal"]
            group_key = group["group_key"]

            # "All RSS" mode: all items match
            if len(word_groups) == 1 and word_groups[0]["group_key"] == "All RSS":
                matched = True
            else:
                # Check required words (supports regex syntax)
                if required_words:
                    all_required_present = all(
                        _word_matches(req_item, title_lower)
                        for req_item in required_words
                    )
                    if not all_required_present:
                        continue

                # Check normal words (supports regex syntax)
                if normal_words:
                    any_normal_present = any(
                        _word_matches(normal_item, title_lower)
                        for normal_item in normal_words
                    )
                    if not any_normal_present:
                        continue

                matched = True

            if matched:
                word_stats[group_key]["count"] += 1

                # Format time display
                published_at = item.get("published_at", "")
                time_display = format_iso_time_friendly(published_at, timezone, include_date=True) if published_at else ""

                # Determine if it is newly added
                is_new = url in new_urls if url else False

                # Get rank (based on publish time order)
                rank = url_to_rank.get(url, 99) if url else 99

                title_data = {
                    "title": title,
                    "source_name": item.get("feed_name", item.get("feed_id", "RSS")),
                    "time_display": time_display,
                    "count": 1,  # RSS items usually appear only once
                    "ranks": [rank],
                    "rank_threshold": rank_threshold,
                    "url": url,
                    "mobile_url": "",
                    "is_new": is_new,
                }
                word_stats[group_key]["titles"].append(title_data)
                break  # An item only matches the first word group

    # Build statistical results
    stats = []
    group_key_to_position = {
        group["group_key"]: idx for idx, group in enumerate(word_groups)
    }
    group_key_to_max_count = {
        group["group_key"]: group.get("max_count", 0) for group in word_groups
    }
    group_key_to_display_name = {
        group["group_key"]: group.get("display_name") for group in word_groups
    }

    for group_key, data in word_stats.items():
        if data["count"] == 0:
            continue

        # Sort by publish time (newest first)
        sorted_titles = sorted(
            data["titles"],
            key=lambda x: x["ranks"][0] if x["ranks"] else 999
        )

        # Apply maximum display quantity limit
        group_max_count = group_key_to_max_count.get(group_key, 0)
        if group_max_count == 0:
            group_max_count = max_news_per_keyword
        if group_max_count > 0:
            sorted_titles = sorted_titles[:group_max_count]

        # Prefer display_name, otherwise use group_key
        display_word = group_key_to_display_name.get(group_key) or group_key

        stats.append({
            "word": display_word,
            "count": data["count"],
            "position": group_key_to_position.get(group_key, 999),
            "titles": sorted_titles,
            "percentage": round(data["count"] / total_items * 100, 2) if total_items > 0 else 0,
        })

    # Sort
    if sort_by_position_first:
        stats.sort(key=lambda x: (x["position"], -x["count"]))
    else:
        stats.sort(key=lambda x: (-x["count"], x["position"]))

    matched_count = sum(stat["count"] for stat in stats)
    if not quiet:
        print(f"[RSS] Keyword group statistics: {matched_count}/{total_items} items matched")

    return stats, total_items


def convert_keyword_stats_to_platform_stats(
    keyword_stats: List[Dict],
    weight_config: Dict,
    rank_threshold: int = 5,
) -> List[Dict]:
    """
    Convert statistics grouped by keyword to statistics grouped by platform

    Args:
        keyword_stats: Original statistics grouped by keyword
        weight_config: Weight configuration
        rank_threshold: Rank threshold

    Returns:
        Statistics grouped by platform, format is consistent with original stats
    """
    # 1. Collect all news, group by platform
    platform_map: Dict[str, List[Dict]] = {}

    for stat in keyword_stats:
        keyword = stat["word"]
        for title_data in stat["titles"]:
            source_name = title_data["source_name"]

            if source_name not in platform_map:
                platform_map[source_name] = []

            # Copy title_data and add matched keywords
            title_with_keyword = title_data.copy()
            title_with_keyword["matched_keyword"] = keyword
            platform_map[source_name].append(title_with_keyword)

    # 2. Deduplicate (keep only one item for the same title under the same platform, keep the first matched keyword)
    for source_name, titles in platform_map.items():
        seen_titles: Dict[str, bool] = {}
        unique_titles = []
        for title_data in titles:
            title_text = title_data["title"]
            if title_text not in seen_titles:
                seen_titles[title_text] = True
                unique_titles.append(title_data)
        platform_map[source_name] = unique_titles

    # 3. Sort news within each platform by weight
    for source_name, titles in platform_map.items():
        platform_map[source_name] = sorted(
            titles,
            key=lambda x: (
                -calculate_news_weight(x, rank_threshold, weight_config),
                min(x["ranks"]) if x["ranks"] else 999,
                -x["count"],
            ),
        )

    # 4. Build platform statistical results
    platform_stats = []
    for source_name, titles in platform_map.items():
        platform_stats.append({
            "word": source_name,  # Platform name as grouping identifier
            "count": len(titles),
            "titles": titles,
            "percentage": 0,  # Can be calculated later
        })

    # 5. Sort platforms by number of news items
    platform_stats.sort(key=lambda x: -x["count"])

    return platform_stats
