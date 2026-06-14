"""
Date parsing tool

Supports parsing multiple natural language date formats, including relative and absolute dates.
"""

import re
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional

from .errors import InvalidParameterError


class DateParser:
    """Date parser class"""

    # Chinese date mapping
    CN_DATE_MAPPING = {
        "Today": 0,
        "Yesterday": 1,
        "Day before yesterday": 2,
        "Three days ago": 3,
    }

    # English date mapping
    EN_DATE_MAPPING = {
        "today": 0,
        "yesterday": 1,
    }

    # Date range expressions (used for resolve_date_range_expression)
    RANGE_EXPRESSIONS = {
        # Chinese expressions
        "Today": "today",
        "Yesterday": "yesterday",
        "This week": "this_week",
        "The week": "this_week",
        "Current week": "this_week",
        "Last week": "last_week",
        "This month": "this_month",
        "The month": "this_month",
        "Current month": "this_month",
        "Last month": "last_month",
        "Previous month": "last_month",
        "Last 3 days": "last_3_days",
        "Recent 3 days": "last_3_days",
        "Last 7 days": "last_7_days",
        "Recent 7 days": "last_7_days",
        "Last one week": "last_7_days",
        "Past one week": "last_7_days",
        "Last 14 days": "last_14_days",
        "Recent 14 days": "last_14_days",
        "Last two weeks": "last_14_days",
        "Past two weeks": "last_14_days",
        "Last 30 days": "last_30_days",
        "Recent 30 days": "last_30_days",
        "Last one month": "last_30_days",
        "Past one month": "last_30_days",
        # English expressions
        "today": "today",
        "yesterday": "yesterday",
        "this week": "this_week",
        "current week": "this_week",
        "last week": "last_week",
        "this month": "this_month",
        "current month": "this_month",
        "last month": "last_month",
        "last 3 days": "last_3_days",
        "past 3 days": "last_3_days",
        "last 7 days": "last_7_days",
        "past 7 days": "last_7_days",
        "past week": "last_7_days",
        "last 14 days": "last_14_days",
        "past 14 days": "last_14_days",
        "last 30 days": "last_30_days",
        "past 30 days": "last_30_days",
        "past month": "last_30_days",
    }

    # Weekday mapping
    WEEKDAY_CN = {
        "One": 0, "Two": 1, "Three": 2, "Four": 3,
        "Five": 4, "Six": 5, "Sun": 6, "Day": 6
    }

    WEEKDAY_EN = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    @staticmethod
    def parse_date_query(date_query: str) -> datetime:
        """
        Parse date query string

        Supported formats:
        - Relative dates (Chinese): today, yesterday, the day before yesterday, three days ago, N days ago
        - Relative dates (English): today, yesterday, N days ago
        - Weekdays (Chinese): last Monday, last Tuesday, this Wednesday
        - Weekdays (English): last monday, this friday
        - Absolute dates: 2025-10-10, 10 month 10 day, 2025 year 10 month 10 day

        Args:
            date_query: Date query string

        Returns:
            datetime object

        Raises:
            InvalidParameterError: Unrecognized date format

        Examples:
            >>> DateParser.parse_date_query("today")
            datetime(2025, 10, 11)
            >>> DateParser.parse_date_query("yesterday")
            datetime(2025, 10, 10)
            >>> DateParser.parse_date_query("3 days ago")
            datetime(2025, 10, 8)
            >>> DateParser.parse_date_query("2025-10-10")
            datetime(2025, 10, 10)
        """
        if not date_query or not isinstance(date_query, str):
            raise InvalidParameterError(
                "Date query string cannot be empty",
                suggestion="Please provide a valid date query, e.g., today, yesterday, 2025-10-10"
            )

        date_query = date_query.strip().lower()

        # 1. Try to parse common Chinese relative dates
        if date_query in DateParser.CN_DATE_MAPPING:
            days_ago = DateParser.CN_DATE_MAPPING[date_query]
            return datetime.now() - timedelta(days=days_ago)

        # 2. Try to parse common English relative dates
        if date_query in DateParser.EN_DATE_MAPPING:
            days_ago = DateParser.EN_DATE_MAPPING[date_query]
            return datetime.now() - timedelta(days=days_ago)

        # 3. Try to parse "N days ago" or "N days ago"
        cn_days_ago_match = re.match(r'(\d+)\s*days ago', date_query)
        if cn_days_ago_match:
            days = int(cn_days_ago_match.group(1))
            if days > 365:
                raise InvalidParameterError(
                    f"Number of days too large: {days} days",
                    suggestion="Please use a relative date less than 365 days or use an absolute date"
                )
            return datetime.now() - timedelta(days=days)

        en_days_ago_match = re.match(r'(\d+)\s*days?\s+ago', date_query)
        if en_days_ago_match:
            days = int(en_days_ago_match.group(1))
            if days > 365:
                raise InvalidParameterError(
                    f"Number of days too large: {days} days",
                    suggestion="Please use a relative date less than 365 days or use an absolute date"
                )
            return datetime.now() - timedelta(days=days)

        # 4. Try to parse weekdays (Chinese): last Monday, this Wednesday
        cn_weekday_match = re.match(r'(last|this)week([1234567])', date_query)
        if cn_weekday_match:
            week_type = cn_weekday_match.group(1)  # last or this
            weekday_str = cn_weekday_match.group(2)
            target_weekday = DateParser.WEEKDAY_CN[weekday_str]
            return DateParser._get_date_by_weekday(target_weekday, week_type == "last")

        # 5. Try to parse weekdays (English): last monday, this friday
        en_weekday_match = re.match(r'(last|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', date_query)
        if en_weekday_match:
            week_type = en_weekday_match.group(1)  # last or this
            weekday_str = en_weekday_match.group(2)
            target_weekday = DateParser.WEEKDAY_EN[weekday_str]
            return DateParser._get_date_by_weekday(target_weekday, week_type == "last")

        # 6. Try to parse absolute dates: YYYY-MM-DD
        iso_date_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_query)
        if iso_date_match:
            year = int(iso_date_match.group(1))
            month = int(iso_date_match.group(2))
            day = int(iso_date_match.group(3))
            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"Invalid date: {date_query}",
                    suggestion=f"Date value error: {str(e)}"
                )

        # 7. Try to parse Chinese dates: MM month DD day or YYYY year MM month DD day
        cn_date_match = re.match(r'(?:(\d{4})year)?(\d{1,2})month(\d{1,2})day', date_query)
        if cn_date_match:
            year_str = cn_date_match.group(1)
            month = int(cn_date_match.group(2))
            day = int(cn_date_match.group(3))

            # If there is no year, use the current year
            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
                # If the month is greater than the current month, it means last year
                current_month = datetime.now().month
                if month > current_month:
                    year -= 1

            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"Invalid date: {date_query}",
                    suggestion=f"Date value error: {str(e)}"
                )

        # 8. Try to parse slash format: YYYY/MM/DD or MM/DD
        slash_date_match = re.match(r'(?:(\d{4})/)?(\d{1,2})/(\d{1,2})', date_query)
        if slash_date_match:
            year_str = slash_date_match.group(1)
            month = int(slash_date_match.group(2))
            day = int(slash_date_match.group(3))

            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
                current_month = datetime.now().month
                if month > current_month:
                    year -= 1

            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"Invalid date: {date_query}",
                    suggestion=f"Date value error: {str(e)}"
                )

        # If no formats match
        raise InvalidParameterError(
            f"Unrecognized date format: {date_query}",
            suggestion=(
                "Supported formats:\n"
                "- Relative dates: today, yesterday, the day before yesterday, 3 days ago, today, yesterday, 3 days ago\n"
                "- Weekdays: last Monday, this Wednesday, last monday, this friday\n"
                "- Absolute dates: 2025-10-10, October 10, October 10, 2025"
            )
        )

    @staticmethod
    def _get_date_by_weekday(target_weekday: int, is_last_week: bool) -> datetime:
        """
        Get date based on day of the week

        Args:
            target_weekday: Target weekday (0=Monday, 6=Sunday)
            is_last_week: Whether it is last week

        Returns:
            datetime object
        """
        today = datetime.now()
        current_weekday = today.weekday()

        # Calculate days difference
        if is_last_week:
            # A day last week
            days_diff = current_weekday - target_weekday + 7
        else:
            # A day this week
            days_diff = current_weekday - target_weekday
            if days_diff < 0:
                days_diff += 7

        return today - timedelta(days=days_diff)

    @staticmethod
    def format_date_folder(date: datetime) -> str:
        """
        Format date as folder name

        Args:
            date: datetime object

        Returns:
            Folder name, format: YYYY-MM-DD

        Examples:
            >>> DateParser.format_date_folder(datetime(2025, 10, 11))
            '2025-10-11'
        """
        return date.strftime("%Y-%m-%d")

    @staticmethod
    def validate_date_not_future(date: datetime) -> None:
        """
        Validate date is not in the future

        Args:
            date: Date to validate

        Raises:
            InvalidParameterError: Date is in the future
        """
        if date.date() > datetime.now().date():
            raise InvalidParameterError(
                f"Cannot query future dates: {date.strftime('%Y-%m-%d')}",
                suggestion="Please use today or past dates"
            )

    @staticmethod
    def validate_date_not_too_old(date: datetime, max_days: int = 365) -> None:
        """
        Validate date is not too old

        Args:
            date: Date to validate
            max_days: Maximum number of days

        Raises:
            InvalidParameterError: Date is too old
        """
        days_ago = (datetime.now().date() - date.date()).days
        if days_ago > max_days:
            raise InvalidParameterError(
                f"Date is too old: {date.strftime('%Y-%m-%d')} ({days_ago} days ago)",
                suggestion=f"Please query data within {max_days} days"
            )

    @staticmethod
    def resolve_date_range_expression(expression: str) -> Dict:
        """
        Parse natural language date expression into standard date range

        This is a method specifically designed for MCP tools, used to parse date expressions on the server side,
        avoiding inconsistency issues caused by AI models calculating dates themselves.

        Args:
            expression: Natural language date expression, supports:
                - Single day: "today", "yesterday", "today", "yesterday"
                - This week/last week: "this week", "last week", "this week", "last week"
                - This month/last month: "this month", "last month", "this month", "last month"
                - Last N days: "last 7 days", "last 30 days", "last 7 days", "last 30 days"
                - Dynamic N days: "last 5 days", "last 10 days"

        Returns:
            Parsed result dictionary:
            {
                "success": True,
                "expression": "this week",
                "normalized": "this_week",
                "date_range": {
                    "start": "2025-11-18",
                    "end": "2025-11-24"
                },
                "current_date": "2025-11-26",
                "description": "This week (Monday to Sunday)"
            }

        Raises:
            InvalidParameterError: Unrecognized date expression

        Examples:
            >>> DateParser.resolve_date_range_expression("this week")
            {"success": True, "date_range": {"start": "2025-11-18", "end": "2025-11-24"}, ...}

            >>> DateParser.resolve_date_range_expression("last 7 days")
            {"success": True, "date_range": {"start": "2025-11-20", "end": "2025-11-26"}, ...}
        """
        if not expression or not isinstance(expression, str):
            raise InvalidParameterError(
                "Date expression cannot be empty",
                suggestion="Please provide a valid date expression, such as: this week, last 7 days, last week"
            )

        expression_lower = expression.strip().lower()
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        # 1. Try to match predefined expressions
        normalized = DateParser.RANGE_EXPRESSIONS.get(expression_lower)

        # 2. Try to match dynamic "last N days" / "last N days" pattern
        if not normalized:
            # Chinese: last N days
            cn_match = re.match(r'last(\d+)days', expression_lower)
            if cn_match:
                days = int(cn_match.group(1))
                normalized = f"last_{days}_days"

            # English: last N days
            en_match = re.match(r'(?:last|past)\s+(\d+)\s+days?', expression_lower)
            if en_match:
                days = int(en_match.group(1))
                normalized = f"last_{days}_days"

        if not normalized:
            # Provide a list of supported expressions
            supported_cn = ["today", "yesterday", "this week", "last week", "this month", "last month",
                           "last 7 days", "last 30 days", "last N days"]
            supported_en = ["today", "yesterday", "this week", "last week",
                           "this month", "last month", "last 7 days", "last N days"]
            raise InvalidParameterError(
                f"Unrecognized date expression: {expression}",
                suggestion=f"Supported expressions:\nChinese: {', '.join(supported_cn)}\nEnglish: {', '.join(supported_en)}"
            )

        # 3. Calculate date range based on normalized type
        start_date, end_date, description = DateParser._calculate_date_range(
            normalized, today
        )

        return {
            "success": True,
            "expression": expression,
            "normalized": normalized,
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "current_date": today_str,
            "description": description
        }

    @staticmethod
    def _calculate_date_range(
        normalized: str,
        today: datetime
    ) -> Tuple[datetime, datetime, str]:
        """
        Calculate the actual date range based on the normalized date type

        Args:
            normalized: Normalized date type
            today: Current date

        Returns:
            (start_date, end_date, description) tuple
        """
        # Single day type
        if normalized == "today":
            return today, today, "today"

        if normalized == "yesterday":
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday, "yesterday"

        # This week (Monday to Sunday)
        if normalized == "this_week":
            # Calculate this Monday
            weekday = today.weekday()  # 0=Monday, 6=Sunday
            start = today - timedelta(days=weekday)
            end = start + timedelta(days=6)
            # If this week has not ended, end cannot exceed today
            if end > today:
                end = today
            return start, end, f"This week (Monday to Sunday, {start.strftime('%m-%d')} to {end.strftime('%m-%d')})"

        # Last week (last Monday to last Sunday)
        if normalized == "last_week":
            weekday = today.weekday()
            # This Monday
            this_monday = today - timedelta(days=weekday)
            # Last Monday
            start = this_monday - timedelta(days=7)
            end = start + timedelta(days=6)
            return start, end, f"Last week ({start.strftime('%m-%d')} to {end.strftime('%m-%d')})"

        # This month (1st of this month to today)
        if normalized == "this_month":
            start = today.replace(day=1)
            return start, today, f"This month ({start.strftime('%m-%d')} to {today.strftime('%m-%d')})"

        # Last month (1st of last month to the last day of last month)
        if normalized == "last_month":
            # Last day of last month = 1st of this month - 1 day
            first_of_this_month = today.replace(day=1)
            end = first_of_this_month - timedelta(days=1)
            start = end.replace(day=1)
            return start, end, f"Last month ({start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')})"

        # Last N days (last_N_days format)
        match = re.match(r'last_(\d+)_days', normalized)
        if match:
            days = int(match.group(1))
            start = today - timedelta(days=days - 1)  # Includes today, so it is days-1
            return start, today, f"Last {days} days ({start.strftime('%m-%d')} to {today.strftime('%m-%d')})"

        # Fallback: return today
        return today, today, "Today (default)"

    @staticmethod
    def get_supported_expressions() -> Dict[str, list]:
        """
        Get a list of supported date expressions

        Returns:
            Categorized list of expressions
        """
        return {
            "Single day": ["Today", "Yesterday", "today", "yesterday"],
            "Week": ["This week", "Last week", "this week", "last week"],
            "Month": ["This month", "Last month", "this month", "last month"],
            "Last N days": ["Last 3 days", "Last 7 days", "Last 14 days", "Last 30 days",
                      "last 3 days", "last 7 days", "last 14 days", "last 30 days"],
            "Dynamic days": ["Last N days", "last N days"]
        }
