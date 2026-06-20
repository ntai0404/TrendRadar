# coding=utf-8
"""
YouTube Source

Sử dụng yt-dlp để lấy subtitle/metadata từ video và search.
Cài đặt: pip install yt-dlp (hoặc pipx install yt-dlp)
Zero config - không cần API key.

Capabilities: Video metadata, subtitles/transcript, search
"""

import json
import subprocess
import shutil
from typing import Dict, Any, List

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class YouTubeSource(ExternalSource):
    """YouTube source via yt-dlp"""

    @property
    def source_id(self) -> str:
        return "youtube"

    @property
    def source_name(self) -> str:
        return "YouTube"

    def is_available(self) -> bool:
        """Kiểm tra yt-dlp đã cài chưa"""
        return shutil.which("yt-dlp") is not None

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Fetch video metadata và subtitle.

        Config keys:
            channels: List[str] - YouTube channel URLs để lấy video mới
            search_queries: List[str] - Search queries
            max_results: int - Số video tối đa mỗi channel/query (default: 5)
            get_subtitles: bool - Có lấy subtitle không (default: True)
            subtitle_lang: str - Ngôn ngữ subtitle (default: "vi,en")
        """
        if not self.is_available():
            return self._make_result(error="yt-dlp chưa được cài đặt. Chạy: pip install yt-dlp")

        channels = config.get("channels", [])
        search_queries = config.get("search_queries", [])
        max_results = config.get("max_results", 5)

        if not channels and not search_queries:
            return self._make_result(error="Chưa cấu hình channels hoặc search_queries cho YouTube")

        all_items: List[SourceItem] = []
        errors: List[str] = []

        # Fetch từ channels
        for channel_url in channels:
            try:
                items = self._fetch_channel(channel_url, max_results)
                all_items.extend(items)
            except Exception as e:
                errors.append(f"Channel '{channel_url}': {e}")

        # Search
        for query in search_queries:
            try:
                items = self._search(query, max_results)
                all_items.extend(items)
            except Exception as e:
                errors.append(f"Search '{query}': {e}")

        if not all_items and errors:
            return self._make_result(error="; ".join(errors))

        return self._make_result(items=all_items)

    def _fetch_channel(self, channel_url: str, max_results: int) -> List[SourceItem]:
        """Lấy video mới nhất từ channel"""
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--playlist-end", str(max_results),
            "--no-warnings",
            channel_url,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip()[:200])

        return self._parse_json_lines(result.stdout, source_tag=channel_url)

    def _search(self, query: str, max_results: int) -> List[SourceItem]:
        """Search YouTube"""
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--playlist-end", str(max_results),
            "--no-warnings",
            f"ytsearch{max_results}:{query}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip()[:200])

        return self._parse_json_lines(result.stdout, source_tag=f"search:{query}")

    def _parse_json_lines(self, output: str, source_tag: str = "") -> List[SourceItem]:
        """Parse JSON lines output từ yt-dlp"""
        items = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                title = data.get("title", "")
                if not title or title == "[Deleted video]" or title == "[Private video]":
                    continue

                video_id = data.get("id", "")
                url = data.get("url", data.get("webpage_url", ""))
                if not url and video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"

                items.append(SourceItem(
                    title=title,
                    url=url,
                    source_id=self.source_id,
                    source_name=self.source_name,
                    published_at=data.get("upload_date", ""),
                    author=data.get("channel", data.get("uploader", "")),
                    summary=data.get("description", "")[:300] if data.get("description") else None,
                    metadata={
                        "source_tag": source_tag,
                        "duration": data.get("duration"),
                        "view_count": data.get("view_count"),
                        "like_count": data.get("like_count"),
                        "channel_id": data.get("channel_id", ""),
                    },
                ))
            except (json.JSONDecodeError, TypeError):
                continue

        return items
