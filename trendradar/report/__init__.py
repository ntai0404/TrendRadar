# coding=utf-8
"""
report generation module

Provides report generation and formatting capabilities, including:
- HTML report generation
- Title formatting tool

Module structure:
- helpers: report helper functions (cleaning, escaping, formatting)
- formatter: platform title formatting
- html: HTML report rendering
- generator: report generator
"""

from trendradar.report.helpers import (
    clean_title,
    html_escape,
    format_rank_display,
)
from trendradar.report.formatter import format_title_for_platform
from trendradar.report.html import render_html_content
from trendradar.report.generator import (
    prepare_report_data,
    generate_html_report,
)

__all__ = [
    # Helper function
    "clean_title",
    "html_escape",
    "format_rank_display",
    # Format function
    "format_title_for_platform",
    # HTML rendering
    "render_html_content",
    # report generator
    "prepare_report_data",
    "generate_html_report",
]
