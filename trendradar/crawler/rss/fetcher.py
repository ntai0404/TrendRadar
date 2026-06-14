# coding=utf-8
"""
RSS grabber

Responsible for fetching data from configured RSS feeds and converting them into standard formats
"""

import time
import random
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

import requests

from .parser import RSSParser
from trendradar.storage.base import RSSItem, RSSData
from trendradar.utils.time import get_configured_time, is_within_days, DEFAULT_TIMEZONE


@dataclass
class RSSFeedConfig:
    """RSS feed configuration"""
    id: str # Source ID
    name: str # display name
    url: str                    # RSS URL
    max_items: int = 0 # Maximum number of items (0=no limit)
    enabled: bool = True # Whether to enable
    max_age_days: Optional[int] = None # Maximum age of articles (days), overrides global settings; None=use global, 0=disable filtering


class RSSFetcher:
    """RSS Grabber"""

    def __init__(
        self,
        feeds: List[RSSFeedConfig],
        request_interval: int = 2000,
        timeout: int = 15,
        use_proxy: bool = False,
        proxy_url: str = "",
        timezone: str = DEFAULT_TIMEZONE,
        freshness_enabled: bool = True,
        default_max_age_days: int = 3,
    ):
        """
        Initialize the crawler

        Args:
            feeds: RSS feed configuration list
            request_interval: request interval (milliseconds)
            timeout: request timeout (seconds)
            use_proxy: whether to use a proxy
            proxy_url: proxy URL
            timezone: time zone configuration (such as 'Asia/Shanghai')
            freshness_enabled: Whether to enable freshness filtering
            default_max_age_days: Default maximum article age (days)
        """
        self.feeds = [f for f in feeds if f.enabled]
        self.request_interval = request_interval
        self.timeout = timeout
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        self.timezone = timezone
        self.freshness_enabled = freshness_enabled
        self.default_max_age_days = default_max_age_days

        self.parser = RSSParser()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create request session"""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "TrendRadar/2.0 RSS Reader (https://github.com/trendradar)",
            "Accept": "application/feed+json, application/json, application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })

        if self.use_proxy and self.proxy_url:
            session.proxies = {
                "http": self.proxy_url,
                "https": self.proxy_url,
            }

        return session

    def _filter_by_freshness(
        self,
        items: List[RSSItem],
        feed: RSSFeedConfig,
    ) -> Tuple[List[RSSItem], int]:
        """
        Filter articles based on freshness

        Args:
            items: list of articles to be filtered
            feed: RSS feed configuration

        Returns:
            (filtered article list, number of filtered articles)
        """
        # If disabled globally, return directly
        if not self.freshness_enabled:
            return items, 0

        # Determine max_age_days for this feed
        max_days = feed.max_age_days
        if max_days is None:
            max_days = self.default_max_age_days

        # If set to 0, disable filtering for this feed
        if max_days == 0:
            return items, 0

        #Filtering logic: retain articles without publishing time
        filtered = []
        for item in items:
            if not item.published_at:
                # No release time, reserved
                filtered.append(item)
            elif is_within_days(item.published_at, max_days, self.timezone):
                # Keep within the specified number of days
                filtered.append(item)
            # Otherwise filter out

        filtered_count = len(items) - len(filtered)
        return filtered, filtered_count

    def fetch_feed(self, feed: RSSFeedConfig) -> Tuple[List[RSSItem], Optional[str]]:
        """
        Fetch a single RSS feed

        Args:
            feed: RSS feed configuration

        Returns:
            (item list, error message) tuple
        """
        try:
            response = self.session.get(feed.url, timeout=self.timeout)
            response.raise_for_status()

            parsed_items = self.parser.parse(response.text, feed.url)

            # Limit the number of entries (0=no limit)
            if feed.max_items > 0:
                parsed_items = parsed_items[:feed.max_items]

            # Convert to RSSItem (using configured time zone)
            now = get_configured_time(self.timezone)
            crawl_time = now.strftime("%H:%M")
            items = []

            for parsed in parsed_items:
                item = RSSItem(
                    title=parsed.title,
                    feed_id=feed.id,
                    feed_name=feed.name,
                    url=parsed.url,
                    guid=parsed.guid or "",
                    published_at=parsed.published_at or "",
                    summary=parsed.summary or "",
                    author=parsed.author or "",
                    crawl_time=crawl_time,
                    first_time=crawl_time,
                    last_time=crawl_time,
                    count=1,
                )
                items.append(item)

            # Note: Freshness filtering has been moved to the push stage (_convert_rss_items_to_list)
            # In this way, all articles will be stored in the database, but old articles will not be pushed.
            print(f"[RSS] {feed.name}: Get {len(items)} items")
            return items, None

        except requests.Timeout:
            error = f"Request timeout ({self.timeout}s)"
            print(f"[RSS] {feed.name}: {error}")
            return [], error

        except requests.RequestException as e:
            error = f"Request failed: {e}"
            print(f"[RSS] {feed.name}: {error}")
            return [], error

        except ValueError as e:
            error = f"Parse failed: {e}"
            print(f"[RSS] {feed.name}: {error}")
            return [], error

        except Exception as e:
            error = f"Unknown error: {e}"
            print(f"[RSS] {feed.name}: {error}")
            return [], error

    def fetch_all(self) -> RSSData:
        """
        Crawl all RSS feeds

        Returns:
            RSSData object
        """
        all_items: Dict[str, List[RSSItem]] = {}
        id_to_name: Dict[str, str] = {}
        failed_ids: List[str] = []

        # Use configured time zone
        now = get_configured_time(self.timezone)
        crawl_time = now.strftime("%H:%M")
        crawl_date = now.strftime("%Y-%m-%d")

        print(f"[RSS] Start crawling {len(self.feeds)} RSS feeds...")

        for i, feed in enumerate(self.feeds):
            #Request interval (with random fluctuation)
            if i > 0:
                interval = self.request_interval / 1000
                jitter = random.uniform(-0.2, 0.2) * interval
                time.sleep(interval + jitter)

            items, error = self.fetch_feed(feed)

            id_to_name[feed.id] = feed.name

            if error:
                failed_ids.append(feed.id)
            else:
                all_items[feed.id] = items

        total_items = sum(len(items) for items in all_items.values())
        print(f"[RSS] Fetching completed: {len(all_items)} sources successfully, {len(failed_ids)} failed, total {total_items} items")

        return RSSData(
            date=crawl_date,
            crawl_time=crawl_time,
            items=all_items,
            id_to_name=id_to_name,
            failed_ids=failed_ids,
        )

    @classmethod
    def from_config(cls, config: Dict) -> "RSSFetcher":
        """
        Create a crawler from a configuration dictionary

        Args:
            config: Configuration dictionary, the format is as follows:
                {
                    "enabled": true,
                    "request_interval": 2000,
                    "freshness_filter": {
                        "enabled": true,
                        "max_age_days": 3
                    },
                    "feeds": [
                        {"id": "hacker-news", "name": "Hacker News", "url": "...", "max_age_days": 1}
                    ]
                }

        Returns:
            RSSFetcher instance
        """
        # Read freshness filtering configuration
        freshness_config = config.get("freshness_filter", {})
        freshness_enabled = freshness_config.get("enabled", True) # Enabled by default
        default_max_age_days = freshness_config.get("max_age_days", 3) # Default 3 days

        feeds = []
        for feed_config in config.get("feeds", []):
            # Read and verify max_age_days for a single feed (optional)
            max_age_days_raw = feed_config.get("max_age_days")
            max_age_days = None
            if max_age_days_raw is not None:
                try:
                    max_age_days = int(max_age_days_raw)
                    if max_age_days < 0:
                        feed_id = feed_config.get("id", "unknown")
                        print(f"[Warning] max_age_days for RSS feed '{feed_id}' is negative, global default will be used")
                        max_age_days = None
                except (ValueError, TypeError):
                    feed_id = feed_config.get("id", "unknown")
                    print(f"[Warning] Max_age_days format error for RSS feed '{feed_id}': {max_age_days_raw}")
                    max_age_days = None

            feed = RSSFeedConfig(
                id=feed_config.get("id", ""),
                name=feed_config.get("name", ""),
                url=feed_config.get("url", ""),
                max_items=feed_config.get("max_items", 0), # 0=No limit
                enabled=feed_config.get("enabled", True),
                max_age_days=max_age_days, # None=use global, 0=disable, >0=override
            )
            if feed.id and feed.url:
                feeds.append(feed)

        return cls(
            feeds=feeds,
            request_interval=config.get("request_interval", 2000),
            timeout=config.get("timeout", 15),
            use_proxy=config.get("use_proxy", False),
            proxy_url=config.get("proxy_url", ""),
            timezone=config.get("timezone", DEFAULT_TIMEZONE),
            freshness_enabled=freshness_enabled,
            default_max_age_days=default_max_age_days,
        )
