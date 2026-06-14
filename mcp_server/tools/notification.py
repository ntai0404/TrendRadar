# coding=utf-8
"""
Notification push tool

Supports sending messages to configured notification channels, automatically detecting channel configurations in config.yaml and .env.
Accepts markdown format content, internally automatically converts the format according to the requirements of each channel before sending.
"""

import json
import os
import re
import smtplib
import time
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
import yaml

from trendradar.core.loader import _load_webhook_config, _load_notification_config
from trendradar.notification.batch import (
    truncate_to_bytes,
    get_batch_header,
    get_max_batch_header_size,
    add_batch_headers,
)
from trendradar.notification.formatters import strip_markdown
from trendradar.notification.senders import SMTP_CONFIGS

from ..utils.errors import MCPError, InvalidParameterError


# ==================== Channel enablement judgment rules ====================

# Which configuration items each channel needs to be non-empty to be considered "configured"
# Note: NTFY_SERVER_URL has a default value of "https://ntfy.sh" in the loader, and is not used as a judgment basis
_CHANNEL_REQUIREMENTS = {
    "feishu": ["FEISHU_WEBHOOK_URL"],
    "dingtalk": ["DINGTALK_WEBHOOK_URL"],
    "wework": ["WEWORK_WEBHOOK_URL"],
    "telegram": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
    "email": ["EMAIL_FROM", "EMAIL_PASSWORD", "EMAIL_TO"],
    "ntfy": ["NTFY_TOPIC"],
    "bark": ["BARK_URL"],
    "slack": ["SLACK_WEBHOOK_URL"],
    "generic_webhook": ["GENERIC_WEBHOOK_URL"],
}

# Channel display name
_CHANNEL_NAMES = {
    "feishu": "Feishu",
    "dingtalk": "DingTalk",
    "wework": "WeCom",
    "telegram": "Telegram",
    "email": "Email",
    "ntfy": "ntfy",
    "bark": "Bark",
    "slack": "Slack",
    "generic_webhook": "Generic Webhook",
}


# ==================== Batch processing configuration ====================

# Default values for the maximum batch bytes of each channel
# Read and overwrite from config.yaml → advanced.batch_size at runtime
_CHANNEL_BATCH_SIZES_DEFAULT = {
    "feishu": 30000,    # config.yaml: advanced.batch_size.feishu
    "dingtalk": 20000,  # config.yaml: advanced.batch_size.dingtalk
    "wework": 4000,     # config.yaml: advanced.batch_size.default
    "telegram": 4000,   # config.yaml: advanced.batch_size.default
    "email": 0,         # Email has no byte limit, no batching
    "ntfy": 3800,       # Strict 4KB limit (ntfy code default value)
    "bark": 4000,       # config.yaml: advanced.batch_size.bark
    "slack": 4000,      # config.yaml: advanced.batch_size.slack
    "generic_webhook": 4000,
}

# Channels that display the latest messages first need to send batches in reverse order
_REVERSE_BATCH_CHANNELS = {"ntfy", "bark"}

# Default batch send interval (seconds), read from config.yaml → advanced.batch_send_interval at runtime
_BATCH_INTERVAL_DEFAULT = 3.0


# ==================== Batch processing ====================
# truncate_to_bytes, get_batch_header, get_max_batch_header_size,
# add_batch_headers reused from trendradar.notification.batch


def _split_text_into_batches(text: str, max_bytes: int) -> List[str]:
    """Split text into batches by byte limit, prioritizing cutting at paragraph boundaries (double newline)

    Split strategy (refer to the atomicity guarantee of trendradar splitter.py):
    1. Prioritize splitting by paragraph (double newline \\n\\n)
    2. When the paragraph still exceeds the limit, split by single line (\\n)
    3. When a single line still exceeds the limit, use _truncate_to_bytes to safely truncate

    Args:
        text: Text converted to the target channel format
        max_bytes: Maximum bytes per batch (deducting the batch header reservation)

    Returns:
        List of batched texts
    """
    if max_bytes <= 0 or len(text.encode("utf-8")) <= max_bytes:
        return [text]

    # Split by paragraph
    paragraphs = text.split("\n\n")
    batches = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
        else:
            # The current paragraph cannot fit, save the existing content first
            if current:
                batches.append(current)
                current = ""

            # Check if a single paragraph exceeds the limit
            if len(para.encode("utf-8")) <= max_bytes:
                current = para
            else:
                # The paragraph itself exceeds the limit, split by line
                lines = para.split("\n")
                for line in lines:
                    candidate = f"{current}\n{line}" if current else line
                    if len(candidate.encode("utf-8")) <= max_bytes:
                        current = candidate
                    else:
                        if current:
                            batches.append(current)
                            current = ""
                        # Single line exceeds the limit, loop truncation until processed
                        if len(line.encode("utf-8")) > max_bytes:
                            remaining = line
                            while remaining:
                                chunk = truncate_to_bytes(remaining, max_bytes)
                                if not chunk:
                                    break
                                batches.append(chunk)
                                # Remove the truncated part
                                remaining = remaining[len(chunk):]
                        else:
                            current = line

    if current:
        batches.append(current)

    return batches if batches else [text]


def _format_for_channel(message: str, channel_id: str) -> str:
    """Adapt and convert generic Markdown to the target channel format

    Unified entry: adapt first (strip unsupported syntax), then convert (Markdown→HTML/mrkdwn, etc.).
    The returned text can be directly used for byte splitting and sending.

    Args:
        message: Original Markdown format text
        channel_id: Target channel ID

    Returns:
        Text in target channel format
    """
    if channel_id == "feishu":
        return _adapt_markdown_for_feishu(message)
    elif channel_id == "dingtalk":
        return _adapt_markdown_for_dingtalk(message)
    elif channel_id == "wework":
        return _adapt_markdown_for_wework(message)
    elif channel_id == "telegram":
        return _markdown_to_telegram_html(message)
    elif channel_id == "ntfy":
        return _adapt_markdown_for_ntfy(message)
    elif channel_id == "bark":
        return _adapt_markdown_for_bark(message)
    elif channel_id == "slack":
        return _convert_markdown_to_slack(message)
    else:
        # email, generic_webhook: Keep original Markdown
        return message


