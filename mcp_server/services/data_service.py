"""
Data access service

Provides a unified data query interface, encapsulates data access logic.
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .cache_service import get_cache
from .parser_service import ParserService
from ..utils.errors import DataNotFoundError


class DataService:
    """Data access service class"""

    # Chinese stop words list (used for auto_extract mode)
    STOPWORDS = {
        'of', 'ed', 'in', 'is', 'I', 'have', 'and', 'then', 'not', 'person', 'all', 'one',
        'one', 'on', 'also', 'very', 'to', 'say', 'want', 'go', 'you', 'will', 'ing', 'not have',
        'look', 'good', 'self', 'this', 'that', 'come', 'by', 'with', 'for', 'to', 'will', 'from',
        'with', 'and', 'etc', 'but', 'or', 'and', 'in', 'middle', 'by', 'can', 'can', 'already',
        'already', 'still', 'more', 'most', 'again', 'because', 'so', 'if', 'although', 'however',
        'what', 'how', 'how', 'which', 'which', 'how much', 'how many', 'this', 'that',
        'he', 'she', 'it', 'they', 'they', 'we', 'you', 'everyone', 'self',
        'like this', 'like that', 'how', 'so', 'then', 'how', 'very', 'special',
        'should', 'possible', 'can', 'need', 'must', 'certainly', 'definitely', 'indeed',
        'currently', 'already', 'once', 'will', 'about to', 'just', 'immediately', 'at once',
        'respond', 'publish', 'state', 'claim', 'expose', 'official', 'latest', 'blockbuster', 'breaking',
        'hot search', 'flood screen', 'trigger', 'attention', 'netizen', 'comment', 'forward', 'like'
    }

    def __init__(self, project_root: str = None):
        """
        Initialize data service

        Args:
            project_root: Project root directory
        """
        self.parser = ParserService(project_root)
        self.cache = get_cache()

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        include_url: bool = False
    ) -> List[Dict]:
        """
        Get the latest batch of crawled news data

        Args:
            platforms: Platform ID list, None means all platforms
            limit: Return count limit
            include_url: Whether to include URL links, default False (saves tokens)

        Returns:
            News list

        Raises:
            DataNotFoundError: Data does not exist
        """
        # Try to get from cache
        cache_key = f"latest_news:{','.join(platforms or [])}:{limit}:{include_url}"
        cached = self.cache.get(cache_key, ttl=900)  # 15 minutes cache
        if cached:
            return cached

        # Read today's data
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date(
            date=None,
            platform_ids=platforms
        )

        # Get the latest file time
        if timestamps:
            latest_timestamp = max(timestamps.values())
            fetch_time = datetime.fromtimestamp(latest_timestamp)
        else:
            fetch_time = datetime.now()

        # Convert to news list
        news_list = []
        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Take the first ranking
                rank = info["ranks"][0] if info["ranks"] else 0

                news_item = {
                    "title": title,
                    "platform": platform_id,
                    "platform_name": platform_name,
                    "rank": rank,
                    "timestamp": fetch_time.strftime("%Y-%m-%d %H:%M:%S")
                }

                # Conditionally add URL field
                if include_url:
                    news_item["url"] = info.get("url", "")
                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                news_list.append(news_item)

        # Sort by ranking
        news_list.sort(key=lambda x: x["rank"])

        # Limit return quantity
        result = news_list[:limit]

        # Cache results
        self.cache.set(cache_key, result)

        return result

    def get_news_by_date(
        self,
        target_date: datetime,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        include_url: bool = False
    ) -> List[Dict]:
        """
        Get news by specified date

        Args:
            target_date: Target date
            platforms: Platform ID list, None means all platforms
            limit: Return count limit
            include_url: Whether to include URL links, default False (saves tokens)

        Returns:
            News list

        Raises:
            DataNotFoundError: Data not found

        Examples:
            >>> service = DataService()
            >>> news = service.get_news_by_date(
            ...     target_date=datetime(2025, 10, 10),
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
        """
        # Try to get from cache
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"news_by_date:{date_str}:{','.join(platforms or [])}:{limit}:{include_url}"
        cached = self.cache.get(cache_key, ttl=900)  # 15 minutes cache
        if cached:
            return cached

        # Read data for the specified date
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date(
            date=target_date,
            platform_ids=platforms
        )

        # Convert to news list
        news_list = []
        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Calculate average ranking
                avg_rank = sum(info["ranks"]) / len(info["ranks"]) if info["ranks"] else 0

                news_item = {
                    "title": title,
                    "platform": platform_id,
                    "platform_name": platform_name,
                    "rank": info["ranks"][0] if info["ranks"] else 0,
                    "avg_rank": round(avg_rank, 2),
                    "count": len(info["ranks"]),
                    "date": date_str
                }

                # Conditionally add URL field
                if include_url:
                    news_item["url"] = info.get("url", "")
                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                news_list.append(news_item)

        # Sort by ranking
        news_list.sort(key=lambda x: x["rank"])

        # Limit return quantity
        result = news_list[:limit]

        # Cache results (historical data cached longer)
        self.cache.set(cache_key, result)

        return result

    def search_news_by_keyword(
        self,
        keyword: str,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Search news by keyword

        Args:
            keyword: Search keyword
            date_range: Date range (start_date, end_date)
            platforms: Platform filter list
            limit: Return count limit (optional)

        Returns:
            Search result dictionary

        Raises:
            DataNotFoundError: Data not found
        """
        # Determine search date range
        if date_range:
            start_date, end_date = date_range
        else:
            # Default search today
            start_date = end_date = datetime.now()

        # Collect all matching news
        results = []
        platform_distribution = Counter()

        # Iterate through date range
        current_date = start_date
        while current_date <= end_date:
            try:
                all_titles, id_to_name, _ = self.parser.read_all_titles_for_date(
                    date=current_date,
                    platform_ids=platforms
                )

                # Search for titles containing keywords
                for platform_id, titles in all_titles.items():
                    platform_name = id_to_name.get(platform_id, platform_id)

                    for title, info in titles.items():
                        if keyword.lower() in title.lower():
                            # Calculate average ranking
                            avg_rank = sum(info["ranks"]) / len(info["ranks"]) if info["ranks"] else 0

                            results.append({
                                "title": title,
                                "platform": platform_id,
                                "platform_name": platform_name,
                                "ranks": info["ranks"],
                                "count": len(info["ranks"]),
                                "avg_rank": round(avg_rank, 2),
                                "url": info.get("url", ""),
                                "mobileUrl": info.get("mobileUrl", ""),
                                "date": current_date.strftime("%Y-%m-%d")
                            })

                            platform_distribution[platform_id] += 1

            except DataNotFoundError:
                # No data for this date, continue to next day
                pass

            # Next day
            current_date += timedelta(days=1)

        if not results:
            raise DataNotFoundError(
                f"No news found containing keyword '{keyword}'",
                suggestion="Please try other keywords or expand the date range"
            )

        # Calculate statistics
        total_ranks = []
        for item in results:
            total_ranks.extend(item["ranks"])

        avg_rank = sum(total_ranks) / len(total_ranks) if total_ranks else 0

        # Limit return quantity (if specified)
        total_found = len(results)
        if limit is not None and limit > 0:
            results = results[:limit]

        return {
            "results": results,
            "total": len(results),
            "total_found": total_found,
            "statistics": {
                "platform_distribution": dict(platform_distribution),
                "avg_rank": round(avg_rank, 2),
                "keyword": keyword
            }
        }

    def _extract_words_from_title(self, title: str, min_length: int = 2) -> List[str]:
        """
        Extract meaningful words from title (used for auto_extract mode)

        Args:
            title: News title
            min_length: Minimum word length

        Returns:
            Keyword list
        """
        # Remove URL and special characters
        title = re.sub(r'http[s]?://\S+', '', title)
        title = re.sub(r'\[.*?\]', '', title)  # Remove square bracket content
        title = re.sub(r'[【】《》「」『』""''・·•]', '', title)  # Remove Chinese punctuation

        # Use regular expression for tokenization (Chinese and English)
        # Match continuous Chinese characters or English words
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}[a-zA-Z0-9]*', title)

        # Filter stop words and short words
        keywords = [
            word for word in words
            if word and len(word) >= min_length and word.lower() not in self.STOPWORDS
            and word not in self.STOPWORDS
        ]

        return keywords

    def get_trending_topics(
        self,
        top_n: int = 10,
        mode: str = "current",
        extract_mode: str = "keywords"
    ) -> Dict:
        """
        Get hot topic statistics

        Args:
            top_n: Return TOP N topics
            mode: Time mode
                - "daily": Cumulative data statistics for the day
                - "current": Latest batch of data statistics (default)
            extract_mode: Extraction mode
                - "keywords": Statistics of preset focus words (based on config/frequency_words.txt)
                - "auto_extract": Automatically extract high-frequency words from news titles

        Returns:
            Topic frequency statistics dictionary

        Raises:
            DataNotFoundError: Data does not exist
        """
        # Try to get from cache
        cache_key = f"trending_topics:{top_n}:{mode}:{extract_mode}"
        cached = self.cache.get(cache_key, ttl=900)  # 15 minutes cache
        if cached:
            return cached

        # Read today's data
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date()

        if not all_titles:
            raise DataNotFoundError(
                "Today's news data not found",
                suggestion="Please ensure the crawler has run and generated data"
            )

        # Select title data to process based on mode
        if mode == "daily":
            titles_to_process = all_titles
        elif mode == "current":
            titles_to_process = all_titles  # Simplified implementation
        else:
            raise ValueError(f"Unsupported mode: {mode}. Supported modes: daily, current")

        # Count word frequency
        word_frequency = Counter()
        keyword_to_news = {}

        # Preload keyword data (avoid repeated calls inside the loop)
        if extract_mode == "keywords":
            from trendradar.core.frequency import _word_matches
            word_groups = self.parser.parse_frequency_words()

        # Iterate through titles to process
        for platform_id, titles in titles_to_process.items():
            for title in titles.keys():
                if extract_mode == "keywords":
                    # Statistics based on preset keywords (supports regex matching)
                    title_lower = title.lower()

                    for group in word_groups:
                        all_words = group.get("required", []) + group.get("normal", [])
                        # Check if it matches any word in the phrase group
                        matched = any(_word_matches(word_config, title_lower) for word_config in all_words)

                        if matched:
                            # Use the group's display_name (group alias or row alias concatenation)
                            display_key = group.get("display_name") or group.get("group_key", "")

                            word_frequency[display_key] += 1
                            if display_key not in keyword_to_news:
                                keyword_to_news[display_key] = []
                            keyword_to_news[display_key].append(title)
                            break  # Each title is only counted for the first matched phrase group

                elif extract_mode == "auto_extract":
                    # Automatically extract keywords
                    extracted_words = self._extract_words_from_title(title)
                    for word in extracted_words:
                        word_frequency[word] += 1
                        if word not in keyword_to_news:
                            keyword_to_news[word] = []
                        keyword_to_news[word].append(title)

        # Get TOP N keywords
        top_keywords = word_frequency.most_common(top_n)

        # Build topic list
        topics = []
        for keyword, frequency in top_keywords:
            matched_news = keyword_to_news.get(keyword, [])

            topics.append({
                "keyword": keyword,
                "frequency": frequency,
                "matched_news": len(set(matched_news)),  # Number of news after deduplication
                "trend": "stable",
                "weight_score": 0.0
            })

        # Build results
        result = {
            "topics": topics,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "extract_mode": extract_mode,
            "total_keywords": len(word_frequency),
            "description": self._get_mode_description(mode, extract_mode)
        }

        # Cache results
        self.cache.set(cache_key, result)

        return result

    def _get_mode_description(self, mode: str, extract_mode: str = "keywords") -> str:
        """Get mode description"""
        mode_desc = {
            "daily": "Cumulative statistics for the day",
            "current": "Latest batch statistics"
        }.get(mode, "Unknown time mode")

        extract_desc = {
            "keywords": "Based on preset focus words",
            "auto_extract": "Automatically extract high-frequency words"
        }.get(extract_mode, "Unknown extraction mode")

        return f"{mode_desc} - {extract_desc}"

    def get_current_config(self, section: str = "all") -> Dict:
        """
        Get current system configuration

        Args:
            section: Configuration section - all/crawler/push/keywords/weights

        Returns:
            Configuration dictionary

        Raises:
            FileParseError: Configuration file parsing error
        """
        # Parse configuration file
        config_data = self.parser.parse_yaml_config()
        word_groups = self.parser.parse_frequency_words()

        # Return corresponding configuration based on section
        advanced = config_data.get("advanced", {})
        advanced_crawler = advanced.get("crawler", {})
        platforms_config = config_data.get("platforms", {})

        if section == "all" or section == "crawler":
            crawler_config = {
                "enable_crawler": platforms_config.get("enabled", True),
                "use_proxy": advanced_crawler.get("use_proxy", False),
                "request_interval": advanced_crawler.get("request_interval", 1),
                "retry_times": 3,
                "platforms": [p["id"] for p in platforms_config.get("sources", []) if p.get("enabled", True)]
            }

        if section == "all" or section == "push":
            notification = config_data.get("notification", {})
            batch_size = advanced.get("batch_size", {})
            push_config = {
                "enable_notification": notification.get("enabled", True),
                "enabled_channels": [],
                "message_batch_size": batch_size.get("default", 4000),
                "push_window": {}  # Migrated to scheduling system (schedule + timeline.yaml)
            }

            # Detect configured notification channels (merge config.yaml + .env)
            from trendradar.core.loader import _load_webhook_config

            webhook_config = _load_webhook_config(config_data)

            channel_checks = {
                "feishu": [webhook_config.get("FEISHU_WEBHOOK_URL")],
                "dingtalk": [webhook_config.get("DINGTALK_WEBHOOK_URL")],
                "wework": [webhook_config.get("WEWORK_WEBHOOK_URL")],
                "telegram": [webhook_config.get("TELEGRAM_BOT_TOKEN"), webhook_config.get("TELEGRAM_CHAT_ID")],
                "email": [webhook_config.get("EMAIL_FROM"), webhook_config.get("EMAIL_PASSWORD"), webhook_config.get("EMAIL_TO")],
                "ntfy": [webhook_config.get("NTFY_SERVER_URL"), webhook_config.get("NTFY_TOPIC")],
                "bark": [webhook_config.get("BARK_URL")],
                "slack": [webhook_config.get("SLACK_WEBHOOK_URL")],
                "generic_webhook": [webhook_config.get("GENERIC_WEBHOOK_URL")],
            }
            for ch_id, required_values in channel_checks.items():
                if all(required_values):
                    push_config["enabled_channels"].append(ch_id)

        if section == "all" or section == "keywords":
            keywords_config = {
                "word_groups": word_groups,
                "total_groups": len(word_groups)
            }

        if section == "all" or section == "weights":
            weight = advanced.get("weight", {})
            weights_config = {
                "rank_weight": weight.get("rank", 0.6),
                "frequency_weight": weight.get("frequency", 0.3),
                "hotness_weight": weight.get("hotness", 0.1)
            }

        # Assemble results
        if section == "all":
            result = {
                "crawler": crawler_config,
                "push": push_config,
                "keywords": keywords_config,
                "weights": weights_config
            }
        elif section == "crawler":
            result = crawler_config
        elif section == "push":
            result = push_config
        elif section == "keywords":
            result = keywords_config
        elif section == "weights":
            result = weights_config
        else:
            result = {}

        return result

    def get_available_date_range(self, db_type: str = "news") -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Scan the output directory and return the actual available date range

        Args:
            db_type: Database type ("news" or "rss")

        Returns:
            (Earliest date, Latest date) tuple, returns (None, None) if there is no data

        Examples:
            >>> service = DataService()
            >>> earliest, latest = service.get_available_date_range()
            >>> print(f"Available date range: {earliest} to {latest}")
        """
        return self.parser.get_available_date_range(db_type)

    def get_system_status(self) -> Dict:
        """
        Get system running status

        Returns:
            System status dictionary
        """
        # Get data statistics
        output_dir = self.parser.project_root / "output"

        total_storage = 0

        # Use parser's method to get date range
        oldest_record, latest_record = self.get_available_date_range(db_type="news")

        # Calculate total storage size of output directory
        if output_dir.exists():
            for item in output_dir.rglob("*"):
                if item.is_file():
                    total_storage += item.stat().st_size

        # Read version information
        version_file = self.parser.project_root / "version"
        version = "unknown"
        if version_file.exists():
            try:
                with open(version_file, "r") as f:
                    version = f.read().strip()
            except (OSError, ValueError):
                pass

        return {
            "system": {
                "version": version,
                "project_root": str(self.parser.project_root)
            },
            "data": {
                "total_storage": f"{total_storage / 1024 / 1024:.2f} MB",
                "oldest_record": oldest_record.strftime("%Y-%m-%d") if oldest_record else None,
                "latest_record": latest_record.strftime("%Y-%m-%d") if latest_record else None,
            },
            "cache": self.cache.get_stats(),
            "health": "healthy"
        }

    # ========================================
    # RSS data query method
    # ========================================

    def get_latest_rss(
        self,
        feeds: Optional[List[str]] = None,
        days: int = 1,
        limit: int = 50,
        include_summary: bool = False
    ) -> List[Dict]:
        """
        Get the latest RSS data (supports multi-day query)

        Args:
            feeds: List of RSS feed IDs, None means all feeds
            days: Get data for the last N days, default 1 (today only), max 30 days
            limit: Limit on the number of returned items
            include_summary: Whether to include summary, default False (saves tokens)

        Returns:
            List of RSS items (deduplicated by URL)

        Raises:
            DataNotFoundError: Data does not exist
        """
        days = min(max(days, 1), 30)  # Limit to 1-30 days
        cache_key = f"latest_rss:{','.join(feeds or [])}:{days}:{limit}:{include_summary}"
        cached = self.cache.get(cache_key, ttl=900)
        if cached:
            return cached

        rss_list = []
        seen_urls = set()  # Cross-date URL deduplication
        today = datetime.now()

        for i in range(days):
            target_date = today - timedelta(days=i)

            try:
                all_items, id_to_name, timestamps = self.parser.read_all_titles_for_date(
                    date=target_date,
                    platform_ids=feeds,
                    db_type="rss"
                )

                # Get crawl time
                if timestamps:
                    latest_timestamp = max(timestamps.values())
                    fetch_time = datetime.fromtimestamp(latest_timestamp)
                else:
                    fetch_time = target_date

                # Convert to list
                for feed_id, items in all_items.items():
                    feed_name = id_to_name.get(feed_id, feed_id)

                    for title, info in items.items():
                        # Cross-date URL deduplication
                        url = info.get("url", "")
                        if url and url in seen_urls:
                            continue
                        if url:
                            seen_urls.add(url)

                        rss_item = {
                            "title": title,
                            "feed_id": feed_id,
                            "feed_name": feed_name,
                            "url": url,
                            "published_at": info.get("published_at", ""),
                            "author": info.get("author", ""),
                            "date": target_date.strftime("%Y-%m-%d"),
                            "fetch_time": fetch_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(fetch_time, datetime) else target_date.strftime("%Y-%m-%d")
                        }

                        if include_summary:
                            rss_item["summary"] = info.get("summary", "")

                        rss_list.append(rss_item)

            except DataNotFoundError:
                continue

        # Sort by publish time (newest first)
        rss_list.sort(key=lambda x: x.get("published_at", ""), reverse=True)

        # Limit return quantity
        result = rss_list[:limit]

        # Cache results
        self.cache.set(cache_key, result)

        return result

    def search_rss(
        self,
        keyword: str,
        feeds: Optional[List[str]] = None,
        days: int = 7,
        limit: int = 50,
        include_summary: bool = False
    ) -> List[Dict]:
        """
        Search RSS data (automatic cross-date deduplication)

        Args:
            keyword: Search keyword
            feeds: List of RSS feed IDs, None means all feeds
            days: Search data for the last N days
            limit: Limit on the number of returned items
            include_summary: Whether to include summary

        Returns:
            List of matched RSS items (deduplicated by URL)
        """
        cache_key = f"search_rss:{keyword}:{','.join(feeds or [])}:{days}:{limit}:{include_summary}"
        cached = self.cache.get(cache_key, ttl=900)
        if cached:
            return cached

        results = []
        seen_urls = set()  # Used for URL deduplication
        today = datetime.now()

        for i in range(days):
            target_date = today - timedelta(days=i)

            try:
                all_items, id_to_name, _ = self.parser.read_all_titles_for_date(
                    date=target_date,
                    platform_ids=feeds,
                    db_type="rss"
                )

                for feed_id, items in all_items.items():
                    feed_name = id_to_name.get(feed_id, feed_id)

                    for title, info in items.items():
                        # Cross-date deduplication: skip if URL has already appeared
                        url = info.get("url", "")
                        if url and url in seen_urls:
                            continue
                        if url:
                            seen_urls.add(url)

                        # Keyword matching (title or summary)
                        summary = info.get("summary", "")
                        if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
                            rss_item = {
                                "title": title,
                                "feed_id": feed_id,
                                "feed_name": feed_name,
                                "url": url,
                                "published_at": info.get("published_at", ""),
                                "author": info.get("author", ""),
                                "date": target_date.strftime("%Y-%m-%d")
                            }

                            if include_summary:
                                rss_item["summary"] = summary

                            results.append(rss_item)

            except DataNotFoundError:
                continue

        # Sort by publish time
        results.sort(key=lambda x: x.get("published_at", ""), reverse=True)

        # Limit return quantity
        result = results[:limit]

        # Cache results
        self.cache.set(cache_key, result)

        return result

    def get_rss_feeds_status(self) -> Dict:
        """
        Get RSS feed status

        Returns:
            RSS feed status information
        """
        cache_key = "rss_feeds_status"
        cached = self.cache.get(cache_key, ttl=900)
        if cached:
            return cached

        # Get available RSS dates
        available_dates = self.parser.get_available_dates(db_type="rss")

        # Get today's RSS data statistics
        today_stats = {}
        try:
            all_items, id_to_name, _ = self.parser.read_all_titles_for_date(
                date=None,
                platform_ids=None,
                db_type="rss"
            )

            for feed_id, items in all_items.items():
                today_stats[feed_id] = {
                    "name": id_to_name.get(feed_id, feed_id),
                    "item_count": len(items)
                }

        except DataNotFoundError:
            pass

        result = {
            "available_dates": available_dates[:10],  # Last 10 days
            "total_dates": len(available_dates),
            "today_feeds": today_stats,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.cache.set(cache_key, result)

        return result
