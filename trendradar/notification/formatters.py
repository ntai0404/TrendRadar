# coding=utf-8
"""
Notification content format conversion module

Provide format conversion functions between different push platforms
"""

import re


def strip_markdown(text: str) -> str:
    """Remove the markdown syntax format in the text and use it for personal WeChat push

    Args:
        text: Contains text in markdown format

    Returns:
        Plain text content
    """
    #Convert link [text](url) -> text url (retain URL)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 \2', text)

    # Protect the URL first to prevent subsequent markdown cleaning from accidentally damaging the underline and other characters in the link.
    protected_urls: list[str] = []

    def _protect_url(match: re.Match) -> str:
        protected_urls.append(match.group(0))
        return f"@@URLTOKEN{len(protected_urls) - 1}@@"

    text = re.sub(r'https?://[^\s<>\]]+', _protect_url, text)

    # Remove bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\w)__(?!\s)(.+?)(?<!\s)__(?!\w)', r'\1', text)

    # Remove italics *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)', r'\1', text)

    # Remove strikethrough ~~text~~
    text = re.sub(r'~~(.+?)~~', r'\1', text)

    # Remove images ![alt](url) -> alt
    text = re.sub(r'!\[(.+?)\]\(.+?\)', r'\1', text)

    # Remove inline code `code`
    text = re.sub(r'`(.+?)`', r'\1', text)

    #Remove reference symbols >
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # Remove title symbols # ## ### etc.
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    # Remove horizontal dividing lines --- or ***
    text = re.sub(r'^[\-\*]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove HTML tag <font color='xxx'>text</font> -> text
    text = re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)

    # Clean up redundant blank lines (retain up to two consecutive blank lines)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Restore previously protected URL
    for idx, url in enumerate(protected_urls):
        text = text.replace(f"@@URLTOKEN{idx}@@", url)

    return text.strip()


def convert_markdown_to_mrkdwn(content: str) -> str:
    """
    Convert standard Markdown to Slack’s mrkdwn format

    Conversion rules:
    - **bold** → *bold*
    - [text](url) → <url|text>
    - Preserve other formats (code blocks, lists, etc.)

    Args:
        content: Content in Markdown format

    Returns:
        Content in Slack mrkdwn format
    """
    # 1. Convert link format: [text](url) → <url|text>
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', content)

    # 2. Convert bold: **text** → *text*
    content = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', content)

    return content
