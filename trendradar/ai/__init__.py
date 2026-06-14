# coding=utf-8
"""
TrendRadar AI module

Provides in-depth analysis and translation functions of hot news using large AI models
"""

from .analyzer import AIAnalyzer, AIAnalysisResult
from .filter import AIFilter, AIFilterResult
from .translator import AITranslator, TranslationResult, BatchTranslationResult
from .formatter import (
    get_ai_analysis_renderer,
    render_ai_analysis_markdown,
    render_ai_analysis_feishu,
    render_ai_analysis_dingtalk,
    render_ai_analysis_html_rich,
    render_ai_analysis_plain,
)

__all__ = [
    # parser
    "AIAnalyzer",
    "AIAnalysisResult",
    #Smart filtering
    "AIFilter",
    "AIFilterResult",
    # Translator
    "AITranslator",
    "TranslationResult",
    "BatchTranslationResult",
    # format
    "get_ai_analysis_renderer",
    "render_ai_analysis_markdown",
    "render_ai_analysis_feishu",
    "render_ai_analysis_dingtalk",
    "render_ai_analysis_html_rich",
    "render_ai_analysis_plain",
]
