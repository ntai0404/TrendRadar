# coding=utf-8
"""
URL processing tool module

Provides URL standardization function to eliminate the impact of dynamic parameters when deduplicating:
- normalize_url: normalize URL, remove dynamic parameters
"""

from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import Dict, Set


# Specific parameters that need to be removed on each platform
# - weibo: There are band_rank (ranking) and Refer (source) dynamic parameters
# - Other platforms: URL is in path format or simple keyword query, no processing required
PLATFORM_PARAMS_TO_REMOVE: Dict[str, Set[str]] = {
    # Weibo: band_rank is a dynamic ranking parameter, Refer is a source parameter, and t is a time range parameter.
    # Example: https://s.weibo.com/weibo?q=xxx&t=31&band_rank=1&Refer=top
    # Reserved: q (keyword)
    # Remove: band_rank, Refer, t
    "weibo": {"band_rank", "Refer", "t"},
}

# Universal tracking parameters (applicable to all platforms)
# These parameters are usually added by shared links or ad tracking and do not affect content identification.
COMMON_TRACKING_PARAMS: Set[str] = {
    # UTM tracking parameters
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    # Common tracking parameters
    "ref", "referrer", "source", "channel",
    # Timestamp and random parameters
    "_t", "timestamp", "_", "random",
    # Share related
    "share_token", "share_id", "share_from",
}


def normalize_url(url: str, platform_id: str = "") -> str:
    """
    Standardize URLs, remove dynamic parameters

    Used for database deduplication to ensure that different URL variations of the same news can be correctly identified as the same one.

    Processing rules:
    1. Remove platform-specific dynamic parameters (such as Weibo’s band_rank)
    2. Remove common tracking parameters (such as utm_*)
    3. Keep core query parameters (such as search keywords q=, wd=, keyword=)
    4. Sort query parameters alphabetically (to ensure consistency)

    Args:
        url: original URL
        platform_id: Platform ID, used to apply platform specific rules

    Returns:
        Normalized URL

    Examples:
        >>> normalize_url("https://s.weibo.com/weibo?q=test&band_rank=6&Refer=top", "weibo")
        'https://s.weibo.com/weibo?q=test'

        >>> normalize_url("https://example.com/page?id=1&utm_source=twitter", "")
        'https://example.com/page?id=1'
    """
    if not url:
        return url

    try:
        # Parse URL
        parsed = urlparse(url)

        # If there are no query parameters, return directly
        if not parsed.query:
            return url

        # Parse query parameters
        params = parse_qs(parsed.query, keep_blank_values=True)

        # Collect parameters that need to be removed (use lowercase for comparison)
        params_to_remove: Set[str] = set()

        # Add common tracking parameters
        params_to_remove.update(COMMON_TRACKING_PARAMS)

        # Add platform specific parameters
        if platform_id and platform_id in PLATFORM_PARAMS_TO_REMOVE:
            params_to_remove.update(PLATFORM_PARAMS_TO_REMOVE[platform_id])

        # Filter parameters (convert parameter names to lowercase for comparison)
        filtered_params = {
            key: values
            for key, values in params.items()
            if key.lower() not in {p.lower() for p in params_to_remove}
        }

        # If there are no parameters after filtering, return the URL without query string
        if not filtered_params:
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                "", # Empty query string
                "" # Remove fragment
            ))

        # Rebuild query string (sorted alphabetically to ensure consistency)
        sorted_params = []
        for key in sorted(filtered_params.keys()):
            for value in filtered_params[key]:
                sorted_params.append((key, value))

        new_query = urlencode(sorted_params)

        # Rebuild URL (remove fragment)
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            "" # Remove fragment
        ))

        return normalized

    except Exception:
        # Return the original URL when parsing fails
        return url
