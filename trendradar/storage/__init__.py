# coding=utf-8
"""
Storage module - supports multiple storage backends

Supported storage backends:
- local: local SQLite + TXT/HTML file
- remote: remote cloud storage (S3 compatible protocol: R2/OSS/COS/S3, etc.)
- auto: Automatically select according to the environment (use remote for GitHub Actions, local for others)
"""

from trendradar.storage.base import (
    StorageBackend,
    NewsItem,
    NewsData,
    RSSItem,
    RSSData,
    convert_crawl_results_to_news_data,
)
from trendradar.storage.sqlite_mixin import SQLiteStorageMixin
from trendradar.storage.local import LocalStorageBackend
from trendradar.storage.manager import StorageManager, get_storage_manager

# Optional import of remote backend (requires boto3)
try:
    from trendradar.storage.remote import RemoteStorageBackend
    HAS_REMOTE = True
except ImportError:
    RemoteStorageBackend = None
    HAS_REMOTE = False

__all__ = [
    #Basic class
    "StorageBackend",
    "NewsItem",
    "NewsData",
    "RSSItem",
    "RSSData",
    # Mixin
    "SQLiteStorageMixin",
    #Conversion function
    "convert_crawl_results_to_news_data",
    # Backend implementation
    "LocalStorageBackend",
    "RemoteStorageBackend",
    "HAS_REMOTE",
    # Manager
    "StorageManager",
    "get_storage_manager",
]
