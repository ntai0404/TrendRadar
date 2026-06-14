# coding=utf-8
"""
LLM Bot Crawler Module

This module provides a browser automation crawler integrated with LLM (9Router)
to scrape data from websites requiring login (e.g. Facebook, YouTube, Groups)
and extract metadata, screenshots, and content using LLM reasoning.
"""
from .pipeline import LLMBotPipeline

__all__ = ["LLMBotPipeline"]