def _prepare_batches(message: str, channel_id: str, batch_sizes: Dict = None) -> List[str]:
    """Complete batch pipeline: format adaptation → byte splitting → add batch header

    Args:
        message: Original Markdown format text
        channel_id: Target channel ID
        batch_sizes: Batch size dictionary for each channel (from config.yaml), None uses default values

    Returns:
        Prepared batch list (header added, reverse order processed)
    """
    sizes = batch_sizes or _CHANNEL_BATCH_SIZES_DEFAULT
    max_bytes = sizes.get(channel_id, sizes.get("default", 4000))
    if max_bytes <= 0:
        # No byte limit (e.g., email), return original text
        return [message]

    formatted = _format_for_channel(message, channel_id)

    # Split after reserving space for batch header
    header_reserve = get_max_batch_header_size(channel_id)
    batches = _split_text_into_batches(formatted, max_bytes - header_reserve)

    # Add batch header (do not add for single batch)
    batches = add_batch_headers(batches, channel_id, max_bytes)

    # ntfy/Bark send in reverse order (client displays newest first)
    if channel_id in _REVERSE_BATCH_CHANNELS and len(batches) > 1:
        batches = list(reversed(batches))

    return batches

CHANNEL_FORMAT_GUIDES = {
    "feishu": {
        "name": "Feishu",
        "format": "Markdown (Card Message)",
        "max_length": "Approx. 29000 bytes",
        "supported": [
            "**Bold**",
            "[Link text](URL)",
            "<font color='red/green/grey/orange/blue'>Colored text</font>",
            "--- (Divider)",
            "Line break to separate paragraphs",
        ],
        "unsupported": [
            "# Heading syntax (not rendered as heading style)",
            "> Blockquote",
            "Table / Image embedding",
        ],
        "prompt": (
            "Feishu Card Markdown formatting strategy:\n"
            "1. Use **bold** for subtitles and keywords\n"
            "2. Use <font color='red'>red</font> to mark urgent/important content\n"
            "3. Use <font color='grey'>grey</font> to mark auxiliary info (time, source)\n"
            "4. Use <font color='orange'>orange</font> to mark warnings\n"
            "5. Use <font color='green'>green</font> to mark positive/success info\n"
            "6. Use [text](URL) to add clickable links\n"
            "7. Use --- to separate different topic areas\n"
            "8. Do not use # heading syntax (not rendered in card)\n"
            "9. Do not use > blockquote syntax\n"
            "10. Use line break + bold to simulate hierarchical structure"
        ),
    },
    "dingtalk": {
        "name": "DingTalk",
        "format": "Markdown",
        "max_length": "Approx. 20000 bytes",
        "supported": [
            "### Heading 3 / #### Heading 4",
            "**Bold**",
            "[Link text](URL)",
            "> Blockquote",
            "--- (Divider)",
            "- Unordered list / 1. Ordered list",
        ],
        "unsupported": [
            "# Heading 1 / ## Heading 2 (may not render)",
            "<font> Colored text",
            "~~Strikethrough~~",
            "Table / Image embedding",
        ],
        "prompt": (
            "DingTalk Markdown formatting strategy:\n"
            "1. Use ### or #### for section headings (do not use # and ##)\n"
            "2. Use **bold** to highlight keywords and data\n"
            "3. Use > blockquote to show remarks or supplementary explanations\n"
            "4. Use --- to separate different topic areas\n"
            "5. Use [text](URL) to add clickable links\n"
            "6. Use ordered lists (1. 2. 3.) to organize key points\n"
            "7. Do not use <font> color tags (DingTalk does not support)\n"
            "8. Do not use strikethrough syntax\n"
            "9. Add a blank line between heading and body to improve readability"
        ),
    },
    "wework": {
        "name": "WeCom",
        "format": "Markdown (Group Bot) / Plain text (Personal WeChat)",
        "max_length": "Approx. 4000 bytes",
        "supported": [
            "**Bold**",
            "[Link text](URL)",
            "> Blockquote (only effective on the first line)",
        ],
        "unsupported": [
            "# Heading syntax",
            "--- (Horizontal divider)",
            "<font> Colored text",
            "~~Strikethrough~~",
            "Table / Image embedding / Ordered list",
        ],
        "prompt": (
            "WeCom Markdown formatting strategy:\n"
            "1. Use **bold** for subtitles and key words\n"
            "2. Use [text](URL) to add clickable links\n"
            "3. Use > blockquote to show remarks (only effective on the first line)\n"
            "4. Keep content concise, subject to 4KB limit\n"
            "5. Do not use # heading syntax (does not render)\n"
            "6. Do not use --- (does not render), use multiple line breaks to separate areas\n"
            "7. Do not use <font> color tags\n"
            "8. Do not use strikethrough and ordered lists\n"
            "9. Use line breaks + bold to simulate hierarchical structure\n"
            "10. In personal WeChat mode, all formatting is stripped to plain text"
        ),
    },
    "telegram": {
        "name": "Telegram",
        "format": "HTML (automatically converted from Markdown)",
        "max_length": "Approx. 4096 characters",
        "supported": [
            "<b>Bold</b> (converted from **bold**)",
            "<i>Italic</i> (converted from *Italic*)",
            "<s>Strikethrough</s> (converted from ~~Strikethrough~~)",
            "<code>Inline code</code> (converted from `code`)",
            "<a href='URL'>Link</a> (converted from [text](URL))",
            "<blockquote>Blockquote</blockquote> (converted from > quote)",
        ],
        "unsupported": [
            "# Heading syntax (automatically strip # prefix)",
            "--- (Divider, automatically stripped)",
            "<font> Colored text (automatically stripped)",
            "Table / Image embedding",
        ],
        "prompt": (
            "Telegram HTML formatting strategy (input is still Markdown, automatically converted to HTML):\n"
            "1. Use **bold** to highlight keywords (converted to <b>)\n"
            "2. Use *italic* to mark auxiliary information (converted to <i>)\n"
            "3. Use `code` to mark data values/time (converted to <code>)\n"
            "4. Use [text](URL) to add links (converted to <a>)\n"
            "5. Use lines starting with > as blockquotes (converted to <blockquote>)\n"
            "6. Do not use # headings (Telegram has no heading styles, only strips #)\n"
            "7. Do not use --- dividers (stripped), use empty lines to separate\n"
            "8. Do not use <font> color tags (stripped)\n"
            "9. Content is limited to 4096 characters, keep it concise\n"
            "10. Link previews are disabled by default, suitable for information-dense messages"
        ),
    },
    "email": {
        "name": "Email",
        "format": "HTML (full webpage, converted from Markdown)",
        "max_length": "No hard limit",
        "supported": [
            "# / ## / ### Headings (converted to <h1>/<h2>/<h3>)",
            "**Bold** / *Italic* / ~~Strikethrough~~",
            "[Link text](URL)",
            "`Inline code`",
            "--- (Horizontal divider)",
        ],
        "unsupported": [
            "<font> Colored text (escaped display)",
            "Complex tables",
        ],
        "prompt": (
            "Email HTML formatting strategy (input is Markdown, automatically converted to styled HTML):\n"
            "1. Use # / ## / ### to create clear heading hierarchies\n"
            "2. Use **bold** and *italic* to enhance readability\n"
            "3. Use [text](URL) to add links (blue clickable)\n"
            "4. Use --- to separate different sections\n"
            "5. Use `code` to mark technical terms or data\n"
            "6. Can write longer content, emails have no strict length limits\n"
            "7. Email subject automatically appends date and time\n"
            "8. Automatically includes plain text fallback version"
        ),
    },
    "ntfy": {
        "name": "ntfy",
        "format": "Markdown (native support)",
        "max_length": "Approx. 3800 bytes (single message 4KB limit)",
        "supported": [
            "**Bold** / *Italic*",
            "[Link text](URL)",
            "> Blockquote",
            "`Inline code`",
            "- List",
        ],
        "unsupported": [
            "# Heading syntax (rendering depends on client)",
            "<font> Colored text",
            "--- (rendering depends on client)",
            "Table",
        ],
        "prompt": (
            "ntfy Markdown formatting strategy:\n"
            "1. Use **bold** to highlight keywords\n"
            "2. Use [text](URL) to add clickable links\n"
            "3. Use > blockquote to show notes\n"
            "4. Use `code` to mark data values\n"
            "5. Content should be concise, subject to 4KB limit\n"
            "6. Do not use <font> color tags (invalid)\n"
            "7. Do not rely on # headings and --- dividers\n"
            "8. Use blank lines and bold text to organize information hierarchy"
        ),
    },
    "bark": {
        "name": "Bark",
        "format": "Markdown (iOS push)",
        "max_length": "Approx. 3600 bytes (APNs 4KB limit)",
        "supported": [
            "**Bold**",
            "[Link text](URL)",
            "Basic text format",
        ],
        "unsupported": [
            "# Heading syntax",
            "<font> Colored text",
            "--- (Divider)",
            "> Blockquote",
            "Complex nested format",
        ],
        "prompt": (
            "Bark formatting strategy (iOS push notification):\n"
            "1. Content must be extremely concise, mobile reading scenario\n"
            "2. Use **bold** to mark core information\n"
            "3. Use [text](URL) to add links\n"
            "4. Do not use complex formats like headings/colors/blockquotes\n"
            "5. Subject to APNs 4KB limit, control content length\n"
            "6. Hierarchical structure is achieved by indentation and line breaks\n"
            "7. Suitable for short notifications and summaries, not suitable for long texts"
        ),
    },
    "slack": {
        "name": "Slack",
        "format": "mrkdwn (Slack proprietary format, automatically converted from Markdown)",
        "max_length": "Approx. 4000 bytes",
        "supported": [
            "*Bold* (converted from **bold**)",
            "_Italic_",
            "~Strikethrough~ (converted from ~~Strikethrough~~)",
            "<URL|Link text> (converted from [Text](URL))",
            "`Inline code`",
            "```Code block```",
            "> Blockquote",
        ],
        "unsupported": [
            "# Heading syntax (stripped to bold)",
            "<font> Colored text",
            "--- Divider (rendering unstable)",
            "Table",
        ],
        "prompt": (
            "Slack mrkdwn formatting strategy (input is Markdown, automatically converted to mrkdwn):\n"
            "1. Use **bold** to highlight keywords (converted to *bold*)\n"
            "2. Use ~~strikethrough~~ to mark outdated information (converted to ~strikethrough~)\n"
            "3. Use [Text](URL) to add links (converted to <URL|Text>)\n"
            "4. Use > blockquote to show remarks\n"
            "5. Use `code` to mark data values\n"
            "6. Do not use # headings (Slack has no heading styles)\n"
            "7. Do not use <font> color tags\n"
            "8. Use blank lines and bold to organize information hierarchy"
        ),
    },
    "generic_webhook": {
        "name": "General Webhook",
        "format": "Markdown (or custom template)",
        "max_length": "Approx. 4000 bytes",
        "supported": ["Standard Markdown syntax"],
        "unsupported": ["Depends on the receiving end"],
        "prompt": (
            "General Webhook formatting strategy:\n"
            "1. Use standard Markdown format\n"
            "2. Avoid using special platform-specific syntax\n"
            "3. If a custom template is configured, the content will be filled into the {content} placeholder"
        ),
    },
}


