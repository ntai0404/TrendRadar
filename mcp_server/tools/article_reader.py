"""
Article content reading tool

Convert URLs to LLM-friendly Markdown format via the Jina AI Reader API.
Supports single and batch reading, with built-in rate limiting and concurrency control.

"""

import time
from typing import Dict, List

import requests

from ..utils.errors import MCPError, InvalidParameterError


# Jina Reader configuration
JINA_READER_BASE = "https://r.jina.ai"
DEFAULT_TIMEOUT = 30 # seconds
MAX_BATCH_SIZE = 5 # Maximum number of articles in a single batch
BATCH_INTERVAL = 5.0 # Batch request interval (seconds)


class ArticleReaderTools:
    """Article content reading tool class"""

    def __init__(self, project_root: str = None, jina_api_key: str = None):
        """
        Initialize article reading tool

        Args:
            project_root: project root directory
            jina_api_key: Jina API Key (optional, having Key can increase the rate limit)
        """
        self.project_root = project_root
        self.jina_api_key = jina_api_key
        self._last_request_time = 0.0

    def _build_headers(self) -> Dict[str, str]:
        """Build request header"""
        headers = {
            "Accept": "text/markdown",
            "X-Return-Format": "markdown",
            "X-No-Cache": "true",
        }
        if self.jina_api_key:
            headers["Authorization"] = f"Bearer {self.jina_api_key}"
        return headers

    def _throttle(self):
        """Rate control: ensure 5 seconds between requests"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < BATCH_INTERVAL:
            time.sleep(BATCH_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def read_article(
        self,
        url: str,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Dict:
        """
        Read the content of a single article (Markdown format)

        Args:
            url: article link
            timeout: request timeout (seconds), default 30

        Returns:
            Article content dictionary
        """
        try:
            if not url or not url.startswith(("http://", "https://")):
                raise InvalidParameterError(
                    f"Invalid URL: {url}",
                    suggestion="URL must start with http:// or https://"
                )

            self._throttle()

            response = requests.get(
                f"{JINA_READER_BASE}/{url}",
                headers=self._build_headers(),
                timeout=timeout
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "data": {
                        "url": url,
                        "content": response.text,
                        "format": "markdown",
                        "content_length": len(response.text)
                    }
                }
            elif response.status_code == 429:
                return {
                    "success": False,
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Jina Reader rate limit, please try again later",
                        "suggestion": "Free limit: 100 RPM / 2 concurrency, configurable API Key to increase the limit"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": {
                        "code": "FETCH_FAILED",
                        "message": f"HTTP {response.status_code}: {response.reason}",
                        "url": url
                    }
                }

        except requests.Timeout:
            return {
                "success": False,
                "error": {
                    "code": "TIMEOUT",
                    "message": f"Request timeout ({timeout} seconds)",
                    "url": url,
                    "suggestion": "You can try adding the timeout parameter"
                }
            }
        except MCPError as e:
            return {"success": False, "error": e.to_dict()}
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "REQUEST_ERROR",
                    "message": str(e),
                    "url": url
                }
            }

    def read_articles_batch(
        self,
        urls: List[str],
        timeout: int = DEFAULT_TIMEOUT
    ) -> Dict:
        """
        Read the content of multiple articles in batches (up to 5 articles, interval of 5 seconds)

        Args:
            urls: list of article links
            timeout: request timeout for each article (seconds)

        Returns:
            Read results in batches
        """
        try:
            if not urls:
                raise InvalidParameterError(
                    "URL list cannot be empty",
                    suggestion="Please provide at least one URL"
                )

            # Limit to 5 articles at most
            actual_urls = urls[:MAX_BATCH_SIZE]
            skipped = len(urls) - len(actual_urls)

            results = []
            succeeded = 0
            failed = 0

            for i, url in enumerate(actual_urls):
                result = self.read_article(url=url, timeout=timeout)

                results.append({
                    "index": i + 1,
                    "url": url,
                    "success": result["success"],
                    "data": result.get("data"),
                    "error": result.get("error")
                })

                if result["success"]:
                    succeeded += 1
                else:
                    failed += 1

            return {
                "success": True,
                "summary": {
                    "description": "Batch article reading results",
                    "requested": len(urls),
                    "processed": len(actual_urls),
                    "succeeded": succeeded,
                    "failed": failed,
                    "skipped": skipped,
                    "interval_seconds": BATCH_INTERVAL,
                },
                "articles": results,
                "note": f"{skipped} articles have been skipped (single limit {MAX_BATCH_SIZE} articles)" if skipped > 0 else None
            }

        except MCPError as e:
            return {"success": False, "error": e.to_dict()}
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "BATCH_ERROR",
                    "message": str(e)
                }
            }
