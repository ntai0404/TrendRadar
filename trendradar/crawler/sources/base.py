# coding=utf-8
"""
Base class cho External Sources

Mỗi nguồn mới (Twitter, YouTube, Reddit, ...) kế thừa ExternalSource
và implement phương thức fetch().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class SourceItem:
    """Một item từ nguồn bên ngoài (tweet, video, post, ...)"""
    title: str
    url: str
    source_id: str              # ID nguồn (twitter, youtube, reddit, ...)
    source_name: str            # Tên hiển thị nguồn
    published_at: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # metadata có thể chứa: likes, retweets, views, subreddit, channel, ...


@dataclass
class SourceResult:
    """Kết quả fetch từ một nguồn"""
    source_id: str
    source_name: str
    items: List[SourceItem] = field(default_factory=list)
    error: Optional[str] = None
    fetched_at: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def count(self) -> int:
        return len(self.items)


class ExternalSource(ABC):
    """
    Base class cho tất cả external sources.

    Mỗi source phải implement:
      - source_id: str
      - source_name: str
      - fetch(config) -> SourceResult
      - is_available() -> bool
    """

    @property
    @abstractmethod
    def source_id(self) -> str:
        """ID duy nhất của nguồn (vd: 'twitter', 'youtube')"""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Tên hiển thị (vd: 'Twitter/X', 'YouTube')"""
        ...

    @abstractmethod
    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Fetch dữ liệu từ nguồn.

        Args:
            config: Cấu hình riêng cho nguồn này từ config.yaml

        Returns:
            SourceResult chứa danh sách items hoặc error
        """
        ...

    def is_available(self) -> bool:
        """
        Kiểm tra xem source có sẵn sàng không (tool đã cài, cookie có, ...).
        Mặc định trả True — override nếu cần check dependency.
        """
        return True

    def _make_result(
        self,
        items: List[SourceItem] = None,
        error: Optional[str] = None,
    ) -> SourceResult:
        """Helper tạo SourceResult"""
        return SourceResult(
            source_id=self.source_id,
            source_name=self.source_name,
            items=items or [],
            error=error,
            fetched_at=datetime.utcnow().isoformat(),
        )
