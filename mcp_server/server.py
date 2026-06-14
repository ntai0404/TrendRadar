"""
TrendRadar MCP Server - FastMCP 2.0 Implementation

Use FastMCP 2.0 to provide a production-grade MCP tool server.
Supports both stdio and HTTP transport modes.
"""

import asyncio
import json
from typing import List, Optional, Dict, Union

from fastmcp import FastMCP

from .tools.data_query import DataQueryTools
from .tools.analytics import AnalyticsTools
from .tools.search_tools import SearchTools
from .tools.config_mgmt import ConfigManagementTools
from .tools.system import SystemManagementTools
from .tools.storage_sync import StorageSyncTools
from .tools.article_reader import ArticleReaderTools
from .tools.notification import NotificationTools
from .utils.date_parser import DateParser
from .utils.errors import MCPError


# Create FastMCP 2.0 application
mcp = FastMCP('trendradar-news')

# Global tool instance (initialized on first request)
_tools_instances = {}


def _get_tools(project_root: Optional[str] = None):
    """Get or create tool instance (singleton pattern)"""
    if not _tools_instances:
        _tools_instances['data'] = DataQueryTools(project_root)
        _tools_instances['analytics'] = AnalyticsTools(project_root)
        _tools_instances['search'] = SearchTools(project_root)
        _tools_instances['config'] = ConfigManagementTools(project_root)
        _tools_instances['system'] = SystemManagementTools(project_root)
        _tools_instances['storage'] = StorageSyncTools(project_root)
        _tools_instances['article'] = ArticleReaderTools(project_root)
        _tools_instances['notification'] = NotificationTools(project_root)
    return _tools_instances


# ==================== MCP Resources ====================

@mcp.resource("config://platforms")
async def get_platforms_resource() -> str:
    """
    Get supported platform list

    Return all platform information configured in config.yaml, including ID and name.
    """
    tools = _get_tools()
    config = await asyncio.to_thread(
        tools['config'].get_current_config, section="crawler"
    )
    return json.dumps({
        "platforms": config.get("platforms", []),
        "description": "List of trending platforms supported by TrendRadar"
    }, ensure_ascii=False, indent=2)


@mcp.resource("config://rss-feeds")
async def get_rss_feeds_resource() -> str:
    """
    Get RSS feed list

    Return all currently configured RSS feed information.
    """
    tools = _get_tools()
    status = await asyncio.to_thread(tools['data'].get_rss_feeds_status)
    return json.dumps({
        "feeds": status.get("today_feeds", {}),
        "description": "List of RSS feeds supported by TrendRadar"
    }, ensure_ascii=False, indent=2)


