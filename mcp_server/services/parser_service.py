"""
Data analysis service

v2.0.0: Only supports SQLite database, removes TXT file support
New storage structure: output/{type}/{date}.db
"""

import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import yaml

from ..utils.errors import FileParseError, DataNotFoundError
from .cache_service import get_cache


class ParserService:
    """Data parsing service class"""

    def __init__(self, project_root: str = None):
        """
        Initialize parsing service

        Args:
            project_root: project root directory, defaults to the parent directory of the current directory
        """
        if project_root is None:
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.cache = get_cache()

        # frequency_words.txt mtime cache
        self._freq_words_cache: Optional[List[Dict]] = None
        self._freq_words_mtime: float = 0.0

    @staticmethod
    def clean_title(title: str) -> str:
        """Clean title text"""
        title = re.sub(r'\s+', ' ', title)
        title = title.strip()
        return title

    def get_date_folder_name(self, date: datetime = None) -> str:
        """
        Get date string (ISO format)

        Args:
            date: date object, default is today

        Returns:
            Date string (YYYY-MM-DD)
        """
        if date is None:
            date = datetime.now()
        return date.strftime("%Y-%m-%d")

    def _get_db_path(self, date: datetime = None, db_type: str = "news") -> Optional[Path]:
        """
        Get database file path

        New structure: output/{type}/{date}.db

        Args:
            date: date object, default is today
            db_type: database type ("news" or "rss")

        Returns:
            Database file path, returns None if it does not exist
        """
        date_str = self.get_date_folder_name(date)
        db_path = self.project_root / "output" / db_type / f"{date_str}.db"
        if db_path.exists():
            return db_path
        return None

    def _read_from_sqlite(
        self,
        date: datetime = None,
        platform_ids: Optional[List[str]] = None,
        db_type: str = "news"
    ) -> Optional[Tuple[Dict, Dict, Dict]]:
        """
        Read data from SQLite database

        Args:
            date: date object, default is today
            platform_ids: list of platform IDs, None means all platforms
            db_type: database type ("news" or "rss")

        Returns:
            (all_titles, id_to_name, all_timestamps) tuple, returns None if the database does not exist
        """
        db_path = self._get_db_path(date, db_type)
        if db_path is None:
            return None

        all_titles = {}
        id_to_name = {}
        all_timestamps = {}

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if db_type == "news":
                return self._read_news_from_sqlite(cursor, platform_ids, all_titles, id_to_name, all_timestamps)
            elif db_type == "rss":
                return self._read_rss_from_sqlite(cursor, platform_ids, all_titles, id_to_name, all_timestamps)

        except Exception as e:
            print(f"Warning: Failed to read data from SQLite: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    def _read_news_from_sqlite(
        self,
        cursor,
        platform_ids: Optional[List[str]],
        all_titles: Dict,
        id_to_name: Dict,
        all_timestamps: Dict
    ) -> Optional[Tuple[Dict, Dict, Dict]]:
        """Read data from the hot list database"""
        # Check if the table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='news_items'
        """)
        if not cursor.fetchone():
            return None

        # Build query
        if platform_ids:
            placeholders = ','.join(['?' for _ in platform_ids])
            query = f"""
                SELECT n.id, n.platform_id, p.name as platform_name, n.title,
                       n.rank, n.url, n.mobile_url,
                       n.first_crawl_time, n.last_crawl_time, n.crawl_count
                FROM news_items n
                LEFT JOIN platforms p ON n.platform_id = p.id
                WHERE n.platform_id IN ({placeholders})
            """
            cursor.execute(query, platform_ids)
        else:
            cursor.execute("""
                SELECT n.id, n.platform_id, p.name as platform_name, n.title,
                       n.rank, n.url, n.mobile_url,
                       n.first_crawl_time, n.last_crawl_time, n.crawl_count
                FROM news_items n
                LEFT JOIN platforms p ON n.platform_id = p.id
            """)

        rows = cursor.fetchall()

        # Collect all news_item_id for querying historical rankings
        news_ids = [row['id'] for row in rows]
        rank_history_map = {}

        if news_ids:
            placeholders = ",".join("?" * len(news_ids))
            cursor.execute(f"""
                SELECT news_item_id, rank FROM rank_history
                WHERE news_item_id IN ({placeholders})
                ORDER BY news_item_id, crawl_time
            """, news_ids)

            for rh_row in cursor.fetchall():
                news_id = rh_row['news_item_id']
                rank = rh_row['rank']
                if news_id not in rank_history_map:
                    rank_history_map[news_id] = []
                rank_history_map[news_id].append(rank)

        for row in rows:
            news_id = row['id']
            platform_id = row['platform_id']
            platform_name = row['platform_name'] or platform_id
            title = row['title']

            if platform_id not in id_to_name:
                id_to_name[platform_id] = platform_name

            if platform_id not in all_titles:
                all_titles[platform_id] = {}

            ranks = rank_history_map.get(news_id, [row['rank']])

            all_titles[platform_id][title] = {
                "ranks": ranks,
                "url": row['url'] or "",
                "mobileUrl": row['mobile_url'] or "",
                "first_time": row['first_crawl_time'] or "",
                "last_time": row['last_crawl_time'] or "",
                "count": row['crawl_count'] or 1,
            }

        # Get the crawl time as timestamps
        cursor.execute("""
            SELECT crawl_time, created_at FROM crawl_records
            ORDER BY crawl_time
        """)
        for row in cursor.fetchall():
            crawl_time = row['crawl_time']
            created_at = row['created_at']
            try:
                ts = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").timestamp()
            except (ValueError, TypeError):
                ts = datetime.now().timestamp()
            all_timestamps[f"{crawl_time}.db"] = ts

        if not all_titles:
            return None

        return (all_titles, id_to_name, all_timestamps)

    def _read_rss_from_sqlite(
        self,
        cursor,
        feed_ids: Optional[List[str]],
        all_items: Dict,
        id_to_name: Dict,
        all_timestamps: Dict
    ) -> Optional[Tuple[Dict, Dict, Dict]]:
        """Read data from RSS database"""
        # Check if the table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='rss_items'
        """)
        if not cursor.fetchone():
            return None

        # Build query
        if feed_ids:
            placeholders = ','.join(['?' for _ in feed_ids])
            query = f"""
                SELECT i.id, i.feed_id, f.name as feed_name, i.title,
                       i.url, i.published_at, i.summary, i.author,
                       i.first_crawl_time, i.last_crawl_time, i.crawl_count
                FROM rss_items i
                LEFT JOIN rss_feeds f ON i.feed_id = f.id
                WHERE i.feed_id IN ({placeholders})
                ORDER BY i.published_at DESC
            """
            cursor.execute(query, feed_ids)
        else:
            cursor.execute("""
                SELECT i.id, i.feed_id, f.name as feed_name, i.title,
                       i.url, i.published_at, i.summary, i.author,
                       i.first_crawl_time, i.last_crawl_time, i.crawl_count
                FROM rss_items i
                LEFT JOIN rss_feeds f ON i.feed_id = f.id
                ORDER BY i.published_at DESC
            """)

        rows = cursor.fetchall()

        for row in rows:
            feed_id = row['feed_id']
            feed_name = row['feed_name'] or feed_id
            title = row['title']

            if feed_id not in id_to_name:
                id_to_name[feed_id] = feed_name

            if feed_id not in all_items:
                all_items[feed_id] = {}

            all_items[feed_id][title] = {
                "url": row['url'] or "",
                "published_at": row['published_at'] or "",
                "summary": row['summary'] or "",
                "author": row['author'] or "",
                "first_time": row['first_crawl_time'] or "",
                "last_time": row['last_crawl_time'] or "",
                "count": row['crawl_count'] or 1,
            }

        # Get the crawl time
        cursor.execute("""
            SELECT crawl_time, created_at FROM rss_crawl_records
            ORDER BY crawl_time
        """)
        for row in cursor.fetchall():
            crawl_time = row['crawl_time']
            created_at = row['created_at']
            try:
                ts = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").timestamp()
            except (ValueError, TypeError):
                ts = datetime.now().timestamp()
            all_timestamps[f"{crawl_time}.db"] = ts

        if not all_items:
            return None

        return (all_items, id_to_name, all_timestamps)

    def read_all_titles_for_date(
        self,
        date: datetime = None,
        platform_ids: Optional[List[str]] = None,
        db_type: str = "news"
    ) -> Tuple[Dict, Dict, Dict]:
        """
        Read all data for a specified date (with cache)

        Args:
            date: date object, default is today
            platform_ids: Platform/Feed ID list, None means all
            db_type: database type ("news" or "rss")

        Returns:
            (all_titles, id_to_name, all_timestamps) tuple

        Raises:
            DataNotFoundError: data does not exist
        """
        date_str = self.get_date_folder_name(date)
        platform_key = ','.join(sorted(platform_ids)) if platform_ids else 'all'
        cache_key = f"read_all:{db_type}:{date_str}:{platform_key}"

        is_today = (date is None) or (date.date() == datetime.now().date())
        ttl = 900 if is_today else 900

        cached = self.cache.get(cache_key, ttl=ttl)
        if cached:
            return cached

        result = self._read_from_sqlite(date, platform_ids, db_type)
        if result:
            self.cache.set(cache_key, result)
            return result

        raise DataNotFoundError(
            f"{db_type} data for {date_str} not found",
            suggestion="Please run the crawler first or check if the date is correct"
        )

    def parse_yaml_config(self, config_path: str = None) -> dict:
        """
        Parse YAML configuration files

        Args:
            config_path: Configuration file path, default is config/config.yaml

        Returns:
            Configuration dictionary

        Raises:
            FileParseError: Configuration file parsing error
        """
        if config_path is None:
            config_path = self.project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileParseError(str(config_path), "Configuration file does not exist")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            return config_data
        except Exception as e:
            raise FileParseError(str(config_path), str(e))

    def parse_frequency_words(self, words_file: str = None) -> List[Dict]:
        """
        Parse keyword configuration files (with mtime cache)

        Only re-parse frequency_words.txt when it is modified to avoid repeated IO within the loop.

        Reuse the parsing logic of trendradar.core.frequency and support:
        - Comment lines starting with #
        - Blank lines separate phrases
        - [Group Alias] As the first line of the phrase, assign an alias to the entire group
        - + prefix required words, ! prefix filter words, @ quantity limit
        - /pattern/ regular expression syntax
        - => alias display name syntax
        - [GLOBAL_FILTER] Global filter area

        Display name priority: Group alias > Row alias splicing > Keyword splicing

        Args:
            words_file: keyword file path, default is config/frequency_words.txt

        Returns:
            phrase list

        Raises:
            FileParseError: File parsing error
        """
        import os
        from trendradar.core.frequency import load_frequency_words

        if words_file is None:
            words_file = str(self.project_root / "config" / "frequency_words.txt")
        else:
            words_file = str(words_file)

        try:
            current_mtime = os.path.getmtime(words_file)

            if self._freq_words_cache is not None and current_mtime == self._freq_words_mtime:
                return self._freq_words_cache

            word_groups, filter_words, global_filters = load_frequency_words(words_file)
            self._freq_words_cache = word_groups
            self._freq_words_mtime = current_mtime
            return word_groups
        except FileNotFoundError:
            return []
        except Exception as e:
            raise FileParseError(words_file, str(e))

    def get_available_dates(self, db_type: str = "news") -> List[str]:
        """
        Get a list of available dates

        Args:
            db_type: database type ("news" or "rss")

        Returns:
            List of date strings (YYYY-MM-DD format, sorted in descending order)
        """
        db_dir = self.project_root / "output" / db_type
        if not db_dir.exists():
            return []

        dates = []
        for db_file in db_dir.glob("*.db"):
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})\.db$', db_file.name)
            if date_match:
                dates.append(date_match.group(1))

        return sorted(dates, reverse=True)

    def get_available_date_range(self, db_type: str = "news") -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Get available date range

        Args:
            db_type: database type ("news" or "rss")

        Returns:
            (earliest date, latest date) tuple, or (None, None) if there is no data
        """
        dates = self.get_available_dates(db_type)
        if not dates:
            return (None, None)

        earliest = datetime.strptime(dates[-1], "%Y-%m-%d")
        latest = datetime.strptime(dates[0], "%Y-%m-%d")
        return (earliest, latest)
