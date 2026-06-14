"""
Parameter validation tool

Provide unified parameter validation functionality.
Support cases where the MCP client serializes parameters into strings.
"""

from datetime import datetime
from typing import List, Optional, Union
import os
import json
import yaml
import ast

from .errors import InvalidParameterError
from .date_parser import DateParser


# ==================== Helper functions: Handle string serialization ====================

def _parse_string_to_list(value: str) -> List[str]:
    """
    Parse string to list

    Supported formats:
    - JSON array: '["zhihu", "weibo"]'
    - Python list string: "['zhihu', 'weibo']"
    - Comma-separated: "zhihu, weibo" or "zhihu,weibo"

    Args:
        value: String value

    Returns:
        Parsed list

    Raises:
        InvalidParameterError: Parsing failed
    """
    value = value.strip()

    if not value:
        return []

    # Try JSON parsing: '["zhihu", "weibo"]'
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        # If the parsing result is not a list, continue trying other methods
    except json.JSONDecodeError:
        pass

    # Try Python literal parsing: "['zhihu', 'weibo']"
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        if isinstance(parsed, str):
            # Single string, wrap into a list
            return [parsed]
    except (ValueError, SyntaxError):
        pass

    # Try comma-separated: "zhihu, weibo" or "zhihu,weibo"
    if ',' in value:
        items = [item.strip() for item in value.split(',')]
        return [item for item in items if item]

    # Single value
    return [value]


def _parse_string_to_int(value: str, param_name: str = "parameter") -> int:
    """
    Parse string to integer

    Args:
        value: String value
        param_name: Parameter name (used for error messages)

    Returns:
        Parsed integer

    Raises:
        InvalidParameterError: Parsing failed
    """
    value = value.strip()

    try:
        # Try direct conversion
        return int(value)
    except ValueError:
        pass

    # Try parsing as float then convert to integer
    try:
        return int(float(value))
    except ValueError:
        raise InvalidParameterError(
            f"{param_name} must be an integer, cannot parse: {value}",
            suggestion=f"Please provide a valid integer value, such as: 10, 50, 100"
        )


def _parse_string_to_float(value: str, param_name: str = "parameter") -> float:
    """
    Parse string to float

    Args:
        value: String value
        param_name: Parameter name (used for error messages)

    Returns:
        Parsed float

    Raises:
        InvalidParameterError: Parsing failed
    """
    value = value.strip()

    try:
        return float(value)
    except ValueError:
        raise InvalidParameterError(
            f"{param_name} must be a number, cannot parse: {value}",
            suggestion=f"Please provide a valid number value, such as: 0.6, 3.0"
        )


def _parse_string_to_bool(value: str) -> bool:
    """
    Parse string to boolean

    Args:
        value: String value

    Returns:
        Parsed boolean
    """
    value = value.strip().lower()

    if value in ('true', '1', 'yes', 'on'):
        return True
    elif value in ('false', '0', 'no', 'off', ''):
        return False
    else:
        # Default non-empty string to True
        return bool(value)


# Platform list mtime cache (avoids re-reading config.yaml on every MCP call)
_platforms_cache: Optional[List[str]] = None
_platforms_config_mtime: float = 0.0
_platforms_config_path: Optional[str] = None