# ==================== Channel Markdown Adaptation ====================

def _adapt_markdown_for_feishu(text: str) -> str:
    """Adapt general Markdown to Feishu card Markdown format

    Feishu card supports: **bold**, [link](url), <font color='...'>, ---
    Does not support: # headings, > blockquote
    """
    # Convert # headings to bold (Feishu cards do not render heading syntax)
    text = re.sub(r'^#{1,6}\s+(.+)$', r'**\1**', text, flags=re.MULTILINE)
    # Remove blockquote syntax prefix (Feishu does not support)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _adapt_markdown_for_dingtalk(text: str) -> str:
    """Adapt general Markdown to DingTalk Markdown format

    DingTalk supports: ### #### headings, **bold**, [link](url), > blockquote, ---
    Does not support: # ## headings, <font> colored text, ~~strikethrough~~
    """
    # Remove <font> tags (DingTalk does not support, keep content)
    text = re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)
    # Downgrade # and ## headings to ### (DingTalk only supports ### and ####)
    text = re.sub(r'^##\s+(.+)$', r'### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+(.+)$', r'### \1', text, flags=re.MULTILINE)
    # Remove strikethrough syntax (DingTalk does not support)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _adapt_markdown_for_wework(text: str) -> str:
    """Adapt general Markdown to WeChat Work Markdown format

    WeChat Work supports: **bold**, [link](url), > quote (limited)
    Does not support: # heading, ---, <font>, ~~strikethrough~~, ordered list
    """
    # Remove <font> tags (keep content)
    text = re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)
    # Convert # headings to bold (WeChat Work does not render heading syntax)
    text = re.sub(r'^#{1,6}\s+(.+)$', r'**\1**', text, flags=re.MULTILINE)
    # Replace --- dividers with multiple newlines (WeChat Work does not render horizontal lines)
    text = re.sub(r'^[\-\*]{3,}\s*$', '\n\n', text, flags=re.MULTILINE)
    # Remove strikethrough syntax (WeChat Work does not support)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    # Clean up extra blank lines (keep at most two)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip()


