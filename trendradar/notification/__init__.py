# coding=utf-8
"""
Notification push module

Provides multi-channel notification push function, including:
- Feishu, DingTalk, Enterprise WeChat
- Telegram、Slack
- Email、ntfy、Bark

Module structure:
- formatters: content format conversion
- batch: batch processing tool
- renderer: notification content rendering
- splitter: split messages in batches
- senders: message sender (send function for each channel)
- dispatcher: multi-account notification dispatcher
"""

from trendradar.notification.formatters import (
    strip_markdown,
    convert_markdown_to_mrkdwn,
)
from trendradar.notification.batch import (
    get_batch_header,
    get_max_batch_header_size,
    truncate_to_bytes,
    add_batch_headers,
)
from trendradar.notification.renderer import (
    render_feishu_content,
    render_dingtalk_content,
)
from trendradar.notification.splitter import (
    split_content_into_batches,
    DEFAULT_BATCH_SIZES,
)
from trendradar.notification.senders import (
    send_to_feishu,
    send_to_dingtalk,
    send_to_wework,
    send_to_telegram,
    send_to_email,
    send_to_ntfy,
    send_to_bark,
    send_to_slack,
    SMTP_CONFIGS,
)
from trendradar.notification.dispatcher import NotificationDispatcher

__all__ = [
    #Format conversion
    "strip_markdown",
    "convert_markdown_to_mrkdwn",
    # Batch processing
    "get_batch_header",
    "get_max_batch_header_size",
    "truncate_to_bytes",
    "add_batch_headers",
    #Content rendering
    "render_feishu_content",
    "render_dingtalk_content",
    #Message batching
    "split_content_into_batches",
    "DEFAULT_BATCH_SIZES",
    # Message sender
    "send_to_feishu",
    "send_to_dingtalk",
    "send_to_wework",
    "send_to_telegram",
    "send_to_email",
    "send_to_ntfy",
    "send_to_bark",
    "send_to_slack",
    "SMTP_CONFIGS",
    # Notify the scheduler
    "NotificationDispatcher",
]