def get_supported_platforms() -> List[str]:
    """
    Dynamically get the list of supported platforms from config.yaml (with mtime cache)

    Only re-read when config.yaml is modified, avoiding repeated IO on every MCP call.

    Returns:
        List of platform IDs

    Note:
        - Returns an empty list on read failure, allowing all platforms to pass (fallback strategy)
        - Platform list comes from the platforms configuration in config/config.yaml
    """
    global _platforms_cache, _platforms_config_mtime, _platforms_config_path

    try:
        if _platforms_config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            _platforms_config_path = os.path.normpath(
                os.path.join(current_dir, "..", "..", "config", "config.yaml")
            )

        current_mtime = os.path.getmtime(_platforms_config_path)

        if _platforms_cache is not None and current_mtime == _platforms_config_mtime:
            return _platforms_cache

        with open(_platforms_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            platforms_config = config.get('platforms', {})
            sources = platforms_config.get('sources', [])
            _platforms_cache = [p['id'] for p in sources if 'id' in p and p.get('enabled', True)]
            _platforms_config_mtime = current_mtime
            return _platforms_cache
    except Exception as e:
        print(f"Warning: Unable to load platform configuration: {e}")
        return []


def validate_platforms(platforms: Optional[Union[List[str], str]]) -> List[str]:
    """
    Validate platform list

    Args:
        platforms: List of platform IDs or string, None means using all platforms configured in config.yaml
                   Supports multiple formats:
                   - None: Use default platforms
                   - ["zhihu", "weibo"]: JSON array
                   - '["zhihu", "weibo"]': JSON array string
                   - "['zhihu', 'weibo']": Python list string
                   - "zhihu, weibo": Comma-separated string
                   - "zhihu": Single platform string

    Returns:
        Validated platform list

    Raises:
        InvalidParameterError: Platform not supported

    Note:
        - When platforms=None, returns the platform list configured in config.yaml
        - Validates whether the platform ID is in the platforms configuration of config.yaml
        - When configuration loading fails, allows all platforms to pass (fallback strategy)
    """
    supported_platforms = get_supported_platforms()

    if platforms is None:
        # Return the platform list from the configuration file (user's default configuration)
        return supported_platforms if supported_platforms else []

    # Support list input in string format (some MCP clients serialize JSON arrays as strings)
    if isinstance(platforms, str):
        platforms = _parse_string_to_list(platforms)
        if not platforms:
            # Empty string or empty after parsing, use default platforms
            return supported_platforms if supported_platforms else []

    if not isinstance(platforms, list):
        raise InvalidParameterError("platforms parameter must be a list type")

    if not platforms:
        # When the list is empty, return the platform list from the configuration file
        return supported_platforms if supported_platforms else []

    # If configuration loading fails (supported_platforms is empty), allow all platforms to pass
    if not supported_platforms:
        print("Warning: Platform configuration not loaded, skipping platform validation")
        return platforms

    # Validate whether each platform is in the configuration
    invalid_platforms = [p for p in platforms if p not in supported_platforms]
    if invalid_platforms:
        raise InvalidParameterError(
            f"Unsupported platforms: {', '.join(invalid_platforms)}",
            suggestion=f"Supported platforms (from config.yaml): {', '.join(supported_platforms)}"
        )

    return platforms


def validate_limit(limit: Optional[Union[int, str]], default: int = 20, max_limit: int = 1000) -> int:
    """
    Validate quantity limit parameter

    Args:
        limit: Limit quantity (integer or string)
        default: Default value
        max_limit: Maximum limit

    Returns:
        Validated limit value

    Raises:
        InvalidParameterError: Invalid parameter
    """
    if limit is None:
        return default

    # Support integer in string format (some MCP clients serialize numbers as strings)
    if isinstance(limit, str):
        limit = _parse_string_to_int(limit, "limit")

    if not isinstance(limit, int):
        raise InvalidParameterError("limit parameter must be an integer type")

    if limit <= 0:
        raise InvalidParameterError("limit must be greater than 0")

    if limit > max_limit:
        raise InvalidParameterError(
            f"limit cannot exceed {max_limit}",
            suggestion=f"Please use pagination or lower the limit value"
        )

    return limit


def validate_date(date_str: str) -> datetime:
    """
    Validate date format

    Args:
        date_str: Date string (YYYY-MM-DD)

    Returns:
        datetime object

    Raises:
        InvalidParameterError: Date format error
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise InvalidParameterError(
            f"Date format error: {date_str}",
            suggestion="Please use YYYY-MM-DD format, for example: 2025-10-11"
        )


def normalize_date_range(date_range: Optional[Union[dict, str]]) -> Optional[Union[dict, str]]:
    """
    Normalize date_range parameter

    Some MCP clients (especially HTTP) will serialize JSON objects into strings and pass them in.
    This function attempts to parse a JSON string into a dict, and keeps it as is if it's not in JSON format.

    Args:
        date_range: Date range, could be:
            - dict: {"start": "2025-01-01", "end": "2025-01-07"}
            - JSON string: '{"start": "2025-01-01", "end": "2025-01-07"}'
            - Normal string: "Today", "Yesterday", "2025-01-01"
            - None

    Returns:
        Normalized date_range (dict or normal string)

    Examples:
        >>> normalize_date_range('{"start":"2025-01-01","end":"2025-01-07"}')
        {"start": "2025-01-01", "end": "2025-01-07"}
        >>> normalize_date_range("Today")
        "Today"
        >>> normalize_date_range({"start": "2025-01-01", "end": "2025-01-07"})
        {"start": "2025-01-01", "end": "2025-01-07"}
    """
    if date_range is None:
        return None

    # If it is already a dict, return directly
    if isinstance(date_range, dict):
        return date_range

    # If it is a string, attempt to parse as JSON
    if isinstance(date_range, str):
        # Check if it looks like a JSON object
        stripped = date_range.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass  # Parsing failed, treat as normal string

    return date_range


def validate_date_range(date_range: Optional[Union[dict, str]]) -> Optional[tuple]:
    """
    Validate date range

    Args:
        date_range: Date range, supports multiple formats:
            - dict: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            - JSON string: '{"start": "2025-01-01", "end": "2025-01-07"}'
            - Single day string: "2025-01-01" (automatically converted to a range of the same day)
            - Natural language: "Today", "Yesterday", "This week", "Last 7 days", etc.

    Returns:
        (start_date, end_date) tuple, or None

    Raises:
        InvalidParameterError: Invalid date range
    """
    if date_range is None:
        return None

    # Support string format input
    if isinstance(date_range, str):
        stripped = date_range.strip()

        # 1. Check if it is JSON object format
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                date_range = json.loads(stripped)
            except json.JSONDecodeError as e:
                raise InvalidParameterError(
                    f"date_range JSON parsing failed: {e}",
                    suggestion='Please use correct JSON format: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}'
                )
        # 2. Check if it is single day string format YYYY-MM-DD
        elif len(stripped) == 10 and stripped[4] == '-' and stripped[7] == '-':
            try:
                single_date = datetime.strptime(stripped, "%Y-%m-%d")
                return (single_date, single_date)
            except ValueError:
                raise InvalidParameterError(
                    f"Date format error: {stripped}",
                    suggestion="Please use YYYY-MM-DD format, for example: 2025-10-11"
                )
        # 3. Attempt natural language parsing
        else:
            try:
                result = DateParser.resolve_date_range_expression(stripped)
                if result.get("success"):
                    dr = result["date_range"]
                    start_date = datetime.strptime(dr["start"], "%Y-%m-%d")
                    end_date = datetime.strptime(dr["end"], "%Y-%m-%d")
                    return (start_date, end_date)
                else:
                    raise InvalidParameterError(
                        f"Unrecognized date expression: {stripped}",
                        suggestion="Supported formats: YYYY-MM-DD, {\"start\": \"...\", \"end\": \"...\"}, or natural language (Today, This week, Last 7 days, etc.)"
                    )
            except InvalidParameterError:
                raise
            except Exception:
                raise InvalidParameterError(
                    f"Date parsing failed: {stripped}",
                    suggestion="Supported formats: YYYY-MM-DD, {\"start\": \"...\", \"end\": \"...\"}, or natural language (Today, This week, Last 7 days, etc.)"
                )

    if not isinstance(date_range, dict):
        raise InvalidParameterError(
            "date_range must be a dictionary type, date string, or valid JSON string",
            suggestion='For example: {"start": "2025-10-01", "end": "2025-10-11"} or "2025-10-01"'
        )

    start_str = date_range.get("start")
    end_str = date_range.get("end")

    if not start_str or not end_str:
        raise InvalidParameterError(
            "date_range must contain start and end fields",
            suggestion='For example: {"start": "2025-10-01", "end": "2025-10-11"}'
        )

    start_date = validate_date(start_str)
    end_date = validate_date(end_str)

    if start_date > end_date:
        raise InvalidParameterError(
            "Start date cannot be later than end date",
            suggestion=f"start: {start_str}, end: {end_str}"
        )

    # Check if the date is in the future
    today = datetime.now().date()
    if start_date.date() > today or end_date.date() > today:
        # Get available date range prompt
        try:
            from ..services.data_service import DataService
            data_service = DataService()
            earliest, latest = data_service.get_available_date_range()

            if earliest and latest:
                available_range = f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"
            else:
                available_range = "No available data"
        except Exception:
            available_range = "Unknown (please check the output directory)"

        future_dates = []
        if start_date.date() > today:
            future_dates.append(start_str)
        if end_date.date() > today and end_str != start_str:
            future_dates.append(end_str)

        raise InvalidParameterError(
            f"Querying future dates is not allowed: {', '.join(future_dates)} (Current date: {today.strftime('%Y-%m-%d')})",
            suggestion=f"Currently available data range: {available_range}"
        )

    return (start_date, end_date)


def validate_keyword(keyword: str) -> str:
    """
    Validate keyword

    Args:
        keyword: Search keyword

    Returns:
        Processed keyword

    Raises:
        InvalidParameterError: Invalid keyword
    """
    if not keyword:
        raise InvalidParameterError("keyword cannot be empty")

    if not isinstance(keyword, str):
        raise InvalidParameterError("keyword must be a string type")

    keyword = keyword.strip()

    if not keyword:
        raise InvalidParameterError("keyword cannot be whitespace")

    if len(keyword) > 100:
        raise InvalidParameterError(
            "keyword length cannot exceed 100 characters",
            suggestion="Please use a more concise keyword"
        )

    return keyword


def validate_top_n(top_n: Optional[Union[int, str]], default: int = 10) -> int:
    """
    Validate TOP N parameter

    Args:
        top_n: TOP N quantity (integer or string)
        default: Default value

    Returns:
        Validated value

    Raises:
        InvalidParameterError: Invalid parameter
    """
    return validate_limit(top_n, default=default, max_limit=100)


def validate_mode(mode: Optional[str], valid_modes: List[str], default: str) -> str:
    """
    Validate mode parameter

    Args:
        mode: Mode string
        valid_modes: List of valid modes
        default: Default mode

    Returns:
        Validated mode

    Raises:
        InvalidParameterError: Invalid mode
    """
    if mode is None:
        return default

    if not isinstance(mode, str):
        raise InvalidParameterError("mode must be a string type")

    if mode not in valid_modes:
        raise InvalidParameterError(
            f"Invalid mode: {mode}",
            suggestion=f"Supported modes: {', '.join(valid_modes)}"
        )

    return mode


def validate_config_section(section: Optional[str]) -> str:
    """
    Validate configuration section parameter

    Args:
        section: Configuration section name

    Returns:
        Validated configuration section

    Raises:
        InvalidParameterError: Invalid configuration section
    """
    valid_sections = ["all", "crawler", "push", "keywords", "weights"]
    return validate_mode(section, valid_sections, "all")


def validate_threshold(
    threshold: Optional[Union[float, int, str]],
    default: float = 0.6,
    min_value: float = 0.0,
    max_value: float = 1.0,
    param_name: str = "threshold"
) -> float:
    """
    Validate threshold parameter (float)

    Args:
        threshold: Threshold (float, integer, or string)
        default: Default value
        min_value: Minimum value
        max_value: Maximum value
        param_name: Parameter name (used for error messages)

    Returns:
        Validated threshold

    Raises:
        InvalidParameterError: Invalid parameter
    """
    if threshold is None:
        return default

    # Support numbers in string format (some MCP clients serialize numbers as strings)
    if isinstance(threshold, str):
        threshold = _parse_string_to_float(threshold, param_name)

    # Convert integer to float
    if isinstance(threshold, int):
        threshold = float(threshold)

    if not isinstance(threshold, float):
        raise InvalidParameterError(
            f"{param_name} must be a numeric type",
            suggestion=f"Please provide a number between {min_value} and {max_value}"
        )

    if threshold < min_value or threshold > max_value:
        raise InvalidParameterError(
            f"{param_name} must be between {min_value} and {max_value}, current value: {threshold}",
            suggestion=f"Recommended value: {default}"
        )

    return threshold


def validate_date_query(
    date_query: str,
    allow_future: bool = False,
    max_days_ago: int = 365
) -> datetime:
    """
    Validate and parse date query string

    Args:
        date_query: Date query string
        allow_future: Whether to allow future dates
        max_days_ago: Maximum number of days allowed for query

    Returns:
        Parsed datetime object

    Raises:
        InvalidParameterError: Invalid date query

    Examples:
        >>> validate_date_query("yesterday")
        datetime(2025, 10, 10)
        >>> validate_date_query("2025-10-10")
        datetime(2025, 10, 10)
    """
    if not date_query:
        raise InvalidParameterError(
            "Date query string cannot be empty",
            suggestion="Please provide a date query, e.g.: today, yesterday, 2025-10-10"
        )

    # Use DateParser to parse the date
    parsed_date = DateParser.parse_date_query(date_query)

    # Validate that the date is not in the future
    if not allow_future:
        DateParser.validate_date_not_future(parsed_date)

    # Validate that the date is not too far in the past
    DateParser.validate_date_not_too_old(parsed_date, max_days=max_days_ago)

    return parsed_date