def _adapt_markdown_for_ntfy(text: str) -> str:
    """Adapt general Markdown to ntfy format

    ntfy supports: **bold**, *italic*, [link](url), > quote, `code`
    Unreliable: # heading, ---, <font>
    """
    # Remove <font> tags (ntfy does not support)
    text = re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)
    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _adapt_markdown_for_bark(text: str) -> str:
    """Adapt general Markdown to Bark format (iOS push)

    Bark supports: **bold**, [link](url), basic text
    Does not support: # heading, <font>, ---, > quote, complex nesting
    """
    # Remove <font> tags (keep content)
    text = re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)
    # Convert # headings to bold
    text = re.sub(r'^#{1,6}\s+(.+)$', r'**\1**', text, flags=re.MULTILINE)
    # Replace --- with newlines
    text = re.sub(r'^[\-\*]{3,}\s*$', '\n', text, flags=re.MULTILINE)
    # Remove quote syntax
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # Remove strikethrough syntax
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ==================== Format Conversion ====================

def _markdown_to_telegram_html(text: str) -> str:
    """
    Convert markdown to Telegram supported HTML format

    Telegram supported tags: <b>, <i>, <s>, <code>, <a href="url">text</a>, <blockquote>
    """
    # Preprocessing: remove <font> tags (Telegram does not support, keep content)
    text = re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)

    lines = text.split('\n')
    result_lines = []
    in_blockquote = False

    for line in lines:
        # Convert heading symbols # ## ### to bold
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if header_match:
            line = f'**{header_match.group(2)}**'

        # Remove horizontal dividers
        if re.match(r'^[\-\*]{3,}\s*$', line):
            if in_blockquote:
                result_lines.append('</blockquote>')
                in_blockquote = False
            line = ''

        # Process quote blocks > text → <blockquote>text</blockquote>
        quote_match = re.match(r'^>\s*(.*)$', line)
        if quote_match:
            if not in_blockquote:
                result_lines.append('<blockquote>')
                in_blockquote = True
            result_lines.append(quote_match.group(1))
            continue
        elif in_blockquote:
            result_lines.append('</blockquote>')
            in_blockquote = False

        result_lines.append(line)

    if in_blockquote:
        result_lines.append('</blockquote>')

    text = '\n'.join(result_lines)

    # Escape HTML entities (before tag replacement, but after blockquote tags)
    # Segment processing: keep generated HTML tags
    parts = re.split(r'(</?blockquote>)', text)
    escaped_parts = []
    for part in parts:
        if part in ('<blockquote>', '</blockquote>'):
            escaped_parts.append(part)
        else:
            part = part.replace('&', '&amp;')
            part = part.replace('<', '&lt;')
            part = part.replace('>', '&gt;')
            escaped_parts.append(part)
    text = ''.join(escaped_parts)

    # Convert links [text](url) → <a href="url">text</a>
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    # Convert bold **text** → <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    # Convert italic *text* → <i>text</i>
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)

    # Convert strikethrough ~~text~~ → <s>text</s>
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)

    # Convert inline code `code` → <code>code</code>
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _convert_markdown_to_slack(text: str) -> str:
    """Convert Markdown to Slack mrkdwn format (enhanced version)

    Slack mrkdwn differences from standard Markdown:
    - Bold: *text* (not **text**)
    - Strikethrough: ~text~ (not ~~text~~)
    - Link: <url|text> (not [text](url))
    - Header syntax not supported
    """
    # Remove <font> tags (keep content)
    text = re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)
    # Convert # headers to bold (Slack has no header style)
    text = re.sub(r'^#{1,6}\s+(.+)$', r'**\1**', text, flags=re.MULTILINE)
    # Remove --- dividers (Slack rendering is unstable)
    text = re.sub(r'^[\-\*]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Convert link format: [text](url) → <url|text>
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', text)
    # Convert strikethrough: ~~text~~ → ~text~
    text = re.sub(r'~~(.+?)~~', r'~\1~', text)
    # Convert bold: **text** → *text* (must be after strikethrough)
    text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _markdown_to_simple_html(text: str) -> str:
    """
    Convert markdown to simple HTML (for Email)
    """
    html = text

    # Escape
    html = html.replace('&', '&amp;')
    html = html.replace('<', '&lt;')
    html = html.replace('>', '&gt;')

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Headers ### → <h3>
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Strikethrough
    html = re.sub(r'~~(.+?)~~', r'<del>\1</del>', html)

    # Inline code
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Divider
    html = re.sub(r'^[\-\*]{3,}\s*$', '<hr>', html, flags=re.MULTILINE)

    # Line break
    html = html.replace('\n', '<br>\n')

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>TrendRadar Notification</title>
<style>body{{font-family:sans-serif;padding:20px;max-width:800px;margin:0 auto}}
a{{color:#1a73e8}}h1,h2,h3{{color:#333}}hr{{border:none;border-top:1px solid #ddd;margin:16px 0}}
code{{background:#f5f5f5;padding:2px 6px;border-radius:3px}}</style>
</head><body>{html}</body></html>"""


# ==================== Senders for each channel ====================

def _send_feishu(webhook_url: str, content: str, title: str) -> Dict:
    """Feishu send (plain text message, consistent with trendradar send_to_feishu)

    Feishu webhook uses msg_type: "text", all information is integrated into content.text.
    """
    payload = {
        "msg_type": "text",
        "content": {
            "text": content,
        },
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=30)
        data = resp.json()
        ok = resp.status_code == 200 and (data.get("code") == 0 or data.get("StatusCode") == 0)
        detail = ""
        if not ok:
            detail = data.get("msg") or data.get("StatusMessage", "")
        return {"success": ok, "detail": detail}
    except Exception as e:
        return {"success": False, "detail": str(e)}


def _send_dingtalk(webhook_url: str, content: str, title: str) -> Dict:
    """DingTalk send (receives adapted Markdown)"""
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": title, "text": content}
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=30)
        data = resp.json()
        ok = resp.status_code == 200 and data.get("errcode") == 0
        return {"success": ok, "detail": data.get("errmsg", "") if not ok else ""}
    except Exception as e:
        return {"success": False, "detail": str(e)}


def _send_wework(webhook_url: str, content: str, title: str, msg_type: str = "markdown") -> Dict:
    """WeCom send (receives adapted Markdown, text mode automatically strips formatting)"""
    if msg_type == "text":
        payload = {"msgtype": "text", "text": {"content": strip_markdown(content)}}
    else:
        payload = {"msgtype": "markdown", "markdown": {"content": content}}

    try:
        resp = requests.post(webhook_url, json=payload, timeout=30)
        data = resp.json()
        ok = resp.status_code == 200 and data.get("errcode") == 0
        return {"success": ok, "detail": data.get("errmsg", "") if not ok else ""}
    except Exception as e:
        return {"success": False, "detail": str(e)}


def _send_telegram(bot_token: str, chat_id: str, content: str, title: str) -> Dict:
    """Telegram send (receives converted HTML)"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": content,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        data = resp.json()
        ok = resp.status_code == 200 and data.get("ok")
        return {"success": ok, "detail": data.get("description", "") if not ok else ""}
    except Exception as e:
        return {"success": False, "detail": str(e)}


def _send_email(
    from_email: str, password: str, to_email: str,
    message: str, title: str,
    smtp_server: str = "", smtp_port: str = ""
) -> Dict:
    """Email send (HTML format)"""
    try:
        domain = from_email.split("@")[-1].lower()
        html_content = _markdown_to_simple_html(message)

        # SMTP configuration
        if smtp_server and smtp_port:
            server_host = smtp_server
            port = int(smtp_port)
            use_tls = port != 465
        elif domain in SMTP_CONFIGS:
            cfg = SMTP_CONFIGS[domain]
            server_host = cfg["server"]
            port = cfg["port"]
            use_tls = cfg["encryption"] == "TLS"
        else:
            server_host = f"smtp.{domain}"
            port = 587
            use_tls = True

        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr(("TrendRadar", from_email))

        recipients = [addr.strip() for addr in to_email.split(",")]
        msg["To"] = ", ".join(recipients)

        now = datetime.now()
        msg["Subject"] = Header(f"{title} - {now.strftime('%m/%d %H:%M')}", "utf-8")
        msg["MIME-Version"] = "1.0"
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        # Plain text fallback
        msg.attach(MIMEText(strip_markdown(message), "plain", "utf-8"))
        # HTML body
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        if use_tls:
            server = smtplib.SMTP(server_host, port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(server_host, port, timeout=30)
            server.ehlo()

        server.login(from_email, password)
        server.send_message(msg)
        server.quit()

        return {"success": True, "detail": ""}
    except Exception as e:
        return {"success": False, "detail": str(e)}


def _send_ntfy(server_url: str, topic: str, content: str, title: str, token: str = "") -> Dict:
    """ntfy send (receives adapted Markdown, consistent with trendradar send_to_ntfy)

    Note: Title uses ASCII characters to avoid HTTP header encoding issues.
    Supports 429 rate limit retry.
    """
    base_url = server_url.rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url}"
    url = f"{base_url}/{topic}"

    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Markdown": "yes",
        "Title": "TrendRadar Notification",  # ASCII, avoids HTTP header encoding issues
        "Priority": "default",
        "Tags": "news",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.post(url, data=content.encode("utf-8"), headers=headers, timeout=30)
        if resp.status_code == 200:
            return {"success": True, "detail": ""}
        elif resp.status_code == 429:
            # Rate limit, wait and retry once (consistent with trendradar)
            time.sleep(10)
            retry_resp = requests.post(url, data=content.encode("utf-8"), headers=headers, timeout=30)
            ok = retry_resp.status_code == 200
            return {"success": ok, "detail": "" if ok else f"retry status={retry_resp.status_code}"}
        elif resp.status_code == 413:
            return {"success": False, "detail": f"Message too large and rejected ({len(content.encode('utf-8'))} bytes)"}
        else:
            return {"success": False, "detail": f"status={resp.status_code}"}
    except Exception as e:
        return {"success": False, "detail": str(e)}


def _send_bark(bark_url: str, content: str, title: str) -> Dict:
    """Bark send (receives adapted Markdown, iOS push)"""
    parsed = urlparse(bark_url)
    device_key = parsed.path.strip('/').split('/')[0] if parsed.path else None
    if not device_key:
        return {"success": False, "detail": f"Cannot extract device_key from URL: {bark_url}"}

    api_endpoint = f"{parsed.scheme}://{parsed.netloc}/push"
    payload = {
        "title": title,
        "markdown": content,
        "device_key": device_key,
        "sound": "default",
        "group": "TrendRadar",
        "action": "none",
    }

    try:
        resp = requests.post(api_endpoint, json=payload, timeout=30)
        data = resp.json()
        ok = resp.status_code == 200 and data.get("code") == 200
        return {"success": ok, "detail": data.get("message", "") if not ok else ""}
    except Exception as e:
        return {"success": False, "detail": str(e)}


def _send_slack(webhook_url: str, content: str, title: str) -> Dict:
    """Slack send (receives converted mrkdwn)"""
    payload = {"text": content}

    try:
        resp = requests.post(webhook_url, json=payload, timeout=30)
        ok = resp.status_code == 200 and resp.text == "ok"
        return {"success": ok, "detail": "" if ok else resp.text}
    except Exception as e:
        return {"success": False, "detail": str(e)}


def _send_generic_webhook(
    webhook_url: str, message: str, title: str, payload_template: str = ""
) -> Dict:
    """Generic Webhook send (Markdown format, supports custom templates)"""
    try:
        if payload_template:
            json_content = json.dumps(message)[1:-1]
            json_title = json.dumps(title)[1:-1]
            payload_str = payload_template.replace("{content}", json_content).replace("{title}", json_title)
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                payload = {"title": title, "content": message}
        else:
            payload = {"title": title, "content": message}

        resp = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        ok = 200 <= resp.status_code < 300
        return {"success": ok, "detail": "" if ok else f"status={resp.status_code}"}
    except Exception as e:
        return {"success": False, "detail": str(e)}


# ==================== Utility Classes ====================

class NotificationTools:
    """Notification push utility class"""

    def __init__(self, project_root: str = None):
        if project_root:
            self.project_root = Path(project_root)
        else:
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent.parent

    def _load_merged_config(self) -> Dict[str, Any]:
        """
        Load merged notification configuration (config.yaml + .env)

        Returns:
            Merged dictionary containing webhook configuration and notification parameters
        """
        config_path = self.project_root / "config" / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = {}

        webhook_config = _load_webhook_config(config_data)
        notification_config = _load_notification_config(config_data)
        return {**webhook_config, **notification_config}

    def _detect_config_source(self, env_key: str, yaml_value: str) -> str:
        """Detect configuration item source: env / yaml / unconfigured"""
        env_val = os.environ.get(env_key, "").strip()
        if env_val:
            return "env"
        elif yaml_value:
            return "yaml"
        return ""

    def get_channel_format_guide(self, channel: Optional[str] = None) -> Dict:
        """
        Get channel formatting strategy guide

        Returns Markdown features, limitations, and best formatting prompts supported by each channel,
        for LLM reference when generating push content, ensuring content style fits the target channel.

        Args:
            channel: Specify channel ID, None returns strategies for all channels

        Returns:
            Formatting strategy dictionary
        """
        if channel:
            if channel not in CHANNEL_FORMAT_GUIDES:
                valid = list(CHANNEL_FORMAT_GUIDES.keys())
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_CHANNEL",
                        "message": f"Invalid channel: {channel}",
                        "suggestion": f"Supported channels: {valid}",
                    },
                }
            guide = CHANNEL_FORMAT_GUIDES[channel]
            return {
                "success": True,
                "channel": channel,
                "guide": guide,
            }
        else:
            return {
                "success": True,
                "summary": f"Total {len(CHANNEL_FORMAT_GUIDES)} channel formatting strategies",
                "guides": CHANNEL_FORMAT_GUIDES,
            }

    def get_notification_channels(self) -> Dict:
        """
        Get configuration status of all notification channels

        Detect config.yaml and .env environment variables, return whether each channel is configured.

        Returns:
            Channel status dictionary
        """
        try:
            config = self._load_merged_config()
            enabled = config.get("ENABLE_NOTIFICATION", True)

            # Read directly from yaml (used to determine source)
            config_path = self.project_root / "config" / "config.yaml"
            yaml_channels = {}
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
                    yaml_channels = raw.get("notification", {}).get("channels", {})

            channels = []
            env_key_map = {
                "FEISHU_WEBHOOK_URL": ("feishu", "webhook_url"),
                "DINGTALK_WEBHOOK_URL": ("dingtalk", "webhook_url"),
                "WEWORK_WEBHOOK_URL": ("wework", "webhook_url"),
                "TELEGRAM_BOT_TOKEN": ("telegram", "bot_token"),
                "TELEGRAM_CHAT_ID": ("telegram", "chat_id"),
                "EMAIL_FROM": ("email", "from"),
                "EMAIL_PASSWORD": ("email", "password"),
                "EMAIL_TO": ("email", "to"),
                "NTFY_SERVER_URL": ("ntfy", "server_url"),
                "NTFY_TOPIC": ("ntfy", "topic"),
                "BARK_URL": ("bark", "url"),
                "SLACK_WEBHOOK_URL": ("slack", "webhook_url"),
                "GENERIC_WEBHOOK_URL": ("generic_webhook", "webhook_url"),
            }

            for channel_id, required_keys in _CHANNEL_REQUIREMENTS.items():
                is_configured = all(config.get(k) for k in required_keys)

                # Determine source
                sources = set()
                for key in required_keys:
                    ch_name, field = env_key_map.get(key, ("", ""))
                    yaml_val = yaml_channels.get(ch_name, {}).get(field, "")
                    src = self._detect_config_source(key, yaml_val)
                    if src:
                        sources.add(src)

                channels.append({
                    "id": channel_id,
                    "name": _CHANNEL_NAMES.get(channel_id, channel_id),
                    "configured": is_configured,
                    "source": list(sources) if sources else [],
                })

            configured_count = sum(1 for ch in channels if ch["configured"])

            return {
                "success": True,
                "notification_enabled": enabled,
                "summary": f"{configured_count}/{len(channels)} channels configured",
                "channels": channels,
            }
        except Exception as e:
            return {
                "success": False,
                "error": {"code": "INTERNAL_ERROR", "message": str(e)},
            }

    def send_notification(
        self,
        message: str,
        title: str = "TrendRadar Notification",
        channels: Optional[List[str]] = None,
    ) -> Dict:
        """
        Send message to configured notification channels

        Accepts markdown format content, internally automatically converts to the format required by each channel.

        Args:
            message: markdown format message content
            title: Message title
            channels: List of channels to send to, None means send to all configured channels
                      Optional values: feishu, dingtalk, wework, telegram, email, ntfy, bark, slack, generic_webhook

        Returns:
            Send result dictionary
        """
        if not message or not message.strip():
            return {
                "success": False,
                "error": {"code": "EMPTY_MESSAGE", "message": "Message content cannot be empty"},
            }

        try:
            config = self._load_merged_config()

            if not config.get("ENABLE_NOTIFICATION", True):
                return {
                    "success": False,
                    "error": {"code": "NOTIFICATION_DISABLED", "message": "Notification feature is disabled (notification.enabled = false)"},
                }

            # Determine target channels
            all_channel_ids = list(_CHANNEL_REQUIREMENTS.keys())
            if channels:
                # Validate channel names
                invalid = [ch for ch in channels if ch not in all_channel_ids]
                if invalid:
                    raise InvalidParameterError(
                        f"Invalid channel: {invalid}",
                        suggestion=f"Supported channels: {all_channel_ids}"
                    )
                target_channels = channels
            else:
                # Send to all configured channels
                target_channels = [
                    ch_id for ch_id, keys in _CHANNEL_REQUIREMENTS.items()
                    if all(config.get(k) for k in keys)
                ]

            if not target_channels:
                return {
                    "success": False,
                    "error": {
                        "code": "NO_CHANNELS",
                        "message": "No configured target channels",
                        "suggestion": "Please configure at least one notification channel in config.yaml or .env",
                    },
                }

            # Send by channel
            results = {}
            for ch_id in target_channels:
                required_keys = _CHANNEL_REQUIREMENTS[ch_id]
                if not all(config.get(k) for k in required_keys):
                    results[ch_id] = {"success": False, "detail": "Channel not configured"}
                    continue

                result = self._dispatch_to_channel(ch_id, config, message, title)
                results[ch_id] = result

            success_count = sum(1 for r in results.values() if r["success"])
            total = len(results)

            return {
                "success": success_count > 0,
                "summary": f"{success_count}/{total} channels sent successfully",
                "results": {
                    ch_id: {
                        "name": _CHANNEL_NAMES.get(ch_id, ch_id),
                        **r,
                    }
                    for ch_id, r in results.items()
                },
            }

        except MCPError as e:
            return {"success": False, "error": e.to_dict()}
        except Exception as e:
            return {
                "success": False,
                "error": {"code": "INTERNAL_ERROR", "message": str(e)},
            }

    def _dispatch_to_channel(
        self, channel_id: str, config: Dict, message: str, title: str
    ) -> Dict:
        """Distribute messages to specified channels (format adaptation → byte batching → multiple accounts × batch sending)

        Read configuration from config.yaml → advanced.batch_size / batch_send_interval.
        """
        # Read batch configuration from config (consistent with trendradar)
        batch_sizes = self._get_batch_sizes()
        batch_interval = self._get_batch_interval()

        # Email has no byte limit, does not go through batch pipeline
        if channel_id == "email":
            return _send_email(
                config["EMAIL_FROM"],
                config["EMAIL_PASSWORD"],
                config["EMAIL_TO"],
                message, title,
                config.get("EMAIL_SMTP_SERVER", ""),
                config.get("EMAIL_SMTP_PORT", ""),
            )

        # Unified batch pipeline: format adaptation → byte splitting → add batch header → (optional) reverse order
        batches = _prepare_batches(message, channel_id, batch_sizes)

        # Route and send by channel
        if channel_id == "feishu":
            return self._send_batched_multi_account(
                config["FEISHU_WEBHOOK_URL"], batches, channel_id,
                lambda url, content: _send_feishu(url, content, title),
                batch_interval,
            )
        elif channel_id == "dingtalk":
            return self._send_batched_multi_account(
                config["DINGTALK_WEBHOOK_URL"], batches, channel_id,
                lambda url, content: _send_dingtalk(url, content, title),
                batch_interval,
            )
        elif channel_id == "wework":
            msg_type = config.get("WEWORK_MSG_TYPE", "markdown")
            return self._send_batched_multi_account(
                config["WEWORK_WEBHOOK_URL"], batches, channel_id,
                lambda url, content: _send_wework(url, content, title, msg_type),
                batch_interval,
            )
        elif channel_id == "telegram":
            return self._send_batched_telegram(
                config, batches, title, batch_interval,
            )
        elif channel_id == "ntfy":
            return self._send_batched_ntfy(
                config, batches, title, batch_interval,
            )
        elif channel_id == "bark":
            return self._send_batched_multi_account(
                config["BARK_URL"], batches, channel_id,
                lambda url, content: _send_bark(url, content, title),
                batch_interval,
            )
        elif channel_id == "slack":
            return self._send_batched_multi_account(
                config["SLACK_WEBHOOK_URL"], batches, channel_id,
                lambda url, content: _send_slack(url, content, title),
                batch_interval,
            )
        elif channel_id == "generic_webhook":
            template = config.get("GENERIC_WEBHOOK_TEMPLATE", "")
            return self._send_batched_multi_account(
                config["GENERIC_WEBHOOK_URL"], batches, channel_id,
                lambda url, content: _send_generic_webhook(url, content, title, template),
                batch_interval,
            )
        else:
            return {"success": False, "detail": f"Unknown channel: {channel_id}"}

    def _get_batch_sizes(self) -> Dict:
        """Read advanced.batch_size from config.yaml, merge into default values"""
        try:
            config_path = self.project_root / "config" / "config.yaml"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
                advanced = raw.get("advanced", {})
                cfg_sizes = advanced.get("batch_size", {})
                # Build channel mapping from config
                sizes = dict(_CHANNEL_BATCH_SIZES_DEFAULT)
                default_size = cfg_sizes.get("default", 4000)
                for ch_id in sizes:
                    if ch_id in cfg_sizes:
                        sizes[ch_id] = cfg_sizes[ch_id]
                    elif ch_id not in ("email", "ntfy") and sizes[ch_id] == 4000:
                        # Use default from config
                        sizes[ch_id] = default_size
                return sizes
        except Exception:
            pass
        return dict(_CHANNEL_BATCH_SIZES_DEFAULT)

    def _get_batch_interval(self) -> float:
        """Read advanced.batch_send_interval from config.yaml"""
        try:
            config_path = self.project_root / "config" / "config.yaml"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
                return float(raw.get("advanced", {}).get("batch_send_interval", _BATCH_INTERVAL_DEFAULT))
        except Exception:
            pass
        return _BATCH_INTERVAL_DEFAULT

    def _send_batched_multi_account(
        self, urls_str: str, batches: List[str], channel_id: str, send_func,
        batch_interval: float = _BATCH_INTERVAL_DEFAULT,
    ) -> Dict:
        """Multiple accounts × batch sending (; separated URLs)"""
        urls = [u.strip() for u in urls_str.split(";") if u.strip()]
        if not urls:
            return {"success": False, "detail": "URL is empty"}

        any_ok = False
        details = []
        for url in urls:
            for i, batch in enumerate(batches):
                r = send_func(url, batch)
                if r["success"]:
                    any_ok = True
                elif r["detail"]:
                    details.append(r["detail"])
                # Interval between batches
                if i < len(batches) - 1:
                    time.sleep(batch_interval)

        return {
            "success": any_ok,
            "detail": "; ".join(details) if details else "",
            "batches": len(batches),
        }

    def _send_batched_telegram(
        self, config: Dict, batches: List[str], title: str,
        batch_interval: float = _BATCH_INTERVAL_DEFAULT,
    ) -> Dict:
        """Telegram multiple accounts × batch sending (token/chat_id pairing)"""
        tokens = config["TELEGRAM_BOT_TOKEN"].split(";")
        chat_ids = config["TELEGRAM_CHAT_ID"].split(";")
        if len(tokens) != len(chat_ids):
            return {"success": False, "detail": "Inconsistent number of bot_token and chat_id"}

        any_ok = False
        details = []
        for token, cid in zip(tokens, chat_ids):
            token, cid = token.strip(), cid.strip()
            if not (token and cid):
                continue
            for i, batch in enumerate(batches):
                r = _send_telegram(token, cid, batch, title)
                if r["success"]:
                    any_ok = True
                elif r["detail"]:
                    details.append(r["detail"])
                if i < len(batches) - 1:
                    time.sleep(batch_interval)

        return {
            "success": any_ok,
            "detail": "; ".join(details) if details else "",
            "batches": len(batches),
        }

    def _send_batched_ntfy(
        self, config: Dict, batches: List[str], title: str,
        batch_interval: float = _BATCH_INTERVAL_DEFAULT,
    ) -> Dict:
        """ntfy multiple accounts × batch sending (server/topic/token pairing, including rate limit handling)"""
        servers = config["NTFY_SERVER_URL"].split(";")
        topics = config["NTFY_TOPIC"].split(";")
        tokens_str = config.get("NTFY_TOKEN", "")
        tokens = tokens_str.split(";") if tokens_str else [""]
        if len(servers) != len(topics):
            return {"success": False, "detail": "Inconsistent number of server_url and topic"}

        any_ok = False
        details = []
        for i, (srv, topic) in enumerate(zip(servers, topics)):
            srv, topic = srv.strip(), topic.strip()
            tk = tokens[i].strip() if i < len(tokens) else ""
            if not (srv and topic):
                continue
            # ntfy.sh public server uses 2s interval (consistent with trendradar)
            interval = 2.0 if "ntfy.sh" in srv else batch_interval
            for j, batch in enumerate(batches):
                r = _send_ntfy(srv, topic, batch, title, tk)
                if r["success"]:
                    any_ok = True
                elif r["detail"]:
                    details.append(r["detail"])
                if j < len(batches) - 1:
                    time.sleep(interval)

        return {
            "success": any_ok,
            "detail": "; ".join(details) if details else "",
            "batches": len(batches),
        }
