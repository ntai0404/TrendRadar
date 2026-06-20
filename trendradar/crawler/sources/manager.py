# coding=utf-8
"""
External Source Manager

Quản lý và điều phối tất cả external sources.
Đọc config, khởi tạo sources, chạy fetch và trả kết quả thống nhất.
"""

import time
from typing import Dict, Any, List, Optional

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult
from trendradar.crawler.sources.twitter import TwitterSource
from trendradar.crawler.sources.youtube import YouTubeSource
from trendradar.crawler.sources.reddit import RedditSource
from trendradar.crawler.sources.exa_search import ExaSearchSource
from trendradar.crawler.sources.xueqiu import XueqiuSource
from trendradar.crawler.sources.github_trending import GitHubTrendingSource
from trendradar.crawler.sources.podcast import PodcastSource
from trendradar.crawler.sources.xiaohongshu import XiaoHongShuSource
from trendradar.crawler.sources.linkedin import LinkedInSource
from trendradar.crawler.sources.v2ex import V2EXSource


# Registry tất cả sources
ALL_SOURCES: Dict[str, type] = {
    "twitter": TwitterSource,
    "youtube": YouTubeSource,
    "reddit": RedditSource,
    "exa_search": ExaSearchSource,
    "xueqiu": XueqiuSource,
    "github": GitHubTrendingSource,
    "podcast": PodcastSource,
    "xiaohongshu": XiaoHongShuSource,
    "linkedin": LinkedInSource,
    "v2ex": V2EXSource,
}


class ExternalSourceManager:
    """
    Quản lý external sources.

    Đọc cấu hình từ config.yaml section 'external_sources',
    khởi tạo các source được enabled, chạy fetch và gom kết quả.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Section 'external_sources' từ config.yaml
        """
        self.config = config
        self.enabled_sources: List[ExternalSource] = []
        self._init_sources()

    def _init_sources(self) -> None:
        """Khởi tạo các source được enabled trong config"""
        sources_config = self.config.get("sources", {})

        for source_id, source_cls in ALL_SOURCES.items():
            source_cfg = sources_config.get(source_id, {})

            # Mặc định disabled — phải bật tường minh
            if not source_cfg.get("enabled", False):
                continue

            source = source_cls()
            self.enabled_sources.append(source)

    def fetch_all(self, quiet: bool = False) -> List[SourceResult]:
        """
        Fetch từ tất cả enabled sources.

        Args:
            quiet: Nếu True thì không print log

        Returns:
            Danh sách SourceResult từ mỗi source
        """
        if not self.enabled_sources:
            if not quiet:
                print("[Sources] Không có external source nào được bật")
            return []

        sources_config = self.config.get("sources", {})
        results: List[SourceResult] = []

        if not quiet:
            names = [s.source_name for s in self.enabled_sources]
            print(f"[Sources] Bắt đầu fetch {len(self.enabled_sources)} nguồn: {', '.join(names)}")

        for source in self.enabled_sources:
            source_cfg = sources_config.get(source.source_id, {})

            if not quiet:
                print(f"[Sources] Đang fetch: {source.source_name}...", end=" ")

            # Check availability
            if not source.is_available():
                result = source._make_result(
                    error=f"{source.source_name} chưa sẵn sàng (tool chưa cài hoặc thiếu credentials)"
                )
                results.append(result)
                if not quiet:
                    print(f"⚠️ Không sẵn sàng")
                continue

            # Fetch
            try:
                result = source.fetch(source_cfg)
                results.append(result)

                if not quiet:
                    if result.success:
                        print(f"✅ {result.count} items")
                    else:
                        print(f"❌ {result.error}")

            except Exception as e:
                result = source._make_result(error=f"Unexpected error: {e}")
                results.append(result)
                if not quiet:
                    print(f"❌ Exception: {e}")

            # Interval giữa các source
            time.sleep(1)

        # Summary
        if not quiet:
            total_items = sum(r.count for r in results)
            success_count = sum(1 for r in results if r.success)
            print(f"[Sources] Hoàn thành: {success_count}/{len(results)} thành công, tổng {total_items} items")

        return results

    def get_all_items(self, quiet: bool = False) -> List[SourceItem]:
        """
        Fetch tất cả và gom thành 1 danh sách SourceItem phẳng.

        Returns:
            Danh sách tất cả SourceItem từ mọi source
        """
        results = self.fetch_all(quiet=quiet)
        all_items = []
        for result in results:
            all_items.extend(result.items)
        return all_items

    def get_status(self) -> List[Dict[str, Any]]:
        """
        Trả về trạng thái tất cả sources (cho doctor/status check).

        Returns:
            List of dicts: [{"id": ..., "name": ..., "enabled": ..., "available": ...}, ...]
        """
        sources_config = self.config.get("sources", {})
        status = []

        for source_id, source_cls in ALL_SOURCES.items():
            source_cfg = sources_config.get(source_id, {})
            enabled = source_cfg.get("enabled", False)

            source = source_cls()
            available = source.is_available() if enabled else None

            status.append({
                "id": source_id,
                "name": source.source_name,
                "enabled": enabled,
                "available": available,
            })

        return status

    @classmethod
    def from_config(cls, full_config: Dict[str, Any]) -> "ExternalSourceManager":
        """
        Factory: tạo manager từ full config dict.

        Args:
            full_config: Config dict đầy đủ (đọc từ config.yaml)
        """
        ext_config = full_config.get("EXTERNAL_SOURCES", full_config.get("external_sources", {}))
        return cls(ext_config)
