# coding=utf-8
"""
External Sources Module - Nguồn dữ liệu mở rộng

Tích hợp các nguồn bên ngoài (Twitter, YouTube, Reddit, GitHub, v.v.)
vào pipeline TrendRadar.
"""

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult
from trendradar.crawler.sources.manager import ExternalSourceManager

__all__ = [
    "ExternalSource",
    "SourceItem",
    "SourceResult",
    "ExternalSourceManager",
]
