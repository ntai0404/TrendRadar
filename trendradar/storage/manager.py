# coding=utf-8
"""
Storage Manager - Unified management of storage backends

Automatically select the appropriate storage backend based on environment and configuration
"""

import os
from typing import Optional

from trendradar.storage.base import StorageBackend, NewsData, RSSData
from trendradar.utils.time import DEFAULT_TIMEZONE


# Storage manager singleton
_storage_manager: Optional["StorageManager"] = None


class StorageManager:
    """
    Storage Manager

    Features:
    - Automatically detect runtime environment (GitHub Actions / Docker / Local)
    - Select storage backend based on configuration (local / remote / auto)
    - Provide a unified storage interface
    - Support pulling data from remote to local
    """

    def __init__(
        self,
        backend_type: str = "auto",
        data_dir: str = "output",
        enable_txt: bool = True,
        enable_html: bool = True,
        remote_config: Optional[dict] = None,
        local_retention_days: int = 0,
        remote_retention_days: int = 0,
        pull_enabled: bool = False,
        pull_days: int = 0,
        timezone: str = DEFAULT_TIMEZONE,
    ):
        """
        Initialize storage manager

        Args:
            backend_type: Storage backend type (local / remote / auto)
            data_dir: Local data directory
            enable_txt: Whether to enable TXT snapshots
            enable_html: Whether to enable HTML reports
            remote_config: Remote storage configuration (endpoint_url, bucket_name, access_key_id, etc.)
            local_retention_days: Local data retention days (0 = unlimited)
            remote_retention_days: Remote data retention days (0 = unlimited)
            pull_enabled: Whether to enable automatic pull on startup
            pull_days: Pull data for the last N days
            timezone: Timezone configuration
        """
        self.backend_type = backend_type
        self.data_dir = data_dir
        self.enable_txt = enable_txt
        self.enable_html = enable_html
        self.remote_config = remote_config or {}
        self.local_retention_days = local_retention_days
        self.remote_retention_days = remote_retention_days
        self.pull_enabled = pull_enabled
        self.pull_days = pull_days
        self.timezone = timezone

        self._backend: Optional[StorageBackend] = None
        self._remote_backend: Optional[StorageBackend] = None

    @staticmethod
    def is_github_actions() -> bool:
        """Detect if running in GitHub Actions environment"""
        return os.environ.get("GITHUB_ACTIONS") == "true"

    @staticmethod
    def is_docker() -> bool:
        """Detect if running in a Docker container"""
        # Method 1: Check /.dockerenv file
        if os.path.exists("/.dockerenv"):
            return True

        # Method 2: Check cgroup (Linux)
        try:
            with open("/proc/1/cgroup", "r") as f:
                return "docker" in f.read()
        except (FileNotFoundError, PermissionError):
            pass

        # Method 3: Check environment variables
        return os.environ.get("DOCKER_CONTAINER") == "true"

    def _resolve_backend_type(self) -> str:
        """Parse the actual backend type used"""
        if self.backend_type == "auto":
            if self.is_github_actions():
                # GitHub Actions environment, check if remote storage is configured
                if self._has_remote_config():
                    return "remote"
                else:
                    print("[Storage Manager] GitHub Actions environment but remote storage is not configured, using local storage")
                    return "local"
            else:
                return "local"
        return self.backend_type

    def _has_remote_config(self) -> bool:
        """Check if there is a valid remote storage configuration"""
        # Check configuration or environment variables
        bucket_name = self.remote_config.get("bucket_name") or os.environ.get("S3_BUCKET_NAME")
        access_key = self.remote_config.get("access_key_id") or os.environ.get("S3_ACCESS_KEY_ID")
        secret_key = self.remote_config.get("secret_access_key") or os.environ.get("S3_SECRET_ACCESS_KEY")
        endpoint = self.remote_config.get("endpoint_url") or os.environ.get("S3_ENDPOINT_URL")

        # Debug log
        has_config = bool(bucket_name and access_key and secret_key and endpoint)
        if not has_config:
            print(f"[Storage Manager] Remote storage configuration check failed:")
            print(f"  - bucket_name: {'Configured' if bucket_name else 'Not configured'}")
            print(f"  - access_key_id: {'Configured' if access_key else 'Not configured'}")
            print(f"  - secret_access_key: {'Configured' if secret_key else 'Not configured'}")
            print(f"  - endpoint_url: {'Configured' if endpoint else 'Not configured'}")

        return has_config

    def _create_remote_backend(self) -> Optional[StorageBackend]:
        """Create remote storage backend"""
        try:
            from trendradar.storage.remote import RemoteStorageBackend

            return RemoteStorageBackend(
                bucket_name=self.remote_config.get("bucket_name") or os.environ.get("S3_BUCKET_NAME", ""),
                access_key_id=self.remote_config.get("access_key_id") or os.environ.get("S3_ACCESS_KEY_ID", ""),
                secret_access_key=self.remote_config.get("secret_access_key") or os.environ.get("S3_SECRET_ACCESS_KEY", ""),
                endpoint_url=self.remote_config.get("endpoint_url") or os.environ.get("S3_ENDPOINT_URL", ""),
                region=self.remote_config.get("region") or os.environ.get("S3_REGION", ""),
                enable_txt=self.enable_txt,
                enable_html=self.enable_html,
                timezone=self.timezone,
            )
        except ImportError as e:
            print(f"[Storage Manager] Remote backend import failed: {e}")
            print("[Storage Manager] Please ensure boto3 is installed: pip install boto3")
            return None
        except Exception as e:
            print(f"[Storage Manager] Remote backend initialization failed: {e}")
            return None

    def get_backend(self) -> StorageBackend:
        """Get storage backend instance"""
        if self._backend is None:
            resolved_type = self._resolve_backend_type()

            if resolved_type == "remote":
                self._backend = self._create_remote_backend()
                if self._backend:
                    print(f"[Storage Manager] Using remote storage backend")
                else:
                    print("[Storage Manager] Falling back to local storage")
                    resolved_type = "local"

            if resolved_type == "local" or self._backend is None:
                from trendradar.storage.local import LocalStorageBackend

                self._backend = LocalStorageBackend(
                    data_dir=self.data_dir,
                    enable_txt=self.enable_txt,
                    enable_html=self.enable_html,
                    timezone=self.timezone,
                )
                print(f"[Storage Manager] Using local storage backend (Data directory: {self.data_dir})")

        return self._backend

    def pull_from_remote(self) -> int:
        """
        Pull data from remote to local

        Returns:
            Number of successfully pulled files
        """
        if not self.pull_enabled or self.pull_days <= 0:
            return 0

        if not self._has_remote_config():
            print("[Storage Manager] Remote storage not configured, cannot pull")
            return 0

        # Create remote backend (if not exists)
        if self._remote_backend is None:
            self._remote_backend = self._create_remote_backend()

        if self._remote_backend is None:
            print("[Storage Manager] Cannot create remote backend, pull failed")
            return 0

        # Call pull method
        return self._remote_backend.pull_recent_days(self.pull_days, self.data_dir)

    def save_news_data(self, data: NewsData) -> bool:
        """Save news data"""
        return self.get_backend().save_news_data(data)

    def save_rss_data(self, data: RSSData) -> bool:
        """Save RSS data"""
        return self.get_backend().save_rss_data(data)

    def get_rss_data(self, date: Optional[str] = None) -> Optional[RSSData]:
        """Get all RSS data for a specified date (daily summary mode)"""
        return self.get_backend().get_rss_data(date)

    def get_latest_rss_data(self, date: Optional[str] = None) -> Optional[RSSData]:
        """Get the latest fetched RSS data (Bảng xếp hạng hiện tại mode)"""
        return self.get_backend().get_latest_rss_data(date)

    def detect_new_rss_items(self, current_data: RSSData) -> dict:
        """Detect new RSS entries (incremental mode)"""
        return self.get_backend().detect_new_rss_items(current_data)

    def get_today_all_data(self, date: Optional[str] = None) -> Optional[NewsData]:
        """Get all data for today"""
        return self.get_backend().get_today_all_data(date)

    def get_latest_crawl_data(self, date: Optional[str] = None) -> Optional[NewsData]:
        """Get latest fetched data"""
        return self.get_backend().get_latest_crawl_data(date)

    def detect_new_titles(self, current_data: NewsData) -> dict:
        """Detect new titles"""
        return self.get_backend().detect_new_titles(current_data)

    def save_txt_snapshot(self, data: NewsData) -> Optional[str]:
        """Save TXT snapshot"""
        return self.get_backend().save_txt_snapshot(data)

    def save_html_report(self, html_content: str, filename: str) -> Optional[str]:
        """Save HTML report"""
        return self.get_backend().save_html_report(html_content, filename)

    def is_first_crawl_today(self, date: Optional[str] = None) -> bool:
        """Check if it is the first fetch of the day"""
        return self.get_backend().is_first_crawl_today(date)

    def cleanup(self) -> None:
        """Clean up resources"""
        if self._backend:
            self._backend.cleanup()
        if self._remote_backend:
            self._remote_backend.cleanup()

    def cleanup_old_data(self) -> int:
        """
        Clean up expired data

        Returns:
            Number of deleted date directories
        """
        total_deleted = 0

        # Clean up local data
        if self.local_retention_days > 0:
            total_deleted += self.get_backend().cleanup_old_data(self.local_retention_days)

        # Clean up remote data (if configured)
        if self.remote_retention_days > 0 and self._has_remote_config():
            if self._remote_backend is None:
                self._remote_backend = self._create_remote_backend()
            if self._remote_backend:
                total_deleted += self._remote_backend.cleanup_old_data(self.remote_retention_days)

        return total_deleted

    @property
    def backend_name(self) -> str:
        """Get current backend name"""
        return self.get_backend().backend_name

    @property
    def supports_txt(self) -> bool:
        """Whether TXT snapshot is supported"""
        return self.get_backend().supports_txt

    def has_period_executed(self, date_str: str, period_key: str, action: str) -> bool:
        """Check if a specific action in a specified time period has been executed"""
        return self.get_backend().has_period_executed(date_str, period_key, action)

    def record_period_execution(self, date_str: str, period_key: str, action: str) -> bool:
        """Record action execution for a time period"""
        return self.get_backend().record_period_execution(date_str, period_key, action)

    # === AI intelligent filtering storage operations ===

    def begin_batch(self):
        """Enable batch mode (delayed upload for remote backend)"""
        self.get_backend().begin_batch()

    def end_batch(self):
        """End batch mode (unified upload of dirty databases)"""
        self.get_backend().end_batch()

    def get_active_ai_filter_tags(self, date=None, interests_file="ai_interests.txt"):
        """Get active tags for a specified interest file"""
        return self.get_backend().get_active_ai_filter_tags(date, interests_file)

    def get_latest_prompt_hash(self, date=None, interests_file="ai_interests.txt"):
        """Get the latest prompt_hash for a specified interest file"""
        return self.get_backend().get_latest_prompt_hash(date, interests_file)

    def get_latest_ai_filter_tag_version(self, date=None):
        """Get the latest tag version number"""
        return self.get_backend().get_latest_ai_filter_tag_version(date)

    def deprecate_all_ai_filter_tags(self, date=None, interests_file="ai_interests.txt"):
        """Discard active tags and classification results for a specified interest file"""
        return self.get_backend().deprecate_all_ai_filter_tags(date, interests_file)

    def save_ai_filter_tags(self, tags, version, prompt_hash, date=None, interests_file="ai_interests.txt"):
        """Save newly extracted tags"""
        return self.get_backend().save_ai_filter_tags(tags, version, prompt_hash, date, interests_file)

    def save_ai_filter_results(self, results, date=None):
        """Save classification results"""
        return self.get_backend().save_ai_filter_results(results, date)

    def get_active_ai_filter_results(self, date=None, interests_file="ai_interests.txt"):
        """Get active classification results for a specified interest file"""
        return self.get_backend().get_active_ai_filter_results(date, interests_file)

    def deprecate_specific_ai_filter_tags(self, tag_ids, date=None):
        """Deprecate the tag with the specified ID and its associated classification results"""
        return self.get_backend().deprecate_specific_ai_filter_tags(tag_ids, date)

    def update_ai_filter_tags_hash(self, interests_file, new_hash, date=None):
        """Cập nhật the prompt_hash of all active tags in the specified interest file"""
        return self.get_backend().update_ai_filter_tags_hash(interests_file, new_hash, date)

    def update_ai_filter_tag_descriptions(self, tag_updates, date=None, interests_file="ai_interests.txt"):
        """Match by tag name, Cập nhật the description of active tags"""
        return self.get_backend().update_ai_filter_tag_descriptions(tag_updates, date, interests_file)

    def update_ai_filter_tag_priorities(self, tag_priorities, date=None, interests_file="ai_interests.txt"):
        """Match by tag name, Cập nhật the priority of active tags"""
        return self.get_backend().update_ai_filter_tag_priorities(tag_priorities, date, interests_file)

    def save_analyzed_news(self, news_ids, source_type, interests_file, prompt_hash, matched_ids, date=None):
        """Batch record analyzed news (both matched and unmatched are recorded)"""
        return self.get_backend().save_analyzed_news(news_ids, source_type, interests_file, prompt_hash, matched_ids, date)

    def get_analyzed_news_ids(self, source_type="hotlist", date=None, interests_file="ai_interests.txt"):
        """Get the set of analyzed news IDs"""
        return self.get_backend().get_analyzed_news_ids(source_type, date, interests_file)

    def clear_analyzed_news(self, date=None, interests_file="ai_interests.txt"):
        """Clear all analyzed records of the specified interest file"""
        return self.get_backend().clear_analyzed_news(date, interests_file)

    def clear_unmatched_analyzed_news(self, date=None, interests_file="ai_interests.txt"):
        """Clear unmatched analyzed records"""
        return self.get_backend().clear_unmatched_analyzed_news(date, interests_file)

    def get_all_news_ids(self, date=None):
        """Get all news IDs and titles"""
        return self.get_backend().get_all_news_ids(date)

    def get_all_rss_ids(self, date=None):
        """Get all RSS IDs and titles"""
        return self.get_backend().get_all_rss_ids(date)



