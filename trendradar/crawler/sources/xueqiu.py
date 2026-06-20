# coding=utf-8
"""
Xueqiu (雪球) Source

Theo dõi sentiment chứng khoán Trung Quốc — ảnh hưởng thị trường VN.
Yêu cầu: Browser cookie (cấu hình qua agent-reach configure)

Capabilities: Stock quotes, hot posts, hot stocks, search
"""

import json
import subprocess
import shutil
import os
from typing import Dict, Any, List

import requests

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class XueqiuSource(ExternalSource):
    """Xueqiu (雪球) source"""

    @property
    def source_id(self) -> str:
        return "xueqiu"

    @property
    def source_name(self) -> str:
        return "Xueqiu (雪球)"

    # Xueqiu API endpoints
    HOT_POSTS_URL = "https://xueqiu.com/statuses/hot/listV2.json"
    HOT_STOCKS_URL = "https://stock.xueqiu.com/v5/stock/hot_stock/list.json"

    def is_available(self) -> bool:
        """Kiểm tra cookie hoặc agent-reach cấu hình"""
        cookie = self._get_cookie()
        return bool(cookie)

    def _get_cookie(self) -> str:
        """Lấy cookie từ config hoặc agent-reach"""
        # Thử từ env
        cookie = os.environ.get("XUEQIU_COOKIE", "")
        if cookie:
            return cookie

        # Thử từ agent-reach config file
        config_path = os.path.expanduser("~/.agent-reach/config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("cookies", {}).get("xueqiu", "")
            except Exception:
                pass

        return ""

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Fetch hot posts và hot stocks từ Xueqiu.

        Config keys:
            cookie: str - Xueqiu cookie (override env/config)
            max_results: int - Số post tối đa (default: 15)
            include_hot_stocks: bool - Có lấy cổ phiếu hot không (default: True)
        """
        cookie = config.get("cookie", "") or self._get_cookie()
        if not cookie:
            return self._make_result(
                error="Chưa cấu hình Xueqiu cookie. Set env XUEQIU_COOKIE hoặc dùng agent-reach configure"
            )

        max_results = config.get("max_results", 15)
        include_hot_stocks = config.get("include_hot_stocks", True)

        all_items: List[SourceItem] = []
        errors: List[str] = []

        # Lấy hot posts
        try:
            items = self._fetch_hot_posts(cookie, max_results)
            all_items.extend(items)
        except Exception as e:
            errors.append(f"Hot posts: {e}")

        # Lấy hot stocks
        if include_hot_stocks:
            try:
                items = self._fetch_hot_stocks(cookie)
                all_items.extend(items)
            except Exception as e:
                errors.append(f"Hot stocks: {e}")

        if not all_items and errors:
            return self._make_result(error="; ".join(errors))

        return self._make_result(items=all_items)

    def _fetch_hot_posts(self, cookie: str, max_results: int) -> List[SourceItem]:
        """Lấy bài viết hot"""
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        params = {"a": "1", "count": str(max_results), "type": "10"}

        resp = requests.get(self.HOT_POSTS_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for item in data.get("items", []):
            original = item.get("original_status", item)
            title = original.get("title", "") or original.get("description", "")[:100]
            if not title:
                continue

            user = original.get("user", {})
            items.append(SourceItem(
                title=title,
                url=f"https://xueqiu.com{original.get('target', '')}",
                source_id=self.source_id,
                source_name=self.source_name,
                published_at=str(original.get("created_at", "")),
                author=user.get("screen_name", ""),
                metadata={
                    "type": "hot_post",
                    "reply_count": original.get("reply_count", 0),
                    "retweet_count": original.get("retweet_count", 0),
                    "like_count": original.get("like_count", 0),
                },
            ))

        return items

    def _fetch_hot_stocks(self, cookie: str) -> List[SourceItem]:
        """Lấy cổ phiếu hot"""
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        params = {"size": "10", "type": "10", "_type": "10"}

        resp = requests.get(self.HOT_STOCKS_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for stock in data.get("data", {}).get("items", []):
            name = stock.get("name", "")
            symbol = stock.get("symbol", "")
            if not name:
                continue

            percent = stock.get("percent", 0)
            current = stock.get("current", 0)
            title = f"🔥 {name} ({symbol}) {percent:+.2f}% @ {current}"

            items.append(SourceItem(
                title=title,
                url=f"https://xueqiu.com/S/{symbol}",
                source_id=self.source_id,
                source_name=self.source_name,
                metadata={
                    "type": "hot_stock",
                    "symbol": symbol,
                    "percent": percent,
                    "current": current,
                    "volume": stock.get("volume", 0),
                },
            ))

        return items
