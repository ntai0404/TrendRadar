# coding=utf-8
"""
Remote storage backend (S3 compatible protocol)

Supports Cloudflare R2, Alibaba Cloud OSS, Tencent Cloud COS, AWS S3, MinIO, etc.
Use S3 compatible API (boto3) to access object storage
Data flow: Download today's SQLite -> Merge new data -> Upload back to remote
"""

import pytz
import re
import shutil
import sys
import tempfile
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    import boto3
    from botocore.config import Config as BotoConfig
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None
    BotoConfig = None
    ClientError = Exception

from trendradar.storage.base import StorageBackend, NewsData, RSSItem, RSSData
from trendradar.storage.sqlite_mixin import SQLiteStorageMixin
from trendradar.utils.time import (
    DEFAULT_TIMEZONE,
    get_configured_time,
    format_date_folder,
    format_time_filename,
)


class RemoteStorageBackend(SQLiteStorageMixin, StorageBackend):
    """
    Remote cloud storage backend (S3 compatible protocol)

    Features:
    - Use S3 compatible API to access remote storage
    - Supports Cloudflare R2, Alibaba Cloud OSS, Tencent Cloud COS, AWS S3, MinIO, etc.
    - Download SQLite to temporary directory for operations
    - Support data merging and uploading
    - Support pulling historical data from remote to local
    - Automatically clean up temporary files after running
    """

    def __init__(
        self,
        bucket_name: str,
        access_key_id: str,
        secret_access_key: str,
        endpoint_url: str,
        region: str = "",
        enable_txt: bool = False,  # Remote mode does not generate TXT by default
        enable_html: bool = True,
        temp_dir: Optional[str] = None,
        timezone: str = DEFAULT_TIMEZONE,
    ):
        """
        Initialize remote storage backend

        Args:
            bucket_name: Bucket name
            access_key_id: Access key ID
            secret_access_key: Secret access key
            endpoint_url: Endpoint URL
            region: Region (optional, required by some providers)
            enable_txt: Whether to enable TXT snapshot (disabled by default)
            enable_html: Whether to enable HTML report
            temp_dir: Temporary directory path (uses system temporary directory by default)
            timezone: Timezone configuration
        """
        if not HAS_BOTO3:
            raise ImportError("Remote storage backend requires boto3: pip install boto3")

        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.region = region
        self.enable_txt = enable_txt
        self.enable_html = enable_html
        self.timezone = timezone

        # Create temporary directory
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp(prefix="trendradar_"))
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize S3 client
        # Use virtual-hosted style addressing (mainstream)
        # Select signature version based on provider:
        # - Tencent Cloud COS and Alibaba Cloud OSS use SigV2 to avoid chunked encoding issues
        # - Other providers (AWS S3, Cloudflare R2, MinIO, etc.) use SigV4 by default
        use_sigv2 = "myqcloud.com" in endpoint_url.lower() or "aliyuncs.com" in endpoint_url.lower()
        signature_version = 's3' if use_sigv2 else 's3v4'

        s3_config = BotoConfig(
            s3={"addressing_style": "virtual"},
            signature_version=signature_version,
        )

        client_kwargs = {
            "endpoint_url": endpoint_url,
            "aws_access_key_id": access_key_id,
            "aws_secret_access_key": secret_access_key,
            "config": s3_config,
        }
        if region:
            client_kwargs["region_name"] = region

        self.s3_client = boto3.client("s3", **client_kwargs)

        # Track downloaded files (for cleanup)
        self._downloaded_files: List[Path] = []
        self._db_connections: Dict[str, sqlite3.Connection] = {}

        # Batch mode: delay upload to avoid frequently uploading the same file
        self._batch_mode = False
        self._batch_dirty: set = set()  # Set of (date, db_type) to be uploaded

        print(f"[Remote Storage] Initialization complete, bucket: {bucket_name}, signature version: {signature_version}")

    @property
    def backend_name(self) -> str:
        return "remote"

    @property
    def supports_txt(self) -> bool:
        return self.enable_txt

    # ========================================
    # SQLiteStorageMixin abstract method implementation
    # ========================================

    def _get_configured_time(self) -> datetime:
        """Get current time in configured timezone"""
        return get_configured_time(self.timezone)

    def _format_date_folder(self, date: Optional[str] = None) -> str:
        """Format date folder name (ISO format: YYYY-MM-DD)"""
        return format_date_folder(date, self.timezone)

    def _format_time_filename(self) -> str:
        """Format time file name (format: HH-MM)"""
        return format_time_filename(self.timezone)

    def _get_remote_db_key(self, date: Optional[str] = None, db_type: str = "news") -> str:
        """
        Get object key of SQLite file in remote storage

        Args:
            date: Date string
            db_type: Database type ("news" or "rss")

        Returns:
            Remote object key, e.g., "news/2025-12-28.db" or "rss/2025-12-28.db"
        """
        date_folder = self._format_date_folder(date)
        return f"{db_type}/{date_folder}.db"

    def _get_local_db_path(self, date: Optional[str] = None, db_type: str = "news") -> Path:
        """
        Get local temporary SQLite file path

        Args:
            date: Date string
            db_type: Database type ("news" or "rss")

        Returns:
            Local temporary file path
        """
        date_folder = self._format_date_folder(date)
        db_dir = self.temp_dir / db_type
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / f"{date_folder}.db"

    def _check_object_exists(self, r2_key: str) -> bool:
        """
        Check if object exists in remote storage

        Args:
            r2_key: Remote object key

        Returns:
            Whether it exists
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=r2_key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            # S3 compatible storage may return 404, NoSuchKey, or other variants
            if error_code in ("404", "NoSuchKey", "Not Found"):
                return False
            # Other errors (like permission issues) are also treated as non-existent, but print a warning
            print(f"[Remote Storage] Failed to check object existence ({r2_key}): {e}")
            return False
        except Exception as e:
            print(f"[Remote Storage] Exception checking object existence ({r2_key}): {e}")
            return False

    def _download_sqlite(self, date: Optional[str] = None, db_type: str = "news") -> Optional[Path]:
        """
        Download today's SQLite file from remote storage to local temporary directory

        Use get_object + iter_chunks instead of download_file,
        to correctly handle Tencent Cloud COS's chunked transfer encoding.

        Args:
            date: Date string
            db_type: Database type ("news" or "rss")

        Returns:
            Local file path, returns None if it does not exist
        """
        r2_key = self._get_remote_db_key(date, db_type)
        local_path = self._get_local_db_path(date, db_type)

        # Ensure directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists first
        if not self._check_object_exists(r2_key):
            print(f"[Remote Storage] File does not exist, will create new database: {r2_key}")
            return None

        try:
            # Use get_object + iter_chunks instead of download_file
            # iter_chunks will automatically handle chunked transfer encoding
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=r2_key)
            with open(local_path, 'wb') as f:
                for chunk in response['Body'].iter_chunks(chunk_size=1024*1024):
                    f.write(chunk)
            self._downloaded_files.append(local_path)
            print(f"[Remote Storage] Downloaded: {r2_key} -> {local_path}")
            return local_path
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            # S3 compatible storage may return different error codes
            if error_code in ("404", "NoSuchKey", "Not Found"):
                print(f"[Remote Storage] File does not exist, will create new database: {r2_key}")
                return None
            else:
                print(f"[Remote Storage] Download failed (error code: {error_code}): {e}")
                raise
        except Exception as e:
            print(f"[Remote Storage] Download exception: {e}")
            raise

    def begin_batch(self):
        """Enable batch mode: delay upload to avoid frequently uploading the same file"""
        self._batch_mode = True
        self._batch_dirty.clear()

    def end_batch(self):
        """End batch mode: uniformly upload all dirty databases"""
        self._batch_mode = False
        for date, db_type in self._batch_dirty:
            self._upload_sqlite(date, db_type)
        self._batch_dirty.clear()

    def _upload_sqlite(self, date: Optional[str] = None, db_type: str = "news") -> bool:
        """
        Upload local SQLite file to remote storage

        Delayed upload in batch mode, uniformly triggered by end_batch().

        Args:
            date: Date string
            db_type: Database type ("news" or "rss")

        Returns:
            Whether upload is successful
        """
        if self._batch_mode:
            self._batch_dirty.add((date, db_type))
            return True
        local_path = self._get_local_db_path(date, db_type)
        r2_key = self._get_remote_db_key(date, db_type)

        if not local_path.exists():
            print(f"[Remote Storage] Local file does not exist, cannot upload: {local_path}")
            return False

        try:
            # Get local file size
            local_size = local_path.stat().st_size
            print(f"[Remote Storage] Preparing to upload: {local_path} ({local_size} bytes) -> {r2_key}")

            # Read file content as bytes then upload
            # Avoid using chunked transfer encoding in the requests library when passing file objects
            # S3-compatible services like Tencent Cloud COS may not handle chunked encoding correctly
            with open(local_path, 'rb') as f:
                file_content = f.read()

            # Use put_object and explicitly set ContentLength to ensure chunked encoding is not used
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=r2_key,
                Body=file_content,
                ContentLength=local_size,
                ContentType='application/x-sqlite3',
            )
            print(f"[Remote Storage] Uploaded: {local_path} -> {r2_key}")

            # Verify successful upload
            if self._check_object_exists(r2_key):
                print(f"[Remote Storage] Upload verification successful: {r2_key}")
                return True
            else:
                print(f"[Remote Storage] Upload verification failed: File not found in remote storage")
                return False

        except Exception as e:
            print(f"[Remote Storage] Upload failed: {e}")
            return False

    def _get_connection(self, date: Optional[str] = None, db_type: str = "news") -> sqlite3.Connection:
        """
        Get database connection

        Args:
            date: Date string
            db_type: Database type ("news" or "rss")

        Returns:
            Database connection
        """
        local_path = self._get_local_db_path(date, db_type)
        db_path = str(local_path)

        if db_path not in self._db_connections:
            # Ensure directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # If it does not exist locally, try downloading from remote storage
            if not local_path.exists():
                self._download_sqlite(date, db_type)

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            self._init_tables(conn, db_type)
            self._db_connections[db_path] = conn

        return self._db_connections[db_path]

    # ========================================
    # StorageBackend interface implementation (delegated to mixin + upload)
    # ========================================

    def save_news_data(self, data: NewsData) -> bool:
        """
        Save news data to remote storage

        Process: Download existing database → Insert/Cập nhật data → Upload back to remote storage
        """
        # Query the number of existing records
        conn = self._get_connection(data.date)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM news_items")
        row = cursor.fetchone()
        existing_count = row[0] if row else 0
        if existing_count > 0:
            print(f"[Remote Storage] Already have {existing_count} historical records, will merge new data")

        # Use mixin implementation to save data
        success, new_count, updated_count, title_changed_count, off_list_count = \
            self._save_news_data_impl(data, "[Remote Storage]")

        if not success:
            return False

        # Query the total number of records after merging
        cursor.execute("SELECT COUNT(*) as count FROM news_items")
        row = cursor.fetchone()
        final_count = row[0] if row else 0

        # Output detailed storage statistics log
        log_parts = [f"[Remote Storage] Processing complete: Added {new_count} items"]
        if updated_count > 0:
            log_parts.append(f"Cập nhật {updated_count} items")
        if title_changed_count > 0:
            log_parts.append(f"Title changed {title_changed_count} items")
        if off_list_count > 0:
            log_parts.append(f"Dropped off list {off_list_count} items")
        log_parts.append(f"(Total after deduplication: {final_count} items)")
        print("，".join(log_parts))

        # Upload to remote storage
        if self._upload_sqlite(data.date):
            print(f"[Remote Storage] Data synchronized to remote storage")
            return True
        else:
            print(f"[Remote Storage] Failed to upload to remote storage")
            return False

    def get_today_all_data(self, date: Optional[str] = None) -> Optional[NewsData]:
        """Get all news data for the specified date (after merging)"""
        return self._get_today_all_data_impl(date)

    def get_latest_crawl_data(self, date: Optional[str] = None) -> Optional[NewsData]:
        """Get the data from the latest scrape"""
        return self._get_latest_crawl_data_impl(date)

    def detect_new_titles(self, current_data: NewsData) -> Dict[str, Dict]:
        """Detect newly added titles"""
        return self._detect_new_titles_impl(current_data)

    def is_first_crawl_today(self, date: Optional[str] = None) -> bool:
        """Check if it is the first scrape of the day"""
        return self._is_first_crawl_today_impl(date)

    # ========================================
    # Time period execution record (scheduling system)
    # ========================================

    def has_period_executed(self, date_str: str, period_key: str, action: str) -> bool:
        """Check if a specific action in the specified time period has been executed"""
        return self._has_period_executed_impl(date_str, period_key, action)

    def record_period_execution(self, date_str: str, period_key: str, action: str) -> bool:
        """Record the execution of an action for a time period"""
        success = self._record_period_execution_impl(date_str, period_key, action)

        if success:
            now_str = self._get_configured_time().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[Remote Storage] Time period execution record saved: {period_key}/{action} at {now_str}")

            # Upload to remote storage to ensure record persistence
            if self._upload_sqlite(date_str):
                print(f"[Remote Storage] Time period execution records have been synchronized to remote storage")
                return True
            else:
                print(f"[Remote Storage] Failed to synchronize time period execution records to remote storage")
                return False

        return False

    # ========================================
    # RSS data storage method
    # ========================================

    def save_rss_data(self, data: RSSData) -> bool:
        """
        Save RSS data to remote storage

        Process: Download existing database → Insert/Cập nhật data → Upload back to remote storage
        """
        success, new_count, updated_count = self._save_rss_data_impl(data, "[Remote Storage]")

        if not success:
            return False

        # Output statistics log
        log_parts = [f"[Remote Storage] RSS processing completed: added {new_count} items"]
        if updated_count > 0:
            log_parts.append(f"Cập nhật {updated_count} items")
        print("，".join(log_parts))

        # Upload to remote storage
        if self._upload_sqlite(data.date, db_type="rss"):
            print(f"[Remote Storage] RSS data has been synchronized to remote storage")
            return True
        else:
            print(f"[Remote Storage] Failed to upload RSS to remote storage")
            return False

    def get_rss_data(self, date: Optional[str] = None) -> Optional[RSSData]:
        """Get all RSS data for a specified date"""
        return self._get_rss_data_impl(date)

    def detect_new_rss_items(self, current_data: RSSData) -> Dict[str, List[RSSItem]]:
        """Detect newly added RSS items"""
        return self._detect_new_rss_items_impl(current_data)

    def get_latest_rss_data(self, date: Optional[str] = None) -> Optional[RSSData]:
        """Get the latest fetched RSS data"""
        return self._get_latest_rss_data_impl(date)

    # ========================================
    # AI intelligent filtering storage method
    # ========================================

    def get_active_ai_filter_tags(self, date=None, interests_file="ai_interests.txt"):
        return self._get_active_tags_impl(date, interests_file)

    def get_latest_prompt_hash(self, date=None, interests_file="ai_interests.txt"):
        return self._get_latest_prompt_hash_impl(date, interests_file)

    def get_latest_ai_filter_tag_version(self, date=None):
        return self._get_latest_tag_version_impl(date)

    def deprecate_all_ai_filter_tags(self, date=None, interests_file="ai_interests.txt"):
        count = self._deprecate_all_tags_impl(date, interests_file)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def save_ai_filter_tags(self, tags, version, prompt_hash, date=None, interests_file="ai_interests.txt"):
        count = self._save_tags_impl(date, tags, version, prompt_hash, interests_file)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def save_ai_filter_results(self, results, date=None):
        count = self._save_filter_results_impl(date, results)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def get_active_ai_filter_results(self, date=None, interests_file="ai_interests.txt"):
        return self._get_active_filter_results_impl(date, interests_file)

    def deprecate_specific_ai_filter_tags(self, tag_ids, date=None):
        count = self._deprecate_specific_tags_impl(date, tag_ids)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def update_ai_filter_tags_hash(self, interests_file, new_hash, date=None):
        count = self._update_tags_hash_impl(date, interests_file, new_hash)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def update_ai_filter_tag_descriptions(self, tag_updates, date=None, interests_file="ai_interests.txt"):
        count = self._update_tag_descriptions_impl(date, tag_updates, interests_file)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def update_ai_filter_tag_priorities(self, tag_priorities, date=None, interests_file="ai_interests.txt"):
        count = self._update_tag_priorities_impl(date, tag_priorities, interests_file)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def save_analyzed_news(self, news_ids, source_type, interests_file, prompt_hash, matched_ids, date=None):
        count = self._save_analyzed_news_impl(date, news_ids, source_type, interests_file, prompt_hash, matched_ids)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def get_analyzed_news_ids(self, source_type="hotlist", date=None, interests_file="ai_interests.txt"):
        return self._get_analyzed_news_ids_impl(date, source_type, interests_file)

    def clear_analyzed_news(self, date=None, interests_file="ai_interests.txt"):
        count = self._clear_analyzed_news_impl(date, interests_file)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def clear_unmatched_analyzed_news(self, date=None, interests_file="ai_interests.txt"):
        count = self._clear_unmatched_analyzed_news_impl(date, interests_file)
        if count > 0:
            self._upload_sqlite(date)
        return count

    def get_all_news_ids(self, date=None):
        return self._get_all_news_ids_impl(date)

    def get_all_rss_ids(self, date=None):
        return self._get_all_rss_ids_impl(date)

    # ========================================
    # Remote specific features: TXT/HTML snapshots (temporary directory)
    # ========================================

    def save_txt_snapshot(self, data: NewsData) -> Optional[str]:
        """Save TXT snapshot (not supported by default in remote storage mode)"""
        if not self.enable_txt:
            return None

        # If enabled, save to local temporary directory
        try:
            date_folder = self._format_date_folder(data.date)
            txt_dir = self.temp_dir / date_folder / "txt"
            txt_dir.mkdir(parents=True, exist_ok=True)

            file_path = txt_dir / f"{data.crawl_time}.txt"

            with open(file_path, "w", encoding="utf-8") as f:
                for source_id, news_list in data.items.items():
                    source_name = data.id_to_name.get(source_id, source_id)

                    if source_name and source_name != source_id:
                        f.write(f"{source_id} | {source_name}\n")
                    else:
                        f.write(f"{source_id}\n")

                    sorted_news = sorted(news_list, key=lambda x: x.rank)

                    for item in sorted_news:
                        line = f"{item.rank}. {item.title}"
                        if item.url:
                            line += f" [URL:{item.url}]"
                        if item.mobile_url:
                            line += f" [MOBILE:{item.mobile_url}]"
                        f.write(line + "\n")

                    f.write("\n")

                if data.failed_ids:
                    f.write("==== The following ID requests failed ====\n")
                    for failed_id in data.failed_ids:
                        f.write(f"{failed_id}\n")

            print(f"[Remote Storage] TXT snapshot saved: {file_path}")
            return str(file_path)

        except Exception as e:
            print(f"[Remote Storage] Failed to save TXT snapshot: {e}")
            return None

    def save_html_report(self, html_content: str, filename: str) -> Optional[str]:
        """Save HTML report to temporary directory"""
        if not self.enable_html:
            return None

        try:
            date_folder = self._format_date_folder()
            html_dir = self.temp_dir / date_folder / "html"
            html_dir.mkdir(parents=True, exist_ok=True)

            file_path = html_dir / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"[Remote Storage] HTML report saved: {file_path}")
            return str(file_path)

        except Exception as e:
            print(f"[Remote Storage] Failed to save HTML report: {e}")
            return None

    # ========================================
    # Remote specific features: Resource cleanup
    # ========================================

    def cleanup(self) -> None:
        """Clean up resources (close connections and delete temporary files)"""
        # Check if Python is shutting down
        if sys.meta_path is None:
            return

        # Close database connection
        db_connections = getattr(self, "_db_connections", {})
        for db_path, conn in list(db_connections.items()):
            try:
                conn.close()
                print(f"[Remote Storage] Close database connection: {db_path}")
            except Exception as e:
                print(f"[Remote Storage] Failed to close connection {db_path}: {e}")

        if db_connections:
            db_connections.clear()

        # Delete temporary directory
        temp_dir = getattr(self, "temp_dir", None)
        if temp_dir:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    print(f"[Remote Storage] Temporary directory cleaned up: {temp_dir}")
            except Exception as e:
                # Ignore errors during Python shutdown
                if sys.meta_path is not None:
                    print(f"[Remote Storage] Failed to clean up temporary directory: {e}")

        downloaded_files = getattr(self, "_downloaded_files", None)
        if downloaded_files:
            downloaded_files.clear()

    def cleanup_old_data(self, retention_days: int) -> int:
        """
        Clean up expired data on remote storage

        Args:
            retention_days: Retention days (0 means no cleanup)

        Returns:
            Number of deleted database files
        """
        if retention_days <= 0:
            return 0

        deleted_count = 0
        cutoff_date = self._get_configured_time() - timedelta(days=retention_days)

        try:
            # List all objects under the news/ prefix in remote storage
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix="news/")

            # Collect object keys to be deleted
            objects_to_delete = []
            deleted_dates = set()

            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    key = obj['Key']

                    # Parse date (format: news/YYYY-MM-DD.db)
                    folder_date = None
                    date_str = None
                    try:
                        date_match = re.match(r'news/(\d{4})-(\d{2})-(\d{2})\.db$', key)
                        if date_match:
                            folder_date = datetime(
                                int(date_match.group(1)),
                                int(date_match.group(2)),
                                int(date_match.group(3)),
                                tzinfo=pytz.timezone(self.timezone)
                            )
                            date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                    except Exception:
                        continue

                    if folder_date and folder_date < cutoff_date:
                        objects_to_delete.append({'Key': key})
                        deleted_dates.add(date_str)

            # Batch delete objects (max 1000 at a time)
            if objects_to_delete:
                batch_size = 1000
                for i in range(0, len(objects_to_delete), batch_size):
                    batch = objects_to_delete[i:i + batch_size]
                    try:
                        self.s3_client.delete_objects(
                            Bucket=self.bucket_name,
                            Delete={'Objects': batch}
                        )
                        print(f"[Remote Storage] Delete {len(batch)} objects")
                    except Exception as e:
                        print(f"[Remote Storage] Batch delete failed: {e}")

                deleted_count = len(deleted_dates)
                for date_str in sorted(deleted_dates):
                    print(f"[Remote Storage] Clean up expired data: news/{date_str}.db")

                print(f"[Remote Storage] Cleaned up a total of {deleted_count} expired date database files")

            return deleted_count

        except Exception as e:
            print(f"[Remote Storage] Failed to clean up expired data: {e}")
            return deleted_count

    def __del__(self):
        """Destructor"""
        # Check if Python is shutting down
        if sys.meta_path is None:
            return
        try:
            self.cleanup()
        except Exception:
            # Errors may occur when Python shuts down, just ignore them
            pass

    # ========================================
    # Remote-specific features: data pulling and listing
    # ========================================

    def pull_recent_days(self, days: int, local_data_dir: str = "output") -> int:
        """
        Pull data from the last N days from remote to local

        Args:
            days: Number of days to pull
            local_data_dir: Local data directory

        Returns:
            Number of successfully pulled database files
        """
        if days <= 0:
            return 0

        local_dir = Path(local_data_dir)
        local_dir.mkdir(parents=True, exist_ok=True)

        pulled_count = 0
        now = self._get_configured_time()

        print(f"[Remote Storage] Start pulling data for the last {days} days...")

        for i in range(days):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            # Local target path
            local_date_dir = local_dir / date_str
            local_db_path = local_date_dir / "news.db"

            # If it already exists locally, skip
            if local_db_path.exists():
                print(f"[Remote Storage] Skipped (already exists locally): {date_str}")
                continue

            # Remote object key
            remote_key = f"news/{date_str}.db"

            # Check if it exists remotely
            if not self._check_object_exists(remote_key):
                print(f"[Remote Storage] Skipped (does not exist remotely): {date_str}")
                continue

            # Download (use get_object + iter_chunks to handle chunked encoding)
            try:
                local_date_dir.mkdir(parents=True, exist_ok=True)
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=remote_key)
                with open(local_db_path, 'wb') as f:
                    for chunk in response['Body'].iter_chunks(chunk_size=1024*1024):
                        f.write(chunk)
                print(f"[Remote Storage] Pulled: {remote_key} -> {local_db_path}")
                pulled_count += 1
            except Exception as e:
                print(f"[Remote Storage] Pull failed ({date_str}): {e}")

        print(f"[Remote Storage] Pull complete, downloaded a total of {pulled_count} database files")
        return pulled_count

    def list_remote_dates(self) -> List[str]:
        """
        List all available dates in remote storage

        Returns:
            List of date strings (YYYY-MM-DD format)
        """
        dates = []

        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix="news/")

            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    key = obj['Key']
                    # Parse date
                    date_match = re.match(r'news/(\d{4}-\d{2}-\d{2})\.db$', key)
                    if date_match:
                        dates.append(date_match.group(1))

            return sorted(dates, reverse=True)

        except Exception as e:
            print(f"[Remote Storage] Failed to list remote dates: {e}")
            return []
