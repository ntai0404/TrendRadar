# coding=utf-8
"""
XiaoHongShu (小红书) Source — PLACEHOLDER

Chưa hoàn thiện. Cần cài OpenCLI hoặc xiaohongshu-mcp.
Desktop: OpenCLI (browser session)
Server: xiaohongshu-mcp (QR login)

Capabilities: Search notes, read note detail, comments
"""

import json
import subprocess
import shutil
from typing import Dict, Any, List

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class XiaoHongShuSource(ExternalSource):
    """XiaoHongShu (小红书) source — PLACEHOLDER"""

    @property
    def source_id(self) -> str:
        return "xiaohongshu"

    @property
    def source_name(self) -> str:
        return "XiaoHongShu (小红书)"

    def is_available(self) -> bool:
        """Kiểm tra opencli đã cài chưa"""
        return shutil.which("opencli") is not None

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Fetch notes từ XiaoHongShu.

        Config keys:
            search_queries: List[str] - Search queries
            max_results: int - Số note tối đa mỗi query (default: 10)

        TODO: Implement khi có nhu cầu thực tế
        """
        if not self.is_available():
            return self._make_result(
                error="[PLACEHOLDER] opencli chưa cài. Xem: https://github.com/jackwener/opencli"
            )

        search_queries = config.get("search_queries", [])
        max_results = config.get("max_results", 10)

        if not search_queries:
            return self._make_result(error="Chưa cấu hình search_queries cho XiaoHongShu")

        all_items: List[SourceItem] = []
        errors: List[str] = []

        for query in search_queries:
            try:
                cmd = [
                    "opencli", "xiaohongshu", "search", query,
                    "-n", str(max_results), "-f", "json",
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding="utf-8",
                )
                if result.returncode == 0:
                    notes = json.loads(result.stdout)
                    if isinstance(notes, list):
                        for note in notes:
                            title = note.get("title", "") or note.get("desc", "")[:80]
                            if not title:
                                continue
                            all_items.append(SourceItem(
                                title=title,
                                url=note.get("url", note.get("note_url", "")),
                                source_id=self.source_id,
                                source_name=self.source_name,
                                author=note.get("user", {}).get("nickname", ""),
                                summary=note.get("desc", "")[:200],
                                metadata={
                                    "query": query,
                                    "likes": note.get("liked_count", 0),
                                },
                            ))
                else:
                    errors.append(f"Query '{query}': {result.stderr.strip()[:100]}")
            except Exception as e:
                errors.append(f"Query '{query}': {e}")

        if not all_items and errors:
            return self._make_result(error="; ".join(errors))

        return self._make_result(items=all_items)
