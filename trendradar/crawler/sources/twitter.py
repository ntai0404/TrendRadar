# coding=utf-8
"""
Twitter/X Source

Sử dụng twitter-cli (cookie-based, miễn phí) để search tweets.
Cài đặt: pipx install twitter-cli
Cấu hình cookie: agent-reach configure twitter-cookies "..."

Capabilities: Search tweets, read timeline, read profiles
"""

import json
import subprocess
import shutil
from typing import Dict, Any, List

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class TwitterSource(ExternalSource):
    """Twitter/X source via twitter-cli"""

    @property
    def source_id(self) -> str:
        return "twitter"

    @property
    def source_name(self) -> str:
        return "Twitter/X"

    def is_available(self) -> bool:
        """Kiểm tra twitter-cli đã cài và có cookie chưa"""
        if shutil.which("twitter") is None:
            return False
        # twitter-cli cần TWITTER_AUTH_TOKEN + TWITTER_CT0 env vars
        import os
        return bool(os.environ.get("TWITTER_AUTH_TOKEN") and os.environ.get("TWITTER_CT0"))

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Fetch tweets theo queries cấu hình.

        Config keys:
            queries: List[str] - Danh sách search queries
            max_results: int - Số tweet tối đa mỗi query (default: 10)
            language: str - Ngôn ngữ filter (default: None)
        """
        if not self.is_available():
            return self._make_result(error="twitter-cli chưa được cài đặt. Chạy: pipx install twitter-cli")

        queries = config.get("queries", [])
        max_results = config.get("max_results", 10)

        if not queries:
            return self._make_result(error="Chưa cấu hình queries cho Twitter")

        all_items: List[SourceItem] = []
        errors: List[str] = []

        for query in queries:
            try:
                cmd = ["twitter", "search", query, "-n", str(max_results), "--json"]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding="utf-8",
                )

                if result.returncode != 0:
                    errors.append(f"Query '{query}': {result.stderr.strip()}")
                    continue

                tweets = self._parse_output(result.stdout, query)
                all_items.extend(tweets)

            except subprocess.TimeoutExpired:
                errors.append(f"Query '{query}': timeout")
            except Exception as e:
                errors.append(f"Query '{query}': {e}")

        if not all_items and errors:
            return self._make_result(error="; ".join(errors))

        return self._make_result(items=all_items)

    def _parse_output(self, output: str, query: str) -> List[SourceItem]:
        """Parse JSON output từ twitter-cli"""
        items = []
        try:
            data = json.loads(output)

            # twitter-cli format: {"ok": true, "data": [...]}
            if isinstance(data, dict) and "data" in data:
                tweets = data["data"]
            elif isinstance(data, list):
                tweets = data
            else:
                tweets = data.get("tweets", [])

            for tweet in tweets:
                if not isinstance(tweet, dict):
                    continue

                text = tweet.get("text", "")
                if not text:
                    continue

                # Build URL
                tweet_id = tweet.get("id", "")
                author_info = tweet.get("author", {})
                screen_name = author_info.get("screenName", "") if isinstance(author_info, dict) else ""
                author_name = author_info.get("name", screen_name) if isinstance(author_info, dict) else str(author_info)

                if tweet_id and screen_name:
                    url = f"https://x.com/{screen_name}/status/{tweet_id}"
                else:
                    url = f"https://x.com/search?q={query}"

                created_at = tweet.get("createdAtISO", tweet.get("createdAt", ""))
                metrics = tweet.get("metrics", {})

                # Dùng 100 ký tự đầu làm title nếu tweet dài
                title = text[:100] + ("..." if len(text) > 100 else "")

                items.append(SourceItem(
                    title=title,
                    url=url,
                    source_id=self.source_id,
                    source_name=self.source_name,
                    published_at=created_at,
                    author=author_name or screen_name,
                    content=text,
                    metadata={
                        "query": query,
                        "likes": metrics.get("likes", 0),
                        "retweets": metrics.get("retweets", 0),
                        "views": metrics.get("views", 0),
                    },
                ))
        except (json.JSONDecodeError, TypeError):
            # Nếu output không phải JSON, parse line-by-line
            for line in output.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("{"):
                    items.append(SourceItem(
                        title=line[:100],
                        url=f"https://x.com/search?q={query}",
                        source_id=self.source_id,
                        source_name=self.source_name,
                        content=line,
                        metadata={"query": query},
                    ))

        return items
