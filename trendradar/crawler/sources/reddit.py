# coding=utf-8
"""
Reddit Source

Sử dụng rdt-cli hoặc OpenCLI để đọc Reddit posts.
Cài đặt: pipx install 'git+https://github.com/public-clis/rdt-cli.git'
Login: rdt login

Capabilities: Search posts, read subreddit, read comments
"""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List

from trendradar.crawler.sources.base import ExternalSource, SourceItem, SourceResult


class RedditSource(ExternalSource):
    """Reddit source via rdt-cli"""

    @property
    def source_id(self) -> str:
        return "reddit"

    @property
    def source_name(self) -> str:
        return "Reddit"

    def is_available(self) -> bool:
        """Kiểm tra rdt-cli đã cài chưa"""
        return shutil.which("rdt") is not None or Path.home().joinpath(".local", "bin", "rdt.exe").exists()

    def _get_rdt_cmd(self) -> list:
        """Not used directly — see _run_rdt"""
        return []

    def _run_rdt(self, args: list) -> subprocess.CompletedProcess:
        """Run rdt command via its pipx venv python to avoid exe entry point issues on Windows"""
        import os

        # Use pipx venv python + rdt_cli.cli directly
        pipx_venv_python = Path.home() / "pipx" / "venvs" / "rdt-cli" / "Scripts" / "python.exe"
        if pipx_venv_python.exists():
            # Build a small inline script that calls rdt_cli.cli
            args_repr = repr(args)
            script = f"from rdt_cli.cli import cli; cli({args_repr})"
            cmd = [str(pipx_venv_python), "-c", script]
        else:
            # Fallback: rdt exe (may crash on some Windows setups)
            rdt_exe = shutil.which("rdt") or str(Path.home() / ".local" / "bin" / "rdt.exe")
            cmd = [rdt_exe] + args

        env = os.environ.copy()
        pipx_bin = str(Path.home() / ".local" / "bin")
        if pipx_bin not in env.get("PATH", ""):
            env["PATH"] = pipx_bin + os.pathsep + env.get("PATH", "")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        return result

    def fetch(self, config: Dict[str, Any]) -> SourceResult:
        """
        Fetch Reddit posts.

        Config keys:
            subreddits: List[str] - Subreddits to monitor (vd: ["VietNam", "wallstreetbets"])
            search_queries: List[str] - Search queries
            max_results: int - Số post tối đa mỗi subreddit/query (default: 10)
            sort: str - Sắp xếp: hot, new, top (default: "hot")
        """
        if not self.is_available():
            return self._make_result(
                error="rdt-cli chưa được cài đặt. Chạy: pipx install 'git+https://github.com/public-clis/rdt-cli.git' && rdt login"
            )

        subreddits = config.get("subreddits", [])
        search_queries = config.get("search_queries", [])
        max_results = config.get("max_results", 10)
        sort = config.get("sort", "hot")

        if not subreddits and not search_queries:
            return self._make_result(error="Chưa cấu hình subreddits hoặc search_queries cho Reddit")

        all_items: List[SourceItem] = []
        errors: List[str] = []

        # Fetch từ subreddits
        for sub in subreddits:
            try:
                items = self._fetch_subreddit(sub, max_results, sort)
                all_items.extend(items)
            except Exception as e:
                errors.append(f"r/{sub}: {e}")

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

    def _fetch_subreddit(self, subreddit: str, max_results: int, sort: str) -> List[SourceItem]:
        """Lấy posts từ subreddit via search"""
        result = self._run_rdt(["search", f"subreddit:{subreddit}", "-n", str(max_results), "--json"])

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip()[:200])

        return self._parse_output(result.stdout, tag=f"r/{subreddit}")

    def _search(self, query: str, max_results: int) -> List[SourceItem]:
        """Search Reddit"""
        result = self._run_rdt(["search", query, "-n", str(max_results), "--json"])

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip()[:200])

        return self._parse_output(result.stdout, tag=f"search:{query}")

    def _parse_output(self, output: str, tag: str = "") -> List[SourceItem]:
        """Parse JSON output từ rdt-cli"""
        items = []
        try:
            data = json.loads(output)

            # rdt-cli format: {"ok": true, "data": {"kind": "Listing", "data": {"children": [...]}}}
            if isinstance(data, dict) and "data" in data:
                listing = data["data"]
                if isinstance(listing, dict) and "data" in listing:
                    children = listing["data"].get("children", [])
                elif isinstance(listing, dict) and "children" in listing:
                    children = listing.get("children", [])
                else:
                    children = listing if isinstance(listing, list) else []
            elif isinstance(data, list):
                children = data
            else:
                children = []

            for child in children:
                # Each child: {"kind": "t3", "data": {...}}
                post = child.get("data", child) if isinstance(child, dict) else {}
                if not isinstance(post, dict):
                    continue

                title = post.get("title", "")
                if not title:
                    continue

                permalink = post.get("permalink", "")
                url = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")

                items.append(SourceItem(
                    title=title,
                    url=url,
                    source_id=self.source_id,
                    source_name=self.source_name,
                    published_at=str(post.get("created_utc", "")),
                    author=post.get("author", ""),
                    summary=post.get("selftext", "")[:300] if post.get("selftext") else None,
                    metadata={
                        "tag": tag,
                        "subreddit": post.get("subreddit", ""),
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                    },
                ))
        except (json.JSONDecodeError, TypeError):
            pass

        return items