@mcp.resource("data://available-dates")
async def get_available_dates_resource() -> str:
    """
    Get available data date range

    Return the list of queryable dates in local storage.
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['storage'].list_available_dates, source="local"
    )
    return json.dumps({
        "dates": result.get("data", {}).get("local", {}).get("dates", []),
        "description": "List of queryable dates in local storage"
    }, ensure_ascii=False, indent=2)


@mcp.resource("config://keywords")
async def get_keywords_resource() -> str:
    """
    Get focus word configuration

    Return the focus word groups configured in frequency_words.txt.
    """
    tools = _get_tools()
    config = await asyncio.to_thread(
        tools['config'].get_current_config, section="keywords"
    )
    return json.dumps({
        "word_groups": config.get("word_groups", []),
        "total_groups": config.get("total_groups", 0),
        "description": "TrendRadar focus word configuration"
    }, ensure_ascii=False, indent=2)


# ==================== Date parsing tool (priority call) ====================

@mcp.tool
async def resolve_date_range(
    expression: str
) -> str:
    """
    [Recommended priority call] Parse natural language date expressions into standard date ranges

    **Why is this tool needed?**
    Users often use natural language to express dates such as "this week" and "last 7 days", but AI models calculating dates themselves
    may lead to inconsistent results. This tool uses precise current time calculations on the server side to ensure all
    AI models get a consistent date range.

    **Recommended usage flow:**
    1. User says "Analyze the sentiment of AI this week"
    2. AI calls resolve_date_range("this week") → gets precise date range
    3. AI calls analyze_sentiment(topic="ai", date_range=date_range returned in previous step)

    Args:
        expression: Natural language date expression, supports:
            - Single day: "today", "yesterday", "today", "yesterday"
            - Week: "this week", "last week", "this week", "last week"
            - Month: "this month", "last month", "this month", "last month"
            - Last N days: "last 7 days", "last 30 days", "last 7 days", "last 30 days"
            - Dynamic: "last 5 days", "last 10 days" (any number of days)

    Returns:
        Date range in JSON format, can be directly used for the date_range parameter of other tools:
        {
            "success": true,
            "expression": "this week",
            "date_range": {
                "start": "2025-11-18",
                "end": "2025-11-26"
            },
            "current_date": "2025-11-26",
            "description": "This week (Monday to Sunday, 11-18 to 11-26)"
        }

    Examples:
        User: "Analyze the sentiment of AI this week"
        AI call steps:
        1. resolve_date_range("this week")
           → {"date_range": {"start": "2025-11-18", "end": "2025-11-26"}, ...}
        2. analyze_sentiment(topic="ai", date_range={"start": "2025-11-18", "end": "2025-11-26"})

        User: "Look at Tesla news from the last 7 days"
        AI call steps:
        1. resolve_date_range("last 7 days")
           → {"date_range": {"start": "2025-11-20", "end": "2025-11-26"}, ...}
        2. search_news(query="Tesla", date_range={"start": "2025-11-20", "end": "2025-11-26"})
    """
    try:
        result = await asyncio.to_thread(DateParser.resolve_date_range_expression, expression)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except MCPError as e:
        return json.dumps({
            "success": False,
            "error": e.to_dict()
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }, ensure_ascii=False, indent=2)


# ==================== Data Query Tools ====================

@mcp.tool
async def get_latest_news(
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Get the latest batch of crawled news data to quickly understand current hot topics

    Args:
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo'], if not specified, all platforms are used
        limit: Return count limit, default 50, max 1000
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        JSON format news list

    **Data Display Suggestions**
    - Default to displaying all returned data unless the user explicitly requests a summary
    - Only filter when the user says "summarize" or "pick out the key points"
    - If the user asks "why is only a part displayed", it means complete data is needed
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['data'].get_latest_news,
        platforms=platforms, limit=limit, include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_trending_topics(
    top_n: int = 10,
    mode: str = 'current',
    extract_mode: str = 'keywords'
) -> str:
    """
    Get trending topic statistics

    Args:
        top_n: Return TOP N topics, default 10
        mode: Time mode
            - "daily": Cumulative data statistics for the current day
            - "current": Latest batch of data statistics (default)
        extract_mode: Extraction mode
            - "keywords": Count preset keywords (based on config/frequency_words.txt, default)
            - "auto_extract": Automatically extract high-frequency words from news titles (no preset required, automatically discover hot topics)

    Returns:
        JSON format topic frequency statistics list

    Examples:
        - Use preset keywords: get_trending_topics(mode="current")
        - Automatically extract hot topics: get_trending_topics(extract_mode="auto_extract", top_n=20)
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['data'].get_trending_topics,
        top_n=top_n, mode=mode, extract_mode=extract_mode
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== RSS Data Query Tools ====================

@mcp.tool
async def get_latest_rss(
    feeds: Optional[List[str]] = None,
    days: int = 1,
    limit: int = 50,
    include_summary: bool = False
) -> str:
    """
    Get the latest RSS feed data (supports multi-day queries)

    RSS data is stored separately from trending news and displayed in a time stream, suitable for getting the latest content from specific sources.

    Args:
        feeds: List of RSS feed IDs, e.g., ['hacker-news', '36kr'], if not specified, returns all feeds
        days: Get data from the last N days, default 1 (today only), max 30 days
        limit: Return count limit, default 50, max 500
        include_summary: Whether to include article summaries, default False (saves tokens)

    Returns:
        JSON format RSS entry list

    Examples:
        - get_latest_rss()
        - get_latest_rss(days=7, feeds=['hacker-news'])
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['data'].get_latest_rss,
        feeds=feeds, days=days, limit=limit, include_summary=include_summary
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def search_rss(
    keyword: str,
    feeds: Optional[List[str]] = None,
    days: int = 7,
    limit: int = 50,
    include_summary: bool = False
) -> str:
    """
    Search RSS data

    Search for articles containing specified keywords in RSS feed data.

    Args:
        keyword: Search keyword (required)
        feeds: List of RSS feed IDs, e.g., ['hacker-news', '36kr']
               - When not specified: search all RSS feeds
        days: Search data from the last N days, default 7 days, max 30 days
        limit: Return count limit, default 50
        include_summary: Whether to include article summary, default False

    Returns:
        JSON format list of matching RSS entries

    Examples:
        - search_rss(keyword="AI")
        - search_rss(keyword="machine learning", feeds=['hacker-news'], days=14)
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['data'].search_rss,
        keyword=keyword,
        feeds=feeds,
        days=days,
        limit=limit,
        include_summary=include_summary
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_rss_feeds_status() -> str:
    """
    Get RSS feed status information

    View currently configured RSS feeds and their data statistics.

    Returns:
        JSON format RSS feed status, including:
        - available_dates: List of dates with RSS data
        - total_dates: Total number of dates
        - today_feeds: Data statistics of each RSS feed today
            - {feed_id}: { name, item_count }
        - generated_at: Generation time

    Examples:
        - get_rss_feeds_status()  # View status of all RSS feeds
    """
    tools = _get_tools()
    result = await asyncio.to_thread(tools['data'].get_rss_feeds_status)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_news_by_date(
    date_range: Optional[Union[Dict[str, str], str]] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Get news data for a specified date, used for historical data analysis and comparison

    Args:
        date_range: Date range, supports multiple formats:
            - Range object: {"start": "2025-01-01", "end": "2025-01-07"}
            - Natural language: "today", "yesterday", "this week", "last 7 days"
            - Single day string: "2025-01-15"
            - Default value: "today"
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo'], if not specified, all platforms are used
        limit: Return count limit, default 50, max 1000
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        JSON format news list, including title, platform, ranking, etc.
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['data'].get_news_by_date,
        date_range=date_range,
        platforms=platforms,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)