def get_storage_manager(
    backend_type: str = "auto",
    data_dir: str = "output",
    enable_txt: bool = True,
    enable_html: bool = True,
    remote_config: Optional[dict] = None,
    local_retention_days: int = 0,
    remote_retention_days: int = 0,
    pull_enabled: bool = False,
    pull_days: int = 0,
    timezone: str = DEFAULT_TIMEZONE,
    force_new: bool = False,
) -> StorageManager:
    """
    Get the storage manager singleton

    Args:
        backend_type: Storage backend type
        data_dir: Local data directory
        enable_txt: Whether to enable TXT snapshots
        enable_html: Whether to enable HTML reports
        remote_config: Remote storage configuration
        local_retention_days: Local data retention days (0 = unlimited)
        remote_retention_days: Remote data retention days (0 = unlimited)
        pull_enabled: Whether to enable automatic pull on startup
        pull_days: Pull data from the last N days
        timezone: Timezone configuration
        force_new: Whether to force the creation of a new instance

    Returns:
        StorageManager instance
    """
    global _storage_manager

    if _storage_manager is None or force_new:
        _storage_manager = StorageManager(
            backend_type=backend_type,
            data_dir=data_dir,
            enable_txt=enable_txt,
            enable_html=enable_html,
            remote_config=remote_config,
            local_retention_days=local_retention_days,
            remote_retention_days=remote_retention_days,
            pull_enabled=pull_enabled,
            pull_days=pull_days,
            timezone=timezone,
        )

    return _storage_manager
