# coding=utf-8
"""
V2EX Source — PLACEHOLDER

Cộng đồng tech Trung Quốc. Public JSON API, không cần auth.
Zero config.

Capabilities: Hot topics, node topics, topic detail + replies
"""

import json
from typing import Dict, Any, List

import requests

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class V2EXSource(ExternalSource):
    """V2EX tech community source — PLACEHOLDER"""

    @property
    def source_id(self) -> str:
        return "v2ex"

    @property
    def source_name(self) -> str:
        return "V2EX"

    # V2EX public API
    HOT_URL = "https://www.v2ex.com/api/topics/hot.json"
    LATEST_URL = "https://www.v2ex.com/api/topics/latest.json"

    def is_available(self) -> bool:
        """V2EX public API luôn available"""
        return True

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Fetch V2EX hot/latest topics.

        Config keys:
            mode: str - "hot" hoặc "latest" (default: "hot")
            nodes: List[str] - Node IDs to follow (vd: ["python", "ai"])
            max_results: int - Số topic tối đa (default: 15)

        TODO: Implement node-specific fetch khi cần
        """
        mode = config.get("mode", "hot")
        max_results = config.get("max_results", 15)

        url = self.HOT_URL if mode == "hot" else self.LATEST_URL

        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "TrendRadar/2.0"
            })
            resp.raise_for_status()
            topics = resp.json()
        except Exception as e:
            return self._make_result(error=f"V2EX API error: {e}")

        items = []
        for topic in topics[:max_results]:
            title = topic.get("title", "")
            if not title:
                continue

            node = topic.get("node", {})
            member = topic.get("member", {})

            items.append(SourceItem(
                title=title,
                url=f"https://www.v2ex.com/t/{topic.get('id', '')}",
                source_id=self.source_id,
                source_name=self.source_name,
                published_at=str(topic.get("created", "")),
                author=member.get("username", ""),
                summary=topic.get("content", "")[:200] if topic.get("content") else None,
                metadata={
                    "type": mode,
                    "node": node.get("name", ""),
                    "node_title": node.get("title", ""),
                    "replies": topic.get("replies", 0),
                },
            ))

        return self._make_result(items=items)