# ==================== Advanced Data Analysis Tools ====================

@mcp.tool
async def analyze_topic_trend(
    topic: str,
    analysis_type: str = "trend",
    date_range: Optional[Union[Dict[str, str], str]] = None,
    granularity: str = "day",
    spike_threshold: float = 3.0,
    time_window: int = 24,
    lookahead_hours: int = 6,
    confidence_threshold: float = 0.7
) -> str:
    """
    Unified topic trend analysis tool - integrates multiple trend analysis modes

    Recommendation: When using natural language dates, call resolve_date_range first to get the exact date range.

    Args:
        topic: Topic keywords (required)
        analysis_type: Analysis type
            - "trend": Popularity trend analysis (default)
            - "lifecycle": Lifecycle analysis
            - "viral": Abnormal popularity detection
            - "predict": Topic prediction
        date_range: Date range, format {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}, default last 7 days
        granularity: Time granularity, default "day"
        spike_threshold: Popularity spike multiplier threshold (viral mode), default 3.0
        time_window: Detection time window in hours (viral mode), default 24
        lookahead_hours: Predict future hours (predict mode), default 6
        confidence_threshold: Confidence threshold (predict mode), default 0.7

    Returns:
        JSON format trend analysis results

    Examples:
        - analyze_topic_trend(topic="AI", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - analyze_topic_trend(topic="Tesla", analysis_type="lifecycle")
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['analytics'].analyze_topic_trend_unified,
        topic=topic,
        analysis_type=analysis_type,
        date_range=date_range,
        granularity=granularity,
        threshold=spike_threshold,
        time_window=time_window,
        lookahead_hours=lookahead_hours,
        confidence_threshold=confidence_threshold
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_data_insights(
    insight_type: str = "platform_compare",
    topic: Optional[str] = None,
    date_range: Optional[Union[Dict[str, str], str]] = None,
    min_frequency: int = 3,
    top_n: int = 20
) -> str:
    """
    Unified data insight analysis tool - integrates multiple data analysis modes

    Args:
        insight_type: Insight type, optional values:
            - "platform_compare": Platform comparison analysis (compare attention to topics across different platforms)
            - "platform_activity": Platform activity statistics (statistics on publishing frequency and active time of each platform)
            - "keyword_cooccur": Keyword co-occurrence analysis (analyze patterns of keywords appearing together)
        topic: Topic keyword (optional, applicable to platform_compare mode)
        date_range: **[Object Type]** Date range (optional)
                    - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Example**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Important**: Must be in object format, cannot pass integers
        min_frequency: Minimum co-occurrence frequency (keyword_cooccur mode), default 3
        top_n: Return TOP N results (keyword_cooccur mode), default 20

    Returns:
        Data insight analysis results in JSON format

    Examples:
        - analyze_data_insights(insight_type="platform_compare", topic="Artificial Intelligence")
        - analyze_data_insights(insight_type="platform_activity", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - analyze_data_insights(insight_type="keyword_cooccur", min_frequency=5, top_n=15)
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['analytics'].analyze_data_insights_unified,
        insight_type=insight_type,
        topic=topic,
        date_range=date_range,
        min_frequency=min_frequency,
        top_n=top_n
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_sentiment(
    topic: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    date_range: Optional[Union[Dict[str, str], str]] = None,
    limit: int = 50,
    sort_by_weight: bool = True,
    include_url: bool = False
) -> str:
    """
    Analyze sentiment tendency and popularity trend of news

    Suggestion: When using natural language dates, call resolve_date_range first to get the exact date range.

    Args:
        topic: Topic keyword (optional)
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo'], if not specified, all platforms are used
        date_range: Date range, format {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}, default today
        limit: Number of news to return, default 50, max 100 (titles will be deduplicated)
        sort_by_weight: Whether to sort by popularity weight, default True
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        Analysis results in JSON format, including sentiment distribution, popularity trends, and related news

    Examples:
        - analyze_sentiment(topic="AI", date_range={"start": "2025-01-01", "end": "2025-01-07"})
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['analytics'].analyze_sentiment,
        topic=topic,
        platforms=platforms,
        date_range=date_range,
        limit=limit,
        sort_by_weight=sort_by_weight,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def find_related_news(
    reference_title: str,
    date_range: Optional[Union[Dict[str, str], str]] = None,
    threshold: float = 0.5,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Find other news related to the specified news title (supports today's and historical data)

    Args:
        reference_title: Reference news title (full or partial)
        date_range: Date range (optional)
            - Not specified: Only query today's data
            - "today", "yesterday", "last_week", "last_month": Preset values
            - {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}: Custom range
        threshold: Similarity threshold, between 0-1, default 0.5 (higher means stricter matching)
        limit: Return count limit, default 50
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        List of related news in JSON format, sorted by similarity

    Examples:
        - find_related_news(reference_title="Tesla price cut")
        - find_related_news(reference_title="AI breakthrough", date_range="last_week")
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['search'].find_related_news_unified,
        reference_title=reference_title,
        date_range=date_range,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def generate_summary_report(
    report_type: str = "daily",
    date_range: Optional[Union[Dict[str, str], str]] = None
) -> str:
    """
    Daily/Weekly summary generator - Automatically generate hot topic summary reports

    Args:
        report_type: Report type (daily/weekly)
        date_range: **[Object Type]** Custom date range (optional)
                    - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Example**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Important**: Must be in object format, cannot pass integers

    Returns:
        Summary report in JSON format, containing Markdown formatted content
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['analytics'].generate_summary_report,
        report_type=report_type,
        date_range=date_range
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def aggregate_news(
    date_range: Optional[Union[Dict[str, str], str]] = None,
    platforms: Optional[List[str]] = None,
    similarity_threshold: float = 0.7,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Cross-platform news aggregation - Deduplicate and merge similar news

    Merge the same event reported by different platforms into a single aggregated news item, showing cross-platform coverage and comprehensive popularity.

    Args:
        date_range: Date range, queries today if not specified
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo'], uses all platforms if not specified
        similarity_threshold: Similarity threshold, 0.3-1.0, default 0.7 (higher is stricter)
        limit: Number of aggregated news to return, default 50
        include_url: Whether to include URL links, default False

    Returns:
        Aggregated results in JSON format, including deduplication statistics, aggregated news list, and platform coverage statistics

    Examples:
        - aggregate_news()
        - aggregate_news(similarity_threshold=0.8)
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['analytics'].aggregate_news,
        date_range=date_range,
        platforms=platforms,
        similarity_threshold=similarity_threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def compare_periods(
    period1: Union[Dict[str, str], str],
    period2: Union[Dict[str, str], str],
    topic: Optional[str] = None,
    compare_type: str = "overview",
    platforms: Optional[List[str]] = None,
    top_n: int = 10
) -> str:
    """
    Period comparison analysis - Compare news data between two time periods

    Compare dimensions such as hot topics, platform activity, and news volume across different periods.

    **Usage scenarios:**
    - Compare hot topic changes between this week and last week
    - Analyze the popularity difference of a topic between two periods
    - View periodic changes in platform activity

    Args:
        period1: First time period (baseline period)
            - {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}: Date range
            - "today", "yesterday", "this_week", "last_week", "this_month", "last_month": Preset values
        period2: Second time period (comparison period, format same as period1)
        topic: Optional topic keywords (focus on specific topic comparison)
        compare_type: Comparison type
            - "overview": General overview (default) - News volume, keyword changes, TOP news
            - "topic_shift": Topic shift analysis - Rising topics, declining topics, newly emerged topics
            - "platform_activity": Platform activity comparison - Changes in news volume across platforms
        platforms: Platform filter list, e.g., ['zhihu', 'weibo']
        top_n: Return TOP N results, default 10

    Returns:
        Comparison analysis results in JSON format, including:
        - periods: Date ranges of the two periods
        - compare_type: Comparison type
        - overview/topic_shift/platform_comparison: Specific comparison results (based on type)

    Examples:
        - compare_periods(period1="last_week", period2="this_week")  # Week-over-week comparison
        - compare_periods(period1="last_month", period2="this_month", compare_type="topic_shift")
        - compare_periods(
            period1={"start": "2025-01-01", "end": "2025-01-07"},
            period2={"start": "2025-01-08", "end": "2025-01-14"},
            topic="Artificial Intelligence"
          )
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['analytics'].compare_periods,
        period1=period1,
        period2=period2,
        topic=topic,
        compare_type=compare_type,
        platforms=platforms,
        top_n=top_n
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Intelligent Search Tools ====================

@mcp.tool
async def search_news(
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
) -> str:
    """
    Unified search interface, supports multiple search modes, can search hotlists and RSS simultaneously

    Suggestion: When using natural language dates, call resolve_date_range first to get the exact date range.

    Args:
        query: Search keywords or content snippets
        search_mode: Search mode
            - "keyword": Exact keyword match (default)
            - "fuzzy": Fuzzy content match
            - "entity": Entity name search (person/location/organization)
        date_range: Date range, format {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}, default today
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo'], uses all platforms if not specified
        limit: Hot list return count limit, default 50
        sort_by: Sort method - "relevance" (relevance) / "weight" (weight) / "date" (date)
        threshold: Similarity threshold (fuzzy mode only), 0-1, default 0.6
        include_url: Whether to include URL links, default False
        include_rss: Whether to search RSS data simultaneously, default False
        rss_limit: RSS return count limit, default 20

    Returns:
        Search results in JSON format, including hot news list and optional RSS results

    Examples:
        - search_news(query="AI")
        - search_news(query="AI", include_rss=True)
        - search_news(query="Tesla", date_range={"start": "2025-01-01", "end": "2025-01-07"})
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['search'].search_news_unified,
        query=query,
        search_mode=search_mode,
        date_range=date_range,
        platforms=platforms,
        limit=limit,
        sort_by=sort_by,
        threshold=threshold,
        include_url=include_url,
        include_rss=include_rss,
        rss_limit=rss_limit
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Configuration and System Management Tools ====================

@mcp.tool
async def get_current_config(
    section: str = "all"
) -> str:
    """
    Get current system configuration

    Args:
        section: Configuration section, optional values:
            - "all": All configurations (default)
            - "crawler": Crawler configuration
            - "push": Push configuration
            - "keywords": Keywords configuration
            - "weights": Weights configuration

    Returns:
        Configuration information in JSON format
    """
    tools = _get_tools()
    result = await asyncio.to_thread(tools['config'].get_current_config, section=section)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_system_status() -> str:
    """
    Get system running status and health check information

    Returns system version, data statistics, cache status, and other information

    Returns:
        System status information in JSON format
    """
    tools = _get_tools()
    result = await asyncio.to_thread(tools['system'].get_system_status)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def check_version(
    proxy_url: Optional[str] = None
) -> str:
    """
    Check for version updates (checks both TrendRadar and MCP Server)

    Compare local version with GitHub remote version to determine if an update is needed.

    Args:
        proxy_url: Optional proxy URL for accessing GitHub (e.g., http://127.0.0.1:7890)

    Returns:
        Version check results in JSON format, including version comparison of the two components and whether an update is needed

    Examples:
        - check_version()
        - check_version(proxy_url="http://127.0.0.1:7890")
    """
    tools = _get_tools()
    result = await asyncio.to_thread(tools['system'].check_version, proxy_url=proxy_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def trigger_crawl(
    platforms: Optional[List[str]] = None,
    save_to_local: bool = False,
    include_url: bool = False
) -> str:
    """
    Manually trigger a crawl task (optional persistence)

    Args:
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo'], if not specified, all platforms are used
        save_to_local: Whether to save to local output directory, default False
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        Task status information in JSON format, including success/failure platform list and news data

    Examples:
        - trigger_crawl(platforms=['zhihu'])
        - trigger_crawl(save_to_local=True)
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['system'].trigger_crawl,
        platforms=platforms, save_to_local=save_to_local, include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Storage Synchronization Tools ====================

@mcp.tool
async def sync_from_remote(
    days: int = 7
) -> str:
    """
    Pull data from remote storage to local

    Used for scenarios like MCP Server: crawler saves to remote cloud storage (e.g., Cloudflare R2),
    MCP Server pulls to local for analysis and query.

    Args:
        days: Pull data for the last N days, default 7 days
              - 0: Do not pull
              - 7: Pull data for the last week
              - 30: Pull data for the last month

    Returns:
        Synchronization results in JSON format, including:
        - success: Whether successful
        - synced_files: Number of successfully synchronized files
        - synced_dates: List of successfully synced dates
        - skipped_dates: Skipped dates (already exist locally)
        - failed_dates: Failed dates and error messages
        - message: Description of operation result

    Examples:
        - sync_from_remote()  # Pull the last 7 days
        - sync_from_remote(days=30)  # Pull the last 30 days

    Note:
        Need to configure remote storage (storage.remote) in config/config.yaml or set environment variables:
        - S3_ENDPOINT_URL: Service endpoint
        - S3_BUCKET_NAME: Bucket name
        - S3_ACCESS_KEY_ID: Access key ID
        - S3_SECRET_ACCESS_KEY: Secret access key
    """
    tools = _get_tools()
    result = await asyncio.to_thread(tools['storage'].sync_from_remote, days=days)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_storage_status() -> str:
    """
    Get storage configuration and status

    View current storage backend configuration, local and remote storage status information.

    Returns:
        Storage status information in JSON format, including local/remote storage status and pull configuration
    """
    tools = _get_tools()
    result = await asyncio.to_thread(tools['storage'].get_storage_status)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def list_available_dates(
    source: str = "both"
) -> str:
    """
    List available date ranges locally/remotely

    View which dates have data available in local and remote storage.

    Args:
        source: Data source
            - "local": Local only
            - "remote": Remote only
            - "both": List and compare both (default)

    Returns:
        List of dates in JSON format, including date information from each source and comparison results

    Examples:
        - list_available_dates()
        - list_available_dates(source="local")
    """
    tools = _get_tools()
    result = await asyncio.to_thread(tools['storage'].list_available_dates, source=source)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Article content reading tool ====================

@mcp.tool
async def read_article(
    url: str,
    timeout: int = 30
) -> str:
    """
    Read article content of the specified URL, return LLM-friendly Markdown format

    Convert web pages to clean Markdown via Jina AI Reader, automatically removing noise content such as ads and navigation bars.
    Suitable for: reading news body, getting article details, analyzing article content.

    **Typical usage flow:**
    1. First use search_news(include_url=True) to search for news and get links
    2. Then use read_article(url=link) to read the body content
    3. AI analyzes, summarizes, translates, etc. the Markdown body

    Args:
        url: Article link (required), starting with http:// or https://
        timeout: Request timeout (seconds), default 30, maximum 60

    Returns:
        Article content in JSON format, including the complete Markdown body

    Examples:
        - read_article(url="https://example.com/news/123")

    Note:
        - Use Jina AI Reader free service (100 RPM limit)
        - 5 seconds interval between each request (built-in rate control)
        - Some paywall/login wall pages may not be fully retrieved
    """
    tools = _get_tools()
    timeout = min(max(timeout, 10), 60)
    result = await asyncio.to_thread(
        tools['article'].read_article,
        url=url, timeout=timeout
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def read_articles_batch(
    urls: List[str],
    timeout: int = 30
) -> str:
    """
    Batch read multiple article contents (up to 5 articles, 5 seconds interval)

    Request article content one by one, automatically interval 5 seconds between each to comply with rate limits.

    **Typical usage flow:**
    1. First use search_news(include_url=True) to search for news and get multiple links
    2. Then use read_articles_batch(urls=[...]) to batch read the body
    3. AI comparative analysis and comprehensive reporting on multiple articles

    Args:
        urls: List of article links (required), process up to 5 articles
        timeout: Request timeout per article (seconds), default 30

    Returns:
        Batch read results in JSON format, including the full content and status of each article

    Examples:
        - read_articles_batch(urls=["https://a.com/1", "https://b.com/2"])

    Note:
        - Read up to 5 articles at a time, excess will be skipped
        - 5 articles take about 25-30 seconds (5 seconds interval per article)
        - Failure of a single article does not affect the reading of others
    """
    tools = _get_tools()
    timeout = min(max(timeout, 10), 60)
    result = await asyncio.to_thread(
        tools['article'].read_articles_batch,
        urls=urls, timeout=timeout
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Notification Push Tools ====================


@mcp.tool
async def get_channel_format_guide(channel: Optional[str] = None) -> str:
    """
    Get the formatting strategy guide for notification channels

    Returns the Markdown features, format limits, and best formatting prompts supported by each channel.
    Use this tool before calling send_notification to understand the formatting requirements of the target channel,
    thereby generating message content with the best layout effect.

    Overview of format differences across channels:
    - Feishu: Supports **bold**, <font color>colored text, [link](url), --- divider
    - DingTalk: Supports ### heading, **bold**, > quote, --- divider, does not support color
    - WeCom: Only supports **bold**, [link](url), > quote, does not support headings and dividers
    - Telegram: Automatically converted to HTML, supports bold/italic/strikethrough/code/link/block quote
    - ntfy: Supports standard Markdown, does not support color
    - Bark: iOS push, only supports bold and links, content needs to be concise
    - Slack: Automatically converted to mrkdwn, *bold*, ~strikethrough~, <url|link>
    - Email: Automatically converted to full HTML webpage, supports headings/styles/dividers
    - Generic Webhook: Standard Markdown or custom template

    Args:
        channel: Specify channel ID (optional), returns all channel strategies if not specified
                 Optional values: feishu, dingtalk, wework, telegram, email, ntfy, bark, slack, generic_webhook

    Returns:
        Channel formatting strategy in JSON format, including supported features, limitations, and formatting prompts

    Examples:
        - get_channel_format_guide()  # Get all channel strategies
        - get_channel_format_guide(channel="feishu")  # Get Feishu strategy
        - get_channel_format_guide(channel="telegram")  # Get Telegram strategy
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['notification'].get_channel_format_guide,
        channel=channel
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_notification_channels() -> str:
    """
    Get all configured notification channels and their status

    Detect notification channel configurations in config.yaml and .env environment variables.
    Supports 9 channels: Feishu, DingTalk, WeCom, Telegram, Email, ntfy, Bark, Slack, Generic Webhook.

    Returns:
        Channel status in JSON format, including whether each channel is configured and the configuration source

    Examples:
        - get_notification_channels()
    """
    tools = _get_tools()
    result = await asyncio.to_thread(tools['notification'].get_notification_channels)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def send_notification(
    message: str,
    title: str = "TrendRadar Notification",
    channels: Optional[List[str]] = None,
) -> str:
    """
    Send messages to configured notification channels

    Accepts markdown format content, internally automatically adapts to the format requirements and limitations of each channel:
    - Feishu: Markdown card message (supports **bold**, <font color>colored text, [link](url), ---)
    - DingTalk: Markdown (automatically downgrades headings to ###, strips <font> tags and strikethrough)
    - WeCom: Markdown (automatically strips # headings, ---, <font> tags, strikethrough)
    - Telegram: HTML (automatically converts **→<b>, *→<i>, ~~→<s>, >→<blockquote>)
    - Email: HTML email (full webpage style, supports # headings, ---, bold italic)
    - ntfy: Markdown (automatically strips <font> tags)
    - Bark: Markdown (automatically simplified to bold+links, adapted for iOS push)
    - Slack: mrkdwn (automatically converts **→*, ~~→~, [text](url)→<url|text>)
    - Generic Webhook: Markdown (supports custom templates)

    Tip: Before sending, you can call get_channel_format_guide to get the detailed formatting strategy of the target channel,
    to generate message content with the best layout effect.

    Args:
        message: message content in markdown format (required)
        title: message title, default "TrendRadar Notification"
        channels: specify the list of channels to send to, if not specified, it will be sent to all configured channels
                  Optional values: feishu, dingtalk, wework, telegram, email, ntfy, bark, slack, generic_webhook

    Returns:
        Sending results in JSON format, including the sending status of each channel

    Examples:
        - send_notification(message="**Test message**\nThis is a test notification")
        - send_notification(message="Emergency notification", title="System alert", channels=["feishu", "dingtalk"])
    """
    tools = _get_tools()
    result = await asyncio.to_thread(
        tools['notification'].send_notification,
        message=message, title=title, channels=channels
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Startup Entry ====================

def run_server(
    project_root: Optional[str] = None,
    transport: str = 'stdio',
    host: str = '0.0.0.0',
    port: int = 3333
):
    """
    Start the MCP server

    Args:
        project_root: project root directory path
        transport: transport mode, 'stdio' or 'http'
        host: listening address for HTTP mode, default 0.0.0.0
        port: listening port for HTTP mode, default 3333
    """
    # Initialize tool instances
    _get_tools(project_root)

    # Print startup information
    print()
    print("=" * 60)
    print("  TrendRadar MCP Server - FastMCP 2.0")
    print("=" * 60)
    print(f"  Transport mode: {transport.upper()}")

    if transport == 'stdio':
        print("  Protocol: MCP over stdio (standard input/output)")
        print("  Description: Communicate with MCP client via standard input/output")
    elif transport == 'http':
        print(f"  Protocol: MCP over HTTP (production environment)")
        print(f"  Server listening: {host}:{port}")

    if project_root:
        print(f"  Project directory: {project_root}")
    else:
        print("  Project directory: Current directory")

    print()
    print("  Registered tools:")
    print("    === Date parsing tools (recommended to call first) ===")
    print("    0. resolve_date_range       - Parse natural language dates into standard format")
    print()
    print("    === Basic data query (P0 core) ===")
    print("    1. get_latest_news        - Get latest news")
    print("    2. get_news_by_date       - Query news by date (supports natural language)")
    print("    3. get_trending_topics    - Get trending topics (supports automatic extraction)")
    print()
    print("    === RSS data query ===")
    print("    4. get_latest_rss         - Get latest RSS subscription data")
    print("    5. search_rss             - Search RSS data")
    print("    6. get_rss_feeds_status   - Get RSS feed status")
    print()
    print("    === Intelligent retrieval tools ===")
    print("    7. search_news            - Unified news search (keyword/fuzzy/entity)")
    print("    8. find_related_news      - Find related news (supports historical data)")
    print()
    print("    === Advanced Data Analysis ===")
    print("    9. analyze_topic_trend      - Unified topic trend analysis (popularity/lifecycle/viral/prediction)")
    print("    10. analyze_data_insights   - Unified data insights analysis (platform comparison/activity/keyword co-occurrence)")
    print("    11. analyze_sentiment       - Sentiment analysis")
    print("    12. aggregate_news          - Cross-platform news aggregation and deduplication")
    print("    13. compare_periods         - Period comparison analysis (week-over-week/month-over-month)")
    print("    14. generate_summary_report - Daily/weekly summary generation")
    print()
    print("    === Configuration and System Management ===")
    print("    15. get_current_config      - Get current system configuration")
    print("    16. get_system_status       - Get system running status")
    print("    17. check_version           - Check version update (compare local and remote versions)")
    print("    18. trigger_crawl           - Manually trigger crawl task")
    print()
    print("    === Storage Synchronization Tools ===")
    print("    19. sync_from_remote        - Pull data from remote storage to local")
    print("    20. get_storage_status      - Get storage configuration and status")
    print("    21. list_available_dates    - List available local/remote dates")
    print()
    print("    === Article Content Reading ===")
    print("    22. read_article            - Read single article content (Markdown format)")
    print("    23. read_articles_batch     - Batch read multiple articles (automatic rate limiting)")
    print()
    print("    === Notification Push Tools ===")
    print("    24. get_channel_format_guide  - Get channel formatting strategy guide (prompts)")
    print("    25. get_notification_channels - Get configured notification channel status")
    print("    26. send_notification         - Send message to notification channel (auto-adapt format)")
    print("=" * 60)
    print()

    # Run server based on transport mode
    if transport == 'stdio':
        mcp.run(transport='stdio')
    elif transport == 'http':
        # HTTP mode (recommended for production)
        mcp.run(
            transport='http',
            host=host,
            port=port,
            path='/mcp'  # HTTP endpoint path
        )
    else:
        raise ValueError(f"Unsupported transport mode: {transport}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='TrendRadar MCP Server - News hotspot aggregation MCP tool server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
For detailed configuration tutorial, please check: README-Cherry-Studio.md
        """
    )
    parser.add_argument(
        '--transport',
        choices=['stdio', 'http'],
        default='stdio',
        help='Transport mode: stdio (default) or http (production environment)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Listen address for HTTP mode, default 0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3333,
        help='Listen port for HTTP mode, default 3333'
    )
    parser.add_argument(
        '--project-root',
        help='Project root directory path'
    )

    args = parser.parse_args()

    run_server(
        project_root=args.project_root,
        transport=args.transport,
        host=args.host,
        port=args.port
    )
