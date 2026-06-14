"""
Advanced data analysis tools

Provides advanced analysis functions such as popularity trend analysis, platform comparison, keyword co-occurrence, and sentiment analysis.
"""

import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from difflib import SequenceMatcher

import yaml

from trendradar.core.analyzer import calculate_news_weight as _calculate_news_weight

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_top_n,
    validate_date_range,
    validate_threshold
)
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


# Weight configuration mtime cache (avoid reading the same configuration file repeatedly)
_weight_config_cache: Optional[Dict] = None
_weight_config_mtime: float = 0.0
_weight_config_path: Optional[str] = None

_WEIGHT_DEFAULT_CONFIG = {
    "RANK_WEIGHT": 0.6,
    "FREQUENCY_WEIGHT": 0.3,
    "HOTNESS_WEIGHT": 0.1,
}


def _get_weight_config() -> Dict:
    """
    Read weight configuration from config.yaml (with mtime cache)

    Only re-read when the configuration file is modified to avoid repeated IO in the loop.

    Returns:
        Weight configuration dictionary, including RANK_WEIGHT, FREQUENCY_WEIGHT, HOTNESS_WEIGHT
    """
    global _weight_config_cache, _weight_config_mtime, _weight_config_path

    try:
        # Calculate path on first call (reuse later)
        if _weight_config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            _weight_config_path = os.path.normpath(
                os.path.join(current_dir, "..", "..", "config", "config.yaml")
            )

        current_mtime = os.path.getmtime(_weight_config_path)

        # File unmodified and cache valid, return directly
        if _weight_config_cache is not None and current_mtime == _weight_config_mtime:
            return _weight_config_cache

        # File modified or read for the first time, re-parse
        with open(_weight_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            weight = config.get('advanced', {}).get('weight', {})
            _weight_config_cache = {
                "RANK_WEIGHT": weight.get('rank', 0.6),
                "FREQUENCY_WEIGHT": weight.get('frequency', 0.3),
                "HOTNESS_WEIGHT": weight.get('hotness', 0.1),
            }
            _weight_config_mtime = current_mtime
            return _weight_config_cache
    except (OSError, yaml.YAMLError, KeyError, TypeError):
        return _WEIGHT_DEFAULT_CONFIG


def calculate_news_weight(news_data: Dict, rank_threshold: int = 5) -> float:
    """
    Calculate news weight (used for sorting)

    Reuse trendradar.core.analyzer.calculate_news_weight implementation,
    Weight configuration is read from advanced.weight in config.yaml.

    Args:
        news_data: News data dictionary, containing ranks and count fields
        rank_threshold: High ranking threshold, default 5

    Returns:
        Weight score (float between 0-100)
    """
    return _calculate_news_weight(news_data, rank_threshold, _get_weight_config())


class AnalyticsTools:
    """Advanced data analysis tool class"""

    def __init__(self, project_root: str = None):
        """
        Initialize analysis tool

        Args:
            project_root: Project root directory
        """
        self.data_service = DataService(project_root)

    def analyze_data_insights_unified(
        self,
        insight_type: str = "platform_compare",
        topic: Optional[str] = None,
        date_range: Optional[Union[Dict[str, str], str]] = None,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        Unified data insight analysis tool - integrates multiple data analysis modes

        Args:
            insight_type: Insight type, optional values:
                - "platform_compare": Platform comparison analysis (compare attention to topics across different platforms)
                - "platform_activity": Platform activity statistics (count publishing frequency and active times of each platform)
                - "keyword_cooccur": Keyword co-occurrence analysis (analyze patterns of keywords appearing simultaneously)
            topic: Topic keyword (optional, applicable to platform_compare mode)
            date_range: Date range, format: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            min_frequency: Minimum co-occurrence frequency (keyword_cooccur mode), default 3
            top_n: Return TOP N results (keyword_cooccur mode), default 20

        Returns:
            Data insight analysis result dictionary

        Examples:
            - analyze_data_insights_unified(insight_type="platform_compare", topic="Artificial Intelligence")
            - analyze_data_insights_unified(insight_type="platform_activity", date_range={...})
            - analyze_data_insights_unified(insight_type="keyword_cooccur", min_frequency=5)
        """
        try:
            # Parameter validation
            if insight_type not in ["platform_compare", "platform_activity", "keyword_cooccur"]:
                raise InvalidParameterError(
                    f"Invalid insight type: {insight_type}",
                    suggestion="Supported types: platform_compare, platform_activity, keyword_cooccur"
                )

            # Call the corresponding method according to the insight type
            if insight_type == "platform_compare":
                return self.compare_platforms(
                    topic=topic,
                    date_range=date_range
                )
            elif insight_type == "platform_activity":
                return self.get_platform_activity_stats(
                    date_range=date_range
                )
            else:  # keyword_cooccur
                return self.analyze_keyword_cooccurrence(
                    min_frequency=min_frequency,
                    top_n=top_n
                )

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

    def analyze_topic_trend_unified(
        self,
        topic: str,
        analysis_type: str = "trend",
        date_range: Optional[Union[Dict[str, str], str]] = None,
        granularity: str = "day",
        threshold: float = 3.0,
        time_window: int = 24,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        Unified topic trend analysis tool - integrates multiple trend analysis modes

        Args:
            topic: Topic keyword (required)
            analysis_type: Analysis type, optional values:
                - "trend": Popularity trend analysis (track popularity changes of the topic)
                - "lifecycle": Lifecycle analysis (complete cycle from appearance to disappearance)
                - "viral": Abnormal popularity detection (identify suddenly viral topics)
                - "predict": Topic prediction (predict potential future hot spots)
            date_range: Date range (trend and lifecycle modes), optional
                       - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **Default**: If not specified, defaults to analyzing the last 7 days
            granularity: Time granularity (trend mode), default "day" (hour/day)
            threshold: Popularity surge multiplier threshold (viral mode), default 3.0
            time_window: Detection time window in hours (viral mode), default 24
            lookahead_hours: Predict future hours (predict mode), default 6
            confidence_threshold: Confidence threshold (predict mode), default 0.7

        Returns:
            Trend analysis result dictionary

        Examples (Assuming today is 2025-11-17):
            - User: "Analyze the trend of AI in the last 7 days" → analyze_topic_trend_unified(topic="Artificial Intelligence", analysis_type="trend", date_range={"start": "2025-11-11", "end": "2025-11-17"})
            - User: "Look at Tesla's popularity this month" → analyze_topic_trend_unified(topic="Tesla", analysis_type="lifecycle", date_range={"start": "2025-11-01", "end": "2025-11-17"})
            - analyze_topic_trend_unified(topic="Bitcoin", analysis_type="viral", threshold=3.0)
            - analyze_topic_trend_unified(topic="ChatGPT", analysis_type="predict", lookahead_hours=6)
        """
        try:
            # Parameter validation
            topic = validate_keyword(topic)

            if analysis_type not in ["trend", "lifecycle", "viral", "predict"]:
                raise InvalidParameterError(
                    f"Invalid analysis type: {analysis_type}",
                    suggestion="Supported types: trend, lifecycle, viral, predict"
                )

            # Call the corresponding method based on the analysis type
            if analysis_type == "trend":
                return self.get_topic_trend_analysis(
                    topic=topic,
                    date_range=date_range,
                    granularity=granularity
                )
            elif analysis_type == "lifecycle":
                return self.analyze_topic_lifecycle(
                    topic=topic,
                    date_range=date_range
                )
            elif analysis_type == "viral":
                # viral mode does not require the topic parameter, uses general detection
                return self.detect_viral_topics(
                    threshold=threshold,
                    time_window=time_window
                )
            else:  # predict
                # predict mode does not require the topic parameter, uses general prediction
                return self.predict_trending_topics(
                    lookahead_hours=lookahead_hours,
                    confidence_threshold=confidence_threshold
                )

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

    def get_topic_trend_analysis(
        self,
        topic: str,
        date_range: Optional[Union[Dict[str, str], str]] = None,
        granularity: str = "day"
    ) -> Dict:
        """
        Popularity trend analysis - Track the popularity change trend of a specific topic

        Args:
            topic: Topic keyword
            date_range: Date range (optional)
                       - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **Default**: If not specified, defaults to analyzing the last 7 days
            granularity: Time granularity, only supports day

        Returns:
            Trend analysis result dictionary

        Examples:
            User query examples:
            - "Help me analyze the popularity trend of the topic 'Artificial Intelligence' over the last week"
            - "Check the popularity change of 'Bitcoin' over the past week"
            - "See how the trend of 'iPhone' is in the last 7 days"
            - "Analyze the popularity trend of 'Tesla' over the last month"
            - "Check the trend change of 'ChatGPT' in December 2024"

            Code call examples:
            >>> tools = AnalyticsTools()
            >>> # Analyze 7-day trend (Assuming today is 2025-11-17)
            >>> result = tools.get_topic_trend_analysis(
            ...     topic="Artificial Intelligence",
            ...     date_range={"start": "2025-11-11", "end": "2025-11-17"},
            ...     granularity="day"
            ... )
            >>> # Analyze historical month trend
            >>> result = tools.get_topic_trend_analysis(
            ...     topic="Tesla",
            ...     date_range={"start": "2024-12-01", "end": "2024-12-31"},
            ...     granularity="day"
            ... )
            >>> print(result['trend_data'])
        """
        try:
            # Validate parameters
            topic = validate_keyword(topic)

            # Validate granularity parameter (only supports day)
            if granularity != "day":
                from ..utils.errors import InvalidParameterError
                raise InvalidParameterError(
                    f"Unsupported granularity parameter: {granularity}",
                    suggestion="Currently only supports 'day' granularity, because the underlying data is aggregated by day"
                )

            # Process date range (defaults to the last 7 days if not specified)
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # Default to the last 7 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            # Collect trend data
            trend_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    # Count the number of topic occurrences at this time point
                    count = 0
                    matched_titles = []

                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1
                                matched_titles.append(title)

                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count,
                        "sample_titles": matched_titles[:3]  # Only keep the first 3 samples
                    })

                except DataNotFoundError:
                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0,
                        "sample_titles": []
                    })

                # Increment time by day
                current_date += timedelta(days=1)

            # Calculate trend indicators
            counts = [item["count"] for item in trend_data]
            total_days = (end_date - start_date).days + 1

            if len(counts) >= 2:
                # Calculate the rate of change
                first_non_zero = next((c for c in counts if c > 0), 0)
                last_count = counts[-1]

                if first_non_zero > 0:
                    change_rate = ((last_count - first_non_zero) / first_non_zero) * 100
                else:
                    change_rate = 0

                # Find the peak time
                max_count = max(counts)
                peak_index = counts.index(max_count)
                peak_time = trend_data[peak_index]["date"]
            else:
                change_rate = 0
                peak_time = None
                max_count = 0

            return {
                "success": True,
                "summary": {
                    "description": f"Popularity trend analysis of the topic '{topic}'",
                    "topic": topic,
                    "date_range": {
                        "start": start_date.strftime("%Y-%m-%d"),
                        "end": end_date.strftime("%Y-%m-%d"),
                        "total_days": total_days
                    },
                    "granularity": granularity,
                    "total_mentions": sum(counts),
                    "average_mentions": round(sum(counts) / len(counts), 2) if counts else 0,
                    "peak_count": max_count,
                    "peak_time": peak_time,
                    "change_rate": round(change_rate, 2),
                    "trend_direction": "Rising" if change_rate > 10 else "Falling" if change_rate < -10 else "Stable"
                },
                "data": trend_data
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

    def compare_platforms(
        self,
        topic: Optional[str] = None,
        date_range: Optional[Union[Dict[str, str], str]] = None
    ) -> Dict:
        """
        Platform comparison analysis - Compare the attention of different platforms to the same topic

        Args:
            topic: Topic keywords (optional, if not specified, compare overall activity)
            date_range: Date range, format: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

        Returns:
            Platform comparison analysis results

        Examples:
            User query examples:
            - "Compare the attention of various platforms to the 'artificial intelligence' topic"
            - "See which platform, Zhihu or Weibo, pays more attention to tech news"
            - "Analyze the hot spot distribution of each platform today"

            Code call example:
            >>> # Compare platforms (assuming today is 2025-11-17)
            >>> result = tools.compare_platforms(
            ...     topic="artificial intelligence",
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"}
            ... )
            >>> print(result['platform_stats'])
        """
        try:
            # Parameter validation
            if topic:
                topic = validate_keyword(topic)
            date_range_tuple = validate_date_range(date_range)

            # Determine date range
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # Collect data from each platform
            platform_stats = defaultdict(lambda: {
                "total_news": 0,
                "topic_mentions": 0,
                "unique_titles": set(),
                "top_keywords": Counter()
            })

            # Iterate through the date range
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title in titles.keys():
                            platform_stats[platform_name]["total_news"] += 1
                            platform_stats[platform_name]["unique_titles"].add(title)

                            # If a topic is specified, count the news containing the topic
                            if topic and topic.lower() in title.lower():
                                platform_stats[platform_name]["topic_mentions"] += 1

                            # Extract keywords (simple tokenization)
                            keywords = self._extract_keywords(title)
                            platform_stats[platform_name]["top_keywords"].update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # Convert to a serializable format
            result_stats = {}
            for platform, stats in platform_stats.items():
                coverage_rate = 0
                if stats["total_news"] > 0:
                    coverage_rate = (stats["topic_mentions"] / stats["total_news"]) * 100

                result_stats[platform] = {
                    "total_news": stats["total_news"],
                    "topic_mentions": stats["topic_mentions"],
                    "unique_titles": len(stats["unique_titles"]),
                    "coverage_rate": round(coverage_rate, 2),
                    "top_keywords": [
                        {"keyword": k, "count": v}
                        for k, v in stats["top_keywords"].most_common(5)
                    ]
                }

            # Find unique hot spots for each platform
            unique_topics = self._find_unique_topics(platform_stats)

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_stats": result_stats,
                "unique_topics": unique_topics,
                "total_platforms": len(result_stats)
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

    def analyze_keyword_cooccurrence(
        self,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        Keyword co-occurrence analysis - Analyze which keywords often appear together

        Args:
            min_frequency: Minimum co-occurrence frequency
            top_n: Return TOP N keyword pairs

        Returns:
            Keyword co-occurrence analysis results

        Examples:
            User query examples:
            - "Analyze which keywords often appear together"
            - "See which words 'artificial intelligence' often appears with"
            - "Find keyword associations in today's news"

            Code call example:
            >>> tools = AnalyticsTools()
            >>> result = tools.analyze_keyword_cooccurrence(
            ...     min_frequency=5,
            ...     top_n=15
            ... )
            >>> print(result['cooccurrence_pairs'])
        """
        try:
            # Parameter validation
            min_frequency = validate_limit(min_frequency, default=3, max_limit=100)
            top_n = validate_top_n(top_n, default=20)

            # Read today's data
            all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            # Keyword co-occurrence statistics
            cooccurrence = Counter()
            keyword_titles = defaultdict(list)

            for platform_id, titles in all_titles.items():
                for title in titles.keys():
                    # Extract keywords
                    keywords = self._extract_keywords(title)

                    # Record the titles where each keyword appears
                    for kw in keywords:
                        keyword_titles[kw].append(title)

                    # Calculate pairwise co-occurrence
                    if len(keywords) >= 2:
                        for i, kw1 in enumerate(keywords):
                            for kw2 in keywords[i+1:]:
                                # Uniform sorting to avoid duplicates
                                pair = tuple(sorted([kw1, kw2]))
                                cooccurrence[pair] += 1

            # Filter low-frequency co-occurrences
            filtered_pairs = [
                (pair, count) for pair, count in cooccurrence.items()
                if count >= min_frequency
            ]

            # Sort and take TOP N
            top_pairs = sorted(filtered_pairs, key=lambda x: x[1], reverse=True)[:top_n]

            # Build results
            result_pairs = []
            for (kw1, kw2), count in top_pairs:
                # Find title samples containing both keywords
                titles_with_both = [
                    title for title in keyword_titles[kw1]
                    if kw2 in self._extract_keywords(title)
                ]

                result_pairs.append({
                    "keyword1": kw1,
                    "keyword2": kw2,
                    "cooccurrence_count": count,
                    "sample_titles": titles_with_both[:3]
                })

            return {
                "success": True,
                "summary": {
                    "description": "Keyword co-occurrence analysis results",
                    "total": len(result_pairs),
                    "min_frequency": min_frequency,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "data": result_pairs
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

    def analyze_sentiment(
        self,
        topic: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        date_range: Optional[Union[Dict[str, str], str]] = None,
        limit: int = 50,
        sort_by_weight: bool = True,
        include_url: bool = False
    ) -> Dict:
        """
        Sentiment analysis - Generate structured prompts for AI sentiment analysis

        This tool collects news data and generates optimized AI prompts, which you can send to AI for deep sentiment analysis.

        Args:
            topic: Topic keyword (optional), only analyze news containing this keyword
            platforms: Platform filter list (optional), e.g., ['zhihu', 'weibo']
            date_range: Date range (optional), format: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       If not specified, defaults to querying today's data
            limit: Limit on the number of news returned, default 50, max 100
            sort_by_weight: Whether to sort by weight, default True (recommended)
            include_url: Whether to include URL links, default False (saves tokens)

        Returns:
            Structured results containing AI prompts and news data

        Examples:
            User query examples:
            - "Analyze the sentiment of today's news"
            - "See if 'Tesla' related news is positive or negative"
            - "Analyze the sentiment attitude of various platforms towards 'artificial intelligence'"
            - "See if 'Tesla' related news is positive or negative, please select the top 10 news within a week to analyze"

            Code call example:
            >>> tools = AnalyticsTools()
            >>> # Analyze today's Tesla news, return top 10
            >>> result = tools.analyze_sentiment(
            ...     topic="Tesla",
            ...     limit=10
            ... )
            >>> # Analyze Tesla news within a week (assuming today is 2025-11-17)
            >>> result = tools.analyze_sentiment(
            ...     topic="Tesla",
            ...     date_range={"start": "2025-11-11", "end": "2025-11-17"},
            ...     limit=10
            ... )
            >>> print(result['ai_prompt'])  # Get the generated prompt
        """
        try:
            # Parameter validation
            if topic:
                topic = validate_keyword(topic)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Process date range
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # Default today
                start_date = end_date = datetime.now()

            # Collect news data (supports multiple days)
            all_news_items = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # Collect news for that date
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        for title, info in titles.items():
                            # If a topic is specified, only collect titles containing the topic
                            if topic and topic.lower() not in title.lower():
                                continue

                            news_item = {
                                "platform": platform_name,
                                "title": title,
                                "ranks": info.get("ranks", []),
                                "count": len(info.get("ranks", [])),
                                "date": current_date.strftime("%Y-%m-%d")
                            }

                            # Conditionally add URL field
                            if include_url:
                                news_item["url"] = info.get("url", "")
                                news_item["mobileUrl"] = info.get("mobileUrl", "")

                            all_news_items.append(news_item)

                except DataNotFoundError:
                    # No data for this date, continue to the next day
                    pass

                # Next day
                current_date += timedelta(days=1)

            if not all_news_items:
                time_desc = "Today" if start_date == end_date else f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"No related news found ({time_desc})",
                    suggestion="Please try other topics, date ranges, or platforms"
                )

            # Deduplicate (keep the same title only once)
            unique_news = {}
            for item in all_news_items:
                key = f"{item['platform']}::{item['title']}"
                if key not in unique_news:
                    unique_news[key] = item
                else:
                    # Merge ranks (if the same news appears on multiple days)
                    existing = unique_news[key]
                    existing["ranks"].extend(item["ranks"])
                    existing["count"] = len(existing["ranks"])

            deduplicated_news = list(unique_news.values())

            # Sort by weight (if enabled)
            if sort_by_weight:
                deduplicated_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )

            # Limit return quantity
            selected_news = deduplicated_news[:limit]

            # Generate AI prompt
            ai_prompt = self._create_sentiment_analysis_prompt(
                news_data=selected_news,
                topic=topic
            )

            # Build time range description
            if start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "method": "ai_prompt_generation",
                "summary": {
                    "description": "Sentiment analysis data and AI prompt",
                    "total_found": len(deduplicated_news),
                    "returned": len(selected_news),
                    "requested_limit": limit,
                    "duplicates_removed": len(all_news_items) - len(deduplicated_news),
                    "topic": topic,
                    "time_range": time_range_desc,
                    "platforms": list(set(item["platform"] for item in selected_news)),
                    "sorted_by_weight": sort_by_weight
                },
                "ai_prompt": ai_prompt,
                "data": selected_news,
                "usage_note": "Please send the content of the ai_prompt field to AI for sentiment analysis"
            }

            # If the returned quantity is less than the requested quantity, add a note
            if len(selected_news) < limit and len(deduplicated_news) >= limit:
                result["note"] = "The returned quantity is less than the requested quantity due to deduplication logic (the same title is kept only once across different platforms)"
            elif len(deduplicated_news) < limit:
                result["note"] = f"Only {len(deduplicated_news)} matching news found within the specified time range"

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

    def _create_sentiment_analysis_prompt(
        self,
        news_data: List[Dict],
        topic: Optional[str]
    ) -> str:
        """
        Create AI prompt for sentiment analysis

        Args:
            news_data: List of news data (sorted and limited in quantity)
            topic: Topic keywords

        Returns:
            Formatted AI prompt
        """
        # Group by platform
        platform_news = defaultdict(list)
        for item in news_data:
            platform_news[item["platform"]].append({
                "title": item["title"],
                "date": item.get("date", "")
            })

        # Build prompt
        prompt_parts = []

        # 1. Task description
        if topic:
            prompt_parts.append(f"Please analyze the sentiment tendency of the following news titles about '{topic}'.")
        else:
            prompt_parts.append("Please analyze the sentiment tendency of the following news titles.")

        prompt_parts.append("")
        prompt_parts.append("Analysis requirements:")
        prompt_parts.append("1. Identify the sentiment tendency of each news (positive/negative/neutral)")
        prompt_parts.append("2. Count the number and percentage of each sentiment category")
        prompt_parts.append("3. Analyze sentiment differences across different platforms")
        prompt_parts.append("4. Summarize the overall sentiment trend")
        prompt_parts.append("5. List typical positive and negative news samples")
        prompt_parts.append("")

        # 2. Data overview
        prompt_parts.append(f"Data overview:")
        prompt_parts.append(f"- Total news: {len(news_data)}")
        prompt_parts.append(f"- Covered platforms: {len(platform_news)}")

        # Time range
        dates = set(item.get("date", "") for item in news_data if item.get("date"))
        if dates:
            date_list = sorted(dates)
            if len(date_list) == 1:
                prompt_parts.append(f"- Time range: {date_list[0]}")
            else:
                prompt_parts.append(f"- Time range: {date_list[0]} to {date_list[-1]}")

        prompt_parts.append("")

        # 3. Display news by platform
        prompt_parts.append("News list (categorized by platform, sorted by importance):")
        prompt_parts.append("")

        for platform, items in sorted(platform_news.items()):
            prompt_parts.append(f"[{platform}] ({len(items)} items)")
            for i, item in enumerate(items, 1):
                title = item["title"]
                date_str = f" [{item['date']}]" if item.get("date") else ""
                prompt_parts.append(f"{i}. {title}{date_str}")
            prompt_parts.append("")

        # 4. Output format instructions
        prompt_parts.append("Please output the analysis results in the following format:")
        prompt_parts.append("")
        prompt_parts.append("## Sentiment distribution statistics")
        prompt_parts.append("- Positive: XX items (XX%)")
        prompt_parts.append("- Negative: XX items (XX%)")
        prompt_parts.append("- Neutral: XX items (XX%)")
        prompt_parts.append("")
        prompt_parts.append("## Platform sentiment comparison")
        prompt_parts.append("[Differences in sentiment tendencies across platforms]")
        prompt_parts.append("")
        prompt_parts.append("## Overall sentiment trend")
        prompt_parts.append("[Overall analysis and key findings]")
        prompt_parts.append("")
        prompt_parts.append("## Typical samples")
        prompt_parts.append("Positive news samples:")
        prompt_parts.append("[List 3-5 items]")
        prompt_parts.append("")
        prompt_parts.append("Negative news samples:")
        prompt_parts.append("[List 3-5 items]")

        return "\n".join(prompt_parts)

    def find_similar_news(
        self,
        reference_title: str,
        threshold: float = 0.6,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        Similar news search - Find related news based on title similarity

        Args:
            reference_title: Reference title
            threshold: Similarity threshold (between 0-1)
            limit: Return count limit, default 50
            include_url: Whether to include URL links, default False (to save tokens)

        Returns:
            Similar news list

        Examples:
            User query examples:
            - "Find news similar to 'Tesla price cut'"
            - "Find similar reports about the iPhone release"
            - "See if there are any reports similar to this news"

            Code call example:
            >>> tools = AnalyticsTools()
            >>> result = tools.find_similar_news(
            ...     reference_title="Tesla announces price cut",
            ...     threshold=0.6,
            ...     limit=10
            ... )
            >>> print(result['similar_news'])
        """
        try:
            # Parameter validation
            reference_title = validate_keyword(reference_title)
            threshold = validate_threshold(threshold, default=0.6, min_value=0.0, max_value=1.0)
            limit = validate_limit(limit, default=50)

            # Read data
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # Calculate similarity
            similar_items = []

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if title == reference_title:
                        continue

                    # Calculate similarity
                    similarity = self._calculate_similarity(reference_title, title)

                    if similarity >= threshold:
                        news_item = {
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "similarity": round(similarity, 3),
                            "rank": info["ranks"][0] if info["ranks"] else 0
                        }

                        # Conditionally add URL field
                        if include_url:
                            news_item["url"] = info.get("url", "")

                        similar_items.append(news_item)

            # Sort by similarity
            similar_items.sort(key=lambda x: x["similarity"], reverse=True)

            # Limit quantity
            result_items = similar_items[:limit]

            if not result_items:
                raise DataNotFoundError(
                    f"No news found with similarity exceeding {threshold}",
                    suggestion="Please lower the similarity threshold or try another title"
                )

            result = {
                "success": True,
                "summary": {
                    "description": "Similar news search results",
                    "total_found": len(similar_items),
                    "returned": len(result_items),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_title": reference_title
                },
                "data": result_items
            }

            if len(similar_items) < limit:
                result["note"] = f"Only {len(similar_items)} similar news items found under similarity threshold {threshold}"

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

    def search_by_entity(
        self,
        entity: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
        sort_by_weight: bool = True
    ) -> Dict:
        """
        Entity recognition search - Search for news containing specific persons/locations/organizations

        Args:
            entity: Entity name
            entity_type: Entity type (person/location/organization), optional
            limit: Return limit, default 50, max 200
            sort_by_weight: Whether to sort by weight, default True

        Returns:
            List of entity-related news

        Examples:
            User query examples:
            - "Search for news related to Musk"
            - "Find reports about Tesla company, return top 20"
            - "See what news there is in Beijing"

            Code call example:
            >>> tools = AnalyticsTools()
            >>> result = tools.search_by_entity(
            ...     entity="Musk",
            ...     entity_type="person",
            ...     limit=20
            ... )
            >>> print(result['related_news'])
        """
        try:
            # Parameter validation
            entity = validate_keyword(entity)
            limit = validate_limit(limit, default=50)

            if entity_type and entity_type not in ["person", "location", "organization"]:
                raise InvalidParameterError(
                    f"Invalid entity type: {entity_type}",
                    suggestion="Supported types: person, location, organization"
                )

            # Read data
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # Search for news containing the entity
            related_news = []
            entity_context = Counter()  # Count words around the entity

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if entity in title:
                        url = info.get("url", "")
                        mobile_url = info.get("mobileUrl", "")
                        ranks = info.get("ranks", [])
                        count = len(ranks)

                        related_news.append({
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "url": url,
                            "mobileUrl": mobile_url,
                            "ranks": ranks,
                            "count": count,
                            "rank": ranks[0] if ranks else 999
                        })

                        # Extract keywords around the entity
                        keywords = self._extract_keywords(title)
                        entity_context.update(keywords)

            if not related_news:
                raise DataNotFoundError(
                    f"No news found containing the entity '{entity}'",
                    suggestion="Please try other entity names"
                )

            # Remove the entity itself
            if entity in entity_context:
                del entity_context[entity]

            # Sort by weight (if enabled)
            if sort_by_weight:
                related_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )
            else:
                # Sort by ranking
                related_news.sort(key=lambda x: x["rank"])

            # Limit the number of returns
            result_news = related_news[:limit]

            return {
                "success": True,
                "summary": {
                    "description": f"News related to entity '{entity}'",
                    "entity": entity,
                    "entity_type": entity_type or "auto",
                    "total_found": len(related_news),
                    "returned": len(result_news),
                    "sorted_by_weight": sort_by_weight
                },
                "data": result_news,
                "related_keywords": [
                    {"keyword": k, "count": v}
                    for k, v in entity_context.most_common(10)
                ]
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

    def generate_summary_report(
        self,
        report_type: str = "daily",
        date_range: Optional[Union[Dict[str, str], str]] = None
    ) -> Dict:
        """
        Daily/weekly summary generator - Automatically generate hot topic summary reports

        Args:
            report_type: Report type (daily/weekly)
            date_range: Custom date range (optional)

        Returns:
            Summary report in Markdown format

        Examples:
            User query examples:
            - "Generate today's news summary report"
            - "Give me a summary of hot topics this week"
            - "Generate a news analysis report for the past 7 days"

            Code call example:
            >>> tools = AnalyticsTools()
            >>> result = tools.generate_summary_report(
            ...     report_type="daily"
            ... )
            >>> print(result['markdown_report'])
        """
        try:
            # Parameter validation
            if report_type not in ["daily", "weekly"]:
                raise InvalidParameterError(
                    f"Invalid report type: {report_type}",
                    suggestion="Supported types: daily, weekly"
                )

            # Determine date range
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                if report_type == "daily":
                    start_date = end_date = datetime.now()
                else:  # weekly
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=6)

            # Collect data
            all_keywords = Counter()
            all_platforms_news = defaultdict(int)
            all_titles_list = []

            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        all_platforms_news[platform_name] += len(titles)

                        for title in titles.keys():
                            all_titles_list.append({
                                "title": title,
                                "platform": platform_name,
                                "date": current_date.strftime("%Y-%m-%d")
                            })

                            # Extract keywords
                            keywords = self._extract_keywords(title)
                            all_keywords.update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # Generate report
            report_title = f"{'Daily' if report_type == 'daily' else 'Weekly'} News Hotspot Summary"
            date_str = f"{start_date.strftime('%Y-%m-%d')}" if report_type == "daily" else f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            # Build Markdown report
            markdown = f"""# {report_title}

**Report Date**: {date_str}
**Generation Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Data Overview

- **Total News Count**: {len(all_titles_list)}
- **Covered Platforms**: {len(all_platforms_news)}
- **Hot Keywords Count**: {len(all_keywords)}

## 🔥 TOP 10 Hot Topics

"""

            # Add TOP 10 keywords
            for i, (keyword, count) in enumerate(all_keywords.most_common(10), 1):
                markdown += f"{i}. **{keyword}** - Appears {count} times\n"

            # Platform analysis
            markdown += "\n## 📱 Platform Activity\n\n"
            sorted_platforms = sorted(all_platforms_news.items(), key=lambda x: x[1], reverse=True)

            for platform, count in sorted_platforms:
                markdown += f"- **{platform}**: {count} news items\n"

            # Trend changes (if weekly report)
            if report_type == "weekly":
                markdown += "\n## 📈 Trend Analysis\n\n"
                markdown += "Topics with sustained popularity this week (sample data):\n\n"

                # Simple trend analysis
                top_keywords = [kw for kw, _ in all_keywords.most_common(5)]
                for keyword in top_keywords:
                    markdown += f"- **{keyword}**: Consistently hot\n"

            # Add sample news (selected by weight to ensure determinism)
            markdown += "\n## 📰 Selected News Samples\n\n"

            # Deterministic selection: sort by title weight, take top 5
            # This way the same input always returns the same result
            if all_titles_list:
                # Calculate weight score for each news item (based on keyword occurrences)
                news_with_scores = []
                for news in all_titles_list:
                    # Simple weight: count occurrences of TOP keywords
                    score = 0
                    title_lower = news['title'].lower()
                    for keyword, count in all_keywords.most_common(10):
                        if keyword.lower() in title_lower:
                            score += count
                    news_with_scores.append((news, score))

                # Sort by weight descending, if weights are equal sort alphabetically by title (ensure determinism)
                news_with_scores.sort(key=lambda x: (-x[1], x[0]['title']))

                # Take top 5
                sample_news = [item[0] for item in news_with_scores[:5]]

                for news in sample_news:
                    markdown += f"- [{news['platform']}] {news['title']}\n"

            markdown += "\n---\n\n*This report is automatically generated by TrendRadar MCP*\n"

            return {
                "success": True,
                "report_type": report_type,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "markdown_report": markdown,
                "statistics": {
                    "total_news": len(all_titles_list),
                    "platforms_count": len(all_platforms_news),
                    "keywords_count": len(all_keywords),
                    "top_keyword": all_keywords.most_common(1)[0] if all_keywords else None
                }
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

    def get_platform_activity_stats(
        self,
        date_range: Optional[Union[Dict[str, str], str]] = None
    ) -> Dict:
        """
        Platform activity statistics - Statistics on publishing frequency and active time periods of each platform

        Args:
            date_range: Date range (optional)

        Returns:
            Platform activity statistics results

        Examples:
            User query examples:
            - "Count the activity of each platform today"
            - "See which platform updates most frequently"
            - "Analyze the publishing time patterns of each platform"

            Code call example:
            >>> # View platform activity (assuming today is 2025-11-17)
            >>> result = tools.get_platform_activity_stats(
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"}
            ... )
            >>> print(result['platform_activity'])
        """
        try:
            # Parameter validation
            date_range_tuple = validate_date_range(date_range)

            # Determine date range
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # Calculate activity for each platform
            platform_activity = defaultdict(lambda: {
                "total_updates": 0,
                "days_active": set(),
                "news_count": 0,
                "hourly_distribution": Counter()
            })

            # Iterate through date range
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        platform_activity[platform_name]["news_count"] += len(titles)
                        platform_activity[platform_name]["days_active"].add(current_date.strftime("%Y-%m-%d"))

                        # Count update frequency (based on file count)
                        platform_activity[platform_name]["total_updates"] += len(timestamps)

                        # Calculate time distribution (based on time in filename)
                        for filename in timestamps.keys():
                            # Parse hour from filename (format: HHMM.txt)
                            match = re.match(r'(\d{2})(\d{2})\.txt', filename)
                            if match:
                                hour = int(match.group(1))
                                platform_activity[platform_name]["hourly_distribution"][hour] += 1

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # Convert to serializable format
            result_activity = {}
            for platform, stats in platform_activity.items():
                days_count = len(stats["days_active"])
                avg_news_per_day = stats["news_count"] / days_count if days_count > 0 else 0

                # Find the most active time period
                most_active_hours = stats["hourly_distribution"].most_common(3)

                result_activity[platform] = {
                    "total_updates": stats["total_updates"],
                    "news_count": stats["news_count"],
                    "days_active": days_count,
                    "avg_news_per_day": round(avg_news_per_day, 2),
                    "most_active_hours": [
                        {"hour": f"{hour:02d}:00", "count": count}
                        for hour, count in most_active_hours
                    ],
                    "activity_score": round(stats["news_count"] / max(days_count, 1), 2)
                }

            # Sort by activity level
            sorted_platforms = sorted(
                result_activity.items(),
                key=lambda x: x[1]["activity_score"],
                reverse=True
            )

            return {
                "success": True,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_activity": dict(sorted_platforms),
                "most_active_platform": sorted_platforms[0][0] if sorted_platforms else None,
                "total_platforms": len(result_activity)
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

    def analyze_topic_lifecycle(
        self,
        topic: str,
        date_range: Optional[Union[Dict[str, str], str]] = None
    ) -> Dict:
        """
        Topic lifecycle analysis - Track the complete cycle of a topic from appearance to disappearance

        Args:
            topic: Topic keyword
            date_range: Date range (optional)
                       - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **Default**: If not specified, defaults to analyzing the last 7 days

        Returns:
            Topic lifecycle analysis results

        Examples:
            User query examples:
            - "Analyze the lifecycle of the 'artificial intelligence' topic"
            - "See if the 'iPhone' topic is a flash in the pan or a continuous hot spot"
            - "Track the popularity changes of the 'Bitcoin' topic"

            Code call example:
            >>> # Analyze topic lifecycle (assuming today is 2025-11-17)
            >>> result = tools.analyze_topic_lifecycle(
            ...     topic="artificial intelligence",
            ...     date_range={"start": "2025-10-19", "end": "2025-11-17"}
            ... )
            >>> print(result['lifecycle_stage'])
        """
        try:
            # Parameter validation
            topic = validate_keyword(topic)

            # Process date range (defaults to the last 7 days if not specified)
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # Default to the last 7 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            # Collect topic historical data
            lifecycle_data = []
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    # Count the number of topic appearances on that day
                    count = 0
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1

                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count
                    })

                except DataNotFoundError:
                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0
                    })

                current_date += timedelta(days=1)

            # Calculate the number of analysis days
            total_days = (end_date - start_date).days + 1

            # Analyze lifecycle stage
            counts = [item["count"] for item in lifecycle_data]

            if not any(counts):
                time_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"Topic '{topic}' not found within {time_desc}",
                    suggestion="Please try other topics or expand the time range"
                )

            # Find first appearance and last appearance
            first_appearance = next((item["date"] for item in lifecycle_data if item["count"] > 0), None)
            last_appearance = next((item["date"] for item in reversed(lifecycle_data) if item["count"] > 0), None)

            # Calculate peak value
            max_count = max(counts)
            peak_index = counts.index(max_count)
            peak_date = lifecycle_data[peak_index]["date"]

            # Calculate average and standard deviation (simple implementation)
            non_zero_counts = [c for c in counts if c > 0]
            avg_count = sum(non_zero_counts) / len(non_zero_counts) if non_zero_counts else 0

            # Determine lifecycle stage
            recent_counts = counts[-3:]  # Last 3 days
            early_counts = counts[:3]    # First 3 days

            if sum(recent_counts) > sum(early_counts):
                lifecycle_stage = "Growth phase"
            elif sum(recent_counts) < sum(early_counts) * 0.5:
                lifecycle_stage = "Decline stage"
            elif max_count in recent_counts:
                lifecycle_stage = "Outbreak stage"
            else:
                lifecycle_stage = "Stable stage"

            # Classification: Flash in the pan vs Sustained hot topic
            active_days = sum(1 for c in counts if c > 0)

            if active_days <= 2 and max_count > avg_count * 2:
                topic_type = "Flash in the pan"
            elif active_days >= total_days * 0.6:
                topic_type = "Sustained hot topic"
            else:
                topic_type = "Cyclical hot topic"

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "total_days": total_days
                },
                "lifecycle_data": lifecycle_data,
                "analysis": {
                    "first_appearance": first_appearance,
                    "last_appearance": last_appearance,
                    "peak_date": peak_date,
                    "peak_count": max_count,
                    "active_days": active_days,
                    "avg_daily_mentions": round(avg_count, 2),
                    "lifecycle_stage": lifecycle_stage,
                    "topic_type": topic_type
                }
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

    def detect_viral_topics(
        self,
        threshold: float = 3.0,
        time_window: int = 24
    ) -> Dict:
        """
        Abnormal popularity detection - Automatically identify suddenly viral topics

        Args:
            threshold: Popularity surge multiplier threshold
            time_window: Detection time window (hours)

        Returns:
            List of viral topics

        Examples:
            User query examples:
            - "Detect which topics suddenly went viral today"
            - "See if there is any news with abnormal popularity"
            - "Warn of possible major events"

            Code invocation example:
            >>> tools = AnalyticsTools()
            >>> result = tools.detect_viral_topics(
            ...     threshold=3.0,
            ...     time_window=24
            ... )
            >>> print(result['viral_topics'])
        """
        try:
            # Parameter validation
            threshold = validate_threshold(threshold, default=3.0, min_value=1.0, max_value=100.0)
            time_window = validate_limit(time_window, default=24, max_limit=72)

            # Read current and previous data
            current_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            # Read yesterday's data as a baseline
            yesterday = datetime.now() - timedelta(days=1)
            try:
                previous_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                    date=yesterday
                )
            except DataNotFoundError:
                previous_all_titles = {}

            # Count current keyword frequency
            current_keywords = Counter()
            current_keyword_titles = defaultdict(list)

            for _, titles in current_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    current_keywords.update(keywords)

                    for kw in keywords:
                        current_keyword_titles[kw].append(title)

            # Count previous keyword frequency
            previous_keywords = Counter()

            for _, titles in previous_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    previous_keywords.update(keywords)

            # Detect abnormal popularity
            viral_topics = []

            for keyword, current_count in current_keywords.items():
                previous_count = previous_keywords.get(keyword, 0)

                # Calculate growth multiplier
                if previous_count == 0:
                    # Newly emerged topics
                    if current_count >= 5:  # Must appear at least 5 times to be considered viral
                        growth_rate = float('inf')
                        is_viral = True
                    else:
                        continue
                else:
                    growth_rate = current_count / previous_count
                    is_viral = growth_rate >= threshold

                if is_viral:
                    viral_topics.append({
                        "keyword": keyword,
                        "current_count": current_count,
                        "previous_count": previous_count,
                        "growth_rate": round(growth_rate, 2) if growth_rate != float('inf') else "New topic",
                        "sample_titles": current_keyword_titles[keyword][:3],
                        "alert_level": "High" if growth_rate > threshold * 2 else "Medium"
                    })

            # Sort by growth rate
            viral_topics.sort(
                key=lambda x: x["current_count"] if x["growth_rate"] == "New topic" else x["growth_rate"],
                reverse=True
            )

            if not viral_topics:
                return {
                    "success": True,
                    "summary": {
                        "description": "Abnormal popularity detection results",
                        "total": 0,
                        "threshold": threshold,
                        "time_window": time_window
                    },
                    "data": [],
                    "message": f"No topics detected with popularity growth exceeding {threshold} times"
                }

            return {
                "success": True,
                "summary": {
                    "description": "Abnormal popularity detection results",
                    "total": len(viral_topics),
                    "threshold": threshold,
                    "time_window": time_window,
                    "detection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "data": viral_topics
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

    def predict_trending_topics(
        self,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        Topic prediction - Predict future potential hot spots based on historical data

        Args:
            lookahead_hours: How many hours ahead to predict
            confidence_threshold: Confidence threshold

        Returns:
            List of predicted potential topics

        Examples:
            User query examples:
            - "Predict potential hot topics for the next 6 hours"
            - "What topics might become popular"
            - "Early discovery of potential topics"

            Code calling example:
            >>> tools = AnalyticsTools()
            >>> result = tools.predict_trending_topics(
            ...     lookahead_hours=6,
            ...     confidence_threshold=0.7
            ... )
            >>> print(result['predicted_topics'])
        """
        try:
            # Parameter validation
            lookahead_hours = validate_limit(lookahead_hours, default=6, max_limit=48)
            confidence_threshold = validate_threshold(
                confidence_threshold,
                default=0.7,
                min_value=0.0,
                max_value=1.0,
                param_name="confidence_threshold"
            )

            # Collect data from the last 3 days for prediction
            keyword_trends = defaultdict(list)

            for days_ago in range(3, 0, -1):
                date = datetime.now() - timedelta(days=days_ago)

                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=date
                    )

                    # Count keywords
                    keywords_count = Counter()
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            keywords = self._extract_keywords(title)
                            keywords_count.update(keywords)

                    # Record historical data for each keyword
                    for keyword, count in keywords_count.items():
                        keyword_trends[keyword].append(count)

                except DataNotFoundError:
                    pass

            # Add today's data
            try:
                all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

                keywords_count = Counter()
                keyword_titles = defaultdict(list)

                for _, titles in all_titles.items():
                    for title in titles.keys():
                        keywords = self._extract_keywords(title)
                        keywords_count.update(keywords)

                        for kw in keywords:
                            keyword_titles[kw].append(title)

                for keyword, count in keywords_count.items():
                    keyword_trends[keyword].append(count)

            except DataNotFoundError:
                raise DataNotFoundError(
                    "Today's data not found",
                    suggestion="Please wait for the crawler task to complete"
                )

            # Predict potential topics
            predicted_topics = []

            for keyword, trend_data in keyword_trends.items():
                if len(trend_data) < 2:
                    continue

                # Simple linear trend prediction
                # Calculate growth rate
                recent_value = trend_data[-1]
                previous_value = trend_data[-2] if len(trend_data) >= 2 else 0

                if previous_value == 0:
                    if recent_value >= 3:
                        growth_rate = 1.0
                    else:
                        continue
                else:
                    growth_rate = (recent_value - previous_value) / previous_value

                # Determine if it is an upward trend
                if growth_rate > 0.3:  # Growth exceeds 30%
                    # Calculate confidence (based on trend stability)
                    if len(trend_data) >= 3:
                        # Check for continuous growth
                        is_consistent = all(
                            trend_data[i] <= trend_data[i+1]
                            for i in range(len(trend_data)-1)
                        )
                        confidence = 0.9 if is_consistent else 0.7
                    else:
                        confidence = 0.6

                    if confidence >= confidence_threshold:
                        predicted_topics.append({
                            "keyword": keyword,
                            "current_count": recent_value,
                            "growth_rate": round(growth_rate * 100, 2),
                            "confidence": round(confidence, 2),
                            "trend_data": trend_data,
                            "prediction": "Upward trend, may become a hot topic",
                            "sample_titles": keyword_titles.get(keyword, [])[:3]
                        })

            # Sort by confidence and growth rate
            predicted_topics.sort(
                key=lambda x: (x["confidence"], x["growth_rate"]),
                reverse=True
            )

            return {
                "success": True,
                "summary": {
                    "description": "Hot topic prediction results",
                    "total": len(predicted_topics),
                    "returned": min(20, len(predicted_topics)),
                    "lookahead_hours": lookahead_hours,
                    "confidence_threshold": confidence_threshold,
                    "prediction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "data": predicted_topics[:20],  # Return TOP 20
                "note": "Prediction is based on historical trends, actual results may vary"
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

    # ==================== Helper methods ====================

    def _extract_keywords(self, title: str, min_length: int = 2) -> List[str]:
        """
        Extract keywords from title (simple implementation)

        Args:
            title: Title text
            min_length: Minimum keyword length

        Returns:
            Keyword list
        """
        # Remove URLs and special characters
        title = re.sub(r'http[s]?://\S+', '', title)
        title = re.sub(r'[^\w\s]', ' ', title)

        # Simple tokenization (by spaces and common separators)
        words = re.split(r'[\s，。！？、]+', title)

        # Filter stop words and short words
        stopwords = {'of', 'le', 'in', 'is', 'I', 'have', 'and', 'just', 'not', 'person', 'all', 'one', 'a', 'on', 'also', 'very', 'to', 'say', 'want', 'go', 'you', 'will', 'zhe', 'no', 'look', 'good', 'self', 'this'}

        keywords = [
            word.strip() for word in words
            if word.strip() and len(word.strip()) >= min_length and word.strip() not in stopwords
        ]

        return keywords

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts

        Args:
            text1: Text 1
            text2: Text 2

        Returns:
            Similarity score (between 0-1)
        """
        # Use SequenceMatcher to calculate similarity
        return SequenceMatcher(None, text1, text2).ratio()

    def _find_unique_topics(self, platform_stats: Dict) -> Dict[str, List[str]]:
        """
        Find unique hot topics for each platform

        Args:
            platform_stats: Platform statistics

        Returns:
            Dictionary of unique topics for each platform
        """
        unique_topics = {}

        # Get TOP keywords for each platform
        platform_keywords = {}
        for platform, stats in platform_stats.items():
            top_keywords = set([kw for kw, _ in stats["top_keywords"].most_common(10)])
            platform_keywords[platform] = top_keywords

        # Find unique keywords
        for platform, keywords in platform_keywords.items():
            # Find all keywords from other platforms
            other_keywords = set()
            for other_platform, other_kws in platform_keywords.items():
                if other_platform != platform:
                    other_keywords.update(other_kws)

            # Find unique ones
            unique = keywords - other_keywords
            if unique:
                unique_topics[platform] = list(unique)[:5]  # Max 5

        return unique_topics

    # ==================== Cross-platform aggregation tools ====================

    def aggregate_news(
        self,
        date_range: Optional[Union[Dict[str, str], str]] = None,
        platforms: Optional[List[str]] = None,
        similarity_threshold: float = 0.7,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        Cross-platform news aggregation - deduplicate and merge similar news

        Merge the same event reported by different platforms into one aggregated news,
        displaying the coverage and comprehensive popularity of the news across platforms.

        Args:
            date_range: Date range (optional)
                - Not specified: Query today
                - {\"start\": \"YYYY-MM-DD\", \"end\": \"YYYY-MM-DD\"}: Date range
            platforms: Platform filter list, e.g., ['zhihu', 'weibo']
            similarity_threshold: Similarity threshold, between 0-1, default 0.7
            limit: Number of aggregated news to return, default 50
            include_url: Whether to include URL links, default False

        Returns:
            Aggregated result dictionary, containing:
            - aggregated_news: Aggregated news list
            - statistics: Aggregation statistics
        """
        try:
            # Parameter validation
            platforms = validate_platforms(platforms)
            similarity_threshold = validate_threshold(
                similarity_threshold, default=0.7, min_value=0.3, max_value=1.0
            )
            limit = validate_limit(limit, default=50)

            # Process date range
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # Collect all news
            all_news = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title, info in titles.items():
                            news_item = {
                                "title": title,
                                "platform": platform_id,
                                "platform_name": platform_name,
                                "date": current_date.strftime("%Y-%m-%d"),
                                "ranks": info.get("ranks", []),
                                "count": len(info.get("ranks", [])),
                                "rank": info["ranks"][0] if info["ranks"] else 999
                            }

                            if include_url:
                                news_item["url"] = info.get("url", "")
                                news_item["mobileUrl"] = info.get("mobileUrl", "")

                            # Calculate weights
                            news_item["weight"] = calculate_news_weight(news_item)
                            all_news.append(news_item)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            if not all_news:
                return {
                    "success": True,
                    "summary": {
                        "description": "Cross-platform news aggregation results",
                        "total": 0,
                        "returned": 0
                    },
                    "data": [],
                    "message": "No news data found"
                }

            # Execute aggregation
            aggregated = self._aggregate_similar_news(
                all_news, similarity_threshold, include_url
            )

            # Sort by comprehensive weight
            aggregated.sort(key=lambda x: x["aggregate_weight"], reverse=True)

            # Limit return quantity
            results = aggregated[:limit]

            # Statistics
            total_original = len(all_news)
            total_aggregated = len(aggregated)
            dedup_rate = 1 - (total_aggregated / total_original) if total_original > 0 else 0

            platform_coverage = Counter()
            for item in aggregated:
                for p in item["platforms"]:
                    platform_coverage[p] += 1

            return {
                "success": True,
                "summary": {
                    "description": "Cross-platform news aggregation results",
                    "original_count": total_original,
                    "aggregated_count": total_aggregated,
                    "returned": len(results),
                    "deduplication_rate": f"{dedup_rate * 100:.1f}%",
                    "similarity_threshold": similarity_threshold,
                    "date_range": {
                        "start": start_date.strftime("%Y-%m-%d"),
                        "end": end_date.strftime("%Y-%m-%d")
                    }
                },
                "data": results,
                "statistics": {
                    "platform_coverage": dict(platform_coverage),
                    "multi_platform_news": len([a for a in aggregated if len(a["platforms"]) > 1]),
                    "single_platform_news": len([a for a in aggregated if len(a["platforms"]) == 1])
                }
            }

        except MCPError as e:
            return {"success": False, "error": e.to_dict()}
        except Exception as e:
            return {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}

    def _aggregate_similar_news(
        self,
        news_list: List[Dict],
        threshold: float,
        include_url: bool
    ) -> List[Dict]:
        """
        Perform similarity aggregation on the news list

        Use a two-layer filtering strategy: first use Jaccard for fast coarse screening, then use SequenceMatcher for precise calculation

        Args:
            news_list: News list
            threshold: Similarity threshold
            include_url: Whether to include URL

        Returns:
            Aggregated news list
        """
        if not news_list:
            return []

        # Pre-calculate character sets for fast filtering
        prepared_news = []
        for news in news_list:
            char_set = set(news["title"])
            prepared_news.append({
                "data": news,
                "char_set": char_set,
                "set_len": len(char_set)
            })

        # Sort by weight
        sorted_items = sorted(prepared_news, key=lambda x: x["data"].get("weight", 0), reverse=True)

        aggregated = []
        used_indices = set()
        PRE_FILTER_RATIO = 0.5  # Coarse screening threshold coefficient

        for i, item in enumerate(sorted_items):
            if i in used_indices:
                continue

            news = item["data"]
            base_set = item["char_set"]
            base_len = item["set_len"]

            group = {
                "representative_title": news["title"],
                "platforms": [news["platform_name"]],
                "platform_ids": [news["platform"]],
                "dates": [news["date"]],
                "best_rank": news["rank"],
                "total_count": news["count"],
                "aggregate_weight": news.get("weight", 0),
                "sources": [{
                    "platform": news["platform_name"],
                    "rank": news["rank"],
                    "date": news["date"]
                }]
            }

            if include_url and news.get("url"):
                group["urls"] = [{
                    "platform": news["platform_name"],
                    "url": news.get("url", ""),
                    "mobileUrl": news.get("mobileUrl", "")
                }]

            used_indices.add(i)

            # Find similar news
            for j in range(i + 1, len(sorted_items)):
                if j in used_indices:
                    continue

                compare_item = sorted_items[j]
                compare_set = compare_item["char_set"]
                compare_len = compare_item["set_len"]

                # Fast coarse screening: length check
                if base_len == 0 or compare_len == 0:
                    continue

                # Fast coarse screening: length ratio check
                if min(base_len, compare_len) / max(base_len, compare_len) < (threshold * PRE_FILTER_RATIO):
                    continue

                # Fast coarse screening: Jaccard similarity
                intersection = len(base_set & compare_set)
                union = len(base_set | compare_set)
                jaccard_sim = intersection / union if union > 0 else 0

                if jaccard_sim < (threshold * PRE_FILTER_RATIO):
                    continue

                # Exact calculation: SequenceMatcher
                other_news = compare_item["data"]
                real_similarity = self._calculate_similarity(news["title"], other_news["title"])

                if real_similarity >= threshold:
                    # Merge into current group
                    if other_news["platform_name"] not in group["platforms"]:
                        group["platforms"].append(other_news["platform_name"])
                        group["platform_ids"].append(other_news["platform"])

                    if other_news["date"] not in group["dates"]:
                        group["dates"].append(other_news["date"])

                    group["best_rank"] = min(group["best_rank"], other_news["rank"])
                    group["total_count"] += other_news["count"]
                    group["aggregate_weight"] += other_news.get("weight", 0) * 0.5  # Extra weight

                    group["sources"].append({
                        "platform": other_news["platform_name"],
                        "rank": other_news["rank"],
                        "date": other_news["date"]
                    })

                    if include_url and other_news.get("url"):
                        if "urls" not in group:
                            group["urls"] = []
                        group["urls"].append({
                            "platform": other_news["platform_name"],
                            "url": other_news.get("url", ""),
                            "mobileUrl": other_news.get("mobileUrl", "")
                        })

                    used_indices.add(j)

            # Add aggregate information
            group["platform_count"] = len(group["platforms"])
            group["is_cross_platform"] = len(group["platforms"]) > 1

            aggregated.append(group)

        return aggregated

    # ==================== Period comparison analysis tool ====================

    def compare_periods(
        self,
        period1: Union[Dict[str, str], str],
        period2: Union[Dict[str, str], str],
        topic: Optional[str] = None,
        compare_type: str = "overview",
        platforms: Optional[List[str]] = None,
        top_n: int = 10
    ) -> Dict:
        """
        Period comparison analysis - Compare news data from two time periods

        Supports multiple comparison dimensions: popularity comparison, topic shift, platform activity, etc.

        Args:
            period1: First time period
                - {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}: Date range
                - "today", "yesterday", "last_week", "last_month": Preset values
            period2: Second time period (same format as period1)
            topic: Optional topic keywords (focus on comparison of specific topics)
            compare_type: Comparison type
                - "overview": General overview (default)
                - "topic_shift": Topic shift analysis
                - "platform_activity": Platform activity comparison
            platforms: Platform filter list
            top_n: Return TOP N results, default 10

        Returns:
            Comparison analysis result dictionary
        """
        try:
            # Parameter validation
            platforms = validate_platforms(platforms)
            top_n = validate_top_n(top_n, default=10)

            if compare_type not in ["overview", "topic_shift", "platform_activity"]:
                raise InvalidParameterError(
                    f"Unsupported comparison type: {compare_type}",
                    suggestion="Supported types: overview, topic_shift, platform_activity"
                )

            # Parse time periods
            date_range1 = self._parse_period(period1)
            date_range2 = self._parse_period(period2)

            if not date_range1 or not date_range2:
                raise InvalidParameterError(
                    "Invalid time period format",
                    suggestion="Use {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'} or preset values like 'last_week'"
                )

            # Collect data for both periods
            data1 = self._collect_period_data(date_range1, platforms, topic)
            data2 = self._collect_period_data(date_range2, platforms, topic)

            # Execute different analysis based on comparison type
            if compare_type == "overview":
                analysis_result = self._compare_overview(data1, data2, date_range1, date_range2, top_n)
            elif compare_type == "topic_shift":
                analysis_result = self._compare_topic_shift(data1, data2, date_range1, date_range2, top_n)
            else:  # platform_activity
                analysis_result = self._compare_platform_activity(data1, data2, date_range1, date_range2)

            result = {
                "success": True,
                "summary": {
                    "description": f"Period comparison analysis ({compare_type})",
                    "compare_type": compare_type,
                    "periods": {
                        "period1": {
                            "start": date_range1[0].strftime("%Y-%m-%d"),
                            "end": date_range1[1].strftime("%Y-%m-%d")
                        },
                        "period2": {
                            "start": date_range2[0].strftime("%Y-%m-%d"),
                            "end": date_range2[1].strftime("%Y-%m-%d")
                        }
                    }
                },
                "data": analysis_result
            }

            if topic:
                result["summary"]["topic_filter"] = topic

            return result

        except MCPError as e:
            return {"success": False, "error": e.to_dict()}
        except Exception as e:
            return {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}

    def _parse_period(self, period: Union[Dict[str, str], str]) -> Optional[tuple]:
        """Parse time period into date range tuple"""
        today = datetime.now()

        if isinstance(period, str):
            if period == "today":
                return (today, today)
            elif period == "yesterday":
                yesterday = today - timedelta(days=1)
                return (yesterday, yesterday)
            elif period == "last_week":
                return (today - timedelta(days=7), today - timedelta(days=1))
            elif period == "this_week":
                # This Monday to today
                days_since_monday = today.weekday()
                monday = today - timedelta(days=days_since_monday)
                return (monday, today)
            elif period == "last_month":
                return (today - timedelta(days=30), today - timedelta(days=1))
            elif period == "this_month":
                first_of_month = today.replace(day=1)
                return (first_of_month, today)
            else:
                return None
        elif isinstance(period, dict):
            try:
                start = datetime.strptime(period["start"], "%Y-%m-%d")
                end = datetime.strptime(period["end"], "%Y-%m-%d")
                return (start, end)
            except (KeyError, ValueError):
                return None
        return None

    def _collect_period_data(
        self,
        date_range: tuple,
        platforms: Optional[List[str]],
        topic: Optional[str]
    ) -> Dict:
        """Collect news data for specified period"""
        start_date, end_date = date_range
        all_news = []
        all_keywords = Counter()
        platform_stats = Counter()

        current_date = start_date
        while current_date <= end_date:
            try:
                all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                    date=current_date,
                    platform_ids=platforms
                )

                for platform_id, titles in all_titles.items():
                    platform_name = id_to_name.get(platform_id, platform_id)

                    for title, info in titles.items():
                        # If topic is specified, filter irrelevant news
                        if topic and topic.lower() not in title.lower():
                            continue

                        news_item = {
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "date": current_date.strftime("%Y-%m-%d"),
                            "ranks": info.get("ranks", []),
                            "rank": info["ranks"][0] if info["ranks"] else 999
                        }
                        news_item["weight"] = calculate_news_weight(news_item)
                        all_news.append(news_item)

                        # Count platforms
                        platform_stats[platform_name] += 1

                        # Extract keywords
                        keywords = self._extract_keywords(title)
                        all_keywords.update(keywords)

            except DataNotFoundError:
                pass

            current_date += timedelta(days=1)

        return {
            "news": all_news,
            "news_count": len(all_news),
            "keywords": all_keywords,
            "platform_stats": platform_stats,
            "date_range": date_range
        }

    def _compare_overview(
        self,
        data1: Dict,
        data2: Dict,
        range1: tuple,
        range2: tuple,
        top_n: int
    ) -> Dict:
        """General overview comparison"""
        # Calculate changes
        count_change = data2["news_count"] - data1["news_count"]
        count_change_pct = (count_change / data1["news_count"] * 100) if data1["news_count"] > 0 else 0

        # TOP keywords comparison
        top_kw1 = [kw for kw, _ in data1["keywords"].most_common(top_n)]
        top_kw2 = [kw for kw, _ in data2["keywords"].most_common(top_n)]

        new_keywords = [kw for kw in top_kw2 if kw not in top_kw1]
        disappeared_keywords = [kw for kw in top_kw1 if kw not in top_kw2]
        persistent_keywords = [kw for kw in top_kw1 if kw in top_kw2]

        # TOP news comparison
        top_news1 = sorted(data1["news"], key=lambda x: x.get("weight", 0), reverse=True)[:top_n]
        top_news2 = sorted(data2["news"], key=lambda x: x.get("weight", 0), reverse=True)[:top_n]

        return {
            "overview": {
                "period1_count": data1["news_count"],
                "period2_count": data2["news_count"],
                "count_change": count_change,
                "count_change_percent": f"{count_change_pct:+.1f}%"
            },
            "keyword_analysis": {
                "new_keywords": new_keywords[:5],
                "disappeared_keywords": disappeared_keywords[:5],
                "persistent_keywords": persistent_keywords[:5]
            },
            "top_news": {
                "period1": [{"title": n["title"], "platform": n["platform_name"]} for n in top_news1],
                "period2": [{"title": n["title"], "platform": n["platform_name"]} for n in top_news2]
            }
        }

    def _compare_topic_shift(
        self,
        data1: Dict,
        data2: Dict,
        range1: tuple,
        range2: tuple,
        top_n: int
    ) -> Dict:
        """Topic shift analysis"""
        kw1 = data1["keywords"]
        kw2 = data2["keywords"]

        # Calculate popularity changes
        all_keywords = set(kw1.keys()) | set(kw2.keys())
        keyword_changes = []

        for kw in all_keywords:
            count1 = kw1.get(kw, 0)
            count2 = kw2.get(kw, 0)
            change = count2 - count1

            if count1 > 0:
                change_pct = (change / count1) * 100
            elif count2 > 0:
                change_pct = 100  # Newly appeared
            else:
                change_pct = 0

            keyword_changes.append({
                "keyword": kw,
                "period1_count": count1,
                "period2_count": count2,
                "change": change,
                "change_percent": round(change_pct, 1)
            })

        # Sort by change magnitude
        rising = sorted([k for k in keyword_changes if k["change"] > 0],
                       key=lambda x: x["change"], reverse=True)[:top_n]
        falling = sorted([k for k in keyword_changes if k["change"] < 0],
                        key=lambda x: x["change"])[:top_n]
        new_topics = [k for k in keyword_changes if k["period1_count"] == 0 and k["period2_count"] > 0][:top_n]

        return {
            "rising_topics": rising,
            "falling_topics": falling,
            "new_topics": new_topics,
            "total_keywords": {
                "period1": len(kw1),
                "period2": len(kw2)
            }
        }

    def _compare_platform_activity(
        self,
        data1: Dict,
        data2: Dict,
        range1: tuple,
        range2: tuple
    ) -> Dict:
        """Platform activity comparison"""
        ps1 = data1["platform_stats"]
        ps2 = data2["platform_stats"]

        all_platforms = set(ps1.keys()) | set(ps2.keys())
        platform_changes = []

        for platform in all_platforms:
            count1 = ps1.get(platform, 0)
            count2 = ps2.get(platform, 0)
            change = count2 - count1

            if count1 > 0:
                change_pct = (change / count1) * 100
            elif count2 > 0:
                change_pct = 100
            else:
                change_pct = 0

            platform_changes.append({
                "platform": platform,
                "period1_count": count1,
                "period2_count": count2,
                "change": change,
                "change_percent": round(change_pct, 1)
            })

        # Sort by change
        platform_changes.sort(key=lambda x: x["change"], reverse=True)

        return {
            "platform_comparison": platform_changes,
            "most_active_growth": platform_changes[0] if platform_changes else None,
            "least_active_growth": platform_changes[-1] if platform_changes else None,
            "total_activity": {
                "period1": sum(ps1.values()),
                "period2": sum(ps2.values())
            }
        }
