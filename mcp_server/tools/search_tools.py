"""
Intelligent news retrieval tool

Provides advanced search functions such as fuzzy search, link query, and historical related news retrieval.
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple, Union

from ..services.data_service import DataService
from ..utils.validators import validate_keyword, validate_limit, validate_threshold, normalize_date_range
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


class SearchTools:
    """Intelligent news retrieval tool class"""

    def __init__(self, project_root: str = None):
        """
        Initialize intelligent retrieval tool

        Args:
            project_root: Project root directory
        """
        self.data_service = DataService(project_root)

    def search_news_unified(
        self,
        query: str,
        search_mode: str = "keyword",
        date_range: Optional[Union[Dict[str, str], str]] = None,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        sort_by: str = "relevance",
        threshold: float = 0.6,
        include_url: bool = False,
        include_rss: bool = False,
        rss_limit: int = 20
    ) -> Dict:
        """
        Unified news search tool - Integrates multiple search modes, supports simultaneous search of hotlists and RSS

        Args:
            query: Query content (required) - Keyword, content snippet, or entity name
            search_mode: Search mode, optional values:
                - "keyword": Exact keyword match (default)
                - "fuzzy": Fuzzy content match (using similarity algorithm)
                - "entity": Entity name search (automatically sorted by weight)
            date_range: Date range (optional)
                       - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **Example**: {"start": "2025-01-01", "end": "2025-01-07"}
                       - **Default**: Defaults to querying today when not specified
                       - **Note**: start and end can be the same (indicating a single-day query)
            platforms: Platform filter list, e.g., ['zhihu', 'weibo']
            limit: Hotlist return count limit, default 50
            sort_by: Sort method, optional values:
                - "relevance": Sort by relevance (default)
                - "weight": Sort by news weight
                - "date": Sort by date
            threshold: Similarity threshold (only valid for fuzzy mode), between 0-1, default 0.6
            include_url: Whether to include URL links, default False (saves tokens)
            include_rss: Whether to search RSS data simultaneously, default False
            rss_limit: RSS return count limit, default 20

        Returns:
            Search result dictionary, containing matched news lists (hotlists and RSS displayed separately)

        Examples:
            - search_news_unified(query="Artificial Intelligence", search_mode="keyword")
            - search_news_unified(query="Tesla price cut", search_mode="fuzzy", threshold=0.4)
            - search_news_unified(query="Musk", search_mode="entity", limit=20)
            - search_news_unified(query="AI", include_rss=True)  # Search hotlists and RSS simultaneously
            - search_news_unified(query="iPhone 16", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        """
        try:
            # Parameter validation
            query = validate_keyword(query)

            if search_mode not in ["keyword", "fuzzy", "entity"]:
                raise InvalidParameterError(
                    f"Invalid search mode: {search_mode}",
                    suggestion="Supported modes: keyword, fuzzy, entity"
                )

            if sort_by not in ["relevance", "weight", "date"]:
                raise InvalidParameterError(
                    f"Invalid sort method: {sort_by}",
                    suggestion="Supported sorting: relevance, weight, date"
                )

            limit = validate_limit(limit, default=50)
            threshold = validate_threshold(threshold, default=0.6, min_value=0.0, max_value=1.0)

            # Process date range
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # When no date is specified, use the latest available data date (instead of datetime.now())
                earliest, latest = self.data_service.get_available_date_range()

                if latest is None:
                    # No available data
                    return {
                        "success": False,
                        "error": {
                            "code": "NO_DATA_AVAILABLE",
                            "message": "No available news data in the output directory",
                            "suggestion": "Please run the crawler first to generate data, or check the output directory"
                        }
                    }

                # Use the latest available date
                start_date = end_date = latest

            # Collect all matching news
            all_matches = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # Execute different search logic based on search mode
                    if search_mode == "keyword":
                        matches = self._search_by_keyword_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )
                    elif search_mode == "fuzzy":
                        matches = self._search_by_fuzzy_mode(
                            query, all_titles, id_to_name, current_date, threshold, include_url
                        )
                    else:  # entity
                        matches = self._search_by_entity_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )

                    all_matches.extend(matches)

                except DataNotFoundError:
                    # No data for this date, continue to the next day
                    pass

                current_date += timedelta(days=1)

            if not all_matches:
                # Get available date range for error prompt
                earliest, latest = self.data_service.get_available_date_range()

                # Determine time range description
                if start_date.date() == datetime.now().date() and start_date == end_date:
                    time_desc = "Today"
                elif start_date == end_date:
                    time_desc = start_date.strftime("%Y-%m-%d")
                else:
                    time_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

                # Build error message
                if earliest and latest:
                    available_desc = f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"
                    message = f"No matching news found (Query range: {time_desc}, Available data: {available_desc})"
                else:
                    message = f"No matching news found ({time_desc})"

                result = {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": query,
                    "search_mode": search_mode,
                    "time_range": time_desc,
                    "message": message
                }
                return result

            # Unified sorting logic
            if sort_by == "relevance":
                all_matches.sort(key=lambda x: x.get("similarity_score", 1.0), reverse=True)
            elif sort_by == "weight":
                from .analytics import calculate_news_weight
                all_matches.sort(key=lambda x: calculate_news_weight(x), reverse=True)
            elif sort_by == "date":
                all_matches.sort(key=lambda x: x.get("date", ""), reverse=True)

            # Limit the number of returns
            results = all_matches[:limit]

            # Build time range description (correctly determine if it is today)
            if start_date.date() == datetime.now().date() and start_date == end_date:
                time_range_desc = "Today"
            elif start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "summary": {
                    "description": f"News search results ({search_mode} mode)",
                    "total_found": len(all_matches),
                    "returned": len(results),
                    "requested_limit": limit,
                    "search_mode": search_mode,
                    "query": query,
                    "platforms": platforms or "All platforms",
                    "time_range": time_range_desc,
                    "sort_by": sort_by
                },
                "data": results
            }

            if search_mode == "fuzzy":
                result["summary"]["threshold"] = threshold
                if len(all_matches) < limit:
                    result["note"] = f"In fuzzy search mode, similarity threshold {threshold} only matched {len(all_matches)} results"

            # If RSS search is enabled, search RSS data at the same time
            if include_rss:
                rss_results = self._search_rss_by_keyword(
                    query=query,
                    start_date=start_date,
                    end_date=end_date,
                    limit=rss_limit,
                    include_url=include_url
                )
                result["rss"] = rss_results["items"]
                result["rss_total"] = rss_results["total"]
                result["summary"]["include_rss"] = True
                result["summary"]["rss_found"] = rss_results["total"]
                result["summary"]["rss_returned"] = len(rss_results["items"])

            return result

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

    def _search_titles(
        self,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        include_url: bool,
        match_func,
    ) -> List[Dict]:
        """
        General title search method

        Args:
            all_titles: All titles dictionary
            id_to_name: Platform ID to name mapping
            current_date: Current date
            include_url: Whether to include URL
            match_func: Match function, receives (title, info), returns (is_match, similarity_score) or None

        Returns:
            List of matching news
        """
        matches = []

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                result = match_func(title, info)
                if result is None:
                    continue

                is_match, similarity = result
                if not is_match:
                    continue

                news_item = {
                    "title": title,
                    "platform": platform_id,
                    "platform_name": platform_name,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "similarity_score": round(similarity, 4),
                    "ranks": info.get("ranks", []),
                    "count": len(info.get("ranks", [])),
                    "rank": info["ranks"][0] if info["ranks"] else 999
                }

                if include_url:
                    news_item["url"] = info.get("url", "")
                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                matches.append(news_item)

        return matches

    def _search_by_keyword_mode(
        self, query: str, all_titles: Dict, id_to_name: Dict,
        current_date: datetime, include_url: bool
    ) -> List[Dict]:
        """Keyword search mode (exact match)"""
        query_lower = query.lower()
        return self._search_titles(
            all_titles, id_to_name, current_date, include_url,
            match_func=lambda title, info: (True, 1.0) if query_lower in title.lower() else (False, 0),
        )

    def _search_by_fuzzy_mode(
        self, query: str, all_titles: Dict, id_to_name: Dict,
        current_date: datetime, threshold: float, include_url: bool
    ) -> List[Dict]:
        """Fuzzy search mode (using similarity algorithm)"""
        return self._search_titles(
            all_titles, id_to_name, current_date, include_url,
            match_func=lambda title, info: self._fuzzy_match(query, title, threshold),
        )

    def _search_by_entity_mode(
        self, query: str, all_titles: Dict, id_to_name: Dict,
        current_date: datetime, include_url: bool
    ) -> List[Dict]:
        """Entity search mode (exactly contains entity name)"""
        return self._search_titles(
            all_titles, id_to_name, current_date, include_url,
            match_func=lambda title, info: (True, 1.0) if query in title else (False, 0),
        )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate the similarity of two texts

        Args:
            text1: Text 1
            text2: Text 2

        Returns:
            Similarity score (between 0-1)
        """
        # Use difflib.SequenceMatcher to calculate sequence similarity
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _fuzzy_match(self, query: str, text: str, threshold: float = 0.3) -> Tuple[bool, float]:
        """
        Fuzzy match function

        Args:
            query: Query text
            text: Text to be matched
            threshold: Match threshold

        Returns:
            (Is match, Similarity score)
        """
        # Direct inclusion check
        if query.lower() in text.lower():
            return True, 1.0

        # Calculate overall similarity
        similarity = self._calculate_similarity(query, text)
        if similarity >= threshold:
            return True, similarity

        # Partial match after tokenization
        query_words = set(self._extract_keywords(query))
        text_words = set(self._extract_keywords(text))

        if not query_words or not text_words:
            return False, 0.0

        # Calculate keyword overlap
        common_words = query_words & text_words
        keyword_overlap = len(common_words) / len(query_words)

        if keyword_overlap >= 0.5:  # 50% keyword overlap
            return True, keyword_overlap

        return False, similarity

    def _extract_keywords(self, text: str, min_length: int = 2) -> List[str]:
        """
        Extract keywords from text

        Args:
            text: Input text
            min_length: Minimum word length

        Returns:
            Keyword list
        """
        # Remove URLs and special characters
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'\[.*?\]', '', text)  # Remove bracket contents

        # Use regular expressions for tokenization (Chinese and English)
        words = re.findall(r'[\w]+', text)

        # Filter short words
        keywords = [word for word in words if word and len(word) >= min_length]

        return keywords

    def _calculate_keyword_overlap(self, keywords1: List[str], keywords2: List[str]) -> float:
        """
        Calculate the overlap between two keyword lists

        Args:
            keywords1: Keyword list 1
            keywords2: Keyword list 2

        Returns:
            Overlap score (between 0-1)
        """
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        # Jaccard similarity
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def _jaccard_similarity(self, list1: List[str], list2: List[str]) -> float:
        """
        Calculate the Jaccard similarity of two lists

        Args:
            list1: List 1
            list2: List 2

        Returns:
            Jaccard similarity (between 0-1)
        """
        if not list1 or not list2:
            return 0.0

        set1 = set(list1)
        set2 = set(list2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def search_related_news_history(
        self,
        reference_title: str,
        time_preset: str = "yesterday",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        threshold: float = 0.4,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        Search for news related to the given news in historical data

        Args:
            reference_title: Reference news title or content
            time_preset: Time range preset value, optional:
                - "yesterday": Yesterday
                - "last_week": Last week (7 days)
                - "last_month": Last month (30 days)
                - "custom": Custom date range (requires start_date and end_date)
            start_date: Custom start date (only valid when time_preset="custom")
            end_date: Custom end date (only valid when time_preset="custom")
            threshold: Similarity threshold (between 0-1), default 0.4
            limit: Return count limit, default 50
            include_url: Whether to include URL links, default False (saves tokens)

        Returns:
            Search result dictionary, containing a list of related news

        Example:
            >>> tools = SearchTools()
            >>> result = tools.search_related_news_history(
            ...     reference_title="Artificial intelligence technology breakthrough",
            ...     time_preset="last_week",
            ...     threshold=0.4,
            ...     limit=50
            ... )
            >>> for news in result['results']:
            ...     print(f"{news['date']}: {news['title']} (Similarity: {news['similarity_score']})")
        """
        try:
            # Parameter validation
            reference_title = validate_keyword(reference_title)
            threshold = validate_threshold(threshold, default=0.4, min_value=0.0, max_value=1.0)
            limit = validate_limit(limit, default=50)

            # Determine query date range
            today = datetime.now()

            if time_preset == "yesterday":
                search_start = today - timedelta(days=1)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_week":
                search_start = today - timedelta(days=7)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_month":
                search_start = today - timedelta(days=30)
                search_end = today - timedelta(days=1)
            elif time_preset == "custom":
                if not start_date or not end_date:
                    raise InvalidParameterError(
                        "Custom time range requires providing start_date and end_date",
                        suggestion="Please provide start_date and end_date parameters"
                    )
                search_start = start_date
                search_end = end_date
            else:
                raise InvalidParameterError(
                    f"Unsupported time range: {time_preset}",
                    suggestion="Please use 'yesterday', 'last_week', 'last_month' or 'custom'"
                )

            # Extract keywords from reference text
            reference_keywords = self._extract_keywords(reference_title)

            if not reference_keywords:
                raise InvalidParameterError(
                    "Unable to extract keywords from reference text",
                    suggestion="Please provide more detailed text content"
                )

            # Collect all related news
            all_related_news = []
            current_date = search_start

            while current_date <= search_end:
                try:
                    # Read data for this date
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(current_date)

                    # Search for related news
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title, info in titles.items():
                            # Calculate title similarity
                            title_similarity = self._calculate_similarity(reference_title, title)

                            # Extract title keywords
                            title_keywords = self._extract_keywords(title)

                            # Calculate keyword overlap
                            keyword_overlap = self._calculate_keyword_overlap(
                                reference_keywords,
                                title_keywords
                            )

                            # Comprehensive similarity (70% keyword overlap + 30% text similarity)
                            combined_score = keyword_overlap * 0.7 + title_similarity * 0.3

                            if combined_score >= threshold:
                                news_item = {
                                    "title": title,
                                    "platform": platform_id,
                                    "platform_name": platform_name,
                                    "date": current_date.strftime("%Y-%m-%d"),
                                    "similarity_score": round(combined_score, 4),
                                    "keyword_overlap": round(keyword_overlap, 4),
                                    "text_similarity": round(title_similarity, 4),
                                    "common_keywords": list(set(reference_keywords) & set(title_keywords)),
                                    "rank": info["ranks"][0] if info["ranks"] else 0
                                }

                                # Conditionally add URL field
                                if include_url:
                                    news_item["url"] = info.get("url", "")
                                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                                all_related_news.append(news_item)

                except DataNotFoundError:
                    # No data for this date, continue to next day
                    pass
                except Exception as e:
                    # Log error but continue processing other dates
                    print(f"Warning: Error processing date {current_date.strftime('%Y-%m-%d')}: {e}")

                # Move to next day
                current_date += timedelta(days=1)

            if not all_related_news:
                return {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": reference_title,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    },
                    "message": "No related news found"
                }

            # Sort by similarity
            all_related_news.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Limit returned results
            results = all_related_news[:limit]

            # Statistics
            platform_distribution = Counter([news["platform"] for news in all_related_news])
            date_distribution = Counter([news["date"] for news in all_related_news])

            result = {
                "success": True,
                "summary": {
                    "description": "Historical related news search results",
                    "total_found": len(all_related_news),
                    "returned": len(results),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_title": reference_title,
                    "reference_keywords": reference_keywords,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    }
                },
                "data": results,
                "statistics": {
                    "platform_distribution": dict(platform_distribution),
                    "date_distribution": dict(date_distribution),
                    "avg_similarity": round(
                        sum([news["similarity_score"] for news in all_related_news]) / len(all_related_news),
                        4
                    ) if all_related_news else 0.0
                }
            }

            if len(all_related_news) < limit:
                result["note"] = f"Only {len(all_related_news)} related news found under relevance threshold {threshold}"

            return result

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

    def find_related_news_unified(
        self,
        reference_title: str,
        date_range: Optional[Union[Dict[str, str], str]] = None,
        threshold: float = 0.5,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        Unified related news search tool - integrates similar news and historical related searches

        Args:
            reference_title: Reference news title
            date_range: Date range (optional)
                - Not specified: Only query today's data
                - {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}: Query specified date range
                - "today": Today
                - "yesterday": Yesterday
                - "last_week": Last 7 days
                - "last_month": Last 30 days
            threshold: Similarity threshold, between 0-1, default 0.5
            limit: Return limit, default 50
            include_url: Whether to include URL links, default False

        Returns:
            List of related news, sorted by similarity
        """
        try:
            # Parameter validation
            reference_title = validate_keyword(reference_title)
            threshold = validate_threshold(threshold, default=0.5, min_value=0.0, max_value=1.0)
            limit = validate_limit(limit, default=50)

            # Determine date range
            today = datetime.now()

            # Normalize date_range (handle JSON string serialization issues)
            date_range = normalize_date_range(date_range)

            if date_range is None or date_range == "today":
                # Only query today
                search_dates = [today]
            elif isinstance(date_range, str):
                # Preset time range
                if date_range == "yesterday":
                    search_dates = [today - timedelta(days=1)]
                elif date_range == "last_week":
                    search_dates = [today - timedelta(days=i) for i in range(7)]
                elif date_range == "last_month":
                    search_dates = [today - timedelta(days=i) for i in range(30)]
                else:
                    # Single day string format
                    try:
                        single_date = datetime.strptime(date_range, "%Y-%m-%d")
                        search_dates = [single_date]
                    except ValueError:
                        search_dates = [today]
            elif isinstance(date_range, dict):
                # Date range object
                start_str = date_range.get("start")
                end_str = date_range.get("end")
                if start_str and end_str:
                    start_date = datetime.strptime(start_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_str, "%Y-%m-%d")
                    search_dates = []
                    current = start_date
                    while current <= end_date:
                        search_dates.append(current)
                        current += timedelta(days=1)
                else:
                    search_dates = [today]
            else:
                search_dates = [today]

            # Extract keywords from reference title
            reference_keywords = self._extract_keywords(reference_title)

            # Collect all related news
            all_related_news = []
            
            for search_date in search_dates:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(search_date)
                    
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        
                        for title, info in titles.items():
                            if title == reference_title:
                                continue
                            
                            # Calculate similarity (using hybrid algorithm)
                            text_similarity = self._calculate_similarity(reference_title, title)
                            
                            # If there are keywords, also calculate keyword overlap
                            if reference_keywords:
                                title_keywords = self._extract_keywords(title)
                                keyword_similarity = self._jaccard_similarity(reference_keywords, title_keywords)
                                # Hybrid similarity: 70% text + 30% keywords
                                similarity = 0.7 * text_similarity + 0.3 * keyword_similarity
                            else:
                                similarity = text_similarity
                            
                            if similarity >= threshold:
                                news_item = {
                                    "title": title,
                                    "platform": platform_id,
                                    "platform_name": platform_name,
                                    "date": search_date.strftime("%Y-%m-%d"),
                                    "similarity": round(similarity, 3),
                                    "rank": info["ranks"][0] if info["ranks"] else 0
                                }
                                
                                if include_url:
                                    news_item["url"] = info.get("url", "")
                                
                                all_related_news.append(news_item)
                                
                except (OSError, KeyError, TypeError, ValueError):
                    # Failed to read data for a certain day, skip
                    continue

            # Sort by similarity
            all_related_news.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Limit quantity
            results = all_related_news[:limit]

            # Statistics
            from collections import Counter
            platform_dist = Counter([n["platform_name"] for n in all_related_news])
            date_dist = Counter([n["date"] for n in all_related_news])

            return {
                "success": True,
                "summary": {
                    "description": "Related news search results",
                    "total_found": len(all_related_news),
                    "returned": len(results),
                    "reference_title": reference_title,
                    "threshold": threshold,
                    "date_range": {
                        "start": min(search_dates).strftime("%Y-%m-%d"),
                        "end": max(search_dates).strftime("%Y-%m-%d")
                    } if search_dates else None
                },
                "data": results,
                "statistics": {
                    "platform_distribution": dict(platform_dist),
                    "date_distribution": dict(date_dist)
                }
            }

        except MCPError as e:
            return {"success": False, "error": e.to_dict()}
        except Exception as e:
            return {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}

    def _search_rss_by_keyword(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 20,
        include_url: bool = False
    ) -> Dict:
        """
        Search keywords in RSS data

        Args:
            query: Search keywords
            start_date: Start date
            end_date: End date
            limit: Return count limit
            include_url: Whether to include URL

        Returns:
            RSS search results dictionary
        """
        all_rss_matches = []
        query_lower = query.lower()
        current_date = start_date

        while current_date <= end_date:
            try:
                # Read RSS data for this date
                all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                    date=current_date,
                    platform_ids=None,
                    db_type="rss"
                )

                for feed_id, items in all_titles.items():
                    feed_name = id_to_name.get(feed_id, feed_id)

                    for title, info in items.items():
                        # Keyword matching (title or summary)
                        title_match = query_lower in title.lower()
                        summary = info.get("summary", "")
                        summary_match = query_lower in summary.lower() if summary else False

                        if title_match or summary_match:
                            rss_item = {
                                "title": title,
                                "feed_id": feed_id,
                                "feed_name": feed_name,
                                "date": current_date.strftime("%Y-%m-%d"),
                                "published_at": info.get("published_at", ""),
                                "author": info.get("author", ""),
                                "match_in": "title" if title_match else "summary"
                            }

                            if include_url:
                                rss_item["url"] = info.get("url", "")

                            all_rss_matches.append(rss_item)

            except DataNotFoundError:
                # No RSS data for this date, continue to next day
                pass
            except (OSError, KeyError, TypeError, ValueError):
                # Other errors, skip
                pass

            current_date += timedelta(days=1)

        # Sort by publish time (newest first)
        all_rss_matches.sort(key=lambda x: x.get("published_at", ""), reverse=True)

        return {
            "items": all_rss_matches[:limit],
            "total": len(all_rss_matches)
        }
