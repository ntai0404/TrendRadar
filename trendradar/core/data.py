# coding=utf-8
"""
Data processing module

Provides data reading and detection functions:
- read_all_today_titles: Read all titles of the day from the storage backend
- detect_latest_new_titles: Detect the latest batch of new titles

Author: TrendRadar Team
"""

from typing import Dict, List, Tuple, Optional


def read_all_today_titles_from_storage(
    storage_manager,
    current_platform_ids: Optional[List[str]] = None,
) -> Tuple[Dict, Dict, Dict]:
    """
    Read all headers for the current day (SQLite data) from storage backend

    Args:
        storage_manager: storage manager instance
        current_platform_ids: list of currently monitored platform IDs (for filtering)

    Returns:
        Tuple[Dict, Dict, Dict]: (all_results, id_to_name, title_info)
    """
    try:
        news_data = storage_manager.get_today_all_data()

        if not news_data or not news_data.items:
            return {}, {}, {}

        all_results = {}
        final_id_to_name = {}
        title_info = {}

        for source_id, news_list in news_data.items.items():
            # Filter by platform
            if current_platform_ids is not None and source_id not in current_platform_ids:
                continue

            # Get the source name
            source_name = news_data.id_to_name.get(source_id, source_id)
            final_id_to_name[source_id] = source_name

            if source_id not in all_results:
                all_results[source_id] = {}
                title_info[source_id] = {}

            for item in news_list:
                title = item.title
                ranks = item.ranks or [item.rank]
                first_time = item.first_time or item.crawl_time
                last_time = item.last_time or item.crawl_time
                count = item.count
                rank_timeline = item.rank_timeline

                all_results[source_id][title] = {
                    "ranks": ranks,
                    "url": item.url or "",
                    "mobileUrl": item.mobile_url or "",
                }

                title_info[source_id][title] = {
                    "first_time": first_time,
                    "last_time": last_time,
                    "count": count,
                    "ranks": ranks,
                    "url": item.url or "",
                    "mobileUrl": item.mobile_url or "",
                    "rank_timeline": rank_timeline,
                }

        return all_results, final_id_to_name, title_info

    except Exception as e:
        print(f"[Storage] Failed to read data from storage backend: {e}")
        return {}, {}, {}


def read_all_today_titles(
    storage_manager,
    current_platform_ids: Optional[List[str]] = None,
    quiet: bool = False,
) -> Tuple[Dict, Dict, Dict]:
    """
    Read all titles for the current day (from storage backend)

    Args:
        storage_manager: storage manager instance
        current_platform_ids: list of currently monitored platform IDs (for filtering)
        quiet: Whether to use quiet mode (no log printing)

    Returns:
        Tuple[Dict, Dict, Dict]: (all_results, id_to_name, title_info)
    """
    all_results, final_id_to_name, title_info = read_all_today_titles_from_storage(
        storage_manager, current_platform_ids
    )

    if not quiet:
        if all_results:
            total_count = sum(len(titles) for titles in all_results.values())
            print(f"[Storage] has read {total_count} titles from the storage backend")
        else:
            print("[Storage] No data for the day")

    return all_results, final_id_to_name, title_info


def detect_latest_new_titles_from_storage(
    storage_manager,
    current_platform_ids: Optional[List[str]] = None,
) -> Dict:
    """
    Detect the latest batch of newly added titles from the storage backend

    Args:
        storage_manager: storage manager instance
        current_platform_ids: list of currently monitored platform IDs (for filtering)

    Returns:
        Dict: Add new title {source_id: {title: title_data}}
    """
    try:
        # Get the latest crawled data
        latest_data = storage_manager.get_latest_crawl_data()
        if not latest_data or not latest_data.items:
            return {}

        # Get all historical data
        all_data = storage_manager.get_today_all_data()
        if not all_data or not all_data.items:
            # There is no historical data (first crawl), there should be no "New" title
            return {}

        # Get the latest batch time
        latest_time = latest_data.crawl_time

        # Step 1: Collect the latest batch of titles (titles with last_crawl_time = latest_time)
        latest_titles = {}
        for source_id, news_list in latest_data.items.items():
            if current_platform_ids is not None and source_id not in current_platform_ids:
                continue
            latest_titles[source_id] = {}
            for item in news_list:
                latest_titles[source_id][item.title] = {
                    "ranks": [item.rank],
                    "url": item.url or "",
                    "mobileUrl": item.mobile_url or "",
                }

        # Step 2: Collect historical titles
        #Key logic: A title is a historical title as long as its first_crawl_time < latest_time
        # In this way, even if there are multiple records of the same title (with different URLs), as long as any one is historical, the title is considered historical.
        historical_titles = {}
        for source_id, news_list in all_data.items.items():
            if current_platform_ids is not None and source_id not in current_platform_ids:
                continue

            historical_titles[source_id] = set()
            for item in news_list:
                first_time = item.first_time or item.crawl_time
                # If the first occurrence of the record is earlier than the latest batch, the title is a historical title
                if first_time < latest_time:
                    historical_titles[source_id].add(item.title)

        # Check if this is the first crawl of the day (without any historical titles)
        # If the historical title collections of all platforms are empty, it means there is only one crawl batch.
        # In this case, consider all latest batch headers as "newly added" (for first push in incremental mode)
        has_historical_data = any(len(titles) > 0 for titles in historical_titles.values())
        if not has_historical_data:
            # First crawl: return all latest titles as "new"
            return latest_titles

        # Step 3: Find out the new title = latest batch title - historical title
        new_titles = {}
        for source_id, source_latest_titles in latest_titles.items():
            historical_set = historical_titles.get(source_id, set())
            source_new_titles = {}

            for title, title_data in source_latest_titles.items():
                if title not in historical_set:
                    source_new_titles[title] = title_data

            if source_new_titles:
                new_titles[source_id] = source_new_titles

        return new_titles

    except Exception as e:
        print(f"[Storage] Failed to detect new title from storage backend: {e}")
        return {}


def detect_latest_new_titles(
    storage_manager,
    current_platform_ids: Optional[List[str]] = None,
    quiet: bool = False,
) -> Dict:
    """
    Detect the latest batch of new titles for the day (from the storage backend)

    Args:
        storage_manager: storage manager instance
        current_platform_ids: list of currently monitored platform IDs (for filtering)
        quiet: Whether to use quiet mode (no log printing)

    Returns:
        Dict: Add new title {source_id: {title: title_data}}
    """
    new_titles = detect_latest_new_titles_from_storage(storage_manager, current_platform_ids)
    if new_titles and not quiet:
        total_new = sum(len(titles) for titles in new_titles.values())
        print(f"[Storage] detected {total_new} new titles from the storage backend")
    return new_titles
