# coding=utf-8
"""
RSS parser

Supports parsing of RSS 2.0, Atom and JSON Feed 1.1 formats
"""

import re
import html
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from email.utils import parsedate_to_datetime

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    feedparser = None


@dataclass
class ParsedRSSItem:
    """Parsed RSS entry"""
    title: str
    url: str
    published_at: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    guid: Optional[str] = None


class RSSParser:
    """RSS Parser"""

    def __init__(self, max_summary_length: int = 500):
        """
        Initialize the parser

        Args:
            max_summary_length: maximum length of summary
        """
        if not HAS_FEEDPARSER:
            raise ImportError("RSS parsing requires installation of feedparser: pip install feedparser")

        self.max_summary_length = max_summary_length

    def parse(self, content: str, feed_url: str = "") -> List[ParsedRSSItem]:
        """
        Parse RSS/Atom/JSON Feed content

        Args:
            content: Feed content (XML or JSON)
            feed_url: Feed URL (for error prompts)

        Returns:
            Parsed list of entries
        """
        # First try to detect JSON Feed
        if self._is_json_feed(content):
            return self._parse_json_feed(content, feed_url)

        # Use feedparser to parse RSS/Atom
        feed = feedparser.parse(content)

        if feed.bozo and not feed.entries:
            raise ValueError(f"RSS parsing failed ({feed_url}): {feed.bozo_exception}")

        items = []
        for entry in feed.entries:
            item = self._parse_entry(entry)
            if item:
                items.append(item)

        return items

    def _is_json_feed(self, content: str) -> bool:
        """
        Detect if content is in JSON feed format

        The JSON feed must contain a version field with a value of https://jsonfeed.org/version/1 or 1.1
        """
        content = content.strip()
        if not content.startswith("{"):
            return False

        try:
            data = json.loads(content)
            version = data.get("version", "")
            return "jsonfeed.org" in version
        except (json.JSONDecodeError, TypeError):
            return False

    def _parse_json_feed(self, content: str, feed_url: str = "") -> List[ParsedRSSItem]:
        """
        Parse JSON Feed 1.1 format

        JSON Feed specification: https://www.jsonfeed.org/version/1.1/

        Args:
            content: JSON Feed content
            feed_url: Feed URL (for error prompts)

        Returns:
            Parsed list of entries
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON Feed parsing failed ({feed_url}): {e}")

        items_data = data.get("items", [])
        if not items_data:
            return []

        items = []
        for item_data in items_data:
            item = self._parse_json_feed_item(item_data)
            if item:
                items.append(item)

        return items

    def _parse_json_feed_item(self, item_data: Dict[str, Any]) -> Optional[ParsedRSSItem]:
        """Parse a single JSON feed entry"""
        url = item_data.get("url", "") or item_data.get("external_url", "")

        title = item_data.get("title", "")
        if not title:
            content_text = item_data.get("content_text", "")
            if content_text:
                title = content_text[:20] + ("..." if len(content_text) > 20 else "")

        title = self._clean_text(title)
        if not title and url:
            title = url
        if not title:
            return None

        # Release time (ISO 8601 format)
        published_at = None
        date_str = item_data.get("date_published") or item_data.get("date_modified")
        if date_str:
            published_at = self._parse_iso_date(date_str)

        # Summary: Prioritize summary, otherwise use content_text
        summary = item_data.get("summary", "")
        if not summary:
            content_text = item_data.get("content_text", "")
            content_html = item_data.get("content_html", "")
            summary = content_text or self._clean_text(content_html)

        if summary:
            summary = self._clean_text(summary)
            if len(summary) > self.max_summary_length:
                summary = summary[:self.max_summary_length] + "..."

        # author
        author = None
        authors = item_data.get("authors", [])
        if authors:
            names = [a.get("name", "") for a in authors if isinstance(a, dict) and a.get("name")]
            if names:
                author = ", ".join(names)

        # GUID
        guid = item_data.get("id", "") or url

        return ParsedRSSItem(
            title=title,
            url=url,
            published_at=published_at,
            summary=summary or None,
            author=author,
            guid=guid,
        )

    def _parse_iso_date(self, date_str: str) -> Optional[str]:
        """Parse ISO 8601 date format"""
        if not date_str:
            return None

        try:
            # Handle common ISO 8601 formats
            # Replace Z with +00:00
            date_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(date_str)
            return dt.isoformat()
        except (ValueError, TypeError):
            pass

        return None

    def parse_url(self, url: str, timeout: int = 10) -> List[ParsedRSSItem]:
        """
        Parse RSS from URL

        Args:
            url: RSS URL
            timeout: timeout (seconds)

        Returns:
            Parsed list of entries
        """
        import requests

        response = requests.get(url, timeout=timeout, headers={
            "User-Agent": "TrendRadar/2.0 RSS Reader"
        })
        response.raise_for_status()

        return self.parse(response.text, url)

    def _parse_entry(self, entry: Any) -> Optional[ParsedRSSItem]:
        """Parse a single entry"""
        title = self._clean_text(entry.get("title", ""))

        url = entry.get("link", "")
        if not url:
            links = entry.get("links", [])
            for link in links:
                if link.get("rel") == "alternate" or link.get("type", "").startswith("text/html"):
                    url = link.get("href", "")
                    break
            if not url and links:
                url = links[0].get("href", "")

        if not title:
            raw_summary = entry.get("summary") or entry.get("description", "")
            if not raw_summary:
                content = entry.get("content", [])
                if content and isinstance(content, list):
                    raw_summary = content[0].get("value", "")
            if raw_summary:
                title = self._clean_text(raw_summary)
                if len(title) > 20:
                    title = title[:20] + "..."
            if not title and url:
                title = url

        if not title:
            return None

        published_at = self._parse_date(entry)
        summary = self._parse_summary(entry)
        author = self._parse_author(entry)
        guid = entry.get("id") or entry.get("guid", {}).get("value") or url

        return ParsedRSSItem(
            title=title,
            url=url,
            published_at=published_at,
            summary=summary,
            author=author,
            guid=guid,
        )

    def _clean_text(self, text: str) -> str:
        """Clean text"""
        if not text:
            return ""

        # Decode HTML entities
        text = html.unescape(text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _parse_date(self, entry: Any) -> Optional[str]:
        """Parse release date"""
        # feedparser will automatically parse the date into published_parsed
        date_struct = entry.get("published_parsed") or entry.get("updated_parsed")

        if date_struct:
            try:
                dt = datetime(*date_struct[:6])
                return dt.isoformat()
            except (ValueError, TypeError):
                pass

        # Try to parse manually
        date_str = entry.get("published") or entry.get("updated")
        if date_str:
            try:
                dt = parsedate_to_datetime(date_str)
                return dt.isoformat()
            except (ValueError, TypeError):
                pass

            # Try ISO format
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.isoformat()
            except (ValueError, TypeError):
                pass

        return None

    def _parse_summary(self, entry: Any) -> Optional[str]:
        """Analysis summary"""
        summary = entry.get("summary") or entry.get("description", "")

        if not summary:
            # Try to get from content
            content = entry.get("content", [])
            if content and isinstance(content, list):
                summary = content[0].get("value", "")

        if not summary:
            return None

        summary = self._clean_text(summary)

        # Truncate too long abstracts
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length] + "..."

        return summary

    def _parse_author(self, entry: Any) -> Optional[str]:
        """Analyze the author"""
        author = entry.get("author")
        if author:
            return self._clean_text(author)

        # Try to get from dc:creator
        author = entry.get("dc_creator")
        if author:
            return self._clean_text(author)

        # Try to get from the authors list
        authors = entry.get("authors", [])
        if authors:
            names = [a.get("name", "") for a in authors if a.get("name")]
            if names:
                return ", ".join(names)

        return None
