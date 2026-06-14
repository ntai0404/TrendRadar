# coding=utf-8
"""
SQLite Storage Mixin

Provide common SQLite database operation logic for LocalStorageBackend and RemoteStorageBackend to reuse.
"""

import sqlite3
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from trendradar.storage.base import NewsItem, NewsData, RSSItem, RSSData
from trendradar.utils.url import normalize_url


class SQLiteStorageMixin:
    """
    SQLite storage operation Mixin

    Subclasses need to implement the following abstract methods:
    - _get_connection(date, db_type) -> sqlite3.Connection
    - _get_configured_time() -> datetime
    - _format_date_folder(date) -> str
    - _format_time_filename() -> str
    """

    # ========================================
    # Abstract methods - subclasses must implement
    # ========================================

    @abstractmethod
    def _get_connection(self, date: Optional[str] = None, db_type: str = "news") -> sqlite3.Connection:
        """Get database connection"""
        pass

    @abstractmethod
    def _get_configured_time(self) -> datetime:
        """Get current time in configured timezone"""
        pass

    @abstractmethod
    def _format_date_folder(self, date: Optional[str] = None) -> str:
        """Format date folder name (ISO format: YYYY-MM-DD)"""
        pass

    @abstractmethod
    def _format_time_filename(self) -> str:
        """Format time file name (format: HH-MM)"""
        pass

    # ========================================
    # Schema management
    # ========================================

    def _get_schema_path(self, db_type: str = "news") -> Path:
        """
        Get schema.sql file path

        Args:
            db_type: Database type ("news" or "rss")

        Returns:
            schema file path
        """
        if db_type == "rss":
            return Path(__file__).parent / "rss_schema.sql"
        return Path(__file__).parent / "schema.sql"

    def _get_ai_filter_schema_path(self) -> Path:
        """Get AI filter schema file path"""
        return Path(__file__).parent / "ai_filter_schema.sql"

    def _init_tables(self, conn: sqlite3.Connection, db_type: str = "news") -> None:
        """
        Initialize database table structure from schema.sql

        Args:
            conn: Database connection
            db_type: Database type ("news" or "rss")
        """
        schema_path = self._get_schema_path(db_type)

        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
        else:
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        # news database additionally loads AI filter table structure
        if db_type == "news":
            ai_filter_schema = self._get_ai_filter_schema_path()
            if ai_filter_schema.exists():
                with open(ai_filter_schema, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())

        if db_type == "rss":
            self._migrate_rss_schema(conn)

        conn.commit()

    def _migrate_rss_schema(self, conn: sqlite3.Connection) -> None:
        """Migrate rss_items table structure (add guid column to existing database)"""
        cursor = conn.execute("PRAGMA table_info(rss_items)")
        columns = {row[1] for row in cursor.fetchall()}
        if "guid" not in columns:
            conn.execute("ALTER TABLE rss_items ADD COLUMN guid TEXT DEFAULT ''")
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_rss_guid_feed
                ON rss_items(guid, feed_id) WHERE guid != ''
            """)

    # ========================================
    # News data storage
    # ========================================

    def _save_news_data_impl(self, data: NewsData, log_prefix: str = "[Storage]") -> tuple[bool, int, int, int, int]:
        """
        Save news data to SQLite (core implementation)

        Args:
            data: News data
            log_prefix: Log prefix

        Returns:
            (success, new_count, updated_count, title_changed_count, off_list_count)
        """
        try:
            conn = self._get_connection(data.date)
            cursor = conn.cursor()

            # Get current time in configured timezone
            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")

            # First synchronize platform information to platforms table
            for source_id, source_name in data.id_to_name.items():
                cursor.execute("""
                    INSERT INTO platforms (id, name, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        updated_at = excluded.updated_at
                """, (source_id, source_name, now_str))

            # Statistics counter
            new_count = 0
            updated_count = 0
            title_changed_count = 0
            success_sources = []

            for source_id, news_list in data.items.items():
                success_sources.append(source_id)

                for item in news_list:
                    try:
                        # Standardize URL (remove dynamic parameters, such as Weibo's band_rank)
                        normalized_url = normalize_url(item.url, source_id) if item.url else ""

                        # Check if it already exists (via standardized URL + platform_id)
                        if normalized_url:
                            cursor.execute("""
                                SELECT id, title FROM news_items
                                WHERE url = ? AND platform_id = ?
                            """, (normalized_url, source_id))
                            existing = cursor.fetchone()

                            if existing:
                                # Already exists, Cập nhật record
                                existing_id, existing_title = existing

                                update_title = item.title
                                if (update_title and update_title.strip().startswith(("http://", "https://", "//"))
                                        and existing_title and not existing_title.strip().startswith(("http://", "https://", "//"))):
                                    update_title = existing_title

                                # Check if title has changed
                                if existing_title != update_title:
                                    # Record title change
                                    cursor.execute("""
                                        INSERT INTO title_changes
                                        (news_item_id, old_title, new_title, changed_at)
                                        VALUES (?, ?, ?, ?)
                                    """, (existing_id, existing_title, update_title, now_str))
                                    title_changed_count += 1

                                # Record ranking history
                                cursor.execute("""
                                    INSERT INTO rank_history
                                    (news_item_id, rank, crawl_time, created_at)
                                    VALUES (?, ?, ?, ?)
                                """, (existing_id, item.rank, data.crawl_time, now_str))

                                # Cập nhật existing record
                                cursor.execute("""
                                    UPDATE news_items SET
                                        title = ?,
                                        rank = ?,
                                        mobile_url = ?,
                                        last_crawl_time = ?,
                                        crawl_count = crawl_count + 1,
                                        updated_at = ?
                                    WHERE id = ?
                                """, (update_title, item.rank, item.mobile_url,
                                      data.crawl_time, now_str, existing_id))
                                updated_count += 1
                            else:
                                # Does not exist, insert new record (store standardized URL)
                                cursor.execute("""
                                    INSERT INTO news_items
                                    (title, platform_id, rank, url, mobile_url,
                                     first_crawl_time, last_crawl_time, crawl_count,
                                     created_at, updated_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                                """, (item.title, source_id, item.rank, normalized_url,
                                      item.mobile_url, data.crawl_time, data.crawl_time,
                                      now_str, now_str))
                                new_id = cursor.lastrowid
                                # Record initial ranking
                                cursor.execute("""
                                    INSERT INTO rank_history
                                    (news_item_id, rank, crawl_time, created_at)
                                    VALUES (?, ?, ?, ?)
                                """, (new_id, item.rank, data.crawl_time, now_str))
                                new_count += 1
                        else:
                            # If URL is empty, insert directly (no deduplication)
                            cursor.execute("""
                                INSERT INTO news_items
                                (title, platform_id, rank, url, mobile_url,
                                 first_crawl_time, last_crawl_time, crawl_count,
                                 created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                            """, (item.title, source_id, item.rank, "",
                                  item.mobile_url, data.crawl_time, data.crawl_time,
                                  now_str, now_str))
                            new_id = cursor.lastrowid
                            # Record initial ranking
                            cursor.execute("""
                                INSERT INTO rank_history
                                (news_item_id, rank, crawl_time, created_at)
                                VALUES (?, ?, ?, ?)
                            """, (new_id, item.rank, data.crawl_time, now_str))
                            new_count += 1

                    except sqlite3.Error as e:
                        print(f"{log_prefix} Failed to save news item [{item.title[:30]}...]: {e}")

            total_items = new_count + updated_count

            # ========================================
            # Drop-off detection: detect news that was on the list last time but not this time
            # ========================================
            off_list_count = 0

            # Get the last crawl time
            cursor.execute("""
                SELECT crawl_time FROM crawl_records
                WHERE crawl_time < ?
                ORDER BY crawl_time DESC
                LIMIT 1
            """, (data.crawl_time,))
            prev_record = cursor.fetchone()

            if prev_record:
                prev_crawl_time = prev_record[0]

                # For each successfully crawled platform, detect dropping off the ranking
                for source_id in success_sources:
                    # Get all standardized URLs for this platform in the current crawl
                    current_urls = set()
                    for item in data.items.get(source_id, []):
                        normalized_url = normalize_url(item.url, source_id) if item.url else ""
                        if normalized_url:
                            current_urls.add(normalized_url)

                    # Query news that were on the ranking last time (last_crawl_time = prev_crawl_time) but are not on the ranking this time
                    # These news are "dropping off the ranking for the first time" and need to be recorded
                    cursor.execute("""
                        SELECT id, url FROM news_items
                        WHERE platform_id = ?
                          AND last_crawl_time = ?
                          AND url != ''
                    """, (source_id, prev_crawl_time))

                    for row in cursor.fetchall():
                        news_id, url = row[0], row[1]
                        if url not in current_urls:
                            # Insert drop-off record (rank=0 indicates dropping off the ranking)
                            cursor.execute("""
                                INSERT INTO rank_history
                                (news_item_id, rank, crawl_time, created_at)
                                VALUES (?, 0, ?, ?)
                            """, (news_id, data.crawl_time, now_str))
                            off_list_count += 1

            # Record crawl information
            cursor.execute("""
                INSERT OR REPLACE INTO crawl_records
                (crawl_time, total_items, created_at)
                VALUES (?, ?, ?)
            """, (data.crawl_time, total_items, now_str))

            # Get the ID of the newly inserted crawl_record
            cursor.execute("""
                SELECT id FROM crawl_records WHERE crawl_time = ?
            """, (data.crawl_time,))
            record_row = cursor.fetchone()
            if record_row:
                crawl_record_id = record_row[0]

                # Record successful sources
                for source_id in success_sources:
                    cursor.execute("""
                        INSERT OR REPLACE INTO crawl_source_status
                        (crawl_record_id, platform_id, status)
                        VALUES (?, ?, 'success')
                    """, (crawl_record_id, source_id))

                # Record failed sources
                for failed_id in data.failed_ids:
                    # Ensure failed platforms are also in the platforms table
                    cursor.execute("""
                        INSERT OR IGNORE INTO platforms (id, name, updated_at)
                        VALUES (?, ?, ?)
                    """, (failed_id, failed_id, now_str))

                    cursor.execute("""
                        INSERT OR REPLACE INTO crawl_source_status
                        (crawl_record_id, platform_id, status)
                        VALUES (?, ?, 'failed')
                    """, (crawl_record_id, failed_id))

            conn.commit()

            return True, new_count, updated_count, title_changed_count, off_list_count

        except Exception as e:
            print(f"{log_prefix} Save failed: {e}")
            return False, 0, 0, 0, 0

    def _get_today_all_data_impl(self, date: Optional[str] = None) -> Optional[NewsData]:
        """
        Get all news data for the specified date (after merging)

        Args:
            date: Date string, defaults to today

        Returns:
            Merged news data
        """
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            # Get all news data (including id for querying ranking history)
            cursor.execute("""
                SELECT n.id, n.title, n.platform_id, p.name as platform_name,
                       n.rank, n.url, n.mobile_url,
                       n.first_crawl_time, n.last_crawl_time, n.crawl_count
                FROM news_items n
                LEFT JOIN platforms p ON n.platform_id = p.id
                ORDER BY n.platform_id, n.last_crawl_time
            """)

            rows = cursor.fetchall()
            if not rows:
                return None

            # Collect all news_item_id
            news_ids = [row[0] for row in rows]

            # Batch query ranking history (get time and rank simultaneously)
            # Filtering logic: only keep drop-off records (rank=0) before last_crawl_time
            # This avoids showing meaningless records after the news permanently drops off the ranking
            rank_history_map: Dict[int, List[int]] = {}
            rank_timeline_map: Dict[int, List[Dict[str, Any]]] = {}
            if news_ids:
                placeholders = ",".join("?" * len(news_ids))
                cursor.execute(f"""
                    SELECT rh.news_item_id, rh.rank, rh.crawl_time
                    FROM rank_history rh
                    JOIN news_items ni ON rh.news_item_id = ni.id
                    WHERE rh.news_item_id IN ({placeholders})
                      AND NOT (rh.rank = 0 AND rh.crawl_time > ni.last_crawl_time)
                    ORDER BY rh.news_item_id, rh.crawl_time
                """, news_ids)
                for rh_row in cursor.fetchall():
                    news_id, rank, crawl_time = rh_row[0], rh_row[1], rh_row[2]

                    if not crawl_time:
                        continue

                    # Build ranks list (deduplicated, excluding drop-off records rank=0)
                    if news_id not in rank_history_map:
                        rank_history_map[news_id] = []
                    if rank != 0 and rank not in rank_history_map[news_id]:
                        rank_history_map[news_id].append(rank)

                    # Build rank_timeline list (complete timeline, including drop-offs)
                    if news_id not in rank_timeline_map:
                        rank_timeline_map[news_id] = []
                    # Extract time part (HH:MM)
                    try:
                        time_part = crawl_time.split()[1][:5] if ' ' in crawl_time else crawl_time[:5]
                    except (IndexError, AttributeError):
                        time_part = "??:??"
                    rank_timeline_map[news_id].append({
                        "time": time_part,
                        "rank": rank if rank != 0 else None  # 0 converted to None indicates dropping off the ranking
                    })

            # Group by platform_id
            items: Dict[str, List[NewsItem]] = {}
            id_to_name: Dict[str, str] = {}
            crawl_date = self._format_date_folder(date)

            for row in rows:
                news_id = row[0]
                platform_id = row[2]
                title = row[1]
                platform_name = row[3] or platform_id

                id_to_name[platform_id] = platform_name

                if platform_id not in items:
                    items[platform_id] = []

                # Get ranking history, if none then use current rank
                ranks = rank_history_map.get(news_id, [row[4]])
                rank_timeline = rank_timeline_map.get(news_id, [])

                items[platform_id].append(NewsItem(
                    title=title,
                    source_id=platform_id,
                    source_name=platform_name,
                    rank=row[4],
                    url=row[5] or "",
                    mobile_url=row[6] or "",
                    crawl_time=row[8],  # last_crawl_time
                    ranks=ranks,
                    first_time=row[7],  # first_crawl_time
                    last_time=row[8],   # last_crawl_time
                    count=row[9],       # crawl_count
                    rank_timeline=rank_timeline,
                ))

            final_items = items

            # Get failed sources
            cursor.execute("""
                SELECT DISTINCT css.platform_id
                FROM crawl_source_status css
                JOIN crawl_records cr ON css.crawl_record_id = cr.id
                WHERE css.status = 'failed'
            """)
            failed_ids = [row[0] for row in cursor.fetchall()]

            # Get the latest crawl time
            cursor.execute("""
                SELECT crawl_time FROM crawl_records
                ORDER BY crawl_time DESC
                LIMIT 1
            """)

            time_row = cursor.fetchone()
            crawl_time = time_row[0] if time_row else self._format_time_filename()

            return NewsData(
                date=crawl_date,
                crawl_time=crawl_time,
                items=final_items,
                id_to_name=id_to_name,
                failed_ids=failed_ids,
            )

        except Exception as e:
            print(f"[Storage] Failed to read data: {e}")
            return None

    def _get_latest_crawl_data_impl(self, date: Optional[str] = None) -> Optional[NewsData]:
        """
        Get the data from the latest crawl

        Args:
            date: Date string, defaults to today

        Returns:
            Latest crawled news data
        """
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            # Get the latest crawl time
            cursor.execute("""
                SELECT crawl_time FROM crawl_records
                ORDER BY crawl_time DESC
                LIMIT 1
            """)

            time_row = cursor.fetchone()
            if not time_row:
                return None

            latest_time = time_row[0]

            # Get news data for this time (including id for querying ranking history)
            cursor.execute("""
                SELECT n.id, n.title, n.platform_id, p.name as platform_name,
                       n.rank, n.url, n.mobile_url,
                       n.first_crawl_time, n.last_crawl_time, n.crawl_count
                FROM news_items n
                LEFT JOIN platforms p ON n.platform_id = p.id
                WHERE n.last_crawl_time = ?
            """, (latest_time,))

            rows = cursor.fetchall()
            if not rows:
                return None

            # Collect all news_item_id
            news_ids = [row[0] for row in rows]

            # Batch query ranking history (get time and rank simultaneously)
            # Filtering logic: only keep drop-off records (rank=0) before last_crawl_time
            # This avoids showing meaningless records after the news permanently drops off the ranking
            rank_history_map: Dict[int, List[int]] = {}
            rank_timeline_map: Dict[int, List[Dict[str, Any]]] = {}
            if news_ids:
                placeholders = ",".join("?" * len(news_ids))
                cursor.execute(f"""
                    SELECT rh.news_item_id, rh.rank, rh.crawl_time
                    FROM rank_history rh
                    JOIN news_items ni ON rh.news_item_id = ni.id
                    WHERE rh.news_item_id IN ({placeholders})
                      AND NOT (rh.rank = 0 AND rh.crawl_time > ni.last_crawl_time)
                    ORDER BY rh.news_item_id, rh.crawl_time
                """, news_ids)
                for rh_row in cursor.fetchall():
                    news_id, rank, crawl_time = rh_row[0], rh_row[1], rh_row[2]

                    if not crawl_time:
                        continue

                    # Build ranks list (deduplicated, excluding drop-off records rank=0)
                    if news_id not in rank_history_map:
                        rank_history_map[news_id] = []
                    if rank != 0 and rank not in rank_history_map[news_id]:
                        rank_history_map[news_id].append(rank)

                    # Build rank_timeline list (complete timeline, including drop-offs)
                    if news_id not in rank_timeline_map:
                        rank_timeline_map[news_id] = []
                    # Extract time part (HH:MM)
                    try:
                        time_part = crawl_time.split()[1][:5] if ' ' in crawl_time else crawl_time[:5]
                    except (IndexError, AttributeError):
                        time_part = "??:??"
                    rank_timeline_map[news_id].append({
                        "time": time_part,
                        "rank": rank if rank != 0 else None  # 0 converted to None means unranked
                    })

            items: Dict[str, List[NewsItem]] = {}
            id_to_name: Dict[str, str] = {}
            crawl_date = self._format_date_folder(date)

            for row in rows:
                news_id = row[0]
                platform_id = row[2]
                platform_name = row[3] or platform_id
                id_to_name[platform_id] = platform_name

                if platform_id not in items:
                    items[platform_id] = []

                # Get ranking history, if none then use current ranking
                ranks = rank_history_map.get(news_id, [row[4]])
                rank_timeline = rank_timeline_map.get(news_id, [])

                items[platform_id].append(NewsItem(
                    title=row[1],
                    source_id=platform_id,
                    source_name=platform_name,
                    rank=row[4],
                    url=row[5] or "",
                    mobile_url=row[6] or "",
                    crawl_time=row[8],  # last_crawl_time
                    ranks=ranks,
                    first_time=row[7],  # first_crawl_time
                    last_time=row[8],   # last_crawl_time
                    count=row[9],       # crawl_count
                    rank_timeline=rank_timeline,
                ))

            # Get failed sources (for the latest scrape)
            cursor.execute("""
                SELECT css.platform_id
                FROM crawl_source_status css
                JOIN crawl_records cr ON css.crawl_record_id = cr.id
                WHERE cr.crawl_time = ? AND css.status = 'failed'
            """, (latest_time,))

            failed_ids = [row[0] for row in cursor.fetchall()]

            return NewsData(
                date=crawl_date,
                crawl_time=latest_time,
                items=items,
                id_to_name=id_to_name,
                failed_ids=failed_ids,
            )

        except Exception as e:
            print(f"[Storage] Failed to get latest data: {e}")
            return None

    def _detect_new_titles_impl(self, current_data: NewsData) -> Dict[str, Dict]:
        """
        Detect newly added titles

        This method compares currently scraped data with historical data to find newly added titles.
        Key logic: Only titles that have never appeared in historical batches are considered newly added.

        Args:
            current_data: Currently scraped data

        Returns:
            Newly added title data {source_id: {title: NewsItem}}
        """
        try:
            # Get historical data
            historical_data = self._get_today_all_data_impl(current_data.date)

            if not historical_data:
                # No historical data, everything is new
                new_titles = {}
                for source_id, news_list in current_data.items.items():
                    new_titles[source_id] = {item.title: item for item in news_list}
                return new_titles

            # Get current batch time
            current_time = current_data.crawl_time

            # Collect historical titles (titles with first_time < current_time)
            # This correctly handles the situation where the same title generates multiple records due to URL changes
            historical_titles: Dict[str, set] = {}
            for source_id, news_list in historical_data.items.items():
                historical_titles[source_id] = set()
                for item in news_list:
                    first_time = item.first_time or item.crawl_time
                    if first_time < current_time:
                        historical_titles[source_id].add(item.title)

            # Check if there is historical data
            has_historical_data = any(len(titles) > 0 for titles in historical_titles.values())
            if not has_historical_data:
                # First scrape, no concept of "newly added"
                return {}

            # Detect newly added
            new_titles = {}
            for source_id, news_list in current_data.items.items():
                hist_set = historical_titles.get(source_id, set())
                for item in news_list:
                    if item.title not in hist_set:
                        if source_id not in new_titles:
                            new_titles[source_id] = {}
                        new_titles[source_id][item.title] = item

            return new_titles

        except Exception as e:
            print(f"[Storage] Failed to detect new titles: {e}")
            return {}

    def _is_first_crawl_today_impl(self, date: Optional[str] = None) -> bool:
        """
        Check if it is the first scrape of the day

        Args:
            date: Date string, defaults to today

        Returns:
            Whether it is the first scrape
        """
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) as count FROM crawl_records
            """)

            row = cursor.fetchone()
            count = row[0] if row else 0

            # If there is only one or no record, consider it the first scrape
            return count <= 1

        except Exception as e:
            print(f"[Storage] Failed to check first scrape: {e}")
            return True

    def _get_crawl_times_impl(self, date: Optional[str] = None) -> List[str]:
        """
        Get a list of all scrape times for a specified date

        Args:
            date: Date string, defaults to today

        Returns:
            List of scrape times (sorted by time)
        """
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT crawl_time FROM crawl_records
                ORDER BY crawl_time
            """)

            rows = cursor.fetchall()
            return [row[0] for row in rows]

        except Exception as e:
            print(f"[Storage] Failed to get scrape time list: {e}")
            return []

    # ========================================
    # Time period execution records (scheduling system)
    # ========================================

    def _has_period_executed_impl(self, date_str: str, period_key: str, action: str) -> bool:
        """
        Check if a certain action for a specified time period has been executed today

        Args:
            date_str: Date string YYYY-MM-DD
            period_key: Time period key
            action: Action type (analyze / push)

        Returns:
            Whether it has been executed
        """
        try:
            conn = self._get_connection(date_str)
            cursor = conn.cursor()

            # First check if the table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='period_executions'
            """)
            if not cursor.fetchone():
                return False

            cursor.execute("""
                SELECT 1 FROM period_executions
                WHERE execution_date = ? AND period_key = ? AND action = ?
            """, (date_str, period_key, action))

            return cursor.fetchone() is not None

        except Exception as e:
            print(f"[Storage] Failed to check time period execution record: {e}")
            return False

    def _record_period_execution_impl(self, date_str: str, period_key: str, action: str) -> bool:
        """
        Record the action execution for a time period

        Args:
            date_str: Date string YYYY-MM-DD
            period_key: Time period key
            action: Action type (analyze / push)

        Returns:
            Whether recording was successful
        """
        try:
            conn = self._get_connection(date_str)
            cursor = conn.cursor()

            # Ensure the table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS period_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_date TEXT NOT NULL,
                    period_key TEXT NOT NULL,
                    action TEXT NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(execution_date, period_key, action)
                )
            """)

            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT OR IGNORE INTO period_executions (execution_date, period_key, action, executed_at)
                VALUES (?, ?, ?, ?)
            """, (date_str, period_key, action, now_str))

            conn.commit()
            return True

        except Exception as e:
            print(f"[Storage] Failed to record time period execution: {e}")
            return False

    # ========================================
    # RSS data storage
    # ========================================

    def _save_rss_data_impl(self, data: RSSData, log_prefix: str = "[Storage]") -> tuple[bool, int, int]:
        """
        Save RSS data to SQLite (using URL as unique identifier)

        Args:
            data: RSS data
            log_prefix: Log prefix

        Returns:
            (success, new_count, updated_count)
        """
        try:
            conn = self._get_connection(data.date, db_type="rss")
            cursor = conn.cursor()

            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")

            # Sync RSS feed info to rss_feeds table
            for feed_id, feed_name in data.id_to_name.items():
                cursor.execute("""
                    INSERT INTO rss_feeds (id, name, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        updated_at = excluded.updated_at
                """, (feed_id, feed_name, now_str))

            # Statistics counter
            new_count = 0
            updated_count = 0

            for feed_id, rss_list in data.items.items():
                for item in rss_list:
                    try:
                        item_guid = getattr(item, "guid", "") or ""
                        existing = None

                        # Deduplication priority: guid > url
                        if item_guid:
                            cursor.execute("""
                                SELECT id, title FROM rss_items
                                WHERE guid = ? AND feed_id = ?
                            """, (item_guid, feed_id))
                            existing = cursor.fetchone()

                        if not existing and item.url:
                            cursor.execute("""
                                SELECT id, title FROM rss_items
                                WHERE url = ? AND feed_id = ?
                            """, (item.url, feed_id))
                            existing = cursor.fetchone()

                        if existing:
                            existing_id = existing[0]
                            existing_title = existing[1]
                            update_title = item.title
                            if (update_title and update_title.strip().startswith(("http://", "https://", "//"))
                                    and existing_title and not existing_title.strip().startswith(("http://", "https://", "//"))):
                                update_title = existing_title
                            cursor.execute("""
                                UPDATE rss_items SET
                                    title = ?,
                                    url = CASE WHEN ? != '' THEN ? ELSE url END,
                                    guid = CASE WHEN ? != '' THEN ? ELSE guid END,
                                    published_at = ?,
                                    summary = ?,
                                    author = ?,
                                    last_crawl_time = ?,
                                    crawl_count = crawl_count + 1,
                                    updated_at = ?
                                WHERE id = ?
                            """, (update_title,
                                  item.url, item.url,
                                  item_guid, item_guid,
                                  item.published_at, item.summary,
                                  item.author, data.crawl_time, now_str, existing_id))
                            updated_count += 1
                        elif item.url or item_guid:
                            try:
                                cursor.execute("""
                                    INSERT INTO rss_items
                                    (title, feed_id, url, guid, published_at, summary, author,
                                     first_crawl_time, last_crawl_time, crawl_count,
                                     created_at, updated_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                                """, (item.title, feed_id, item.url, item_guid,
                                      item.published_at, item.summary, item.author,
                                      data.crawl_time, data.crawl_time, now_str, now_str))
                                new_count += 1
                            except sqlite3.IntegrityError:
                                pass

                    except sqlite3.Error as e:
                        print(f"{log_prefix} Failed to save RSS item [{item.title[:30]}...]: {e}")

            total_items = new_count + updated_count

            # Record crawl info
            cursor.execute("""
                INSERT OR REPLACE INTO rss_crawl_records
                (crawl_time, total_items, created_at)
                VALUES (?, ?, ?)
            """, (data.crawl_time, total_items, now_str))

            # Record crawl status
            cursor.execute("""
                SELECT id FROM rss_crawl_records WHERE crawl_time = ?
            """, (data.crawl_time,))
            record_row = cursor.fetchone()
            if record_row:
                crawl_record_id = record_row[0]

                # Record successful feeds
                for feed_id in data.items.keys():
                    cursor.execute("""
                        INSERT OR REPLACE INTO rss_crawl_status
                        (crawl_record_id, feed_id, status)
                        VALUES (?, ?, 'success')
                    """, (crawl_record_id, feed_id))

                # Record failed feeds
                for failed_id in data.failed_ids:
                    cursor.execute("""
                        INSERT OR IGNORE INTO rss_feeds (id, name, updated_at)
                        VALUES (?, ?, ?)
                    """, (failed_id, failed_id, now_str))

                    cursor.execute("""
                        INSERT OR REPLACE INTO rss_crawl_status
                        (crawl_record_id, feed_id, status)
                        VALUES (?, ?, 'failed')
                    """, (crawl_record_id, failed_id))

            conn.commit()

            return True, new_count, updated_count

        except Exception as e:
            print(f"{log_prefix} Failed to save RSS data: {e}")
            return False, 0, 0

    def _get_rss_data_impl(self, date: Optional[str] = None) -> Optional[RSSData]:
        """
        Get all RSS data for a specified date

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            RSSData object, returns None if no data
        """
        try:
            conn = self._get_connection(date, db_type="rss")
            cursor = conn.cursor()

            # Get all RSS data
            cursor.execute("""
                SELECT i.id, i.title, i.feed_id, f.name as feed_name,
                       i.url, i.published_at, i.summary, i.author,
                       i.first_crawl_time, i.last_crawl_time, i.crawl_count
                FROM rss_items i
                LEFT JOIN rss_feeds f ON i.feed_id = f.id
                ORDER BY i.published_at DESC
            """)

            rows = cursor.fetchall()
            if not rows:
                return None

            items: Dict[str, List[RSSItem]] = {}
            id_to_name: Dict[str, str] = {}
            crawl_date = self._format_date_folder(date)

            for row in rows:
                feed_id = row[2]
                feed_name = row[3] or feed_id

                id_to_name[feed_id] = feed_name

                if feed_id not in items:
                    items[feed_id] = []

                items[feed_id].append(RSSItem(
                    title=row[1],
                    feed_id=feed_id,
                    feed_name=feed_name,
                    url=row[4] or "",
                    published_at=row[5] or "",
                    summary=row[6] or "",
                    author=row[7] or "",
                    crawl_time=row[9],
                    first_time=row[8],
                    last_time=row[9],
                    count=row[10],
                ))

            # Get the latest crawl time
            cursor.execute("""
                SELECT crawl_time FROM rss_crawl_records
                ORDER BY crawl_time DESC
                LIMIT 1
            """)
            time_row = cursor.fetchone()
            crawl_time = time_row[0] if time_row else self._format_time_filename()

            # Get failed feeds
            cursor.execute("""
                SELECT DISTINCT cs.feed_id
                FROM rss_crawl_status cs
                JOIN rss_crawl_records cr ON cs.crawl_record_id = cr.id
                WHERE cs.status = 'failed'
            """)
            failed_ids = [row[0] for row in cursor.fetchall()]

            return RSSData(
                date=crawl_date,
                crawl_time=crawl_time,
                items=items,
                id_to_name=id_to_name,
                failed_ids=failed_ids,
            )

        except Exception as e:
            print(f"[Storage] Failed to read RSS data: {e}")
            return None

    def _detect_new_rss_items_impl(self, current_data: RSSData) -> Dict[str, List[RSSItem]]:
        """
        Detect new RSS items (incremental mode)

        This method compares current crawl data with historical data to find new RSS items.
        Key logic: Only URLs that have never appeared in historical batches are considered new.

        Args:
            current_data: Currently crawled RSS data

        Returns:
            New RSS items {feed_id: [RSSItem, ...]}
        """
        try:
            # Get historical data
            historical_data = self._get_rss_data_impl(current_data.date)

            if not historical_data:
                # No historical data, all are new
                return current_data.items.copy()

            # Get current batch time
            current_time = current_data.crawl_time

            # Collect historical URLs (items with first_time < current_time)
            historical_urls: Dict[str, set] = {}
            for feed_id, rss_list in historical_data.items.items():
                historical_urls[feed_id] = set()
                for item in rss_list:
                    first_time = item.first_time or item.crawl_time
                    if first_time < current_time:
                        if item.url:
                            historical_urls[feed_id].add(item.url)

            # Check if there is historical data
            has_historical_data = any(len(urls) > 0 for urls in historical_urls.values())
            if not has_historical_data:
                # First crawl, no concept of "new"
                return {}

            # Detect new
            new_items: Dict[str, List[RSSItem]] = {}
            for feed_id, rss_list in current_data.items.items():
                hist_set = historical_urls.get(feed_id, set())
                for item in rss_list:
                    # Determine if new by URL
                    if item.url and item.url not in hist_set:
                        if feed_id not in new_items:
                            new_items[feed_id] = []
                        new_items[feed_id].append(item)

            return new_items

        except Exception as e:
            print(f"[Storage] Failed to detect new RSS items: {e}")
            return {}

    def _get_latest_rss_data_impl(self, date: Optional[str] = None) -> Optional[RSSData]:
        """
        Get the latest crawled RSS data (Bảng xếp hạng hiện tại mode)

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            The latest fetched RSS data, returns None if there is no data
        """
        try:
            conn = self._get_connection(date, db_type="rss")
            cursor = conn.cursor()

            # Get the latest fetch time
            cursor.execute("""
                SELECT crawl_time FROM rss_crawl_records
                ORDER BY crawl_time DESC
                LIMIT 1
            """)

            time_row = cursor.fetchone()
            if not time_row:
                return None

            latest_time = time_row[0]

            # Get the RSS data for this time
            cursor.execute("""
                SELECT i.id, i.title, i.feed_id, f.name as feed_name,
                       i.url, i.published_at, i.summary, i.author,
                       i.first_crawl_time, i.last_crawl_time, i.crawl_count
                FROM rss_items i
                LEFT JOIN rss_feeds f ON i.feed_id = f.id
                WHERE i.last_crawl_time = ?
                ORDER BY i.published_at DESC
            """, (latest_time,))

            rows = cursor.fetchall()
            if not rows:
                return None

            items: Dict[str, List[RSSItem]] = {}
            id_to_name: Dict[str, str] = {}
            crawl_date = self._format_date_folder(date)

            for row in rows:
                feed_id = row[2]
                feed_name = row[3] or feed_id

                id_to_name[feed_id] = feed_name

                if feed_id not in items:
                    items[feed_id] = []

                items[feed_id].append(RSSItem(
                    title=row[1],
                    feed_id=feed_id,
                    feed_name=feed_name,
                    url=row[4] or "",
                    published_at=row[5] or "",
                    summary=row[6] or "",
                    author=row[7] or "",
                    crawl_time=row[9],
                    first_time=row[8],
                    last_time=row[9],
                    count=row[10],
                ))

            # Get failed sources (for the latest fetch)
            cursor.execute("""
                SELECT cs.feed_id
                FROM rss_crawl_status cs
                JOIN rss_crawl_records cr ON cs.crawl_record_id = cr.id
                WHERE cr.crawl_time = ? AND cs.status = 'failed'
            """, (latest_time,))

            failed_ids = [row[0] for row in cursor.fetchall()]

            return RSSData(
                date=crawl_date,
                crawl_time=latest_time,
                items=items,
                id_to_name=id_to_name,
                failed_ids=failed_ids,
            )

        except Exception as e:
            print(f"[Storage] Failed to get the latest RSS data: {e}")
            return None

    # ========================================
    # AI Smart Filtering - Tag Management
    # ========================================

    def _get_active_tags_impl(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> List[Dict[str, Any]]:
        """Get the list of active tags for the specified interest file"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, tag, description, version, prompt_hash, priority
                FROM ai_filter_tags
                WHERE status = 'active' AND interests_file = ?
                ORDER BY priority ASC, id ASC
            """, (interests_file,))

            return [
                {
                    "id": row[0], "tag": row[1], "description": row[2],
                    "version": row[3], "prompt_hash": row[4], "priority": row[5],
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[AI Filtering] Failed to get tags: {e}")
            return []

    def _get_latest_prompt_hash_impl(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> Optional[str]:
        """Get the prompt_hash of the latest version tags for the specified interest file"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT prompt_hash FROM ai_filter_tags
                WHERE status = 'active' AND interests_file = ?
                ORDER BY version DESC
                LIMIT 1
            """, (interests_file,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"[AI Filtering] Failed to get prompt_hash: {e}")
            return None

    def _get_latest_tag_version_impl(self, date: Optional[str] = None) -> int:
        """Get the latest version number"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT MAX(version) FROM ai_filter_tags
            """)
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else 0
        except Exception as e:
            print(f"[AI Filtering] Failed to get version number: {e}")
            return 0

    def _deprecate_all_tags_impl(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> int:
        """Mark the active tags and associated classification results of the specified interest file as deprecated"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()
            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")

            # Get the active tag ids for this interest file
            cursor.execute(
                "SELECT id FROM ai_filter_tags WHERE status = 'active' AND interests_file = ?",
                (interests_file,)
            )
            tag_ids = [row[0] for row in cursor.fetchall()]

            if not tag_ids:
                return 0

            # Deprecate tags
            placeholders = ",".join("?" * len(tag_ids))
            cursor.execute(f"""
                UPDATE ai_filter_tags
                SET status = 'deprecated', deprecated_at = ?
                WHERE id IN ({placeholders})
            """, [now_str] + tag_ids)
            tag_count = cursor.rowcount

            # Deprecate associated classification results
            placeholders = ",".join("?" * len(tag_ids))
            cursor.execute(f"""
                UPDATE ai_filter_results
                SET status = 'deprecated', deprecated_at = ?
                WHERE tag_id IN ({placeholders}) AND status = 'active'
            """, [now_str] + tag_ids)

            conn.commit()
            print(f"[AI Filtering] Deprecated {tag_count} tags and associated classification results")
            return tag_count
        except Exception as e:
            print(f"[AI Filtering] Failed to deprecate tags: {e}")
            return 0

    def _save_tags_impl(
        self, date: Optional[str], tags: List[Dict], version: int, prompt_hash: str,
        interests_file: str = "ai_interests.txt"
    ) -> int:
        """Save newly extracted tags"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()
            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")

            count = 0
            for idx, tag_data in enumerate(tags, start=1):
                priority = tag_data.get("priority", idx)
                try:
                    priority = int(priority)
                except (TypeError, ValueError):
                    priority = idx
                cursor.execute("""
                    INSERT INTO ai_filter_tags
                    (tag, description, priority, version, prompt_hash, interests_file, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tag_data["tag"],
                    tag_data.get("description", ""),
                    priority,
                    version,
                    prompt_hash,
                    interests_file,
                    now_str,
                ))
                count += 1

            conn.commit()
            return count
        except Exception as e:
            print(f"[AI Filtering] Failed to save tags: {e}")
            return 0

    def _deprecate_specific_tags_impl(
        self, date: Optional[str], tag_ids: List[int]
    ) -> int:
        """Deprecate the tag with the specified ID and its associated classification results (used during Cập nhật thêm)"""
        if not tag_ids:
            return 0
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()
            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")

            placeholders = ",".join("?" * len(tag_ids))

            cursor.execute(f"""
                UPDATE ai_filter_tags
                SET status = 'deprecated', deprecated_at = ?
                WHERE id IN ({placeholders})
            """, [now_str] + tag_ids)
            tag_count = cursor.rowcount

            cursor.execute(f"""
                UPDATE ai_filter_results
                SET status = 'deprecated', deprecated_at = ?
                WHERE tag_id IN ({placeholders}) AND status = 'active'
            """, [now_str] + tag_ids)

            conn.commit()
            return tag_count
        except Exception as e:
            print(f"[AI Filtering] Failed to deprecate the specified tag: {e}")
            return 0

    def _update_tags_hash_impl(
        self, date: Optional[str], interests_file: str, new_hash: str
    ) -> int:
        """Cập nhật the prompt_hash of all active tags for the specified interest file (used during Cập nhật thêm)"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE ai_filter_tags
                SET prompt_hash = ?
                WHERE interests_file = ? AND status = 'active'
            """, (new_hash, interests_file))
            count = cursor.rowcount

            conn.commit()
            return count
        except Exception as e:
            print(f"[AI Filtering] Failed to Cập nhật tag hash: {e}")
            return 0

    # ========================================
    # AI Smart Filtering - Classification Result Management
    # ========================================

    def _update_tag_descriptions_impl(
        self, date: Optional[str], tag_updates: List[Dict],
        interests_file: str = "ai_interests.txt"
    ) -> int:
        """Match by tag name, Cập nhật the description field of active tags"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            count = 0
            for t in tag_updates:
                tag_name = t.get("tag", "")
                description = t.get("description", "")
                if not tag_name:
                    continue
                cursor.execute("""
                    UPDATE ai_filter_tags
                    SET description = ?
                    WHERE tag = ? AND interests_file = ? AND status = 'active'
                """, (description, tag_name, interests_file))
                count += cursor.rowcount

            conn.commit()
            return count
        except Exception as e:
            print(f"[AI Filtering] Failed to Cập nhật tag description: {e}")
            return 0

    def _update_tag_priorities_impl(
        self, date: Optional[str], tag_priorities: List[Dict],
        interests_file: str = "ai_interests.txt"
    ) -> int:
        """Match by tag name, Cập nhật the priority field of active tags"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            count = 0
            for t in tag_priorities:
                tag_name = t.get("tag", "")
                priority = t.get("priority")
                if not tag_name:
                    continue
                try:
                    priority = int(priority)
                except (TypeError, ValueError):
                    continue
                cursor.execute("""
                    UPDATE ai_filter_tags
                    SET priority = ?
                    WHERE tag = ? AND interests_file = ? AND status = 'active'
                """, (priority, tag_name, interests_file))
                count += cursor.rowcount

            conn.commit()
            return count
        except Exception as e:
            print(f"[AI Filtering] Failed to Cập nhật tag priority: {e}")
            return 0

    # ========================================
    # AI Smart Filtering - Analyzed News Tracking
    # ========================================

    def _save_analyzed_news_impl(
        self, date: Optional[str], news_ids: List[int], source_type: str,
        interests_file: str, prompt_hash: str, matched_ids: set
    ) -> int:
        """Batch record analyzed news (record both matched and unmatched)"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()
            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")

            count = 0
            for nid in news_ids:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO ai_filter_analyzed_news
                        (news_item_id, source_type, interests_file, prompt_hash, matched, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        nid, source_type, interests_file, prompt_hash,
                        1 if nid in matched_ids else 0,
                        now_str,
                    ))
                    count += 1
                except Exception:
                    pass

            conn.commit()
            return count
        except Exception as e:
            print(f"[AI Filtering] Failed to save analyzed records: {e}")
            return 0

    def _get_analyzed_news_ids_impl(
        self, date: Optional[str] = None, source_type: str = "hotlist",
        interests_file: str = "ai_interests.txt"
    ) -> set:
        """Get the set of analyzed news IDs (used for deduplication)"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT news_item_id FROM ai_filter_analyzed_news
                WHERE source_type = ? AND interests_file = ?
            """, (source_type, interests_file))

            return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            print(f"[AI Filtering] Failed to get analyzed IDs: {e}")
            return set()

    def _clear_analyzed_news_impl(
        self, date: Optional[str] = None, interests_file: str = "ai_interests.txt"
    ) -> int:
        """Clear all analyzed records for the specified interest file (used during full reclassification)"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM ai_filter_analyzed_news
                WHERE interests_file = ?
            """, (interests_file,))

            count = cursor.rowcount
            conn.commit()
            return count
        except Exception as e:
            print(f"[AI Filtering] Failed to clear analyzed records: {e}")
            return 0

    def _clear_unmatched_analyzed_news_impl(
        self, date: Optional[str] = None, interests_file: str = "ai_interests.txt"
    ) -> int:
        """Clear unmatched analyzed records, allowing these news to have a chance to be re-analyzed by new tags"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM ai_filter_analyzed_news
                WHERE interests_file = ? AND matched = 0
            """, (interests_file,))

            count = cursor.rowcount
            conn.commit()
            return count
        except Exception as e:
            print(f"[AI Filtering] Failed to clear unmatched records: {e}")
            return 0

    # ========================================
    # AI Smart Filtering - Classification Result Management (Original)
    # ========================================

    def _save_filter_results_impl(
        self, date: Optional[str], results: List[Dict]
    ) -> int:
        """Batch save classification results"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()
            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")

            count = 0
            for r in results:
                try:
                    cursor.execute("""
                        INSERT INTO ai_filter_results
                        (news_item_id, source_type, tag_id, relevance_score, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        r["news_item_id"],
                        r.get("source_type", "hotlist"),
                        r["tag_id"],
                        r.get("relevance_score", 0.0),
                        now_str,
                    ))
                    count += 1
                except sqlite3.IntegrityError:
                    pass  # Duplicate record, skip

            conn.commit()
            return count
        except Exception as e:
            print(f"[AI Filter] Failed to save classification result: {e}")
            return 0

    def _get_active_filter_results_impl(self, date: Optional[str] = None, interests_file: str = "ai_interests.txt") -> List[Dict[str, Any]]:
        """Get the active classification results of the specified interest file, JOIN news_items to get news details"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            # Trending results
            cursor.execute("""
                SELECT
                    r.news_item_id, r.source_type, r.tag_id, r.relevance_score,
                    t.tag, t.description as tag_description, t.priority,
                    n.title, n.platform_id as source_id, p.name as source_name,
                    n.url, n.mobile_url, n.rank,
                    n.first_crawl_time, n.last_crawl_time, n.crawl_count
                FROM ai_filter_results r
                JOIN ai_filter_tags t ON r.tag_id = t.id
                JOIN news_items n ON r.news_item_id = n.id
                LEFT JOIN platforms p ON n.platform_id = p.id
                WHERE r.status = 'active' AND r.source_type = 'hotlist'
                    AND t.status = 'active' AND t.interests_file = ?
                ORDER BY t.priority ASC, t.id ASC, r.relevance_score DESC
            """, (interests_file,))

            results = []
            hotlist_news_ids = []
            for row in cursor.fetchall():
                results.append({
                    "news_item_id": row[0], "source_type": row[1],
                    "tag_id": row[2], "relevance_score": row[3],
                    "tag": row[4], "tag_description": row[5], "tag_priority": row[6],
                    "title": row[7], "source_id": row[8],
                    "source_name": row[9] or row[8],
                    "url": row[10] or "", "mobile_url": row[11] or "",
                    "rank": row[12],
                    "first_time": row[13], "last_time": row[14],
                    "count": row[15],
                })
                hotlist_news_ids.append(row[0])

            # Batch query ranking history (Trending)
            ranks_map: Dict[int, List[int]] = {}
            rank_timeline_map: Dict[int, List[Dict[str, Any]]] = {}
            if hotlist_news_ids:
                unique_ids = list(set(hotlist_news_ids))
                placeholders = ",".join("?" * len(unique_ids))
                cursor.execute(f"""
                    SELECT news_item_id, rank, crawl_time FROM rank_history
                    WHERE news_item_id IN ({placeholders})
                    ORDER BY news_item_id, crawl_time
                """, unique_ids)
                for rh_row in cursor.fetchall():
                    nid, rank, crawl_time = rh_row[0], rh_row[1], rh_row[2]

                    if not crawl_time:
                        continue

                    if nid not in ranks_map:
                        ranks_map[nid] = []
                    if rank != 0 and rank not in ranks_map[nid]:
                        ranks_map[nid].append(rank)

                    if nid not in rank_timeline_map:
                        rank_timeline_map[nid] = []
                    try:
                        time_part = crawl_time.split()[1][:5] if ' ' in crawl_time else crawl_time[:5]
                    except (IndexError, AttributeError):
                        time_part = "??:??"
                    rank_timeline_map[nid].append({
                        "time": time_part,
                        "rank": rank if rank != 0 else None
                    })

            for item in results:
                item["ranks"] = ranks_map.get(item["news_item_id"], [item["rank"]])
                item["rank_timeline"] = rank_timeline_map.get(item["news_item_id"], [])

            # RSS results (if rss database exists)
            try:
                rss_conn = self._get_connection(date, db_type="rss")
                rss_cursor = rss_conn.cursor()

                # Get classification result IDs of rss type from news database
                cursor.execute("""
                    SELECT r.news_item_id, r.tag_id, r.relevance_score,
                           t.tag, t.description, t.priority
                    FROM ai_filter_results r
                    JOIN ai_filter_tags t ON r.tag_id = t.id
                    WHERE r.status = 'active' AND r.source_type = 'rss'
                        AND t.status = 'active' AND t.interests_file = ?
                    ORDER BY t.priority ASC, t.id ASC, r.relevance_score DESC
                """, (interests_file,))

                rss_filter_rows = cursor.fetchall()
                if rss_filter_rows:
                    rss_ids = [row[0] for row in rss_filter_rows]
                    placeholders = ",".join("?" * len(rss_ids))
                    rss_cursor.execute(f"""
                        SELECT i.id, i.title, i.feed_id, f.name as feed_name,
                               i.url, i.published_at
                        FROM rss_items i
                        LEFT JOIN rss_feeds f ON i.feed_id = f.id
                        WHERE i.id IN ({placeholders})
                    """, rss_ids)

                    rss_info = {row[0]: row for row in rss_cursor.fetchall()}

                    for fr_row in rss_filter_rows:
                        rss_id = fr_row[0]
                        info = rss_info.get(rss_id)
                        if info:
                            results.append({
                                "news_item_id": rss_id,
                                "source_type": "rss",
                                "tag_id": fr_row[1],
                                "relevance_score": fr_row[2],
                                "tag": fr_row[3],
                                "tag_description": fr_row[4],
                                "tag_priority": fr_row[5],
                                "title": info[1],
                                "source_id": info[2],
                                "source_name": info[3] or info[2],
                                "url": info[4] or "",
                                "mobile_url": "",
                                "rank": 0,
                                "ranks": [],
                                "first_time": info[5] or "",
                                "last_time": info[5] or "",
                                "count": 1,
                            })
            except Exception:
                pass  # Silently skip when RSS database does not exist

            return results
        except Exception as e:
            print(f"[AI Filter] Failed to get classification results: {e}")
            return []

    def _get_all_news_ids_impl(self, date: Optional[str] = None) -> List[Dict]:
        """Get the id and title of all news for the day (used for AI filter classification)"""
        try:
            conn = self._get_connection(date)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT n.id, n.title, n.platform_id, p.name as platform_name
                FROM news_items n
                LEFT JOIN platforms p ON n.platform_id = p.id
                ORDER BY n.id
            """)

            return [
                {
                    "id": row[0], "title": row[1],
                    "source_id": row[2], "source_name": row[3] or row[2],
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[AI Filter] Failed to get news list: {e}")
            return []

    def _get_all_rss_ids_impl(self, date: Optional[str] = None) -> List[Dict]:
        """Get the id and title of all RSS items for the day (used for AI filter classification)"""
        try:
            conn = self._get_connection(date, db_type="rss")
            cursor = conn.cursor()

            cursor.execute("""
                SELECT i.id, i.title, i.feed_id, f.name as feed_name, i.published_at
                FROM rss_items i
                LEFT JOIN rss_feeds f ON i.feed_id = f.id
                ORDER BY i.id
            """)

            return [
                {
                    "id": row[0], "title": row[1],
                    "source_id": row[2], "source_name": row[3] or row[2],
                    "published_at": row[4] or "",
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[AI Filter] Failed to get RSS list: {e}")
            return []
