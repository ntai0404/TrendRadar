# coding=utf-8
"""
LinkedIn Source — PLACEHOLDER

Đọc profiles, companies, job search.
Yêu cầu: linkedin-scraper-mcp (cần browser login)
Hoặc Jina Reader cho public pages.

Capabilities: Profile detail, company pages, job search
"""

import json
import subprocess
import shutil
from typing import Dict, Any, List

import requests

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class LinkedInSource(ExternalSource):
    """LinkedIn source — PLACEHOLDER"""

    @property
    def source_id(self) -> str:
        return "linkedin"

    @property
    def source_name(self) -> str:
        return "LinkedIn"

    def is_available(self) -> bool:
        """LinkedIn qua Jina Reader luôn available"""
        return True

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Fetch LinkedIn content.

        Config keys:
            profiles: List[str] - LinkedIn profile URLs to read
            companies: List[str] - Company page URLs
            job_queries: List[str] - Job search queries
            use_jina: bool - Dùng Jina Reader (default: True)

        TODO: Tích hợp linkedin-scraper-mcp khi có nhu cầu
        """
        profiles = config.get("profiles", [])
        companies = config.get("companies", [])
        urls = profiles + companies

        if not urls:
            return self._make_result(error="[PLACEHOLDER] Chưa cấu hình profiles/companies cho LinkedIn")

        all_items: List[SourceItem] = []
        errors: List[str] = []

        # Dùng Jina Reader cho public pages
        for url in urls:
            try:
                jina_url = f"https://r.jina.ai/{url}"
                resp = requests.get(jina_url, timeout=20, headers={"Accept": "text/plain"})
                if resp.status_code == 200:
                    content = resp.text
                    # Extract title (first meaningful line)
                    lines = [l.strip() for l in content.split("\n") if l.strip()]
                    title = lines[0][:100] if lines else url

                    all_items.append(SourceItem(
                        title=title,
                        url=url,
                        source_id=self.source_id,
                        source_name=self.source_name,
                        content=content[:2000],
                        summary=content[:300],
                        metadata={"type": "jina_reader"},
                    ))
                else:
                    errors.append(f"{url}: HTTP {resp.status_code}")
            except Exception as e:
                errors.append(f"{url}: {e}")

        if not all_items and errors:
            return self._make_result(error="; ".join(errors))

        return self._make_result(items=all_items)
