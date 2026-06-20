# coding=utf-8
"""
Exa Search Source

AI semantic web search — tìm tin tức theo topic thay vì chờ RSS.
Cài đặt: pip install exa-py (hoặc dùng qua mcporter)
API key: Miễn phí tại https://exa.ai

Capabilities: Semantic search, similar content discovery
"""

import json
import subprocess
import shutil
from typing import Dict, Any, List

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class ExaSearchSource(ExternalSource):
    """Exa AI semantic search source"""

    @property
    def source_id(self) -> str:
        return "exa_search"

    @property
    def source_name(self) -> str:
        return "Exa Search"

    def is_available(self) -> bool:
        """Kiểm tra exa SDK hoặc mcporter"""
        try:
            import exa_py  # noqa: F401
            return True
        except ImportError:
            pass
        return shutil.which("mcporter") is not None

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Search web bằng AI semantic.

        Config keys:
            api_key: str - Exa API key (hoặc env EXA_API_KEY)
            queries: List[str] - Search queries
            max_results: int - Số kết quả mỗi query (default: 10)
            use_autoprompt: bool - Exa tự tối ưu query (default: True)
            num_days: int - Chỉ lấy kết quả trong N ngày gần (default: 3)
        """
        queries = config.get("queries", [])
        max_results = config.get("max_results", 10)
        api_key = config.get("api_key", "")
        num_days = config.get("num_days", 3)

        if not queries:
            return self._make_result(error="Chưa cấu hình queries cho Exa Search")

        # Thử dùng exa-py SDK trước
        try:
            return self._fetch_with_sdk(queries, max_results, api_key, num_days)
        except ImportError:
            pass

        # Fallback: dùng mcporter
        if shutil.which("mcporter"):
            return self._fetch_with_mcporter(queries, max_results)

        return self._make_result(error="Cần cài exa-py (pip install exa-py) hoặc mcporter")

    def _fetch_with_sdk(
        self, queries: List[str], max_results: int, api_key: str, num_days: int
    ) -> SourceResult:
        """Fetch qua exa-py SDK"""
        import os
        from exa_py import Exa  # type: ignore

        key = api_key or os.environ.get("EXA_API_KEY", "")
        if not key:
            return self._make_result(error="Chưa cấu hình api_key cho Exa (hoặc set EXA_API_KEY env)")

        exa = Exa(api_key=key)
        all_items: List[SourceItem] = []
        errors: List[str] = []

        from datetime import datetime, timedelta
        start_date = (datetime.utcnow() - timedelta(days=num_days)).strftime("%Y-%m-%d")

        for query in queries:
            try:
                results = exa.search(
                    query,
                    num_results=max_results,
                    use_autoprompt=True,
                    start_published_date=start_date,
                )

                for r in results.results:
                    all_items.append(SourceItem(
                        title=r.title or query,
                        url=r.url,
                        source_id=self.source_id,
                        source_name=self.source_name,
                        published_at=r.published_date if hasattr(r, "published_date") else None,
                        author=r.author if hasattr(r, "author") else None,
                        summary=r.text[:300] if hasattr(r, "text") and r.text else None,
                        metadata={
                            "query": query,
                            "score": r.score if hasattr(r, "score") else None,
                        },
                    ))
            except Exception as e:
                errors.append(f"Query '{query}': {e}")

        if not all_items and errors:
            return self._make_result(error="; ".join(errors))

        return self._make_result(items=all_items)

    def _fetch_with_mcporter(self, queries: List[str], max_results: int) -> SourceResult:
        """Fallback: dùng mcporter CLI"""
        all_items: List[SourceItem] = []
        errors: List[str] = []

        for query in queries:
            try:
                cmd = [
                    "mcporter", "call",
                    f"exa.web_search_exa(query=\"{query}\", num_results={max_results})",
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding="utf-8",
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    results_list = data.get("results", []) if isinstance(data, dict) else []
                    for r in results_list:
                        all_items.append(SourceItem(
                            title=r.get("title", query),
                            url=r.get("url", ""),
                            source_id=self.source_id,
                            source_name=self.source_name,
                            published_at=r.get("published_date"),
                            summary=r.get("text", "")[:300] if r.get("text") else None,
                            metadata={"query": query},
                        ))
                else:
                    errors.append(f"mcporter query '{query}': {result.stderr.strip()[:100]}")
            except Exception as e:
                errors.append(f"mcporter query '{query}': {e}")

        if not all_items and errors:
            return self._make_result(error="; ".join(errors))

        return self._make_result(items=all_items)
