# coding=utf-8
"""
Local storage backend - SQLite + TXT/HTML

Use SQLite as the main storage, supporting optional TXT snapshots and HTML reports
"""

import sqlite3
import shutil
import pytz
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from trendradar.storage.base import StorageBackend, NewsData, RSSItem, RSSData
from trendradar.storage.sqlite_mixin import SQLiteStorageMixin
from trendradar.utils.time import (
    DEFAULT_TIMEZONE,
    get_configured_time,
    format_date_folder,
    format_time_filename,
)


class LocalStorageBackend(SQLiteStorageMixin, StorageBackend):
    """
    Local storage backend

    Use SQLite database to store news data, supporting:
    - SQLite database files organized by date
    - Optional TXT snapshots (for debugging)
    - HTML report generation
    """

    def __init__(
        self,
        data_dir: str = "output",
        enable_txt: bool = True,
        enable_html: bool = True,
        timezone: str = DEFAULT_TIMEZONE,
    ):
        """
        Initialize local storage backend

        Args:
            data_dir: Data directory path
            enable_txt: Whether to enable TXT snapshots
            enable_html: Whether to enable HTML reports
            timezone: Timezone configuration
        """
        self.data_dir = Path(data_dir)
        self.enable_txt = enable_txt
        self.enable_html = enable_html
        self.timezone = timezone
        self._db_connections: Dict[str, sqlite3.Connection] = {}

    @property
    def backend_name(self) -> str:
        return "local"

    @property
    def supports_txt(self) -> bool:
        return self.enable_txt

    # ========================================
    # SQLiteStorageMixin abstract method implementation
    # ========================================

    def _get_configured_time(self) -> datetime:
        """Get the current time in the configured timezone"""
        return get_configured_time(self.timezone)

    def _format_date_folder(self, date: Optional[str] = None) -> str:
        """Format date folder name (ISO format: YYYY-MM-DD)"""
        return format_date_folder(date, self.timezone)

    def _format_time_filename(self) -> str:
        """Format time file name (Format: HH-MM)"""
        return format_time_filename(self.timezone)

    def _get_db_path(self, date: Optional[str] = None, db_type: str = "news") -> Path:
        """
        Get SQLite database path

        New structure (flat): output/{type}/{date}.db
        - output/news/2025-12-28.db
        - output/rss/2025-12-28.db

        Args:
            date: Date string
            db_type: Database type ("news" or "rss")

        Returns:
            Database file path
        """
        date_str = self._format_date_folder(date)
        db_dir = self.data_dir / db_type
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / f"{date_str}.db"

    def _get_connection(self, date: Optional[str] = None, db_type: str = "news") -> sqlite3.Connection:
        """
        Get database connection (with cache)

        Args:
            date: Date string
            db_type: Database type ("news" or "rss")

        Returns:
            Database connection
        """
        db_path = str(self._get_db_path(date, db_type))

        if db_path not in self._db_connections:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            self._init_tables(conn, db_type)
            self._db_connections[db_path] = conn

        return self._db_connections[db_path]

    # ========================================
    # StorageBackend interface implementation (delegated to mixin)
    # ========================================

    def save_news_data(self, data: NewsData) -> bool:
        """Save news data to SQLite"""
        db_path = self._get_db_path(data.date)
        if not db_path.exists():
            # Ensure directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)

        success, new_count, updated_count, title_changed_count, off_list_count = \
            self._save_news_data_impl(data, "[Local Storage]")

        if success:
            # Output detailed storage statistics log
            log_parts = [f"[Local Storage] Processing complete: added {new_count} items"]
            if updated_count > 0:
                log_parts.append(f"Cập nhật {updated_count} items")
            if title_changed_count > 0:
                log_parts.append(f"Title changed {title_changed_count} items")
            if off_list_count > 0:
                log_parts.append(f"Off list {off_list_count} items")
            print("，".join(log_parts))

        return success

    def get_today_all_data(self, date: Optional[str] = None) -> Optional[NewsData]:
        """Get all news data for a specified date (after merging)"""
        db_path = self._get_db_path(date)
        if not db_path.exists():
            return None
        return self._get_today_all_data_impl(date)

    def get_latest_crawl_data(self, date: Optional[str] = None) -> Optional[NewsData]:
        """Get the data from the latest scrape"""
        db_path = self._get_db_path(date)
        if not db_path.exists():
            return None
        return self._get_latest_crawl_data_impl(date)

    def detect_new_titles(self, current_data: NewsData) -> Dict[str, Dict]:
        """Detect newly added titles"""
        return self._detect_new_titles_impl(current_data)

    def is_first_crawl_today(self, date: Optional[str] = None) -> bool:
        """Check if it is the first scrape of the day"""
        db_path = self._get_db_path(date)
        if not db_path.exists():
            return True
        return self._is_first_crawl_today_impl(date)

    def get_crawl_times(self, date: Optional[str] = None) -> List[str]:
        """Get a list of all scrape times for a specified date"""
        db_path = self._get_db_path(date)
        if not db_path.exists():
            return []
        return self._get_crawl_times_impl(date)

    # ========================================
    # Time period execution records (scheduling system)
    # ========================================

    def has_period_executed(self, date_str: str, period_key: str, action: str) -> bool:
        """Check if a specific action in the specified time period has been executed"""
        return self._has_period_executed_impl(date_str, period_key, action)

    def record_period_execution(self, date_str: str, period_key: str, action: str) -> bool:
        """Record the execution of an action for a time period"""
        success = self._record_period_execution_impl(date_str, period_key, action)
        if success:
            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[Local Storage] Time period execution record saved: {period_key}/{action} at {now_str}")
        return success

    # ========================================
    # RSS data storage method
    # ========================================

    def save_rss_data(self, data: RSSData) -> bool:
        """Save RSS data to SQLite"""
        success, new_count, updated_count = self._save_rss_data_impl(data, "[Local Storage]")

        if success:
            # Output statistics log
            log_parts = [f"[Local Storage] RSS processing completed: {new_count} new items"]
            if updated_count > 0:
                log_parts.append(f"Cập nhật {updated_count} items")
            print("，".join(log_parts))

        return success

    def get_rss_data(self, date: Optional[str] = None) -> Optional[RSSData]:
        """Get all RSS data for a specified date"""
        return self._get_rss_data_impl(date)

    def detect_new_rss_items(self, current_data: RSSData) -> Dict[str, List[RSSItem]]:
        """Detect newly added RSS items"""
        return self._detect_new_rss_items_impl(current_data)

    def get_latest_rss_data(self, date: Optional[str] = None) -> Optional[RSSData]:
        """Get the most recently fetched RSS data"""
        db_path = self._get_db_path(date, db_type="rss")
        if not db_path.exists():
            return None
        return self._get_latest_rss_data_impl(date)

    # ========================================
    # AI intelligent filtering
    # ========================================

    def get_active_ai_filter_tags(self, date=None, interests_file="ai_interests.txt"):
        return self._get_active_tags_impl(date, interests_file)

    def get_latest_prompt_hash(self, date=None, interests_file="ai_interests.txt"):
        return self._get_latest_prompt_hash_impl(date, interests_file)

    def get_latest_ai_filter_tag_version(self, date=None):
        return self._get_latest_tag_version_impl(date)

    def deprecate_all_ai_filter_tags(self, date=None, interests_file="ai_interests.txt"):
        return self._deprecate_all_tags_impl(date, interests_file)

    def save_ai_filter_tags(self, tags, version, prompt_hash, date=None, interests_file="ai_interests.txt"):
        return self._save_tags_impl(date, tags, version, prompt_hash, interests_file)

    def save_ai_filter_results(self, results, date=None):
        return self._save_filter_results_impl(date, results)

    def get_active_ai_filter_results(self, date=None, interests_file="ai_interests.txt"):
        return self._get_active_filter_results_impl(date, interests_file)

    def deprecate_specific_ai_filter_tags(self, tag_ids, date=None):
        return self._deprecate_specific_tags_impl(date, tag_ids)

    def update_ai_filter_tags_hash(self, interests_file, new_hash, date=None):
        return self._update_tags_hash_impl(date, interests_file, new_hash)

    def update_ai_filter_tag_descriptions(self, tag_updates, date=None, interests_file="ai_interests.txt"):
        return self._update_tag_descriptions_impl(date, tag_updates, interests_file)

    def update_ai_filter_tag_priorities(self, tag_priorities, date=None, interests_file="ai_interests.txt"):
        return self._update_tag_priorities_impl(date, tag_priorities, interests_file)

    def save_analyzed_news(self, news_ids, source_type, interests_file, prompt_hash, matched_ids, date=None):
        return self._save_analyzed_news_impl(date, news_ids, source_type, interests_file, prompt_hash, matched_ids)

    def get_analyzed_news_ids(self, source_type="hotlist", date=None, interests_file="ai_interests.txt"):
        return self._get_analyzed_news_ids_impl(date, source_type, interests_file)

    def clear_analyzed_news(self, date=None, interests_file="ai_interests.txt"):
        return self._clear_analyzed_news_impl(date, interests_file)

    def clear_unmatched_analyzed_news(self, date=None, interests_file="ai_interests.txt"):
        return self._clear_unmatched_analyzed_news_impl(date, interests_file)

    def get_all_news_ids(self, date=None):
        return self._get_all_news_ids_impl(date)

    def get_all_rss_ids(self, date=None):
        return self._get_all_rss_ids_impl(date)

    # ========================================
    # Local specific features: TXT/HTML snapshots
    # ========================================

    def save_txt_snapshot(self, data: NewsData) -> Optional[str]:
        """
        Save TXT snapshot

        New structure: output/txt/{date}/{time}.txt

        Args:
            data: News data

        Returns:
            Saved file path
        """
        if not self.enable_txt:
            return None

        try:
            date_folder = self._format_date_folder(data.date)
            txt_dir = self.data_dir / "txt" / date_folder
            txt_dir.mkdir(parents=True, exist_ok=True)

            file_path = txt_dir / f"{data.crawl_time}.txt"

            with open(file_path, "w", encoding="utf-8") as f:
                for source_id, news_list in data.items.items():
                    source_name = data.id_to_name.get(source_id, source_id)

                    # Write source title
                    if source_name and source_name != source_id:
                        f.write(f"{source_id} | {source_name}\n")
                    else:
                        f.write(f"{source_id}\n")

                    # Sort by ranking
                    sorted_news = sorted(news_list, key=lambda x: x.rank)

                    for item in sorted_news:
                        line = f"{item.rank}. {item.title}"
                        if item.url:
                            line += f" [URL:{item.url}]"
                        if item.mobile_url:
                            line += f" [MOBILE:{item.mobile_url}]"
                        f.write(line + "\n")

                    f.write("\n")

                # Write failed sources
                if data.failed_ids:
                    f.write("==== The following ID requests failed ====\n")
                    for failed_id in data.failed_ids:
                        f.write(f"{failed_id}\n")

            print(f"[Local Storage] TXT snapshot saved: {file_path}")
            return str(file_path)

        except Exception as e:
            print(f"[Local Storage] Failed to save TXT snapshot: {e}")
            return None

    def save_html_report(self, html_content: str, filename: str) -> Optional[str]:
        """
        Save HTML report

        New structure: output/html/{date}/{filename}

        Args:
            html_content: HTML content
            filename: File name

        Returns:
            Saved file path
        """
        if not self.enable_html:
            return None

        try:
            date_folder = self._format_date_folder()
            html_dir = self.data_dir / "html" / date_folder
            html_dir.mkdir(parents=True, exist_ok=True)

            file_path = html_dir / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"[Local Storage] HTML report saved: {file_path}")
            return str(file_path)

        except Exception as e:
            print(f"[Local Storage] Failed to save HTML report: {e}")
            return None

    # ========================================
    # Local specific features: Resource cleanup
    # ========================================

    def cleanup(self) -> None:
        """Clean up resources (close database connections)"""
        for db_path, conn in self._db_connections.items():
            try:
                conn.close()
                print(f"[Local Storage] Close database connection: {db_path}")
            except Exception as e:
                print(f"[Local Storage] Failed to close connection {db_path}: {e}")

        self._db_connections.clear()

    def cleanup_old_data(self, retention_days: int) -> int:
        """
        Clean up expired data

        New structure cleanup logic:
        - output/news/{date}.db  -> Delete expired .db files
        - output/rss/{date}.db   -> Delete expired .db files
        - output/txt/{date}/     -> Delete expired date directories
        - output/html/{date}/    -> Delete expired date directories

        Args:
            retention_days: Retention days (0 means no cleanup)

        Returns:
            Number of deleted files/directories
        """
        if retention_days <= 0:
            return 0

        deleted_count = 0
        cutoff_date = self._get_configured_time() - timedelta(days=retention_days)

        def parse_date_from_name(name: str) -> Optional[datetime]:
            """Parse date from file or directory name (ISO format: YYYY-MM-DD)"""
            # Remove .db suffix
            name = name.replace('.db', '')
            try:
                date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', name)
                if date_match:
                    return datetime(
                        int(date_match.group(1)),
                        int(date_match.group(2)),
                        int(date_match.group(3)),
                        tzinfo=pytz.timezone(self.timezone)
                    )
            except Exception:
                pass
            return None

        try:
            if not self.data_dir.exists():
                return 0

            # Clean up database files (news/, rss/)
            for db_type in ["news", "rss"]:
                db_dir = self.data_dir / db_type
                if not db_dir.exists():
                    continue

                for db_file in db_dir.glob("*.db"):
                    file_date = parse_date_from_name(db_file.name)
                    if file_date and file_date < cutoff_date:
                        # Close database connection first
                        db_path = str(db_file)
                        if db_path in self._db_connections:
                            try:
                                self._db_connections[db_path].close()
                                del self._db_connections[db_path]
                            except Exception:
                                pass

                        # Delete file
                        try:
                            db_file.unlink()
                            deleted_count += 1
                            print(f"[Local Storage] Clean up expired data: {db_type}/{db_file.name}")
                        except Exception as e:
                            print(f"[Local Storage] Failed to delete file {db_file}: {e}")

            # Clean up snapshot directories (txt/, html/)
            for snapshot_type in ["txt", "html"]:
                snapshot_dir = self.data_dir / snapshot_type
                if not snapshot_dir.exists():
                    continue

                for date_folder in snapshot_dir.iterdir():
                    if not date_folder.is_dir() or date_folder.name.startswith('.'):
                        continue

                    folder_date = parse_date_from_name(date_folder.name)
                    if folder_date and folder_date < cutoff_date:
                        try:
                            shutil.rmtree(date_folder)
                            deleted_count += 1
                            print(f"[Local Storage] Clean up expired data: {snapshot_type}/{date_folder.name}")
                        except Exception as e:
                            print(f"[Local Storage] Failed to delete directory {date_folder}: {e}")

            if deleted_count > 0:
                print(f"[Local Storage] Cleaned up a total of {deleted_count} expired files/directories")

            return deleted_count

        except Exception as e:
            print(f"[Local Storage] Failed to clean up expired data: {e}")
            return deleted_count

    def __del__(self):
        """Destructor, ensure connection is closed"""
        self.cleanup()
