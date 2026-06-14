"""
Data query tool

Implement P0 core data query tool.
"""

from typing import Dict, List, Optional, Union

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_date_range,
    validate_top_n,
    validate_mode,
    validate_date_query,
    normalize_date_range
)
from ..utils.errors import MCPError


class DataQueryTools:
    """Data query tool class"""

    def __init__(self, project_root: str = None):
        """
        Initialize data query tool

        Args:
            project_root: Project root directory
        """
        self.data_service = DataService(project_root)

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        Get the latest batch of crawled news data

        Args:
            platforms: List of platform IDs, e.g., ['zhihu', 'weibo']
            limit: Return count limit, default 20
            include_url: Whether to include URL links, default False (saves tokens)

        Returns:
            News list dictionary

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.get_latest_news(platforms=['zhihu'], limit=10)
            >>> print(result['total'])
            10
        """
        try:
            # Parameter validation
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Get data
            news_list = self.data_service.get_latest_news(
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "success": True,
                "summary": {
                    "description": "Latest batch of crawled news data",
                    "total": len(news_list),
                    "returned": len(news_list),
                    "platforms": platforms or "All platforms"
                },
                "data": news_list
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def search_news_by_keyword(
        self,
        keyword: str,
        date_range: Optional[Union[Dict, str]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Search historical news by keyword

        Args:
            keyword: Search keyword (required)
            date_range: Date range, format: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            platforms: Platform filter list
            limit: Return count limit (optional, default returns all)

        Returns:
            Search result dictionary

        Example (Assuming today is 2025-11-17):
            >>> tools = DataQueryTools()
            >>> result = tools.search_news_by_keyword(
            ...     keyword="Artificial Intelligence",
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"},
            ...     limit=50
            ... )
            >>> print(result['total'])
        """
        try:
            # Parameter validation
            keyword = validate_keyword(keyword)
            date_range_tuple = validate_date_range(date_range)
            platforms = validate_platforms(platforms)

            if limit is not None:
                limit = validate_limit(limit, default=100)

            # Search data
            search_result = self.data_service.search_news_by_keyword(
                keyword=keyword,
                date_range=date_range_tuple,
                platforms=platforms,
                limit=limit
            )

            return {
                **search_result,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_trending_topics(
        self,
        top_n: Optional[int] = None,
        mode: Optional[str] = None,
        extract_mode: Optional[str] = None
    ) -> Dict:
        """
        Get hot topic statistics

        Args:
            top_n: Return TOP N topics, default 10
            mode: Time mode
                - "daily": Daily cumulative data statistics
                - "current": Latest batch data statistics (default)
            extract_mode: Extraction mode
                - "keywords": Count preset focus words (based on config/frequency_words.txt, default)
                - "auto_extract": Automatically extract high-frequency words from news titles

        Returns:
            Topic frequency statistics dictionary

        Example:
            >>> tools = DataQueryTools()
            >>> # Use preset focus words
            >>> result = tools.get_trending_topics(top_n=5, mode="current")
            >>> # Automatically extract high-frequency words
            >>> result = tools.get_trending_topics(top_n=10, extract_mode="auto_extract")
        """
        try:
            # Parameter validation
            top_n = validate_top_n(top_n, default=10)
            valid_modes = ["daily", "current"]
            mode = validate_mode(mode, valid_modes, default="current")

            # Validate extract_mode
            if extract_mode is None:
                extract_mode = "keywords"
            elif extract_mode not in ["keywords", "auto_extract"]:
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": f"Unsupported extraction mode: {extract_mode}",
                        "suggestion": "Supported modes: keywords, auto_extract"
                    }
                }

            # Get trending topics
            trending_result = self.data_service.get_trending_topics(
                top_n=top_n,
                mode=mode,
                extract_mode=extract_mode
            )

            return {
                **trending_result,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_news_by_date(
        self,
        date_range: Optional[Union[Dict[str, str], str]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        Query news by date, supports natural language dates

        Args:
            date_range: Date range (optional, default "today"), supports:
                - Range object: {"start": "2025-01-01", "end": "2025-01-07"}
                - Relative dates: today, yesterday, the day before yesterday, 3 days ago
                - Single day string: 2025-10-10
            platforms: List of platform IDs, e.g., ['zhihu', 'weibo']
            limit: Return count limit, default 50
            include_url: Whether to include URL links, default False (saves tokens)

        Returns:
            News list dictionary

        Example:
            >>> tools = DataQueryTools()
            >>> # No date specified, defaults to querying today
            >>> result = tools.get_news_by_date(platforms=['zhihu'], limit=20)
            >>> # Specify date
            >>> result = tools.get_news_by_date(
            ...     date_range="yesterday",
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
            >>> print(result['total'])
            20
        """
        try:
            # Parameter validation - default today
            if date_range is None:
                date_range = "today"

            # Normalize date_range (handle JSON string serialization issues)
            date_range = normalize_date_range(date_range)

            # Process date_range: supports string or object
            if isinstance(date_range, dict):
                # Range object, get start date
                date_str = date_range.get('start', 'today')
            else:
                date_str = date_range
            target_date = validate_date_query(date_str)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Get data
            news_list = self.data_service.get_news_by_date(
                target_date=target_date,
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "success": True,
                "summary": {
                    "description": f"News queried by date ({target_date.strftime('%Y-%m-%d')})",
                    "total": len(news_list),
                    "returned": len(news_list),
                    "date": target_date.strftime("%Y-%m-%d"),
                    "date_range": date_range,
                    "platforms": platforms or "All platforms"
                },
                "data": news_list
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    # ========================================
    # RSS data query methods
    # ========================================

    def get_latest_rss(
        self,
        feeds: Optional[List[str]] = None,
        days: int = 1,
        limit: Optional[int] = None,
        include_summary: bool = False
    ) -> Dict:
        """
        Get the latest RSS data (supports multi-day queries)

        Args:
            feeds: List of RSS feed IDs, e.g., ['hacker-news', '36kr']
            days: Get data for the last N days, default 1 (today only), max 30 days
            limit: Return count limit, default 50
            include_summary: Whether to include summary, default False (saves tokens)

        Returns:
            RSS entry list dictionary
        """
        try:
            limit = validate_limit(limit, default=50)

            rss_list = self.data_service.get_latest_rss(
                feeds=feeds,
                days=days,
                limit=limit,
                include_summary=include_summary
            )

            return {
                "success": True,
                "summary": {
                    "description": f"RSS subscription data for the last {days} days" if days > 1 else "Latest RSS subscription data",
                    "total": len(rss_list),
                    "returned": len(rss_list),
                    "days": days,
                    "feeds": feeds or "All feeds"
                },
                "data": rss_list
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def search_rss(
        self,
        keyword: str,
        feeds: Optional[List[str]] = None,
        days: int = 7,
        limit: Optional[int] = None,
        include_summary: bool = False
    ) -> Dict:
        """
        Search RSS data

        Args:
            keyword: Search keyword
            feeds: List of RSS feed IDs
            days: Search data for the last N days, default 7 days
            limit: Return count limit, default 50
            include_summary: Whether to include summary

        Returns:
            List of matched RSS entries
        """
        try:
            keyword = validate_keyword(keyword)
            limit = validate_limit(limit, default=50)

            if days < 1 or days > 30:
                days = 7

            rss_list = self.data_service.search_rss(
                keyword=keyword,
                feeds=feeds,
                days=days,
                limit=limit,
                include_summary=include_summary
            )

            return {
                "success": True,
                "summary": {
                    "description": f"RSS search results (keyword: {keyword})",
                    "total": len(rss_list),
                    "returned": len(rss_list),
                    "keyword": keyword,
                    "feeds": feeds or "All feeds",
                    "days": days
                },
                "data": rss_list
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_rss_feeds_status(self) -> Dict:
        """
        Get RSS feed status

        Returns:
            RSS feed status information
        """
        try:
            status = self.data_service.get_rss_feeds_status()

            return {
                **status,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

