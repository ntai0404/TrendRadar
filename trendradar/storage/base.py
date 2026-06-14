# coding=utf-8
"""
Storage backend abstract base class and data model

Define a unified storage interface, all storage backends need to implement these methods
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set


@dataclass
class NewsItem:
    """News item data model (hot list data)"""

    title: str                          # News title
    source_id: str                      # Source platform ID (e.g., toutiao, baidu)
    source_name: str = ""               # Source platform name (used at runtime, not stored in database)
    rank: int = 0                       # Rank
    url: str = ""                       # Link URL
    mobile_url: str = ""                # Mobile URL
    crawl_time: str = ""                # Crawl time (HH:MM format)

    # Statistics (used for analysis)
    ranks: List[int] = field(default_factory=list)  # Historical rank list
    first_time: str = ""                # First appearance time
    last_time: str = ""                 # Last appearance time
    count: int = 1                      # Appearance count
    rank_timeline: List[Dict[str, Any]] = field(default_factory=list)  # Complete rank timeline
                                        # Format: [{"time": "09:30", "rank": 1}, {"time": "10:00", "rank": 2}, ...]
                                        # None indicates dropping off the list: [{"time": "11:00", "rank": None}]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "rank": self.rank,
            "url": self.url,
            "mobile_url": self.mobile_url,
            "crawl_time": self.crawl_time,
            "ranks": self.ranks,
            "first_time": self.first_time,
            "last_time": self.last_time,
            "count": self.count,
            "rank_timeline": self.rank_timeline,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsItem":
        """Create from dictionary"""
        return cls(
            title=data.get("title", ""),
            source_id=data.get("source_id", ""),
            source_name=data.get("source_name", ""),
            rank=data.get("rank", 0),
            url=data.get("url", ""),
            mobile_url=data.get("mobile_url", ""),
            crawl_time=data.get("crawl_time", ""),
            ranks=data.get("ranks", []),
            first_time=data.get("first_time", ""),
            last_time=data.get("last_time", ""),
            count=data.get("count", 1),
            rank_timeline=data.get("rank_timeline", []),
        )


@dataclass
class RSSItem:
    """RSS item data model"""

    title: str                          # Title
    feed_id: str                        # RSS feed ID (e.g., "hacker-news")
    feed_name: str = ""                 # RSS feed name (used at runtime)
    url: str = ""                       # Article link
    guid: str = ""                      # GUID/ID (RSS guid or Atom id)
    published_at: str = ""              # RSS publish time (ISO format)
    summary: str = ""                   # Summary/description
    author: str = ""                    # Author
    crawl_time: str = ""                # Crawl time (HH:MM format)

    # Statistics
    first_time: str = ""                # First crawl time
    last_time: str = ""                 # Last crawl time
    count: int = 1                      # Crawl count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "feed_id": self.feed_id,
            "feed_name": self.feed_name,
            "url": self.url,
            "published_at": self.published_at,
            "summary": self.summary,
            "author": self.author,
            "crawl_time": self.crawl_time,
            "first_time": self.first_time,
            "last_time": self.last_time,
            "count": self.count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RSSItem":
        """Create from dictionary"""
        return cls(
            title=data.get("title", ""),
            feed_id=data.get("feed_id", ""),
            feed_name=data.get("feed_name", ""),
            url=data.get("url", ""),
            published_at=data.get("published_at", ""),
            summary=data.get("summary", ""),
            author=data.get("author", ""),
            crawl_time=data.get("crawl_time", ""),
            first_time=data.get("first_time", ""),
            last_time=data.get("last_time", ""),
            count=data.get("count", 1),
        )


@dataclass
class RSSData:
    """
    RSS data collection

    Structure:
    - date: Date (YYYY-MM-DD)
    - crawl_time: Crawl time (HH:MM)
    - items: RSS items grouped by feed_id
    - id_to_name: Mapping from feed_id to name
    - failed_ids: List of failed feed_ids
    """

    date: str                                   # Date
    crawl_time: str                             # Crawl time
    items: Dict[str, List[RSSItem]]             # Items grouped by feed_id
    id_to_name: Dict[str, str] = field(default_factory=dict)   # ID to name mapping
    failed_ids: List[str] = field(default_factory=list)        # Failed IDs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        items_dict = {}
        for feed_id, rss_list in self.items.items():
            items_dict[feed_id] = [item.to_dict() for item in rss_list]

        return {
            "date": self.date,
            "crawl_time": self.crawl_time,
            "items": items_dict,
            "id_to_name": self.id_to_name,
            "failed_ids": self.failed_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RSSData":
        """Create from dictionary"""
        items = {}
        items_data = data.get("items", {})
        for feed_id, rss_list in items_data.items():
            items[feed_id] = [RSSItem.from_dict(item) for item in rss_list]

        return cls(
            date=data.get("date", ""),
            crawl_time=data.get("crawl_time", ""),
            items=items,
            id_to_name=data.get("id_to_name", {}),
            failed_ids=data.get("failed_ids", []),
        )

    def get_total_count(self) -> int:
        """Get total number of items"""
        return sum(len(rss_list) for rss_list in self.items.values())


@dataclass
class NewsData:
    """
    News data collection

    Structure:
    - date: Date (YYYY-MM-DD)
    - crawl_time: Crawl time (HH:MM)
    - items: News items grouped by source ID
    - id_to_name: Mapping from source ID to name
    - failed_ids: List of failed source IDs
    """

    date: str                                   # Date
    crawl_time: str                             # Crawl time
    items: Dict[str, List[NewsItem]]            # News grouped by source
    id_to_name: Dict[str, str] = field(default_factory=dict)   # ID to name mapping
    failed_ids: List[str] = field(default_factory=list)        # Failed IDs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        items_dict = {}
        for source_id, news_list in self.items.items():
            items_dict[source_id] = [item.to_dict() for item in news_list]

        return {
            "date": self.date,
            "crawl_time": self.crawl_time,
            "items": items_dict,
            "id_to_name": self.id_to_name,
            "failed_ids": self.failed_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsData":
        """Create from dictionary"""
        items = {}
        items_data = data.get("items", {})
        for source_id, news_list in items_data.items():
            items[source_id] = [NewsItem.from_dict(item) for item in news_list]

        return cls(
            date=data.get("date", ""),
            crawl_time=data.get("crawl_time", ""),
            items=items,
            id_to_name=data.get("id_to_name", {}),
            failed_ids=data.get("failed_ids", []),
        )

    def get_total_count(self) -> int:
        """Get total number of news items"""
        return sum(len(news_list) for news_list in self.items.values())

    def merge_with(self, other: "NewsData") -> "NewsData":
        """
        Merge another NewsData into current data

        Merge rules:
        - Merge ranking history for news with the same source_id + title
        - Cập nhật last_time and count
        - Keep the earlier first_time
        """
        merged_items = {}

        # Copy current data
        for source_id, news_list in self.items.items():
            merged_items[source_id] = {item.title: item for item in news_list}

        # Merge other data
        for source_id, news_list in other.items.items():
            if source_id not in merged_items:
                merged_items[source_id] = {}

            for item in news_list:
                if item.title in merged_items[source_id]:
                    # Merge existing news
                    existing = merged_items[source_id][item.title]

                    # Merge rankings
                    existing_ranks = set(existing.ranks) if existing.ranks else set()
                    new_ranks = set(item.ranks) if item.ranks else set()
                    merged_ranks = sorted(existing_ranks | new_ranks)
                    existing.ranks = merged_ranks

                    # Cập nhật time
                    if item.first_time and (not existing.first_time or item.first_time < existing.first_time):
                        existing.first_time = item.first_time
                    if item.last_time and (not existing.last_time or item.last_time > existing.last_time):
                        existing.last_time = item.last_time

                    # Cập nhật count
                    existing.count += 1

                    # Keep URL (if originally none)
                    if not existing.url and item.url:
                        existing.url = item.url
                    if not existing.mobile_url and item.mobile_url:
                        existing.mobile_url = item.mobile_url
                else:
                    # Add new news
                    merged_items[source_id][item.title] = item

        # Convert back to list format
        final_items = {}
        for source_id, items_dict in merged_items.items():
            final_items[source_id] = list(items_dict.values())

        # Merge id_to_name
        merged_id_to_name = {**self.id_to_name, **other.id_to_name}

        # Merge failed_ids (deduplicate)
        merged_failed_ids = list(set(self.failed_ids + other.failed_ids))

        return NewsData(
            date=self.date or other.date,
            crawl_time=other.crawl_time,  # Use the newer crawl time
            items=final_items,
            id_to_name=merged_id_to_name,
            failed_ids=merged_failed_ids,
        )


class StorageBackend(ABC):
    """
    Storage backend abstract base class

    All storage backends need to implement these methods to support:
    - Save news data
    - Read all data for the day
    - Detect new news
    - Generate report files (TXT/HTML)
    """

    @abstractmethod
    def save_news_data(self, data: NewsData) -> bool:
        """
        Save news data

        Args:
            data: News data

        Returns:
            Whether the save was successful
        """
        pass

    @abstractmethod
    def get_today_all_data(self, date: Optional[str] = None) -> Optional[NewsData]:
        """
        Get all news data for a specified date

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Merged news data, returns None if there is no data
        """
        pass

    @abstractmethod
    def get_latest_crawl_data(self, date: Optional[str] = None) -> Optional[NewsData]:
        """
        Get the latest crawled data

        Args:
            date: Date string, defaults to today

        Returns:
            Latest crawled news data
        """
        pass

    @abstractmethod
    def detect_new_titles(self, current_data: NewsData) -> Dict[str, Dict]:
        """
        Detect new titles

        Args:
            current_data: Currently crawled data

        Returns:
            New title data, format: {source_id: {title: title_data}}
        """
        pass

    @abstractmethod
    def save_txt_snapshot(self, data: NewsData) -> Optional[str]:
        """
        Save TXT snapshot (optional feature, available in local environment)

        Args:
            data: News data

        Returns:
            Saved file path, returns None if not supported
        """
        pass

    @abstractmethod
    def save_html_report(self, html_content: str, filename: str) -> Optional[str]:
        """
        Save HTML report

        Args:
            html_content: HTML content
            filename: File name

        Returns:
            Saved file path
        """
        pass

    @abstractmethod
    def is_first_crawl_today(self, date: Optional[str] = None) -> bool:
        """
        Check if it is the first crawl of the day

        Args:
            date: Date string, defaults to today

        Returns:
            Whether it is the first crawl
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up resources (e.g., temporary files, database connections, etc.)
        """
        pass

    @abstractmethod
    def cleanup_old_data(self, retention_days: int) -> int:
        """
        Clean up expired data

        Args:
            retention_days: Retention days (0 means no cleanup)

        Returns:
            Number of deleted date directories
        """
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """
        Storage backend name
        """
        pass

    @property
    @abstractmethod
    def supports_txt(self) -> bool:
        """
        Whether generating TXT snapshots is supported
        """
        pass

    # === Time period execution record (scheduling system) ===

    def has_period_executed(self, date_str: str, period_key: str, action: str) -> bool:
        """
        Check if a specific action in a specified time period has been executed

        Args:
            date_str: Date string YYYY-MM-DD
            period_key: time period key
            action: action type (analyze / push)

        Returns:
            Whether executed
        """
        return False

    def record_period_execution(self, date_str: str, period_key: str, action: str) -> bool:
        """
        Record action execution for the time period

        Args:
            date_str: date string YYYY-MM-DD
            period_key: time period key
            action: action type (analyze / push)

        Returns:
            Whether recorded successfully
        """
        return False

    # === AI intelligent filtering (default implementation, subclasses override via mixin) ===

    def begin_batch(self) -> None:
        """Enable batch mode (remote backend delays upload, local backend no operation)"""
        pass

    def end_batch(self) -> None:
        """End batch mode"""
        pass

    def get_active_ai_filter_tags(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> List[Dict]:
        return []

    def get_latest_prompt_hash(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> Optional[str]:
        return None

    def get_latest_ai_filter_tag_version(self, date: Optional[str] = None) -> int:
        return 0

    def deprecate_all_ai_filter_tags(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> int:
        return 0

    def save_ai_filter_tags(self, tags: List[Dict], version: int, prompt_hash: str, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> int:
        return 0

    def save_ai_filter_results(self, results: List[Dict], date: Optional[str] = None) -> int:
        return 0

    def get_active_ai_filter_results(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> List[Dict]:
        return []

    def deprecate_specific_ai_filter_tags(self, tag_ids: List[int], date: Optional[str] = None) -> int:
        return 0

    def update_ai_filter_tags_hash(self, interests_file: str, new_hash: str, date: Optional[str] = None) -> int:
        return 0

    def update_ai_filter_tag_descriptions(self, tag_updates: List[Dict], date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> int:
        return 0

    def update_ai_filter_tag_priorities(self, tag_priorities: List[Dict], date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> int:
        return 0

    def save_analyzed_news(self, news_ids: List[str], source_type: str, interests_file: str, prompt_hash: str, matched_ids: Set[str], date: Optional[str] = None) -> int:
        return 0

    def get_analyzed_news_ids(self, source_type: str = "hotlist", date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> Set[str]:
        return set()

    def clear_analyzed_news(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> int:
        return 0

    def clear_unmatched_analyzed_news(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> int:
        return 0

    def get_all_news_ids(self, date: Optional[str] = None) -> List[Dict]:
        return []

    def get_all_rss_ids(self, date: Optional[str] = None) -> List[Dict]:
        return []


def convert_crawl_results_to_news_data(
    results: Dict[str, Dict],
    id_to_name: Dict[str, str],
    failed_ids: List[str],
    crawl_time: str,
    crawl_date: str,
) -> NewsData:
    """
    Convert crawler results to NewsData format

    Args:
        results: results returned by crawler {source_id: {title: {ranks: [], url: "", mobileUrl: ""}}}
        id_to_name: mapping from source ID to name
        failed_ids: failed source IDs
        crawl_time: crawl time (HH:MM)
        crawl_date: crawl date (YYYY-MM-DD)

    Returns:
        NewsData object
    """
    items = {}

    for source_id, titles_data in results.items():
        source_name = id_to_name.get(source_id, source_id)
        news_list = []

        for title, data in titles_data.items():
            ranks = data.get("ranks", [])
            url = data.get("url", "")
            mobile_url = data.get("mobileUrl", "")

            rank = ranks[0] if ranks else 99

            news_item = NewsItem(
                title=title,
                source_id=source_id,
                source_name=source_name,
                rank=rank,
                url=url,
                mobile_url=mobile_url,
                crawl_time=crawl_time,
                ranks=ranks,
                first_time=crawl_time,
                last_time=crawl_time,
                count=1,
            )
            news_list.append(news_item)

        items[source_id] = news_list

    return NewsData(
        date=crawl_date,
        crawl_time=crawl_time,
        items=items,
        id_to_name=id_to_name,
        failed_ids=failed_ids,
    )
