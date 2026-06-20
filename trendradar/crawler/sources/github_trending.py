# coding=utf-8
"""
GitHub Trending Source

Theo dõi trending repos, tech trend.
Sử dụng: gh CLI (zero config cho public repos) hoặc GitHub API.
Cài đặt gh CLI: https://cli.github.com

Capabilities: Trending repos, search repos/issues, starred repos
"""

import json
import subprocess
import shutil
from typing import Dict, Any, List

import requests

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class GitHubTrendingSource(ExternalSource):
    """GitHub trending repos source"""

    @property
    def source_id(self) -> str:
        return "github"

    @property
    def source_name(self) -> str:
        return "GitHub Trending"

    # GitHub trending không có API chính thức, dùng unofficial hoặc gh search
    TRENDING_API = "https://api.gitterapp.com/repositories"

    def is_available(self) -> bool:
        """gh CLI hoặc requests đều OK"""
        return True  # requests luôn available

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Fetch GitHub trending repos hoặc search.

        Config keys:
            language: str - Filter theo ngôn ngữ (vd: "python", default: "")
            since: str - Khoảng thời gian: daily, weekly, monthly (default: "daily")
            search_queries: List[str] - GitHub search queries (vd: ["LLM framework", "AI agent"])
            max_results: int - Số repo tối đa (default: 15)
        """
        language = config.get("language", "")
        since = config.get("since", "daily")
        search_queries = config.get("search_queries", [])
        max_results = config.get("max_results", 15)

        all_items: List[SourceItem] = []
        errors: List[str] = []

        # Lấy trending repos
        try:
            items = self._fetch_trending(language, since, max_results)
            all_items.extend(items)
        except Exception as e:
            errors.append(f"Trending: {e}")

        # Search queries (qua gh CLI nếu có)
        for query in search_queries:
            try:
                items = self._search_repos(query, max_results)
                all_items.extend(items)
            except Exception as e:
                errors.append(f"Search '{query}': {e}")

        if not all_items and errors:
            return self._make_result(error="; ".join(errors))

        return self._make_result(items=all_items)

    def _fetch_trending(self, language: str, since: str, max_results: int) -> List[SourceItem]:
        """Fetch trending repos từ unofficial API"""
        params = {"since": since}
        if language:
            params["language"] = language

        try:
            resp = requests.get(self.TRENDING_API, params=params, timeout=15)
            resp.raise_for_status()
            repos = resp.json()
        except Exception:
            # Fallback: dùng gh CLI search
            return self._search_repos(f"stars:>100 pushed:>2026-06-15", max_results)

        items = []
        for repo in repos[:max_results]:
            name = repo.get("author", "") + "/" + repo.get("name", "")
            description = repo.get("description", "") or ""
            stars = repo.get("stars", 0)
            current_stars = repo.get("currentPeriodStars", 0)
            lang = repo.get("language", "")

            title = f"⭐ {name} (+{current_stars} stars)"
            if lang:
                title += f" [{lang}]"

            items.append(SourceItem(
                title=title,
                url=repo.get("url", f"https://github.com/{name}"),
                source_id=self.source_id,
                source_name=self.source_name,
                summary=description[:200] if description else None,
                metadata={
                    "type": "trending",
                    "stars": stars,
                    "current_period_stars": current_stars,
                    "language": lang,
                    "forks": repo.get("forks", 0),
                },
            ))

        return items

    def _search_repos(self, query: str, max_results: int) -> List[SourceItem]:
        """Search repos via gh CLI hoặc API"""
        # Thử gh CLI trước
        if shutil.which("gh"):
            try:
                cmd = [
                    "gh", "search", "repos", query,
                    "--limit", str(max_results),
                    "--json", "fullName,description,url,stargazersCount,language,updatedAt",
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding="utf-8",
                )
                if result.returncode == 0:
                    repos = json.loads(result.stdout)
                    items = []
                    for repo in repos:
                        items.append(SourceItem(
                            title=f"{repo.get('fullName', '')} (⭐{repo.get('stargazersCount', 0)})",
                            url=repo.get("url", ""),
                            source_id=self.source_id,
                            source_name=self.source_name,
                            published_at=repo.get("updatedAt", ""),
                            summary=repo.get("description", "")[:200] if repo.get("description") else None,
                            metadata={
                                "type": "search",
                                "query": query,
                                "language": repo.get("language", ""),
                                "stars": repo.get("stargazersCount", 0),
                            },
                        ))
                    return items
            except Exception:
                pass

        # Fallback: GitHub API (unauthenticated, rate-limited)
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "stars", "per_page": max_results},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            items = []
            for repo in data.get("items", []):
                items.append(SourceItem(
                    title=f"{repo.get('full_name', '')} (⭐{repo.get('stargazers_count', 0)})",
                    url=repo.get("html_url", ""),
                    source_id=self.source_id,
                    source_name=self.source_name,
                    published_at=repo.get("updated_at", ""),
                    summary=repo.get("description", "")[:200] if repo.get("description") else None,
                    metadata={
                        "type": "search",
                        "query": query,
                        "language": repo.get("language", ""),
                        "stars": repo.get("stargazers_count", 0),
                    },
                ))
            return items
        except Exception as e:
            raise RuntimeError(f"GitHub API: {e}")
